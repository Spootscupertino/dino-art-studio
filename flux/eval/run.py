#!/usr/bin/env python3
"""
Frozen eval harness for T-rex LoRA comparison.

Generates each prompt in flux/eval/prompts.json for every specified LoRA
(plus the baseline) at fixed seeds, writing outputs to:
  assets/gallery/flux/evals/<lora_name>/<prompt_id>_seed_<NNNN>.{png,json}

Usage:
  python3 flux/eval/run.py                          # baseline + all registered LoRAs
  python3 flux/eval/run.py --lora trex_v3           # specific LoRA only
  python3 flux/eval/run.py --lora baseline,trex_v1  # comma-separated list

Seeds are frozen per prompt (stored in prompts.json). Never change them — the
whole point is identical seeds across LoRA versions forever.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = Path("/Users/ericeldridge/dino_art/.env")
REGISTRY_PATH = REPO_ROOT / "flux" / "loras" / "registry.json"
PROMPTS_PATH = Path(__file__).parent / "prompts.json"
OUT_ROOT = REPO_ROOT / "assets" / "gallery" / "flux" / "evals"

BASELINE_MODEL = "black-forest-labs/flux-dev"
COMMON_INPUT = {
    "aspect_ratio": "1:1",
    "num_inference_steps": 28,
    "guidance_scale": 3.0,
    "output_format": "png",
    "megapixels": "1",
}


def load_token() -> str:
    if os.environ.get("REPLICATE_API_TOKEN"):
        return os.environ["REPLICATE_API_TOKEN"]
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.startswith("REPLICATE_API_TOKEN="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    return v
    sys.exit("REPLICATE_API_TOKEN not found")


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text())


def load_prompts() -> list[dict]:
    return json.loads(PROMPTS_PATH.read_text())


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
                    wait = int(json.loads(e.read()).get("retry_after", 10)) + 2
                except Exception:
                    wait = 15
                print(f"    429 throttled, sleeping {wait}s…", flush=True)
                time.sleep(wait)
                continue
            sys.exit(f"HTTP {e.code} on {method} {url}: {e.read().decode()}")
    sys.exit(f"Exhausted retries on {method} {url}")


def create_prediction(token: str, target: str, prompt: str, seed: int) -> str:
    inp = {**COMMON_INPUT, "prompt": prompt, "seed": seed}
    if target.startswith("model:"):
        model = target.split(":", 1)[1]
        url = f"https://api.replicate.com/v1/models/{model}/predictions"
        body = {"input": inp}
    else:
        url = "https://api.replicate.com/v1/predictions"
        body = {"version": target.split(":", 1)[1], "input": inp}
    return api("POST", url, token, body)["id"]


def wait_for(token: str, pred_id: str, timeout_s: int = 300) -> dict:
    start = time.time()
    url = f"https://api.replicate.com/v1/predictions/{pred_id}"
    while time.time() - start < timeout_s:
        res = api("GET", url, token)
        if res["status"] in ("succeeded", "failed", "canceled"):
            return res
        time.sleep(3)
    sys.exit(f"Timeout waiting on {pred_id}")


def download(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)


def resolve_loras(requested: list[str], registry: dict) -> list[dict]:
    """Return list of {name, target, trigger} dicts."""
    loras = []
    for name in requested:
        if name == "baseline":
            loras.append({"name": "baseline", "target": f"model:{BASELINE_MODEL}", "trigger": ""})
        elif name in registry:
            rec = registry[name]
            loras.append({
                "name": name,
                "target": f"version:{rec['version']}",
                "trigger": rec["trigger_word"],
            })
        else:
            sys.exit(f"Unknown LoRA '{name}'. Registered: {list(registry.keys())}")
    return loras


def build_prompt(template: str, trigger: str) -> str:
    return template.replace("trex_TRIGGER", trigger).strip() if trigger else template.replace("trex_TRIGGER ", "").strip()


def run_eval(token: str, lora: dict, prompts: list[dict]):
    name = lora["name"]
    print(f"\n{'='*50}")
    print(f"LoRA: {name}  ({lora['target'][:30]}…)")
    print(f"{'='*50}")
    for p in prompts:
        out_png = OUT_ROOT / name / f"{p['id']}_seed_{p['seed']:04d}.png"
        out_json = out_png.with_suffix(".json")
        if out_png.exists():
            print(f"  [{p['id']}] already exists, skipping")
            continue
        prompt = build_prompt(p["prompt"], lora["trigger"])
        print(f"  [{p['id']}] seed={p['seed']} generating…", flush=True)
        pid = create_prediction(token, lora["target"], prompt, p["seed"])
        res = wait_for(token, pid)
        if res["status"] != "succeeded":
            print(f"  [{p['id']}] FAILED: {res.get('error')}")
            continue
        urls = res["output"] if isinstance(res["output"], list) else [res["output"]]
        download(urls[0], out_png)
        sidecar = {
            "lora": name,
            "prompt_id": p["id"],
            "seed": p["seed"],
            "prompt": prompt,
            "target": lora["target"],
            "rubric_focus": p["rubric_focus"],
            "prediction_id": pid,
            "output_url": urls[0],
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        out_json.write_text(json.dumps(sidecar, indent=2))
        print(f"  [{p['id']}] saved {out_png.relative_to(REPO_ROOT)}")


def main():
    parser = argparse.ArgumentParser(description="Run frozen eval across LoRAs")
    parser.add_argument("--lora", help="Comma-separated LoRA names (default: baseline + all registered)")
    args = parser.parse_args()

    registry = load_registry()
    prompts = load_prompts()
    token = load_token()

    if args.lora:
        requested = [x.strip() for x in args.lora.split(",")]
    else:
        requested = ["baseline"] + list(registry.keys())

    loras = resolve_loras(requested, registry)
    print(f"Eval: {len(prompts)} prompts × {len(loras)} LoRAs = {len(prompts)*len(loras)} predictions")
    for lora in loras:
        run_eval(token, lora, prompts)
    print("\n✓ Eval complete")


if __name__ == "__main__":
    main()
