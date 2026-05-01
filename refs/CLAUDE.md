# refs/ — Reference image library (ref-curator's domain)

Full build-out deferred to Phase 3. See root CLAUDE.md for migration status.

## What lives here (eventually)

- `paleoart_refs.json` — curated paleoart `--sref` CDN URLs
- `skeletal_refs.json` — skeletal reconstruction `--sref` CDN URLs
- `sref_urls.json` / `sref_sources.json` — flat sref pools by species
- `gallery_best/` — **auto-mirrored from gallery horizontal/ and vertical/ by sync_gallery.py**

## gallery_best/ — feedback loop

`tools/sync_gallery.py` copies every image dropped into
`site/src/assets/gallery/horizontal/` or `.../vertical/` here automatically.
These become the seed pool for context-aware `--sref` selection in future MJ prompts.

```
refs/gallery_best/
├── horizontal/   ← landscape best-of (native MJ 3:2 output)
└── vertical/     ← portrait best-of (cropped/padded for Printify)
```

The ref-curator agent owns writes to the JSON files. `sync_gallery.py` owns writes
to `gallery_best/` only. Never overlap.
