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
- **42 species** — 8 terrestrial, 14 marine, 4 aerial, 8 arthropod, 8 plant (all with diet + habitat populated)
- **308 parameters** — exactly 20 per habitat per category (behavior, camera, condition, lighting, mood, weather) + anatomy + style

## Current Architecture

### Interactive Flow
1. **Habitat** — Terrestrial / Marine / Aerial / Arthropod / Plant (first choice, gates everything below)
2. **Output mode** — habitat-filtered (e.g. `surface_break` marine-only, `soaring_thermal` aerial-only)
3. **Species** — filtered to selected habitat
4. **Lighting** → **Camera** → **Mood** → **Condition** → **Behavior** → **Weather**
   - All menus show **name only** (no descriptions), **20 options** each, **custom ordered** (ORDER BY id)
   - Weather is filtered by lighting compatibility (sky state grouping)

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

### Prompt Assembly — 5-Section Priority Order
No category bleed between sections. Earlier = richer, later = shorter/supportive.

1. **Subject** — species name + size, anatomy, feathering, tail posture, coloration, required params, skin texture, mouth/teeth (skipped on arthropods, plants, and toothless beak species), behavior (first 2 phrases), condition, style anchor. *Mood is selected but NOT injected — Session 9.*
2. **Interaction** — habitat-specific (`HABITAT_INTERACTION` dict, 2 phrases each):
   - Terrestrial: feet fully weight-bearing, natural keratin wear on claw tips
   - Marine: body partially submerged, waterline crossing torso
   - Aerial: wing membrane taut against light, body suspended in open sky
   - Arthropod: massive body weight pressing into ground, body segments clearly defined
   - Plant: rooted in soil, root buttresses visible at base
3. **Environment** — period + habitat setting (capped at 3 phrases), composition framing. *Anti-CGI environment anchor removed in Session 9.*
4. **Lighting** — first phrase of lighting param only. *Weather is NOT injected — Session 9.*
5. **Camera** — lens spec only (underwater fixed_camera no longer contains `natural light from above`)

Deduplication pass strips exact repeated clauses before final join.

### Habitat-Specific Realism (`HABITAT_REALISM`) — Session 9 lean
- **Terrestrial:** National Geographic wildlife photography, telephoto bokeh, film grain
- **Marine:** National Geographic ocean wildlife photography, underwater caustics, marine biology documentary  *(Surface-only artifacts removed: was contradicting underwater shots.)*
- **Aerial:** National Geographic bird-in-flight photography, raptor flight documentary
- **Arthropod:** National Geographic wildlife photography, photographed like a large animal not a small insect
- **Plant:** National Geographic botanical photography, botanical field photograph

### Habitat-Specific Negative Prompts (`HABITAT_NEGATIVE`)
- **Terrestrial:** (base negative only)
- **Marine:** dry land, standing on ground, desert, forest floor, no water, dry skin, dusty
- **Aerial:** standing on ground, walking, sitting, grounded, feet on dirt, terrestrial pose, folded wings
- **Arthropod:** vertebrate anatomy, fur, feathers, mammal, small insect, tiny bug, macro photography of small creature, normal sized, modern insect
- **Plant:** animal, creature, dinosaur, insect, moving, walking, eyes, mouth

### Lighting → Weather Compatibility
- Each lighting has a sky state: `clear`, `overcast`, `mixed`, `storm`
- Each weather has compatible sky states (e.g. `monsoon_heavy` → `storm`/`overcast`)
- `pick_weather()` filters weather options to only show compatible choices
- `volcanic_ash_fall` is compatible with any sky state

### Hardcoded Constants (Session 9 lean)
- **Style (per clade via `CLADE_STYLE`):**
  - Vertebrates: `"hyperrealistic, anatomically accurate, living animal skin texture, natural imperfections, photographed in the wild"`
  - Arthropod: `"... living chitinous exoskeleton ..."`
  - Plant: `"hyperrealistic, botanically accurate, living plant tissue, bark and leaf texture, natural imperfections, photographed in the wild"`
- **Mouth (carnivore):** `"yellowed uneven teeth"` — trimmed from 3 phrases to 1
- **Mouth (herbivore):** `"grinding teeth worn flat"` — trimmed from 3 phrases to 1
- **Mouth (arthropod):** `"mandibles or chelicerae visible, no vertebrate mouth"`
- **Mouth (toothless beak species):** *not injected* — guarded by description/notes scan
- **Negative prompt:** modular `build_negative_prompt(habitat)` — clade-specific anatomy + studio + fossil + indoor + CGI blocks

### Modular Vary Region Workflow — 4 Steps

Every run outputs four labeled prompts. MJ flags stripped from Steps 2–4 (paste directly into Vary Region field).

| Step | Target | Stylize | Notes |
|------|--------|---------|-------|
| **STEP 1** | Full image | 100 (default) | Includes all MJ flags. Paste into `/imagine`. |
| **STEP 2** | Feet/flippers/wings/legs | 20 | Habitat + diet aware. Terrestrial → talons/elephant feet. Marine → flipper. Aerial → wing membrane. Arthropod → jointed exoskeleton legs. |
| **STEP 3** | Background | 30 | Uses same lighting + weather as main. Specifies no animal in frame. |
| **STEP 4** | Mouth/jaw/mouthparts | 20 | Diet + habitat aware. Carnivore → tooth decay, debris, flies, saliva strand, croc jaw ref. Marine → jaw at waterline, algae, water beading. Herbivore → worn molars, plant fibre. Arthropod → species-specific (chelicerae for scorpions, circular mouth for Anomalocaris, mandibles for others). |

### Schema Validator
`validate_prompt(prompt, allow_mj_params, label)`:
- Main prompt: raises if no `--` flags found
- Fix prompts: raises if any `--` flags remain after stripping

### `--sref` Behaviour
When `--sref` is passed, forces `"full body visible head to tail"` into subject block regardless of mode — prevents close-up style reference pulling MJ toward feet/detail crops.

### Output Modes (13 total, habitat-filtered)
- **All habitats:** `portrait`, `canvas`, `environmental`, `extreme_closeup`, `action_freeze`, `tracking_side`, `ground_level`, `aerial_overhead`, `dusk_long_exp`
- **Marine only:** `surface_break`, `underwater`
- **Aerial only:** `soaring_thermal`, `dive_strike`, `perched`

