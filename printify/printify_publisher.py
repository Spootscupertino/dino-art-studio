"""Printify publisher — orchestrator.

Reads:
  - site/src/data/products.json (gallery contract feed)
  - site/src/assets/gallery/<category>/*.png (the actual artwork)
  - printify/printify_config.yaml (blueprint/variant truth)
  - printify/printify_ledger.json (idempotency + audit trail)

Writes:
  - printify/printify_ledger.json
  - printify/printify_config.yaml (only with --bootstrap-config)

Modes:
  --dry-run         (default) print API calls that WOULD fire, no writes
  --live            actually create + publish products
  --image PATH      target a single image instead of all unpublished
  --bootstrap-config inspect existing shop, derive config, write yaml

Hard rules:
  - Never publish live without explicit --live flag.
  - Skip any image already in the ledger (idempotent).
  - Free shipping override on every product.
  - Pricing match: existing-product price first, else cost*2.2 -> .99 floor.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Local
sys.path.insert(0, str(Path(__file__).resolve().parent))
import printify_api as api  # noqa: E402

# image_fit is a soft dependency — only needed for --live uploads.
try:
    import image_fit  # noqa: E402
    _IMAGE_FIT_AVAILABLE = True
except ImportError:
    _IMAGE_FIT_AVAILABLE = False

REPO_ROOT = Path(__file__).resolve().parent.parent
GALLERY_DIR = REPO_ROOT / "site" / "src" / "assets" / "gallery"
PRODUCTS_JSON = REPO_ROOT / "site" / "src" / "data" / "products.json"
CONFIG_PATH = Path(__file__).resolve().parent / "printify_config.yaml"
LEDGER_PATH = Path(__file__).resolve().parent / "printify_ledger.json"


def _is_flux_generated(image_path: Path) -> bool:
    sidecar = image_path.with_suffix(".json")
    if not sidecar.exists():
        return False
    try:
        meta = json.loads(sidecar.read_text())
    except Exception:
        return False
    return meta.get("source") == "flux" or "flux_params" in meta or bool(meta.get("lora"))


def _needs_approval(image_path: Path) -> bool:
    """Publish gate: Flux output requires <image>.approved sibling marker.

    Mirrors tools/sync_gallery.py — duplicated by design so neither pipeline
    can publish a LoRA experiment without explicit human sign-off.
    """
    if not _is_flux_generated(image_path):
        return False
    return not image_path.with_suffix(image_path.suffix + ".approved").exists()

POSTER_SIZES = ["12x18", "18x24", "24x36"]
CANVAS_SIZES = ["16x20", "18x24", "24x36"]
MUG_SIZES = ["11oz_mug", "15oz_mug"]

# Which product kinds to create per gallery category.
# Canvas retired 2026-05-28 — store now ships posters + mugs (phone cases TBD).
CATEGORY_PRODUCTS: Dict[str, List[str]] = {
    "horizontal": ["poster", "mug"],
    "vertical": ["poster", "mug"],
}
DEFAULT_PRODUCTS: List[str] = ["poster", "mug"]

KIND_CONTEXT = {
    "poster": ("Dinosaur Wall Art", "Fine Art Print"),
    "wrapped_canvas": ("Dinosaur Wall Art", "Wrapped Canvas"),
    "mug": ("Dinosaur Mug", "Coffee Mug"),
}


# ---------- tiny YAML I/O (no PyYAML dependency) ----------
# Our config is a small, well-known shape — we hand-roll read/write so the
# stdlib-only constraint holds. If the user installs PyYAML later, swap in.

def _yaml_dump(obj: Any, indent: int = 0) -> str:
    pad = "  " * indent
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, (int, float)):
        return repr(obj)
    if isinstance(obj, str):
        if obj == "" or any(c in obj for c in ":#\n") or obj.strip() != obj:
            return json.dumps(obj)
        return obj
    if isinstance(obj, list):
        if not obj:
            return "[]"
        # Render scalar-of-dict list as flow-style for variants readability.
        if all(isinstance(x, dict) for x in obj):
            lines = []
            for x in obj:
                inline = ", ".join(f"{k}: {_yaml_dump(v)}" for k, v in x.items())
                lines.append(f"{pad}- {{ {inline} }}")
            return "\n" + "\n".join(lines)
        return "\n" + "\n".join(f"{pad}- {_yaml_dump(x)}" for x in obj)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        out = []
        for k, v in obj.items():
            rendered = _yaml_dump(v, indent + 1)
            if rendered.startswith("\n"):
                out.append(f"{pad}{k}:{rendered}")
            else:
                out.append(f"{pad}{k}: {rendered}")
        return "\n".join(out) if indent == 0 else "\n" + "\n".join(out)
    return json.dumps(obj)


def _yaml_load(text: str) -> Dict[str, Any]:
    """Trivial YAML loader for the limited shapes we emit. Falls back to
    treating unknown content as raw strings. NOT a general parser."""
    # If a richer YAML lib is available, prefer it.
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        pass
    # Hand-rolled mini-parser: indent-based dicts, "- { k: v, ... }" flow lists,
    # scalars: null/true/false/int/float/string.
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]

    def parse_scalar(s: str) -> Any:
        s = s.strip()
        if s == "null" or s == "~":
            return None
        if s == "true":
            return True
        if s == "false":
            return False
        if s == "[]":
            return []
        if s == "{}":
            return {}
        if s.startswith("\"") and s.endswith("\""):
            return json.loads(s)
        try:
            if "." in s:
                return float(s)
            return int(s)
        except ValueError:
            return s

    def parse_flow_dict(s: str) -> Dict[str, Any]:
        # "{ k: v, k2: v2 }"
        s = s.strip()
        if s.startswith("{") and s.endswith("}"):
            s = s[1:-1].strip()
        out: Dict[str, Any] = {}
        # naive split on commas (no nested objects in our schema)
        for part in [p for p in s.split(",") if p.strip()]:
            k, _, v = part.partition(":")
            out[k.strip()] = parse_scalar(v)
        return out

    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any]] = [(-1, root)]

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        # pop stack to current indent
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else root

        if stripped.startswith("- "):
            item_text = stripped[2:].strip()
            if isinstance(parent, list):
                if item_text.startswith("{"):
                    parent.append(parse_flow_dict(item_text))
                else:
                    parent.append(parse_scalar(item_text))
            i += 1
            continue

        key, _, rest = stripped.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "":
            # Look at next line: list or dict?
            j = i + 1
            child: Any
            if j < len(lines) and lines[j].lstrip().startswith("- "):
                child = []
            else:
                child = {}
            if isinstance(parent, dict):
                parent[key] = child
            stack.append((indent, child))
        else:
            if rest.startswith("{"):
                val = parse_flow_dict(rest)
            else:
                val = parse_scalar(rest)
            if isinstance(parent, dict):
                parent[key] = val
        i += 1

    return root


# ---------- config + ledger ----------

@dataclass
class Variant:
    id: int
    size: str
    retail_cents: int
    shipping_cents: int = 0
    source_product_id: Optional[str] = None


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    return _yaml_load(CONFIG_PATH.read_text())


def write_config(cfg: Dict[str, Any]) -> None:
    header = (
        "# Printify publisher config — SOURCE OF TRUTH derived from existing Etsy shop.\n"
        "# Regenerate via: python3 printify/printify_publisher.py --bootstrap-config\n"
        f"# Generated: {datetime.now(timezone.utc).isoformat()}\n\n"
    )
    CONFIG_PATH.write_text(header + _yaml_dump(cfg) + "\n")


def load_ledger() -> Dict[str, Any]:
    if not LEDGER_PATH.exists():
        return {"version": 1, "entries": {}}
    return json.loads(LEDGER_PATH.read_text())


def write_ledger(ledger: Dict[str, Any]) -> None:
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2) + "\n")


def ledger_key(image_rel: str) -> str:
    """Stable key = relative gallery path, e.g. 'predators/tyrannosaurus-rex-...png'."""
    return image_rel.replace("\\", "/")


# ---------- pricing ----------

def round_to_dollar(price_cents: int) -> int:
    """Round retail price to the nearest whole dollar (nearest 100 cents).

    Examples: 2237 -> 2200, 2250 -> 2300 (standard .5-up), 4713 -> 4700.
    """
    return int(round(price_cents / 100.0)) * 100


def fallback_retail_cents(cost_cents: int, multiplier: float = 2.2) -> int:
    return round_to_dollar(int(cost_cents * multiplier))


# ---------- bootstrap from existing shop ----------

# Heuristic size detection from variant title strings.
SIZE_TOKENS = {
    "12x18", "12 x 18", "12\" x 18\"", "12″ x 18″",
    "16x20", "16 x 20",
    "18x24", "18 x 24",
    "24x36", "24 x 36",
}

def normalize_size(s: str) -> Optional[str]:
    if not s:
        return None
    t = "".join(c if c.isalnum() or c == "x" else "x" if ord(c) == 0xd7 else "" for c in s.lower())
    for size in ["12x18", "16x20", "18x24", "24x36"]:
        if size in t:
            return size
    # Mug sizes: match "11oz", "11 oz", "11-oz" etc.
    t_raw = s.lower()
    if ("11" in t_raw) and ("oz" in t_raw or "mug" in t_raw):
        return "11oz_mug"
    if ("15" in t_raw) and ("oz" in t_raw or "mug" in t_raw):
        return "15oz_mug"
    return None


def classify_blueprint(title: str, blueprint_title: str = "") -> Optional[str]:
    """Return 'poster', 'wrapped_canvas', 'mug', or None."""
    haystack = f"{title} {blueprint_title}".lower()
    if "mug" in haystack or "cup" in haystack:
        return "mug"
    if "canvas" in haystack:
        return "wrapped_canvas"
    if "poster" in haystack or "print" in haystack and "canvas" not in haystack:
        return "poster"
    return None


def bootstrap_config_from_shop() -> Dict[str, Any]:
    shop_id = api.get_shop_id()
    products = api.list_products(shop_id)
    print(f"[bootstrap] shop_id={shop_id}  existing_products={len(products)}")

    buckets: Dict[str, Dict[str, Variant]] = {"poster": {}, "wrapped_canvas": {}, "mug": {}}
    meta: Dict[str, Dict[str, Any]] = {"poster": {}, "wrapped_canvas": {}, "mug": {}}
    kind_sizes = {"poster": POSTER_SIZES, "wrapped_canvas": CANVAS_SIZES, "mug": MUG_SIZES}

    for prod in products:
        detail = api.get_product(shop_id, prod["id"])
        bp_id = detail.get("blueprint_id")
        pp_id = detail.get("print_provider_id")
        title = detail.get("title", "")
        kind = classify_blueprint(title)
        if kind is None:
            print(f"[bootstrap] skip product {prod['id']}: cannot classify ({title!r})")
            continue
        meta[kind].setdefault("blueprint_id", bp_id)
        meta[kind].setdefault("print_provider_id", pp_id)
        for v in detail.get("variants", []):
            size = normalize_size(v.get("title", ""))
            if not size or size not in kind_sizes[kind]:
                continue
            buckets[kind].setdefault(
                size,
                Variant(
                    id=v["id"],
                    size=size,
                    retail_cents=v.get("price", 0),
                    shipping_cents=0,
                    source_product_id=prod["id"],
                ),
            )

    def _product_section(kind: str, sizes: List[str]) -> Dict[str, Any]:
        return {
            "blueprint_id": meta[kind].get("blueprint_id"),
            "print_provider_id": meta[kind].get("print_provider_id"),
            "variants": [asdict(buckets[kind][s]) for s in sizes if s in buckets[kind]],
        }

    cfg = {
        "shop_id": shop_id,
        "products": {
            "poster": _product_section("poster", POSTER_SIZES),
            "wrapped_canvas": _product_section("wrapped_canvas", CANVAS_SIZES),
            "mug": _product_section("mug", MUG_SIZES),
        },
        "pricing": {"fallback_multiplier": 2.2, "round_to": "dollar"},
        "shipping": {"free_shipping_override": True, "etsy_shipping_profile_id": None},
    }
    return cfg


# ---------- product feed reading ----------

def load_products_feed() -> List[Dict[str, Any]]:
    return json.loads(PRODUCTS_JSON.read_text())


def find_feed_entry(rel_path: str, feed: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for e in feed:
        if e.get("filename") == rel_path:
            return e
    return None


# ---------- dry-run / live publish ----------

def plan_publish(image_rel: str, feed_entry: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Return the planned API calls (no network writes) for one image."""
    products_cfg = cfg.get("products", {})
    category = feed_entry.get("category", "")
    enabled_kinds = CATEGORY_PRODUCTS.get(category, DEFAULT_PRODUCTS)

    title = feed_entry.get("title") or Path(image_rel).stem
    description = feed_entry.get("description") or ""
    keywords = feed_entry.get("keywords") or []

    plan = {
        "image": image_rel,
        "category": category,
        "enabled_kinds": enabled_kinds,
        "title": title,
        "uploads": [{"endpoint": "POST /uploads/images.json", "file": image_rel}],
        "products": [],
    }

    for kind, sizes in [
        ("poster", POSTER_SIZES),
        ("wrapped_canvas", CANVAS_SIZES),
        ("mug", MUG_SIZES),
    ]:
        if kind not in enabled_kinds:
            continue
        kcfg = products_cfg.get(kind, {})
        if not kcfg.get("blueprint_id"):
            plan["products"].append({"kind": kind, "status": "SKIPPED — config missing (run --bootstrap-config)"})
            continue
        variants_payload = []
        for v in kcfg.get("variants", []):
            if v["size"] not in sizes:
                continue
            variants_payload.append({
                "id": v["id"],
                "price": v["retail_cents"],
                "is_enabled": True,
            })
        ctx, label = KIND_CONTEXT[kind]
        plan["products"].append({
            "kind": kind,
            "endpoint": f"POST /shops/{cfg.get('shop_id')}/products.json",
            "blueprint_id": kcfg["blueprint_id"],
            "print_provider_id": kcfg["print_provider_id"],
            "title": f"{title} | {ctx} | {label}",
            "description": description,
            "tags": keywords[:13],
            "variants": variants_payload,
            "free_shipping_override": cfg.get("shipping", {}).get("free_shipping_override", True),
            "publish_endpoint": f"POST /shops/{cfg.get('shop_id')}/products/<new_id>/publish.json",
        })
    return plan


