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
- **Species anatomy module system (Session 15):** `species/` Python package with per-species anatomy modules containing skull, dentition, limb structure, integument, body proportions, coloration evidence, locomotion, flora associations, and key inaccuracy notes for all 42 species. Integrated into `assemble_prompt()` — replaces old basic science-table fields with rich anatomy data scaled to output mode (close/mid/wide). Banned-flora negatives auto-injected into `--no` to prevent anachronistic vegetation.
- **Lean prompt mode (Sessions 9–11):** Realism stack eradicated from prose path: no `style_param` injection, no `HABITAT_REALISM` injection, no camera brands/lens specs, no `wildlife photography`, no `anatomically accurate`, no `living animal skin texture`. Behavior cut to 1 phrase, condition to 2. CANVAS_PRINT block removed. Marine interaction defaults to *underwater*. Mood + weather still selected for context-reactive branching but never injected into prose.
- **25 output modes (Session 14):** redesigned from 20 to 25, including 6 epic wide landscape options (environmental, valley_panorama, ridgeline_silhouette, river_crossing, misty_dawn, storm_front) with auto-triggered wide_mode.
- **Auto-selected scene settings (Session 14):** Lighting, camera, and weather are auto-applied based on mode/habitat/species — no longer shown as user menus.
- **Wide-mode composition system (Sessions 13–14):** WIDE_MODES auto-trigger ultra-wide framing with landscape-dominant composition, subject reads small in frame, anatomy detail suppressed, close-up blockers in `--no`.
- **Clade-aware everything:** style anchor, negative prompt, mouth/teeth, interaction block, realism block — all picked from per-clade dicts.
- **Context-reactive branching:** Fully implemented for terrestrial, marine, aerial — **arthropod and plant use generic fallback**.
- **Invalid combo blocking:** Active for terrestrial, marine, aerial — not yet implemented for arthropod/plant.
- **Modular 4-step workflow:** All 4 steps output per run; arthropods get species-specific mouthpart fixes; plants skip Steps 2 and 4.

### Species Anatomy Module System (Session 15)

#### Architecture
```
species/
├── __init__.py          # Registry: SPECIES_REGISTRY dict + get_anatomy() lookup
├── base.py              # Dataclasses + build_anatomy_prompt() / build_anatomy_negative()
├── tyrannosaurus_rex.py # Per-species ANATOMY object (one per species)
├── velociraptor.py
├── ... (42 species modules total)
└── sigillaria.py
```

#### Dataclasses (base.py)
- **SkullAnatomy** — overall_shape, distinctive_features, eye_description, nostril_position, crest_or_horn, beak
- **DentitionProfile** — tooth_shape, tooth_count_note, jaw_mechanics, bite_force_note, visible_teeth
- **LimbStructure** — forelimb, hindlimb, wing_or_flipper, stance, digit_count, special_appendage
- **Integument** — primary_covering, texture_detail, special_structures, membrane, armor
- **BodyProportions** — body_length_m, body_mass_kg, build, neck, tail, silhouette, size_comparison
- **ColorationEvidence** — likely_pattern, display_structures, fossil_evidence, additional_notes
- **LocomotionProfile** — primary_mode, swimming, flight, gait_detail, speed_note, special
- **FloraAssociation** — primary_flora, ground_cover, canopy, water_plants, banned_flora
- **SpeciesAnatomy** — master class holding all sub-dataclasses plus species_name, common_name, period, habitat, unique_features[]

#### Prompt Builders
- **`build_anatomy_prompt(anatomy, mode_type)`** — generates MJ-ready anatomy string:
  - `"close"` — full detail: skull, teeth, integument, limbs, body, coloration, locomotion, 3 unique features
  - `"mid"` — moderate: skull shape, tooth shape, integument, silhouette+build+size_comparison, 1 limb detail, coloration, 3 unique features
  - `"wide"` — minimal: silhouette + 2 unique features only
- **`build_anatomy_negative(anatomy)`** — returns banned flora for `--no` (e.g. "grass" for Jurassic species, "flowering plants" for Carboniferous)

#### Mode Mapping in assemble_prompt()
| anatomy_mode | Output modes |
|---|---|
| `"close"` | portrait, extreme_closeup, eye_contact, jaws_detail, action_freeze |
| `"mid"` | canvas, tracking_side, ground_level, camera_trap, confrontation, shoreline, group_herd, etc. |
| `"wide"` | environmental, valley_panorama, ridgeline_silhouette, river_crossing, misty_dawn, storm_front |

