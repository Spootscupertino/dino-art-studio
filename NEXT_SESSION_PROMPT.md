# Next Session — Printify Automation

## Goal
Build a drop-folder watcher that takes Midjourney output images and auto-publishes them as **Poster** and **Wrapped Canvas** products on Printify. One image in → two products live.

## Working directory
`/Users/ericeldridge/dino_art/`

## What already exists
- `.env` contains `PRINTIFY_API_KEY` and `PRINTIFY_SHOP_ID` — already provisioned, do not regenerate.
- `generate_prompt.py` — the Midjourney prompt generator. **Do NOT modify.** Read-only context for this session.
- `RECAP.md` — Idea #2 in "10 Ideas — Next Phase" scopes this feature. Read it first.
- No existing Printify code. Greenfield.

## Scope — what to build

### 1. Drop folder + watcher
- Pick a folder (propose `drops/` at repo root, confirm with user).
- User drops a finished MJ image file (JPG/PNG) into the folder.
- A Python script polls or uses `watchdog` to detect new files and runs the pipeline on each.
- After success, move the file to `drops/published/<timestamp>-<species>/` with a sidecar `.json` of the created Printify product IDs and public URLs.
- On failure, move to `drops/failed/` with an error log.

### 2. Printify product creation — two SKUs per image
For each dropped image, upload once to Printify's image library, then create **both** of:

**Poster** — confirm blueprint + print provider + sizes with user at session start. Propose:
- Blueprint: standard matte poster
- Sizes to enable: 12"×18", 18"×24", 24"×36" (all portrait by default, landscape if image aspect > 1)

**Wrapped Canvas** — confirm blueprint + print provider + sizes. Propose:
- Blueprint: wrapped canvas (gallery wrap)
- Sizes: 16"×20", 18"×24", 24"×36"

Both products:
- Title + description auto-generated from the source filename or sidecar metadata (e.g. `velociraptor_riverbed_epic_aerial.jpg` → "Velociraptor at the Riverbed — Epic Aerial"). Ask user for title/description template.
- Tags: species name, habitat, "paleoart", "wildlife", "dinosaur".
- **Free shipping: always on** — use the Printify per-product shipping override so the customer sees free shipping regardless of the provider's default.

### 3. Image fitting
- Detect source aspect ratio.
- For each product/size, auto-crop or pad the image so it fits the print area without distortion.
- Poster + canvas typically want different bleed — handle both. Use Pillow.
- If the source aspect can't reasonably fit a given size (e.g. 1:1 source, 24×36 target), skip that size and log it — don't publish a cropped disaster.

### 4. Pricing rules
Confirm the exact policy with user before coding. Propose as default:
- **Cost-plus markup:** retail = provider_cost × 2.2, rounded up to the next `.99`.
- Minimum retail floor: $19.99 poster, $49.99 canvas.
- Store the rule in a small YAML/JSON config (`printify_config.yaml`) so it can be tuned without code edits.
- Per-size overrides allowed in the same config.

### 5. Publish
- Create the product via API.
- Publish to the connected storefront.
- Log product_id, public URL, and applied pricing per size to the sidecar `.json`.

## Questions to resolve with user BEFORE writing code
1. Exact poster blueprint + print provider (Printify has multiple — user to pick).
2. Exact canvas blueprint + print provider.
3. Final size list per product.
4. Title/description template — auto from filename vs. sidecar `.json` metadata the user writes alongside the image.
5. Markup formula (confirm the 2.2× / .99 default or override).
6. Whether to auto-publish to storefront immediately or leave as draft for review.
7. Is there a storefront variant image requirement (e.g. lifestyle mockups) or is the raw print-area image enough?

## Out of scope for this session
- Do not touch `generate_prompt.py`, `species/*`, `sref_urls.json`, or any MJ-generation code.
- Do not build a UI — CLI / file-drop only.
- Do not integrate with the A/B testing DB yet. That's a later session.
- Do not add automatic upscaling — assume the user is dropping print-ready resolution.

## Tech hints
- Printify REST API docs: `https://developers.printify.com/`
- Key endpoints: `POST /v1/uploads/images.json`, `POST /v1/shops/{shop_id}/products.json`, `POST /v1/shops/{shop_id}/products/{product_id}/publish.json`, shipping override via `is_default_shipping_method: false` + `handling_time` and per-variant shipping in the product payload.
- Auth: `Authorization: Bearer $PRINTIFY_API_KEY`
- Image upload accepts base64 or URL — use base64 from local file.
- Watchdog: `pip install watchdog` if needed, or a simple 2-second poll loop is fine.
- Keep the codebase's existing style: stdlib where possible, `python3`, no new frameworks.

## Deliverables
- `printify_watcher.py` — main entry (`python3 printify_watcher.py` starts the watcher).
- `printify_config.yaml` — pricing, sizes, blueprints, tags template.
- `printify_api.py` — thin API wrapper module.
- `drops/` folder structure with `.gitignore` for the actual image files.
- Dry-run mode: `--dry-run` flag that does everything except call the live API (logs the payloads it would send).

## Definition of done
- Drop one test image in `drops/`.
- Within 30 seconds, two Printify products exist (poster + canvas), priced per the rule, free shipping on, correctly fit per size.
- Sidecar `.json` lists both product IDs and public storefront URLs.
- Source file moved to `drops/published/…`.
- Re-dropping the same filename does NOT create duplicates — idempotency via a hash or ledger file.

## First message to send in the new chat
> Read `NEXT_SESSION_PROMPT.md` and `RECAP.md` idea #2, then ask me the clarifying questions before writing any code.
