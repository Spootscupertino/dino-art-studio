# Jurassinkart — Project Recap

## What We're Building

**Goal:** Generate dinosaur images that look like real wildlife photography — telephoto lens, natural light, animal just existing in habitat. Benchmark: a Cuban crocodile zoo photo.

**Platform:** jurassinkart.com — Astro site on Vercel, sells prints via Printify/Etsy.

**The wall we hit with Midjourney:** MJ is a black box. We've maxed out prompt engineering. The next leap: run Flux locally on M1 + fine-tune with a LoRA trained on scientifically accurate reference images. We own the model, we own the results.

**Where we are now:** Pipeline is hardened with three guardrails (signal-split winners.json, auto-rater quarantine, publish gate), anatomy thesis written for T. rex, 5 curated training refs ingested (skeletal x2, paleoart x2, living analog cassowary x1). Phase 3 is the throwaway LoRA — train it, see what comes out, learn from the result.

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
                          | (8+ score = training candidate)
                          v
                 flux/export_dataset.py
                 (formats for ai-toolkit)
                          |
                          v
                 flux/datasets/dino_refs/
                          |
                          v
                   ai-toolkit (external)
                          |
                          v
                 flux/loras/dino_winners.safetensors
                          |
                          v
              flux/generate_image.py  <-- generate_prompt.py
              (M1 Mac, local Flux-dev)     (builds the prompt)
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

10. **Local Flux on M1** — Flux-dev runs on the Mac mini in ~45 seconds per image at bfloat16 precision with MPS acceleration. LoRA loading support is wired. ComfyUI server for visual iteration. No API bills, no rate limits.

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
| `flux/export_dataset.py` | Export training_refs as ai-toolkit dataset |
| `flux/train_lora.py` | LoRA scaffold — WIP, use ai-toolkit externally |
| `flux/LORA_TRAINING.md` | Step-by-step guide to collect → export → train |
| `flux/generate_image.py` | Runs Flux-dev locally on M1, supports LoRA |
| `flux/comfyui_server.py` | Local web UI for Flux generation |
| `tools/sync_gallery.py` | Watches gallery folders, syncs to site, auto-deploys |

---

## Where We Are Now

| Phase | Status | What shipped |
|---|---|---|
| Phase A | Done | `generate_prompt.py`, species DB, parameter weights, MJ feedback loop |
| Phase B | Done | Flux local generation, T-rex signature, `auto_rater.py`, ComfyUI server |
| Phase C | Done | `reference.py` batch intake, `.txt` captions, `export_dataset.py`, `LORA_TRAINING.md` |
| Tightening 0 | Done | Three guardrails: signal-split winners.json, auto-rater quarantine, publish gate |
| Tightening 1 | Done | T. rex anatomy thesis at `refs/anatomy_theses/tyrannosaurus.md` |
| Tightening 2 | Done | 5 curated T. rex refs ingested + drop-folder pipeline (`flux/ingest_training_drops.py`) |
| Tightening 3 | IN PROGRESS | Throwaway T. rex LoRA — training submitted to Replicate H200, awaiting .safetensors |
| Tightening 4 | Next | A/B test: 25 paired seeds with/without LoRA, rated against the thesis |
| Tightening 5 | Pending | Decide: keep, iterate config, or kill the LoRA |

**Current milestone:** Training job ID `wad5pnmbb5rmy0cy2z29jefvqw` submitted to Replicate. Status: Processing on H200 GPU. Config: 1000 steps, rank 16, lr 0.0004, batch 1, res 512/768/1024, caption_dropout 0.05. ETA: ~20 min. Cost: ~$1.50–3.00. Next session: download trex_v1.safetensors from training detail page, run the 25-pair A/B test from `flux/ab_test_plan_trex_v1.md`.

---

## Next Level — Ideas to Push Image Quality Further

### Immediate (Tightening 3 — IN PROGRESS)
- ✓ **Phase A smoke test** — Local Flux-dev load on M1 failed at MPS watermark (exit 3 OOM: 20.13GB > 20.13GB cap). Concluded local training infeasible.
- ✓ **Pivot to Replicate** — Submitted 1000-step LoRA training to Replicate ostris/flux-dev-lora-trainer on H200 GPU. Training ID: `wad5pnmbb5rmy0cy2z29jefvqw`. Status: Processing. ETA: ~20 min.
- ✓ **A/B test plan drafted** — `flux/ab_test_plan_trex_v1.md` — 25 paired seeds, with vs. without LoRA, sidecar-tagged `.approved=false` (publish gate blocks accidental shipping).
- ✓ **Dataset pipeline** — `flux/zip_dataset.py` bundles 5 image+caption pairs into 2.5MB zip. Uploaded and ingested by Replicate.

### Next (Tightening 4 — A/B Testing)
- **Download trex_v1.safetensors** from Replicate training detail page → `flux/loras/trex_v1.safetensors`
- **Run A/B test** — execute both with_lora and without_lora generations for all 25 seeds, save to `assets/gallery/flux/ab_tests/trex_v1/`
- **Rate against anatomy thesis** — score all 50 images (1–5) across 5 categories from `refs/anatomy_theses/tyrannosaurus.md`
- **Analyze** — mean delta, win rate per seed. Success threshold: mean ≥ 2.0, LoRA wins ≥ 18/25 pairs

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

## Infrastructure

- **Machine:** Mac mini M1, Terminal, Python 3.9.6
- **Site:** jurassinkart.com (Vercel, auto-deploys from `main`)
- **Repos:** `dino-art-studio` (dev mirror) + `jurassinkart.com` (Vercel), `origin` pushes to both
- **DB:** `dino_art.db` (SQLite, gitignored — regenerate with `python3 setup_db.py`)
- **Watcher:** launchd agent `com.jurassinkart.sync-gallery` watches 5 gallery subfolders
- **Env:** `.env` at root — PRINTIFY_API_TOKEN, MIDJOURNEY_*, DISCORD_WEBHOOK_URL
- **Archive:** `.claude/archive/` — preserved WIP patches (gitignored, machine-local)
