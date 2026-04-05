#!/usr/bin/env python3
"""
generate_prompt.py — interactive Midjourney prompt builder for dinosaur art.

Usage:
    python generate_prompt.py
    python generate_prompt.py --ar 16:9 --stylize 500 --chaos 10
    python generate_prompt.py --db /path/to/other.db
"""

import argparse
import sqlite3
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Terminal color constants (ANSI escape codes)
# ---------------------------------------------------------------------------

class C:
    """ANSI color/style codes. All reset automatically via RESET."""
    RESET        = "\033[0m"
    BOLD         = "\033[1m"
    DIM          = "\033[2m"
    CYAN         = "\033[36m"
    BOLD_CYAN    = "\033[1;36m"
    WHITE        = "\033[37m"
    BRIGHT_WHITE = "\033[97m"
    GREEN        = "\033[32m"
    BOLD_GREEN   = "\033[1;32m"
    YELLOW       = "\033[33m"
    RED          = "\033[31m"
    BOLD_RED     = "\033[1;31m"
    MAGENTA      = "\033[35m"


def hdr(text: str) -> str:
    """Bold cyan section header."""
    return f"{C.BOLD_CYAN}{text}{C.RESET}"


def opt(text: str) -> str:
    """Bright white numbered option."""
    return f"{C.BRIGHT_WHITE}{text}{C.RESET}"


def ok(text: str) -> str:
    """Green confirmation / auto-applied."""
    return f"{C.BOLD_GREEN}{text}{C.RESET}"


def warn(text: str) -> str:
    """Yellow advisory / outdated flag."""
    return f"{C.YELLOW}{text}{C.RESET}"


def err(text: str) -> str:
    """Red error / hard block."""
    return f"{C.BOLD_RED}{text}{C.RESET}"


def dim(text: str) -> str:
    """Dim secondary info."""
    return f"{C.DIM}{text}{C.RESET}"

DB_DEFAULT = Path(__file__).parent / "dino_art.db"
SPECIES_REF_DIR = Path(__file__).parent / "species_reference"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".raw", ".cr2", ".cr3", ".arw", ".nef"}
OUTDATED_THRESHOLD = 2020  # flag species whose last_scientific_update is before this year

# Period → evocative environment phrase (one tight setting, no stacked sub-clauses)
ENVIRONMENTS = {
    # Terrestrial
    "Triassic":            "arid Triassic floodplain, sparse conifers and ferns",
    "Jurassic":            "lush Jurassic forest, towering conifers, morning mist",
    "Cretaceous":          "Late Cretaceous river delta, open floodplain, flowering plants",
    "Other":               "ancient prehistoric landscape",
    # Marine
    "marine_Jurassic":     "warm shallow Jurassic sea, turquoise water, sunlit upper ocean",
    "marine_Cretaceous":   "Late Cretaceous Western Interior Seaway, open ocean, surface light above",
    "marine_Triassic":     "ancient Triassic shallow sea, clear tropical water",
    "marine_Other":        "ancient prehistoric ocean, open deep water",
    # Aerial
    "aerial_Jurassic":     "vast Jurassic sky, forest canopy below, warm thermals",
    "aerial_Cretaceous":   "Late Cretaceous sky, open floodplain below, horizon stretching wide",
    "aerial_Triassic":     "open Triassic sky, sparse land far below",
    "aerial_Other":        "vast prehistoric sky, open aerial expanse",
}

CATEGORIES = ["lighting", "camera", "mood", "condition"]

# Style is always hyperrealism — never ask the user
HYPERREALISM_STYLE = {
    "id":    24,
    "name":  "hyperrealism",
    "value": "hyperrealistic, anatomically accurate, living animal skin texture, subsurface scattering, 8K texture",
}

# ---------------------------------------------------------------------------
# Mouth / teeth / saliva — diet-aware, injected as a dedicated prompt block
# ---------------------------------------------------------------------------

MOUTH_TEETH_CARNIVORE = (
    "yellowed uneven teeth, wet interior mouth, heavy saliva stranding between teeth"
)

MOUTH_TEETH_HERBIVORE = (
    "wet lips parted, grinding teeth worn flat, saliva catching light along jaw"
)

# ---------------------------------------------------------------------------
# Ground interaction — feet/claws as a spatial relationship block, not anatomy.
# Kept separate from the subject section so MJ reads it as contact with ground.
# ---------------------------------------------------------------------------

GROUND_INTERACTION = (
    "feet fully weight-bearing, each toe contacting ground at a different angle, "
    "visible pressure on toe pads, natural keratin wear on claw tips, "
    "packed dirt between digits, knuckle joints slightly bent under load"
)

# ---------------------------------------------------------------------------
# Canvas print mode constants
# ---------------------------------------------------------------------------

CANVAS_PRINT = (
    "high dynamic range, shadow detail retained, highlight detail retained, "
    "print-ready detail, no blown highlights"
)

