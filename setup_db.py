"""
Set up the dinosaur art prompt engineering SQLite database.

Usage:
    python setup_db.py              # creates dino_art.db with schema + seed data
    python setup_db.py --no-seed    # schema only
    python setup_db.py --db PATH    # custom database path
"""

import argparse
import sqlite3
from pathlib import Path

DB_DEFAULT = Path(__file__).parent / "dino_art.db"
SCHEMA_FILE = Path(__file__).parent / "schema.sql"


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

SEED_SPECIES = [
    # (name, common_name, period, diet, size_class, description, notes, habitat)
    ("Tyrannosaurus rex",   "T. rex",      "Cretaceous", "Carnivore", "Massive", "Apex predator of the Late Cretaceous",           None, "terrestrial"),
    ("Velociraptor",        "Raptor",      "Cretaceous", "Carnivore", "Small",   "Small feathered solitary predator, small-prey specialist",
     "closed mouth option, low-slung feathered biped, propatagium confirmed — forearm folds inward at rest (bird-like wing fold), not held straight out; sickle claw raised off ground",
     "terrestrial"),
    ("Triceratops",         "Triceratops", "Cretaceous", "Herbivore", "Large",   "Three-horned ceratopsid",                        None, "terrestrial"),
    ("Stegosaurus",         "Stegosaurus", "Jurassic",   "Herbivore", "Large",   "Plated herbivore with thagomizer tail",           None, "terrestrial"),
    ("Brachiosaurus",       "Brachiosaurus","Jurassic",  "Herbivore", "Massive", "Long-necked sauropod",                           None, "terrestrial"),
    ("Ankylosaurus",        "Ankylosaurus","Cretaceous", "Herbivore", "Large",   "Armored dinosaur with club tail",                None, "terrestrial"),
    ("Pteranodon",          "Pteranodon",  "Cretaceous", "Piscivore", "Large",   "Large pterosaur (not a dinosaur, but a classic)", None, "aerial"),
    ("Spinosaurus",         "Spinosaurus", "Cretaceous", "Piscivore", "Massive", "Sail-backed semi-aquatic predator",
     "closed mouth option, low-slung quadrupedal stance, elongated torso with disproportionately small hindlimbs, "
     "deep muscular sail along spine",
     "marine"),
    ("Parasaurolophus",     "Para",        "Cretaceous", "Herbivore", "Large",   "Crested hadrosaur",                              None, "terrestrial"),
    ("Dilophosaurus",       "Dilopho",     "Jurassic",   "Carnivore", "Medium",  "Double-crested early theropod",                  None, "terrestrial"),
    # Marine species
    ("Mosasaurus",          "Mosasaur",    "Cretaceous", "Carnivore", "Massive", "Large marine reptile, elongated body, four short flippers, deep laterally compressed tail",
     "fully aquatic, keeled scales along back, rounded snout, conical teeth varying in size, loose jaw hinge allowing wide gape, barrel-shaped torso tapering to crescent tail fin", "marine"),
    ("Elasmosaurus",        "Elasmosaur",  "Cretaceous", "Piscivore", "Large",   "Extremely long-necked plesiosaur, small head, four broad flippers",
     "fully aquatic, neck longer than body, small head with needle-like teeth, four paddle-shaped flippers", "marine"),
    ("Ichthyosaurus",       "Ichthyosaur", "Jurassic",   "Piscivore", "Medium",  "Dolphin-shaped marine reptile, large eyes, streamlined body",
     "fully aquatic, dolphin-like body shape, enormous eyes, dorsal fin, crescent tail fluke, smooth skin", "marine"),
    ("Liopleurodon",        "Liopleurodon","Jurassic",   "Carnivore", "Large",   "Short-necked pliosaur, massive skull, four powerful flippers",
     "fully aquatic, enormous head relative to body, four large flippers, powerful bite, robust body", "marine"),
    ("Kronosaurus",         "Kronosaurus", "Cretaceous", "Carnivore", "Large",   "Giant pliosaur, massive jaws, short neck, powerful build",
     "fully aquatic, enormous skull, short thick neck, four broad flippers, barrel-shaped body", "marine"),
    # Marine — sharks
    ("Megalodon",           "Megalodon",   "Miocene",    "Carnivore", "Massive", "Largest predatory shark, broad heavy body, massive triangular teeth",
     "fully aquatic, great white shark body plan scaled up, thick conical snout, dark eyes set wide, "
     "serrated triangular teeth each the size of a human hand, powerful crescent tail, "
     "heavy scarring on snout from prey, countershaded grey above white below", "marine"),
    ("Cretoxyrhina",        "Ginsu Shark", "Cretaceous", "Carnivore", "Large",   "Fast open-ocean predator shark, sleek and muscular",
     "fully aquatic, streamlined torpedo body, large dark eye, smooth skin, "
     "rows of blade-like teeth with no serrations, powerful tail fin, "
     "mako shark body plan, built for speed and ambush", "marine"),
    ("Helicoprion",         "Helicoprion", "Permian",    "Carnivore", "Large",   "Bizarre shark-relative with spiral tooth whorl in lower jaw",
     "fully aquatic, ratfish-like body, single spiral whorl of teeth curling under lower jaw like a circular saw, "
     "older smaller teeth at centre of spiral and newest largest teeth at outer edge, "
     "no upper teeth, smooth cartilaginous body, deep ocean dweller", "marine"),
    # Marine — fish
    ("Dunkleosteus",        "Dunkleosteus","Devonian",   "Carnivore", "Large",   "Armored predatory fish with bony head plates and guillotine jaw",
     "fully aquatic, massive bony head shield with interlocking plates, "
     "no true teeth but self-sharpening bony jaw blades, heavy armored front half, "
     "unarmored muscular rear half, broad flat head, small eyes set forward", "marine"),
    ("Xiphactinus",         "Bulldog Fish","Cretaceous", "Piscivore", "Large",   "Large predatory bony fish with upturned jaw and fangs",
     "fully aquatic, elongated torpedo body up to 6m, large upturned lower jaw with prominent fangs, "
     "bulldog-like underbite, forked tail, silvery scaled body, large pectoral fins", "marine"),
    ("Leedsichthys",        "Leedsichthys","Jurassic",   "Filter-feeder", "Massive", "Largest bony fish ever, whale-sized filter feeder",
     "fully aquatic, enormous body up to 16m, wide gaping mouth for filter feeding, "
     "gill rakers instead of teeth, broad paddle-like pectoral fins, "
     "dark mottled skin, whale shark-like feeding posture", "marine"),
    # Marine — other
    ("Archelon",            "Archelon",    "Cretaceous", "Omnivore",  "Large",   "Giant sea turtle with leathery shell and wide flippers",
     "fully aquatic, leathery skin-covered shell not hard scutes, "
     "massive front flippers for open-ocean swimming, hooked beak, "
     "shell up to 4m wide, barnacles and algae growing on shell, "
     "resembles oversized leatherback turtle", "marine"),
    ("Ammonite",            "Ammonite",    "Jurassic",   "Carnivore", "Medium",  "Spiral-shelled cephalopod with tentacles and iridescent shell",
     "fully aquatic, coiled chambered shell with ribbed surface, "
     "soft tentacles extending from shell opening, large intelligent eye, "
     "iridescent nacre sheen on shell surface, jet propulsion swimming, "
     "squid-like body inside shell, shell patterns vary — ridged and knobbed", "marine"),
    # Aerial species
    ("Quetzalcoatlus",      "Quetzal",     "Cretaceous", "Carnivore", "Massive", "Largest known flying animal, giraffe-sized pterosaur with enormous wingspan",
     "enormous wingspan, long stiff neck, toothless pointed beak, walked quadrupedally on ground, launched from all fours", "aerial"),
    ("Rhamphorhynchus",     "Rhampho",     "Jurassic",   "Piscivore", "Small",   "Long-tailed pterosaur with diamond-shaped tail vane and forward-pointing teeth",
     "long bony tail with diamond vane at tip, forward-pointing interlocking teeth for fish catching, compact body", "aerial"),
    ("Dimorphodon",         "Dimorphodon", "Jurassic",   "Piscivore", "Small",   "Early pterosaur with oversized head and deep puffin-like beak",
     "disproportionately large skull, deep narrow beak, short wings, long tail, compact body", "aerial"),
]

