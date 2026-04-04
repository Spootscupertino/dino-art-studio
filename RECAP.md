# Prompt Engineering Changes — Session Recap

## Problem
Generated images consistently looked like museum specimens or fossil displays rather than living animals in natural environments.

## Root Causes Found

### 1. `photogrammetry skin detail` (generate_prompt.py + setup_db.py)
Midjourney associates "photogrammetry" with 3D fossil/specimen scanning. Replaced with `living animal skin texture` everywhere.

### 2. `skin_texture_type` DB values (migrate_scientific.py + live DB)
Every species had specimen/fossil language embedded in their skin block:
- `osteoderms, keeled scutes, dense armor (extensively documented)` → `interlocking bony armor plates covering back and flanks, each raised scute with a keeled ridge, thick leathery living hide between plates, heavily armored skin`
- `pebbly scales (mummified specimens of close relatives)` → `pebbly mosaic scales across body, smooth rounded scale texture, hide loose and folded at joints`
- `conical scales (specimens known)` → `conical raised scales covering body, rough interlocking hide, each scale individually defined`
- All 10 species updated in both migrate_scientific.py and the live DB.

### 3. Style parameter names (setup_db.py)
- `natural history plate` → `wildlife field illustration`
- `natural history illustration` → `wildlife ecology illustration`

### 4. Prompt length (350+ words)
Midjourney loses the "living wild animal" signal when the positive prompt is bloated. Individual DB parameter values were 40–80 words each.

## Fixes Applied

### generate_prompt.py
- `HYPERREALISM_STYLE`: replaced `photogrammetry skin detail` with `living animal skin texture`
- `MOUTH_TEETH_CARNIVORE`: trimmed from 36 to 12 words
- `MOUTH_TEETH_HERBIVORE`: trimmed from 22 to 11 words
- `FEET_CLAWS`: trimmed from 26 to 13 words
- `ENVIRONMENTS` dict: all values cut to one tight phrase, 4–7 words each
- `CANVAS_SPECIES_EXTRAS`: trimmed
- All `OUTPUT_MODES` composition and fixed_camera strings trimmed to 8–12 words
- Inline placement composition strings trimmed to 8–10 words
- `global_rules` removed from positive prose (redundant with `--no` block)
- Removed malformed word-slice cap; budget controlled at source instead
- Fixed coloration filter to also skip bare `"unknown"` values
- Fixed `species.get("diet")` → `species["diet"]` (`sqlite3.Row` has no `.get()`)
- Added `diet` to `fetch_species` SELECT query (was missing, caused KeyError)
- Environment block now assembles FIRST in `prose_parts`, before species/anatomy — forces MJ to establish the outdoor setting before processing anatomy detail
- `NEGATIVE_PROMPT`: added fossil/skeleton blockers — `fossil, fossilized, skeleton, skeletal, bones, bone structure, excavation, petrified, museum specimen, rock matrix, sediment, dinosaur fossil, fossil record, prehistoric bones, mineralized, stone cast, osteoderms, osteoderm`
- `NEGATIVE_PROMPT`: added indoor/built environment blockers — `indoors, interior, building, warehouse, arena, concrete floor`

### setup_db.py
- Added `behavior` (15 params), `condition` (4 params), `weather` (10 params) to `SEED_PARAMETERS` with all values ≤15 words
- Added fossil/skeleton/osteoderm blockers to `NEGATIVE_PROMPT` seed
- Replaced museum-adjacent style names
- Added `SEED_SKIN_CORRECTIONS` dict — 5 species whose skin textures were seeded outside `migrate_scientific.py`; applied as UPDATEs during seeding so a fresh re-seed produces living-animal language
- Removed studio/indoor lighting words from seed values: `cinematic`, `chiaroscuro`, `dramatic rim lighting`, `cinematic grandeur`, `epic scale`

### migrate_scientific.py
- All 10 `skin_texture_type` values rewritten to living-animal language
- Removed all parenthetical specimen/source notes from skin descriptions

### Live DB (`dino_art.db`)
- All 29 behavior/condition/weather parameter values updated directly
- All 15 species `skin_texture_type` values updated directly (10 via migrate_scientific.py path + 5 via direct SQL)
- Removed `cinematic`, `chiaroscuro`, `cinematic grandeur`, `epic scale` from 4 parameter values (`dramatic_rim`, `epic`, `dawn_plains`, `tracking_panning`)

## Verified Output (Ankylosaurus portrait, rim lighting, epic mood, weathered adult, scanning territory)

**172 words — positive prompt only, environment leads:**

```
Late Cretaceous river delta, open floodplain, flowering plants, large Ankylosaurus, Armored dinosaur with club tail, tail posture: horizontal, club actively swung, five-toed forefeet with short stubby rounded hooflike nails each individually visible, four-toed hindfeet with short blunt claws separately defined, columnar pillar limbs supporting armored weight, toes compact but each one distinctly separated, no merged or fused digits, hyperrealistic, anatomically accurate, living animal skin texture, subsurface scattering, 8K texture, interlocking bony armor plates covering back and flanks, each raised scute with a keeled ridge, thick leathery living hide between plates, heavily armored skin, wet lips parted, grinding teeth worn flat, saliva catching light along jaw, individual toe pads weight-bearing, natural keratin wear on claws, dirt caught between digits, head raised, body still, eyes on middle distance, nostrils flared, territorial survey, strong rim lighting, deep shadows, high contrast, cloudless sky, hard directional light, crisp shadows, fully saturated colours, shot on medium shot, three-quarter view, natural pose, vast scale, awe-inspiring, monumental presence, weathered hide, healed scratches on flanks, thickened skin at joints, subtle asymmetry
```

## Outstanding
None — all known museum-aesthetic sources resolved.
