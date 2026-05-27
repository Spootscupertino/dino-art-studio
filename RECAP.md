# Jurassinkart — Project Recap

## What We're Building

**Goal:** Generate dinosaur images that look like real wildlife photography — telephoto lens, natural light, animal just existing in habitat. Benchmark: a Cuban crocodile zoo photo.

**Platform:** jurassinkart.com — Astro site on Vercel, sells prints via Printify/Etsy.

**The wall we hit with Midjourney:** MJ is a black box. We've maxed out prompt engineering. The next leap: run Flux locally on M1 + fine-tune with a LoRA trained on scientifically accurate reference images. We own the model, we own the results.

**Where we are now:** The throwaway T. rex LoRA succeeded. Training ran on Replicate's `ostris/flux-dev-lora-trainer`; the resulting `trex_v1` LoRA beat baseline Flux-dev on 5/5 A/B pairs with mean Δ +7.2 / 25 against the anatomy thesis. We've committed fully to Replicate-Flux for both training and inference and retired the local SDXL stack — local SDXL couldn't load Flux LoRAs, so one coherent cloud stack replaces two incompatible halves. Cost is ~$0.03–0.05 per image, ~$1–3 per training run.

**The discipline:** 5 great refs > 50 mixed refs. One full loop completed > five half-built loops. Don't add more refs until Phase 4 tells us why we'd need them.

---

## The Pipeline (How Images Get Made)

```
REFERENCE IMAGES                  YOUR FEEDBACK
(paleoart, museum,                (rate 1–10 via terminal)
 living analogs)                         |
       |                                 |
       v                                 v
  reference.py                  unified_feedback.py
  (interview +                   (score + anatomy notes)
   anatomy notes)                        |
   + .txt captions                       |
       |                                 |
       +-----------> winners.json <------+
                          |
                          | (signal_type=anatomy_ref)
                          v
                 flux/export_dataset.py
                 (zip image+caption pairs)
                          |
                          v
                 flux/datasets/*_dataset.zip
                          |
                          v
            Replicate ostris/flux-dev-lora-trainer
                 (web UI, ~$1–3, ~20 min)
                          |
                          v
                trained LoRA version hash
                 + flux/loras/<name>.safetensors (archived)
                 + flux/loras/registry.json (registered)
                          |
                          v
              flux/generate.py <-- generate_prompt.py
              (Replicate Flux-dev API)    (builds the prompt)
                          |
                          v
                 flux/ab_test_replicate.py
                 (5 paired seeds, baseline vs LoRA)
                          |
                          v
                 assets/gallery/flux/
                          |
                          v
                 auto_rater.py (heuristic score)
                          |
                     if score 8+ ---------> winners.json (loop)
                          |
                     good images
                          |
                          v
                 site/src/assets/gallery/
                          |
                          v
               tools/sync_gallery.py
               (watcher auto-syncs on drop)
                          |
                          v
                  jurassinkart.com
                          |
                          v
              printify_publisher.py --> Etsy
```

---

## Top 10 Features Built So Far

1. **`prompt` command** — One command, full MJ prompt with T-rex signature, anatomy hints, 4 variants (main + feet/background/mouth fixes). Just type `prompt` and paste into MJ.

2. **`feedback` command** — Terminal interview: drag an image in, rate it 1–10, add anatomy notes. Saves to `winners.json`. High scorers become training data. Closes the loop between generation and improvement.

3. **`reference` command** — Drag-drop a scientifically accurate reference image (paleoart, museum photo, living analog), walk through an anatomy interview, and get it logged as a training example. Batch mode: add multiple images in one session.

4. **Auto-caption generation** — Every reference image gets a `.txt` caption file automatically (`a photo of Tyrannosaurus rex, massive hands, correct skull proportions...`). This is exactly what LoRA trainers (ai-toolkit, SimpleTuner) expect.

5. **`flux/export_dataset.py`** — One command turns all your reference images into an ai-toolkit-ready dataset folder: symlinked images, `dataset.json` metadata, species breakdown summary. No manual file wrangling.

6. **winners.json feedback loop** — A single file that accumulates your best MJ images, Flux generations, and reference photos. Anatomy notes flow into future prompts automatically via `get_winner_anatomy_hints()`. The more you rate, the better the prompts get.

