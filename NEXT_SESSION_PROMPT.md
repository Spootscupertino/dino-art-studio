# Next Session Prompt — T-rex LoRA v2: Scale to 20 Verified Refs + Retrain

## Context (read first)

Last session established the **Dev/Ops boundary** and the license enforcement infrastructure for the T-rex LoRA training pipeline. You (Claude) are **Lead Dev**. Ops (the user + Gemini) handles all image sourcing and legal clearance via "Transmittal Packages."

### What landed last session

1. **Audit + attribution** on the 5 original T-rex training refs:
   - 4 confirmed Wikimedia sources (steveoc86, Durbed, WildFrogs, Zissoudisctrucker — all CC BY-SA) marked `verified: true`
   - 1 cassowary `quarantined: true` (unknown source, excluded from training)

2. **Schema enforcement** in `flux/ingest_training_drops.py`:
   - Sidecar JSON now requires `source_url`, `image_url`, `creator`, `license`, `license_url`, `verified`, `source_checked_date`, `quarantined`
   - License allowlist: CC0 / CC BY (any version) / CC BY-SA (any version) / Public Domain
   - **Hard ban**: NC and ND licenses
   - New `--validate` flag audits the entire `training_refs/` tree

3. **Interactive intake** in `reference.py`:
   - Required: `source_url` and `creator` (no longer allow-blank)
   - New `pick_license()` prompt that only shows allowed licenses

4. **Batch 1 partially landed** in `~/Desktop/Jurassinkart/Training Drops/tyrannosaurus/skeletal/`:
   - `tyrannosaurus-rex-2025-2460-1384_wideexact_1230.jpg` — AMNH 5027, Public Domain
   - `Tyrannoskull.jpg` — A.E. Anderson, Public Domain
   - `Tyrannosaurus_Sue_skeletal_reconstruction.png` — Scott A. Hartman, CC BY 4.0 (verified against Wikimedia Commons)
   - `Tyrannosaurus_muscle_mass.png` — Hutchinson et al., CC BY 2.5 (Ops decision pending: stay in `skeletal/` or move to `paleoart/`?)

5. **Still pending from Batch 1** (Ops will drop in next session):
   - Item #4: Cassowary (Pearson Scott Foresman, Public Domain) → `living_analog/`
   - Item #6: Luis Rey dynamic action pose (CC BY 2.5) → `paleoart/`

## Goal for next session

Get from **5 verified refs → 20 verified refs**, then retrain as `trex_v2`.

Net after Batch 1 completes: **9 verified** (4 original + 5 new — cassowary quarantine replaced 1:1).

Need to source **11 more** via additional Ops Transmittal Packages.

## Diversity targets for the 11 remaining refs

Discuss with Ops. Aim for coverage gaps in the current 9:

- **Action / behavior poses**: roaring head-up, lunging strike, walking three-quarter view, juvenile gait
- **Lighting / environment**: backlit silhouette, low-angle daylight, mist/fog, harsh sun shadow
- **Anatomical close-ups**: hand/claw detail, foot/digit, scleral ring, dorsal vertebrae
- **Living analogs** (more variety beyond cassowary): secretarybird gait, monitor lizard skin texture, emu/ostrich locomotion

All sources must be CC0 / CC BY / CC BY-SA / Public Domain. NC and ND are auto-rejected.

## Concrete action items

1. **For each Ops Transmittal Package**:
   - Confirm files dropped into `~/Desktop/Jurassinkart/Training Drops/tyrannosaurus/<skeletal|paleoart|living_analog>/`
   - Run `python3 flux/ingest_training_drops.py` (moves files + writes sidecar stubs)
   - Populate each sidecar JSON with the Transmittal attribution via `Edit` tool
   - Hand-write a **descriptive** `.txt` caption per ref (anatomy-specific, not generic — generic captions are part of why trex_v1 was a 4/10)
   - Run `python3 flux/ingest_training_drops.py --validate --species tyrannosaurus` after each batch

2. **Once 20 refs are clean**:
   - Run `python3 flux/export_dataset.py` to bundle `flux/datasets/trex_v2_dataset.zip`
   - Hand off to Ops with the recipe from [flux/LORA_TRAINING.md](flux/LORA_TRAINING.md):
     - rank: 16
     - learning rate: 1e-4
     - steps: ~1500 (more refs → can push higher than v1's 1000)
     - trigger_word: `trex_v2`
   - **Ops runs the actual training on Replicate web UI** (~$1–3, ~30–60 min)
   - Once Ops returns training ID + version hash, register `trex_v2` in `flux/loras/registry.json`
   - Run `python3 flux/ab_test_replicate.py` for the 5-pair A/B vs v1

3. **Final validation**:
   - Generate 3 test images with `flux/generate.py --lora trex_v2`: stalking shot, frontal portrait, running pose
   - Compare side-by-side with v1 outputs
   - Honest 1–10 rating, target: **7+/10** (v1 baseline was 4/10)

## Hard rules — DO NOT relax

- **Dev/Ops boundary**: Do not download, scrape, or pull images yourself. Ops provides Transmittal Packages with URL + creator + license. If Ops sends NC or ND, refuse. If Ops sends an unrecognized license, flag before ingesting.
- **No filename-based attribution**: Every sidecar must have `verified: true` only after Ops or visual confirmation against the source URL.
- **Captions matter for LoRA quality**: Each caption should describe actual image content (pose, angle, anatomy emphasis), not be a generic species tag.

## Files to read at session start

- [flux/LORA_TRAINING.md](flux/LORA_TRAINING.md) — full retrain workflow
- [flux/ingest_training_drops.py](flux/ingest_training_drops.py) — schema + allowlist
- [reference.py](reference.py) — interactive intake fallback
- [flux/loras/registry.json](flux/loras/registry.json) — to register `trex_v2` after training
