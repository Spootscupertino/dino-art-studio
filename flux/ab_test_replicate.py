#!/usr/bin/env python3
"""
Replicate A/B test for trex_v3 LoRA vs trex_v2 (the prior best LoRA).

For each seed, runs two predictions:
  - challenger: spootscupertino/trex_v3 (trigger word "trex_v3")
  - champion:   spootscupertino/trex_v2 (trigger word "trex_v2")

Same seed in both paths so the only variable is the LoRA.

Mouth-feature-biased base prompt — v3's training corpus emphasizes
biomech_mouth/, corrected_mj/, and extremes_macro/, so we should validate the
intended improvement against the same anatomical focus.

Outputs land in assets/gallery/flux/ab_tests/trex_v3/{champion_v2,challenger_v3}/seed_XXXX.{png,json}

Before running: fill CHALLENGER_VERSION below with the version hash returned
by Replicate after the trex_v3 training run completes.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = Path("/Users/ericeldridge/dino_art/.env")
REGISTRY_PATH = REPO_ROOT / "flux" / "loras" / "registry.json"
OUT_ROOT = REPO_ROOT / "assets" / "gallery" / "flux" / "ab_tests" / "trex_v3"

SEEDS = [42, 123, 777, 1024, 2025]
BASE_PROMPT = (
    "Tyrannosaurus rex roaring at low golden hour light, three-quarter portrait, "
    "open lipped mouth with recurved serrated teeth visible, exposed gumline, "
    "binocular forward-facing eyes, scaly hide with fine integument texture, "
    "photorealistic"
)


def _load_registry():
    return json.loads(REGISTRY_PATH.read_text())


_REG = _load_registry()
CHAMPION_VERSION = _REG["trex_v2"]["version"]
CHAMPION_TRIGGER = _REG["trex_v2"]["trigger_word"]
# Fill in after v3 training finishes — read it back out of the registry.
CHALLENGER_VERSION = _REG.get("trex_v3", {}).get("version", "")
CHALLENGER_TRIGGER = _REG.get("trex_v3", {}).get("trigger_word", "trex_v3")

CHAMPION_PROMPT = f"{CHAMPION_TRIGGER} {BASE_PROMPT}"
CHALLENGER_PROMPT = f"{CHALLENGER_TRIGGER} {BASE_PROMPT}"

COMMON_INPUT = {
    "aspect_ratio": "1:1",
    "num_inference_steps": 28,
    "guidance_scale": 3.0,
    "output_format": "png",
    "megapixels": "1",
}


def load_token() -> str:
    if "REPLICATE_API_TOKEN" in os.environ and os.environ["REPLICATE_API_TOKEN"]:
        return os.environ["REPLICATE_API_TOKEN"]
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.startswith("REPLICATE_API_TOKEN="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    return v
    sys.exit("REPLICATE_API_TOKEN not found in env or .env")


def api(method: str, url: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(8):
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                try:
                    payload = json.loads(e.read())
                    wait = int(payload.get("retry_after", 10)) + 2
                except Exception:
                    wait = 15
                print(f"    429 throttled, sleeping {wait}s…", flush=True)
                time.sleep(wait)
                continue
            sys.exit(f"HTTP {e.code} on {method} {url}: {e.read().decode()}")
    sys.exit(f"Exhausted retries on {method} {url}")


def create_prediction(token: str, target: str, prompt: str, seed: int) -> str:
    """target is either 'model:<owner>/<name>' or 'version:<hash>'."""
    inp = {**COMMON_INPUT, "prompt": prompt, "seed": seed}
    if target.startswith("model:"):
        model = target.split(":", 1)[1]
        url = f"https://api.replicate.com/v1/models/{model}/predictions"
        body = {"input": inp}
    elif target.startswith("version:"):
        url = "https://api.replicate.com/v1/predictions"
        body = {"version": target.split(":", 1)[1], "input": inp}
    else:
        sys.exit(f"bad target {target}")
    res = api("POST", url, token, body)
    return res["id"]


def wait_for(token: str, pred_id: str, timeout_s: int = 300) -> dict:
    start = time.time()
    url = f"https://api.replicate.com/v1/predictions/{pred_id}"
    while time.time() - start < timeout_s:
        res = api("GET", url, token)
        if res["status"] in ("succeeded", "failed", "canceled"):
            return res
        time.sleep(3)
    sys.exit(f"Timeout waiting on prediction {pred_id}")


def download(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)


def run_pair(token: str, seed: int):
    print(f"\n── seed {seed} ──")
    for label, target, prompt in [
        ("champion_v2", f"version:{CHAMPION_VERSION}", CHAMPION_PROMPT),
        ("challenger_v3", f"version:{CHALLENGER_VERSION}", CHALLENGER_PROMPT),
    ]:
        out_png = OUT_ROOT / label / f"seed_{seed:04d}.png"
        out_json = out_png.with_suffix(".json")
        if out_png.exists():
            print(f"  [{label}] already exists, skipping")
            continue
        print(f"  [{label}] creating prediction…", flush=True)
        pid = create_prediction(token, target, prompt, seed)
        res = wait_for(token, pid)
        if res["status"] != "succeeded":
            print(f"  [{label}] FAILED: {res.get('error')}")
            continue
        urls = res["output"] if isinstance(res["output"], list) else [res["output"]]
        download(urls[0], out_png)
        sidecar = {
            "seed": seed,
            "label": label,
            "target": target,
            "prompt": prompt,
            "input": {**COMMON_INPUT, "prompt": prompt, "seed": seed},
            "prediction_id": pid,
            "output_url": urls[0],
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        out_json.write_text(json.dumps(sidecar, indent=2))
        print(f"  [{label}] saved {out_png.relative_to(REPO_ROOT)}")


def main():
    if not CHALLENGER_VERSION:
        sys.exit(
            "trex_v3 version not set yet. After the Replicate training run "
            "finishes, add the version hash to flux/loras/registry.json under "
            '"trex_v3" and re-run.'
        )
    token = load_token()
    print(f"Token loaded ({token[:6]}…), {len(SEEDS)} pairs to run")
    print(f"  champion : trex_v2  ({CHAMPION_VERSION[:12]}…)")
    print(f"  challenger: trex_v3 ({CHALLENGER_VERSION[:12]}…)")
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    for seed in SEEDS:
        run_pair(token, seed)
    print("\n✓ All pairs done")


if __name__ == "__main__":
    main()