# ---------------------------------------------------------------------------
# Negative prompt — appended as --no flag to fight Midjourney's extremity slop
# ---------------------------------------------------------------------------

NEGATIVE_PROMPT = (
    # Anatomy / extremity errors
    "fused digits, merged toes, webbed feet, blob hands, extra fingers, "
    "missing claws, undefined claw tips, floating toes, amputated digits, "
    "incorrect toe count, melted feet, smooth footpad with no digit separation, "
    "smeared claws, indistinct talons, CGI smoothness on extremities, "
    # Studio / controlled environment blockers
    "studio background, seamless backdrop, portrait lighting, gradient background, "
    "grey background, controlled lighting, specimen photography, museum display, "
    "exhibit lighting, black background, white background, studio flash, "
    "specimen mount, display case, diorama, natural history exhibit, "
    # Fossil / skeletal blockers
    "fossil, fossilized, skeleton, skeletal, bones, bone structure, excavation, "
    "petrified, paleontology specimen, museum specimen, rock matrix, sediment, "
    "dinosaur fossil, fossil record, prehistoric bones, mineralized, stone cast, "
    "osteoderms, osteoderm, "
    # Indoor / built environment blockers
    "indoors, interior, building, warehouse, arena, concrete floor"
)

# Species-specific additions that only apply in canvas / full-body modes
CANVAS_SPECIES_EXTRAS = {
    "Velociraptor": "sickle claw raised, palms inward, tail extended for balance",
}

# ---------------------------------------------------------------------------
# Output modes
# Each entry drives fixed-camera text, composition instructions, and flags.
# fixed_camera=None means the user picks a camera from the DB.
# composition="PLACEMENT" is a sentinel that triggers the placement sub-menu.
# ---------------------------------------------------------------------------

OUTPUT_MODES: dict[str, dict] = {
    "portrait": {
        "display":       "Portrait close-up",
        "desc":          "telephoto, tight framing, mood-focused",
        "fixed_camera":  None,
        "composition":   "",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
    },
    "canvas": {
        "display":       "Full body canvas print",
        "desc":          "mid-range lens, 60/40 negative space, print-ready",
        "fixed_camera":  "Canon EOS R5 24-70mm f/4, mid-range, habitat in frame",
        "composition":   "PLACEMENT",
        "canvas_print":  True,
        "full_body":     True,
        "needs_placement": True,
    },
    "environmental": {
        "display":       "Environmental wide shot",
        "desc":          "animal small in vast landscape, habitat dominant",
        "fixed_camera":  "Canon EOS R5 16-35mm f/2.8, ultra-wide, animal under 20% of frame",
        "composition":   "animal small in vast prehistoric landscape, habitat dominant",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
    },
    "extreme_closeup": {
        "display":       "Extreme detail close-up",
        "desc":          "macro, single surface dominant, texture abstracted",
        "fixed_camera":  "Canon EOS R5 100mm macro f/8, razor-thin depth of field",
        "composition":   "single anatomical surface fills frame, texture dominant",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
    },
    "action_freeze": {
        "display":       "Action freeze frame",
        "desc":          "motion stopped at peak energy, every detail sharp",
        "fixed_camera":  "Canon EOS R5 400mm f/2.8, 1/2000s freeze, sharp throughout",
        "composition":   "frozen mid-action at peak moment, kinetic force implied",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
    },
    "silhouette": {
        "display":       "Silhouette against sky",
        "desc":          "backlit, form only, no surface detail",
        "fixed_camera":  "Canon EOS R5, exposed for bright background, strong rim light",
        "composition":   "pure silhouette against sky, stark contrast, form only",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
    },
    "tracking_side": {
        "display":       "Tracking side profile",
        "desc":          "panning shot, sharp subject, motion-blurred background",
        "fixed_camera":  "Canon EOS R5 400mm f/2.8, panning, subject sharp on blurred background",
        "composition":   "lateral tracking shot, sharp side profile, background streaked",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
    },
    "ground_level": {
        "display":       "Ground-level upward",
        "desc":          "camera at ground, animal towers above lens",
        "fixed_camera":  "Canon EOS R5 24mm f/2.8, camera at ground, extreme upward angle",
        "composition":   "ground-level upward, animal towers overhead, sky behind",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
    },
    "aerial_overhead": {
        "display":       "Aerial overhead",
        "desc":          "direct overhead, dorsal surface visible, habitat below",
        "fixed_camera":  "Canon EOS R5 35mm, directly overhead, dorsal surface",
        "composition":   "overhead view, dorsal surface centred, habitat visible around animal",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
    },
    "dusk_long_exp": {
        "display":       "Dusk long exposure",
        "desc":          "motion blur, ambient light only, atmospheric",
        "fixed_camera":  "Canon EOS R5 50mm f/5.6, tripod, long exposure at dusk",
        "composition":   "long exposure, moving elements blurred, static elements sharp",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
    },
}


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        sys.exit(f"Database not found: {db_path}\nRun setup_db.py first.")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def fetch_species(conn: sqlite3.Connection) -> list:
    return conn.execute(
        "SELECT id, name, common_name, period, diet, size_class, description, notes, habitat FROM species ORDER BY name"
    ).fetchall()