7. **Auto-rater (`auto_rater.py`)** — Heuristic scoring for Flux images. Output is **quarantined to `candidates.json`** — never reaches `winners.json` directly. Manual `--promote` is the gate, since the heuristics aren't validated against anatomical accuracy. Use `--write-candidate`, `--candidates`, `--promote SPECIES INDEX`.

8. **Gallery watcher + auto-deploy** — Drop an image into any gallery subfolder and the launchd watcher auto-syncs to `site/src/assets/gallery/`, pushes to GitHub, and deploys to jurassinkart.com within minutes. Zero manual steps.

9. **Printify pipeline** — Best images publish as Posters and Wrapped Canvas at all sizes on Etsy/Printify. Cost-plus pricing, free shipping override, ledger tracks all product IDs and URLs. **Publish gate:** any Flux-tagged image requires a sibling `<image>.approved` marker before this pipeline (or `tools/sync_gallery.py`) will touch it.

11. **Signal-split winners.json** — Every entry tagged `signal_type ∈ {mj_composition, flux_quality, anatomy_ref}`. Top-3 trim runs per signal_type per species, so MJ winners can't evict Flux winners and reference anatomy stays separated from generated quality.

12. **Anatomy thesis (`refs/anatomy_theses/tyrannosaurus.md`)** — 5 scoring categories (posture, hands, feet, skull-body, realism) and auto-reject conditions (kangaroo posture, 3-finger hands, tail-dragging). The ruler used to judge refs and generated images.

13. **Training-drops ingest (`flux/ingest_training_drops.py`)** — Manual-run pipeline: drop image into `~/Desktop/Jurassinkart/Training Drops/<species>/<source_type>/`, run script, image moves to `assets/gallery/flux/training_refs/` with auto-generated `.txt` and `.json` sidecars. Manual by design — auto-watching here is the trap the publish gate guards against.

10. **Replicate-Flux generation (`flux/generate.py`)** — Single-image CLI calls Replicate's Flux-dev API. With `--lora <name>` looks up the trained LoRA in `flux/loras/registry.json` and POSTs to that version. ~$0.03–0.05/image, 20–40 sec round-trip, no local model weights.

---

## Key Commands

| Command | What it does |
|---|---|
| `prompt` | Generate MJ/Flux prompt with anatomy hints |
| `feedback [image]` | Rate image, save notes, track winners |
| `reference [image]` | Intake a reference image with anatomy interview |
| `python3 flux/export_dataset.py` | Export training dataset for ai-toolkit |

---

## Key Files

| File | What it does |
|---|---|
| `generate_prompt.py` | Builds MJ/Flux prompt. T-rex signature, anatomy hints, 4 variants |
| `unified_feedback.py` | Terminal interview: rate 1-10, save anatomy notes, track winners |
| `reference.py` | Batch intake of reference images + auto .txt captions |
| `auto_rater.py` | Heuristic auto-rating for Flux images |
| `flux/export_dataset.py` | Bundle training_refs into a zip for Replicate trainer |
| `flux/LORA_TRAINING.md` | Replicate-hosted LoRA training workflow |
| `flux/generate.py` | Single-image CLI: calls Replicate Flux-dev (baseline or LoRA) |
| `flux/ab_test_replicate.py` | 5-pair A/B harness for validating a new LoRA |
| `flux/loras/registry.json` | Trained LoRA registry: name → version hash + trigger word |
| `tools/sync_gallery.py` | Watches gallery folders, syncs to site, auto-deploys |

---

## Training Set Audit — v1/v2/v3 (2026-05-14)

What each LoRA actually trained on, reconstructed from Replicate training run inputs.

| LoRA | Images | Autocaption | LR | Steps | Notes |
|---|---|---|---|---|---|
| trex_v1 | 5 | OFF | 0.0004 | 1000 | Clean flat refs: cassowary, 2× paleoart, 2× skeleton. A/B 5/5 Δ+7.2 — valid. |
| trex_v2 | 23 | **ON** | 5e-5 | 1000 | Autocaption=True overrides all hand-written captions. Contains `Allosaurus_skeleton_1.jpg` (non-T-rex contamination). LR 10× lower than v1. Never A/B tested. |
| trex_v3 | 26 | OFF | 1e-4 | 1500 | 19/26 are MJ self-generations (feedback-loop risk). Correct captions. A/B vs v2 running 2026-05-14. |

