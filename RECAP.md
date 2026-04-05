# RECAP — Dinosaur Art Prompt Generator

## System
- **Machine:** Mac mini, Terminal, Python 3.9.6
- **Main files:** `/Users/ericeldridge/dino_art/`
- **Script:** `generate_prompt.py`
- **Database:** `dino_art.db` (gitignored — regenerate with `python3 setup_db.py`)
- **Run with:** `python3 /Users/ericeldridge/dino_art/generate_prompt.py`
- **With references:** `python3 /Users/ericeldridge/dino_art/generate_prompt.py --sref [URL] --cref [URL]`

## Goal
Generate Midjourney images that look like **real wildlife photography** — benchmark is a Cuban crocodile zoo photo, plus komodo dragon hand, ostrich stride, and flamingo foot close-up reference photos. Natural light, animal just existing in habitat, muted color, telephoto bokeh, imperfect focus, film grain. No painterly/illustrated/CGI quality.

## Database Stats
- **30 species** (all with diet + habitat populated)
- **Parameters:** 31 anatomy, 20 behavior, 14 camera, 24 condition, 10 lighting, 15 mood, 1 style, 10 weather
- Behaviors have a `habitat` column — marine/aerial behaviors only show for matching species
- All anatomy blocks compressed to ~20 words each

## Current Architecture

### CLI Arguments
| Flag | Default | Purpose |
|------|---------|---------|
| `--style` | `raw` | MJ style mode |
| `--stylize` | `100` | MJ stylize |
| `--chaos` | `0` | MJ chaos |
| `--quality` | `1.0` | MJ quality |
| `--sref` | None | Style reference URL — appended directly to output prompt |
| `--cref` | None | Character reference URL — appended directly to output prompt |
| `--db` | `dino_art.db` | Database path |

### Prompt Assembly Priority Order
Five strict sections — no category bleed allowed:

1. **Subject** — species name + size, anatomy, feathering, tail posture, coloration, required params, skin texture, mouth/teeth, behavior, condition, mood, style anchor. Richest section.
2. **Interaction** — feet/ground contact mechanics only (`GROUND_INTERACTION` constant). Separate from subject so MJ reads it as spatial relationship, not anatomy.
3. **Environment** — period + habitat setting, composition framing appended here.
4. **Lighting** — one lighting condition + one weather phrase. Short.
5. **Camera** — lens spec only. Minimal.

- Deduplication pass strips exact repeated clauses before final join
- Canvas print extras appended after camera when applicable

### Hardcoded Constants (not in DB)
- **Style:** `"hyperrealistic, anatomically accurate, living animal skin texture, subsurface scattering, 8K texture"`
- **Mouth (carnivore):** `"yellowed uneven teeth, wet interior mouth, heavy saliva stranding between teeth"`
- **Mouth (herbivore):** `"wet lips parted, grinding teeth worn flat, saliva catching light along jaw"`
- **Ground interaction:** `"feet fully weight-bearing, each toe contacting ground at a different angle, visible pressure on toe pads, natural keratin wear on claw tips, packed dirt between digits, knuckle joints slightly bent under load"`
- **Negative prompt:** full anatomy errors (fused digits, blob hands, etc.), studio blockers, fossil/skeleton blockers, indoor blockers

### Modular Vary Region Workflow
Every run outputs three labeled prompts:

**STEP 1 — Main prompt**
Full image generation. Includes all MJ flags (`--style`, `--stylize`, `--no`, etc.). Paste directly into MJ `/imagine`.

**STEP 2 — Feet fix** (`--stylize 20`)
Vary Region inpainting for feet/claws. Diet and habitat aware:
- Carnivore/Piscivore → recurved talons, komodo dragon foot reference
- Herbivore → column-like toes, elephant foot reference
- Marine → flipper/paddle limb version
MJ flags stripped — paste directly into Vary Region prompt field.

**STEP 3 — Environment fix** (`--stylize 30`)
Vary Region inpainting for background/habitat. Uses same lighting + weather as main prompt for consistency. Specifies "no animal in frame, habitat only."
MJ flags stripped — paste directly into Vary Region prompt field.

### Schema Validator
`validate_prompt(prompt, allow_mj_params, label)` — called on all three outputs before display:
- Main prompt: raises if no `--` flags found
- Fix prompts: raises if any `--` flags remain after stripping

### `--sref` Behaviour
When `--sref` is passed with a foot/close-up reference photo, MJ's style reference can pull composition toward close-ups. Fix: `has_sref=True` forces `"full body visible head to tail"` into the subject block regardless of output mode.

### Output Modes (9 total)
`portrait`, `canvas`, `environmental`, `extreme_closeup`, `action_freeze`, `tracking_side`, `ground_level`, `aerial_overhead`, `dusk_long_exp`

### Environments (habitat + period aware)
Terrestrial: Triassic, Jurassic, Cretaceous, Other
Marine: Jurassic, Cretaceous, Triassic, Other
Aerial: Jurassic, Cretaceous, Triassic, Other

---

## All Changes By Session

