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
    # (name, common_name, period, diet, size_class, description, notes)
    ("Tyrannosaurus rex",   "T. rex",      "Cretaceous", "Carnivore", "Massive", "Apex predator of the Late Cretaceous",           None),
    ("Velociraptor",        "Raptor",      "Cretaceous", "Carnivore", "Small",   "Small feathered solitary predator, small-prey specialist",
     "closed mouth option, low-slung feathered biped, propatagium confirmed — forearm folds inward at rest (bird-like wing fold), not held straight out; sickle claw raised off ground"),
    ("Triceratops",         "Triceratops", "Cretaceous", "Herbivore", "Large",   "Three-horned ceratopsid",                        None),
    ("Stegosaurus",         "Stegosaurus", "Jurassic",   "Herbivore", "Large",   "Plated herbivore with thagomizer tail",           None),
    ("Brachiosaurus",       "Brachiosaurus","Jurassic",  "Herbivore", "Massive", "Long-necked sauropod",                           None),
    ("Ankylosaurus",        "Ankylosaurus","Cretaceous", "Herbivore", "Large",   "Armored dinosaur with club tail",                None),
    ("Pteranodon",          "Pteranodon",  "Cretaceous", "Piscivore", "Large",   "Large pterosaur (not a dinosaur, but a classic)",None),
    ("Spinosaurus",         "Spinosaurus", "Cretaceous", "Piscivore", "Massive", "Sail-backed semi-aquatic predator",
     "closed mouth option, low-slung quadrupedal stance, crocodilian body proportions, "
     "deep muscular sail along spine"),
    ("Parasaurolophus",     "Para",        "Cretaceous", "Herbivore", "Large",   "Crested hadrosaur",                              None),
    ("Dilophosaurus",       "Dilopho",     "Jurassic",   "Carnivore", "Medium",  "Double-crested early theropod",                  None),
]