**Key finding on v2:** `autocaption=True` means the Replicate trainer discarded all hand-written captions and generated its own. The effort spent on caption quality for v2 had zero effect on training. LR drop from 4e-4 → 5e-5 likely underfit. Since v2 was never A/B tested, its position in the champion chain is unknown — v1 may still be the best LoRA.

**Key finding on the subdir bug:** The `training_refs/*` vs `training_refs/**/*` bug in `export_dataset.py` was fixed in the v3 session. v1 was pre-subdir (flat, unaffected). v2 appears to have been built before the subdir structure was fully adopted, so the bug's impact on v2 is unclear. v3 used the corrected glob.

## Where We Are Now

| Phase | Status | What shipped |
|---|---|---|
| Phase A | Done | `generate_prompt.py`, species DB, parameter weights, MJ feedback loop |
| Phase B | Done | Flux local generation, T-rex signature, `auto_rater.py`, ComfyUI server |
| Phase C | Done | `reference.py` batch intake, `.txt` captions, `export_dataset.py`, `LORA_TRAINING.md` |
| Tightening 0 | Done | Three guardrails: signal-split winners.json, auto-rater quarantine, publish gate |
| Tightening 1 | Done | T. rex anatomy thesis at `refs/anatomy_theses/tyrannosaurus.md` |
| Tightening 2 | Done | 5 curated T. rex refs ingested + drop-folder pipeline (`flux/ingest_training_drops.py`) |
| Tightening 3 | Done | Throwaway T. rex LoRA — training submitted to Replicate H200, `.safetensors` downloaded |
| Tightening 4 | Done | A/B test: 5 paired seeds, LoRA won 5/5, mean Δ +7.2 / 25. LoRA promoted. |
| Tightening 5 | Done | Retired local SDXL stack, committed to Replicate-Flux for training + inference |
| Tightening 6 | Done | v2 + v3 LoRA datasets built and submitted to Replicate. v3 registered, A/B underway. |
| Tightening 7 | Done | Training set audit: v2's autocaption=True bug documented. Frozen eval harness built (`flux/eval/`). |

**Current milestone:** Eval harness (`flux/eval/run.py` + `flux/eval/score.py`) provides a single comparable score per LoRA. v4 experiment (drop MJ ratio to ~30%) can proceed once v3 A/B is scored.

---

## Next Level — Ideas to Push Image Quality Further

### Recently done (Tightenings 3–5)
- ✓ **Tightening 3** — Local Flux-dev training OOM'd on M1 (20.13GB / 20.13GB cap). Pivoted to Replicate `ostris/flux-dev-lora-trainer` on H200. Training ID `wad5pnmbb5rmy0cy2z29jefvqw`, 1000 steps, rank 16, lr 0.0004, caption_dropout 0.05.
- ✓ **Tightening 4** — 5-pair A/B test on `flux/ab_test_replicate.py`. LoRA won 5/5, scores: 12.4 → 19.6 (mean Δ +7.2). Vanilla Flux defaults to upright kangaroo / screaming mouth / 3-finger hands. With LoRA: horizontal spine, lifted tail, 2-finger hands, digitigrade stance — the anatomy thesis showing up in the model.
- ✓ **Tightening 5** — Retired local SDXL stack: `generate_image.py`, `comfyui_server.py`, `train_lora.py`, `SETUP.md`, `PHASE_B.md`, the launcher .command, and `DinoGenerator.app`. Created `flux/generate.py` (single-image CLI) and `flux/loras/registry.json`. Rewrote `flux/CLAUDE.md` and `flux/LORA_TRAINING.md`. One coherent cloud stack now.

### Next (Tightening 6+)
- **Species #2 LoRA** — pick a second species (raptor? Triceratops?). Curate 5–10 refs, caption, zip, train, A/B validate.
- **Promote `trex_v1` images** — pick a few hero seeds, generate at higher resolution / vertical AR, add `.approved` marker, push to Printify.

### Short term
- **Species-by-species LoRA library** — one LoRA per species starting with T-rex. Stack multiple LoRAs for mixed-species scenes.
- **LLaVA anatomy validation** — after each generation, auto-run LLaVA to check for anatomical errors (feather coverage, claw count, finger count). Flag failures before you ever see them.
- **ControlNet skeleton guidance** — overlay skeletal reference as ControlNet input to force correct proportions. Especially useful for T-rex bipedal balance.
- **Seed bank** — save seeds that produce good anatomy. Replay with new prompts to explore composition variations without starting over.

