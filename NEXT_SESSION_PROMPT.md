# Next Session — Audit, Eval Harness, and Controlled v4

## Strategic framing (read first)

We've sold 2 posters. That's not enough signal to know what's broken about the *product*, so the bet for now is: **MJ outputs are by definition undifferentiated; a strong T-rex LoRA is the most plausible way to make this work look like *yours* and not "someone with an MJ subscription."** That bet is defensible. But the v1 → v2 → v3 loop so far has not been a real experiment — every iteration changed dataset, captions, and hyperparams simultaneously, so we don't know what helped and what didn't. **This session fixes that before spending more money on training runs.**

## Hard rule for this session

**Do not start a v4 training run until Phase 3 (eval harness) is built.** Otherwise we repeat the uninterpretable pattern and burn another $1–3 on a result that can't be compared to anything.

## Phase 1 — See what v3 actually did

By now `spootscupertino/trex_v3` should be done training (it was submitted ~end of 2026-05-13 with 1500 steps).

1. Get the version hash:
   ```bash
   source .env
   curl -s -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
     https://api.replicate.com/v1/models/spootscupertino/trex_v3 \
     | jq '{owner: .owner, name: .name, version: .latest_version.id, created: .latest_version.created_at}'
   ```
2. Register in `flux/loras/registry.json` under `"trex_v3"` with version hash, training_id, `trained_on`.
3. Run the existing A/B:
   ```bash
   python3 flux/ab_test_replicate.py
   ```
   Outputs land in `assets/gallery/flux/ab_tests/trex_v3/`. Eyeball the pairs.

**Treat the result as data, not a verdict.** v3's dataset, captions, and hyperparams all differ from v2 — even a clean win doesn't tell us *why*. Don't promote v3 to the gallery yet.

## Phase 2 — Audit the silent bugs in v1 and v2

`flux/export_dataset.py` was scanning `training_refs/*` instead of `training_refs/**/*` until last session. That means once we restructured into `<species>/<source_type>/` subdirs, **every export was emitting whatever stray files lived at the top level** and silently skipping the curated refs in subdirs. This may have invalidated v1 and v2 entirely.

1. Pull the v1 and v2 training run pages on Replicate. Each one stores the `input_images` URL it actually trained on. Download both zips:
   ```bash
   # The training detail JSON includes the input file URL
   curl -s -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
     https://api.replicate.com/v1/trainings/wad5pnmbb5rmy0cy2z29jefvqw | jq .input
   curl -s -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
     https://api.replicate.com/v1/trainings/yzx4g2vpesrmy0cy49tvqap360 | jq .input
   ```
2. Unzip each and **list the actual contents.** If v1's "5/5 win, mean Δ 7.2" was measured against a LoRA trained on stray top-level files instead of the curated 4 refs, that scoreboard is meaningless.
3. Write the finding into `RECAP.md`. If v1 / v2 were trained on the wrong data, say so — don't paper over it.

## Phase 3 — Build the frozen eval harness (highest leverage)

Single number per LoRA, comparable across all future versions. Stop scoring on different prompts every time.

### Files to create

- `flux/eval/prompts.json` — **frozen** list of ~10 prompts covering rubric axes:
  - mouth_roar — open-mouth roar, teeth + lipped jaw + tongue visible
  - frontal_portrait — binocular forward-facing eyes, deep skull
  - full_body_stalking — three-quarter view, walking gait, environment
  - foot_detail — digitigrade foot, three weight-bearing toes, claws
  - integument_macro — skin/scale texture
  - hand_detail — two-fingered manus, claw curvature
  - juvenile — sub-adult proportions, longer legs, less massive skull
  - silhouette_backlit — backlit at low sun, anatomy by outline only
  - environmental_mist — atmospheric depth, T-rex in fog/light shaft
  - action_lunge — predator strike pose, dynamic
- `flux/eval/run.py` — generates each prompt × {baseline, v1, v2, v3, …, vN} at **fixed seeds** (e.g. one seed per prompt, never change). Writes outputs to `assets/gallery/flux/evals/<lora_name>/<prompt_id>_seed_NNNN.png`.
- `flux/eval/score.py` — blind-scoring CLI. Shows you each image with the LoRA name hidden behind a hash. You score on the 5-axis rubric (proportions, hands, feet, mouth/teeth, integument — 1-5 each). After scoring is committed, reveals which LoRA produced what. Persists scores to `flux/eval/scores.json` keyed by `(lora, prompt_id, seed, scorer, scored_at)`.