SEED_PARAMETERS = [
    # Midjourney-tuned prompt modifiers
    # category, name, value (injected into prompt text), weight

    # --- style: visual aesthetic descriptors MJ renders well ---
    ("style", "oil_painting",     "oil painting by Greg Rutkowski, impasto texture, painterly",       1.0),
    ("style", "watercolor",       "loose watercolor illustration, wet-on-wet blooms, paper texture",  1.0),
    ("style", "concept_art",      "concept art, matte painting, trending on ArtStation",              1.0),
    ("style", "hyperrealism",     (
        "hyperrealistic, anatomically accurate, living animal skin texture, "
        "subsurface scattering, 8K texture, shot on Canon EOS R5 400mm f/2.8, "
        "shallow depth of field, sharp anatomical detail, National Geographic wildlife photography, "
        "film grain, chromatic aberration, lens imperfection, real camera noise, "
        "not CGI, not rendered, not digital art, "
        "real wetland ecology, accurate Cretaceous flora, no anachronistic plants, "
        "volumetric atmosphere, photojournalism composition"
    ), 1.2),
    ("style", "ink_etching",      "detailed ink etching, crosshatching, wildlife field illustration",  1.0),
    ("style", "paleontology_art", "scientific paleoart, anatomically precise, detailed wildlife ecology illustration", 1.1),

    # --- lighting: MJ responds strongly to lighting cues ---
    ("lighting", "golden_hour",      "golden hour, warm low-angle sunlight, long shadows, lens flare",                                                                        1.0),
    ("lighting", "dramatic_rim",     "strong rim lighting, deep shadows, high contrast",                                                                                      1.1),
    ("lighting", "overcast",         "overcast sky, soft diffused light, muted tones, flat natural light",                                                                    1.0),
    ("lighting", "stormy",           "storm light, dark cumulonimbus, dramatic rays through clouds",                                                                          1.1),
    ("lighting", "blue_hour",        "blue hour twilight, cold flat ambient light, no direct sun, muted desaturated tones, horizon faintly lit",                              1.0),
    ("lighting", "harsh_midday",     "harsh midday sun directly overhead, bleached highlights, hard shadows directly below, squinting heat haze at horizon",                  1.0),
    ("lighting", "broken_cloud",     "broken cloud cover, intermittent direct sun patches, uneven illumination across habitat, shifting shadow edges",                        1.0),
    ("lighting", "backlit_haze",     "animal backlit by diffuse haze, silhouette edges glowing, atmospheric scattering, low sun behind subject",                              1.0),
    ("lighting", "pre_storm",        "pre-storm greenish ambient light, heavy cloud ceiling, eerie flat illumination, no distinct shadows",                                   1.0),
    ("lighting", "dappled_canopy",   "dappled light through canopy gaps, moving light patches on skin, deep shadow between lit zones",                                        1.0),

    # --- camera: framing and lens descriptors ---
    ("camera", "epic_wide",       "ultra-wide establishing shot, sweeping prehistoric landscape",     1.0),
    ("camera", "closeup_portrait","extreme close-up portrait, eye contact, shallow depth of field",   1.0),
    ("camera", "dynamic_low",     "dynamic low-angle action shot, motion blur, sense of speed",       1.1),
    ("camera", "aerial",          "aerial bird's-eye view, vast scale, tiny figures below",           1.0),
    ("camera", "medium_shot",     "medium shot, three-quarter view, natural pose",                    1.0),

    # --- mood: documentary wildlife tone — no drama, no spectacle ---
    ("mood", "quiet_power",          "animal simply existing, no drama, no spectacle, mundane moment caught on camera",                                                       1.0),
    ("mood", "serene",               "calm resting moment, animal at ease, no awareness of camera, documentary stillness",                                                    1.0),
    ("mood", "menacing",             "tense predatory stillness, locked gaze, not posing — caught mid-hunt by camera",                                                        1.1),
    ("mood", "closed_mouth_natural", "closed mouth, natural resting behavior, no threat display",                                                                             1.0),
    ("mood", "alert_scan",           "head raised mid-scan, ears and eyes forward, animal has detected something, body still, weight not yet shifted",                        1.0),
    ("mood", "drinking",             "head lowered to water, tongue or lips at surface, body weight shifted forward, vulnerable posture, documentary candid",                 1.0),
    ("mood", "heat_rest",            "sprawled in shade, limbs loose, eyes half-closed, animal conserving energy in midday heat, no awareness of camera",                    1.0),
    ("mood", "mid_stride",           "caught mid-step, one foot lifted, weight on rear leg, natural gait frozen by shutter, not posed",                                      1.0),
    ("mood", "feeding_focus",        "head down, fully absorbed in eating, animal ignoring surroundings, documentary feeding behaviour",                                      1.0),
    ("mood", "territorial_hold",     "standing its ground, body angled sideways, not charging — holding position, weight evenly planted",                                    1.0),
    ("mood", "post_kill_pause",      "standing over kill, not feeding yet, breathing heavy, blood on muzzle, staring into distance",                                         1.0),
    ("mood", "scent_check",          "nose low to ground, mouth slightly open, jacobson organ active, slow deliberate movement, tracking",                                   1.0),
    ("mood", "wading_slow",          "moving through shallow water, legs lifting high over surface, body steady, water disturbed around feet",                               1.0),
    ("mood", "dust_bath",            "animal rolling or crouching in dry dirt, dust rising around body, eyes closed, instinctive behaviour",                                 1.0),
    ("mood", "eye_contact",          "direct unblinking eye contact with camera, animal fully aware of lens, no threat display — just watching",                             1.0),

    # --- behavior: what the animal is doing ---
    ("behavior", "scanning_territory",   "head raised, body still, eyes on middle distance, nostrils flared, territorial survey",                                             1.0),
    ("behavior", "mid_stride",           "mid-stride, one foot raised, weight shifting forward, muscles tensed, tail counterbalancing",                                       1.0),
    ("behavior", "feeding",              "head lowered, actively feeding, neck extended, jaw working, natural feeding posture",                                               1.0),
    ("behavior", "resting_alert",        "body lowered, eyes open and tracking, head slightly raised, coiled readiness beneath calm",                                         1.0),
    ("behavior", "drinking_at_water",    "head lowered to water, neck extended, nose above still water, body weight forward",                                                 1.0),
    ("behavior", "threat_display",       "broadside threat display, body maximised for size, head lowered, crest extended, dominant stance",                                  1.0),
    ("behavior", "emerging_from_cover",  "emerging from dense vegetation, half-visible, one side in shadow, eyes locked forward",                                             1.0),
    ("behavior", "post_rain_stillness",  "standing after rain, skin glistening, steam rising from hide, puddles at feet",                                                     1.0),
    ("behavior", "shaking_off_water",    "violent full-body shake, water droplets exploding outward, head whipping, kinetic blur",                                            1.0),
    ("behavior", "cruising_open_water",  "level cruise through open water, streamlined posture, bow wave at snout, effortless power",                                         1.0),
    ("behavior", "breaching_surface",    "explosive breach through water surface, cascading foam, massive spray catching light, peak arc",                                    1.0),
    ("behavior", "hunting_dive",         "banking steeply downward, body on attack vector, dark water deepening, prey at depth",                                              1.0),
    ("behavior", "diving_strike",        "wings folded, near-vertical power dive, target below, extreme velocity, committed strike",                                          1.0),
    ("behavior", "thermal_soaring",      "wings at full span, banking on thermal, wingtips curled, scanning territory below",                                                 1.0),
    ("behavior", "landing_approach",     "wings spread in braking arc, legs forward, deceleration, final seconds before touchdown",                                           1.0),
    ("behavior", "freeze_detect",        "frozen mid-step, one foot still raised, weight on three limbs, head locked toward unseen threat, not breathing visibly",            1.0),
    ("behavior", "jaw_clean",            "dragging lower jaw slowly across ground after feeding, scraping residue from teeth on dirt and rock, eyes forward, deliberate",     1.0),
    ("behavior", "mud_wallow",           "lying on side in shallow mud, one foreleg pushing against ground, coating flank, eye just above mud line, slow roll",               1.0),
    ("behavior", "body_press_thermoreg", "belly flat against sun-warmed rock or ground, legs splayed out, eyes half-closed, absorbing heat through ventral surface",          1.0),
    ("behavior", "carcass_pause",        "standing directly over fresh kill, not yet feeding, head hanging, flanks heaving, blood pooling dark in soil beneath",              1.0),

    # --- condition: physical state of the animal ---
    ("condition", "weathered_adult",        "weathered hide, healed scratches on flanks, thickened skin at joints, subtle asymmetry",                                                                        1.0),
    ("condition", "battle_scarred",         "healed bite scars on neck, claw marks on ribcage, torn eyelid, powerful survivor",                                                                              1.0),
    ("condition", "elder_specimen",         "elder, deep wrinkles at eye and jaw, worn teeth, clouded iris, thickened scarred skin",                                                                         1.0),
    ("condition", "pristine_juvenile",      "pristine unblemished skin, smooth scales, bright alert eyes, full feathers where applicable",                                                                   1.0),
    ("condition", "mud_caked",              "thick dried mud caked on legs and underbelly, wet mud still fresh on feet, hide dark and streaked where mud is drying",                                         1.0),
    ("condition", "wet_from_water",         "freshly emerged from water, hide visibly wet, water beading on scales, dark wet patches drying unevenly across body",                                          1.0),
    ("condition", "parasite_load",          "clusters of ticks behind jaw and in skin folds, animal showing no reaction, naturalistic parasite load common in large reptiles",                              1.0),
    ("condition", "missing_toe",            "one toe on left forefoot absent at second joint, healed clean stump with thickened keratin, old injury fully recovered",                                       1.0),
    ("condition", "moulting_skin",          "patches of old skin lifting at joints and along flanks, new brighter scale layer beneath, dry flaking edges catching light",                                   1.0),
    ("condition", "blood_on_muzzle",        "fresh blood staining around mouth and lower jaw, wet and dark, recent feed, no other visible injury",                                                          1.0),
    ("condition", "algae_on_hide",          "faint green algae growth on dorsal scales and tail, common in semi-aquatic species, uneven coverage with bare patches",                                        1.0),
    ("condition", "fly_attention",          "several flies resting on eye corners and nostril edges, animal unbothered, naturalistic detail common in field photography",                                   1.0),
    ("condition", "lean_season",            "ribs just visible through skin on flanks, hip bones prominent, animal in lean condition between kills, alert but conserving energy",                           1.0),
    ("condition", "dominant_prime",         "peak condition adult, full muscle mass, no visible injury, glossy hide, clear eyes, animal at top of physical form",                                           1.0),
    ("condition", "eye_wound",              "milky scar tissue across left eye cornea, iris still visible beneath, old puncture wound fully healed, eye functional but visibly damaged",                    1.0),
    ("condition", "torn_sail",              "two tears in dorsal sail, edges healed to scar ridges, sail membrane translucent at thinner patches, bone spines intact",                                      1.0),
    ("condition", "jaw_asymmetry",          "lower jaw slightly off-centre from healed fracture, one tooth row misaligned by a few millimetres, bite still functional",                                    1.0),
    ("condition", "hide_bite_flank",        "deep bite scar on left flank, three parallel claw tracks crossing it, tissue raised and discoloured, fur or scale growth absent in scar",                     1.0),
    ("condition", "broken_horn_tip",        "right horn or crest tip snapped off mid-shaft, break point weathered smooth, bone core exposed and yellowed, healed years ago",                               1.0),
    ("condition", "missing_claw_digit",     "second claw on right forefoot entirely absent, digit stump rounded with thick keratin, compensatory weight shift visible in stance",                          1.0),
    ("condition", "patchy_hide",            "irregular bare patches on neck and shoulder where scales have shed and not fully regrown, raw pink underlayer visible at patch edges",                         1.0),
    ("condition", "embedded_tooth",         "foreign tooth fragment lodged in jaw muscle near hinge, skin grown partially over it, faint raised lump with discolouration",                                 1.0),
    ("condition", "split_claw",             "primary killing claw split lengthwise from tip to base, crack packed with dried mud, claw still functional, edges serrated from the break",                   1.0),
    ("condition", "neck_scar_collar",       "ring of healed bite scars encircling base of neck, consistent with juvenile predator attack survived, skin thickened and puckered at scar line",              1.0),

    # --- weather: atmospheric and environmental conditions ---
    ("weather", "clear_pristine",      "cloudless sky, hard directional light, crisp shadows, fully saturated colours", 1.0),
    ("weather", "storm_approaching",   "cumulonimbus wall on horizon, sky bruised green-grey, eerie stillness, air charged with electricity", 1.0),
    ("weather", "post_storm_clearing", "storm just passed, broken cloud, shafts of sunlight, glistening surfaces, steam from ground", 1.0),
    ("weather", "monsoon_heavy",       "heavy driving rain, diagonal streaks across frame, surfaces glistening, steam from warm hide", 1.0),
    ("weather", "ground_mist",         "dense ground mist at knee height, legs dissolved in fog, body floating above mist", 1.0),
    ("weather", "heat_haze",           "intense heat, air shimmer from baked ground, bleached sky, dust rising from every footfall", 1.0),
    ("weather", "light_snowfall",      "light snow falling, snowflakes on scales, breath condensation visible, muted blue-white palette", 1.0),
    ("weather", "arctic_freeze",       "extreme cold, frost on scales, breath condensation heavy, ice at eyelid edges, blue-white light", 1.0),
    ("weather", "volcanic_ash_fall",   "volcanic ash drifting down, sulphurous yellow-grey atmosphere, sun a pale disc, ash on scales", 1.0),
    ("weather", "wildfire_smoke",      "wildfire smoke, sun an ember-orange disc, ash drifting, deep orange and amber light", 1.0),

    # --- anatomy: species-level body accuracy requirements ---
    ("anatomy", "full_body_accuracy", (
        "full body visible including hands and feet, pronated wrists corrected, "
        "hands in neutral position with palms facing inward, sickle claw raised off ground, "
        "correct theropod hand anatomy, fingers not splayed, wrist not bent downward"
    ), 1.2),
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
           (name, common_name, period, diet, size_class, description, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        SEED_SPECIES,
    )
    print(f"  Seeded {cur.rowcount} species rows")

    cur.executemany(
        """INSERT OR IGNORE INTO parameters
           (category, name, value, weight)
           VALUES (?, ?, ?, ?)""",
        SEED_PARAMETERS,
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
