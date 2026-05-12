# Next Session Prompt — Tightening 6: Second-Species LoRA

## Status Coming In

**Tightening 5 (retire local SDXL, commit to Replicate-Flux) is complete.**

- `flux/generate.py` is the only generator. Single-image CLI, calls Replicate. Smoke-tested.
- `flux/loras/registry.json` is the source of truth. Currently registers `trex_v1` (5/5 win rate, mean Δ +7.2).
- `flux/ab_test_replicate.py` is the validation gate for any new LoRA.
- Local SDXL stack (`generate_image.py`, `comfyui_server.py`, `train_lora.py`, `SETUP.md`, `PHASE_B.md`, launcher, `DinoGenerator.app`, `PHASE_C_README.md`, `requirements.txt`) is deleted.
- Docs (root `CLAUDE.md`, `flux/CLAUDE.md`, `flux/LORA_TRAINING.md`, `RECAP.md`) all describe the cloud-only Replicate-Flux stack.

The stack is coherent end-to-end. Time to put it through its paces with a second species.

## What You're Doing This Session

**Train a LoRA for species #2.** The full loop — pick species, curate refs, caption, zip, train on Replicate, register, A/B validate, promote (or kill).

We proved the loop works on T. rex. Now we prove it generalizes. If species #2 hits the threshold, the next 10 species are mechanical.

## Step-by-Step

### 1. Pick the species

Pick one. Suggested candidates (any will do; pick by what you're most curious about):

- **Velociraptor** — different body plan (feathered, smaller, sickle claw on hind foot). Tests whether the loop handles non-T-rex anatomy.
- **Triceratops** — quadruped + frill + horns. Tests whether the loop handles quadrupedal posture vs the biped baked into T. rex refs.
- **Spinosaurus** — sail-back, aquatic, elongated jaw. Tests an unusual body plan.

Write a one-paragraph anatomy thesis at `refs/anatomy_theses/<species_lower>.md` if one doesn't exist. Mirror the structure of `refs/anatomy_theses/tyrannosaurus.md` (5 scoring categories, auto-reject conditions).

### 2. Curate 5–10 refs

Use `python3 reference.py` to intake each one. Mix sources (paleoart, museum, living analog). Each ref needs a `.txt` caption: `"a photo of <species>, <anatomy notes>"`.

### 3. Zip and upload

```bash
python3 flux/export_dataset.py
```

Upload `flux/datasets/<species>_dataset.zip` to Replicate's `ostris/flux-dev-lora-trainer` web UI. Use the same recipe that worked for T. rex (rank 16, lr 1e-4, 1000 steps, caption_dropout 0.05, batch 1, res 512/768/1024). Trigger word = `<species_lower>_v1`.

### 4. Archive and register

After training succeeds:
- Download `.safetensors` → `flux/loras/<species>_v1.safetensors`
- Save config snapshot → `flux/loras/<species>_v1.config.yaml`
- Get version hash: `curl -s -H "Authorization: Bearer $REPLICATE_API_TOKEN" https://api.replicate.com/v1/models/<owner>/<slug> | jq .latest_version.id`
- Add entry to `flux/loras/registry.json`

### 5. A/B validate

Adjust the constants at the top of `flux/ab_test_replicate.py`:
- `SEEDS` — keep the same 5 (42, 123, 777, 1024, 2025) for comparable scoring discipline
- `BASE_PROMPT` — species-appropriate scene
- `LORA_VERSION` — new version hash
- `OUT_ROOT` — `assets/gallery/flux/ab_tests/<species>_v1`

Run it. Score each pair 1–5 across the 5 thesis categories. Promotion threshold: **mean Δ ≥ 2.0, win rate ≥ 80%**.

### 6. Promote or kill

- **Promote:** Record `ab_test_winrate` + `ab_test_mean_delta` in the registry. Commit.
- **Kill:** Note what failed in `RECAP.md`. Adjust the recipe (more refs, different caption discipline, different rank) and retry. Don't lower the threshold.

## Key Files

- `flux/generate.py` — daily-driver CLI
- `flux/ab_test_replicate.py` — A/B harness (edit constants at top for each LoRA)
- `flux/loras/registry.json` — registry; add new entry here
- `flux/LORA_TRAINING.md` — full workflow reference
- `refs/anatomy_theses/tyrannosaurus.md` — thesis template

## Definition of Done

✓ Species #2 chosen and anatomy thesis written
✓ 5–10 refs curated via `reference.py`
✓ Dataset zipped and trained on Replicate
✓ `<species>_v1.safetensors` + config archived locally
✓ Registry entry added
✓ A/B test run, scored, recorded
✓ Result documented in RECAP.md
✓ One commit landed