def collect_unpublished(ledger: Dict[str, Any]) -> List[str]:
    """Return list of relative gallery paths not yet in the ledger."""
    out = []
    if not GALLERY_DIR.exists():
        return out
    for p in sorted(GALLERY_DIR.rglob("*.png")):
        rel = str(p.relative_to(GALLERY_DIR))
        if ledger_key(rel) not in ledger.get("entries", {}):
            out.append(rel)
    return out


# ---------- CLI ----------

def cmd_bootstrap_config(_args) -> int:
    cfg = bootstrap_config_from_shop()
    write_config(cfg)
    print(f"[bootstrap] wrote {CONFIG_PATH}")
    print(json.dumps(cfg, indent=2))
    return 0


def _upload_with_fit(abs_path: Path, print_size_str: str) -> tuple:
    """Prepare image for a specific print size and upload it.

    Returns (image_id, fit_info_dict).
    fit_info_dict is logged to the ledger ``image_fit`` key.
    """
    upload_path = str(abs_path)
    fit_info: Dict[str, Any] = {"original": str(abs_path), "print_size": print_size_str}

    if _IMAGE_FIT_AVAILABLE:
        try:
            result = image_fit.prepare_for_print(str(abs_path), print_size_str)
            if result is None:
                raise RuntimeError(
                    f"image_fit.prepare_for_print returned None for {abs_path} @ {print_size_str}"
                )
            tmp_path, fit_meta = result
            upload_path = tmp_path
            fit_info.update(fit_meta)
        except Exception as exc:
            print(f"[warn] image_fit failed for {abs_path} @ {print_size_str}: {exc} — using original")
            fit_info["warning"] = str(exc)
    else:
        fit_info["warning"] = "image_fit module not available — uploading original without fit"

    upload_resp = api.upload_image(upload_path)
    return upload_resp["id"], fit_info


