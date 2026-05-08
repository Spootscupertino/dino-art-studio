# Next Session — Phase 3: Train the Throwaway T. rex LoRA

Paste everything below this line into the new session. It's self-contained.

---

## Where I left off

I'm building a Midjourney + Flux dinosaur paleoart pipeline at `/Users/ericeldridge/dino_art/`. Last session we hardened the system after a brutal critique — the upshot: **stop optimizing the wrong thing, run one full training loop end-to-end, learn from what comes out**. We're following a 5-phase plan (Phases 0–2 done, Phase 3 starts now).

### What landed in Phase 0 (guardrails — on a worktree, not yet merged)
- `winners.json` now has `signal_type ∈ {mj_composition, flux_quality, anatomy_ref}` so MJ winners, Flux winners, and reference images don't pollute each other's training signal. Top-3 trimming runs *per signal_type* per species.
- `auto_rater.py` is quarantined: it writes only to `candidates.json`, never to `winners.json`. Promotion to winners requires `python3 auto_rater.py --promote SPECIES INDEX`.
- Publish gate: any image with a Flux sidecar JSON requires a sibling `<image>.approved` file before `tools/sync_gallery.py` or `printify/printify_publisher.py` will touch it. Prevents an unproven LoRA's first output from accidentally hitting Etsy.

### What landed in Phase 1 (anatomy thesis)
- `refs/anatomy_theses/tyrannosaurus.md` — 5 scoring categories (posture / hands / feet / skull-body / realism), auto-reject conditions (3-finger hands, kangaroo posture, tail-dragging, etc.). This is the ruler for judging refs and generated images. Read it before anything else.

### What landed in Phase 2 (curated 5 T. rex refs)
At `assets/gallery/flux/training_refs/tyrannosaurus/`:
- `skeletal/tyrannosaurus_wikimedia_side_skeleton.png` — full lateral mount
- `skeletal/tyrannosaurus_wikimedia_skeleton_bent_over.png` — alternate skeletal pose
- `paleoart/tyrannosaurus_wikimedia_paleo_art_side_profile.png`
- `paleoart/tyrannosaurus_wikimedia_paleo_art_side_profile_feathers.png` *(both paleoart are side profile — known weakness)*
- `living_analog/tyrannosaurus_living_analog_cassowary_mid_stride.png` — cassowary, lateral, foraging pose, digitigrade feet visible

Each image has `.txt` (caption) and `.json` (metadata: species, source_type, source_url, license, thesis_score) sidecars. Captions are mostly auto-stubs — readable but not polished.

The drop-folder ingest pipeline lives at `flux/ingest_training_drops.py` (manual run only, by design). Drop folders are at `~/Desktop/Jurassinkart/Training Drops/<species>/<source_type>/`.

### What ALSO happened on the main checkout (not the worktree)
While the worktree work was happening, I ran `unified_feedback.py` ~10 times rating MJ images and `reference.py` ~3 times registering reference images. **Those writes landed in `/Users/ericeldridge/dino_art/dino_art.db` and the root `winners.json` / `paleoart_refs.json` — not in the worktree.** Our worktree's `winners.json` still has only the seed entries. We need to merge before Phase 3 so the LoRA training pipeline sees both.

---

## What I want this session to do

### Step 0 — Merge the worktree back to main

The worktree is at `.claude/worktrees/romantic-blackwell-a223d8/` on branch `claude/romantic-blackwell-a223d8`. Recent commits added the publish gate, signal-split, candidates quarantine, anatomy thesis, ingest script, and 5 ingested T. rex refs.

Before doing anything else:

1. From the worktree, commit any uncommitted work and confirm the branch is clean.
2. Switch to the main checkout (`/Users/ericeldridge/dino_art/`) and merge the branch.
3. Resolve any conflicts. The likely conflict zones:
   - `winners.json` — main has new ratings I added this week; worktree has the schema migration adding `signal_type`. Apply the migration to main's entries (mj source → mj_composition, flux source → flux_quality).
   - `paleoart_refs.json` / `skeletal_refs.json` — main has new ref registrations; worktree didn't touch these, so main wins.
