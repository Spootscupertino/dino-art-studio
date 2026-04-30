# tools/ — Gallery sync watcher pipeline (shared infra)

The "drop a file → it appears live" automation. Currently the **best-loved subsystem** in the project — preserve its UX above all else.

## Owner & scope

No single agent owns this — it's shared infra between `site-custodian` (consumes `products.json`) and `printify-publisher` (will hook in alongside). Treat changes here with the same care as production deploy scripts.

## What lives here

```
tools/
├── sync_gallery.py         # Walks site/src/assets/gallery/<category>/, emits products.json
├── sync_and_deploy.sh      # Runs sync_gallery, git add/commit/push (auto-deploy)
├── install_watcher.sh      # Installs launchd agent com.jurassinkart.sync-gallery
└── logs/
    └── sync.log            # Tail this when something feels off
```

## The contract

**Input:** any change inside one of the 5 watched gallery subfolders:
- `site/src/assets/gallery/predators/`
- `site/src/assets/gallery/herbivores/`
- `site/src/assets/gallery/marine/`
- `site/src/assets/gallery/aerial/`
- `site/src/assets/gallery/flora_arthropods/`

**Output:**
1. `site/src/data/products.json` regenerated with full SEO metadata (alt, description, keywords, scientific_name, era, category)
2. Auto-commit on `main` with message `Auto-sync gallery: +N added`
3. Auto-push to `origin` (which dual-pushes to both GitHub remotes)
4. Vercel rebuilds → live in ~2 min

## Critical gotchas

- **launchd `WatchPaths` does not recurse.** Each of the 5 category subfolders is registered separately in `install_watcher.sh`. If you add a new category, register it explicitly.
- **Throttle:** 10s `ThrottleInterval` debounces multiple-file drops. Don't lower it — Vercel build budget.
- **Category is derived from the subfolder**, not from the filename. `SPECIES_META` in `sync_gallery.py` provides scientific_name / era / traits keyed by basename.
- **Manual title overrides stick** — `sync_gallery.py` preserves any `title` already in `products.json`. Re-running won't clobber human edits.
- **SEO fields always re-derive** — improvements to `derive_alt()` / `derive_description()` / `derive_keywords()` propagate to every old entry on next sync.

## Verifying the watcher is alive

```bash
launchctl list | grep jurassinkart    # expect: com.jurassinkart.sync-gallery
tail -f tools/logs/sync.log           # while you drop a file in the gallery
```

To reinstall after editing the agent plist:
```bash
launchctl bootout gui/$UID/com.jurassinkart.sync-gallery 2>/dev/null
bash tools/install_watcher.sh
```

## Future hook for Printify

When `printify/printify_publisher.py` is ready, `sync_and_deploy.sh` will call it (in `--dry-run` mode by default) **after** `sync_gallery.py` and **before** the git commit. Live publishing will remain manual — gated by user running `--live` flag explicitly.

## What this directory does NOT do

- Doesn't generate prompts (that's `mj/`)
- Doesn't talk to Printify (that's `printify/`)
- Doesn't render the site (that's `site/`)
- Doesn't write to the DB (that's `db/`)

If `sync_gallery.py` ever needs DB access for richer SEO metadata, it goes through a thin reader module owned by `mj-logger` — never raw SQL here.