SEED_PARAMETERS = [
    # (category, name, value, weight, habitats)
    # "all" expanded to "terrestrial,marine,aerial" at insert time
    # Insertion order = display order (ORDER BY id)

    # ═══════════════════════════════════════════════════════════════════
    # STYLE (not user-selectable, kept for DB reference)
    # ═══════════════════════════════════════════════════════════════════
    ("style", "hyperrealism", (
        "hyperrealistic, anatomically accurate, living animal skin texture, "
        "subsurface scattering, 8K texture, shot on Canon EOS R5 400mm f/2.8, "
        "shallow depth of field, sharp anatomical detail, National Geographic wildlife photography, "
        "film grain, chromatic aberration, lens imperfection, real camera noise, "
        "not CGI, not rendered, not digital art, "
        "volumetric atmosphere, photojournalism composition"
    ), 1.2, "all"),

    # ═══════════════════════════════════════════════════════════════════
    # LIGHTING — 20 per habitat, soft → harsh → dramatic progression
    # ═══════════════════════════════════════════════════════════════════
    # Shared (T+M+A) — 8
    ("lighting", "dawn_first_light",   "first light before sunrise, deep blue sky warming at horizon, long faint shadows, cold ambient",                    1.0, "all"),
    ("lighting", "golden_hour",        "golden hour, warm low-angle sunlight, long shadows, lens flare",                                                    1.0, "all"),
    ("lighting", "overcast",           "overcast sky, soft diffused light, muted tones, flat natural light",                                                1.0, "all"),
    ("lighting", "broken_cloud",       "broken cloud cover, intermittent direct sun patches, uneven illumination, shifting shadow edges",                   1.0, "all"),
    ("lighting", "backlit_haze",       "animal backlit by diffuse haze, silhouette edges glowing, atmospheric scattering, low sun behind subject",          1.0, "all"),
    ("lighting", "blue_hour",          "blue hour twilight, cold flat ambient light, no direct sun, muted desaturated tones, horizon faintly lit",          1.0, "all"),
    ("lighting", "pre_storm",          "pre-storm greenish ambient light, heavy cloud ceiling, eerie flat illumination, no distinct shadows",               1.0, "all"),
    ("lighting", "stormy",             "storm light, dark cumulonimbus, dramatic rays through clouds",                                                      1.1, "all"),
    # Shared T+A — 2
    ("lighting", "sunset_warm",        "warm sunset light, orange-pink sky, long amber shadows, horizon glowing",                                           1.0, "terrestrial,aerial"),
    ("lighting", "dramatic_rim",       "strong rim lighting, deep shadows, high contrast",                                                                  1.1, "terrestrial,aerial"),
    # Terrestrial-only — 10
    ("lighting", "harsh_midday",       "harsh midday sun directly overhead, bleached highlights, hard shadows directly below, heat haze at horizon",        1.0, "terrestrial"),
    ("lighting", "dappled_canopy",     "dappled light through canopy gaps, moving light patches on skin, deep shadow between lit zones",                    1.0, "terrestrial"),
    ("lighting", "forest_floor_shade", "deep shade under dense canopy, minimal direct light, cool blue-green ambient, rare bright patches",                 1.0, "terrestrial"),
    ("lighting", "fog_diffuse",        "completely diffused in dense fog, no shadows, soft edges, grey-white ambient",                                      1.0, "terrestrial"),
    ("lighting", "dust_glow",          "particulate-filled air glowing in backlight, amber atmosphere, dust motes visible",                                 1.0, "terrestrial"),
    ("lighting", "shaft_light",        "single shaft of light through gap in canopy, rest in deep shadow, spotlight effect",                                1.0, "terrestrial"),
    ("lighting", "reflected_water",    "light bouncing off nearby water surface, rippled patterns on skin, wavering highlights",                            1.0, "terrestrial"),
    ("lighting", "twilight_fade",      "last moments before dark, deep blue-purple sky, barely visible, ambient only",                                      1.0, "terrestrial"),
    ("lighting", "moonlit",            "cool blue moonlight, deep long shadows, nocturnal, silver highlights on wet surfaces",                              1.0, "terrestrial"),
    ("lighting", "high_noon_flat",     "flat harsh noon light from directly above, minimal shadow definition, washed out",                                  1.0, "terrestrial"),
    # Marine-only — 12
    ("lighting", "underwater_caustics","sunlight filtering through water surface, shifting caustic patterns on skin, blue-green ambient light",             1.0, "marine"),
    ("lighting", "deep_water_fade",    "light fading with depth, animal lit from above, dark water below, natural light gradient",                          1.0, "marine"),
    ("lighting", "surface_dapple",     "rippling surface above casting moving light patterns, shifting bright patches on skin",                             1.0, "marine"),
    ("lighting", "bioluminescent",     "faint blue-green bioluminescence in surrounding water, self-lit particles, dark ambient",                           1.0, "marine"),
    ("lighting", "noon_column",        "strong vertical light column from midday sun above, bright cone in dark water",                                     1.0, "marine"),
    ("lighting", "reef_scatter",       "light scattered by coral and pale sand below, warm multicoloured reflections from beneath",                         1.0, "marine"),
    ("lighting", "murk_glow",          "diffuse glow in turbid water, scattered particles lit, low visibility, greenish cast",                              1.0, "marine"),
    ("lighting", "dawn_surface",       "warm dawn light hitting water surface above, amber colours penetrating shallows",                                   1.0, "marine"),
    ("lighting", "moonlit_surface",    "moonlight on calm surface above, silver-blue water, faint light reaching shallow depth",                            1.0, "marine"),
    ("lighting", "twilight_depth",     "last light of day barely reaching depth, deep blue-purple water, silhouette visibility only",                       1.0, "marine"),
    ("lighting", "storm_dark_above",   "dark stormy surface above, minimal light reaching water, greenish murky cast, turbulent",                           1.0, "marine"),
    ("lighting", "sun_shaft_angle",    "angled sun shafts cutting through water column, distinct bright beams in dark water",                               1.0, "marine"),
    # Aerial-only — 10
    ("lighting", "open_sky_flat",      "flat even sky light from all directions, no ground shadow, open atmospheric illumination",                          1.0, "aerial"),
    ("lighting", "cloud_shadow",       "flying through patches of cloud shadow and direct sun, flickering illumination",                                    1.0, "aerial"),
    ("lighting", "reflected_ground",   "light reflected up from bright terrain or water below, lit from beneath",                                           1.0, "aerial"),
    ("lighting", "halo_backlit",       "complete backlit halo around body, rim light on all edges, body dark, bright sky behind",                           1.0, "aerial"),
    ("lighting", "storm_flash",        "momentary lightning flash illuminating everything, brief harsh white light, frozen instant",                         1.0, "aerial"),
    ("lighting", "thermal_shimmer",    "heat distortion in air around animal, wavering light, rising warm air visible",                                     1.0, "aerial"),
    ("lighting", "fog_top_layer",      "flying above fog layer, bright above, white diffuse below, soft contrast",                                          1.0, "aerial"),
    ("lighting", "rain_scatter",       "light scattered through falling rain, grey even illumination, soft edges on everything",                            1.0, "aerial"),
    ("lighting", "altitude_clear",     "crystalline light at high altitude, deep blue sky, intense UV clarity, sharp hard shadows",                         1.0, "aerial"),
    ("lighting", "horizon_glow",       "warm horizon glow at animal's altitude, sky gradient from warm to cold, even side light",                           1.0, "aerial"),

    # ═══════════════════════════════════════════════════════════════════
    # CAMERA — 20 per habitat
    # ═══════════════════════════════════════════════════════════════════
    # Shared (T+M+A) — 6
    ("camera", "closeup_portrait",     "extreme close-up portrait, eye contact, shallow depth of field",                                                    1.0, "all"),
    ("camera", "medium_shot",          "medium shot, three-quarter view, natural pose",                                                                     1.0, "all"),
    ("camera", "tight_head",           "tight crop on head, eye fills upper third, skin detail razor sharp",                                                1.0, "all"),
    ("camera", "detail_abstract",      "extreme macro, single surface texture fills entire frame, abstracted",                                              1.0, "all"),
    ("camera", "full_body_profile",    "full body side profile, clean separation from background, field guide framing",                                     1.0, "all"),
    ("camera", "rear_three_quarter",   "rear three-quarter view, animal partially turned away, looking back over shoulder",                                 1.0, "all"),
    # Terrestrial-only — 14
    ("camera", "epic_wide",            "ultra-wide establishing shot, sweeping prehistoric landscape, animal small in frame",                               1.0, "terrestrial"),
    ("camera", "dynamic_low",          "dynamic low-angle action shot, motion blur, sense of speed",                                                        1.1, "terrestrial"),
    ("camera", "aerial_above",         "aerial bird's-eye view, vast scale, dorsal surface visible",                                                        1.0, "terrestrial"),
    ("camera", "ground_level_up",      "camera at ground, extreme upward angle, animal towers overhead",                                                    1.0, "terrestrial"),
    ("camera", "tracking_pan",         "panning tracking shot, subject sharp, background motion-blurred",                                                   1.0, "terrestrial"),
    ("camera", "hidden_blind",         "shot from hide or blind, vegetation framing edges, peering through, documentary",                                   1.0, "terrestrial"),
    ("camera", "telephoto_compress",   "extreme telephoto compression, flat perspective, bokeh dissolving background",                                      1.0, "terrestrial"),
    ("camera", "trail_camera",         "trail camera angle, low fixed position, infrared flash look, candid capture",                                       1.0, "terrestrial"),
    ("camera", "over_shoulder",        "camera behind and above animal, looking past it at habitat ahead",                                                  1.0, "terrestrial"),
    ("camera", "walking_toward",       "animal walking directly toward camera, head-on, growing larger in frame",                                           1.0, "terrestrial"),
    ("camera", "dust_level",           "camera at dust level, particles in foreground, animal through haze",                                                1.0, "terrestrial"),
    ("camera", "canopy_gap_down",      "shot from canopy looking down, animal on forest floor below, leaves framing",                                       1.0, "terrestrial"),
    ("camera", "waterhole_edge",       "camera at water's edge, reflection visible, animal approaching or drinking",                                        1.0, "terrestrial"),
    ("camera", "silhouette_ridge",     "animal on ridge line, silhouetted against sky, form dominant, no detail",                                           1.0, "terrestrial"),
    # Marine-only — 14
    ("camera", "underwater_wide",      "underwater wide-angle, dome port distortion, natural blue-green water colour",                                      1.0, "marine"),
    ("camera", "split_waterline",      "half-above half-below waterline, split frame, sky and ocean in one shot",                                           1.0, "marine"),
    ("camera", "below_looking_up",     "underwater camera looking up, animal silhouetted against bright surface",                                           1.0, "marine"),
    ("camera", "above_looking_down",   "aerial camera looking down into water, animal visible through surface refraction",                                  1.0, "marine"),
    ("camera", "swim_alongside",       "camera swimming alongside at eye level, parallel tracking, intimate distance",                                      1.0, "marine"),
    ("camera", "deep_telephoto",       "underwater telephoto, compressed depth, murky bokeh, subject emerging from dark",                                   1.0, "marine"),
    ("camera", "surface_skim",         "camera at water surface, half-submerged lens, water droplets on glass",                                             1.0, "marine"),
    ("camera", "jaw_level",            "camera at jaw level, mouth and teeth prominent, water around chin",                                                 1.0, "marine"),
    ("camera", "belly_underneath",     "camera directly below animal looking up, belly and flippers silhouetted against surface light",                     1.0, "marine"),
    ("camera", "reef_foreground",      "animal in mid-distance, coral or rock foreground framing, depth layered",                                           1.0, "marine"),
    ("camera", "chase_behind",         "camera behind swimming animal, tail and wake dominant, following pursuit",                                          1.0, "marine"),
    ("camera", "breach_freeze",        "frozen mid-breach, animal partially out of water, spray frozen, dramatic",                                          1.0, "marine"),
    ("camera", "murk_emerge",          "animal emerging from murky water into clearer zone, visibility transition",                                         1.0, "marine"),
    ("camera", "distant_surface",      "distant surface shot, animal small, vast ocean around, scale emphasis",                                             1.0, "marine"),
    # Aerial-only — 14
    ("camera", "flight_tracking",      "telephoto tracking shot, bird-in-flight photography, motion-sharp subject on blurred sky",                          1.0, "aerial"),
    ("camera", "below_up_wings",       "shot from below looking up, animal against open sky, wings fully spread",                                           1.0, "aerial"),
    ("camera", "above_down_dorsal",    "shot from above looking down, dorsal surface visible, ground far below",                                            1.0, "aerial"),
    ("camera", "parallel_flight",      "camera flying parallel, same altitude, wingtip-to-wingtip, intimate formation",                                    1.0, "aerial"),
    ("camera", "head_on_approach",     "animal flying directly toward camera, head and wings growing in frame",                                             1.0, "aerial"),
    ("camera", "banking_turn",         "animal in steep banking turn, one wing high, body angled, centrifugal",                                             1.0, "aerial"),
    ("camera", "distant_speck",        "tiny animal against vast sky, enormous scale, atmospheric perspective",                                             1.0, "aerial"),
    ("camera", "cliff_perch",          "perched on cliff edge, coastal or mountain backdrop, about to launch",                                              1.0, "aerial"),
    ("camera", "stoop_above",          "camera above diving animal looking down, ground rushing up below",                                                  1.0, "aerial"),
    ("camera", "wing_detail",          "extreme close-up of wing membrane in flight, bone structure visible, light through membrane",                       1.0, "aerial"),
    ("camera", "thermal_circle",       "animal circling in thermal, viewed from side, spiral path implied",                                                 1.0, "aerial"),
    ("camera", "sunrise_silhouette",   "animal silhouetted against sunrise, form only, no surface detail, dramatic sky",                                    1.0, "aerial"),
    ("camera", "cloud_frame",          "animal framed by cloud formations, sky architecture surrounding",                                                   1.0, "aerial"),
    ("camera", "landing_sequence",     "legs extending, wings braking, final approach to landing surface, action frozen",                                   1.0, "aerial"),

    # ═══════════════════════════════════════════════════════════════════
    # MOOD — 20 per habitat, calm → alert → intense progression
    # ═══════════════════════════════════════════════════════════════════
    # Shared (T+M+A) — 5
    ("mood", "quiet_power",          "animal simply existing, no drama, no spectacle, mundane moment caught on camera",                                     1.0, "all"),
    ("mood", "serene",               "calm resting moment, animal at ease, no awareness of camera, documentary stillness",                                  1.0, "all"),
    ("mood", "closed_mouth_resting", "closed mouth, natural resting behavior, no threat display",                                                           1.0, "all"),
    ("mood", "eye_contact",          "direct unblinking eye contact with camera, animal fully aware of lens, no threat display — just watching",            1.0, "all"),
    ("mood", "menacing",             "tense predatory stillness, locked gaze, not posing — caught mid-hunt by camera",                                      1.1, "all"),
    # Terrestrial-only — 15
    ("mood", "alert_scan",           "head raised mid-scan, ears and eyes forward, animal has detected something, body still, weight not yet shifted",      1.0, "terrestrial"),
    ("mood", "mid_stride",           "caught mid-step, one foot lifted, weight on rear leg, natural gait frozen by shutter, not posed",                     1.0, "terrestrial"),
    ("mood", "drinking",             "head lowered to water, tongue or lips at surface, body weight shifted forward, vulnerable posture",                   1.0, "terrestrial"),
    ("mood", "feeding_focus",        "head down, fully absorbed in eating, animal ignoring surroundings, documentary feeding behaviour",                    1.0, "terrestrial"),
    ("mood", "heat_rest",            "sprawled in shade, limbs loose, eyes half-closed, animal conserving energy in midday heat",                           1.0, "terrestrial"),
    ("mood", "territorial_hold",     "standing its ground, body angled sideways, not charging — holding position, weight evenly planted",                   1.0, "terrestrial"),
    ("mood", "post_kill_pause",      "standing over kill, not feeding yet, breathing heavy, blood on muzzle, staring into distance",                       1.0, "terrestrial"),
    ("mood", "scent_tracking",       "nose low to ground, mouth slightly open, jacobson organ active, slow deliberate movement",                           1.0, "terrestrial"),
    ("mood", "dust_bath",            "animal rolling or crouching in dry dirt, dust rising around body, eyes closed, instinctive behaviour",               1.0, "terrestrial"),
    ("mood", "wading_shallow",       "moving through shallow water, legs lifting high, body steady, water disturbed around feet",                          1.0, "terrestrial"),
    ("mood", "startled_freeze",      "caught mid-motion, body locked, eyes wide, instant before flight or fight decision",                                 1.0, "terrestrial"),
    ("mood", "grooming",             "head turned to flank, cleaning or preening, mundane self-maintenance moment",                                        1.0, "terrestrial"),
    ("mood", "herd_grazing",         "head down grazing among others, relaxed social feeding, no individual tension",                                      1.0, "terrestrial"),
    ("mood", "dawn_waking",          "just woken, body stiff, blinking, first movements of the day, limbs unfolding",                                      1.0, "terrestrial"),
    ("mood", "dusk_settling",        "settling into rest position as light fades, body lowering, eyes heavy, day ending",                                   1.0, "terrestrial"),
    # Marine-only — 15
    ("mood", "cruising_calm",        "gliding through open water with minimal effort, body relaxed, slow undulating movement",                              1.0, "marine"),
    ("mood", "surface_rest",         "floating motionless at water surface, body buoyant, eyes just above waterline, conserving energy",                    1.0, "marine"),
    ("mood", "deep_patrol",          "moving through dark water at depth, body streamlined, eyes forward, slow deliberate patrolling",                      1.0, "marine"),
    ("mood", "hunting_focus",        "locked onto prey below, body angled downward, jaw slightly open, committed pursuit",                                  1.0, "marine"),
    ("mood", "post_feed_drift",      "drifting after feeding, jaw slack, body heavy, blood wisps dissipating in water around mouth",                        1.0, "marine"),
    ("mood", "surfacing_breath",     "head breaking water surface, nostrils clearing water, exhale spray visible, momentary pause",                         1.0, "marine"),
    ("mood", "ambush_still",         "hovering motionless in water column, perfectly still, waiting for prey to approach",                                  1.0, "marine"),
    ("mood", "territorial_patrol",   "slow circuit of territory, body posture assertive, jaw slightly open, warning presence",                             1.0, "marine"),
    ("mood", "playful_roll",         "rolling at surface, belly flash, relaxed body language, no threat, exploratory",                                     1.0, "marine"),
    ("mood", "curiosity_approach",   "slowly approaching camera or unfamiliar object, cautious, head tilted, investigative",                               1.0, "marine"),
    ("mood", "resting_on_bottom",    "settled on ocean floor, body relaxed against sand or rock, eyes tracking lazily",                                    1.0, "marine"),
    ("mood", "burst_acceleration",   "explosive forward lunge, body fully extended, maximum speed, prey strike instant",                                   1.0, "marine"),
    ("mood", "kelp_weaving",         "threading slowly through kelp forest, body flexing, dappled light, exploratory calm",                                1.0, "marine"),
    ("mood", "dawn_ascent",          "rising from deep water toward brightening surface, body angled up, morning routine",                                 1.0, "marine"),
    ("mood", "dusk_descent",         "sinking into darker water as light fades, body relaxing, settling deeper for night",                                 1.0, "marine"),
    # Aerial-only — 15
    ("mood", "thermal_drift",        "wings locked, riding thermal updraft, effortless altitude, scanning below with slow head turns",                      1.0, "aerial"),
    ("mood", "wind_buffet",          "wings adjusting to turbulence, body angled against crosswind, fighting for stability",                                1.0, "aerial"),
    ("mood", "perched_alert",        "perched on cliff edge, wings folded, body upright, scanning horizon, about to launch",                                1.0, "aerial"),
    ("mood", "glide_descent",        "shallow descending glide, wings slightly swept back, losing altitude gradually",                                      1.0, "aerial"),
    ("mood", "hunting_scan",         "circling above territory, head angled down, scanning ground or water for prey",                                      1.0, "aerial"),
    ("mood", "territorial_display",  "wings spread wide in mid-air, body puffed, aggressive posture toward rival",                                         1.0, "aerial"),
    ("mood", "effortless_cruise",    "level flight, wings barely moving, body perfectly streamlined, long-distance travel",                                 1.0, "aerial"),
    ("mood", "startled_flare",       "sudden wing flare, body jerking, reacting to unexpected threat or gust",                                             1.0, "aerial"),
    ("mood", "feeding_return",       "returning from successful hunt, prey in beak or talons, purposeful flight toward nest",                              1.0, "aerial"),
    ("mood", "dawn_launch",          "launching from perch at first light, wings opening, initial drop before lift",                                       1.0, "aerial"),
    ("mood", "dusk_roost_approach",  "approaching roosting cliff as light fades, decelerating, legs extending",                                            1.0, "aerial"),
    ("mood", "playful_tumble",       "mid-air tumble or roll, wings tucked briefly, acrobatic, non-threatening",                                           1.0, "aerial"),
    ("mood", "exhausted_glide",      "wings held stiff, barely adjusting, body heavy, long flight fatigue visible",                                        1.0, "aerial"),
    ("mood", "rain_endurance",       "flying through rain, wings heavy with water, head tucked, dogged persistence",                                       1.0, "aerial"),
    ("mood", "juvenile_clumsy",      "young animal in awkward flight, wings not fully coordinated, wobbling, learning",                                    1.0, "aerial"),

    # ═══════════════════════════════════════════════════════════════════
    # BEHAVIOR — 20 per habitat, passive → active → intense progression
    # ═══════════════════════════════════════════════════════════════════
    # Terrestrial — 20
    ("behavior", "standing_still",       "standing motionless, weight evenly distributed, head level, completely still, at rest",                            1.0, "terrestrial"),
    ("behavior", "scanning_territory",   "head raised, body still, eyes on middle distance, nostrils flared, territorial survey",                           1.0, "terrestrial"),
    ("behavior", "mid_stride",           "mid-stride, one foot raised, weight shifting forward, muscles tensed, tail counterbalancing",                     1.0, "terrestrial"),
    ("behavior", "feeding",              "head lowered, actively feeding, neck extended, jaw working, natural feeding posture",                              1.0, "terrestrial"),
    ("behavior", "resting_alert",        "body lowered, eyes open and tracking, head slightly raised, coiled readiness beneath calm",                       1.0, "terrestrial"),
    ("behavior", "drinking_at_water",    "head lowered to water, neck extended, nose above still water, body weight forward",                               1.0, "terrestrial"),
    ("behavior", "basking_flat",         "belly flat against sun-warmed rock or ground, legs splayed, eyes half-closed, absorbing heat",                    1.0, "terrestrial"),
    ("behavior", "emerging_from_cover",  "emerging from dense vegetation, half-visible, one side in shadow, eyes locked forward",                           1.0, "terrestrial"),
    ("behavior", "post_rain_stillness",  "standing after rain, skin glistening, steam rising from hide, puddles at feet",                                   1.0, "terrestrial"),
    ("behavior", "shaking_off_water",    "violent full-body shake, water droplets exploding outward, head whipping, kinetic blur",                          1.0, "terrestrial"),
    ("behavior", "threat_display",       "broadside threat display, body maximised for size, head lowered, crest extended, dominant stance",                1.0, "terrestrial"),
    ("behavior", "freeze_detect",        "frozen mid-step, one foot still raised, head locked toward unseen threat, not breathing visibly",                 1.0, "terrestrial"),
    ("behavior", "jaw_clean_on_ground",  "dragging lower jaw across ground after feeding, scraping residue on dirt and rock, deliberate",                   1.0, "terrestrial"),
    ("behavior", "mud_wallow",           "lying on side in shallow mud, one foreleg pushing, coating flank, eye just above mud line",                       1.0, "terrestrial"),
    ("behavior", "carcass_standing",     "standing directly over fresh kill, not yet feeding, head hanging, flanks heaving",                                1.0, "terrestrial"),
    ("behavior", "dust_rolling",         "rolling on dry ground, dust cloud rising, legs kicking, coating hide in dust",                                    1.0, "terrestrial"),
    ("behavior", "head_butt_spar",       "head lowered, pushing against rival or tree, neck muscles bulging, power contest",                               1.0, "terrestrial"),
    ("behavior", "tail_swipe",           "tail mid-swing, defensive or aggressive sweep, body pivoting, kinetic force",                                    1.0, "terrestrial"),
    ("behavior", "nesting_tend",         "near nest or eggs, body lowered protectively, head turning watchfully, parental",                                 1.0, "terrestrial"),
    ("behavior", "charging_full",        "full charge forward, head down, legs driving, dust exploding from feet, committed",                              1.0, "terrestrial"),
    # Marine — 20
    ("behavior", "cruising_open_water",  "level cruise through open water, streamlined posture, bow wave at snout, effortless power",                       1.0, "marine"),
    ("behavior", "hovering_still",       "suspended motionless in water column, fins making micro-adjustments, neutrally buoyant",                         1.0, "marine"),
    ("behavior", "slow_patrol",          "slow deliberate swimming, body undulating gently, surveying territory at depth",                                  1.0, "marine"),
    ("behavior", "surface_breathing",    "rising to surface, snout breaking water, exhale spray visible, quick gulp of air",                               1.0, "marine"),
    ("behavior", "bottom_glide",         "gliding just above ocean floor, belly close to sand, stirring sediment, hunting by ambush",                       1.0, "marine"),
    ("behavior", "kelp_threading",       "weaving through underwater vegetation, body flexing between fronds, dappled light from above",                   1.0, "marine"),
    ("behavior", "tail_propulsion",      "powerful tail stroke mid-swim, body flexing in S-curve, water displaced behind, muscular effort",                 1.0, "marine"),
    ("behavior", "surface_roll",         "rolling at water surface, one flipper breaking surface, belly briefly visible, slow barrel roll",                  1.0, "marine"),
    ("behavior", "feeding_underwater",   "jaw working on prey, fragments drifting, body braced, feeding frenzy energy or slow methodical tearing",         1.0, "marine"),
    ("behavior", "breaching_surface",    "explosive breach through water surface, cascading foam, massive spray catching light, peak arc",                  1.0, "marine"),
    ("behavior", "hunting_dive",         "banking steeply downward, body on attack vector, dark water deepening, prey at depth",                            1.0, "marine"),
    ("behavior", "jaw_snap_strike",      "jaw open wide in mid-strike, teeth exposed, water distortion around head, explosive acceleration",                1.0, "marine"),
    ("behavior", "chase_pursuit",        "full speed pursuit, body fully extended, tail driving, wake turbulence behind",                                   1.0, "marine"),
    ("behavior", "resting_on_seafloor",  "settled on ocean floor, body draped over rocks or sand, minimal movement, resting",                              1.0, "marine"),
    ("behavior", "spy_hopping",          "head raised vertically above surface, looking around, body hanging below waterline",                             1.0, "marine"),
    ("behavior", "flipper_steering",     "one flipper extended turning sharply, body banking, precise course correction",                                   1.0, "marine"),
    ("behavior", "debris_rubbing",       "rubbing body against rock or coral, scraping parasites, slow deliberate contact",                                1.0, "marine"),
    ("behavior", "bubble_trail",         "exhaling underwater, stream of bubbles rising from nostrils, body moving through own bubble trail",               1.0, "marine"),
    ("behavior", "deep_sinking",         "sinking passively into darker water, body relaxing, descending into depth",                                      1.0, "marine"),
    ("behavior", "current_riding",       "body angled into ocean current, using flow to hold position, minimal effort, natural drift",                     1.0, "marine"),
    # Aerial — 20
    ("behavior", "thermal_soaring",      "wings at full span, banking on thermal, wingtips curled, scanning territory below",                               1.0, "aerial"),
    ("behavior", "level_cruise",         "steady level flight, wings in efficient cruising position, slight adjustments, long-distance travel",             1.0, "aerial"),
    ("behavior", "updraft_hover",        "near-stationary in strong updraft, wings spread wide, body tilted into wind, minimal flapping",                   1.0, "aerial"),
    ("behavior", "glide_coast",          "wings held rigid, no flapping, slowly losing altitude, conserving energy",                                        1.0, "aerial"),
    ("behavior", "cliff_launch",         "pushing off cliff edge, wings snapping open, initial drop before first wingbeat, gravity to lift transition",     1.0, "aerial"),
    ("behavior", "landing_approach",     "wings spread in braking arc, legs forward, deceleration, final seconds before touchdown",                         1.0, "aerial"),
    ("behavior", "fish_snatch",          "skimming water surface, lower jaw dipping in, snatching fish mid-flight, spray from jaw contact",                 1.0, "aerial"),
    ("behavior", "diving_strike",        "wings folded, near-vertical power dive, target below, extreme velocity, committed strike",                        1.0, "aerial"),
    ("behavior", "banking_turn",         "steep banking turn, one wing high one low, body tilted, changing direction",                                      1.0, "aerial"),
    ("behavior", "flapping_climb",       "powerful wingbeats gaining altitude, body angled upward, muscular effort visible in chest",                       1.0, "aerial"),
    ("behavior", "wind_correction",      "wings adjusting to sudden gust, body tilting, compensating, maintaining course",                                  1.0, "aerial"),
    ("behavior", "aerial_display",       "acrobatic mid-air display, loops or rolls, territorial or courtship flight",                                     1.0, "aerial"),
    ("behavior", "prey_carry",           "flying with prey in beak or feet, body heavier, flight laboured, purposeful heading",                            1.0, "aerial"),
    ("behavior", "cliff_perching",       "perched on cliff face, wings folded tight, claws gripping rock, body compact, watching",                         1.0, "aerial"),
    ("behavior", "preening_perched",     "perched, head turned to wing, beak working through feathers or pycnofibres, grooming",                           1.0, "aerial"),
    ("behavior", "rival_chase",          "pursuing another pterosaur, aggressive posture, beak open, territorial conflict in air",                          1.0, "aerial"),
    ("behavior", "headwind_struggle",    "pushing into strong headwind, wings fully extended, barely making progress, effort visible",                      1.0, "aerial"),
    ("behavior", "wake_turbulence",      "flying through turbulent air behind cliff or another animal, body buffeted, adjusting",                           1.0, "aerial"),
    ("behavior", "morning_stretch",      "perched, wings extending one at a time, stretching before first flight, loosening joints",                       1.0, "aerial"),
    ("behavior", "tandem_flight",        "flying alongside another of same species, matched speed, social flight, formation",                              1.0, "aerial"),

    # ═══════════════════════════════════════════════════════════════════
    # CONDITION — 20 per habitat, pristine → weathered → damaged
    # ═══════════════════════════════════════════════════════════════════
    # Shared (T+M+A) — 6
    ("condition", "pristine_juvenile",   "pristine unblemished skin, smooth scales, bright alert eyes, full feathers where applicable",                     1.0, "all"),
    ("condition", "dominant_prime",      "peak condition adult, full muscle mass, no visible injury, glossy hide, clear eyes",                              1.0, "all"),
    ("condition", "weathered_adult",     "weathered hide, healed scratches on flanks, thickened skin at joints, subtle asymmetry",                          1.0, "all"),
    ("condition", "elder_specimen",      "elder, deep wrinkles at eye and jaw, worn teeth, clouded iris, thickened scarred skin",                            1.0, "all"),
    ("condition", "lean_season",         "ribs just visible through skin on flanks, hip bones prominent, lean condition, conserving energy",                1.0, "all"),
    ("condition", "battle_scarred",      "healed bite scars on neck, claw marks on ribcage, torn eyelid, powerful survivor",                                1.0, "all"),
    # Shared T+M — 2
    ("condition", "blood_on_muzzle",     "fresh blood staining around mouth and lower jaw, wet and dark, recent feed",                                     1.0, "terrestrial,marine"),
    ("condition", "moulting_skin",       "patches of old skin lifting at joints and along flanks, new scale layer beneath, flaking edges",                  1.0, "terrestrial,marine"),
    # Terrestrial-only — 12
    ("condition", "mud_caked",           "thick dried mud caked on legs and underbelly, wet mud still fresh on feet, hide streaked",                         1.0, "terrestrial"),
    ("condition", "wet_after_rain",      "hide visibly wet, water beading on scales, dark wet patches drying unevenly across body",                        1.0, "terrestrial"),
    ("condition", "parasite_ticks",      "clusters of ticks behind jaw and in skin folds, animal unbothered, naturalistic parasite load",                   1.0, "terrestrial"),
    ("condition", "fly_attention",       "several flies resting on eye corners and nostril edges, animal unbothered, field photography detail",             1.0, "terrestrial"),
    ("condition", "missing_toe",         "one toe absent at second joint, healed clean stump with thickened keratin, old injury recovered",                 1.0, "terrestrial"),
    ("condition", "split_claw",          "primary claw split lengthwise from tip to base, crack packed with dried mud, still functional",                   1.0, "terrestrial"),
    ("condition", "broken_horn_tip",     "horn or crest tip snapped off mid-shaft, break point weathered smooth, bone core exposed, healed years ago",     1.0, "terrestrial"),
    ("condition", "patchy_hide",         "irregular bare patches on neck and shoulder where scales shed and not regrown, raw pink underlayer",              1.0, "terrestrial"),
    ("condition", "eye_wound",           "milky scar tissue across left eye cornea, iris visible beneath, old puncture wound healed",                       1.0, "terrestrial"),
    ("condition", "jaw_asymmetry",       "lower jaw off-centre from healed fracture, one tooth row misaligned, bite still functional",                      1.0, "terrestrial"),
    ("condition", "embedded_tooth",      "foreign tooth fragment lodged in jaw muscle, skin grown partially over it, faint raised lump",                    1.0, "terrestrial"),
    ("condition", "neck_scar_collar",    "ring of healed bite scars encircling base of neck, skin thickened and puckered at scar line",                     1.0, "terrestrial"),
    # Marine-only — 12
    ("condition", "algae_on_hide",       "faint green algae growth on dorsal scales and tail, uneven coverage with bare patches",                           1.0, "marine"),
    ("condition", "barnacle_growth",     "clusters of barnacles encrusted on lower jaw, flipper edges, and tail base, long-term marine residency",          1.0, "marine"),
    ("condition", "shark_bite_scar",     "crescent-shaped healed bite scar on flank, consistent with large shark attack, tissue raised and pale",           1.0, "marine"),
    ("condition", "salt_crust",          "dried salt crystals on skin above waterline, white mineral deposits in skin folds, sun-dried",                    1.0, "marine"),
    ("condition", "fishing_line_scar",   "thin linear scar around flipper base, healed entanglement mark, skin thinned along line",                        1.0, "marine"),
    ("condition", "remora_attached",     "small remora fish attached to belly, symbiotic passenger, animal unbothered",                                    1.0, "marine"),
    ("condition", "coral_scrape",        "long shallow scrape along flank from coral contact, raw but not bleeding, recent",                               1.0, "marine"),
    ("condition", "waterlogged_pale",    "skin pale and waterlogged from extended deep dive, colour returning as blood flows surface",                      1.0, "marine"),
    ("condition", "tooth_missing_jaw",   "gap in tooth row where tooth was lost, gum healed over, neighbouring teeth slightly shifted",                    1.0, "marine"),
    ("condition", "flipper_notch",       "v-shaped notch missing from trailing edge of flipper, healed smooth, old injury",                                1.0, "marine"),
    ("condition", "eye_clouded",         "one eye clouded with parasitic infection, functional but visibly opaque, unbothered",                             1.0, "marine"),
    ("condition", "belly_scars",         "network of old scrape scars on belly from seafloor contact, healed flat and pale",                               1.0, "marine"),
    # Aerial-only — 12
    ("condition", "torn_membrane",       "small tear in wing membrane near trailing edge, edges healed to thin scar tissue, flight functional",            1.0, "aerial"),
    ("condition", "wind_worn_crest",     "head crest tip worn and chipped from wind exposure, surface roughened, keratin peeling at edges",                 1.0, "aerial"),
    ("condition", "missing_pycnofibres", "bare patches on forearm where pycnofibres lost, raw skin visible, partial regrowth at edges",                    1.0, "aerial"),
    ("condition", "beak_chip",           "beak tip chipped or cracked, keratin split visible, still functional, natural wear",                             1.0, "aerial"),
    ("condition", "talon_worn",          "foot talons worn blunt from rock perching, keratin tips rounded, grip still strong",                              1.0, "aerial"),
    ("condition", "membrane_patch",      "healed patch in wing membrane, thinner translucent area where tear mended, slightly uneven surface",             1.0, "aerial"),
    ("condition", "sun_bleached",        "dorsal scales or pycnofibres bleached lighter by UV exposure, ventral side darker in contrast",                   1.0, "aerial"),
    ("condition", "insect_bitten",       "small welts and bumps around eyes and nostrils from insect bites, minor irritation visible",                     1.0, "aerial"),
    ("condition", "salt_spray_residue",  "fine white salt residue on wing membranes and body from coastal flying, dried mineral film",                      1.0, "aerial"),
    ("condition", "feather_molt",        "pycnofibres moulting in patches, old and new growth visible simultaneously, seasonal transition",                1.0, "aerial"),
    ("condition", "wing_joint_swollen",  "one wing joint slightly swollen, range of motion reduced, compensating with other wing, old strain",             1.0, "aerial"),
    ("condition", "fish_oil_stain",      "oily iridescent stain around beak and throat from recent fish meal, scales glistening with fish oil",            1.0, "aerial"),
    ("condition", "claw_overgrown",      "rear talons slightly overgrown and curving inward, keratin splitting at tips from age",                           1.0, "aerial"),
    ("condition", "dust_coated",         "fine airborne dust settled across wing membranes and crest, grey film dulling natural coloration",                 1.0, "aerial"),

    # ═══════════════════════════════════════════════════════════════════
    # WEATHER — 20 per habitat (filtered by lighting compatibility)
    # ═══════════════════════════════════════════════════════════════════
    # Terrestrial — 20
    ("weather", "clear_pristine",       "cloudless sky, hard directional light, crisp shadows, fully saturated colours",                                    1.0, "terrestrial"),
    ("weather", "heat_haze",            "intense heat, air shimmer from baked ground, bleached sky, dust rising from every footfall",                        1.0, "terrestrial"),
    ("weather", "hot_still_air",        "dead still air, no wind, oppressive heat, everything motionless, heavy atmosphere",                                1.0, "terrestrial"),
    ("weather", "humid_haze",           "thick humid haze, reduced visibility, moisture on every surface, tropical heaviness",                              1.0, "terrestrial"),
    ("weather", "ground_mist",          "dense ground mist at knee height, legs dissolved in fog, body floating above mist",                                1.0, "terrestrial"),
    ("weather", "cold_fog",             "dense cold fog, visibility under 20 metres, everything muffled, grey-white void",                                  1.0, "terrestrial"),
    ("weather", "frost_dawn",           "frost on every surface, breath visible, ground white and crunching, cold clear air",                               1.0, "terrestrial"),
    ("weather", "overcast_flat",        "thick flat overcast, no sun, grey even light, no shadows, muted colours everywhere",                               1.0, "terrestrial"),
    ("weather", "drizzle_steady",       "steady light drizzle, surfaces wet and reflecting, grey sky, fine water in air",                                   1.0, "terrestrial"),
    ("weather", "rain_clearing",        "rain just stopping, last drops falling, clouds breaking, wet surfaces catching first sun",                         1.0, "terrestrial"),
    ("weather", "wind_gusts_dry",       "strong dry wind gusts, vegetation bending, dust lifting, animal braced against wind",                              1.0, "terrestrial"),
    ("weather", "dust_storm",           "airborne dust reducing visibility, amber-brown atmosphere, grit on every surface",                                 1.0, "terrestrial"),
    ("weather", "storm_approaching",    "cumulonimbus wall on horizon, sky bruised green-grey, eerie stillness, air charged",                               1.0, "terrestrial"),
    ("weather", "monsoon_heavy",        "heavy driving rain, diagonal streaks across frame, surfaces glistening, steam from warm hide",                     1.0, "terrestrial"),
    ("weather", "light_snowfall",       "light snow falling, snowflakes on scales, breath condensation visible, muted blue-white palette",                  1.0, "terrestrial"),
    ("weather", "arctic_freeze",        "extreme cold, frost on scales, breath condensation heavy, ice at eyelid edges, blue-white light",                  1.0, "terrestrial"),
    ("weather", "volcanic_ash_fall",    "volcanic ash drifting down, sulphurous yellow-grey atmosphere, sun a pale disc, ash on scales",                    1.0, "terrestrial"),
    ("weather", "wildfire_smoke",       "wildfire smoke, sun an ember-orange disc, ash drifting, deep orange and amber light",                              1.0, "terrestrial"),
    ("weather", "late_afternoon_cool",  "temperature dropping, shadows lengthening, cool air settling, calm before dusk",                                   1.0, "terrestrial"),
    ("weather", "post_storm_clearing",  "storm just passed, broken cloud, shafts of sunlight, glistening surfaces, steam from ground",                     1.0, "terrestrial"),
    # Marine — 20
    ("weather", "calm_surface",         "glassy calm water surface, mirror reflections, no wind, deep colour saturation",                                   1.0, "marine"),
    ("weather", "clear_tropical",       "crystal clear tropical water, high visibility, turquoise blue, sunlight penetrating deep",                         1.0, "marine"),
    ("weather", "warm_shallows",        "warm shallow water, sandy bottom visible, gentle light, comfortable temperature",                                  1.0, "marine"),
    ("weather", "dawn_glass",           "dawn light on perfectly still water, pink and gold reflections, no ripple",                                        1.0, "marine"),
    ("weather", "kelp_drift",           "lazy kelp fronds drifting in gentle current, dappled green light, sheltered water",                                1.0, "marine"),
    ("weather", "reef_current",         "moderate current flowing over reef, fish in background, colourful substrate, clear water",                         1.0, "marine"),
    ("weather", "surface_chop",         "moderate surface chop from wind, whitecaps, uneven light below, turbulent upper layer",                            1.0, "marine"),
    ("weather", "choppy_swell",         "moderate ocean swell, whitecaps, spray in wind, grey-green water, overcast sky reflected",                         1.0, "marine"),
    ("weather", "murky_green",          "murky green water, low visibility, particulate matter suspended, diffuse light from above",                         1.0, "marine"),
    ("weather", "underwater_haze",      "underwater haze reducing visibility, particles in water column, diffuse ambient light",                            1.0, "marine"),
    ("weather", "plankton_bloom",       "dense plankton bloom in water, green-brown tint, reduced visibility, organic particles everywhere",                1.0, "marine"),
    ("weather", "twilight_surface",     "twilight sky reflected on water surface, deep blue-purple water, fading light at depth",                           1.0, "marine"),
    ("weather", "moonlit_calm",         "moonlight on calm water surface, silver reflections, dark water below, nocturnal",                                 1.0, "marine"),
    ("weather", "tidal_surge",          "strong tidal current, water rushing, sediment stirred, animal bracing against flow",                               1.0, "marine"),
    ("weather", "rain_on_surface",      "rain hitting water surface above, ring patterns, fresh water mixing with salt, diffuse light",                     1.0, "marine"),
    ("weather", "ocean_storm",          "heavy ocean storm, dark water, driving spray, massive swells, violent surface above",                               1.0, "marine"),
    ("weather", "storm_surge_murk",     "storm-churned water, zero visibility, sediment and debris, chaotic current",                                       1.0, "marine"),
    ("weather", "thermocline_shift",    "visible temperature boundary in water, shimmer at thermocline, clear above, murky below",                          1.0, "marine"),
    ("weather", "deep_current_cold",    "deep cold current, dark water, slow-moving dense flow, pressure and cold palpable",                                1.0, "marine"),
    ("weather", "volcanic_vent_warm",   "warm water rising from volcanic vent below, mineral-rich shimmer, otherworldly glow",                              1.0, "marine"),
    # Aerial — 20
    ("weather", "high_altitude_clear",  "clear sky at altitude, deep blue above, haze layer below, crisp air, long-distance visibility",                    1.0, "aerial"),
    ("weather", "dawn_horizon",         "dawn colours at altitude, warm horizon, cold sky above, still air, quiet",                                         1.0, "aerial"),
    ("weather", "sunset_altitude",      "sunset colours surrounding animal at altitude, orange-pink clouds, warm light everywhere",                         1.0, "aerial"),
    ("weather", "thermal_column",       "rising thermal air visible as heat shimmer, cumulus cloud forming above, updraft energy",                           1.0, "aerial"),
    ("weather", "calm_dead_air",        "completely calm air, no thermals, no wind, flat atmospheric conditions, still flight",                              1.0, "aerial"),
    ("weather", "coastal_wind",         "strong coastal wind, salt spray in air, wind-sculpted clouds, bright harsh light",                                  1.0, "aerial"),
    ("weather", "tailwind_fast",        "strong tailwind, ground rushing below, accelerated flight, cloud streaks",                                         1.0, "aerial"),
    ("weather", "headwind_strong",      "powerful headwind, animal barely making progress, wings fully extended, turbulent",                                 1.0, "aerial"),
    ("weather", "crosswind_shear",      "wind shear from side, body tilting to compensate, uneven air, challenging flight",                                 1.0, "aerial"),
    ("weather", "cloud_layer_below",    "flying above cloud layer, white cloud carpet below, bright sun above, dramatic depth",                             1.0, "aerial"),
    ("weather", "haze_layer",           "flying through or above haze layer, reduced visibility, muted colours, soft edges",                                1.0, "aerial"),
    ("weather", "fog_bank_below",       "dense fog bank below, animal flying above, islands of terrain poking through",                                     1.0, "aerial"),
    ("weather", "updraft_turbulence",   "turbulent updraft air, animal bouncing, wings constantly adjusting, unstable flight",                              1.0, "aerial"),
    ("weather", "mountain_wave",        "mountain wave turbulence, rhythmic rise and fall, lenticular clouds forming",                                      1.0, "aerial"),
    ("weather", "rain_curtain",         "rain curtain ahead or below, animal flying above or through, wet wings, grey veil",                                1.0, "aerial"),
    ("weather", "ice_crystal_air",      "ice crystals in air at altitude, sparkling in sunlight, cold sharp atmosphere",                                    1.0, "aerial"),
    ("weather", "storm_anvil_top",      "near top of storm cell, anvil cloud spreading, dark below, bright above, dangerous air",                           1.0, "aerial"),
    ("weather", "sea_spray_altitude",   "salt spray carried to altitude by coastal updraft, mist in air, maritime atmosphere",                              1.0, "aerial"),
    ("weather", "dust_plume_below",     "dust plume rising from dry terrain below, brown haze at lower altitude, clear above",                              1.0, "aerial"),
    ("weather", "clear_cold_high",      "extremely clear cold air at high altitude, crystalline visibility, deep blue sky, sharp light",                    1.0, "aerial"),

    # ═══════════════════════════════════════════════════════════════════
    # ANATOMY — species-level body accuracy requirements
    # ═══════════════════════════════════════════════════════════════════
    ("anatomy", "full_body_accuracy", (
        "full body visible including hands and feet, pronated wrists corrected, "
        "hands in neutral position with palms facing inward, sickle claw raised off ground, "
        "correct theropod hand anatomy, fingers not splayed, wrist not bent downward"
    ), 1.2, "terrestrial"),
]

