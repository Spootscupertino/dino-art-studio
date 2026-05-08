# Next Session — Tightening 3: Train the Throwaway T. rex LoRA

Paste everything below this line into a fresh Claude Code session at `/Users/ericeldridge/dino_art/`. Self-contained — the agent will have no memory of prior sessions.

---

## Context

I'm building a Midjourney + Flux dinosaur paleoart pipeline at `/Users/ericeldridge/dino_art/` (live at jurassinkart.com). Last session we hardened the system after a brutal critique. The whole point of this session: **train one throwaway LoRA end-to-end and learn from the result.** Not "make a good LoRA." Just: does the loop work?

### What's already in place (already merged to main, already pushed)

- `winners.json` carries `signal_type ∈ {mj_composition, flux_quality, anatomy_ref}` — top-3 trimming runs per signal_type per species.
- `auto_rater.py` is quarantined: heuristic scores write to `candidates.json`, never to `winners.json`. Promotion requires `python3 auto_rater.py --promote SPECIES INDEX`.
- **Publish gate** in `tools/sync_gallery.py` and `printify/printify_publisher.py`: any image with a Flux-tagged sidecar JSON requires a sibling `<image>.approved` file before either pipeline will touch it. This protects against an unproven LoRA's first output accidentally hitting Etsy.
- Anatomy thesis at `refs/anatomy_theses/tyrannosaurus.md` — 5 scoring categories + auto-reject conditions. This is the ruler.
- Drop-folder ingest at `flux/ingest_training_drops.py` (manual run only).
- 5 curated T. rex refs at `assets/gallery/flux/training_refs/tyrannosaurus/`:
  - `skeletal/` — 2 images (lateral mount + alternate pose)
  - `paleoart/` — 2 images (both side profiles, known weakness)
  - `living_analog/` — 1 image (cassowary mid-stride, lateral)

Each has `.txt` (caption) and `.json` (metadata) sidecars. Captions are auto-stubs — readable, not polished.

### What's NOT yet done

- No LoRA has been trained. ai-toolkit may or may not be installed.
- The two paleoart refs are both side-profile — the LoRA will be biased toward that angle. Expected and informative.
- Sidecar `license` and `source_url` fields are mostly empty. We're treating this as a throwaway — no Flux output will reach Etsy without explicit `.approved` markers.

---

## What I want this session to do

### Step 1 — Verify the environment

Confirm without auto-installing heavy ML deps:

1. Read `flux/CLAUDE.md`, `flux/SETUP.md`, `flux/LORA_TRAINING.md` — they describe expected setup.
2. Check `pip list | grep -iE "ai.toolkit|diffusers|peft|safetensors|torch"` and report what's installed.
3. Check the base Flux model weights (location specified in `flux/SETUP.md`).
4. Check disk free space (`df -h .`) — LoRA checkpoints + intermediate files can chew through 5–20GB.
5. Look at `flux/train_lora.py` — is it a working script or a scaffold? If it's WIP, the real path is to call ai-toolkit directly with a config file.

If anything's missing, list what to install + which command would do it. **Don't auto-install.** Wait for me to confirm.

### Step 2 — Export the dataset

Run:
```
python3 flux/export_dataset.py
```

Show me the output. Confirm:
- 5 images included (the T. rex training refs)
- Captions surfaced in the summary look reasonable
- No errors

If a caption is too generic to be useful (e.g. the cassowary one is still the auto-stub `a southern cassowary, large flightless bird, lateral view, photographic, anatomical reference`), tell me before training so I can polish a few. Don't edit captions without asking.

### Step 3 — Train the throwaway LoRA

Use a deliberately small/fast config:

- **Rank:** 8 (small, fast, easy to diagnose)
- **Steps:** 500–1000 (enough signal to see direction, not enough to overfit hard)
- **Trigger word:** `trex_v1` (specific enough to isolate LoRA effect at generate time)
- **Output:** `flux/loras/trex_v1.safetensors`
- **Learning rate:** ai-toolkit defaults are fine for first run

Show me the exact training command before kicking it off. Estimate runtime on M1 (it's slow — possibly 1–4 hours).

If training crashes:
- Capture the full error
- Don't try to "fix" by tweaking config aggressively
- Diagnose root cause first, present options

If training succeeds:
- Confirm `trex_v1.safetensors` exists and is non-zero size
- Don't generate any images yet — that's Step 4

### Step 4 — Draft the A/B test plan (don't run it)

Write out the Phase 4 plan as a script or doc:

- **Prompt:** something specific, e.g. `a Tyrannosaurus rex hunting in a misty forest, scientifically accurate paleoart, horizontal posture`
- **Batches:** 25 with `--lora trex_v1`, 25 without — same 25 seeds in each batch so each pair is comparable
- **Output:** `assets/gallery/flux/ab_tests/trex_v1/{with_lora,without_lora}/`
- **Sidecars:** every output gets a `.json` with `source: "flux"`, `lora: "trex_v1"` (or null), `seed: N`. The publish gate will block any of these from accidentally hitting the gallery — that's the design.
- **Rating:** rate each pair against the 5 categories in `refs/anatomy_theses/tyrannosaurus.md`. Don't be generous — count fingers, measure proportions, check tail carriage.

Don't run the A/B test this session. Just leave the plan ready to execute next session.

---

## Constraints — read these once before starting

- **Don't add more refs.** I have 5. The whole point of this experiment is what we learn from these specific refs.
- **Don't refactor working code.** The auto-rater quarantine, signal-split, publish gate, ingest pipeline — all done. Don't touch them.
- **Don't push to GitHub.** Local commits are fine; pushing main triggers a Vercel deploy and we don't want LoRA experiments deploying.
- **Don't approve any Flux output for Printify.** The `.approved` gate exists for exactly this experiment. No `.approved` markers.
- **No scope creep.** If a side-quest tempts you ("we should also build X"), write it as a one-line note in your reply and move on.
- **Stop and ask if blocked.** A good failure with a clear cause beats a forced success.

## Files to read first (in order)

1. `RECAP.md` — overall plan, current phase, what shipped recently
2. `flux/CLAUDE.md` — LoRA training pipeline owner notes
3. `flux/SETUP.md` and `flux/LORA_TRAINING.md` — environment expectations
4. `refs/anatomy_theses/tyrannosaurus.md` — the ruler (you'll need it for Step 4)

## Success criteria

- ✅ Environment status reported (ready vs. missing pieces clearly listed)
- ✅ Dataset exported, contents verified
- ✅ One LoRA training run completed — success or informative failure both count
- ✅ A/B test plan drafted, not executed

If we hit any blocker, stop and report. The principle: **one full loop completed beats five half-built loops.**
