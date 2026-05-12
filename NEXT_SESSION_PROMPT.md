# Next Session Prompt — Tightening 5: Commit to Replicate-Flux, Retire Local SDXL

## Status Coming In

**Tightening 4 (A/B validation) is complete and the throwaway LoRA succeeded.**

- LoRA: `flux/loras/trex_v1.safetensors` (164 MB, trained on Replicate's `ostris/flux-dev-lora-trainer`)
- Replicate model: `spootscupertino/trex-v1` (private), version `59d8095859aef81024b314d6be18a466764c295fde2c3baf9995f446a2b15873`
- A/B script: `flux/ab_test_replicate.py` — proven working (handles 429 throttling, private-version endpoint)
- Output images: `assets/gallery/flux/ab_tests/trex_v1/{with,without}_lora/seed_{0042,0123,0777,1024,2025}.png` (+ sidecar JSON)

**Scores (5 pairs, 5-category anatomy rubric, 1–5 each, max 25):**

| Seed | Without LoRA | With LoRA | Δ |
|------|---|---|---|
| 42   | 12 | 20 | +8 |
| 123  | 12 | 18 | +6 |
| 777  | 13 | 18 | +5 |
| 1024 | 12 | 21 | +9 |
| 2025 | 13 | 21 | +8 |
| **Mean** | **12.4** | **19.6** | **+7.2** |

- Win rate: **5/5 (100%)**
- Plan threshold for go/no-go: mean Δ ≥ 2.0, win rate ≥ 72%. Both blown past.
- Visual pattern: vanilla Flux = upright kangaroo, screaming mouth, tail in water, 3-finger hands. With LoRA = horizontal spine, lifted tail, calmer mouth, clear 2-finger hands. Anatomy thesis is showing up in the model.

## The Architectural Decision (already made — execute it)

**Commit to Replicate-Flux for both training AND generation. Retire the local SDXL generator entirely.**

Why: training pipeline already lives on Replicate (Flux-dev LoRA trainer); the LoRA we just validated is a Flux LoRA; local SDXL cannot load Flux LoRAs (different architectures). The local generator was a memory-driven compromise from before training existed and has no path to consume its own training output. One coherent stack > two incompatible halves.

**Cost reality check:** ~$0.03–0.05 per Replicate image. At expected volume this is $5–15/month tops. Trivial vs. M1 thrash.

## What You're Doing Today

Clean the repo so the Replicate-Flux stack is the *only* generation path. Every file, doc, and reference to local Flux-dev or local SDXL gets deleted or rewritten. Repo must be coherent end-to-end when you finish — someone reading `flux/CLAUDE.md` should see exactly what's actually true.

## Step-by-Step

### 1. Delete dead files

```bash
git rm flux/generate_image.py          # SDXL generator, no LoRA support, doesn't fit
git rm flux/comfyui_server.py          # FastAPI wrapper around the SDXL generator
git rm flux/train_lora.py              # Non-functional placeholder ("Phase C roadmap")
git rm flux/SETUP.md                   # SDXL/Flux-dev local setup, obsolete
git rm flux/PHASE_B.md                 # Historical, no longer load-bearing
git rm "Launch Dino Generator.command" # Launcher for the retired UI
git rm -r flux/DinoGenerator.app       # macOS app wrapper for same UI
```

Verify nothing else imports any of these before deletion:
```bash
grep -rn "from flux.generate_image\|import flux.generate_image\|from flux.train_lora\|from flux.comfyui_server" .
grep -rn "Launch Dino Generator\|DinoGenerator.app" .
```

If anything shows up, deal with it before deleting (probably also dead, but verify).

### 2. Create `flux/generate.py` (the new single-image generator)

This is the daily-driver replacement for `generate_image.py`. Refactor `flux/ab_test_replicate.py`:
- Extract the Replicate API client (token loading, `api()` retry loop, `create_prediction()`, `wait_for()`, `download()`) into shared functions OR keep them in one file for simplicity
- Single-image CLI: `--prompt`, `--seed`, `--lora <name>` (looks up `flux/loras/<name>.safetensors` for sidecar metadata; the actual weights live on Replicate via the trained model version), `--output <path>`, `--aspect-ratio`, `--steps`, `--guidance`
- If `--lora trex_v1`: use version `59d8095859aef81024b314d6be18a466764c295fde2c3baf9995f446a2b15873`. Future LoRAs need a registry — see step 3.
- Without `--lora`: hits `black-forest-labs/flux-dev` model endpoint
- Writes PNG + sidecar JSON next to it (same format as ab_test_replicate.py)

Don't over-engineer. Mirror `flux/ab_test_replicate.py`'s style.

### 3. Add a tiny LoRA registry

Create `flux/loras/registry.json`:
```json
{
  "trex_v1": {
    "replicate_owner": "spootscupertino",
    "replicate_model": "trex-v1",
    "version": "59d8095859aef81024b314d6be18a466764c295fde2c3baf9995f446a2b15873",
    "trigger_word": "trex_v1",
    "trained_on": "2026-05-11",
    "training_id": "wad5pnmbb5rmy0cy2z29jefvqw",
    "ab_test_winrate": "5/5",
    "ab_test_mean_delta": 7.2
  }
}
```

`flux/generate.py` reads this for `--lora <name>` lookups. Adding a future LoRA = one new JSON entry, no code change.

### 4. Slim `flux/requirements.txt`

Current file has diffusers, torch (MPS), accelerate, peft, fastapi, uvicorn, websockets — all for the retired stack. After cleanup, the only runtime needs are Python stdlib (urllib for Replicate REST). Reduce to:

```
# No third-party deps needed at runtime — Replicate calls go through urllib.
# Dev/test only:
ruff  # if you use it
```

Or just delete the file. Up to you.

### 5. Rewrite `flux/CLAUDE.md`

Replace entirely. Should describe the actual stack:

- Owner: `prompt-crafter`
- Generation: Replicate-Flux (`black-forest-labs/flux-dev` for vanilla, `spootscupertino/trex-v1:<version>` for trex_v1 LoRA). No local generation.
- Training: Replicate (`ostris/flux-dev-lora-trainer`). Submit via the web UI for now; dataset prep is `flux/export_dataset.py`.
- Files: `generate.py` (single-image CLI), `ab_test_replicate.py` (A/B validation harness for new LoRAs), `export_dataset.py` (dataset prep), `loras/registry.json` (LoRA catalog), `loras/*.safetensors` (downloaded weights, kept for archival/reference even though Replicate runs from its own copy)
- No more talk of ComfyUI, ControlNet, MPS, bfloat16, 24GB models, M1 optimization
- Cost: ~$0.03–0.05/image, ~$1–3/training run

### 6. Rewrite `flux/LORA_TRAINING.md`

Single workflow now:
1. Curate references (paleoart, skeletals, wildlife analogs)
2. Caption them
3. Zip them, `flux/export_dataset.py` if helpful
4. Upload to Replicate `ostris/flux-dev-lora-trainer` via the web UI
5. Set trigger word, set epochs/steps/learning rate, kick off
6. Wait ~10–20 min, download `.safetensors` for archival
7. Add entry to `flux/loras/registry.json`
8. Validate with `python3 flux/ab_test_replicate.py` (5 pairs minimum) before treating it as a "real" LoRA
9. If win rate ≥ 80%, promote; else iterate

Cut all ai-toolkit / local M1 / Phase C content.

### 7. Update root `CLAUDE.md`

The flux/ row in the domain table currently says:
> Local Flux-dev generation — M1-optimized image generation with LoRA fine-tuning + branded ComfyUI.

Rewrite to:
> Replicate-Flux generation — cloud Flux-dev image generation + LoRA inference, plus dataset prep for `ostris/flux-dev-lora-trainer` training.

Also update the "Generation pipeline" section under "Cross-domain contracts" to reflect Replicate calls instead of local generation.

### 8. Update `RECAP.md`

Append a Tightening 4 section with:
- A/B test result (5/5 win, +7.2 mean delta)
- Architectural decision (committed to Replicate-Flux)
- What was deleted in Tightening 5

### 9. Verify nothing's broken

```bash
# No dangling references
grep -rn "FluxGenerator\|StableDiffusionXLPipeline\|comfyui_server\|DinoGenerator" --include="*.py" --include="*.md" .

# generate.py works end to end on a single image
python3 flux/generate.py --prompt "Tyrannosaurus rex hunting in a misty river delta" --seed 99 --lora trex_v1 --output /tmp/smoke.png

# ab_test_replicate.py still runs (skips existing files, no-ops cleanly)
python3 flux/ab_test_replicate.py
```

### 10. Commit

One commit, clear message: `Tightening 5: retire local SDXL, commit to Replicate-Flux`

## Key Files

- `flux/ab_test_replicate.py` — reference impl for Replicate API calls (token loading, 429 retry, version-hash predictions)
- `flux/loras/trex_v1.safetensors` — first validated LoRA (archival; Replicate runs from its own copy)
- `flux/loras/trex_v1.config.yaml` — training config snapshot
- `assets/gallery/flux/ab_tests/trex_v1/` — A/B images + sidecars (keep as evidence)
- `/Users/ericeldridge/dino_art/.env` — has `REPLICATE_API_TOKEN` set

## Blockers / Escalations

- If `grep` in step 9 surfaces references in `tools/`, `site/`, `printify/`, or `db/`: don't blindly delete. Read the call site. Most likely these reference the *gallery output directory* (`assets/gallery/flux/`) which we're keeping, not the SDXL generator itself. Different thing.
- If `Launch Dino Generator.command` has an alias somewhere (Dock, login items): can't clean those programmatically; note in the commit message that user should remove manually.
- If you find a *working* feature of the old SDXL UI you didn't know about (e.g. a unique parameter sweep mode), stop and ask the user before deleting — don't lose functionality silently.

## Definition of Done

✓ All 7 files in step 1 deleted
✓ `flux/generate.py` created and smoke-tested with one real Replicate call (produces an image)
✓ `flux/loras/registry.json` created with `trex_v1` entry
✓ `flux/requirements.txt` slimmed or deleted
✓ `flux/CLAUDE.md`, `flux/LORA_TRAINING.md`, root `CLAUDE.md` rewritten to match reality
✓ `RECAP.md` updated with Tightening 4 results + Tightening 5 cleanup
✓ `grep` in step 9 returns no dead references
✓ One commit landed with clean message

---

## Reference: The validated A/B prompt

Used in Tightening 4, in case you want to repro:

- Baseline (vanilla Flux): `"Tyrannosaurus rex hunting in a misty river delta, photorealistic, horizontal posture, two-fingered hands, digitigrade feet"`
- With LoRA: `"trex_v1 Tyrannosaurus rex hunting in a misty river delta, photorealistic, horizontal posture, two-fingered hands, digitigrade feet"`
- Common params: `aspect_ratio=1:1`, `num_inference_steps=28`, `guidance_scale=3.0`, `output_format=png`, `megapixels=1`

## Reference: Common Replicate API gotchas already solved

1. **Rate limiting on accounts with <$5 credit:** 6 req/min, burst of 1. The 429 response includes `retry_after` in seconds. `ab_test_replicate.py:42` handles this; reuse the same retry loop.
2. **Private trained models cannot be called via `/v1/models/<owner>/<name>/predictions`** — get 404. Must use `/v1/predictions` with `version` field set to the full version hash. `ab_test_replicate.py:create_prediction()` shows both patterns.
3. **Version hash from API:** `GET /v1/models/<owner>/<name>` → `latest_version.id`. No need to scrape the web UI.

---

**Remember:** the LoRA works. The throwaway succeeded. This session is *not* about chasing better images — it's about making the codebase reflect the path that actually works, so the next LoRA (Triceratops, Spinosaurus, whatever) drops into a clean home. Boring, mechanical, high-value cleanup. Ship it.