# Skin texture corrections for species whose skin_texture_type was seeded outside
# migrate_scientific.py and still contained fossil/specimen language.
# Applied as UPDATEs during seeding so they override any stale DB values.
SEED_SKIN_CORRECTIONS = {
    "Allosaurus fragilis":             "rough pebbly scales across neck and back, crocodilian-textured hide",
    "Argentinosaurus huinculensis":    "rough armoured skin plates covering body, textured titanosaur hide",
    "Carnotaurus sastrei":             "oval pebbly scales across body, rows of larger conical raised bumps along flanks",
    "Pachycephalosaurus wyomingensis": "smooth scales across body, rows of spiky knobs framing the domed skull",
    "Therizinosaurus cheloniformis":   "feathering probable, dense feather coat across body, quill bases at skin surface",
}

# Species-specific required parameters: (species_name, parameter_name)
SEED_SPECIES_PARAMETERS = [
    ("Velociraptor", "full_body_accuracy"),
]

NEGATIVE_PROMPT = (
    "cartoon, stylized, Jurassic Park inaccurate, shrink-wrapped anatomy, "
    "kangaroo posture, tail dragging, pronated wrists, scaly lizard skin on feathered species, "
    "blurry, watermark, text, toy, anime, "
    "fossil, fossilized, skeleton, skeletal, bones, excavation, petrified, "
    "museum display, museum specimen, natural history exhibit, specimen mount, "
    "display case, diorama, specimen photography, rock matrix, sediment, mineralized, "
    "osteoderms, osteoderm"
)