#### Current Prompt Lengths (anatomy only, before environment/interaction/flags)
| Species | close | mid | wide |
|---|---|---|---|
| T. rex | 2751 chars / 65 clauses | 1444 / 35 | 263 / 8 |
| Velociraptor | 2595 / 55 | 1443 / 30 | 312 / 7 |
| Spinosaurus | 2579 / 61 | 1305 / 29 | 306 / 4 |
| Pteranodon | 2285 / 56 | 1103 / 27 | 235 / 7 |
| Mosasaurus | 2072 / 49 | 1219 / 28 | 279 / 6 |
| Lepidodendron | 975 / 16 | 830 / 14 | 269 / 5 |

**⚠️ Close/mid anatomy prompts are currently too long for MJ.** MJ performs best with ~60-word prompts. Close mode at 55-65 clauses is massively over-token and will cause MJ to ignore later clauses. This is the #1 priority for Session 16.

## Known Issues
- **Anatomy prompts too verbose for MJ** — close mode outputs 2000-2700 chars (55-65 clauses) of anatomy data. MJ's effective attention window is ~60 words / ~350 chars. Everything beyond that is increasingly ignored. The `build_anatomy_prompt()` function needs aggressive compression to output 6-10 high-impact phrases per species, not 30-65.
- **`species_reference/` folders are mostly empty** — READMEs exist with guidance but no actual reference images, skeletal diagrams, or scientific PDFs have been added. These folders should also contain MJ-specific prompt notes (what works, what doesn't for each species).
- **Sessions 13-14 lean output not yet validated with the new anatomy system** — the anatomy module injection replaces the old science fields but hasn't been visually tested in MJ yet.
- **Arthropod/plant have no context-reactive suggestions** — `get_suggestions()` and `get_blocked()` fall through to empty defaults.
- **`condition` param values can leak surface language underwater** — observed: Elasmosaurus underwater included `"head raised vertically above surface"` because condition param contained surface language.
- ~~**Git LFS not installed**~~ ✅ Session 18 — removed LFS hooks entirely. Reference images go to Discord via webhook, not git.
- **`style_param` and `camera_param` are dead inputs to the prose path** — still pass through `assemble_prompt` signature for tag wiring but values are never read for prose.

## Session 12 — Wide Shot Composition Fix
*(see "All Changes By Session" above for Sessions 1-11)*

### Trigger
User found wide shot modes were producing close-up portraits instead of epic landscape canvas prints. The animal filled the frame when it should have been a small figure in a vast environment.

### Root cause
MJ heavily weights early tokens. The subject block (species name + anatomy + pose + condition) was ~20 clauses appearing before environment, so MJ prioritized the animal over the landscape. The word "wide" in composition wasn't enough to override the anatomical detail pull.

### Fix
- Created `WIDE_MODES` set: `{environmental, valley_panorama, ridgeline_silhouette, river_crossing, misty_dawn, storm_front}`
- Wide mode detection: `wide_mode = placement_wide or output_mode in WIDE_MODES`
- When `wide_mode` is active:
  - Subject block stripped to name + description only (no anatomy, no required params, no skin texture, no teeth, no condition)
  - Ultra-wide camera injection: `"shot on ultra-wide 16mm lens, deep depth of field, everything in focus"`
  - Environment overridden with wide composition block: `"ultra-wide angle, vast sweeping landscape, single animal small but clearly visible in frame, large negative space, deep layered depth, epic sense of scale, landscape dominant"`
  - Section order flipped: Subject → Camera → Environment → Lighting → Interaction (camera early = composition driver)
  - Close-up blockers added to `--no`: `"close-up, portrait, headshot, tight crop, macro, face filling frame, telephoto compression, shallow depth of field, bokeh background, detail shot, extreme close-up"`

## Session 13 — (merged into Session 12 above)

## Session 14 — Output Mode Redesign + Auto Scene Settings

### Output Mode Overhaul (20 → 25)
Redesigned all output modes with clear intent separation. Added 6 epic wide landscape modes, specialty atmospheric modes, and ensured every habitat has meaningful options.

### Auto-Selected Scene Settings
Lighting, camera, and weather are now automatically selected based on mode/habitat/species context rather than presented as separate user menus. User flow simplified to: Habitat → Mode → Species → Mood → Behavior → Condition.

## Session 15 — Species Anatomy Module System

### What changed
Built a complete per-species anatomy module system (`species/` Python package) with scientifically accurate data for all 42 species. Each module defines skull, dentition, limbs, integument, body proportions, coloration evidence, locomotion, flora associations, and unique features as structured Python dataclasses.

### Files created
- `species/base.py` — 8 anatomy dataclasses + `build_anatomy_prompt()` and `build_anatomy_negative()` helpers
- `species/__init__.py` — registry mapping all 42 DB species names to anatomy module objects
- 42 individual species modules (`species/tyrannosaurus_rex.py` through `species/sigillaria.py`)

### Integration
- `generate_prompt.py` imports `get_anatomy`, `build_anatomy_prompt`, `build_anatomy_negative` from `species`
- In `assemble_prompt()`, anatomy data replaces old science-table fields (feathering_coverage, tail_posture, skin_texture_type, known_coloration_evidence)
- Anatomy detail level scales with output mode: close (full detail), mid (moderate), wide (silhouette only)
- Banned flora from anatomy modules injected into `--no` negative prompt (prevents anachronistic vegetation)
- Graceful fallback to old science-table fields if anatomy module somehow missing

### Species covered (42 total)
| Habitat | Count | Species |
|---|---|---|
| Terrestrial | 8 | T. rex, Velociraptor, Triceratops, Stegosaurus, Brachiosaurus, Ankylosaurus, Parasaurolophus, Dilophosaurus |
| Marine | 14 | Mosasaurus, Elasmosaurus, Ichthyosaurus, Liopleurodon, Kronosaurus, Spinosaurus, Megalodon, Cretoxyrhina, Helicoprion, Dunkleosteus, Xiphactinus, Leedsichthys, Archelon, Ammonite |
| Aerial | 4 | Pteranodon, Quetzalcoatlus, Rhamphorhynchus, Dimorphodon |
| Arthropod | 8 | Meganeura, Arthropleura, Jaekelopterus, Pulmonoscorpius, Megarachne, Anomalocaris, Eurypterus, Megalograptus |
| Plant | 8 | Lepidodendron, Calamites, Glossopteris, Williamsonia, Araucaria, Archaefructus, Wattieza, Sigillaria |

## Session 16 — CLIP-Optimized Shorthand + Budget System

### What changed
Rewrote the anatomy prompt builder to solve the core problem: Session 15's verbose anatomy data (2000-2700 chars, 55-65 clauses) was far beyond MJ's effective attention window (~60 words). Implemented three converging fixes: prompt compression (#1), hard budget system (#4), and CLIP-optimized shorthand (#5).

### Budget system (`species/base.py`)
- **`BUDGET_CLOSE = 350`** chars — all shorthand + size_comparison + coloration hint
- **`BUDGET_MID = 250`** chars — silhouette + top shorthand phrases
- **`BUDGET_WIDE = 120`** chars — silhouette + one key feature
- **`_budget_join(phrases, budget)`** — fills phrases in priority order until cap reached; always includes first phrase (most visually distinctive)
- Fallback path (`_fallback_prompt()`) for species without shorthand: priority-ranked field extraction (silhouette → texture → skull → teeth → size → unique feature → coloration)

### `mj_shorthand` field
Added `mj_shorthand: list[str]` to `SpeciesAnatomy` dataclass. Each species defines 5-8 CLIP-optimized phrases:
- 2-5 words per phrase, visually concrete, no explanatory prose
- Priority-ordered: index 0 = most visually distinctive feature
- Examples:
  - T. rex: `["massive deep skull with binocular eyes", "tiny two-fingered arms", "pebbly non-overlapping scales", "thick horizontal tail as counterbalance", "powerful pillar-like biped legs", "serrated banana-shaped teeth", "12m long bus-sized predator"]`
  - Anomalocaris: `["two large spiny grasping frontal appendages", "circular pineapple-ring mouth", "stalked compound eyes 16000 lenses", "rippling lateral swimming lobes", "semi-translucent flattened oval body", "1m Cambrian apex predator"]`
  - Lepidodendron: `["diamond-pattern bark from leaf cushions", "unbranched trunk 30m tall column", "crown of forking branches at very top only", "grass-like drooping leaves", "pale grey-green bark with geometric scars"]`

### Compression results (close mode)
| Species | Before | After | Reduction |
|---|---|---|---|
| T. rex | 2751 chars / 65 clauses | 299 chars / 43 words | 89% |
| Velociraptor | 2595 / 55 | 273 / 43 | 89% |
| Spinosaurus | 2579 / 61 | 239 / 29 | 91% |
| Pteranodon | 2285 / 56 | 345 / 50 | 85% |
| Mosasaurus | 2072 / 49 | 285 / 42 | 86% |

### Validation
- **126/126** combinations (42 species × 3 modes) pass budget — 0 violations
- **37/42** species have banned flora negatives (5 marine species correctly have none)
- `build_anatomy_prompt()` signature unchanged — `generate_prompt.py` integration untouched
- Fixed Brachiosaurus silhouette (123 → 100 chars) to fit wide budget

### Files modified
- `species/base.py` — rewrote prompt builder section (budget constants, `_budget_join()`, new `build_anatomy_prompt()`, `_fallback_prompt()`, removed old `_collect_strings()`)
- All 42 species modules — added `mj_shorthand` field
- `species/brachiosaurus.py` — trimmed silhouette text
- `generate_prompt.py` — updated comment block only
- `.gitignore` — added `.env`, `*_backup.py`, `.gitattributes.bak`

### Commit
`e8cd39a` — pushed to `main`

---

## Session 17 — Per-Species Stylize, Multi-Subject Scenes, A/B Testing, CLIP Audit

### What changed
Completed all remaining priorities (#2, #7, #8, #9, #10). The system now has:
- Per-species `--stylize` recommendations and known MJ failure mode display
- Arthropod + plant context-reactive suggestion and blocking systems
- CLIP tokenizer awareness (stopword stripping, token estimation, duplicate removal)
- Multi-subject scene support (predator-prey, ecosystem dioramas)
- Full A/B testing framework for systematic prompt optimization

### Priority #7 — Per-species --stylize + known failures
- Added `recommended_stylize: tuple[int, int, int]` and `known_failures: list[str]` to `species/base.py` SpeciesAnatomy dataclass
- Populated all 42 species modules with species-appropriate stylize ranges and known MJ failure modes
- Generator auto-applies species-recommended `--stylize` when no user override
- Known failures displayed during species selection with ⚠ markers
- **Commit:** `21fb52c`

### Priority #9 — Arthropod/plant context-reactive systems
- `get_arthropod_suggestions()` / `get_arthropod_blocked()`: Carboniferous → coal-swamp, Cambrian → open-water, Devonian → shallow-reef, Ordovician/Silurian → tidal
- `get_plant_suggestions()` / `get_plant_blocked()`: era-appropriate vegetation/weather, growth-stage lighting
- Invalid combinations blocked with reason strings (e.g. "snowy weather contradicts tropical Carboniferous coal swamp")
- **Commit:** `44b42c3`

### Priority #2 — CLIP tokenizer audit
- `_CLIP_STOPWORDS`: set of prose connector words stripped from DB phrases
- `_clip_clean(phrase)`: removes stopwords, returns CLIP-friendly comma-separated tokens
- `_estimate_clip_tokens(text)`: rough estimate (words × 1.3), warns at 77-token CLIP limit
- Subject `species["description"]` dropped when anatomy module present (avoids redundant tokens)
- Behavior + condition DB values cleaned via `_clip_clean()` before injection
- Token count displayed after every prompt box output

### Priority #8 — Multi-subject scenes
- New output modes: `predator_prey`, `ecosystem_diorama` (both terrestrial + marine)
- `PREDATOR_PREY_PAIRINGS`: T.rex→[Triceratops, Parasaurolophus, Ankylosaurus], etc.
- `ECOSYSTEM_PAIRINGS`: maps each species to contemporary cohabitants
- `PREDATOR_PREY_INTERACTIONS`: 4 types with MJ-optimized descriptions (stalking/confrontation/chase/ambush)
- `build_multi_subject_block()`: primary gets "mid" anatomy budget, secondary gets "wide"
- Interactive picker for secondary species and interaction type

### Priority #10 — A/B testing framework
- **Schema**: `ab_tests` + `ab_variants` tables (in `schema.sql` + idempotent `_ensure_ab_tables()`)
- **CLI flags**: `--ab-test`, `--ab-score ID`, `--ab-history`
- **Axes**: lighting, mood, condition, behavior, stylize, output_mode
- **Flow**: select species → pick axis → pick A/B values → generate both prompts → display side-by-side
- **Scoring**: `--ab-score ID` rates each variant 1-5, picks winner (A/B/tie), saves notes
- **History**: `--ab-history` shows tabular view of last 20 tests with winners
- **Integration**: `show_species_ab_summary()` displays winning params during normal species selection

### CLI arguments (updated)
| Flag | Default | Purpose |
|------|---------|---------|
| `--style` | `raw` | MJ style mode |
| `--stylize` | species-specific | MJ stylize (auto-applied from anatomy module) |
| `--chaos` | `0` | MJ chaos |
| `--quality` | `1.0` | MJ quality |
| `--sref` | None | Style reference URL |
| `--cref` | None | Character reference URL |
| `--ab-test` | — | Enter A/B testing mode |
| `--ab-score ID` | — | Score an existing A/B test |
| `--ab-history` | — | Show A/B test history |

### Files modified
- `generate_prompt.py` — +854 lines: CLIP audit, multi-subject, A/B testing (3924 lines total)
- `schema.sql` — added `ab_tests` + `ab_variants` tables
- `species/base.py` — added `recommended_stylize`, `known_failures` fields
- All 42 species modules — populated with stylize ranges + failure modes

### Commits
- `21fb52c` — Priority #7: per-species stylize + known failures
- `44b42c3` — Priority #9: arthropod/plant context-reactive suggestions
- `24c3f95` — Priorities #2, #8, #10: CLIP audit, multi-subject, A/B testing

---

## Session 18 — Group Modes, Feathered Species, Reference Image Pipeline

### What changed
Expanded group/multi-animal output modes, added feathered integument to T. rex and Dilophosaurus, built automated Discord reference image upload pipeline for `--sref` workflow.

### Group Mode Expansion (1 → 4)
- **`GROUP_MODES`** set: `{group_herd, family_group, waterhole_gather, migration_march}`
- All group modes share: explicit count in first tokens, `"wide"` anatomy level, `"full body head to tail"` suppressed
- `is_group` check updated from `output_mode == "group_herd"` to `output_mode in GROUP_MODES`
- Per-mode `GROUP_LEADS` dict with count + composition framing:
  - `group_herd` — "three {species}, spaced apart, each animal distinct, candid wildlife photograph"
  - `family_group` — "one large adult with two smaller juveniles, size variation visible"
  - `waterhole_gather` — "three {species} at muddy water edge, drinking and wading, trampled mud bank"
  - `migration_march` — "column of five {species} walking in loose line receding into distance"
- Anti-CGI waterhole fix: removed "reflections in still water" (triggered CG-mirror), replaced with "murky disturbed water, imperfect natural detail"
- All group compositions include "imperfect natural detail" grounding phrase
- `GROUP / MULTI-ANIMAL` section header added to `select_mode()` menu

| Mode | Habitats | Lead animal count |
|---|---|---|
| `group_herd` | all 5 | three |
| `family_group` | terrestrial, marine, aerial, arthropod | one adult + two juveniles |
| `waterhole_gather` | terrestrial | three |
| `migration_march` | terrestrial, marine, aerial | five |

### Feathered Species Updates
- **T. rex** — integument rewritten from pure scales to dense filamentous proto-feathers:
  - `"dense shaggy proto-feathers like cassowary plumage"` in shorthand
  - `"earth-toned brown feathers with iridescent sheen"` — golden eagle color reference
  - `"bare scaly skin on snout and lower legs"` — mixed coverage like real birds
  - Silhouette updated: `"massive feathered bipedal predator"`
  - Known failure updated: "rainbow/parrot feathers — use cassowary/eagle references"
- **Dilophosaurus** — integument rewritten to feathered:
  - `"filamentous proto-feathers like emu plumage"` body covering
  - `"display plumes framing twin crests like secretary bird"` — leverages MJ's secretary bird training data
  - `"vivid red-orange crest skin like cassowary wattle"` — display coloration
  - Silhouette updated: `"gracile feathered bipedal predator"`
  - 7 CLIP-optimized shorthand phrases (was 6)
- **Velociraptor** — already had full feathering from Session 15, unchanged
- **Species selection** — `[feathered]` tag shown next to species with feathering/pycnofibers in anatomy module (7 species total: T. rex, Velociraptor, Dilophosaurus, Pteranodon, Quetzalcoatlus, Rhamphorhynchus, Dimorphodon)

### Reference Image Upload Pipeline
- **`upload_refs.py`** — automated Discord webhook uploader:
  - `python3 upload_refs.py all` — batch uploads all new images from `reference_images/` subfolders
  - `python3 upload_refs.py upload --file photo.jpg --category waterhole` — single image upload
  - `python3 upload_refs.py list` — show all uploaded URLs
  - Captures Discord CDN URLs from webhook response
  - Auto-wires URLs into `sref_urls.json` mapped to relevant species via `CATEGORY_SPECIES_MAP`
  - Duplicate detection (skips already-uploaded files)
- **`reference_images/`** — 10 category folders:
  - `waterhole/` → Stegosaurus, Triceratops, Ankylosaurus, Brachiosaurus, Parasaurolophus, T. rex
  - `migration/` → Parasaurolophus, Brachiosaurus, Triceratops, Stegosaurus, Ankylosaurus
  - `family/` → all terrestrial + Velociraptor
  - `crocodile/` → T. rex, Spinosaurus, Mosasaurus, Kronosaurus, Liopleurodon, Dilophosaurus
  - `feathered_biped/` → T. rex, Velociraptor, Dilophosaurus
  - `tall_predator/` → Velociraptor, Dilophosaurus, T. rex
  - `komodo/` → T. rex, Velociraptor, Dilophosaurus, Spinosaurus
  - `arthropod_group/` → all 8 arthropod species
  - `tortoise_group/` → Ankylosaurus, Archelon, Stegosaurus, Triceratops
  - `raptor_flight/` → all 4 aerial species
- **Webhook URL** stored in `.env` as `DISCORD_WEBHOOK_URL`

### Files created
- `upload_refs.py` — Discord webhook uploader + sref_urls.json wiring
- `reference_images/` — 10 category subdirectories

### Files modified
- `generate_prompt.py` — GROUP_MODES set, 3 new output modes, GROUP_LEADS dict, is_group logic, [feathered] tag in species selection, anti-CGI waterhole composition
- `species/tyrannosaurus_rex.py` — feathered integument, coloration, silhouette, shorthand, known_failures
- `species/dilophosaurus.py` — feathered integument, coloration, silhouette, shorthand, known_failures
- `.env` — added DISCORD_WEBHOOK_URL

---

## Session 19 — Predator–Prey Rewrite, --sref Pipeline Fix, Naturalism Injection

### What changed
Fixed the `--sref` system (Wikimedia URLs rejected by MJ), rewrote the predator_prey prompt system across 5 iterations based on live MJ testing, and injected living-animal naturalism language extracted from user-provided reptile reference photos.

### --sref Reference Library Restructure
- **Problem:** Wikimedia Commons URLs have percent-encoded paths and redirects — MJ shows "Invalid link" error
- **Solution:** Two-file system separating source catalog from MJ-ready URLs:
  - `sref_sources.json` — 43 verified Wikimedia URLs (download catalog)
  - `sref_urls.json` — Discord CDN URLs that MJ actually accepts
- `upload_refs.py` rewritten with 5 commands: `download`, `upload`, `sync`, `all`, `list`
- 4 new reference_images categories: `marine/`, `sea_scorpion/`, `paleo_plant/`, `ammonite/`
- 40 Discord CDN URLs wired across 27/42 species
- Wikimedia rate-limiting (429 after ~10 requests) prevented full download — increased delays to 3s/5s

### Predator–Prey Prompt Rewrite (5 iterations)

**Problem 1 — Prey species not rendering:**
- Root cause: Primary anatomy at "mid" detail consumed ~33 words, pushing prey name past CLIP's 77-token window
- Fix: Front-loaded "one X with one Y" as first tokens, both species use "wide" anatomy only (~15 words each)
- Result: Both species now render in all 4 MJ panels

**Problem 2 — Species physically merging into chimeras:**
- Added `PREDATOR_PREY_INTERACTIONS` with spatial separation language
- Added predator_prey-specific negative prompt: `merged bodies, conjoined animals, fused creatures, chimera, hybrid animal, two-headed, morphing, blended anatomy`
- Result: Bodies separated but still floating near each other passively

**Problem 3 — No scale difference (prey drawn same size as predator):**
- `build_multi_subject_block()` now reads `body_length_m` from both anatomy modules
- When ratio > 3:1, injects "tiny [prey] dwarfed by massive [predator]"
- Mosasaurus (13m) vs Ammonite (0.5m) = 26:1 ratio → scale language fires
- Added "same size animals, equal sized" to negative prompt
- Stripped terrestrial "dappled light through canopy gaps" from marine scenes
- Result: Scale noticeably improved, Ammonite rendered smaller

**Problem 4 — No interaction (animals just float near each other):**
- **NEW: `HUNT_MOMENTS` dict** — 17 predator/prey pairs × 4 interaction types = 68 bespoke frozen-moment descriptions based on real paleontology
- Each entry describes a specific physical action, not a spatial relationship:
  - Mosasaurus + Ammonite: "mosasaurus jaw closing around ammonite shell, crushing bite, shell cracking"
  - T. rex + Triceratops: "tyrannosaur and triceratops locked face to face, horns versus jaws"
  - Velociraptor + Para: "velociraptor leaping at parasaurolophus flank, sickle claw extended"
- Falls back to generic `PREDATOR_PREY_INTERACTIONS` if no species-pair entry exists
- Subject block now front-loads the hunt ACTION instead of generic scale/position language
- Composition changed to "candid wildlife encounter, two different animals in frame, decisive moment"

**Problem 5 — Doesn't look like real nature (CG render feel):**
- Section 2 (interaction) now habitat-specific for predator_prey:
  - Marine: "murky water, sediment particles, bubbles trailing, bodies moving through water"
  - Terrestrial: "dirt kicked up, dust and debris, muscles tensed, raw animal energy"
- Replaced "National Geographic wildlife photograph" (risked Session 11 staged-specimen bias)

### Naturalism Injection (from user's reptile reference photos)
User provided ~15 reference photos: Komodo dragons (jaw gape, tongue, walking, full body), crocodiles (feeding, basking, head portrait, swimming, group), agama lizards, vine snakes, chameleons, iguanas, sea turtles, tortoises, flying lizards (Draco).

Extracted visual qualities and injected as living-animal texture phrase for close/mid modes:
- **Terrestrial:** "individual scales catching sunlight, warm natural light, living animal"
- **Marine:** "wet skin catching light, water particles, living animal"
- **Arthropod:** "individual chitin plates catching light, organic imperfection, living animal"
- Skipped for wide modes (surface detail not resolvable) and plants
- Describes visual QUALITIES directly, not camera/magazine names (avoids Session 11 staged-specimen bias)

### Token budget for predator_prey (Mosasaurus + Ammonite example)
```
Position  Tokens  Content
1-8       ~8      "one massive Mosasaurus with one medium Ammonite"
9-22      ~14     "mosasaurus jaw closing around ammonite shell, crushing bite, shell cracking"
23-30     ~8      "tiny Ammonite dwarfed by massive Mosasaurus"
31-45     ~15     Mosasaurus wide anatomy (silhouette + top shorthand)
46-58     ~13     Ammonite wide anatomy (silhouette + top shorthand)
59-68     ~10     "murky water, sediment particles, bubbles trailing..."
69-80     ~12     Environment + composition + lighting (fading CLIP attention)
```
Critical content (species names, hunt action, scale) all in first ~30 tokens.

### Files modified
- `generate_prompt.py` — HUNT_MOMENTS (68 entries), build_multi_subject_block() scale anchoring, predator_prey negative prompt, habitat-specific interaction override, living-animal naturalism phrase, predator_prey composition rewrite
- `upload_refs.py` — rewritten with download/sync/upload/list commands, 14 categories
- `sref_urls.json` — reset to Discord CDN URLs (40 URLs, 27 species)
- `sref_sources.json` — NEW, 43 Wikimedia source URLs

### Commits
| Hash | Description |
|------|-------------|
| `6bc450a` | sref_urls.json: 92 Wikimedia URLs across 42 species |
| `a047755` | sref restructure: two-file system, upload_refs.py rewrite |
| `838b27d` | predator_prey CLIP fix: front-load species names, wide anatomy |
| `2b1be5f` | predator_prey: spatial separation + negative prompt |
| `fee8065` | predator_prey: body_length_m scale anchoring |
| `12a9788` | predator_prey: 68 species-pair hunt moments |
| `50ad2d6` | naturalism injection from reptile reference photos |

---

## Next Priorities (Session 19)

### ~~1. Compress anatomy prompts for MJ's attention window~~ ✅ Session 16

### ~~2. Audit prompts against MJ's CLIP tokenizer behavior~~ ✅ Session 17
Added `_clip_clean()` stopword stripper, `_estimate_clip_tokens()` with 77-token warning, dropped species description when anatomy module present, behavior/condition cleaned before injection. Token count displayed after every prompt box.

### ~~3. Add MJ prompt notes to species_reference/ folders~~ ✅ Session 16
All 42 species_reference/ READMEs have MJ Prompt Notes sections with CLIP shorthand, stylize ranges, known failures, and --sref test result tables.

### ~~4. Build a prompt-length validator / budget system~~ ✅ Session 16

### ~~5. Create MJ-optimized "visual shorthand" per species~~ ✅ Session 16

### ~~6. Add `--sref` test results to species_reference/ folders~~ ✅ Session 16
All 42 READMEs have `--sref Test Results` tables ready to populate with empirical data.

### ~~7. Implement per-species `--stylize` recommendations~~ ✅ Session 17
Added `recommended_stylize` and `known_failures` fields to base.py + all 42 species modules. Generator auto-applies species-recommended --stylize when no user override. Known failures displayed during species selection.

### ~~8. Add multi-subject scene support~~ ✅ Session 17, upgraded Session 19
New output modes: `predator_prey`, `ecosystem_diorama`. PREDATOR_PREY_PAIRINGS maps predator→prey, ECOSYSTEM_PAIRINGS maps cohabitants. 4 interaction types (stalking/confrontation/chase/ambush). Both species get "wide" anatomy budget. Full interactive picker in main flow. Session 19: added `HUNT_MOMENTS` (68 species-pair-specific frozen-moment descriptions), `body_length_m` ratio-based scale anchoring, habitat-aware interaction/composition, living-animal naturalism injection.

### ~~9. Implement arthropod/plant context-reactive suggestions + blocking~~ ✅ Session 17
`get_arthropod_suggestions()`, `get_arthropod_blocked()`, `get_plant_suggestions()`, `get_plant_blocked()` with Carboniferous→coal-swamp, Cambrian→open-water, era-appropriate vegetation/weather suggestions. Invalid combos blocked with reasons.

### ~~10. Build a prompt A/B testing framework~~ ✅ Session 17
Full A/B testing system: `--ab-test` generates two prompt variants differing on one axis (lighting/mood/condition/behavior/stylize/output_mode). `--ab-score ID` rates and picks winner. `--ab-history` shows past results. DB tables: `ab_tests` + `ab_variants`. Species selection shows prior A/B wins. Designed for systematic MJ testing workflow.

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

---

## 10 Ideas — Next Phase

### 1. --sref Reference Library Build-Out  🔄 IN PROGRESS
Source and upload all 10 reference photo categories (waterhole, migration, family, crocodile, feathered_biped, tall_predator, komodo, arthropod_group, tortoise_group, raptor_flight). Run `python3 upload_refs.py all` to batch-wire CDN URLs into `sref_urls.json`. Test each category against 2-3 species to validate MJ pulls the right photographic qualities. This is the single highest-impact improvement available right now.

**Session 19 progress:**
- ✅ Populated `sref_urls.json` with 92 Wikimedia URLs → discovered MJ rejects Wikimedia URLs (percent-encoded, redirects)
- ✅ Restructured: `sref_sources.json` (Wikimedia catalog, 43 URLs) → download locally → upload to Discord → `sref_urls.json` (CDN URLs MJ accepts)
- ✅ Rewrote `upload_refs.py` with `download`, `upload`, `sync`, `all`, `list` commands
- ✅ 40 Discord CDN URLs across 27/42 species wired into `sref_urls.json`
- ✅ 4 new reference_images categories added: `marine/`, `sea_scorpion/`, `paleo_plant/`, `ammonite/`
- 🔄 15 species still need images (Wikimedia rate-limited at 429 after ~10 requests)
- 🔄 User sourced komodo + crocodile reference photos — need to save to folders and run `upload_refs.py all`

### 2. Printify Integration — Auto-Upload Best Outputs to Store
Connect `generate_prompt.py` to the Printify API (key already in `.env`). After scoring an A/B test winner or manually marking an output as "print-worthy", auto-upload to Printify as a canvas/poster product with species name, mode, and prompt metadata. Eliminates the manual download→upload→configure loop.

### 3. Batch Generation Mode
Add `--batch` flag that runs through a curated list of species/mode/condition combos and outputs all prompts to a file. User can then paste them into MJ sequentially. Good for overnight generation runs — queue 50 prompts, come back to results. Could also integrate with MJ's `/imagine` queue if API access becomes available.

### 4. Prompt Scoring Dashboard
Build a local web dashboard (Flask or Streamlit) that displays generated images alongside their prompts, A/B test results, and scores. Allows visual side-by-side comparison, tagging ("print-worthy", "needs vary region", "anatomy fail"), and filtering by species/mode/score. Pulls from the existing `prompts` and `ab_tests` DB tables.

### 5. Vary Region Prompt Refinement
The 4-step workflow (main → feet fix → background fix → mouth fix) outputs static prompts. Build an interactive Vary Region assistant: user selects which region failed, system generates a targeted fix prompt with the right anatomy data and `--stylize` for that specific region. Could also learn from past fixes — if T. rex feet always need the same fix, auto-suggest it.

### 6. Seasonal/Time-of-Day Scene Presets
Create curated scene presets that bundle lighting + weather + mood + condition into a single choice: "Monsoon Season" (storm light, heavy rain, mud-caked, waterhole overflow), "Dry Season Drought" (harsh midday, heat haze, lean season, dust), "Dawn Patrol" (first light, ground mist, alert scan, dew-wet). Reduces the menu flow from 6 choices to 1 for users who want a cohesive scene fast.

### 7. Species Interaction Ecosystem Scenes
Expand beyond predator_prey and ecosystem_diorama to full ecosystem tableaux: a waterhole scene with herbivores drinking while a predator watches from treeline, pterosaurs overhead, insects on the water surface. Multiple species from different habitats in one frame. Would need careful token budgeting — primary subject gets "mid", secondary gets "wide", background species get name-only.

### 8. MJ Output Feedback Loop
After generating a prompt, user pastes the MJ output image back into the system. Use CLIP or a vision model to score how well the output matches the prompt intent (did we get 3 animals? is the skin texture right? are the feet anatomically correct?). Auto-suggest prompt adjustments based on what failed. Over time, builds a per-species knowledge base of what works and what doesn't.

### 9. Feathered vs Scaly Toggle
Add a `--feathered` / `--scaly` CLI flag that switches between the feathered and scaled integument variants for species where both are scientifically plausible (T. rex, Dilophosaurus). Store both versions in the anatomy module and let the user choose at runtime. Could also add a "partial feathering" option (feathered back/arms, scaly belly/legs) for maximum variety.

### 10. Claude Code + VS Code Integrated Pipeline
Build a VS Code task pipeline using Claude Code that automates the full workflow:
- **Task 1: Generate** — run `generate_prompt.py` interactively in the VS Code terminal, select species/mode/conditions
- **Task 2: Upload refs** — drag reference images into `reference_images/` folders in the VS Code file explorer, run `upload_refs.py all` via task
- **Task 3: Review** — after MJ generation, open results in VS Code image preview, use Claude Code to analyze anatomy accuracy and suggest fixes
- **Task 4: Score** — run `--ab-score` from VS Code terminal, results auto-logged to DB
- **Task 5: Ship** — mark winners as print-worthy, auto-push to Printify via API
- All steps accessible via VS Code keyboard shortcuts or the command palette
