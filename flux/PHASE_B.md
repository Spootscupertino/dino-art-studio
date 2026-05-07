# Phase B — T-rex signature + targeted scoring

What landed in Phase B (commits 9e65a3b, 8197fa5, 5b54e2f, 242fccd, plus the
follow-up reconcile on main).

## What this changed

### 1. T-rex signature injection (always-on)
- `flux/generate_image.py` and `flux/comfyui_server.py` call
  `inject_trex_signature(prompt)` before rendering. If the prompt mentions
  T-rex and doesn't already carry the upstream signature, the renderer
  appends the triple-threat string (claws / mouth / feet).
- `generate_prompt.py` adds `TREX_SIGNATURE` (a structured dict) and
  `build_trex_anatomy_addon()` injected into `subject_parts` whenever
  the species is Tyrannosaurus rex. The flux-side injector is idempotent
  (skips when "honey-gold" is already in the prompt) so prompts assembled
  through generate_prompt.py don't get double-stamped.

### 2. Generic terrestrial-carnivore extremity emphasis (242fccd)
- `MOUTH_TEETH_CARNIVORE` / `MOUTH_TEETH_HERBIVORE` expanded from 3-word
  stubs into rich tooth + saliva + jaw-line + breath language.
- `HABITAT_INTERACTION["terrestrial"]` expanded with toe-pad / claw /
  track-impression / dust-at-footfall language.
- A new dedicated extremity+jaw line is appended to `subject_parts` for
  any terrestrial carnivore in close/mid framing — T-rex inherits this
  baseline, then the TREX_SIGNATURE adds the species-specific measurements
  on top.
- The Section 2 ground-impact block now fires for all large terrestrial
  diets on movement behaviors, not just T-rex.

### 3. Species enrichment (`species/tyrannosaurus_rex.py`)
- `dentition`: tooth_shape now records honey-gold coloration; new
  `visible_teeth` field captures wear facets, striations, anterior-tooth
  prominence.
- `limbs`: forelimb / hindlimb strings now describe curved claws on the
  digits; new `special_appendage` field carries claw measurements
  (4-5 inch, 45-60° downward angle, dark keratin with striations).
- `unique_features`, `mj_shorthand`, `known_failures` all expanded with
  claw / tooth / jaw failure modes (10+ new entries in known_failures).

### 4. Targeted T-rex scoring in `unified_feedback.py`
- `TREX_PILLARS` adds `claw_detail`, `mouth_detail`, `foot_detail`
  dimensions, appended to `DIMENSIONS` only when the species is T-rex.
- `compute_final_score` normalizes by total weight so the standard
  4-dimension score and the T-rex 7-dimension score both stay on the
  1–10 scale.
- DB schema gains `score_claw_detail` / `score_mouth_detail` /
  `score_foot_detail` columns with idempotent migration.
- `paste_prompt()` rewritten to use SIGALRM timeout for reliable handling
  of large prompt pastes.

### 5. Image-path persistence in winners.json (5b54e2f)
- `save_winner` now persists `image_path` so Phase C LoRA training can
  locate the source images for each winner.

## What did NOT land

Earlier draft notes (now removed) described a 3×3 interactive menu of
claw levels (minimal / balanced / emphasized) × tooth levels
(subtle / visible / detailed). That selector was never implemented — the
shipped solution is a single always-on T-rex signature, which is
simpler and produced better results in side-by-side tests.

## Next: Phase C

LoRA fine-tuning on T-rex winners. Threshold to start: 8 winners with
`final_score >= 8.0` and `image_path` resolvable on disk. The
ref-image interview workflow (`reference.py`) feeds scientifically
accurate paleoart / wildlife reference images into `winners.json` with
`source_type: "reference"` to reach the threshold faster.
