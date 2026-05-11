# Next Session Prompt — Tightening 4: A/B Test Validation

## Status Coming In

**Tightening 3 complete:** LoRA training submitted to Replicate.

- Training job ID: `wad5pnmbb5rmy0cy2z29jefvqw`
- Status when you started: Processing on H200 GPU
- Expected completion: ~20 min from submission (check for "succeeded" or "failed" status on Replicate detail page)
- Cost: ~$1.50–3.00

## What You're Doing Today

**Goal:** Validate whether the throwaway LoRA actually improves T. rex image generation. NOT trying to ship great images — just proving the loop works.

## Step-by-Step

### 1. Check Training Status
- Go to https://replicate.com/p/wad5pnmbb5rmy0cy2z29jefvqw
- **If status = "succeeded":**
  - Download the `.safetensors` file from the Output section
  - Save to `flux/loras/trex_v1.safetensors`
  - Move to Step 2
- **If status = "failed":**
  - Read the error log
  - Adjust config or dataset and resubmit (escalate to planning)
- **If status = "processing":**
  - Wait for completion (check back in 10 min)

### 2. Run A/B Test: Both Paths

The test plan is in `flux/ab_test_plan_trex_v1.md`. Execute both:

```bash
# WITHOUT LoRA (baseline)
python3 flux/generate_image.py \
  --seed 42 \
  --prompt "trex_v1 Tyrannosaurus rex hunting in a misty river delta..." \
  --output assets/gallery/flux/ab_tests/trex_v1/without_lora/seed_0042.png

# WITH LoRA (trex_v1)
python3 flux/generate_image.py \
  --seed 42 \
  --lora flux/loras/trex_v1.safetensors \
  --prompt "trex_v1 Tyrannosaurus rex hunting in a misty river delta..." \
  --output assets/gallery/flux/ab_tests/trex_v1/with_lora/seed_0042.png
```

**Note:** This will generate 50 images (25 seeds × 2 paths). Expect ~45 sec per image on M1 = ~40 min total runtime.

Generate all 25 pairs. Sidecar JSON format (see `ab_test_plan_trex_v1.md`):
```json
{
  "seed": 42,
  "lora": "trex_v1",
  "score_with": 4,
  "score_without": 2,
  "anatomy_notes_with": "...",
  "anatomy_notes_without": "...",
  "approved": false
}
```

### 3. Rate All 50 Images

Use `refs/anatomy_theses/tyrannosaurus.md` as your scoring rubric. 5 categories, 1–5 per category:
1. **Posture** — Horizontal spine? Tail counterbalanced? Digitigrade stance?
2. **Hands** — Two-fingered? Reduced from generic dino? Positioned under body?
3. **Feet** — Tridactyl, digitigrade claws? Not sprawled?
4. **Skull–Body** — Skull proportional? Neck matching? Massive jaws?
5. **Realism** — Photorealistic skin texture? Lighting consistent? Feather coverage anatomically correct?

Score each image 1–5 per category. Write anatomy notes in the sidecar JSON.

### 4. Analyze Results

```bash
python3 analyze_ab_test.py --plan flux/ab_test_plan_trex_v1.md
```

(Create if needed. Compute:)
- Mean score delta (with − without) per seed
- Win rate: how many seeds score higher with LoRA?
- Per-category deltas

**Success threshold (from plan):**
- Mean score delta ≥ 2.0
- LoRA wins ≥ 18/25 pairs

### 5. Decide

- **LoRA is good:** Move to Tightening 5 — refine config, add more species refs, iterate
- **LoRA is bad:** Debug — was the dataset bad? Caption quality? Training hyperparams? Resubmit with adjustments
- **LoRA is mixed:** Analyze which categories improved vs. regressed. Pivot: maybe rank 8 is better, or caption_dropout needs tuning

## Key Files

- `flux/ab_test_plan_trex_v1.md` — 25-seed plan, prompt, sidecar format
- `refs/anatomy_theses/tyrannosaurus.md` — Scoring rubric (5 categories)
- `flux/loras/trex_v1.safetensors` — The trained LoRA (you'll download this)
- `flux/generate_image.py` — Runs with/without LoRA
- `assets/gallery/flux/ab_tests/trex_v1/` — Output directory (create if needed)

## Blockers / Escalations

- Training failed: check Replicate error log, adjust dataset or config, resubmit
- M1 runs out of VRAM during A/B test: reduce to 16 seeds (fastest path to signal)
- Sidecar JSON formatting issues: validate with `json.tool` before analyzing
- LoRA results are ambiguous: focus on posture + hands (the biggest differentiators)

## Definition of Done

✓ All 25 pairs generated (50 images)
✓ All 50 images scored (5 categories each)
✓ Analysis complete (mean delta, win rate)
✓ Decision made (keep / iterate / kill)
✓ Findings logged in RECAP.md update

---

**Remember:** This is a throwaway LoRA. The goal is NOT a perfect result — it's proof that the loop works. Even a mediocre result teaches you something about the training pipeline, the dataset, or the captions. Ship it.