### Species Roster

| Habitat | Species |
|---------|---------|
| Terrestrial | T. rex, Velociraptor, Triceratops, Stegosaurus, Ankylosaurus, Brachiosaurus, Parasaurolophus, Dilophosaurus |
| Marine — Reptiles | Mosasaurus, Elasmosaurus, Ichthyosaurus, Liopleurodon, Kronosaurus, Spinosaurus |
| Marine — Sharks | Megalodon, Cretoxyrhina (Ginsu Shark), Helicoprion |
| Marine — Fish | Dunkleosteus, Xiphactinus (Bulldog Fish), Leedsichthys |
| Marine — Other | Archelon (giant sea turtle), Ammonite (cephalopod) |
| Aerial | Pteranodon, Quetzalcoatlus, Rhamphorhynchus, Dimorphodon |
| Arthropod | Meganeura (giant dragonfly), Arthropleura (giant millipede), Jaekelopterus (giant sea scorpion), Pulmonoscorpius (giant scorpion), Megarachne (eurypterid), Anomalocaris, Eurypterus (sea scorpion), Megalograptus (clawed sea scorpion) |
| Plant | Lepidodendron (scale tree), Calamites (giant horsetail), Glossopteris (tongue fern), Williamsonia (bennettite), Araucaria (monkey puzzle), Archaefructus (first flower), Wattieza (first tree), Sigillaria (seal tree) |

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
- Deleted non-realism DB options: whimsical/eerie moods, bioluminescent lighting, non-realism styles
- Removed silhouette output mode
- Rewrote all mood values for documentary wildlife tone
- Populated diet field for all 30 species
- Added behavior habitat filtering (marine/aerial column)
- Fixed Python 3.9 compatibility
- Added deduplication engine
- Compressed all 31 anatomy blocks ~60%

### Session 3 — Modular Prompts, Validator, Parameter Expansion

#### Bug Fixes
- **`--sref`/`--cref` were never in the argparser** — flags were documented but silently ignored. Now parsed and appended directly to prompt output.
- **Spinosaurus rendered as crocodile** — `"crocodilian body proportions"` triggered MJ's crocodile recognition. Fixed to `"elongated torso with disproportionately small hindlimbs"`.

#### Prompt Assembly Refactor
- Enforced strict 5-section priority order: Subject → Interaction → Environment → Lighting → Camera
- `FEET_CLAWS` renamed `GROUND_INTERACTION`, moved to dedicated section 2, text expanded
- Mood, condition, behavior pulled up into subject (were after camera)
- `"tail posture: ..."` label removed from prompt output

#### Modular Fix Prompts
- `make_feet_fix_prompt()` — diet/habitat aware, `--stylize 20`
- `make_environment_fix_prompt()` — matches main lighting + weather, `--stylize 30`
- `make_mouth_fix_prompt()` — diet/habitat aware, `--stylize 20`, saltwater crocodile jaw reference anchor
- `strip_mj_params()` — truncates at first ` --`
- `validate_prompt()` — schema enforcement on all four outputs

#### Parameter Expansion
- **Lighting** (4 → 10): `blue_hour`, `harsh_midday`, `broken_cloud`, `backlit_haze`, `pre_storm`, `dappled_canopy`
- **Mood** (4 → 15): full documentary wildlife set — `quiet_power`, `alert_scan`, `heat_rest`, `feeding_focus`, `territorial_hold`, `post_kill_pause`, `scent_check`, `wading_slow`, `dust_bath`, `eye_contact` + originals
- **Behavior** (15 → 20): `freeze_detect`, `jaw_clean`, `mud_wallow`, `body_press_thermoreg`, `carcass_pause`
- **Condition** (4 → 24): 10 realism conditions (`mud_caked`, `wet_from_water`, `parasite_load`, `missing_toe`, `moulting_skin`, `blood_on_muzzle`, `algae_on_hide`, `fly_attention`, `lean_season`, `dominant_prime`) + 10 injury conditions (`eye_wound`, `torn_sail`, `jaw_asymmetry`, `hide_bite_flank`, `broken_horn_tip`, `missing_claw_digit`, `patchy_hide`, `embedded_tooth`, `split_claw`, `neck_scar_collar`)

### Session 4 — Habitat-First Architecture

#### Core Change
- **Habitat is now the first interactive choice** — Terrestrial / Marine / Aerial gates every subsequent menu (species, modes, lighting, camera, mood, condition, behavior, weather)

#### Schema
- Added `habitat` column to `species` table (`terrestrial` / `marine` / `aerial`)
- Added `habitats` column to `parameters` table (comma-separated, filtered with `LIKE`)

#### Species Expansion
- Added 5 marine species: Mosasaurus, Elasmosaurus, Ichthyosaurus, Liopleurodon, Kronosaurus
- Added 3 aerial species: Quetzalcoatlus, Rhamphorhynchus, Dimorphodon
- Reclassified Spinosaurus → marine, Pteranodon → aerial

#### Parameter Overhaul
- Every category (behavior, camera, condition, lighting, mood, weather) now has exactly **20 options per habitat**
- All menus display **name only** (no descriptions)
- Custom logical ordering per category (ORDER BY id, insertion order = display order)
- Habitat-specific parameters: e.g. marine behavior includes `breaching_surface`, `deep_dive_descent`; aerial condition includes `torn_membrane`, `wind_worn_crest`

#### Lighting → Weather Filtering
- `LIGHTING_SKY` dict maps each lighting option to a sky state (`clear`/`overcast`/`mixed`/`storm`)
- `WEATHER_SKY_COMPAT` dict defines compatible sky states per weather option
- `pick_weather()` filters weather menu to only show options compatible with chosen lighting
- Example: choosing "harsh midday" hides monsoon/storm weather; choosing "stormy" hides clear/pristine

#### Habitat-Specific Realism
- `HABITAT_INTERACTION` — replaces old single `GROUND_INTERACTION` with per-habitat physics (ground contact / water physics / wing flight)
- `HABITAT_REALISM` — per-habitat National Geographic photography style anchors
- `HABITAT_NEGATIVE` — per-habitat negative prompt additions (marine blocks land, aerial blocks grounded poses)

