# Flux Domain — Replicate-Flux Generation

Owner: `prompt-crafter`

## What this domain does

Generate photorealistic dinosaur images via **Flux-dev hosted on Replicate**, optionally with a trained LoRA. Also prepares datasets for cloud LoRA training on Replicate's `ostris/flux-dev-lora-trainer`.

**All inference is cloud.** No local model weights, no MPS / bfloat16 / ComfyUI / ControlNet. The earlier local SDXL stack was retired in Tightening 5 — local SDXL cannot load Flux LoRAs (different architecture), so one coherent cloud stack replaces two incompatible halves.

## What lives here

| File | Purpose |
|---|---|
| `generate.py` | Single-image CLI. Calls Replicate's Flux-dev model (baseline) or a trained LoRA version. |
| `ab_test_replicate.py` | 5-seed A/B harness: baseline vs LoRA, same seeds both paths. Used to validate every new LoRA. |
| `export_dataset.py` | Bundles `assets/gallery/flux/training_refs/` (image + caption pairs) into a zip for upload to Replicate's trainer. |
| `ingest_training_drops.py` | Helper for dropping reference images into the training pool. |
| `loras/registry.json` | Source of truth for trained LoRAs: name → Replicate version hash, trigger word, A/B stats. |
| `loras/<name>.config.yaml` | Per-LoRA training config snapshot (recipe, hyperparams). |
| `loras/<name>.safetensors` | LoRA weights archived locally (gitignored; Replicate hosts the canonical copy). |
| `datasets/` | Zipped training datasets ready for upload. |

## Cost

- Generation: ~$0.03–0.05 per image
- LoRA training run: ~$1–3 per run on `ostris/flux-dev-lora-trainer`
- Expected steady-state: $5–15/month

## CLI

**Generate a single image:**
```bash
python3 flux/generate.py \
  --prompt "Tyrannosaurus rex hunting in a misty river delta" \
  --seed 42 \
  --lora trex_v1 \
  --output assets/gallery/flux/trex_river_001.png
```
Optional flags: `--aspect-ratio 1:1`, `--steps 28`, `--guidance 3.0`. Omit `--lora` for baseline Flux-dev.

**A/B validate a new LoRA:**
```bash
python3 flux/ab_test_replicate.py
```
Runs 5 seeds × {baseline, LoRA} and writes outputs to `assets/gallery/flux/ab_tests/<lora_name>/`.

## Solved gotchas

1. **Rate limiting** (accounts with <$5 credit): 6 req/min, burst 1. 429 responses include `retry_after`. Both scripts retry automatically.
2. **Private trained models return 404** on `/v1/models/<owner>/<name>/predictions`. POST to `/v1/predictions` with a `version` field instead. Registry stores the version hash.
3. **Version hash discovery:** `GET /v1/models/<owner>/<name>` → `latest_version.id`.

## Contract with other domains

**Input:**
- Prompts from `generate_prompt.py` (root) or any text source.
- Reference images in `assets/gallery/flux/training_refs/` (curated by `reference.py`).

**Output:**
- Generated images: any path; pipeline convention is `assets/gallery/flux/<category>/*.png`.
- Sidecar `<image>.png.json` with prompt, seed, prediction ID, output URL, timestamp.

## Adding a new LoRA

See `flux/LORA_TRAINING.md` for the full workflow.
