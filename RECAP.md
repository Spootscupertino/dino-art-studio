# RECAP — Dinosaur Art Prompt Generator

## System
- **Machine:** Mac mini, Terminal, Python 3.9.6
- **Main files:** `/Users/ericeldridge/dino_art/`
- **Script:** `generate_prompt.py`
- **Database:** `dino_art.db`
- **Run with:** `python3 /Users/ericeldridge/dino_art/generate_prompt.py`
- **With references:** `python3 /Users/ericeldridge/dino_art/generate_prompt.py --sref [URL] --cref [URL]`

## Goal
Generate Midjourney images that look like **real wildlife photography** — benchmark is a Cuban crocodile zoo photo, plus komodo dragon hand, ostrich stride, and flamingo foot close-up reference photos. Natural light, animal just existing in habitat, muted color, telephoto bokeh, imperfect focus, film grain. No painterly/illustrated/CGI quality.

## Database Stats
- **30 species** (all with diet + habitat populated)
- **83 parameters:** 31 anatomy, 15 behavior, 14 camera, 4 condition, 4 lighting, 4 mood, 1 style, 10 weather
- Behaviors have a `habitat` column — marine/aerial behaviors only show for matching species
- All anatomy blocks compressed to ~20 words each (down from ~50)

## Current Architecture

### CLI Arguments
| Flag | Default | Purpose |
|------|---------|---------|
| `--style` | `raw` | MJ style mode |
| `--stylize` | `50` | MJ stylize (lowered from 100 for realism) |
| `--chaos` | `0` | MJ chaos |
| `--quality` | `1.0` | MJ quality |
| `--sref` | None | Style reference image URL (biggest realism lever) |
| `--cref` | None | Character reference image URL |
| `--db` | `dino_art.db` | Database path |