def cmd_list_shipping(_args) -> int:
    """Print Etsy shipping template IDs by reading existing published products."""
    cfg = load_config()
    shop_id = cfg.get("shop_id") or api.get_shop_id()
    print(f"[shipping] reading shipping info from existing products in shop {shop_id}...")
    results = api.get_etsy_shipping_profiles(int(shop_id))
    print(json.dumps(results, indent=2))
    ids = {r["shipping_template_id"] for r in results if r.get("shipping_template_id")}
    if ids:
        print(f"\nFound shipping_template_id(s): {ids}")
        print("Set one as 'shipping.etsy_shipping_profile_id' in printify_config.yaml")
    else:
        print("\nNo shipping_template_id found on existing products.")
        print("These products may not have been published to Etsy yet,")
        print("or the shipping template was set manually inside Etsy.")
        print("Check your Etsy shop's Shipping settings for the template ID.")
    return 0


def cmd_publish_existing(args) -> int:
    """Publish (push to Etsy) an already-created Printify product by ID.

    Useful for retrying products that were created but failed to publish
    (e.g. missing shipping template). Does NOT create a new product.
    """
    cfg = load_config()
    shop_id = cfg.get("shop_id") or api.get_shop_id()
    shipping_profile_id: Optional[int] = (
        cfg.get("shipping", {}).get("etsy_shipping_profile_id") or None
    )
    if shipping_profile_id is not None:
        try:
            shipping_profile_id = int(shipping_profile_id)
        except (ValueError, TypeError):
            shipping_profile_id = None

    product_id: str = args.publish_existing[0]
    kind: str = args.publish_existing[1] if len(args.publish_existing) > 1 else "unknown"

    print(f"[publish-existing] shop={shop_id} product_id={product_id} kind={kind}")
    if shipping_profile_id:
        print(f"[publish-existing] including shipping_profile_id={shipping_profile_id}")
    else:
        print("[publish-existing] WARNING: no etsy_shipping_profile_id in config — "
              "publish may fail. Run --list-shipping to find the right ID.")

    if not args.live:
        print("[dry-run] Would call: POST /shops/{shop_id}/products/{product_id}/publish.json")
        print(f"[dry-run] shipping_profile_id={shipping_profile_id}")
        return 0

    result = api.publish_product(
        int(shop_id),
        product_id,
        shipping_profile_id=shipping_profile_id,
    )
    print(f"[publish-existing] result: {json.dumps(result, indent=2)}")
    return 0