#### New Output Modes
- `surface_break` and `underwater` (marine only)
- `soaring_thermal` and `dive_strike` (aerial only)

#### Step 2 Labels
- Terrestrial → FEET FIX, Marine → FLIPPER FIX, Aerial → WING FIX

#### Migration
- `migrate_scientific.py` updated with `habitat` column for species and `habitats` column for parameters
- Habitat overrides for Pteranodon (→ aerial) and Spinosaurus (→ marine)

### Session 5 — Context-Reactive Branching + Invalid Combo Blocking

#### Core Change
Every menu now shows a `★ SUGGESTED` banner (5 picks, highlighted in the numbered list) driven by what has already been selected. Invalid combinations are blocked at selection time with a red `✗ reason` — the user is re-prompted rather than allowed to assemble a scientifically incoherent prompt.

#### Architecture
- **`get_suggestions(category, context) → list[str]`** — habitat-agnostic dispatcher; routes to `get_marine_suggestions`, `get_terrestrial_suggestions`, `get_aerial_suggestions`
- **`get_blocked(category, context) → dict[str, str]`** — habitat-agnostic dispatcher; routes to per-habitat blocked functions
- **`ctx` dict** in `main()` tracks all selections in order: species → lighting → mood → condition → behavior → weather
- **`_cpick(category, slabel)`** helper in `main()` — injects suggestions + blocked into every `pick_parameter` call; works identically for all three habitats
- **`pick()`** upgraded: shows `★ SUGGESTED` box at top, highlights suggested rows with `★`, shows blocked rows greyed with `✗ reason`, refuses selection of blocked items

#### Suggestion Logic (per habitat)

**Marine:**
- Lighting: species-specific (e.g. Mosasaurus → `surface_dapple`, `murk_glow`; Liopleurodon → `deep_water_fade`, `bioluminescent`); mode overrides for `underwater` and `surface_break`
- Mood: driven by lighting choice; Carnivore diet boosts hunting/menacing moods to front
- Behavior: driven by mood (e.g. `ambush_still` → `hovering_still`, `resting_on_seafloor`; `surfacing_breath` → `spy_hopping`, `breaching_surface`)
- Condition: species-specific baseline; shifts on active hunting/menacing → `blood_on_muzzle`, `battle_scarred`; post-feed → `blood_on_muzzle`, `belly_scars`
- Camera: mode-based; behavior overrides (breaching → `breach_freeze`, `split_waterline`; jaw strike → `jaw_level`, `murk_emerge`; seafloor → `below_looking_up`, `deep_telephoto`)
- Weather: mood-based (storm moods → `ocean_storm`, `tidal_surge`; serene → `calm_surface`, `dawn_glass`; deep patrol → `thermocline_shift`, `deep_current_cold`)

**Terrestrial:**
- Lighting: species-specific (T. rex → `dramatic_rim`, `harsh_midday`; Velociraptor → `dappled_canopy`, `shaft_light`; herbivores → `golden_hour`, `overcast`); mode overrides for `ground_level`, `action_freeze`, `dusk_long_exp`
- Mood: lighting-driven; Carnivore diet boosts `menacing`, `post_kill_pause`, `territorial_hold` to front
- Behavior: mood-driven (e.g. `heat_rest` → `basking_flat`, `resting_alert`; `post_kill_pause` → `carcass_standing`; `dust_bath` → `dust_rolling`)
- Condition: species baseline; post-kill/feeding → `blood_on_muzzle`, `fly_attention`; menacing/charge → `battle_scarred`, `embedded_tooth`; heat rest/basking → `parasite_ticks`, `moulting_skin`
- Camera: mode-based; behavior overrides (charging/stride → `dynamic_low`, `tracking_pan`; drinking → `waterhole_edge`, `hidden_blind`; threat display → `walking_toward`, `ground_level_up`)
- Weather: mood-based (menacing → `storm_approaching`, `volcanic_ash_fall`; heat rest → `heat_haze`, `hot_still_air`; scent tracking → `ground_mist`, `cold_fog`)

**Aerial:**
- Lighting: species-specific (Quetzalcoatlus → `dramatic_rim`, `storm_flash`; Pteranodon → `golden_hour`, `halo_backlit`); mode overrides for `soaring_thermal` → `thermal_shimmer`, `halo_backlit`; `dive_strike` → `storm_flash`, `dramatic_rim`
- Mood: lighting-driven; Carnivore diet boosts `menacing`, `hunting_scan`, `territorial_display` to front
- Behavior: mood-driven (e.g. `thermal_drift` → `thermal_soaring`, `glide_coast`; `wind_buffet` → `wind_correction`, `headwind_struggle`; `hunting_scan` → `diving_strike`, `fish_snatch`)
- Condition: species baseline; hunting/diving → `fish_oil_stain`, `torn_membrane`; exhausted/headwind → `wing_joint_swollen`, `lean_season`; perched → `wind_worn_crest`, `talon_worn`
- Camera: mode-based; behavior overrides (perched → `cliff_perch`, `wing_detail`; diving → `stoop_above`, `head_on_approach`; soaring → `below_up_wings`, `thermal_circle`)
- Weather: mood-based (thermal drift → `thermal_column`, `high_altitude_clear`; menacing → `storm_anvil_top`, `updraft_turbulence`; dusk roost → `sunset_altitude`, `calm_dead_air`)

#### Invalid Combo Blocking

**Marine (15 cross-category + mode blocks):**
- Surface behaviors (`breaching_surface`, `spy_hopping`) ↔ deep moods (`resting_on_bottom`, `deep_patrol`) and deep lighting (`deep_water_fade`, `bioluminescent`)
- Seafloor behaviors (`resting_on_seafloor`, `deep_sinking`) ↔ surface lighting (`surface_dapple`) and surface moods (`surfacing_breath`)
- Still behaviors (`hovering_still`) ↔ `burst_acceleration` mood
- `jaw_snap_strike` ↔ `post_feed_drift` (just ate but now striking)
- Mode blocks: `underwater` mode blocks all surface behaviors/moods; `surface_break` blocks all seafloor behaviors/moods