### Medium term
- **Optuna LoRA hyperparameter search** — treat rank, alpha, LR, epochs as Optuna params. Auto-optimize training config per species.
- **Multi-species training data sharing** — living analog refs (croc jaw, cassowary leg, eagle eye) apply across species. Tag refs as "jaw-reference" or "foot-reference" so multiple species benefit.
- **Iteration loop timing** — benchmark the full loop (generate → rate → caption → train → generate) and optimize the slowest step. Target: under 2 hours for one full LoRA improvement cycle.
- **Caption quality scoring** — rate caption specificity before training. Vague captions ("looks good") hurt training. Flag and improve them.

### Longer term
- **Photo-real lighting LoRA** — train a second LoRA specifically on lighting style (golden hour, overcast diffuse, telephoto bokeh) separate from anatomy. Combine for full realism.
- **Dynamic habitat generation** — build a habitat generator (forest, riverbank, coastal) that generates consistent environments, then composite dinosaur on top. Separates anatomy quality from environment quality.
- **Print-quality upscaling pipeline** — once you have a great 1024×1024, auto-upscale to 4096×4096 for poster printing using Real-ESRGAN or tile-based Flux upscaling. No quality loss at print size.
- **Public voting gallery** — add a vote button on jurassinkart.com. Visitor votes feed back into winners.json as a quality signal. Crowdsourced anatomy rating.

---

## Plan of Attack — "Ten 10s, then discovery, then LoRA" (2026-05-27)

**Where we landed:** the MJ generator now reliably produces 9/10 epic scenes. We cracked the vast/cinematic look this session — front-load composition + a *crisp* (not hazy) sky, scale from depth + distant pterosaurs, and detail refs at low `--iw` so refs season the skin without flattening the composition. Built into the generator as the **Epic-scale toggle** (`select_epic_scale`, habitat-aware so marine/mosasaur gets underwater god rays, not floodplain clouds).

**Why we can't hit 10s yet, and the sequence to fix it.** LoRA is the eventual path to *reliable* 10s but it's deferred — we can launch 9s now for the website/posters/Google recognition, finish a select few to 10 in Photoshop, and come back to LoRA later (arriving with a curated two-finger-rex corpus built via V7 omni reference). Store reality: ~50 products, 1 sale; site plugged into Google ~early May 2026.

1. **Finishing pipeline (Photoshop) — the real 9→10 lever, do FIRST.** We only need a few great images, and we own the Adobe suite. Build a repeatable Finishing Checklist: fix hands/feet (inpaint or PS patch), clean animal-merge contact zones, upscale to print res, dodge/burn for depth, grade toward the crisp-epic look, sharpen, export. Finish ~10 of the best nines.
2. **Lean the generator.** Stay under MJ's 1300-char Prompt Shortener so *we* control the prompt. A/B the full negative stack vs a ~12-token lean list; delete every `--no` term and `X NOT Y` correction that doesn't change v8.1 output. `build_epic_negative()` is the lean prototype — extend it to the default path.
3. **Feedback flywheel (cheap).** Log every keeper into `winners.json` *with settings* (prompt + refs + `--iw` + `--stylize` + species + look). Double duty: reveals which settings make winners, and becomes the curated LoRA dataset — so keep license + a caption note per image now.
4. **Aesthetic range.** Don't ship 10 identical golden-hour standoffs. Span time of day / weather / species / hero-vs-vast framing / mood — more Google query surface and a gallery with a point of view.

**Then — discovery.** 1 sale / 50 products is a discoverability problem as much as an art one. When the 10 ship, pair them with listing quality + the Google integration (titles, tags, descriptions, alt text, structured data).

---

## Infrastructure

- **Machine:** Mac mini M1, Terminal, Python 3.9.6
- **Site:** jurassinkart.com (Vercel, auto-deploys from `main`)
- **Repos:** `dino-art-studio` (dev mirror) + `jurassinkart.com` (Vercel), `origin` pushes to both
- **DB:** `dino_art.db` (SQLite, gitignored — regenerate with `python3 setup_db.py`)
- **Watcher:** launchd agent `com.jurassinkart.sync-gallery` watches 5 gallery subfolders
- **Env:** `.env` at root — PRINTIFY_API_TOKEN, MIDJOURNEY_*, DISCORD_WEBHOOK_URL
- **Archive:** `.claude/archive/` — preserved WIP patches (gitignored, machine-local)