### Prompt Assembly Priority Order
1. Environment (period + habitat aware)
2. Subject/anatomy (species description + required params + style)
3. **Feet/claws** (front-loaded — MJ's weakest area)
4. Mouth/teeth/saliva (diet-aware: carnivore vs herbivore)
5. Skin texture (from DB + "different scale sizes, dirty uneven hide")
6. Behavior (habitat-filtered)
7. Composition (mode-driven)
8. Lighting
9. Weather
10. Camera (fixed per mode, or user-selected)
11. Canvas print extras (if applicable)
12. Mood
13. Condition
- Deduplication pass runs before final join — strips exact repeated clauses

### Hardcoded Constants (not in DB)
- **Style:** Always hyperrealism — `"real wildlife photograph, telephoto lens bokeh, background out of focus, muted natural colour, slightly overexposed sky, camera sensor noise, film grain"`
- **Mouth (carnivore):** `"yellowed uneven teeth each a different size, wet pink raw mouth interior, thick saliva stranding between jaws, drool hanging from lower lip, gum line raw and receded"`
- **Mouth (herbivore):** `"grinding teeth worn flat and stained brown, wet pink mouth interior, thick saliva pooling at jaw hinge, drool strand catching light"`
- **Feet/claws:** `"each toe separately gripping ground at different angles, each claw a different length and curvature, visible knuckle joints bending, cracked worn keratin, caked mud between digits, wrinkled leathery toe pads like a komodo dragon foot photographed up close"`
- **Negative prompt:** `"fused digits, blob hands, extra fingers, melted feet, CGI, 3D render, digital art, concept art, illustration, smooth skin, painted sky, gradient sky, cinematic color grading, studio background, black background, white background, fossil, skeleton, museum, diorama, indoors"`

### Vary Region Feet-Fix
- After every prompt, the script outputs a **second prompt** for Vary Region inpainting of feet/claws only
- Workflow: generate → upscale best image → Vary Region → paint over feet → paste feet-fix prompt
- Diet-aware (carnivore talons vs herbivore hooves), marine species get flipper version
- Uses `--stylize 20` (lower than main prompt) for more literal adherence
- Anchored with "komodo dragon foot reference"

### Output Modes (9 total)
portrait, canvas, environmental, extreme_closeup, action_freeze, tracking_side, ground_level, aerial_overhead, dusk_long_exp

### Mood Options (4, all documentary realism)
- `quiet_power` — "animal simply existing, no drama, mundane moment caught on camera"
- `serene` — "calm resting moment, no awareness of camera, documentary stillness"
- `menacing` — "tense predatory stillness, locked gaze, caught mid-hunt by camera"
- `closed_mouth_natural` — "closed mouth, natural resting behavior, no threat display"

### Environments
- Cretaceous: `"Late Cretaceous mudflat, sparse reed beds, bare river bank, grey silt ground"`
- Weather values with sky anchored to "real photographed sky with atmospheric haze at horizon"

## All Changes Made Across Both Sessions

### Session 1 — Museum Aesthetic Fix
- Replaced `photogrammetry skin detail` with `living animal skin texture` everywhere
- Rewrote all 10 species `skin_texture_type` DB values from specimen language to living-animal language
- Added behavior (15), condition (4), weather (10) parameter categories
- Added fossil/skeleton/indoor blockers to negative prompt
- Removed `cinematic`, `chiaroscuro`, `epic scale` from parameter values
- Environment block moved to position 1 in prompt assembly
- Fixed `species["diet"]` KeyError (sqlite3.Row has no `.get()`)
- Added `diet` to `fetch_species` SELECT query

### Session 2 — Realism Overhaul

#### Removed Non-Realism Options
- **Deleted from DB:** whimsical mood, eerie mood, bioluminescent lighting, oil_painting, watercolor, concept_art, ink_etching, paleontology_art styles
- **Removed** silhouette output mode from script
- **Replaced** epic mood → quiet_power
- **Toned down** all camera options (killed cretaceous_bloom entirely; stripped cinematic language from remaining 13)
- **Rewrote** all mood values for documentary wildlife tone

#### Bug Fixes
- **Diet field populated** for all 30 species (20 were blank → carnivores got herbivore mouth text)
- **Behavior habitat filtering** — added `habitat` column to parameters table; marine behaviors only for marine, aerial only for aerial
- **Python 3.9 compatibility** — removed `str | None` union syntax
- **Deduplication engine** — catches repeated clauses from overlapping required params
- **Velociraptor params merged** — full_body_accuracy removed as redundant with raptor_extremity_anatomy

#### Prompt Compression
- **All 31 anatomy blocks compressed** ~60% shorter (removed filler; negative prompt handles "no fused digits")
- **Negative prompt** 144 words → 36 words
- **Canvas print block trimmed**
- **Skin imperfection block** 7 clauses → 2

#### Realism Push (based on komodo/ostrich/flamingo reference photos)
- **Style rewritten:** telephoto bokeh, muted colour, overexposed sky, sensor noise, film grain
- **Feet/claws front-loaded** to prompt position 3 (was 5)
- **Asymmetry language:** "each claw a different length and curvature", "each tooth a different size"
- **Scale variation:** "different scale sizes on different body regions"
- **Komodo dragon foot anchor** in feet block
- **Sky realism:** negative prompt blocks painted/gradient/illustrated sky; weather values anchor real sky
- **Anti-CGI negatives:** CGI, 3D render, digital art, concept art, cinematic color grading, smooth skin

#### Features Added
- `--sref` CLI flag for style reference image URL
- `--cref` CLI flag for character reference image URL
- Reference URLs displayed in output banner
- Vary Region feet-fix prompt auto-generated after every main prompt

## Current Status
- **Environment, feathering, body, mood, color palette, bokeh:** Solved. Images read as wildlife photography.
- **Claws/toes:** Improved but still MJ's fundamental weakness. Prompt text has hit its ceiling. Remaining levers: `--sref` with real foot photos, and Vary Region inpainting.
- **Sky:** Much improved with atmospheric haze anchors and negative prompt blockers.

## Next Priorities
1. **Test `--sref` with real wildlife photo URLs** — komodo foot, flamingo foot, ostrich stride. Single biggest untapped lever.
2. **Test Vary Region feet-fix workflow** — generate → upscale → paint feet → paste feet-fix prompt
3. **Test `--cref`** with specific paleoart to lock body proportions
4. **Try `--stylize` values below 50** — lower = more literal, might help claws
5. **Try other species** — T. rex, Triceratops, Spinosaurus to verify changes work broadly
6. **Build out `species_reference/`** with real animal analogue photos (crocodile skin for theropods, elephant feet for sauropods, etc.)
7. **Consider prompt weight syntax** — MJ `::` weighting on feet block if `--sref` isn't enough

## Reference Photos Identified This Session
- Komodo dragon hand/foot (digits separated, claws at different angles)
- Ostrich pair mid-stride (muted color, overcast, telephoto bokeh, messy feathers)
- Flamingo foot close-up (scale size transition shin→toe, worn keratin, leathery pad)
- Monitor lizard yawning (wet pink mouth, individual claws on rock, bokeh background)