def fetch_parameters_by_category(conn: sqlite3.Connection, category: str) -> list:
    return conn.execute(
        "SELECT id, name, value, weight FROM parameters WHERE category = ? ORDER BY name",
        (category,),
    ).fetchall()


def fetch_species_required_params(conn: sqlite3.Connection, species_id: int) -> list:
    return conn.execute(
        """SELECT p.id, p.category, p.name, p.value
           FROM species_parameters sp
           JOIN parameters p ON p.id = sp.parameter_id
           WHERE sp.species_id = ? AND sp.required = 1
           ORDER BY p.category, p.name""",
        (species_id,),
    ).fetchall()


def fetch_global_rules(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT rule FROM global_rules WHERE active = 1 ORDER BY id"
    ).fetchall()
    return [r["rule"] for r in rows]


def fetch_species_science(conn: sqlite3.Connection, species_id: int):
    return conn.execute(
        """SELECT body_length_m, body_mass_kg, locomotion_type, feathering_coverage,
                  skin_texture_type, tail_posture, wrist_position,
                  known_coloration_evidence, last_scientific_update, habitat
           FROM species WHERE id = ?""",
        (species_id,),
    ).fetchone()


def fetch_research_notes(conn: sqlite3.Connection, species_id: int) -> list:
    return conn.execute(
        """SELECT finding, author, year, source, affects_prompt
           FROM research_notes
           WHERE species_id = ? ORDER BY affects_prompt DESC, year DESC""",
        (species_id,),
    ).fetchall()


