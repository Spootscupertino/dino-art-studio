# Next Session — Wire Up trex_v3 + Validate End-to-End

## What's already done

Previous session built and submitted the trex_v3 training to Replicate:

- **Dataset:** `flux/datasets/trex_v3_dataset.zip` — 26 verified ref pairs (19 MJ self-generated, 4 Wikimedia, 3 living-analog). 1 cassowary stays quarantined.
- **Training submitted:** `spootscupertino/trex_v3` on `ostris/flux-dev-lora-trainer`, trigger `trex_v3`, **LR 1e-4, 1500 steps, rank 16, batch 1, caption_dropout 0.05, autocaption OFF**.
- **Registry:** trex_v2 backfilled in `flux/loras/registry.json` (version `d8b82ba07d8e…`, training_id `yzx4g2vpesrmy0cy49tvqap360`).
- **A/B harness:** `flux/ab_test_replicate.py` is now v3-vs-v2 (champion = v2, challenger = v3), reads the registry, mouth-focused base prompt. It will refuse to run until trex_v3 has a `version` field set.
- **Pipeline patches:**
  - `flux/ingest_training_drops.py` — 4 new source_types (`integument`, `biomech_mouth`, `corrected_mj`, `extremes_macro`), `Midjourney` license allowed, pre-staged sidecars are preserved on ingest instead of clobbered.
  - `flux/export_dataset.py` — recurses into subdirs (was only scanning top level — silent bug), skips quarantined refs, emits a flat zip alongside the symlink folder.
- **Drop folder state:** `~/Desktop/Jurassinkart/Training Drops/tyrannosaurus/_quarantine/1773421176-02lhewettsuesuite333.webp` is held back (provenance unknown — Field Museum Sue Suite suspected but unverified). Decide before next training cycle.

## Goal for next session

Get trex_v3 from "training kicked off" → "validated, registered, generating live art" in one clean sweep. The whole point of the wire-up is to **prove the pipeline works end-to-end without manual rescue**, so any seam that breaks is a bug worth fixing in code, not papering over by hand.

## Step-by-step

### 1. Confirm training finished

Check the Replicate dashboard or hit the API:

```bash
source /Users/ericeldridge/dino_art/.env
curl -s -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
  https://api.replicate.com/v1/models/spootscupertino/trex_v3 \
  | jq '{owner, name, latest_version: .latest_version.id}'
```

If `latest_version.id` is null → training still running or it failed. If failed, pull the run logs from the Replicate run page and decide whether to retry with adjusted params before doing anything else.

### 2. Register trex_v3 in `flux/loras/registry.json`

Add the new entry next to v1 and v2:

```json
"trex_v3": {
  "replicate_owner": "spootscupertino",
  "replicate_model": "trex_v3",
  "version": "<hash from step 1>",
  "trigger_word": "trex_v3",
  "trained_on": "<YYYY-MM-DD of run completion>",
  "training_id": "<from Replicate run URL>",
  "ab_test_winrate": null,
  "ab_test_mean_delta": null
}
```

### 3. Fire the 5-pair A/B

```bash
python3 flux/ab_test_replicate.py
```

Outputs land in `assets/gallery/flux/ab_tests/trex_v3/{champion_v2,challenger_v3}/seed_XXXX.png`.

Each pair shares a seed so the only variable is the LoRA. Score on the 5-category anatomy rubric (proportions, hands, feet/digits, mouth/lips/teeth, skin/integument — 1–5 each, max 25). Mouth gets extra weight here since that was the explicit reason for v3.

**Promotion thresholds:** mean Δ ≥ +2.0, win rate ≥ 4/5. Record both back into the registry entry.

### 4. Generate 3 hero shots

```bash
python3 flux/generate.py --prompt "<prompt>" --seed <n> --lora trex_v3 --output assets/gallery/flux/<path>.png
```

Three poses to lock in:
- Mouth-open roar (the thing v3 is supposed to fix)
- Frontal binocular portrait
- Full-body action shot in environment

Compare side-by-side with the v2 hero shots. Honest rating; target ≥ 7/10 with mouth specifically ≥ 7/10.

### 5. End-to-end wire-up check (don't skip)

This is the actual point of next session — verify each domain handoff still works:

| Check | Pass condition |
|---|---|
| `flux/generate.py --lora trex_v3` runs | PNG + sidecar JSON land in target path |
| `tools/sync_gallery.py` picks up new flux assets | `site/src/data/products.json` updates |
| Site builds | `cd site && npm run build` exits 0 |
| Printify ledger still references valid gallery paths | `printify/printify_ledger.json` keys all resolve to files |
| Registry → ab_test → generate flow | All three read `flux/loras/registry.json` consistently |

If any of those break, fix in code rather than handing me a workaround. The whole "decompose into domain CLAUDE.mds" project is so each seam stays clean.

### 6. Decide on the quarantined webp

`Training Drops/_quarantine/1773421176-02lhewettsuesuite333.webp` is sitting unused. Options:
- Confirm Field Museum source + CC license → un-quarantine, fold into v4 dataset
- Delete if unidentifiable
- Leave quarantined indefinitely (worst option — clutter)

### 7. Update RECAP.md

Once v3 is validated, append a line to `RECAP.md` recording: training run ID, A/B winrate/Δ, hero-shot scores. Keeps the lineage legible for future sessions.

## Hard rules that still apply

- **Dev/Ops boundary:** I (Claude) don't pull, scrape, or download reference images. You drop them in `Training Drops/`; I ingest.
- **License allowlist:** `flux/ingest_training_drops.py --validate --species tyrannosaurus` must pass clean (modulo the quarantined cassowary) before any future training. NC/ND are auto-rejected. Midjourney self-gen is allowed.
- **Registry is the source of truth** for model versions. `ab_test_replicate.py` and `generate.py` both read it. Don't hardcode hashes anywhere else.
- **Captions matter more than image count.** If a future training disappoints, look at the `.txt` files first.

## Files to read at session start

- [flux/loras/registry.json](flux/loras/registry.json) — current LoRA roster
- [flux/ab_test_replicate.py](flux/ab_test_replicate.py) — v3-vs-v2 harness, mouth-focused prompt
- [flux/LORA_TRAINING.md](flux/LORA_TRAINING.md) — promotion thresholds, full recipe
- [flux/CLAUDE.md](flux/CLAUDE.md) — domain contract