### Acceptance criteria for Phase 3

- Re-run eval against v1, v2, v3 with identical prompts and seeds.
- `flux/eval/scores.json` has at least one full pass per LoRA.
- Print a leaderboard: mean score per LoRA, per-axis breakdown.

This is the bedrock for every future LoRA decision. Build it before anything else in Phase 4+.

## Phase 4 — Controlled v4 (single-axis change)

Hypothesis to test: **the v3 dataset is contaminated by an MJ aesthetic feedback loop.** 19/26 of its images are MJ self-generations. If MJ already gets mouths slightly wrong, training on MJ mouths bakes that wrongness in.

### Experimental setup

- **Freeze v3's hyperparameters exactly.** LR 1e-4, 1500 steps, rank 16, batch 1, caption_dropout 0.05, autocaption OFF.
- **Change only the dataset composition.** Target ~30% MJ / ~70% photographic + paleoart + skeletal + integument. That means drop ~13 of the 19 MJ refs and replace with non-MJ images.
  - Ops drops new non-MJ refs into the appropriate `Training Drops/tyrannosaurus/<source_type>/` folders (skeletal mounts, scientific paleoart from CC sources, more living-analog photos).
  - Keep the 6 best MJ refs (the ones with the most anatomically corrected mouths).
- **Same trigger word convention:** `trex_v4`. Same caption style (re-use Phase 5 hand-captions if done).
- Submit to Replicate as `spootscupertino/trex_v4`. Register in registry.
- Run through Phase 3 eval harness against v3.

### Decision rule

- If **v4 mean score > v3 mean score**: the MJ-loop hypothesis is supported. Keep diluting MJ in v5.
- If **v4 ≈ v3**: dataset composition isn't the bottleneck. Move on to hyperparameter sweeps (steps, LR, rank — one at a time).
- If **v4 < v3**: MJ refs are actually contributing. Stop second-guessing them, focus elsewhere.

Either way you've **learned something** for the first time in this LoRA loop.

## Phase 5 — Hand-caption the surviving MJ refs

Last session I auto-generated 19 captions from filename slugs using regex + canned templates. You yourself flagged in the prior NEXT_SESSION_PROMPT that *"generic captions are part of why trex_v1 was a 4/10."* I repeated that failure mode at 5× the scale.

For the ~6 MJ refs that survive Phase 4's cut:
- Open each image, look at it.
- Write a caption that names *what's actually in the image*: pose, angle, what anatomy is featured, lighting, anything notable. Not "Tyrannosaurus rex, macro detail of the mouth" repeated 6 times.
- Save into the existing `<image>.txt` sidecar.
- Re-export the v4 zip.

This is one focused hour. It's not glamorous. It is likely the highest-impact thing per minute spent on the whole list.

## Deferred (acknowledged, not doing this session)

- License schema cleanup (separate `license` from `usage_rights_basis`) — matters at scale, not at 2 sales.
- Schema axis split (`provenance` vs `subject_focus`) — refactor later.
- Dev/Ops boundary rewrite — symbolic, low cost to leave.
- LFS auto-sync in `end_session_daddy.sh` — fix when it bites again.
- Sales / analytics domain — 2 sales is no signal, revisit at 20.
- `_quarantine/1773421176-02lhewettsuesuite333.webp` — just delete it this session, takes 5 seconds.

## Files to read at session start

- This file
- [flux/loras/registry.json](flux/loras/registry.json) — current LoRA roster
- [flux/ab_test_replicate.py](flux/ab_test_replicate.py) — existing A/B harness (Phase 3 will largely supersede it)
- [flux/export_dataset.py](flux/export_dataset.py) — review the subdir-walk fix from last session
- [flux/CLAUDE.md](flux/CLAUDE.md) — domain contract

## What success looks like at end of session

1. v3's actual A/B result is known and recorded.
2. v1 and v2's actual training inputs are known — and if they were broken, that's documented.
3. `flux/eval/` exists, runs end-to-end, has one full pass scored across v1/v2/v3.
4. v4 has been submitted to Replicate with exactly one variable changed from v3 (dataset composition), and is queued for evaluation when it finishes.
5. The 6 surviving MJ refs have hand-written captions.

If we hit all five, **next** session can start being about hyperparameter sweeps that actually teach us something, instead of vibes.