def cmd_publish(args) -> int:
    cfg = load_config()
    if not cfg.get("products", {}).get("poster", {}).get("blueprint_id"):
        print("ERROR: printify_config.yaml not bootstrapped. Run with --bootstrap-config first.",
              file=sys.stderr)
        return 2

    ledger = load_ledger()
    feed = load_products_feed()

    if args.image:
        rel = str(Path(args.image).resolve().relative_to(GALLERY_DIR))
        targets = [rel]
    else:
        targets = collect_unpublished(ledger)

    if not targets:
        print("Nothing to publish — ledger covers all gallery images.")
        return 0

    shipping_profile_id: Optional[int] = (
        cfg.get("shipping", {}).get("etsy_shipping_profile_id") or None
    )
    if shipping_profile_id is not None:
        try:
            shipping_profile_id = int(shipping_profile_id)
        except (ValueError, TypeError):
            shipping_profile_id = None

    for rel in targets:
        if ledger_key(rel) in ledger.get("entries", {}):
            print(f"[skip] {rel} already in ledger")
            continue
        abs_check = GALLERY_DIR / rel
        if _needs_approval(abs_check):
            print(f"[gate] {rel} — Flux output without {Path(rel).name}.approved marker, skipping")
            continue
        entry = find_feed_entry(rel, feed)
        if entry is None:
            print(f"[warn] {rel} not in products.json — skipping")
            continue
        plan = plan_publish(rel, entry, cfg)
        print("\n" + "=" * 72)
        print(f"PLAN: {rel}")
        print(json.dumps(plan, indent=2))

        if not args.live:
            continue

        # ---------- LIVE PATH ----------
        # Upload source defaults to the gallery file, but --print-file lets a
        # high-res master (kept outside git) feed Printify while the gallery
        # holds only a small web copy.
        if args.print_file:
            abs_path = Path(args.print_file).resolve()
            if not abs_path.exists():
                print(f"[error] --print-file not found: {abs_path}", file=sys.stderr)
                return 2
            print(f"[print-file] uploading master {abs_path.name} (not the gallery web copy)")
        else:
            abs_path = GALLERY_DIR / rel

        # Use the first print size across all product kinds for the shared upload.
        # Each product kind may get a differently-fitted version; we upload once
        # per kind's representative size to keep it simple.
        product_results = []
        fit_log: Dict[str, Any] = {}

        for prod_plan in plan["products"]:
            if prod_plan.get("status", "").startswith("SKIPPED"):
                continue
            kind = prod_plan["kind"]
            # Pick the largest variant size as the representative fit target.
            sizes_for_kind = {"wrapped_canvas": CANVAS_SIZES, "mug": MUG_SIZES}.get(kind, POSTER_SIZES)
            rep_size = sizes_for_kind[-1]  # e.g. "24x36" or "15oz_mug"

            image_id, fit_info = _upload_with_fit(abs_path, rep_size)
            fit_log[kind] = fit_info

            payload = {
                "title": prod_plan["title"],
                "description": prod_plan["description"],
                "blueprint_id": prod_plan["blueprint_id"],
                "print_provider_id": prod_plan["print_provider_id"],
                "tags": prod_plan["tags"],
                "variants": prod_plan["variants"],
                "print_areas": [{
                    "variant_ids": [v["id"] for v in prod_plan["variants"]],
                    "placeholders": [{
                        "position": "front",
                        "images": [{
                            "id": image_id,
                            "x": 0.5, "y": 0.5, "scale": 1.0, "angle": 0,
                        }],
                    }],
                }],
            }
            if shipping_profile_id:
                payload["shipping_template_id"] = shipping_profile_id
            created = api.create_product(cfg["shop_id"], payload)
            if args.draft:
                print(f"  [draft] created {kind} product {created['id']} — "
                      f"NOT pushed to Etsy (review in Printify dashboard)")
            else:
                api.publish_product(
                    cfg["shop_id"],
                    created["id"],
                    shipping_profile_id=shipping_profile_id,
                )
            product_results.append({
                "kind": kind,
                "product_id": created["id"],
                "external_url": (created.get("external") or {}).get("handle"),
                "variants": prod_plan["variants"],
                "image_id": image_id,
                "draft": bool(args.draft),
            })

        ledger.setdefault("entries", {})[ledger_key(rel)] = {
            "published_at": datetime.now(timezone.utc).isoformat(),
            "products": product_results,
            "image_fit": fit_log,
        }
        write_ledger(ledger)

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Printify publisher")
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="Default. Print plan without API writes.")
    ap.add_argument("--live", action="store_true",
                    help="Actually create + publish products. Required for real writes.")
    ap.add_argument("--draft", action="store_true",
                    help="With --live: create products in Printify but DO NOT push to Etsy. "
                         "Leaves them as drafts for manual review/publish in the Printify dashboard.")
    ap.add_argument("--image", type=str, default=None,
                    help="Target a single image (absolute or gallery-relative path). "
                         "Identifies the product (metadata + ledger key).")
    ap.add_argument("--print-file", type=str, default=None,
                    help="Override the upload source with a high-res print master "
                         "(outside git). Use when the gallery holds a small web copy "
                         "but Printify needs the full 300-DPI master. Requires --image.")
    ap.add_argument("--bootstrap-config", action="store_true",
                    help="Inspect existing shop, derive config, write printify_config.yaml.")
    ap.add_argument("--list-shipping", action="store_true",
                    help="List Etsy shipping profiles for the configured shop and exit.")
    ap.add_argument(
        "--publish-existing",
        nargs="+",
        metavar=("PRODUCT_ID", "KIND"),
        help=(
            "Publish (push to Etsy) an already-created Printify product by ID. "
            "Usage: --publish-existing <product_id> [kind]. "
            "Requires --live to actually fire; dry-run by default."
        ),
    )
    args = ap.parse_args(argv)

    if args.bootstrap_config:
        return cmd_bootstrap_config(args)
    if args.list_shipping:
        return cmd_list_shipping(args)
    if args.publish_existing:
        return cmd_publish_existing(args)
    return cmd_publish(args)


if __name__ == "__main__":
    sys.exit(main())