4. Verify after merge: `assets/gallery/flux/training_refs/tyrannosaurus/` has all 5 refs with `.txt` + `.json` sidecars. `winners.json` has both my new MJ ratings AND the `signal_type` field on every entry.
5. Don't push or deploy. Local merge only.

**Stop and report after the merge succeeds, before continuing.**

### Step 1 — Verify environment for Flux LoRA training

This is an M1 Mac (Mac mini). Confirm:
- `flux/` has `train_lora.py`, `export_dataset.py`, `generate_image.py` (it does)
- ai-toolkit or whatever trainer `train_lora.py` uses is installed (`pip list | grep -iE "ai.toolkit|diffusers|peft"`)
- The base Flux model weights are present (check `flux/SETUP.md` and `flux/LORA_TRAINING.md` for the expected paths)
- There's enough disk + memory for an M1 LoRA run

If anything's missing, list what needs installing and stop. Don't auto-install heavy ML deps without confirming with me.

### Step 2 — Run `flux/export_dataset.py` to package the 5 refs

This script reads the `training_refs/` folder and outputs an ai-toolkit-compatible dataset. Run it, show me the summary, confirm:
- 5 images included
- Captions look reasonable (the cassowary one especially — its `.txt` may still be the auto-stub)
- No errors

If a caption is too generic, ask before editing — I want a chance to write better ones.

### Step 3 — Kick off the throwaway LoRA training

Use a deliberately small/fast config:
- Low rank (r=8 or r=16)
- Few steps (~500–1000)
- Trigger word: something specific like `trex_v1` so we can isolate the LoRA's effect
- Save the LoRA to `flux/loras/trex_v1.safetensors`

Don't try to make this LoRA "good." The point is: **does the loop work?** If training crashes, that's the lesson. If it succeeds, we move to Phase 4.

Show me the command before running it. Tell me roughly how long to expect.

### Step 4 — Phase 4 prep: paired-seed A/B test plan

After training succeeds, draft the A/B test (don't run it yet):
- Same prompt, e.g. `a Tyrannosaurus rex hunting in a misty forest, scientifically accurate paleoart`
- 25 images with `--lora trex_v1` + 25 without (50 total)
- Same 25 seeds in both batches so each pair is comparable
- Output to `assets/gallery/flux/ab_tests/trex_v1/{with_lora,without_lora}/`
- Each image gets a `.json` sidecar marking `source: "flux"`, `lora: "trex_v1"` (or null), `seed: N` — the publish gate will block any of these from accidentally hitting the gallery

We'll rate them against the anatomy thesis in `refs/anatomy_theses/tyrannosaurus.md` next session.

---

## Constraints — read carefully

- **Don't add more refs.** I have 5. The whole point of Phase 3 is to train on what we have and learn. Adding refs now defeats the experiment.
- **Don't polish what doesn't need polishing.** The auto-rater, ingest script, signal-split — all done. Don't refactor them.
- **Don't auto-deploy or push to GitHub.** Everything stays local until we evaluate Phase 4 results.
- **Don't approve any Flux output for Printify.** The `.approved` gate exists for exactly this LoRA experiment. No `.approved` markers until we're past Phase 5.
- **Be ruthless about scope.** If a side-quest tempts you ("we should also add X"), write it down and move on. The critique we're answering is "you keep building the factory before making one product." Resist.

## Project orientation files (read these first)

- `CLAUDE.md` (root) — domain index, cross-domain contracts
- `flux/CLAUDE.md` — LoRA training pipeline owner notes
- `flux/LORA_TRAINING.md` — existing setup notes, may be stale
- `refs/anatomy_theses/tyrannosaurus.md` — the ruler
- `RECAP.md` — the broader plan and what each script does

## Success criteria for this session

- ✅ Worktree merged into main, no broken state
- ✅ Confirmed environment is ready (or clear list of what's missing)
- ✅ Dataset exported with 5 refs
- ✅ One LoRA training run completed (success OR informative failure — both are wins)
- ✅ A/B test plan drafted, not run

If we hit a blocker at any step, stop and ask. The critique we're answering values **one full loop done > five half-built loops**.
