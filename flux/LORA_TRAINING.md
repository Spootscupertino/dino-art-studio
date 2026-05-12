# LoRA Training — Replicate Workflow

Train a Flux LoRA on Replicate's `ostris/flux-dev-lora-trainer`, then serve it through `flux/generate.py`.

## Workflow

### 1. Curate and caption refs

Use `reference.py` (at repo root) to intake reference images. Each one lands in `assets/gallery/flux/training_refs/` with a matching `.txt` caption (`"a photo of <species>, <anatomy notes>"`) and is logged to `winners.json` with `source_type="reference"`.

Aim for **5–10 images per species**, mixed sources (paleoart, museum, living analog).

### 2. Bundle into a training zip

```bash
python3 flux/export_dataset.py
```
Produces `flux/datasets/<name>_dataset.zip` (image + caption pairs side-by-side).

### 3. Upload to Replicate's trainer

In the Replicate web UI:

1. Open `ostris/flux-dev-lora-trainer`.
2. Upload the zip from step 2.
3. Set `trigger_word` (e.g. `trex_v1`). This must be unique per LoRA — used to invoke it in prompts.
4. Set hyperparameters. Reasonable starting recipe:
   - rank: 16
   - learning rate: 1e-4 (or 5e-5 if dataset < 8 images)
   - epochs: 1000 steps total, or 50–100 epochs whichever is smaller
   - batch size: 1
5. Run. ~$1–3 per run, ~20–40 min for small datasets.

### 4. Archive the weights and snapshot the config

After training succeeds:

1. Download `.safetensors` from the Replicate run page → `flux/loras/<name>.safetensors` (gitignored, but kept locally for backup).
2. Save the exact recipe as `flux/loras/<name>.config.yaml`. See `flux/loras/trex_v1.config.yaml` for the format.
3. Note the **training ID** and **version hash** from the run page.

### 5. Register the LoRA

Add an entry to `flux/loras/registry.json`:

```json
"<name>": {
  "replicate_owner": "<your_replicate_username>",
  "replicate_model": "<model_slug>",
  "version": "<version_hash>",
  "trigger_word": "<name>",
  "trained_on": "YYYY-MM-DD",
  "training_id": "<replicate_training_id>"
}
```

Get the version hash via:
```bash
curl -s -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
  https://api.replicate.com/v1/models/<owner>/<slug> | jq .latest_version.id
```

### 6. Validate with A/B test

```bash
python3 flux/ab_test_replicate.py
```

(Adjust `SEEDS`, `BASE_PROMPT`, and `LORA_VERSION` for the new LoRA.)

Score each pair on the 5-category anatomy rubric (1–5 each, max 25). Promotion threshold:

- **Mean Δ ≥ 2.0** (LoRA mean − baseline mean)
- **Win rate ≥ 80%** (LoRA wins ≥ 4/5)

Record `ab_test_winrate` and `ab_test_mean_delta` in the registry entry.

### 7. Use it

```bash
python3 flux/generate.py --prompt "<prompt>" --seed <n> --lora <name> --output <path>
```

`generate.py` auto-prepends the trigger word if it isn't already in the prompt.

## Why Replicate (not local ai-toolkit)

- The M1 mini can't train Flux LoRAs in reasonable time / memory.
- One coherent stack: training and inference both run on Replicate's Flux-dev.
- Cost is trivial: a full LoRA cycle (train + validate + 10 hero generations) lands under $5.
- The `.safetensors` is archived locally, so if Replicate ever disappears we still own the weights.