### Session 1 — Museum Aesthetic Fix
- Replaced `photogrammetry skin detail` with `living animal skin texture` everywhere
- Rewrote all 10 species `skin_texture_type` DB values from specimen to living-animal language
- Added behavior (15), condition (4), weather (10) parameter categories
- Added fossil/skeleton/indoor blockers to negative prompt
- Removed `cinematic`, `chiaroscuro`, `epic scale` from parameter values
- Fixed `species["diet"]` KeyError (sqlite3.Row has no `.get()`)

### Session 2 — Realism Overhaul
- Deleted non-realism DB options: whimsical/eerie moods, bioluminescent lighting, oil_painting/watercolor/concept_art/ink_etching/paleontology_art styles
- Removed silhouette output mode
- Rewrote all mood values for documentary wildlife tone
- Populated diet field for all 30 species (20 were blank)
- Added behavior habitat filtering (marine/aerial column)
- Fixed Python 3.9 compatibility (removed `str | None` union syntax)
- Added deduplication engine
- Compressed all 31 anatomy blocks ~60%
- Added `--sref` and `--cref` CLI flags
- Vary Region feet-fix prompt planned

### Session 3 — Modular Prompts, Validator, Parameter Expansion

#### Bug Fixes
- **`--sref`/`--cref` were never in the argparser** — flags were documented but silently ignored. Now parsed and appended directly to prompt output.
- **Spinosaurus rendered as crocodile** — `"crocodilian body proportions"` in species notes triggered MJ's crocodile recognition. Fixed to `"elongated torso with disproportionately small hindlimbs"`.
- **Feet-fix prompt pasted into `--no` field** — user workflow error, not a code bug. Clarified: feet-fix is a separate `/imagine` for Vary Region only.

#### Prompt Assembly Refactor
- Enforced strict 5-section priority order: Subject → Interaction → Environment → Lighting → Camera
- `FEET_CLAWS` renamed `GROUND_INTERACTION` — moved from subject section to dedicated interaction section
- Ground interaction text expanded: toe angles, pad pressure, keratin wear, knuckle bend
- Mood, condition, behavior pulled up into subject section (were after camera)
- `"tail posture: ..."` label removed from prompt — just the descriptor value now
- "Earlier sections more detailed, later sections shorter and supportive" enforced structurally

#### Modular Fix Prompts Added
- `make_feet_fix_prompt()` — species/diet/habitat aware, `--stylize 20`
- `make_environment_fix_prompt()` — uses same lighting + weather as main, `--stylize 30`
- `strip_mj_params()` — truncates at first ` --` for clean Vary Region paste
- `validate_prompt()` — schema enforcement on all three outputs

#### Parameter Expansion
**Lighting** (4 → 10): added `blue_hour`, `harsh_midday`, `broken_cloud`, `backlit_haze`, `pre_storm`, `dappled_canopy`. Removed `bioluminescent`.

**Mood** (4 → 15): replaced epic/whimsical/eerie with documentary wildlife moods:
`quiet_power`, `serene`, `menacing`, `closed_mouth_natural`, `alert_scan`, `drinking`, `heat_rest`, `mid_stride`, `feeding_focus`, `territorial_hold`, `post_kill_pause`, `scent_check`, `wading_slow`, `dust_bath`, `eye_contact`

**Behavior** (15 → 20): added `freeze_detect`, `jaw_clean`, `mud_wallow`, `body_press_thermoreg`, `carcass_pause`

**Condition** (4 → 24): added 10 general realism conditions (`mud_caked`, `wet_from_water`, `parasite_load`, `missing_toe`, `moulting_skin`, `blood_on_muzzle`, `algae_on_hide`, `fly_attention`, `lean_season`, `dominant_prime`) and 10 specific injury conditions (`eye_wound`, `torn_sail`, `jaw_asymmetry`, `hide_bite_flank`, `broken_horn_tip`, `missing_claw_digit`, `patchy_hide`, `embedded_tooth`, `split_claw`, `neck_scar_collar`)

---

## Current Status
- **Environment, feathering, body, mood, color palette, bokeh:** Solved.
- **Modular workflow:** Implemented. Every run outputs Step 1/2/3 ready to paste.
- **Claws/toes:** `GROUND_INTERACTION` block is richer. Remaining lever: `--sref` with real foot photos + Vary Region Step 2.
- **Parameter depth:** 24 conditions, 15 moods, 20 behaviors — enough variety for genuinely different animals every run.

## Next Priorities
1. **Test Step 2 feet-fix workflow in practice** — generate → upscale → Vary Region → paste Step 2 prompt
2. **Test `--sref` with komodo/flamingo/ostrich foot URLs** — confirm full body framing override works
3. **Build out `species_reference/`** — real animal analogue photos per species folder
4. **Test beat-up condition combos** — `split_claw` + `lean_season` + `freeze_detect` is the target stack
5. **Consider `--stylize` tuning per species** — large sauropods may need higher stylize than small raptors

## Reference Photos Identified
- Komodo dragon hand/foot (digits separated, claws at different angles)
- Ostrich pair mid-stride (muted color, overcast, telephoto bokeh, messy feathers)
- Flamingo foot close-up (scale size transition shin→toe, worn keratin, leathery pad)
- Monitor lizard yawning (wet pink mouth, individual claws on rock, bokeh background)
