#!/usr/bin/env python3
"""
Generate a single Flux-dev image via Replicate.

Without --lora: hits the public black-forest-labs/flux-dev model.
With --lora <name>: looks up version + trigger_word in flux/loras/registry.json
and POSTs to /v1/predictions with that version.

Writes the PNG + a sidecar JSON next to it.

Example:
  python3 flux/generate.py \
    --prompt "Tyrannosaurus rex hunting in a misty river delta" \
    --seed 99 \
    --lora trex_v1 \
    --output /tmp/smoke.png
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = Path("/Users/ericeldridge/dino_art/.env")
REGISTRY_PATH = Path(__file__).resolve().parent / "loras" / "registry.json"

BASELINE_MODEL = "black-forest-labs/flux-dev"


def load_token() -> str:
    if os.environ.get("REPLICATE_API_TOKEN"):
        return os.environ["REPLICATE_API_TOKEN"]
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.startswith("REPLICATE_API_TOKEN="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    return v
    sys.exit("REPLICATE_API_TOKEN not found in env or .env")


def load_lora(name: str) -> dict:
    if not REGISTRY_PATH.exists():
        sys.exit(f"LoRA registry missing: {REGISTRY_PATH}")
    registry = json.loads(REGISTRY_PATH.read_text())
    if name not in registry:
        available = ", ".join(registry.keys()) or "(none)"
        sys.exit(f"Unknown LoRA '{name}'. Available: {available}")
    return registry[name]


def api(method: str, url: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    for _ in range(8):
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
                print(f"  429 throttled, sleeping {wait}s…", flush=True)
                time.sleep(wait)
                continue
            sys.exit(f"HTTP {e.code} on {method} {url}: {e.read().decode()}")
    sys.exit(f"Exhausted retries on {method} {url}")


def create_prediction(token: str, lora: dict | None, prompt: str, inp: dict) -> tuple[str, str]:
    """Returns (prediction_id, target_label)."""
    if lora is None:
        url = f"https://api.replicate.com/v1/models/{BASELINE_MODEL}/predictions"
        body = {"input": {**inp, "prompt": prompt}}
        target = f"model:{BASELINE_MODEL}"
    else:
        url = "https://api.replicate.com/v1/predictions"
        body = {"version": lora["version"], "input": {**inp, "prompt": prompt}}
        target = f"version:{lora['version']}"
    res = api("POST", url, token, body)
    return res["id"], target


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


def main():
    p = argparse.ArgumentParser(description="Generate a single Flux-dev image via Replicate.")
    p.add_argument("--prompt", required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--lora", default=None, help="LoRA name from flux/loras/registry.json")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--aspect-ratio", default="1:1")
    p.add_argument("--steps", type=int, default=28)
    p.add_argument("--guidance", type=float, default=3.0)
    args = p.parse_args()

    token = load_token()
    lora = load_lora(args.lora) if args.lora else None

    prompt = args.prompt
    if lora and lora.get("trigger_word") and lora["trigger_word"] not in prompt:
        prompt = f"{lora['trigger_word']} {prompt}"

    inp = {
        "aspect_ratio": args.aspect_ratio,
        "num_inference_steps": args.steps,
        "guidance_scale": args.guidance,
        "output_format": "png",
        "megapixels": "1",
        "seed": args.seed,
    }

    label = f"lora={args.lora}" if args.lora else "baseline"
    print(f"Generating ({label}, seed={args.seed})…", flush=True)
    pred_id, target = create_prediction(token, lora, prompt, inp)
    res = wait_for(token, pred_id)
    if res["status"] != "succeeded":
        sys.exit(f"Prediction {pred_id} {res['status']}: {res.get('error')}")

    urls = res["output"] if isinstance(res["output"], list) else [res["output"]]
    download(urls[0], args.output)

    sidecar = {
        "prompt": prompt,
        "seed": args.seed,
        "lora": args.lora,
        "target": target,
        "input": inp,
        "prediction_id": pred_id,
        "output_url": urls[0],
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    args.output.with_suffix(args.output.suffix + ".json").write_text(json.dumps(sidecar, indent=2))
    print(f"✓ {args.output}")


if __name__ == "__main__":
    main()
