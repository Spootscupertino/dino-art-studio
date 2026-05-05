# Agent Job Descriptions & Specs

Each agent owns a domain, operates independently within it, and publishes outputs that feed other agents. Success = minimal coupling, clear contracts, testable in isolation.

---

## 1. **prompt-crafter**
**Mission:** Generate optimized Midjourney prompts from species + parameters.

### Responsibilities
- Assemble 5-section priority structure (Subject → Interaction → Environment → Lighting → Camera)
- Implement `generate_prompt.py` logic: parameter selection rules, realism anchors, variant outputs
- Manage `--stylize`, `--chaos`, `--ar`, `--sref`, `--cref` flags per species
- Output 4 variants: main + feet-fix / background-fix / mouth-fix specializations
- Validate that `--sref` / `--cref` CDN URLs from `refs/*.json` are current before assembly

### Inputs
- **refs/paleoart_refs.json** — `sref` paleoart URLs by species
- **refs/skeletal_refs.json** — `cref` skeletal URLs by species
- **refs/sref_sources.json** — metadata about each ref (why it's good, anatomy focus)
- **species/*.json** — behavioral/anatomical traits per dino
- **CLI args** — species name, variant type, custom flags

### Outputs
- **stdout** — ready-to-paste Midjourney prompt text
- **logging** → `mj-logger` (optional: log which refs were used for A/B testing)

### Independence Metrics
✓ Works without network calls (refs are local JSON)  
✓ No DB reads (species data is immutable files)  
✓ Can test variants locally with mock refs  
✗ Blocked if refs are broken URLs (but can warn, not fail)

### Team Contracts
- **Consumes:** `refs/*.json` (read-only; curator maintains)
- **Publishes:** stdout (you paste into MJ; no file writes)
- **Talks to:** `ref-curator` (validation only: "are these URLs live?")

### Success Metrics
- Prompts are copy-paste ready (no manual edits)
- Variants meaningfully differ (not just synonyms)
- Flag usage aligns with species anatomy (e.g., high --chaos for chaotic species)

---

## 2. **ref-curator**
**Mission:** Maintain reference image library; ensure all `--sref` / `--cref` URLs are current & labeled.

### Responsibilities
- Add/replace/validate `--sref` (paleoart) and `--cref` (skeletal) image URLs
- Maintain `refs/paleoart_refs.json`, `refs/skeletal_refs.json`, `refs/sref_sources.json`
- Store reference images in `refs/reference_images/` (organized by category)
- Test URLs are live and return valid images (no 404s, redirects, or expired links)
- Document *why* each ref was chosen (anatomy focus, pose quality, realism level)
- Mirror best-performing refs to `refs/gallery_best/` for reuse in future generations

### Inputs
- **User requests** — "add a ref for X", "fix broken sref for Y", "find better paleoart for Z"
- **mj-logger feedback** — which refs won the most A/B tests (best-performing sources)
- **WebSearch/WebFetch** — finding new paleoart/skeletal references online
- **Local gallery images** — identify standout images from past MJ runs to reuse

### Outputs
- **refs/*.json files** — updated with new/fixed URLs
- **refs/reference_images/** — local copies of reference images (for offline access, provenance)
- **refs/gallery_best/** — curated best-of refs from high-performing MJ runs
- **sref_urls.json** — CDN-ready URLs for all refs (consumed by prompt-crafter)

### Independence Metrics
✓ Can research & validate refs independently  
✓ Can test URLs without touching other systems  
✓ No code logic needed (just JSON curation)  
✗ Depends on mj-logger for "which refs won" feedback (async polling OK)

### Team Contracts
- **Consumes:** `mj-logger` best-prompt queries (which refs appear in top-rated runs)
- **Publishes:** `refs/*.json`, `sref_urls.json` (consumed by prompt-crafter)
- **Talks to:** `mj-logger` (read: ratings per prompt), `prompt-crafter` (validate: are these URLs being used?)

### Success Metrics
- Zero broken URLs in refs/* (weekly health check)
- All refs have documented anatomy/style rationale
- Refs are replaced/upgraded when better ones found
- gallery_best/ grows from high-rating MJ runs

---

## 3. **mj-logger**
**Mission:** Track Midjourney generations, log ratings, enable A/B testing & best-prompt queries.

### Responsibilities
- Record every MJ run: prompt + parameters + result image + user rating
- Mark prompts: sent / generated / archived
- Store ratings (1-5 stars, or discrete: ✓/✗)
- Enable queries: "what's my best prompt for species X?" / "which refs won the most?"
- A/B test tracking: same prompt, different --sref / --chaos / --ar → which variant won?
- Expose query API for ref-curator ("top refs by win rate") and printify-publisher ("top-rated images")

### Inputs
- **CLI trigger** — "log this MJ run" with prompt text, image path, rating
- **dino_art.db schema** — prompts, results, ratings tables
- **Midjourney image files** — from `site/src/assets/gallery/` (images tagged by species/variant)

### Outputs
- **dino_art.db** — updated rows in prompts, results, ratings tables
- **Query API** (e.g., CLI or Python functions):
  - `best_prompt_for(species)` → top-rated prompt
  - `top_refs_by_win_rate(species, limit=5)` → which --sref won most
  - `find_variant(species, variant_type)` → best mouth/feet/background fix

### Independence Metrics
✓ Fully independent: owns database, reads gallery files, no network calls  
✓ Can run queries anytime without external dependencies  
✗ No automatic polling (human-triggered logging, async ref feedback)

### Team Contracts
- **Consumes:** `site/src/assets/gallery/` images (read-only; sync_gallery writes)
- **Publishes:** dino_art.db + query API (consumed by ref-curator, printify-publisher)
- **Talks to:** `ref-curator` (provides: "which refs ranked high?"), `printify-publisher` (provides: "top-rated images for product X?")

### Success Metrics
- Every MJ run can be tagged (species, variant, refs used, rating)
- A/B test results are queryable (e.g., "high-chaos beats low-chaos for Triceratops")
- Best-prompt queries are fast (<1s)
- Ratings drive ref curator decisions

---

## 4. **printify-publisher**
**Mission:** Transform top-rated gallery images → Printify products (posters + wrapped canvas), price, publish.

### Responsibilities
- Auto-crop/pad MJ images to print-safe aspect ratios (Poster: 18x24, Wrapped Canvas: 24x36)
- Manage two-SKU publishing: Poster + Wrapped Canvas per image, all sizes
- Calculate cost-plus pricing: material cost + print cost + margin, floor at $X.99
- Override shipping (free on products >$Y)
- Maintain `printify_ledger.json`: product IDs, URLs, pricing, SKU mapping
- Dry-run mode: validate before pushing live
- Query mj-logger for "top-rated images" to prioritize publishing

### Inputs
- **site/src/assets/gallery/\*.png** — source images (from sync_gallery)
- **site/src/data/products.json** — product metadata (title, species, description, SKU)
- **mj-logger queries** — top-rated images by species
- **Printify REST API** — upload images, create products, read pricing

### Outputs
- **printify_ledger.json** — product IDs, URLs, SKU→Printify ID mapping, pricing
- **site/src/data/products.json** — updated with printify product URLs (for "Buy" links)
- **Printify platform** — published products (live or draft per dry-run flag)

### Independence Metrics
✓ Can crop/price images locally without Printify API  
✓ Dry-run lets you validate before publishing  
✗ Requires Printify API key (env var) for live publishing  
✗ Depends on products.json schema (tight coupling to site-custodian)

### Team Contracts
- **Consumes:** `site/src/assets/gallery/`, `site/src/data/products.json` (read + update)
- **Publishes:** `printify_ledger.json` (read by site-custodian for Buy links)
- **Talks to:** `mj-logger` (queries: "which images ranked highest?"), `site-custodian` (updates: products.json with Printify URLs)
- **External:** Printify API

### Success Metrics
- All images have 2 SKUs (Poster + Canvas) at all standard sizes
- Pricing is cost-plus with consistent margin
- Products live on Printify with correct images/URLs
- printify_ledger.json matches Printify platform state

---

## 5. **site-custodian**
**Mission:** Maintain Astro frontend, SEO, product rendering, Buy button integration.

### Responsibilities
- Render gallery (all 7 categories: 5 original + horizontal/vertical best-of)
- Pull product data from `products.json` (species, title, image, description)
- Deep-link Buy buttons to Printify URLs from `printify_ledger.json`
- Manage SEO (meta tags, Open Graph, Google Search Console integration)
- Auto-deploy to Vercel on `main` push
- Monitor build/preview; report errors to user
- Sync watcher integration: auto-rebuild when gallery images land in `site/src/assets/gallery/`

### Inputs
- **site/src/data/products.json** — product metadata
- **printify_ledger.json** — Printify product URLs (for Buy buttons)
- **site/src/assets/gallery/\*.png** — gallery images (from sync_gallery)
- **Google Search Console API** — SEO metrics (optional dashboard)
- **Vercel API** — deploy status, preview URLs

### Outputs
- **jurassinkart.com** — live Astro site
- **Vercel deployments** — auto-preview on branches
- **Google Search Console** — indexed URLs, search performance
- **site/src/data/products.json** — updated with Printify URLs (if sync with printify-publisher)

### Independence Metrics
✓ Can build & test locally without external APIs  
✓ Vercel deploy is automated (just merge to main)  
✓ Gallery render is static, no real-time dependencies  
✗ Tight coupling to products.json schema (shared with printify-publisher)

### Team Contracts
- **Consumes:** `site/src/data/products.json` (read), `printify_ledger.json` (read), `site/src/assets/gallery/` (read)
- **Publishes:** jurassinkart.com (live site)
- **Talks to:** `printify-publisher` (consumes ledger for Buy links), `sync_gallery` watcher (watches: when gallery changes, rebuild)
- **External:** Vercel, Google Search Console

### Success Metrics
- Gallery renders all 7 categories with correct images
- Buy buttons link to live Printify products
- SEO meta tags are current (species name, description, image)
- Site is live within 2 min of merge to main
- Mobile & desktop responsive

---

## Cross-Domain Contracts (Handoff Table)

| From | To | File | Format | Frequency | Coupling |
|---|---|---|---|---|---|
| prompt-crafter | (you) | stdout | text | on-demand | none |
| prompt-crafter | mj-logger | (log call) | SQL | per run | optional |
| ref-curator | prompt-crafter | refs/*.json | JSON | ad-hoc | weak |
| ref-curator | mj-logger | (query call) | API | weekly | weak |
| mj-logger | ref-curator | query result | JSON | async | weak |
| mj-logger | printify-publisher | query result | JSON | per publish | weak |
| sync_gallery | site-custodian | site/src/assets/gallery/ | PNG | file watch | watch event |
| sync_gallery | mj-logger | (indirect) | — | — | — |
| printify-publisher | site-custodian | products.json + ledger | JSON | per product | medium |
| site-custodian | (vercel) | main branch | git | per push | external |

---

## Design Principles

**Autonomy:** Each agent can work independently; no agent calls another agent's functions directly. Handoffs are files or DB queries, never imports.

**Immutability:** Input data (refs/*.json, products.json) are read-only from each agent's perspective. Only the owning agent writes.

**Testing:** Each agent should have a test mode:
- prompt-crafter: generate variants with mock refs
- ref-curator: validate URLs without writing
- mj-logger: query local DB without logging
- printify-publisher: dry-run crop/price without API calls
- site-custodian: build locally, test with mock data

**Scalability:** Agents can be parallelized; nothing serializes across the pipeline (no agent waits for another to finish before starting).

**Ownership:** If an agent needs to modify a file, it owns that file. All writes go through the owning agent.
