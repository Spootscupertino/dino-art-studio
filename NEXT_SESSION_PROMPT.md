# Next Session — Score v5, Wire Up Research Pipeline

## What we built this session

- ✅ Built `trex_v5` dataset (44 source images → 97 weighted training instances)
- ✅ Added v5 folder taxonomy with `weights.json` (mouth 6x, forelimb 4x, eye 3x, etc.)
- ✅ Ingested Steveoc 86 paleoart (lateral life restoration + horizontal mirror) into `v5_full_body_action/` with anatomy-only captions
- ✅ Quarantined the museum statue (`Tyrannosaurus-Rex-model-crop.jpg`) — building background contamination
- ✅ Excluded `skeletal` + `living_analog` v4 folders via weight=0 (didn't transfer to photorealistic per v4 eval)
- ✅ Submitted v5 to Replicate (training ID: `65g9491vsdrmt0cy6tzrg2k2xc`, hardware: H200)
  - Hyperparameters: trigger=`trex_v5`, autocaption=OFF, steps=1500, LR=0.0001, rank=16 (same as v3/v4)
- ✅ Read v3/v4 eval data: **v4 LOST to baseline 7-1-2** on strict rubric. Hands axis catastrophic (1.0 vs 1.6 baseline). Integument was the only axis that improved.
- ✅ Built three new agents in `.claude/agents/`:
  - `source-hunter` (haiku) — CC-licensed image sourcing
  - `license-auditor` (haiku) — legal verification gate
  - `caption-polisher` (sonnet) — anatomy-only caption authoring
- ✅ Stubbed four tools in `tools/`:
  - `source_paleoart.py` — Wikimedia + iNaturalist + Smithsonian + PLOS/PeerJ APIs
  - `license_audit.py` — sidecar verification + auto-quarantine
  - `caption_draft.py` — Ollama vision-model drafter
  - `dedup_refs.py` — pHash near-duplicate detection
- ✅ Updated `weights.json` with v5 thesis + 12-version roadmap notes

## Phase 1 — Check if v5 finished

```bash
source .env
curl -s -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
  https://api.replicate.com/v1/trainings/65g9491vsdrmt0cy6tzrg2k2xc \
  | jq '{status: .status, version: .output.version}'
```

If `succeeded`, copy the version hash and append this to `flux/loras/registry.json`:

```json
"trex_v5": {
  "replicate_owner": "spootscupertino",
  "replicate_model": "trex_v5",
  "version": "<paste hash here>",
  "trigger_word": "trex_v5",
  "trained_on": "2026-05-17",
  "training_id": "65g9491vsdrmt0cy6tzrg2k2xc",
  "ab_test_winrate": null,
  "ab_test_mean_delta": null,
  "dataset_notes": "44 imgs, 97 weighted entries. Mouth 6x, forelimb 4x, eye 3x. Added Steveoc 86 lateral paleoart. Excluded skeletal+living_analog."
}
```

## Phase 2 — Run eval and score

```bash
python3 flux/eval/run.py --lora trex_v5
python3 flux/eval/score.py --scorer "eric"
python3 flux/eval/score.py --scorer "eric" --lora trex_v3 --rescore  # re-score under strict rubric
python3 flux/eval/score.py --scorer "eric" --lora trex_v4 --rescore
python3 flux/eval/score.py --leaderboard
python3 flux/eval/score.py --reveal
```

The re-score of v3 and v4 under the strict (0 = not viewable) rubric is important — without it, the v3→v4→v5 trajectory comparison is apples-to-oranges.

## Phase 3 — Decide v6 strategy based on v5 scores

| v5 hands axis result | Action for v6 |
|---|---|
| ≥ 3.0 | **Ship-worthy on hands.** v6 polishes other axes (proportions, mouth). |
| 2.0 – 2.9 | **Working but not yet hero-tier.** v6 doubles down on forelimb refs — add 2-3 more CC paleoart, bump weight to 6x. |
| 1.0 – 1.9 | **Diagrams aren't enough.** Start the commission inquiry now (Emily Willoughby, RJ Palmer). v6 = same dataset, LR 0.0001→0.0004 as a learning-rate ablation while you wait. |
| < 1.0 | **Something broke.** Diff v5 vs v3 carefully — caption methodology may have over-corrected. |

## Phase 4 — Wire up the research pipeline (v6 prep regardless of v5 outcome)

The three new agents and four tool stubs are in place but the Python tools are not yet implemented. Order of implementation:

1. **`tools/license_audit.py`** — already mostly working, just needs `--verify-urls` curl logic. Test against existing training_refs/ first to find any sidecar gaps.
2. **`tools/source_paleoart.py`** — implement Wikimedia API first (`commons.wikimedia.org/w/api.php`, search namespace=6). Then iNaturalist (`api.inaturalist.org/v1/observations`). Smithsonian + PLOS later.
3. **`tools/dedup_refs.py`** — `pip install imagehash Pillow`, implement pHash + mirror detection.
4. **`tools/caption_draft.py`** — install Ollama on the 2016 MBP, `ollama pull llava:13b`, implement HTTP call to `localhost:11434/api/generate`.

## Phase 5 — 2016 Intel MBP as research box

Pre-flight checklist:
- [ ] Clear browser caches, uninstall Adobe / heavy apps
- [ ] Install Homebrew + Python 3.12
- [ ] Install Ollama (`brew install ollama`)
- [ ] `ollama pull llava:13b` (or `llama3.2-vision:11b` if it runs)
- [ ] Clone the dino_art repo via git or sync via the `dino-art-studio` mirror
- [ ] Test: run `tools/caption_draft.py --folder assets/staging/test/` end-to-end

The Intel MBP runs Ollama at ~3-8 tok/s on 7-8B-class models. Workable for batch overnight runs. Don't expect Flux training on it — that stays on Replicate.

## 12-version roadmap (locked-in)

| Version | Variable changed | Hypothesis | Decision criterion |
|---|---|---|---|
| **v5** *(cooking)* | Dataset architecture: weighted folders | Does weighting + better refs beat v4? | Read hands axis on rubric |
| **v6** | LR ablation OR +2-3 forelimb refs | Underlearning vs data shortage? | Whichever moves hands axis more |
| **v7** | Caption refinement per v5/v6 failure modes | Which caption patterns drive which axes? | Lock caption methodology |
| **v8** | **Commissioned paleoart refs** (if hands still < 2.0) | Photorealistic anchor breaks the plateau? | Hands → 3.5+ |
| **v9** | Steps bump 1500 → 2000 | Under-training? | Lock step count |
| **v10** | Rank 16 → 32 | More capacity helps anatomy precision? | Lock rank |
| **v11** | Multi-resolution training | Better generalization across crops? | Compare to v10 |
| **v12** | Hyperparameter sweep around v11 winner | Polish | **Ship.** |

Estimated total: ~$50 Replicate cost, ~25-30h focused work spread over 4-8 weeks.

## Cost-reduction strategy (the moat for scaling to multiple species)

Three tiers:

1. **Python (zero AI cost):** source_paleoart, license_audit, dedup_refs run via cron or direct invocation
2. **Local Ollama (zero Anthropic cost):** caption_draft on 2016 MBP overnight
3. **Claude (judgment only):** caption-polisher, strategic decisions, code changes

Target: 5-10x reduction vs current Sonnet-everything approach. Critical for scaling beyond tyrannosaurus to allosaurus, triceratops, spinosaurus, etc.

## Hard rules (do not violate)

- **Single-variable change rule:** v5→v6 changes one thing only. Same for every subsequent version.
- **License whitelist is canonical** — see `license-auditor.md`. No exceptions.
- **Captions are anatomy-only** — see `caption-polisher.md`. Strip lighting/style/environment language every time.
- **Never overwrite v3-v5 training data** when iterating. Each version's dataset zip lives forever for repro.
- **Always re-score under the same rubric** when comparing versions. The strict rubric (0 = not viewable) is canonical going forward.

## Known issues to fix at some point

- Dev mirror (`dino-art-studio`) branch push fails when LFS objects > ~50MB. Production push (`jurassinkart.com`) is fine.
- The v5 `flux/eval/run.py` invocation hasn't been verified end-to-end on a new LoRA — first run might need debugging.
- `tools/caption_draft.py` Ollama vision-model output quality is unverified — first batch will need careful caption-polisher review.

## Strategic frame (re-affirmed)

The competitive moat is **anatomically correct two-fingered T-rex forelimbs at photorealistic quality** — something MJ literally cannot produce per our experiments. Audience: paleo enthusiasts, museum gift shops, educational/kids' market, "dad-buys-this-for-his-dinosaur-obsessed-9-year-old." Premium niche, not mass market. Ship target: v9 plausible, v12 proud-to-show-other-paleoartists. $50K-day path runs through niche premium + scientific-accuracy story, not generic Etsy decor.
