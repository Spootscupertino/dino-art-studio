"""image_fit.py — Prepare a source image for a specific Printify print size.

Pipeline:
  A. DPI gate  — skip (return None) if effective DPI < 150 even after upscaling.
  B. Upscaling — try Replicate (real-esrgan 4×), then local binary, then PIL 2×.
  C. Fit       — scale-to-fill + center-crop. Never pads with color bars.

Hard dependency: Pillow (PIL).
Soft dependencies: Replicate API (REPLICATE_API_TOKEN env), realesrgan-ncnn-vulkan binary.

Public API
----------
prepare_for_print(src_path: str, print_size_str: str) -> tuple[str, dict] | None
    Returns (temp_png_path, fit_metadata_dict) or None if DPI floor not met.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from statistics import median
from typing import Any, Dict, Optional, Tuple

try:
    from PIL import Image, ImageFilter  # type: ignore
    # Our print masters are large by design (e.g. 18000x12000 @ 300 DPI). They're
    # our own trusted files, so disable PIL's decompression-bomb guard.
    Image.MAX_IMAGE_PIXELS = None
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

# ---------- constants ----------

DPI_FLOOR = 150          # minimum acceptable effective DPI
DPI_PREFERRED = 300      # Printify's nominal requirement; log a notice below this
DPI_TARGET = 600         # upload target — 2x Printify's requirement so its quality
                         # check clears comfortably (capped at the master's pixels,
                         # never upscaled).
EDGE_SAMPLE_FRACTION = 0.05  # retained for any future use

# Map size keys to (width_inches, height_inches).
# Portrait print sizes use width < height; mug wrap sizes are landscape.
PRINT_SIZES: Dict[str, Tuple[float, float]] = {
    "12x18": (12.0, 18.0),
    "18x24": (18.0, 24.0),
    "24x36": (24.0, 36.0),
    "16x20": (16.0, 20.0),
    # Landscape poster sizes (blueprint 284, Matte Horizontal Posters).
    "18x12": (18.0, 12.0),
    "24x18": (24.0, 18.0),
    "36x24": (36.0, 24.0),
    "11oz_mug": (8.5, 3.6),   # landscape mug wrap
    "15oz_mug": (8.5, 4.0),   # landscape mug wrap
}


# ---------- A. DPI gate ----------

def effective_dpi(src_w: int, src_h: int, print_w_in: float, print_h_in: float) -> float:
    """Compute the effective DPI when the source image fills the print area.

    We fill the print canvas by scaling so the *shorter* source dimension
    covers the *corresponding* print dimension (i.e. scale-to-fill, portrait).
    Returns the DPI along the constraining axis.
    """
    scale_w = print_w_in / src_w
    scale_h = print_h_in / src_h
    # To fill without white bars we must use the smaller scale factor
    # (i.e. the axis that's relatively more constrained).
    fill_scale = min(scale_w, scale_h)
    # Effective DPI = 1 / fill_scale (pixels per inch).
    return 1.0 / fill_scale if fill_scale > 0 else 0.0


# ---------- B. Upscaling ----------

def _upscale_replicate(src_path: str, scale: int = 4) -> Optional[str]:
    """Try to upscale via Replicate nightmareai/real-esrgan. Returns temp path or None."""
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        return None

    print(f"[image_fit] Attempting Replicate upscale ({scale}×) for {src_path}")
    api_url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }
    payload = json.dumps({
        "version": "42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
        "input": {
            "image": _encode_image_data_uri(src_path),
            "scale": scale,
            "face_enhance": False,
        },
    }).encode("utf-8")

    req = urllib.request.Request(api_url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            prediction = json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"[image_fit] Replicate request failed: {exc}")
        return None

    prediction_id = prediction.get("id")
    if not prediction_id:
        print(f"[image_fit] Replicate: no prediction ID in response: {prediction}")
        return None

    # Poll for completion.
    poll_url = f"{api_url}/{prediction_id}"
    poll_headers = {"Authorization": f"Token {token}"}
    for attempt in range(60):  # up to ~5 min
        time.sleep(5)
        req = urllib.request.Request(poll_url, headers=poll_headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status_data = json.loads(resp.read())
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            print(f"[image_fit] Replicate poll error (attempt {attempt}): {exc}")
            continue

        status = status_data.get("status")
        if status == "succeeded":
            output = status_data.get("output")
            if not output:
                print("[image_fit] Replicate succeeded but no output URL.")
                return None
            output_url = output if isinstance(output, str) else output[0]
            return _download_to_temp(output_url, suffix=".png")
        if status in ("failed", "canceled"):
            print(f"[image_fit] Replicate prediction {status}: {status_data.get('error')}")
            return None
        # still processing — keep polling

    print("[image_fit] Replicate poll timed out.")
    return None


def _encode_image_data_uri(src_path: str) -> str:
    """Encode image as a base64 data URI for Replicate input."""
    import base64
    with open(src_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    suffix = Path(src_path).suffix.lower().lstrip(".")
    mime = "image/png" if suffix == "png" else "image/jpeg"
    return f"data:{mime};base64,{data}"


def _download_to_temp(url: str, suffix: str = ".png") -> Optional[str]:
    """Download URL to a named temp file. Returns path or None on error."""
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        with urllib.request.urlopen(url, timeout=120) as resp:
            tmp.write(resp.read())
        tmp.flush()
        tmp.close()
        return tmp.name
    except Exception as exc:
        print(f"[image_fit] Download failed ({url}): {exc}")
        return None


def _upscale_local_binary(src_path: str, scale: int = 4) -> Optional[str]:
    """Try local realesrgan-ncnn-vulkan binary. Returns temp path or None."""
    binary = shutil.which("realesrgan-ncnn-vulkan")
    if not binary:
        return None

    print(f"[image_fit] Attempting local Real-ESRGAN upscale ({scale}×) for {src_path}")
    tmp_out = tempfile.mktemp(suffix=".png")
    try:
        result = subprocess.run(
            [binary, "-i", src_path, "-o", tmp_out, "-s", str(scale)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            print(f"[image_fit] realesrgan-ncnn-vulkan failed: {result.stderr[:500]}")
            return None
        return tmp_out
    except subprocess.TimeoutExpired:
        print("[image_fit] realesrgan-ncnn-vulkan timed out.")
        return None
    except Exception as exc:
        print(f"[image_fit] realesrgan-ncnn-vulkan error: {exc}")
        return None


def _upscale_pil_lanczos(src_path: str) -> str:
    """2× upscale using PIL LANCZOS. Always returns a temp path."""
    print(f"[image_fit] Falling back to PIL LANCZOS 2× upscale for {src_path}")
    img = Image.open(src_path)
    new_w, new_h = img.width * 2, img.height * 2
    img2 = img.resize((new_w, new_h), Image.LANCZOS)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    img2.save(tmp.name)
    tmp.close()
    return tmp.name


def upscale(src_path: str) -> Tuple[str, str]:
    """Attempt upscale. Returns (result_path, method_label)."""
    path = _upscale_replicate(src_path, scale=4)
    if path:
        return path, "replicate_real_esrgan_4x"

    path = _upscale_local_binary(src_path, scale=4)
    if path:
        return path, "local_realesrgan_4x"

    path = _upscale_pil_lanczos(src_path)
    return path, "pil_lanczos_2x"


# Long edge (px) the master must reach so the largest poster (36in @ 300 DPI)
# clears Printify's quality check with headroom. 36 * 300 = 10800.
MASTER_LONG_EDGE = 10800

# real-esrgan on Replicate rejects inputs above its GPU pixel budget
# (~2,096,704 px observed). Stay safely under it, and never feed it its own 4×
# output (which is always over the cap → 413/429). One AI pass max, then LANCZOS.
REALESRGAN_MAX_PIXELS = 2_000_000


def upscale_to_master(
    src_path: str,
    dest_path: str,
    target_long_edge: int = MASTER_LONG_EDGE,
) -> Dict[str, Any]:
    """Upscale src into a high-res print master at dest_path (PNG).

    Strategy: one real-esrgan 4× pass (only when the source fits under the
    model's pixel cap), then LANCZOS-resize to exactly target_long_edge on the
    long edge. real-esrgan is never called more than once — its 4× output always
    exceeds the cap, so repeat calls just 413/429. Sources already over the cap
    skip AI entirely and go straight to LANCZOS.

    Returns metadata: {source_size, master_size, passes, methods}.
    """
    if not _PIL_AVAILABLE:
        raise ImportError("Pillow (PIL) is required for image_fit.")

    with Image.open(src_path) as _im:
        src_w, src_h = _im.size
    meta: Dict[str, Any] = {
        "source_size": f"{src_w}x{src_h}",
        "passes": 0,
        "methods": [],
    }

    work_path = src_path
    long_edge = max(src_w, src_h)

    # One guarded AI pass: only if it helps (still below target) and fits the cap.
    if long_edge < target_long_edge and (src_w * src_h) <= REALESRGAN_MAX_PIXELS:
        up_path, method = upscale(work_path)
        with Image.open(up_path) as up:
            new_long = max(up.size)
        if new_long > long_edge:
            work_path, long_edge = up_path, new_long
            meta["methods"].append(method)
            meta["passes"] += 1
    elif (src_w * src_h) > REALESRGAN_MAX_PIXELS:
        meta["methods"].append("ai_skipped_over_cap")

    master = Image.open(work_path).convert("RGB")
    mw, mh = master.size
    # Resize to exactly target on the long edge — LANCZOS up the remainder, or
    # down if a 4× pass overshot. Upsizing past source is acceptable for a print
    # master (geometric DPI is what Printify checks); it's still real detail.
    if max(mw, mh) != target_long_edge:
        scale = target_long_edge / max(mw, mh)
        master = master.resize((round(mw * scale), round(mh * scale)), Image.LANCZOS)
        meta["methods"].append("pil_lanczos_finish")
        meta["passes"] += 1

    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
    master.save(dest_path, format="PNG", optimize=True)
    meta["master_size"] = f"{master.width}x{master.height}"
    return meta


# ---------- C. Smart fit to portrait ----------

def _edge_median_color(img: Image.Image) -> Tuple[int, int, int]:
    """Sample edge pixels (left/right 5% columns) and return median RGB."""
    w, h = img.size
    sample_cols = max(1, int(w * EDGE_SAMPLE_FRACTION))

    pixels_r, pixels_g, pixels_b = [], [], []
    rgb_img = img.convert("RGB")
    px = rgb_img.load()

    for y in range(h):
        for x in range(sample_cols):
            r, g, b = px[x, y]
            pixels_r.append(r); pixels_g.append(g); pixels_b.append(b)
        for x in range(w - sample_cols, w):
            r, g, b = px[x, y]
            pixels_r.append(r); pixels_g.append(g); pixels_b.append(b)

    return (
        int(median(pixels_r)),
        int(median(pixels_g)),
        int(median(pixels_b)),
    )


def _energy_profile(edge: Image.Image, axis: str) -> list:
    """Collapse a single-channel edge map to a 1-D energy profile.

    axis='x' -> per-column mean energy (length = width)
    axis='y' -> per-row mean energy (length = height)

    Uses PIL's BOX resize to average the perpendicular dimension, so no numpy
    is needed. Returns a list of floats.
    """
    w, h = edge.size
    if axis == "x":
        collapsed = edge.resize((w, 1), Image.BOX)
    else:
        collapsed = edge.resize((1, h), Image.BOX)
    return list(collapsed.getdata())


def _best_offset(profile: list, window: int) -> int:
    """Slide a window of `window` cells over `profile`; return the start offset
    whose window holds the most total energy. Ties resolve toward center."""
    n = len(profile)
    if window >= n:
        return 0
    # Prefix sums for O(n) sliding-window totals.
    prefix = [0.0] * (n + 1)
    for i, v in enumerate(profile):
        prefix[i + 1] = prefix[i] + v
    best_off, best_sum = 0, -1.0
    center_off = (n - window) // 2
    for off in range(0, n - window + 1):
        total = prefix[off + window] - prefix[off]
        # Strictly-greater keeps the first (left-most) max; bias ties toward the
        # center so a flat/low-detail image behaves like the old center-crop.
        if total > best_sum or (total == best_sum and abs(off - center_off) < abs(best_off - center_off)):
            best_sum, best_off = total, off
    return best_off


def fit_to_print(
    img: Image.Image,
    target_w_px: int,
    target_h_px: int,
) -> Tuple[Image.Image, str]:
    """Scale-to-fill then saliency-crop. Never pads — no color bars ever.

    Instead of a blind center-crop, the crop window slides to the region of
    highest edge energy, so a high-detail subject (e.g. a dinosaur's head and
    snout near a frame edge) is kept rather than sliced off. Falls back to a
    center-crop if the energy map is flat. Returns (fitted_image, decision).
    """
    src_w, src_h = img.size

    # Fill-scale: use the larger scale factor so every pixel of the target is covered.
    fill_scale = max(target_w_px / src_w, target_h_px / src_h)

    scaled_w = int(src_w * fill_scale)
    scaled_h = int(src_h * fill_scale)
    scaled = img.convert("RGB").resize((scaled_w, scaled_h), Image.LANCZOS)

    crop_x = scaled_w - target_w_px  # >0 means we crop horizontally
    crop_y = scaled_h - target_h_px  # >0 means we crop vertically

    # Default to center; only run the saliency pass on the axis that's cropped.
    left = crop_x // 2
    top = crop_y // 2
    decision = "center_crop"

    if crop_x > 0 or crop_y > 0:
        # A downscaled grayscale edge map is enough to locate the subject and is
        # fast regardless of master size. FIND_EDGES highlights detailed regions
        # (scales, teeth, claws) over smooth sky/ground.
        probe_long = 512
        pscale = min(1.0, probe_long / max(scaled_w, scaled_h))
        pw, ph = max(1, int(scaled_w * pscale)), max(1, int(scaled_h * pscale))
        edge = scaled.convert("L").resize((pw, ph), Image.LANCZOS).filter(ImageFilter.FIND_EDGES)

        if crop_x > 0:
            prof = _energy_profile(edge, "x")
            win = max(1, round(target_w_px * pscale))
            left = round(_best_offset(prof, win) / pscale)
            left = max(0, min(left, crop_x))
            decision = "saliency_crop"
        if crop_y > 0:
            prof = _energy_profile(edge, "y")
            win = max(1, round(target_h_px * pscale))
            top = round(_best_offset(prof, win) / pscale)
            top = max(0, min(top, crop_y))
            decision = "saliency_crop"

    result = scaled.crop((left, top, left + target_w_px, top + target_h_px))
    return result, decision


# ---------- Main entry point ----------

def prepare_for_print(
    src_path: str,
    print_size_str: str,
    dpi_floor: float = DPI_FLOOR,
    target_dpi: float = DPI_TARGET,
) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Prepare src_path for a given print size. Returns (temp_png_path, metadata) or None.

    metadata keys: decision, effective_dpi_before, effective_dpi_after, upscale_method,
                   print_size, source_size, output_size.
    Returns None if DPI floor is not met even after upscaling.
    """
    if not _PIL_AVAILABLE:
        raise ImportError("Pillow (PIL) is required for image_fit. Install with: pip install Pillow")

    if print_size_str not in PRINT_SIZES:
        raise ValueError(
            f"Unknown print_size_str {print_size_str!r}. Known sizes: {list(PRINT_SIZES)}"
        )

    print_w_in, print_h_in = PRINT_SIZES[print_size_str]

    img = Image.open(src_path)
    src_w, src_h = img.size

    # Orientation match: a clearly-landscape source should produce a landscape
    # print (and vice versa), so swap the print dims to follow it — a 3:2
    # landscape fits 36x24 with no crop instead of being sliced to 24x36.
    # A *square* source has no orientation, so honor the requested print size
    # as-is (the publisher already chose portrait vs landscape from the gallery
    # folder); only swap when the source is strictly one way or the other.
    if src_w != src_h and (src_w > src_h) != (print_w_in > print_h_in):
        print_w_in, print_h_in = print_h_in, print_w_in

    dpi_before = effective_dpi(src_w, src_h, print_w_in, print_h_in)
    meta: Dict[str, Any] = {
        "print_size": print_size_str,
        "source_size": f"{src_w}x{src_h}",
        "effective_dpi_before": round(dpi_before, 1),
    }

    # Upscale FIRST (when below the floor), then size the target against the
    # *upscaled* image. Doing it the other way clamps the target to the small
    # source, so fit_to_print would shrink the upscaled pixels right back down
    # and the upscale would be wasted (the 37-DPI bug).
    upscale_method = "none"
    if dpi_before < dpi_floor:
        print(
            f"[image_fit] DPI {dpi_before:.0f} < floor {dpi_floor} for {src_path} "
            f"@ {print_size_str} — upscaling"
        )
        upscaled_path, upscale_method = upscale(src_path)
        if upscale_method == "pil_lanczos_2x":
            print("[image_fit] NOTE: PIL LANCZOS is 2× only — may still be below DPI floor.")
        img = Image.open(upscaled_path)
        src_w, src_h = img.size
        dpi_after = effective_dpi(src_w, src_h, print_w_in, print_h_in)
        meta["effective_dpi_after"] = round(dpi_after, 1)
        meta["upscale_method"] = upscale_method
        if dpi_after < dpi_floor:
            print(
                f"[image_fit] SKIP: DPI floor not met after upscale "
                f"({dpi_after:.0f} < {dpi_floor}) for {src_path} @ {print_size_str}"
            )
            meta["skip_reason"] = "dpi_floor_not_met_after_upscale"
            return None
    else:
        meta["effective_dpi_after"] = round(dpi_before, 1)
        meta["upscale_method"] = "none"
        if dpi_before < DPI_PREFERRED:
            print(
                f"[image_fit] NOTE: DPI {dpi_before:.0f} is above floor but below preferred "
                f"{DPI_PREFERRED} for {src_path} @ {print_size_str}"
            )

    # Target pixel dimensions at target_dpi (default 600 — 2x Printify's 300 DPI
    # requirement). Computed against the (possibly upscaled) working image so we
    # never throw away resolution. The clamp below only prevents going *beyond*
    # the working image's real pixels (no synthetic upscaling past what we have).
    target_w_px = int(print_w_in * target_dpi)
    target_h_px = int(print_h_in * target_dpi)
    fill_scale = max(target_w_px / src_w, target_h_px / src_h)
    if fill_scale > 1.0:
        target_w_px = int(target_w_px / fill_scale)
        target_h_px = int(target_h_px / fill_scale)

    # Scale-to-fill + center-crop.
    fitted, decision = fit_to_print(img, target_w_px, target_h_px)
    meta["decision"] = decision
    meta["output_size"] = f"{fitted.width}x{fitted.height}"

    # Save as JPEG (much smaller than PNG for base64 upload; 95% quality is
    # indistinguishable from lossless at print viewing distances).
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    fitted.convert("RGB").save(tmp.name, format="JPEG", quality=92, optimize=True)
    tmp.close()

    print(
        f"[image_fit] {Path(src_path).name} @ {print_size_str}: "
        f"{decision}, DPI {meta['effective_dpi_before']} -> {meta['effective_dpi_after']}, "
        f"upscale={upscale_method}, output={meta['output_size']}"
    )
    return tmp.name, meta
