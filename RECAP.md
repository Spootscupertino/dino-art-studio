# Jurassinkart — Project Recap

## What We're Building

**Goal:** Generate dinosaur images that look like real wildlife photography — telephoto lens, natural light, animal just existing in habitat. Benchmark: a Cuban crocodile zoo photo.

**Platform:** jurassinkart.com — Astro site on Vercel, sells prints via Printify/Etsy.

**The wall we hit with Midjourney:** MJ is a black box. We can tweak prompts and reference images but can't teach it new anatomy. We've hit the ceiling of what prompt engineering alone can do. Solution: run Flux locally on M1 Mac + fine-tune it with a LoRA trained on scientifically accurate reference images. We own the model, we own the results.

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
       |                                 |
       +-----------> winners.json <------+
                          |
                          | (8+ score = training candidate)
                          v
                   flux/train_lora.py
                   (WIP scaffold -- use ai-toolkit externally)
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

## Agent Team

Each agent owns a domain. Handoffs are always **files or DB rows**, never function calls across agents.

```
+-----------------------------------------------------------------+
|  prompt-crafter                                                 |
|  generate_prompt.py                                             |
|  Builds MJ/Flux prompts. Reads species DB + refs.              |
|  T-rex signature, anatomy hints from winners.json               |
+-----------------------------+-----------------------------------+
                              | stdout prompt
                              v
+-----------------------------------------------------------------+
|  ref-curator                                                    |
|  paleoart_refs.json, skeletal_refs.json                         |
|  Manages --sref / --cref reference image library                |
+-----------------------------+-----------------------------------+
                              | refs/*.json (read by prompt-crafter)
                              v
+-----------------------------------------------------------------+
|  mj-logger                                                      |
|  dino_art.db (SQLite)                                           |
|  Logs ratings, feedback, parameter weights                      |
|  feedback_agent.py / unified_feedback.py / auto_rater.py       |
+-----------------------------+-----------------------------------+
                              | winners.json + products.json
                              v
+-----------------------------------------------------------------+
|  printify-publisher                                             |
|  printify_publisher.py                                          |
|  Publishes best images as Posters + Wrapped Canvas to Etsy      |
|  Writes printify_ledger.json                                    |
+-----------------------------+-----------------------------------+
                              | printify_ledger.json
                              v
+-----------------------------------------------------------------+
|  site-custodian                                                 |
|  site/ (Astro)                                                  |
|  jurassinkart.com -- gallery, product pages, Buy buttons        |
|  Auto-deploys from main via Vercel                              |
+-----------------------------------------------------------------+
```

---

## Key Files

| File | What it does |
|---|---|
| `generate_prompt.py` | Builds MJ/Flux prompt. T-rex signature, anatomy hints, 4 variants |
| `unified_feedback.py` | Terminal interview: rate image 1-10, save anatomy notes, track winners |
| `reference.py` | Drag-drop a ref image, interview, saved to winners.json + training_refs/ |
| `auto_rater.py` | Heuristic auto-rating for Flux images (no human needed) |
| `flux/generate_image.py` | Runs Flux-dev locally on M1, supports LoRA |
| `flux/train_lora.py` | LoRA training scaffold -- WIP, use ai-toolkit / SimpleTuner externally |
| `flux/comfyui_server.py` | Local web UI for Flux generation |
| `tools/sync_gallery.py` | Watches gallery folders, syncs to site, auto-deploys |

---

## Where We Are Now

| Phase | Status | What shipped |
|---|---|---|
| Phase A | Done | generate_prompt.py, species DB, parameter weights, MJ feedback loop |
| Phase B | Done | Flux local generation, T-rex signature, auto_rater.py, ComfyUI server |
| Phase C | In progress | LoRA training pipeline -- scaffold exists, training not yet functional |
| Phase D | Not started | Full LoRA loop: collect refs, caption, train, generate, loop |

**Immediate wall:** We've maxed out what prompt engineering can do in MJ. The next leap is LoRA fine-tuning on real reference images, but the training pipeline (`flux/train_lora.py`) is a non-functional scaffold. Training needs to happen via an external tool (ai-toolkit or SimpleTuner) with a properly formatted dataset.

---

## Infrastructure

- **Machine:** Mac mini M1, Terminal, Python 3.9.6
- **Site:** jurassinkart.com (Vercel, auto-deploys from `main`)
- **Repos:** `dino-art-studio` (dev mirror) + `jurassinkart.com` (Vercel), `origin` pushes to both
- **DB:** `dino_art.db` (SQLite, gitignored -- regenerate with `python3 setup_db.py`)
- **Watcher:** launchd agent `com.jurassinkart.sync-gallery` watches 5 gallery subfolders
- **Env:** `.env` at root -- PRINTIFY_API_TOKEN, MIDJOURNEY_*, DISCORD_WEBHOOK_URL
- **Archive:** `.claude/archive/` -- preserved WIP patches (gitignored, machine-local)
