# Next Session — Register v4, Run Eval Harness, Score Everything

## What we built this session (don't redo it)

- ✅ trex_v3 registered in `flux/loras/registry.json`, A/B tested: 5/5 wins vs v2, mouth detail visibly improved
- ✅ Audited v1/v2 training bugs: v2 had autocaption=True (discarded hand captions) + Allosaurus contamination + LR 10× lower — v2 is invalid
- ✅ Built frozen eval harness: `flux/eval/prompts.json` (10 prompts, fixed seeds), `flux/eval/run.py` (generates grid), `flux/eval/score.py` (blind scoring 5 axes)
- ✅ Recaptioned all MJ training images by looking at each one
- ✅ Added 6 real-world refs: Komodo mouth open, monitor lizard swallowing prey, cassowary full body, ostrich foot, T-rex skeletal hand, T-rex skin fossil
- ✅ Built and submitted trex_v4 dataset (31 images, ~42% MJ, all vision-captioned) to Replicate
  - Training ID: `ktgpp6zqhhrmt0cy4x0v03919r` (was `processing` at session end)
  - Same hyperparams as v3: LR=0.0001, steps=1500, rank=16, autocaption=OFF

## Phase 1 — Check if v4 is done

```bash
source .env
curl -s -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
  https://api.replicate.com/v1/trainings/ktgpp6zqhhrmt0cy4x0v03919r \
  | jq '{status: .status, version: .output.version}'
```

If `status == "succeeded"`, grab the version hash and register it:
- Add `"trex_v4"` entry to `flux/loras/registry.json` (same shape as v3)
- Set `trained_on: "2026-05-14"`, `training_id: "ktgpp6zqhhrmt0cy4x0v03919r"`

## Phase 2 — Run the eval harness on v3 and v4

```bash
python3 flux/eval/run.py --lora trex_v3
python3 flux/eval/run.py --lora trex_v4
```

Outputs go to `assets/gallery/flux/evals/<lora_name>/`. Takes ~5 min per LoRA (10 prompts × 1 image each).

Also run baseline (no LoRA) if it hasn't been scored yet:
```bash
python3 flux/eval/run.py --baseline
```

## Phase 3 — Score everything blind

```bash
python3 flux/eval/score.py --scorer "eric"
```

You'll see images one at a time — you don't know which LoRA you're scoring. Rate each on 5 axes (1-5): proportions, hands, feet, mouth/teeth, integument. After scoring all images:

```bash
python3 flux/eval/score.py --leaderboard
python3 flux/eval/score.py --reveal
```

**This is the moment of truth.** If v4 > v3 by a meaningful margin, better captions + real refs helped. If not, the problem is somewhere else (dataset size, architecture, hyperparams).

## Phase 4 — Decide on v5

| v4 result | Action |
|---|---|
| v4 clearly beats v3 | Good signal — decide which axis to push next. Options: more real refs (target <30% MJ), longer training (2000 steps), or start generating gallery images |
| v4 ≈ v3 | Caption quality didn't move the needle. Consider: larger dataset, different trigger word, or accept v3 and go generate gallery images |
| v4 loses to v3 | Something broke. Diff the datasets carefully. Check if export_dataset.py included the right files. |

## Hard rule for next session

**Do not submit v5 training until Phase 3 (eval scores) is complete and you've decided what single variable to change.** One change at a time.

## Known issues to fix at some point

- Dev mirror (dino-art-studio) branch push fails when LFS objects > ~50MB — LFS objects push fine but branch push gets pre-receive hook declined. Not urgent since jurassinkart.com (production) always succeeds.
- `flux/eval/run.py` hasn't been run yet — baseline scores for v1/v2/v3 don't exist. Consider running v1 and v2 as well so you have a full history.

## Strategic framing (unchanged)

We've sold 2 posters. The bet is: a strong T-rex LoRA makes this art look like *yours*, not generic MJ. That bet is still defensible. The next gate is: does v4 beat v3 on the rubric? If yes, keep improving. If no, it may be time to stop training and start publishing — more gallery images, more Printify listings, more SEO surface area. Better anatomy doesn't matter if no one sees it.