**Terrestrial (28 cross-category + mode blocks):**
- Combat/charge behaviors (`charging_full`, `head_butt_spar`, `tail_swipe`) ↔ passive moods (`heat_rest`, `serene`, `dusk_settling`)
- `basking_flat` ↔ `moonlit`/`twilight_fade`/`forest_floor_shade` lighting (ectotherm solar thermoregulation — needs direct sun) and ↔ `monsoon_heavy`/`storm_approaching` weather
- `basking_flat` ↔ `menacing`/`mid_stride`/`territorial_hold` moods
- `carcass_standing` ↔ `heat_rest`/`serene`/`herd_grazing`/`grooming` (contextually incoherent)
- `dust_rolling` ↔ `menacing`/`scent_tracking` and wet weather conditions
- `drinking_at_water` ↔ `dust_storm` weather
- Mode block: `action_freeze` blocks passive/static behaviors (basking, resting, jaw cleaning)

**Aerial (19 cross-category + mode blocks):**
- Perched behaviors (`cliff_perching`, `preening_perched`, `morning_stretch`) ↔ in-flight moods (`thermal_drift`, `effortless_cruise`, `wind_buffet`, `hunting_scan`)
- In-flight behaviors (`thermal_soaring`, `diving_strike`, `level_cruise`) ↔ `perched_alert` mood
- `headwind_struggle` ↔ `thermal_drift`/`effortless_cruise`/`serene` (flight physics — can't struggle and drift effortlessly)
- `diving_strike` ↔ `thermal_drift` (contradictory flight mechanics)
- `landing_approach` ↔ `thermal_drift`/`hunting_scan`
- Mode blocks: `soaring_thermal` blocks all perched/ground behaviors; `dive_strike` blocks soaring, hovering, perching, landing, and drifting moods

#### Implementation Notes
- `pick()` upgraded to accept `suggestions` (list), `blocked` (dict), `suggest_label` (str) — backward-compatible, all non-marine/terrestrial/aerial paths pass empty values
- `pick_parameter()` and `pick_weather()` both accept and pass through the same params
- `setdefault` used for blocked dict accumulation — first-matched reason wins (mood rule beats lighting rule when both fire)
- `_cpick()` closure in `main()` captures `ctx` by reference — context updates are reflected in subsequent picks without re-passing

### Session 6 — Anti-CGI Overhaul, Marine Expansion, --sref Integration, Perched Mode

#### Anti-CGI Background Fix
- Removed CG rendering terms from `HYPERREALISM_STYLE`: "subsurface scattering, 8K texture" → "natural imperfections, photographed in the wild"
- Rewrote all 14 `ENVIRONMENTS` entries with photo-grounded language (no fantasy adjectives, real-location feel)
- Added anti-CGI anchor to every environment section: "real outdoor location, imperfect natural detail, uneven terrain"
- Added 11 CGI blockers to `NEGATIVE_PROMPT`: "digital matte painting, rendered background, CGI environment, concept art, 3D render, Unreal Engine, volumetric god rays, hyper-saturated, fantasy landscape, perfect symmetry, smooth gradient sky"
- Updated environment fix prompt (Step 3) with matching anti-CGI negatives

#### --sref Suggestion Integration
- Created `sref_urls.json` — per-species URL registry supporting `{label, url}` objects or bare URL strings
- After species select, if `--sref` not on CLI, shows available reference URLs and lets user pick or skip
- Selected URL auto-appends to prompt output
- All 26 species have entries (empty by default — user populates as they upload reference photos to Discord)

#### Aerial Perched Mode
- Added `perched` output mode (aerial-only) — "Perched on cliff / roost"
- Camera: Canon EOS R5 600mm f/4, telephoto, cliff-level angle
- Composition: "perched on rocky outcrop or cliff edge, wings folded at sides, talons gripping rock"
- Perched interaction block: "talons gripping rocky edge, each digit wrapped around stone, wings folded tight against body"
- Blocks 8 in-flight behaviors + 4 in-flight moods; leaves perched/preening/stretch behaviors unblocked
- Removes "folded wings" from aerial negative prompt in perched mode
- Added to lighting, camera suggestion dicts

#### Marine Species Expansion (6 → 14)
- **Sharks:** Megalodon (Miocene), Cretoxyrhina/Ginsu Shark (Cretaceous), Helicoprion (Permian)
- **Fish:** Dunkleosteus (Devonian), Xiphactinus/Bulldog Fish (Cretaceous), Leedsichthys (Jurassic)
- **Other:** Archelon/giant sea turtle (Cretaceous), Ammonite/cephalopod (Jurassic)
- Expanded schema `period` CHECK constraint: added Devonian, Carboniferous, Permian, Miocene
- Expanded schema `diet` CHECK constraint: added Filter-feeder
- Added `ENVIRONMENTS` entries for new periods: `marine_Devonian`, `marine_Permian`, `marine_Miocene`
- Added all 8 species to `MARINE_LIGHTING_BY_SPECIES` and `MARINE_CONDITION_BY_SPECIES`
- Species-specific mouth fix prompts: shark jaw (great white reference), Helicoprion spiral whorl, Dunkleosteus bony blades, Archelon/Ammonite beaks

#### Marine Waterline Refraction Fix
- Updated `HABITAT_INTERACTION` marine block: above-waterline body "sharp and dry" vs below-waterline "colour-shifted blue-green and slightly distorted by refraction"
- Mode-specific interaction overrides: `underwater` gets "fully submerged" physics, `surface_break` gets "body erupting through surface" physics
- Marine mouth fix (Step 4) now describes jaw split by waterline with explicit refraction difference

#### Mosasaurus Variety Fix
- Rewrote description: removed pose-locking "massive elongated jaw, powerful tail fluke" → body-shape descriptors that don't dictate angle
- Rewrote notes: removed "crocodilian" (triggered MJ's crocodile recognition) → "keeled scales, rounded snout, conical teeth varying in size, loose jaw hinge"

#### Species Reference Folders
- Created 8 new folders for Session 4 marine/aerial species (mosasaurus through dimorphodon)
- Created 8 new folders for Session 6 marine species (megalodon through ammonite)
- Each folder has README with real animal analogues for `--sref` photography guidance
- Total: 26 species reference folders

### Session 7 — Arthropod & Plant Habitats, Diet-Grouped Menus

#### New Habitats
- Added **Arthropod** habitat: 8 prehistoric insects/invertebrates (Meganeura, Arthropleura, Jaekelopterus, Pulmonoscorpius, Megarachne, Anomalocaris, Eurypterus, Megalograptus)
- Added **Plant** habitat: 8 prehistoric plants (Lepidodendron, Calamites, Glossopteris, Williamsonia, Araucaria, Archaefructus, Wattieza, Sigillaria)
- Both habitats have full ENVIRONMENTS, HABITAT_INTERACTION, HABITAT_REALISM, and HABITAT_NEGATIVE entries
- All terrestrial-compatible parameters extended to include arthropod and plant habitats
- Arthropod feet fix: jointed exoskeleton legs, chitinous segments, tarsal claws
- Plants skip mood/behavior/condition selection (no animal behavior), skip Step 2 (feet fix) and Step 4 (mouth fix)

#### Arthropod Scale Fix (tested → looked like normal-sized modern bugs)
- **Root cause 1: "macro insect photography"** in realism anchor told MJ to shoot them like tiny bugs under a macro lens. Changed to **"wildlife photography, photographed like a large animal not a small insect"**
- **Root cause 2: No environmental scale cues** in descriptions. "Giant scorpion up to 70cm" means nothing to MJ. Rewrote all 8 arthropod descriptions with size comparisons: *"as large as an eagle"*, *"longer than a car"*, *"as long as a crocodile"*, *"pincers the size of human fists"*, *"standing among ferns that barely reach its back"*
- **Root cause 3: Vertebrate mouth language** injected into arthropods ("yellowed teeth, saliva stranding"). Replaced with `"mandibles or chelicerae visible, no vertebrate mouth"` in subject block
- Added species-specific arthropod mouth fix prompts (Step 4): chelicerae for scorpions/eurypterids, circular tooth-plate mouth for Anomalocaris, mandibles for insects
- Step 4 label changes to "MOUTHPART FIX" / "mandibles/chelicerae" for arthropods
- Interaction block rewritten with weight/mass language: "massive body weight pressing into ground, legs thick as branches, towering over surrounding ferns"
- Negative prompt expanded: added "small insect, tiny bug, macro photography of small creature, normal sized, modern insect, house bug"
- Notes rewritten from "Use macro photography" to "Photograph like a bird of prey / large reptile / alligator-sized predator"

#### Diet-Grouped Species Menus
- Terrestrial species menu now grouped by **Carnivore** / **Herbivore** with section headers
- Marine species menu grouped by **Predators** / **Fish-Eaters** / **Filter Feeders** / **Omnivores**
- New `_pick_grouped()` function for continuous-numbered menus with diet group headers
- `_species_label()` provides habitat-specific menu titles

#### Schema Updates
- Expanded `habitat` CHECK constraint: added `arthropod`, `plant`
- All 16 new species inserted with full scientific data (period, diet, size_class, body_length, description, notes, fossil sites)
- `sref_urls.json` expanded to 42 species entries

### Session 8 — Clade-Aware Style, Modular Negatives, Output Mode Expansion

#### Clade-Bleed Audit (root cause of plant prompts containing animal-skin language)
- `HYPERREALISM_STYLE` was a single global injecting `"living animal skin texture"` into every clade — visible in fern test where the prompt described a plant with animal-skin language
- `NEGATIVE_PROMPT` was a single global containing ~15 vertebrate-only anatomy errors (`fused digits, talons, footpads, osteoderms`) injected into plant + arthropod prompts as wasted tokens that diluted MJ's attention
- `make_feet_fix_prompt` and `make_mouth_fix_prompt` both inherited the global negative — arthropod legs-fix was getting `"missing claws, indistinct talons"` injected
- `osteoderms` was filed under "fossil blockers" but it's actually vertebrate skin anatomy — should never reach arthropod or plant prompts at all

#### Clade-Aware Style — `CLADE_STYLE` dict
- Replaced `HYPERREALISM_STYLE` with per-clade dict:
  - **Vertebrates** (terrestrial / marine / aerial): `"living animal skin texture"`
  - **Arthropod**: `"living chitinous exoskeleton"`
  - **Plant**: `"botanically accurate, living plant tissue, bark and leaf texture"`
- `main()` now picks `CLADE_STYLE.get(habitat)` instead of the single global
- `HYPERREALISM_STYLE` kept as a back-compat shim pointing at terrestrial

#### Modular Negative Prompt Builder
- Split monolithic `NEGATIVE_PROMPT` into 8 named blocks:
  - `NEG_VERTEBRATE_ANATOMY` (digits, claws, talons, footpads, osteoderms)
  - `NEG_ARTHROPOD_ANATOMY` (segmented chitin, anti-mammalian-limbs / fingers / toes / talons / footpads)
  - `NEG_STUDIO` (universal — backdrops, museum, specimen)
  - `NEG_FOSSIL_VERTEBRATE` (fossil + skeleton + bones — for vertebrate clades)
  - `NEG_FOSSIL_ARTHROPOD` (fossil + amber inclusion, no skeleton/bones)
  - `NEG_FOSSIL_PLANT` (fossil + petrified + herbarium specimen, no skeleton)
  - `NEG_INDOOR` (universal — building, warehouse, concrete)
  - `NEG_CGI` (universal — render, matte painting, fantasy, smooth gradient sky)
- New `build_negative_prompt(habitat)` assembles only the clade-relevant blocks plus `HABITAT_NEGATIVE` extras
- All 3 fix prompts (`make_feet_fix_prompt`, `make_mouth_fix_prompt`, perched-mode override in `assemble_prompt`) wired to the builder
- Perched mode preserves "folded wings" by inlining base blocks without `HABITAT_NEGATIVE` extras

| Clade        | --no tokens before | after |
|--------------|--------------------|-------|
| Terrestrial  | 69                 | 69    |
| Marine       | 76                 | 76    |
| Aerial       | 76                 | 76    |
| Arthropod    | 86                 | 77    |
| **Plant**    | **76**             | **54** |

#### Output Mode Expansion (15 → 20)
- Added 5 new modes specifically chosen to give arthropod and plant a meaningful menu (was 4 each):
  - **`shoreline`** — water-edge transition (terrestrial / marine / plant)
  - **`camera_trap`** — trail-cam aesthetic, candid framing (terrestrial / arthropod / plant)
  - **`canopy_upward`** — looking straight up through canopy (terrestrial / plant / arthropod / aerial)
  - **`misty_dawn`** — dawn fog, atmospheric depth (all 5 clades)
  - **`group_cluster`** — multiple subjects / grove (all 5 clades)
- Per-clade availability after expansion:
  - Terrestrial: 10 → 15
  - Marine: 10 → 13
  - Aerial: 9 → 12
  - **Arthropod: 4 → 8**
  - **Plant: 4 → 9**
- `select_mode()` no longer renders the `desc` column — display name only

#### Validated With Generated Images
- **Calamites** (plant) — botanical photography output, misty dawn, no animal-skin bleed in prompt
- **Megarachne** (arthropod) — proper scale (forest floor dwarfs leaf litter), chitin texture, no vertebrate anatomy bleed
- **Ammonite** (marine) — iridescent nacre rendering correctly with marine pipeline

### Session 9 — Hard Audit: Less-Is-More Prompt Trim

#### Trigger
User showed an Elasmosaurus underwater shot side-by-side with a hand-edited lean version. The original packed ~80 clauses; the lean version was ~28. Diagnosis: the prompt was over-described, contradictory, and wasting MJ attention on filler. User's principle: *"focus on the fundamentals of detail in the animal, and the surrounding environment way more than over complex lighting or behavior instructions."*

#### Contradictions found
- **Marine HABITAT_REALISM contained `water droplets on lens, wet skin detail`** — surface-only artifacts being injected into fully-submerged shots. Logically impossible underwater.
- **Underwater fixed_camera contained `natural light from above`** — lighting language bleeding into the camera section, then duplicating with environment "light filtering from surface above".
- **Underwater composition contained `light filtering from surface above`** — same phrase already in environment dict, creating triple-injection until dedupe ran.
- **Quetzalcoatlus + other beaked species** were getting `MOUTH_TEETH_CARNIVORE` ("yellowed uneven teeth") injected even though notes said "toothless pointed beak".
- **Mood + behavior overlapped massively** — typical pair: behavior `"slow deliberate swimming, body undulating gently"` + mood `"moving through dark water at depth, body streamlined, slow deliberate patrolling"` saying the same thing twice.

#### Bloat sources cut
| Source | Before | After |
|--------|--------|-------|
| `HABITAT_REALISM` (per habitat) | 5–7 phrases | 2–3 phrases |
| `HABITAT_INTERACTION` (per habitat) | 4–6 phrases | 2 phrases |
| `underwater` interaction override | 5 phrases | 2 phrases |
| `surface_break` interaction override | 5 phrases | 2 phrases |
| `perched` interaction override | 6 phrases | 3 phrases |
| `MOUTH_TEETH_CARNIVORE` | 3 phrases | 1 phrase (`yellowed uneven teeth`) |
| `MOUTH_TEETH_HERBIVORE` | 3 phrases | 1 phrase (`grinding teeth worn flat`) |
| Anti-CGI environment anchor | 3 phrases per prompt | removed (covered by --no) |
| Lighting param injection | full value (often 4 phrases) | first phrase only |
| Weather param injection | full value (often 4 phrases) | not injected (kept in tags / branching) |
| Mood param injection | full value (3+ phrases) | not injected (kept in tags / branching) |
| Behavior param injection | full value (3 phrases) | first 2 phrases |
| Environment dict injection | full value (3–4 phrases) | first 3 phrases |

#### Mood / weather are still selected
Both still appear in the menu, drive `ctx` for context-reactive suggestions and invalid-combo blocking, and are saved to the `prompts` table for tags. They are simply no longer injected into the MJ prose. The user can re-enable injection later if MJ behavior changes.

#### Toothless beak guard
`assemble_prompt` now scans `description + notes` for "toothless" or "beak" (without "tooth") and skips the mouth-teeth injection entirely. Fixes Quetzalcoatlus, Pteranodon, Archelon, Ammonite from getting carnivore-tooth language layered over toothless anatomy.

#### Token-count smoke test (after trim)

| Habitat / mode | Clauses |
|----------------|---------|
| Marine / underwater (Elasmosaurus) | 32 (was ~80) |
| Terrestrial / portrait (T. rex) | 26 |
| Plant / portrait (Calamites) | 27 |
| Arthropod / portrait (Megarachne) | 33 |
| Aerial / soaring (Quetzalcoatlus) | 34 — **no false teeth** |

~60% prose reduction across the board, no contradictions across all 5 clades.

### Session 10 — Hard Audit Round 2 (canvas mode + realism spam + mode conflicts)

#### Trigger
User scored Session 9 output: **Visual potential 9/10, System purity 5/10, Lean test integrity 3/10.** The Elasmosaurus *canvas* shot (not the underwater shot Session 9 had tested) still showed:
1. **Mode conflict** — `"fully aquatic"` + `"body partially submerged"` + `"waterline crossing torso"` all in one prompt. Three different states.
2. **Redundant realism spam** — `hyperrealistic, anatomically accurate, living animal skin texture, natural imperfections, photographed in the wild, National Geographic ocean wildlife photography, marine biology documentary` — six overlapping "trust me this is real" phrases.
3. **Narrative clutter** — `"jaw working on prey, fragments drifting, healed bite scars on ribcage, claw marks on neck, torn eyelid, powerful survivor"` — reads as event/character backstory, hostile to a calm portrait.
4. **CANVAS_PRINT bleed** — `"high dynamic range, shadow detail retained, highlight detail retained, print-ready detail, no blown highlights"` doing nothing for MJ.
5. **Camera over-specification** — `"Canon EOS R5 24-70mm f/4, mid-range, habitat in frame"` with HDR claims attached.

Diagnosis: Session 9 trimmed the underwater path I tested but never touched the canvas path, the realism stack, the multi-phrase condition values, or the contradiction between marine `HABITAT_INTERACTION` (waterline) and species-level `"fully aquatic"` text.

#### Fixes

**Marine interaction default flipped to underwater.** Was `"body partially submerged, waterline crossing torso"` — but most marine species in the DB are fully aquatic plesiosaurs/sharks/ichthyosaurs that should never be at the surface unless the mode explicitly says so. Now defaults to `"fully submerged"`. Surface-state modes (`shoreline`, `surface_break`) override with their own waterline language.

**Realism stack collapsed.**
- `CLADE_STYLE`: 5 phrases → 2 (`"anatomically accurate, living animal skin texture"`)
- `HABITAT_REALISM`: 2–3 phrases → 1 (`"ocean wildlife photography, underwater caustics"`)
- Net per-prompt: ~7 realism phrases → 3.

**Behavior + condition further trimmed.**
- Behavior: first 2 phrases → first 1 phrase
- Condition: full → first 2 phrases (was a chain of 4–6 injuries)

**`CANVAS_PRINT` block removed entirely.** Was 5 phrases doing nothing — print readiness happens at upscale time, not in the prompt. The flag stays on `OUTPUT_MODES` for tag/saved-record purposes only.

**Canvas `fixed_camera` trimmed.** `"Canon EOS R5 24-70mm f/4, mid-range, habitat in frame"` → `"Canon EOS R5 24-70mm f/4"`.

**Horizon strip is now mode-aware.** `"horizon visible"` is dropped from marine modes EXCEPT `shoreline` and `surface_break` (where the species is at the surface and a horizon is appropriate).

#### Token-count smoke test (post Session 10)

| Habitat / mode | Session 9 | Session 10 |
|----------------|-----------|------------|
| Marine / canvas (Elasmosaurus) | ~38 | **25** |
| Marine / underwater (Elasmosaurus) | 32 | **24** |
| Marine / shoreline (Elasmosaurus) | — | 29 (correctly keeps surface language) |
| Terrestrial / canvas (T. rex) | ~32 | **20** |
| Plant / canvas (Calamites) | ~30 | **22** |
| Arthropod / portrait (Megarachne) | 33 | **26** |
| Aerial / soaring (Quetzalcoatlus) | 34 | **26** |
| Aerial / perched (Quetzalcoatlus) | — | 27 |

All 8 cases pass the contradiction sweep (no aquatic+submerged on default modes, no horizon underwater, no CANVAS_PRINT bleed, no lighting in camera, no realism spam).

### Session 11 — Realism Stack Eradication + Wide-Scale Placement Variant

#### Trigger
User scored Session 10 output and flagged that the realism stack was *still* causing staged museum-like compositions. Verbatim instruction: *"The following phrases must be removed entirely from the output: anatomically accurate, living animal skin texture, wildlife photography (all variants). These are not improving realism and are biasing the model toward specimen-style composition. Also remove: all camera brands and lens specs, animal centred / symmetrical framing language. Do not replace them with alternatives. Do not change architecture. Only remove these from the active output path."*

#### Root cause discovered
Session 10 trimmed `CLADE_STYLE` and `HABITAT_REALISM` constants but the realism prose was *still* leaking into prompts. Diagnosis: `style_param["value"]` is pulled from the **`parameters` table** (category='style'), not from `CLADE_STYLE`. The DB rows contain the full realism stack baked in (`"hyperrealistic, anatomically accurate, living animal skin texture, subsurface scattering, 8K texture, shot on Canon EOS R5, National Geographic wildlife photography, ..."`). Sessions 9 and 10 had been editing constants that were never reaching the prose.

#### Removals (assemble_prompt prose path only)
- **`style_param["value"]` no longer appended to subject block.** Param is still passed through the function signature for save_prompt / tag wiring; nothing flows into prose.
- **`HABITAT_REALISM` values cleared to empty strings.** Filter in the join drops them. Dict structure preserved.
- **`CLADE_STYLE` values cleared to empty strings.** Same — preserved for parameter-id wiring.
- **Camera section (`camera = ""`).** Camera brands and lens specs no longer flow into prose. `mode_cfg["fixed_camera"]` and `camera_param` are still consulted upstream for tag/save-record purposes.
- **`"animal centred, symmetrical"` stripped from PLACEMENT dead-center sentinel.** Branch now contributes only `horizon_phrase` (when applicable).

#### Wide-scale placement variant (new)
Added a new placement option to `select_canvas_placement()`: **`("wide", "all")`** with label *"Wide scale — environment dominant, distant subject"*. Detected via `wide_mode = bool(placement) and placement[0] == "wide"` near the top of `assemble_prompt` so it works **regardless of the mode's composition template** (canvas, underwater, environmental, etc — not just modes with `composition: "PLACEMENT"`).

When `wide_mode` is active:
- `"full body visible head to tail"` is suppressed in subject block
- Environment composition is **overridden** with the wide-scale phrase block: *"subject small in frame, environment dominant, large negative space, distant subject, scale emphasized over detail"*
- No camera language is added
- All other placement options (rule of thirds, dead center, foreground dominant, etc) are unchanged

#### Token-count smoke test (post Session 11)

| Habitat / mode | S10 | S11 |
|----------------|-----|-----|
| Marine / underwater (Elasmosaurus) | 24 | **18** |
| Marine / underwater + wide (Elasmosaurus) | — | **22** |

Banned-phrase audit on Elasmosaurus / underwater: `anatomically accurate`, `living animal skin texture`, `subsurface scattering`, `8K texture`, `wildlife photography` (all variants), `National Geographic`, `Canon EOS`, `shot on`, `animal centred`, `symmetrical` — all absent. Regression test confirms canvas / rule-of-thirds-left is unaffected (still injects `full body visible head to tail` and `rule of thirds`, does not inject the wide-scale phrases).

---

## Current Status
- **42 species** across 5 habitats — 8 terrestrial, 14 marine, 4 aerial, 8 arthropod, 8 plant
- **Lean prompt mode (Sessions 9 + 10 + 11):** Marine underwater now ~18 clauses (was ~80). Realism stack **eradicated** from prose path: no `style_param` injection, no `HABITAT_REALISM` injection, no camera brands/lens specs, no `wildlife photography`, no `anatomically accurate`, no `living animal skin texture`, no `animal centred / symmetrical`. Behavior cut to 1 phrase, condition to 2. CANVAS_PRINT block removed. Marine interaction defaults to *underwater*, not waterline. Mood + weather still selected for context-reactive branching but never injected into prose. Style + camera params still passed through `assemble_prompt` for save_prompt / tag wiring.
- **Wide-scale placement variant:** `("wide", "all")` added to `select_canvas_placement` — works for any mode (not just `canvas`) via top-level `wide_mode` flag. Suppresses `"full body visible head to tail"`, overrides environment composition with the five-phrase wide-scale block. No camera language added. Other placement options unaffected.
- **Clade-aware everything:** style anchor, negative prompt, mouth/teeth, interaction block, realism block — all picked from per-clade dicts.
- **Toothless beak guard:** Quetzalcoatlus / Pteranodon / Archelon / Ammonite no longer get tooth language injected over their toothless anatomy.
- **Mode-aware horizon strip:** marine canvas/portrait/underwater never inject "horizon visible"; marine shoreline/surface_break do.
- **--sref suggestion system:** Live — prompts user after species select when URLs are available in `sref_urls.json`.
- **Perched mode:** Active for aerial species — unblocks perched behaviors, blocks flight behaviors.
- **Context-reactive branching:** Fully implemented for terrestrial, marine, aerial — **arthropod and plant use generic fallback** (no suggestions or blocking yet).
- **Invalid combo blocking:** Active for terrestrial, marine, aerial — not yet implemented for arthropod/plant.
- **Modular 4-step workflow:** All 4 steps output per run; arthropods get species-specific mouthpart fixes; plants skip Steps 2 and 4.
- **Diet-grouped menus:** Terrestrial (Carnivore/Herbivore) and Marine (Predators/Fish-Eaters/Filter Feeders/Omnivores) species menus have section headers.
- **Validated MJ outputs (Sessions 7–8):** Calamites (plant), Megarachne (arthropod), Ammonite (marine), Elasmosaurus (marine underwater).

## Known Issues
- **Sessions 10 + 11 lean output not yet validated visually in MJ** — smoke-tested in Python and passes contradiction + banned-phrase sweeps; needs visual confirmation that ~18-clause prompts still produce wildlife-photo quality (and that the realism stack removal didn't go *too* far in the other direction).
- **`condition` param values can leak surface language underwater** — observed: Elasmosaurus underwater output included `"head raised vertically above surface"` because the first phrase of the condition param contained surface language. Session 11 caps to first 2 phrases at injection but doesn't filter for mode-incompatible content. Possible fix: tag condition params with `mode_compat` and skip if incompatible, or sanitize the DB rows.
- **`condition` param values often pile multiple states** in the underlying DB — Session 11 truncates at injection but a DB cleanup pass would let context-reactive branching pick from cleaner single-state entries.
- **`behavior` param values similar pattern** — Session 11 caps to first 1 phrase. DB cleanup opportunity, not blocking.
- **Arthropod/plant have no context-reactive suggestions** — `get_suggestions()` and `get_blocked()` fall through to empty defaults for these habitats.
- **Some lighting param values lead with time-of-day language** (`dawn_first_light` → `"first light before sunrise"`) — fine but reads as a time phrase not a lighting effect. DB cleanup opportunity, not blocking.
- **Plant species notes column sometimes contains directive sentences** ("Use modern horsetail as reference but scaled up massively.") that read awkwardly when injected into prose. Pre-existing.
- **Git LFS not installed** — pushes require `--no-verify` to bypass LFS pre-push hook; `.gitattributes` tracks site assets via LFS.
- **`style_param` and `camera_param` are now dead inputs to the prose path** — they still pass through the `assemble_prompt` signature and are saved as tags, but their `value` columns are no longer read for prose. If we want the prose to ever pull from them again, the assembly path needs to be re-wired (not just the constants).

## Next Priorities
1. **Visually validate Session 11 lean prompts in MJ** — re-run Elasmosaurus underwater (with and without `wide`), T. rex canvas, Calamites canvas + wide, Megarachne portrait, Quetzalcoatlus soaring/perched and confirm the trimmed-and-stripped prompts still produce wildlife-photo quality. **Critical: did the realism stack removal go too far?** If outputs now look painterly/illustrated, we may need to re-introduce one or two specific cues — but as deliberate single phrases, not as a stack.
2. **A/B test the wide variant** — pull the same species + mode, generate one with default placement and one with `wide`, compare scale-of-subject readability.
3. **Mode-aware condition filtering** — strip condition phrases that contradict mode (e.g. `"head raised above surface"` should not survive `output_mode == "underwater"`). Either tag DB rows with `mode_compat` or run a post-injection regex pass.
4. **Add arthropod/plant-specific suggestions and blocking** — context-reactive branching for the new habitats.
5. **Per-species "winning combo" cache** — save lighting + behavior + condition + mode sets that produced confirmed-good outputs to a `winning_combos` table; surface as `★ KNOWN GOOD` in menus.
6. **Vision-feedback fix loop** — pass MJ output through Claude vision to score scientific accuracy and auto-suggest which Vary-Region step to apply.
7. **Add terrestrial species** — Pachycephalosaurus, Carnotaurus, Therizinosaurus, Allosaurus.
8. **Printify automation** — user needs to regenerate API key, then build folder-watcher → upscale → upload → draft pipeline.
9. **Populate `sref_urls.json`** — upload real animal analogue photos to Discord, collect URLs per species.
10. **Install Git LFS** — `brew install git-lfs && git lfs install` to stop needing `--no-verify` on every push.

## Reference Photos to Use as `--sref`
- Komodo dragon foot (digits separated, claws at different angles, leathery pads)
- Ostrich mid-stride (muted color, overcast, telephoto bokeh, messy feathers)
- Flamingo foot close-up (scale transition shin→toe, worn keratin)
- Monitor lizard yawning (wet pink mouth, individual claws, bokeh background)
- **Saltwater crocodile jaw** (tooth decay/staining, twig between teeth, algae on jaw, flies, water glistening)
- **Great white shark jaw** (triangular teeth rows, replacement teeth, pink gums) — for Megalodon/Cretoxyrhina
- **Nautilus shell** (spiral pattern, iridescent nacre, ribbed surface) — for Ammonite
- **Leatherback turtle** (leathery shell, barnacles, massive flippers) — for Archelon
- **Whale shark** (filter-feeding posture, mottled skin, wide mouth) — for Leedsichthys
- **Emperor scorpion** (glossy exoskeleton, pedipalps, segmented tail) — for Pulmonoscorpius
- **Horseshoe crab** (broad flat body, compound eyes, paddle legs) — for Jaekelopterus/Eurypterus
- **Giant millipede** (segmented plates, paired legs, rounded body) — for Arthropleura
- **Dragonfly in flight** (veined wings, compound eyes, elongated abdomen) — for Meganeura