SEED_GLOBAL_RULES = [
    ("accuracy", "correct posture and locomotion",        "Enforces horizontal spine, erect gait, proper tail carriage"),
    ("accuracy", "living animal in natural habitat",      "Animal rendered as a wild creature, not a specimen or reconstruction"),
    ("accuracy", "accurate period-correct flora",         "Vegetation matches geological period, no anachronistic plants"),
    ("accuracy", "wildlife documentary realism",          "Framed as wildlife nature photography, not museum or concept art"),
]

SEED_PROMPTS = [
    {
        "species": "Tyrannosaurus rex",
        "title": "T. rex at sunrise",
        "positive": (
            "A Tyrannosaurus rex standing on a rocky bluff at sunrise, "
            "silhouetted against an orange sky, feathers visible on arms, "
            "living animal, dramatic scale"
        ),
        "negative": "cartoon, anime, toy, blurry, watermark, text",
        "tags": "sunrise,silhouette,feathered",
    },
    {
        "species": "Velociraptor",
        "title": "Raptor pack hunt",
        "positive": (
            "Two Velociraptors with full feather plumage hunting in a fern-covered "
            "Cretaceous forest, dappled light through tree canopy, anatomically correct living animals"
        ),
        "negative": "scaly skin only, cartoon, Jurassic Park inaccurate",
        "tags": "pack,hunting,feathered,forest",
    },
    {
        "species": "Brachiosaurus",
        "title": "Brachiosaurus herd at river",
        "positive": (
            "A herd of Brachiosaurus wading through a wide Jurassic river, "
            "lush vegetation, misty mountains in background, golden afternoon light"
        ),
        "negative": "cartoon, modern trees, humans, blurry",
        "tags": "herd,river,landscape",
    },
]


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

