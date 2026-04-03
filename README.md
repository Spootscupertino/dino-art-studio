# Dino Art Studio
Built for a print-on-demand dinosaur art studio.

We don’t generate dinosaur art.

We reconstruct lost animals.

Every image is built from peer-reviewed paleontology—real anatomy, real movement, real biology—then pushed through a cinematic prompt system to produce images that feel alive.

No movie myths. No broken hands. No museum stiffness.

Just dinosaurs as they actually were.

## Why this exists
Most dinosaur art is wrong.

- Wrists are broken
- Tails drag
- Teeth are exposed incorrectly
- Skin and feathers are guessed or outdated

Even when people don’t consciously notice it, they feel it.

This system fixes that.

## What this is
A scientific reconstruction engine disguised as a prompt generator.

- Species-specific anatomy rules enforced automatically
- Peer-reviewed research embedded directly into generation
- Cinematic framing system designed to avoid “museum fossil” outputs
- Repeatable pipeline for consistent, high-quality results

## What it does
- **Interactive CLI** (`generate_prompt.py`) walks you through species, style, lighting, camera, and mood to build a complete Midjourney `/imagine` prompt
- **Auto-applied required parameters** enforce species-level anatomical accuracy without user input
- **Scientific brief** displayed at prompt time: body length, mass, locomotion type, integument, tail posture, and wrist position pulled directly from the database
- **Per-species research notes** flag findings that affect prompt accuracy
- **Prompt history** saved to SQLite with status tracking (`pending → sent → generated → archived`)
- **Reference image scanner** reports how many scientific reference images are loaded per species folder

## Generation modes
Not styles—field scenarios.

- **Predator Lens Mode**: telephoto compression, shallow depth, tension-heavy compositions
- **Field Study Mode**: naturalistic framing, environmental storytelling, observational realism
- **Breakout Mode**: motion-driven, dynamic, animal caught mid-action—not posed
- **Canvas Frame Mode**: print-first composition, rule-of-thirds, gallery-ready

## Scientific backbone
Each species includes:

- Body length and mass
- Locomotion type
- Skin/feather evidence
- Tail posture
- Wrist orientation
- Latest research updates

Key findings directly influence prompt output.

## The difference
Most workflows: prompt → image → hope it looks right

This workflow: research → constraints → prompt → image → iterate

Accuracy isn’t optional—it’s enforced.

## Quick start
```bash
python setup_db.py
python generate_prompt.py
```

## Project structure
```
dino_art/
├── generate_prompt.py      # Main interactive CLI
├── setup_db.py             # Creates and seeds dino_art.db from scratch
├── migrate_scientific.py   # Adds/updates scientific accuracy data in the DB
├── schema.sql              # Full SQLite schema
└── species_reference/      # Per-species scientific reference materials
    ├── tyrannosaurus_rex/  # Skeletal diagrams, fossil photos, skin studies
    ├── velociraptor/
    ├── triceratops/
    └── ...                 # README.md in each folder lists priority sources
```

The database (`dino_art.db`) is not tracked in git — regenerate it with `setup_db.py`.
