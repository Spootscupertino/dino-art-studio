# Dino Art Studio

A scientific accuracy-first prompt engineering system for generating dinosaur art in Midjourney. Every prompt is grounded in peer-reviewed paleontology — correct posture, locomotion, integument, and anatomy — while remaining optimized for photorealistic and painterly Midjourney outputs.

## What it does

- **Interactive CLI** (`generate_prompt.py`) walks you through species, style, lighting, camera, and mood to build a complete Midjourney `/imagine` prompt
- **Two output modes**: portrait close-up (telephoto, mood-focused) and full-body canvas print (mid-range, rule-of-thirds, print-ready)
- **Scientific brief** displayed at prompt time: body length, mass, locomotion type, integument, tail posture, and wrist position pulled directly from the database
- **Per-species research notes** flag findings that affect prompt accuracy (e.g. Bell et al. 2017 on T. rex scales, Cullen et al. 2023 on theropod lips)
- **Auto-applied required parameters** enforce species-level anatomical accuracy without user input (e.g. correct wrist anatomy for Velociraptor)
- **Global accuracy rules** appended to every prompt: peer-reviewed paleontology, no movie inaccuracies, correct posture and locomotion
- **Prompt history** saved to SQLite with status tracking (`pending → sent → generated → archived`)
- **Reference image scanner** reports how many scientific reference images are loaded per species folder

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

## Quick start

```bash
# First time: create the database
python setup_db.py

# Generate a prompt
python generate_prompt.py

# Options
python generate_prompt.py --ar 16:9 --stylize 500 --chaos 10
python generate_prompt.py --version 6.1 --style raw
```

## Scientific accuracy approach

Each species row in the database carries:

| Field | Example (T. rex) |
|---|---|
| `body_length_m` | 12.0 |
| `body_mass_kg` | 8800 |
| `locomotion_type` | bipedal |
| `feathering_coverage` | uncertain |
| `skin_texture_type` | scales (Bell et al. 2017) |
| `tail_posture` | horizontal, heavily muscled |
| `wrist_position` | palms medially facing |
| `last_scientific_update` | 2023 |

Research notes reference specific papers and are flagged `affects_prompt = 1` when the finding should change the generated text. Species whose `last_scientific_update` predates 2020 are flagged at prompt time.

### Key papers per species

**Tyrannosaurus rex**
- Bell et al. 2017 — scales dominant on adult body, no feather evidence (PLOS Biology)
- Hutchinson & Garcia 2002 — max speed 12–25 km/h, not a sprinter (Nature)
- Persons & Currie 2011 — tail heavily muscled, held horizontal (Acta Palaeontologica Polonica)
- Cullen et al. 2023 — lips present covering teeth at rest, varanid-style not crocodilian (Science)

**Velociraptor**
- Full feather plumage confirmed; propatagium (wing-fold skin) confirmed
- Sickle claw raised off ground during locomotion
- Palms face inward — supination anatomically impossible

## Database schema overview

```
species              — reference data, scientific measurements, integument
parameters           — reusable prompt modifiers (style, lighting, camera, mood, anatomy)
species_parameters   — required params auto-applied per species
global_rules         — accuracy rules appended to every prompt
research_notes       — per-species peer-reviewed findings
prompts              — generated prompt history with status tracking
prompt_parameters    — which parameters were active on each prompt
results              — image outputs, seeds, ratings
```

## Reference images

The `species_reference/<species>/` folders hold skeletal diagrams, fossil photographs, skin texture studies, and life reconstructions. These are not tracked in git due to file size — see the `README.md` in each species folder for the priority specimens and file naming conventions. Minimum 4K resolution; RAW preferred for museum photography; 16-bit TIF for flatbed scans.

## Requirements

- Python 3.10+
- No external dependencies — stdlib only (`sqlite3`, `argparse`, `pathlib`)
- Midjourney account for image generation