def create_schema(conn: sqlite3.Connection) -> None:
    sql = SCHEMA_FILE.read_text()
    conn.executescript(sql)
    print(f"  Schema applied from {SCHEMA_FILE.name}")


def seed_data(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.executemany(
        """INSERT OR IGNORE INTO species
           (name, common_name, period, diet, size_class, description, notes, habitat)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        SEED_SPECIES,
    )
    print(f"  Seeded {cur.rowcount} species rows")

    # Expand "all" shorthand to full habitat list before inserting
    expanded_params = []
    for p in SEED_PARAMETERS:
        row = list(p)
        if row[4] == "all":
            row[4] = "terrestrial,marine,aerial"
        expanded_params.append(tuple(row))

    cur.executemany(
        """INSERT OR IGNORE INTO parameters
           (category, name, value, weight, habitats)
           VALUES (?, ?, ?, ?, ?)""",
        expanded_params,
    )
    print(f"  Seeded {cur.rowcount} parameter rows")

    for p in SEED_PROMPTS:
        species_id = cur.execute(
            "SELECT id FROM species WHERE name = ?", (p["species"],)
        ).fetchone()
        species_id = species_id[0] if species_id else None

        cur.execute(
            """INSERT INTO prompts
               (species_id, title, positive_prompt, negative_prompt, tags)
               VALUES (?, ?, ?, ?, ?)""",
            (species_id, p["title"], p["positive"], NEGATIVE_PROMPT, p["tags"]),
        )
    print(f"  Seeded {len(SEED_PROMPTS)} prompt rows")

    cur.executemany(
        "INSERT OR IGNORE INTO global_rules (category, rule, description) VALUES (?, ?, ?)",
        SEED_GLOBAL_RULES,
    )
    print(f"  Seeded {len(SEED_GLOBAL_RULES)} global_rules rows")

    for species_name, param_name in SEED_SPECIES_PARAMETERS:
        sid = cur.execute("SELECT id FROM species WHERE name=?", (species_name,)).fetchone()
        pid = cur.execute("SELECT id FROM parameters WHERE name=?", (param_name,)).fetchone()
        if sid and pid:
            cur.execute(
                "INSERT OR IGNORE INTO species_parameters (species_id, parameter_id, required) VALUES (?,?,1)",
                (sid[0], pid[0]),
            )
    print(f"  Seeded {len(SEED_SPECIES_PARAMETERS)} species_parameters rows")

    for species_name, skin_texture in SEED_SKIN_CORRECTIONS.items():
        cur.execute(
            "UPDATE species SET skin_texture_type = ? WHERE name = ?",
            (skin_texture, species_name),
        )
    print(f"  Applied {len(SEED_SKIN_CORRECTIONS)} skin texture corrections")

    conn.commit()


def setup(db_path: Path, seed: bool = True) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Opening database: {db_path}")

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")

        print("Applying schema...")
        create_schema(conn)

        if seed:
            print("Seeding initial data...")
            seed_data(conn)

    print(f"\nDone. Database ready at: {db_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Set up the dino art prompt DB")
    parser.add_argument("--db", type=Path, default=DB_DEFAULT, metavar="PATH",
                        help="SQLite database file path")
    parser.add_argument("--no-seed", action="store_true",
                        help="Skip seeding initial data")
    args = parser.parse_args()

    setup(args.db, seed=not args.no_seed)


if __name__ == "__main__":
    main()
