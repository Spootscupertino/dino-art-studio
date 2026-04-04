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
    ("lighting", "golden_hour",     "golden hour, warm low-angle sunlight, long shadows, lens flare", 1.0),
    ("lighting", "dramatic_rim",    "dramatic rim lighting, deep shadows, chiaroscuro, cinematic",    1.1),
    ("lighting", "overcast",        "overcast sky, soft diffused light, muted tones, moody atmosphere",1.0),
    ("lighting", "bioluminescent",  "bioluminescent markings, night scene, glowing blues and greens", 1.0),
    ("lighting", "stormy",          "storm light, dark cumulonimbus, dramatic rays through clouds",   1.1),

    # --- camera: framing and lens descriptors ---
    ("camera", "epic_wide",       "ultra-wide establishing shot, sweeping prehistoric landscape",     1.0),
    ("camera", "closeup_portrait","extreme close-up portrait, eye contact, shallow depth of field",   1.0),
    ("camera", "dynamic_low",     "dynamic low-angle action shot, motion blur, sense of speed",       1.1),
    ("camera", "aerial",          "aerial bird's-eye view, vast scale, tiny figures below",           1.0),
    ("camera", "medium_shot",     "medium shot, three-quarter view, natural pose",                    1.0),

    # --- mood: emotional/atmospheric tone ---
    ("mood", "epic",       "epic scale, awe-inspiring, cinematic grandeur",                           1.2),
    ("mood", "serene",     "peaceful and serene, nature documentary atmosphere",                      1.0),
    ("mood", "menacing",   "menacing and predatory, tense atmosphere, primal danger",                 1.1),
    ("mood", "whimsical",  "whimsical and colorful, children's book illustration style",              1.0),
    ("mood", "eerie",      "eerie silence, liminal quality, unsettling calm before an attack",        1.0),

    # --- behavior: what the animal is doing ---
    ("behavior", "scanning_territory",  "head raised, body still, eyes on middle distance, nostrils flared, territorial survey", 1.0),
    ("behavior", "mid_stride",          "mid-stride, one foot raised, weight shifting forward, muscles tensed, tail counterbalancing", 1.0),
    ("behavior", "feeding",             "head lowered, actively feeding, neck extended, jaw working, natural feeding posture", 1.0),
    ("behavior", "resting_alert",       "body lowered, eyes open and tracking, head slightly raised, coiled readiness beneath calm", 1.0),
    ("behavior", "drinking_at_water",   "head lowered to water, neck extended, nose above still water, body weight forward", 1.0),
    ("behavior", "threat_display",      "broadside threat display, body maximised for size, head lowered, crest extended, dominant stance", 1.0),
    ("behavior", "emerging_from_cover", "emerging from dense vegetation, half-visible, one side in shadow, eyes locked forward", 1.0),
    ("behavior", "post_rain_stillness", "standing after rain, skin glistening, steam rising from hide, puddles at feet", 1.0),
    ("behavior", "shaking_off_water",   "violent full-body shake, water droplets exploding outward, head whipping, kinetic blur", 1.0),
    ("behavior", "cruising_open_water", "level cruise through open water, streamlined posture, bow wave at snout, effortless power", 1.0),
    ("behavior", "breaching_surface",   "explosive breach through water surface, cascading foam, massive spray catching light, peak arc", 1.0),
    ("behavior", "hunting_dive",        "banking steeply downward, body on attack vector, dark water deepening, prey at depth", 1.0),
    ("behavior", "diving_strike",       "wings folded, near-vertical power dive, target below, extreme velocity, committed strike", 1.0),
    ("behavior", "thermal_soaring",     "wings at full span, banking on thermal, wingtips curled, scanning territory below", 1.0),
    ("behavior", "landing_approach",    "wings spread in braking arc, legs forward, deceleration, final seconds before touchdown", 1.0),

    # --- condition: physical state of the animal ---
    ("condition", "weathered_adult",   "weathered hide, healed scratches on flanks, thickened skin at joints, subtle asymmetry", 1.0),
    ("condition", "battle_scarred",    "healed bite scars on neck, claw marks on ribcage, torn eyelid, powerful survivor", 1.0),
    ("condition", "elder_specimen",    "elder, deep wrinkles at eye and jaw, worn teeth, clouded iris, thickened scarred skin", 1.0),
    ("condition", "pristine_juvenile", "pristine unblemished skin, smooth scales, bright alert eyes, full feathers where applicable", 1.0),

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