def scan_reference_images() -> dict[str, int]:
    """Return {species_name: image_count} by scanning species_reference subfolders."""
    counts = {}
    if not SPECIES_REF_DIR.exists():
        return counts
    for folder in sorted(SPECIES_REF_DIR.iterdir()):
        if folder.is_dir():
            images = [f for f in folder.iterdir()
                      if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
            counts[folder.name] = len(images)
    return counts


def save_prompt(
    conn: sqlite3.Connection,
    species_id: int,
    title: str,
    positive_prompt: str,
    tags: str,
    parameter_ids: list[int],
) -> int:
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO prompts (species_id, title, positive_prompt, tags, status)
           VALUES (?, ?, ?, ?, 'pending')""",
        (species_id, title, positive_prompt, tags),
    )
    prompt_id = cur.lastrowid
    cur.executemany(
        "INSERT INTO prompt_parameters (prompt_id, parameter_id) VALUES (?, ?)",
        [(prompt_id, pid) for pid in parameter_ids],
    )
    conn.commit()
    return prompt_id


# ---------------------------------------------------------------------------
# Interactive menus
# ---------------------------------------------------------------------------

def pick(label: str, rows: list, display_fn) -> object:
    """Print a numbered menu and return the chosen row."""
    print(f"\n  {hdr(label)}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for i, row in enumerate(rows, 1):
        print(f"  {C.DIM}{i:>2}.{C.RESET}  {opt(display_fn(row))}")
    print()
    while True:
        raw = input(f"  {C.BOLD_CYAN}Choose 1–{len(rows)}:{C.RESET} ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(rows):
            chosen = rows[int(raw) - 1]
            print(f"  {ok('✓')} {ok(display_fn(chosen))}\n")
            return chosen
        print(f"  {err(f'Please enter a number between 1 and {len(rows)}.')}")


def select_mode() -> str:
    """Present the 10 output modes and return the chosen mode key."""
    keys = list(OUTPUT_MODES.keys())
    print(f"\n  {hdr('Select output mode')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for i, key in enumerate(keys, 1):
        cfg = OUTPUT_MODES[key]
        print(f"  {C.DIM}{i:>2}.{C.RESET}  {C.BRIGHT_WHITE}{cfg['display']:<26}{C.RESET}  {dim(cfg['desc'])}")
    print()
    while True:
        raw = input(f"  {C.BOLD_CYAN}Choose 1–{len(keys)}:{C.RESET} ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            chosen_key = keys[int(raw) - 1]
            print(f"  {ok('✓')} {ok(OUTPUT_MODES[chosen_key]['display'])}\n")
            return chosen_key
        print(f"  {err(f'Please enter a number between 1 and {len(keys)}.')}")


def select_canvas_placement() -> tuple[str, str]:
    """Ask how the animal is positioned in frame.
    Returns (composition_phrase, space_side).
    'dead_center' is a sentinel that triggers symmetric composition text."""
    OPTIONS = [
        # (composition_phrase injected into prompt,  space_side label for display)
        ("animal positioned left of centre, rule of thirds",                "right"),
        ("animal positioned right of centre, rule of thirds",               "left"),
        ("dead_center",                                                      ""),
        ("animal filling lower foreground, environment stretching above",   "above"),
        ("animal in far distance, tiny against vast landscape",             "all"),
        ("animal emerging from dense vegetation, partially obscured",       "right"),
        ("animal seen from behind, retreating from camera",                 "ahead"),
        ("animal at water's edge, full reflection below",                   "below"),
        ("camera below looking up, animal against sky",                     "above"),
        ("animal high on ridge or elevated terrain, horizon behind",        "below"),
    ]
    LABELS = [
        "Rule of thirds — left",
        "Rule of thirds — right",
        "Dead centre — symmetrical, camera trap",
        "Foreground dominant — animal fills lower frame",
        "Distant figure — tiny in vast landscape",
        "Emerging from cover — partially obscured",
        "Retreating away — animal from behind",
        "Water's edge — animal with reflection",
        "Low angle — camera below, sky behind",
        "High ground — animal on ridge, horizon below",
    ]
    print(f"\n  {hdr('Animal placement')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for i, label in enumerate(LABELS, 1):
        print(f"  {C.DIM}{i:>2}.{C.RESET}  {opt(label)}")
    print()
    while True:
        raw = input(f"  {C.BOLD_CYAN}Choose 1–{len(OPTIONS)}:{C.RESET} ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(OPTIONS):
            chosen = OPTIONS[int(raw) - 1]
            print(f"  {ok('✓')} {ok(LABELS[int(raw) - 1])}\n")
            return chosen
        print(f"  {err(f'Please enter a number between 1 and {len(OPTIONS)}.')}")


def pick_species(conn: sqlite3.Connection):
    rows = fetch_species(conn)
    if not rows:
        sys.exit("No species found. Run setup_db.py to seed the database.")

    def fmt(r):
        size = f"[{r['size_class']}]" if r["size_class"] else ""
        period = f"({r['period']})" if r["period"] else ""
        common = f" / {r['common_name']}" if r["common_name"] else ""
        return f"{r['name']}{common}  {size} {period}"

    return pick("Select a dinosaur species", rows, fmt)


def pick_parameter(conn: sqlite3.Connection, category: str, name_only: bool = False):
    rows = fetch_parameters_by_category(conn, category)
    if not rows:
        sys.exit(f"No parameters found for category '{category}'. Run setup_db.py.")

    label = f"Select {category.upper()}"

    if name_only:
        def fmt(r):
            return r["name"].replace("_", " ")
    else:
        def fmt(r):
            weight_tag = f" [weight {r['weight']}]" if r["weight"] != 1.0 else ""
            return f"{r['name']:<22} — {r['value']}{weight_tag}"

    return pick(label, rows, fmt)


# ---------------------------------------------------------------------------
# Vary Region fix prompts — modular inpainting prompts for step 2 / 3 / 4
# ---------------------------------------------------------------------------

def validate_prompt(prompt: str, allow_mj_params: bool, label: str) -> None:
    """Raise ValueError if prompt violates its schema.

    Main prompts  (allow_mj_params=True)  — must contain at least one -- flag.
    Fix prompts   (allow_mj_params=False) — must contain no -- flags.
    """
    has_params = ' --' in prompt
    if allow_mj_params and not has_params:
        raise ValueError(f"[{label}] main prompt is missing MJ parameters (--style, --stylize, etc.)")
    if not allow_mj_params and has_params:
        import re
        found = re.findall(r'--\S+', prompt)
        raise ValueError(f"[{label}] fix prompt must not contain MJ parameters, found: {found}")


def strip_mj_params(prompt: str) -> str:
    """Remove all Midjourney parameters (--flag ...) from a prompt string.
    MJ flags are always appended at the end, so everything from the first -- onward is dropped."""
    idx = prompt.find(' --')
    return prompt[:idx].strip() if idx != -1 else prompt.strip()


def make_feet_fix_prompt(species, mj_style: str, stylize: int = 20) -> str:
    """Vary Region prompt for feet/claws. Paint over feet, paste this prompt."""
    diet    = species["diet"] or ""
    habitat = species["habitat"] or "terrestrial"
    name    = species["name"]

    if habitat == "marine":
        core = (
            f"extreme close-up of {name} flipper, paddle limb, "
            "individual digit bones visible under skin tension, wet glistening skin, "
            "natural wear on flipper tip, real wildlife photograph"
        )
    elif diet in ("Carnivore", "Piscivore"):
        core = (
            f"extreme close-up of {name} foot, each toe individually separated gripping ground, "
            "recurved talons each a different length and curvature, "
            "visible knuckle joints bending under weight, "
            "dark worn keratin with cracks and chips, caked mud between digits, "
            "wrinkled leathery toe pads, komodo dragon foot reference, "
            "real wildlife photograph of reptile foot"
        )
    else:
        core = (
            f"extreme close-up of {name} foot, column-like toes weight-bearing, "
            "blunt rounded toenails with natural wear, "
            "wrinkled leathery skin at toe joints, caked mud between digits, "
            "elephant foot reference, real wildlife photograph"
        )

    flags = f"--no {NEGATIVE_PROMPT} --style {mj_style} --stylize {stylize}"
    return f"{core}, telephoto macro, shallow depth of field, muted colour, film grain {flags}"


def make_environment_fix_prompt(species, environment: str, weather_param, lighting_param,
                                 mj_style: str, stylize: int = 30) -> str:
    """Vary Region prompt for background/habitat. Paint over background, paste this prompt."""
    habitat = species["habitat"] or "terrestrial"

    if habitat == "marine":
        ground = "water surface texture, underwater light refraction, natural ocean colour"
    elif habitat == "aerial":
        ground = "real photographed sky, atmospheric haze, natural cloud formation"
    else:
        ground = "ground texture, soil and rock detail, sparse prehistoric vegetation in background"

    core = (
        f"{environment}, {ground}, "
        f"{lighting_param['value']}, {weather_param['value']}, "
        "real photographed sky with atmospheric haze at horizon, "
        "telephoto background bokeh, muted natural colour, film grain, "
        "no animal in frame, habitat only"
    )

    neg = "painted sky, gradient sky, CGI sky, illustration, studio background, digital art, animal, dinosaur"
    flags = f"--no {neg} --style {mj_style} --stylize {stylize}"
    return f"{core} {flags}"


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

def assemble_prompt(
    species,
    science,            # Row from fetch_species_science — injected into subject block
    style_param,
    lighting_param,
    camera_param,       # ignored when mode has a fixed_camera
    mood_param,
    condition_param,
    behavior_param,
    weather_param,
    required_params: list,
    global_rules: list[str],
    mj_style: str,
    stylize: int,
    chaos: int,
    quality: float,
    output_mode: str = "portrait",
    placement: tuple[str, str] = ("", ""),  # (subject_side, space_side) from select_placement()
    has_sref: bool = False,
) -> str:
    mode_cfg     = OUTPUT_MODES.get(output_mode, OUTPUT_MODES["portrait"])
    full_body    = mode_cfg["full_body"]
    canvas_print = mode_cfg["canvas_print"]

    # ── SECTION 1: SUBJECT ───────────────────────────────────────────────────
    # Anatomy, pose, skin, mouth, behavior, condition, mood.
    # Richest section — MJ weights early tokens most heavily.
    # Rule: no environment, no lighting, no camera language here.

    size = species["size_class"].lower() if species["size_class"] else ""
    subject_parts = [f"{size} {species['name']}", species["description"] or ""]

    if species["notes"]:
        subject_parts.append(species["notes"])

    # Anatomy from science table
    if science and science["feathering_coverage"] and science["feathering_coverage"].lower() != "none":
        subject_parts.append(science["feathering_coverage"])
    if science and science["tail_posture"] and science["tail_posture"].lower() not in ("not applicable — pterosaur", ""):
        subject_parts.append(science["tail_posture"])  # no "tail posture:" label — reads as descriptor
    if science and science["known_coloration_evidence"]:
        ce = science["known_coloration_evidence"]
        if not any(ce.lower().startswith(p) for p in ("no direct", "no known", "unknown")):
            subject_parts.append(ce)

    # Required species params (e.g. raptor sickle claw accuracy)
    for rp in required_params:
        subject_parts.append(rp["value"])

    # Canvas species extras (pose specifics for full-body modes)
    if full_body or has_sref:
        if output_mode == "canvas":
            extra = CANVAS_SPECIES_EXTRAS.get(species["name"])
            if extra:
                subject_parts.append(extra)
        subject_parts.append("full body visible head to tail")

    # Skin texture (body surface — belongs in subject)
    if science and science["skin_texture_type"]:
        subject_parts.append(science["skin_texture_type"])

    # Mouth / teeth (body surface — diet-aware)
    diet = species["diet"] or ""
    subject_parts.append(MOUTH_TEETH_CARNIVORE if diet in ("Carnivore", "Piscivore") else MOUTH_TEETH_HERBIVORE)

    # Behavior (what the animal is doing — pose/action)
    subject_parts.append(behavior_param["value"])

    # Condition and mood (body state and demeanor)
    subject_parts.append(condition_param["value"])
    subject_parts.append(mood_param["value"])

    # Hyperrealism style anchor — appended last so it applies to the whole subject block
    subject_parts.append(style_param["value"])

    subject = ", ".join(p for p in subject_parts if p)

    # ── SECTION 2: INTERACTION ────────────────────────────────────────────────
    # Feet/claws as a spatial relationship with the ground, not anatomy.
    # Shorter than subject — focused on contact mechanics only.
    interaction = GROUND_INTERACTION

    # ── SECTION 3: ENVIRONMENT ────────────────────────────────────────────────
    # Habitat and period setting. Composition framing appended here.
    # No subject descriptors, no lighting language.
    habitat = species["habitat"] or "terrestrial"
    period  = species["period"] or "Other"
    if habitat in ("marine", "aerial"):
        env_key = f"{habitat}_{period}"
        environment = ENVIRONMENTS.get(env_key, ENVIRONMENTS.get(f"{habitat}_Other", ENVIRONMENTS["Other"]))
    else:
        environment = ENVIRONMENTS.get(period, ENVIRONMENTS["Other"])

    comp_template = mode_cfg["composition"]
    if comp_template == "PLACEMENT":
        subject_phrase, space_side = placement
        if subject_phrase == "dead_center":
            comp = "animal centred, symmetrical, horizon visible"
        elif space_side in ("right", "left"):
            comp = f"{subject_phrase}, negative space {space_side}, horizon visible"
        else:
            comp = f"{subject_phrase}, horizon visible"
        environment = f"{environment}, {comp}"
    elif comp_template:
        environment = f"{environment}, {comp_template}"

    # ── SECTION 4: LIGHTING ───────────────────────────────────────────────────
    # One lighting condition + one weather phrase. Short and supportive.
    lighting = f"{lighting_param['value']}, {weather_param['value']}"

    # ── SECTION 5: CAMERA ─────────────────────────────────────────────────────
    # Minimal — lens spec only. Everything else is in sections 1–4.
    camera_text = mode_cfg["fixed_camera"] or camera_param["value"]
    camera = f"shot on {camera_text}"

    # ── ASSEMBLE ──────────────────────────────────────────────────────────────
    sections = [subject, interaction, environment, lighting, camera]
    if canvas_print:
        sections.append(CANVAS_PRINT)

    # Deduplication — strip exact repeated clauses that can arise from overlapping params
    seen, deduped_clauses = set(), []
    for clause in ", ".join(s for s in sections if s).split(", "):
        key = clause.strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped_clauses.append(clause.strip())

    prose = ", ".join(deduped_clauses)

    # ── MJ FLAGS ──────────────────────────────────────────────────────────────
    flags = f"--no {NEGATIVE_PROMPT} --style {mj_style} --stylize {stylize} --q {quality:g}"
    if chaos > 0:
        flags += f" --chaos {chaos}"

    return f"{prose} {flags}"


def make_title(species, mood_param, output_mode: str = "portrait") -> str:
    name = species["common_name"] or species["name"]
    mode_display = OUTPUT_MODES.get(output_mode, {}).get("display", output_mode).lower()
    suffix = mode_display if output_mode != "portrait" else mood_param["name"].replace("_", " ")
    return f"{name} — {suffix}"


def make_tags(species, style_param, lighting_param, camera_param, mood_param,
              condition_param, behavior_param, weather_param, output_mode: str = "portrait") -> str:
    parts = []
    if species["period"]:
        parts.append(species["period"].lower())
    for p in (style_param, lighting_param, mood_param):
        parts.append(p["name"])
    parts.append(camera_param["name"] if camera_param else output_mode)
    parts.append(condition_param["name"])
    parts.append(behavior_param["name"])
    parts.append(weather_param["name"])
    parts.append(output_mode)
    return ",".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def display_reference_scan() -> None:
    """Print a startup report of reference images loaded per species."""
    counts = scan_reference_images()
    if not counts:
        print(f"  {dim('[reference] species_reference/ folder not found — skipping image scan')}")
        return
    total = sum(counts.values())
    loaded = sum(1 for c in counts.values() if c > 0)
    print(f"\n  {hdr(f'REFERENCE IMAGES  ({loaded}/{len(counts)} species loaded, {total} total)')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for folder, count in counts.items():
        display_name = folder.replace("_", " ").title()
        bar = f"{C.CYAN}" + "█" * min(count, 20) + C.RESET
        if count:
            status = ok(f"{count:>3} image{'s' if count != 1 else ' '}")
        else:
            status = dim("  — no images yet")
        print(f"  {C.WHITE}{display_name:<22}{C.RESET} {status}  {bar}")
    print()


def display_science_brief(species, science, notes: list) -> None:
    """Print a field-guide summary and research notes for the selected species."""
    name = species["name"]
    print(f"\n  {hdr(f'SPECIES BRIEF — {name}')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)

    if science and any(science):
        length  = f"{science['body_length_m']}m" if science["body_length_m"] else "unknown"
        mass    = f"{science['body_mass_kg']:,.0f} kg" if science["body_mass_kg"] else "unknown"
        loco    = science["locomotion_type"] or "unknown"
        feather = science["feathering_coverage"] or "unknown"
        print(f"  {C.WHITE}Length:{C.RESET} {length:<10} {C.WHITE}Mass:{C.RESET} {mass:<14} {C.WHITE}Locomotion:{C.RESET} {loco}")
        if science["skin_texture_type"]:
            print(f"  {C.WHITE}Skin:{C.RESET}   {science['skin_texture_type']}")
        if science["feathering_coverage"]:
            print(f"  {C.WHITE}Feathering:{C.RESET} {feather}")
        if science["tail_posture"]:
            print(f"  {C.WHITE}Tail posture:{C.RESET} {science['tail_posture']}")
        if science["wrist_position"]:
            print(f"  {C.WHITE}Wrist:{C.RESET} {science['wrist_position']}")

        update_year = science["last_scientific_update"]
        if update_year:
            if update_year < OUTDATED_THRESHOLD:
                print(f"  {warn(f'⚠  Last updated {update_year} — check for more recent observations')}")
            else:
                print(f"  {dim(f'Last updated: {update_year}')}")

    prompt_notes = [n for n in notes if n["affects_prompt"]]
    all_notes    = [n for n in notes if not n["affects_prompt"]]

    if prompt_notes:
        print(f"\n  {hdr(f'PROMPT-RELEVANT FINDINGS ({len(prompt_notes)})')}")
        for n in prompt_notes:
            year_tag = f"[{n['year']}] " if n["year"] else ""
            author   = f"{n['author']} — " if n["author"] else ""
            snippet  = n['finding'][:100] + ('…' if len(n['finding']) > 100 else '')
            print(f"  {C.YELLOW}!{C.RESET}  {dim(year_tag + author)}{C.WHITE}{snippet}{C.RESET}")

    if all_notes:
        print(f"  {dim(f'Background notes: {len(all_notes)} (not prompt-affecting)')}")

    print()


def print_prompt_box(prompt_text: str) -> None:
    """Word-wrap and box the final prompt in bright white with a bold border."""
    border_top    = f"  {C.BOLD_CYAN}┌{'─' * 62}┐{C.RESET}"
    border_bottom = f"  {C.BOLD_CYAN}└{'─' * 62}┘{C.RESET}"
    print(border_top)
    words, line = prompt_text.split(), ""
    lines = []
    for word in words:
        if len(line) + len(word) + 1 > 60:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    for l in lines:
        print(f"  {C.BOLD_CYAN}│{C.RESET}  {C.BRIGHT_WHITE}{l:<60}{C.RESET}{C.BOLD_CYAN}│{C.RESET}")
    print(border_bottom)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactively build a Midjourney dinosaur art prompt."
    )
    parser.add_argument("--db",       type=Path,  default=DB_DEFAULT, metavar="PATH")
    # --version intentionally removed: set MJ model version in Midjourney settings
    parser.add_argument("--style",    default="raw",  choices=["raw", "default"], help="--style flag (default: raw)")
    # --ar intentionally removed: set aspect ratio globally in Midjourney settings
    parser.add_argument("--stylize",  type=int,   default=100,  metavar="N",   help="--stylize 0-1000 (default: 100)")
    parser.add_argument("--chaos",    type=int,   default=0,    metavar="N",   help="--chaos 0-100 (default: 0)")
    parser.add_argument("--quality",  type=float, default=1.0,  choices=[0.25, 0.5, 1.0], help="--q (default: 1.0)")
    parser.add_argument("--sref",     type=str,   default=None, metavar="URL", help="Style reference image URL appended as --sref")
    parser.add_argument("--cref",     type=str,   default=None, metavar="URL", help="Character reference image URL appended as --cref")
    args = parser.parse_args()

    conn = connect(args.db)
    global_rules = fetch_global_rules(conn)

    # --- Startup banner ---
    print(f"\n{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}DINOSAUR ART PROMPT GENERATOR{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")

    # --- Startup: reference image scan ---
    display_reference_scan()

    # --- Mode selection (first thing the user sees) ---
    output_mode = select_mode()
    mode_cfg    = OUTPUT_MODES[output_mode]

    placement: tuple[str, str] = ("", "")
    if mode_cfg["needs_placement"]:
        placement = select_canvas_placement()

    # --- Species ---
    species = pick_species(conn)
    science = fetch_species_science(conn, species["id"])
    notes   = fetch_research_notes(conn, species["id"])
    display_science_brief(species, science, notes)

    required_params = fetch_species_required_params(conn, species["id"])
    if required_params:
        sname = species["name"]
        nrp   = len(required_params)
        print(f"\n  {ok(f'AUTO-APPLIED — {nrp} required parameter(s) for {sname}')}:")
        for rp in required_params:
            cat, pname = rp["category"], rp["name"]
            print(f"    {ok('+')} {dim(f'[{cat}]')} {C.WHITE}{pname}{C.RESET}")
    if mode_cfg["full_body"] and species["name"] in CANVAS_SPECIES_EXTRAS:
        sname = species["name"]
        extra_preview = CANVAS_SPECIES_EXTRAS[sname][:80]
        print(f"  {ok('AUTO-APPLIED')} {dim(f'(full-body extras for {sname})')}:")
        print(f"    {ok('+')} {dim('[anatomy]')} {C.WHITE}{extra_preview}{C.RESET}")

    # Style is always hyperrealism — hardcoded, not user-selectable
    style_param    = HYPERREALISM_STYLE
    lighting_param = pick_parameter(conn, "lighting")

    # Camera: only ask if the mode doesn't fix its own camera
    if mode_cfg["fixed_camera"] is None:
        camera_param = pick_parameter(conn, "camera", name_only=True)
    else:
        camera_param = None
        mode_display = mode_cfg["display"]
        cam_preview  = mode_cfg["fixed_camera"][:80]
        print(f"  {hdr('CAMERA')} {dim(f'(fixed for {mode_display})')}")
        print(f"  {dim(cam_preview)}\n")

    mood_param      = pick_parameter(conn, "mood")
    condition_param = pick_parameter(conn, "condition")
    behavior_param  = pick_parameter(conn, "behavior", name_only=True)
    weather_param   = pick_parameter(conn, "weather")

    # --- Build prompt ---
    prompt_text = assemble_prompt(
        species, science, style_param, lighting_param, camera_param, mood_param,
        condition_param=condition_param,
        behavior_param=behavior_param,
        weather_param=weather_param,
        required_params=required_params,
        global_rules=global_rules,
        mj_style=args.style,
        stylize=args.stylize,
        chaos=args.chaos,
        quality=args.quality,
        output_mode=output_mode,
        placement=placement,
        has_sref=bool(args.sref),
    )

    title = make_title(species, mood_param, output_mode=output_mode)
    tags  = make_tags(species, style_param, lighting_param, camera_param, mood_param,
                      condition_param=condition_param, behavior_param=behavior_param,
                      weather_param=weather_param, output_mode=output_mode)

    # --- Append reference URLs to prompt ---
    if args.sref:
        prompt_text += f" --sref {args.sref}"
    if args.cref:
        prompt_text += f" --cref {args.cref}"

    # --- Build fix prompts ---
    habitat = species["habitat"] or "terrestrial"
    period  = species["period"] or "Other"
    if habitat in ("marine", "aerial"):
        env_key     = f"{habitat}_{period}"
        environment = ENVIRONMENTS.get(env_key, ENVIRONMENTS.get(f"{habitat}_Other", ENVIRONMENTS["Other"]))
    else:
        environment = ENVIRONMENTS.get(period, ENVIRONMENTS["Other"])

    feet_fix_prompt = make_feet_fix_prompt(species, mj_style=args.style)
    env_fix_prompt  = make_environment_fix_prompt(
        species, environment, weather_param, lighting_param, mj_style=args.style
    )

    # --- Display ---
    mode_label = mode_cfg["display"].upper()

    # STEP 1 — Main prompt
    print(f"\n{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}STEP 1 — MAIN PROMPT{C.RESET}  {C.DIM}[{mode_label}]{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"\n  {C.WHITE}Title :{C.RESET} {C.BRIGHT_WHITE}{title}{C.RESET}")
    print(f"  {C.WHITE}Tags  :{C.RESET} {dim(tags)}")
    if args.sref:
        print(f"  {C.WHITE}sref  :{C.RESET} {dim(args.sref)}")
    if args.cref:
        print(f"  {C.WHITE}cref  :{C.RESET} {dim(args.cref)}")
    print()
    validate_prompt(prompt_text, allow_mj_params=True,  label="STEP 1 main")
    print_prompt_box(prompt_text)
    print(f"\n  {hdr('/imagine prompt:')}")
    print(f"  {C.BRIGHT_WHITE}{prompt_text}{C.RESET}\n")

    # STEP 2 — Feet fix
    feet_fix_clean = strip_mj_params(feet_fix_prompt)
    validate_prompt(feet_fix_clean, allow_mj_params=False, label="STEP 2 feet fix")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}STEP 2 — FEET FIX{C.RESET}  {C.DIM}[Vary Region → paint over feet]{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print_prompt_box(feet_fix_clean)
    print(f"\n  {hdr('/imagine prompt:')}")
    print(f"  {C.BRIGHT_WHITE}{feet_fix_clean}{C.RESET}\n")

    # STEP 3 — Environment fix
    env_fix_clean = strip_mj_params(env_fix_prompt)
    validate_prompt(env_fix_clean, allow_mj_params=False, label="STEP 3 environment fix")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}STEP 3 — ENVIRONMENT FIX{C.RESET}  {C.DIM}[Vary Region → paint over background]{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print_prompt_box(env_fix_clean)
    print(f"\n  {hdr('/imagine prompt:')}")
    print(f"  {C.BRIGHT_WHITE}{env_fix_clean}{C.RESET}\n")

    # --- Save ---
    saved_param_ids = (
        [rp["id"] for rp in required_params]
        + [HYPERREALISM_STYLE["id"], lighting_param["id"], mood_param["id"],
           condition_param["id"], behavior_param["id"], weather_param["id"]]
        + ([camera_param["id"]] if camera_param else [])
    )
    prompt_id = save_prompt(
        conn,
        species_id=species["id"],
        title=title,
        positive_prompt=prompt_text,
        tags=tags,
        parameter_ids=saved_param_ids,
    )
    print(f"  {ok(f'✓ Saved — prompt id={prompt_id}, status=pending')}")
    print()


if __name__ == "__main__":
    main()
