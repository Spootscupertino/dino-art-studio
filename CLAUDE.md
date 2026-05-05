# Jurassinkart — Project Index

This is the *index file*. It points at five domains, each with its own CLAUDE.md and its own owning agent. Keep this file under 60 lines.

**If you're starting a session, jump straight to the right domain — don't load this whole repo into context.**

## Domains

| Path | Owner | What lives there |
|---|---|---|
| [`flux/`](./flux/CLAUDE.md) ⭐ **NEW** | `prompt-crafter` | **Local Flux-dev generation** — M1-optimized image generation with LoRA fine-tuning + branded ComfyUI. This is now the star: most realistic dinosaur images, completely under your control. |
| [`mj/`](./mj/CLAUDE.md) *(coming Phase 4)* | `prompt-crafter` | Midjourney prompt assembly: `generate_prompt.py` (currently at root), `species/`, anatomy modules. |
| [`refs/`](./refs/CLAUDE.md) *(coming Phase 3)* | `ref-curator` | Reference image library: paleoart / skeletal / wildlife `--sref` and `--cref` JSONs (currently at root). |
| [`db/`](./db/CLAUDE.md) *(coming Phase 5)* | `mj-logger` | SQLite schema + A/B test logging (currently `setup_db.py` and `dino_art.db` at root). |
| [`tools/`](./tools/CLAUDE.md) | (shared infra) | Gallery sync watcher pipeline: `sync_gallery.py`, `sync_and_deploy.sh`, `install_watcher.sh`. |
| [`printify/`](./printify/CLAUDE.md) | `printify-publisher` | Printify → Etsy product publishing pipeline. |
| [`site/`](./site/CLAUDE.md) | `site-custodian` | Astro frontend at jurassinkart.com. |

## Cross-domain contracts

Every handoff is a **file or DB row**, never a Python import across domains.

**Generation pipeline (new):**
- `unified_feedback.py` rates image (8+) → `winners.json` + LLaVA anatomy analysis
- `flux/train_lora.py` reads `winners.json` → fine-tunes `flux/loras/dino_winners.safetensors`
- `flux/generate_image.py` or `flux/comfyui_server.py` reads LoRA + `generate_prompt.py` output → generates image
- Generated images → `assets/gallery/flux/` (same contract as MJ)

**Original pipeline (unchanged):**
- `refs/*.json` → `mj/generate_prompt.py` (read-only)
- `mj/generate_prompt.py` → stdout (you paste into Midjourney)
- (you drop image) → `site/src/assets/gallery/<category>/*.png`
- `tools/sync_gallery.py` → `site/src/data/products.json` + git push
- `printify/printify_publisher.py` reads `site/src/data/products.json` + gallery images → writes `printify/printify_ledger.json`
- `site/` reads `printify/printify_ledger.json` to deep-link Buy buttons
- `db/dino_art.db` is shared SQLite; one agent owns writes per table

## Migration status

Decomposition is happening in phases (see `RECAP.md` for the full plan). Currently complete: **Phase 1** (CLAUDE.md scoping). Phase 2 (printify/) in progress. Phases 3–6 (refs/, mj/, db/, RECAP split) deferred to dedicated sessions to avoid mid-session refactor risk.

## Top-level facts that stay here

- Live site: https://jurassinkart.com (Vercel, auto-deploys from `main`)
- Two GitHub remotes: `dino-art-studio` (dev mirror) and `jurassinkart.com` (Vercel-connected). `origin` dual-pushes to both.
- Watcher: launchd agent `com.jurassinkart.sync-gallery` watches the 5 gallery subfolders
- Domain DNS: Network Solutions (`ns99.worldnic.com`); Vercel project handles deploys but not DNS
- `.env` at root holds: PRINTIFY_API_TOKEN, MIDJOURNEY_*, DISCORD_WEBHOOK_URL
