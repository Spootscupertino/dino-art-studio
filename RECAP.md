# Jurassinkart — Project Recap

## What We're Building

**Goal:** Generate dinosaur images that look like real wildlife photography — telephoto lens, natural light, animal just existing in habitat. Benchmark: a Cuban crocodile zoo photo.

**Platform:** jurassinkart.com — Astro site on Vercel, sells prints via Printify/Etsy.

**The wall we hit with Midjourney:** MJ is a black box. We've maxed out prompt engineering. The next leap: run Flux locally on M1 + fine-tune with a LoRA trained on scientifically accurate reference images. We own the model, we own the results.

**Where we are now:** First T-rex reference image is in. Training starts next. We're going species by species, starting with T-rex.

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

7. **Auto-rater (`auto_rater.py`)** — Heuristic scoring for Flux images with no human required. Checks sharpness, composition, color, anatomy keywords. High scorers auto-feed into winners.json while you sleep.

8. **Gallery watcher + auto-deploy** — Drop an image into any gallery subfolder and the launchd watcher auto-syncs to `site/src/assets/gallery/`, pushes to GitHub, and deploys to jurassinkart.com within minutes. Zero manual steps.

9. **Printify pipeline** — Best images auto-publish as Posters and Wrapped Canvas at all sizes on Etsy/Printify. Cost-plus pricing, free shipping override, ledger tracks all product IDs and URLs.

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
| Phase D | In progress | LoRA training — first T-rex reference image in, training next |
| Phase E | Not started | Generate with trained LoRA, evaluate, tighten loop |

**Current milestone:** First reference image is in (`training_refs/`). Dataset pipeline is ready. Next session: collect more T-rex references, run `export_dataset.py`, install ai-toolkit, train first LoRA.

---

## Next Level — Ideas to Push Image Quality Further

### Immediate (next session)
- **Collect 10–20 T-rex reference images** — paleoart from Witton/Csotonyi, museum skeletal mounts, bird/croc living analogs. More refs = better LoRA signal.
- **Train first T-rex LoRA** — install ai-toolkit, run training on `flux/datasets/dino_refs/`, save to `flux/loras/trex_v1.safetensors`.
- **A/B test LoRA vs. base** — generate same prompt with and without LoRA, rate both, compare anatomy accuracy.

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
