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

DB_DEFAULT = Path(__file__).parent / "dino_art.db"
SPECIES_REF_DIR = Path(__file__).parent / "species_reference"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".raw", ".cr2", ".cr3", ".arw", ".nef"}
OUTDATED_THRESHOLD = 2020  # flag species whose last_scientific_update is before this year

# Period → evocative environment phrase
ENVIRONMENTS = {
    "Triassic":   "arid Triassic floodplain, sparse conifer groves, early cycads and ferns",
    "Jurassic":   "lush Jurassic forest, towering conifers and giant tree ferns, morning mist",
    "Cretaceous": "Late Cretaceous river delta, flowering plants, open floodplain under vast sky",
    "Other":      "ancient prehistoric landscape, primordial terrain",
}

CATEGORIES = ["style", "lighting", "camera", "mood"]

# ---------------------------------------------------------------------------
# Canvas print mode constants
# ---------------------------------------------------------------------------

CANVAS_CAMERA = (
    "Canon EOS R5 24-70mm f/4, mid-range lens, full environmental context visible, "
    "not telephoto, wide enough to show habitat"
)

CANVAS_PRINT = (
    "high dynamic range, shadow detail preserved, highlight detail preserved, "
    "print-ready detail, no blown highlights"
)

# Species-specific additions that only apply in canvas print mode
CANVAS_SPECIES_EXTRAS = {
    "Velociraptor": (
        "full feathered body visible, sickle claw raised off ground, "
        "palms facing inward correct wrist anatomy, tail counterbalance extended"
    ),
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
        "SELECT id, name, common_name, period, size_class, description, notes FROM species ORDER BY name"
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
                  known_coloration_evidence, last_scientific_update
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
    print(f"\n  {label}")
    print("  " + "-" * 60)
    for i, row in enumerate(rows, 1):
        print(f"  {i:>2}.  {display_fn(row)}")
    print()
    while True:
        raw = input(f"  Choose 1–{len(rows)}: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(rows):
            return rows[int(raw) - 1]
        print(f"  Please enter a number between 1 and {len(rows)}.")


def select_mode() -> str:
    """Ask the user to choose between portrait close-up and canvas print mode.
    Returns 'portrait' or 'canvas'."""
    print("\n" + "=" * 64)
    print("  DINOSAUR ART PROMPT GENERATOR")
    print("=" * 64)
    print("\n  Select output mode")
    print("  " + "-" * 60)
    print("   1.  Portrait close-up      — telephoto, tight framing, mood-focused")
    print("   2.  Full body canvas print — mid-range, 60/40 negative space, print-ready")
    print()
    while True:
        raw = input("  Choose 1–2: ").strip()
        if raw in ("1", "2"):
            return "portrait" if raw == "1" else "canvas"
        print("  Please enter 1 or 2.")


def select_canvas_placement() -> tuple[str, str]:
    """Ask which side the animal sits on. Returns (subject_side, space_side).
    For dead-centre, returns ('dead_center', '') as a sentinel."""
    print("\n  Animal placement")
    print("  " + "-" * 60)
    print("   1.  Animal on left    — rule of thirds, negative space on right")
    print("   2.  Animal on right   — rule of thirds, negative space on left")
    print("   3.  Dead centre       — symmetrical, direct eye contact, camera trap")
    print()
    while True:
        raw = input("  Choose 1–3: ").strip()
        if raw == "1":
            return ("animal positioned left of centre", "right")
        if raw == "2":
            return ("animal positioned right of centre", "left")
        if raw == "3":
            return ("dead_center", "")
        print("  Please enter 1, 2, or 3.")


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


def pick_parameter(conn: sqlite3.Connection, category: str):
    rows = fetch_parameters_by_category(conn, category)
    if not rows:
        sys.exit(f"No parameters found for category '{category}'. Run setup_db.py.")

    label = f"Select {category.upper()} modifier"

    def fmt(r):
        weight_tag = f" [weight {r['weight']}]" if r["weight"] != 1.0 else ""
        return f"{r['name']:<22} — {r['value']}{weight_tag}"

    return pick(label, rows, fmt)


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

def assemble_prompt(
    species,
    style_param,
    lighting_param,
    camera_param,       # None in canvas mode (fixed camera used instead)
    mood_param,
    required_params: list,
    global_rules: list[str],
    mj_version: str,
    mj_style: str,
    ar: str,
    stylize: int,
    chaos: int,
    quality: float,
    canvas_mode: bool = False,
    canvas_placement: str = "",
    canvas_space_side: str = "",
) -> str:
    # --- Subject block ---
    size = species["size_class"].lower() if species["size_class"] else ""
    subject_parts = [f"{size} {species['name']}", species["description"] or ""]
    if species["notes"]:
        subject_parts.append(species["notes"])
    # Required anatomy/accuracy params (e.g. full_body_accuracy for Velociraptor)
    for rp in required_params:
        subject_parts.append(rp["value"])
    # Canvas mode: species-specific canvas extras + full-body framing requirement
    if canvas_mode:
        extra = CANVAS_SPECIES_EXTRAS.get(species["name"])
        if extra:
            subject_parts.append(extra)
        subject_parts.append("full body visible, entire animal head to tail tip in frame")
    subject_parts.append(style_param["value"])
    subject = ", ".join(p for p in subject_parts if p)

    # --- Environment ---
    environment = ENVIRONMENTS.get(species["period"] or "Other", ENVIRONMENTS["Other"])

    # --- Assemble prose ---
    prose_parts = [subject.strip(), environment]

    if canvas_mode:
        if canvas_placement == "dead_center":
            composition = (
                "animal perfectly centred in frame, symmetrical composition, "
                "direct eye contact, static alert pose, equal negative space on both sides, "
                "as if caught by a camera trap, horizon line visible"
            )
        else:
            composition = (
                f"60% frame occupation, 40% negative space, rule of thirds placement, "
                f"{canvas_placement}, negative space on {canvas_space_side} side, "
                f"horizon line visible"
            )
        prose_parts.append(composition)

    prose_parts.append(lighting_param["value"])

    if canvas_mode:
        prose_parts.append(f"shot on {CANVAS_CAMERA}")
        prose_parts.append(CANVAS_PRINT)
    else:
        prose_parts.append(f"shot on {camera_param['value']}")

    prose_parts.append(mood_param["value"])
    prose_parts.extend(global_rules)

    prose = ", ".join(prose_parts)

    # --- MJ flags ---
    flags = f"--v {mj_version} --style {mj_style} --ar {ar} --stylize {stylize} --q {quality:g}"
    if chaos > 0:
        flags += f" --chaos {chaos}"

    return f"{prose} {flags}"


def make_title(species, mood_param, canvas_mode: bool = False) -> str:
    name = species["common_name"] or species["name"]
    suffix = "canvas print" if canvas_mode else mood_param["name"].replace("_", " ")
    return f"{name} — {suffix}"


def make_tags(species, style_param, lighting_param, camera_param, mood_param,
              canvas_mode: bool = False) -> str:
    parts = []
    if species["period"]:
        parts.append(species["period"].lower())
    for p in (style_param, lighting_param, mood_param):
        parts.append(p["name"])
    parts.append("canvas_print" if canvas_mode else camera_param["name"])
    return ",".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def display_reference_scan() -> None:
    """Print a startup report of reference images loaded per species."""
    counts = scan_reference_images()
    if not counts:
        print("  [reference] species_reference/ folder not found — skipping image scan")
        return
    total = sum(counts.values())
    loaded = sum(1 for c in counts.values() if c > 0)
    print(f"\n  REFERENCE IMAGES  ({loaded}/{len(counts)} species have images, {total} total)")
    print("  " + "-" * 60)
    for folder, count in counts.items():
        display_name = folder.replace("_", " ").title()
        bar = "█" * min(count, 20)
        status = f"{count:>3} image{'s' if count != 1 else ' '}" if count else "  — no images yet"
        print(f"  {display_name:<22} {status}  {bar}")
    print()


def display_science_brief(species, science, notes: list) -> None:
    """Print a scientific summary and research notes for the selected species."""
    name = species["name"]
    print(f"\n  SCIENTIFIC BRIEF — {name}")
    print("  " + "─" * 60)

    if science and any(science):
        length = f"{science['body_length_m']}m" if science["body_length_m"] else "unknown"
        mass   = f"{science['body_mass_kg']:,.0f} kg" if science["body_mass_kg"] else "unknown"
        loco   = science["locomotion_type"] or "unknown"
        feather = science["feathering_coverage"] or "unknown"
        print(f"  Length: {length:<10} Mass: {mass:<14} Locomotion: {loco}")
        if science["skin_texture_type"]:
            print(f"  Skin:   {science['skin_texture_type']}")
        if science["feathering_coverage"]:
            print(f"  Feathering: {feather}")
        if science["tail_posture"]:
            print(f"  Tail posture: {science['tail_posture']}")
        if science["wrist_position"]:
            print(f"  Wrist: {science['wrist_position']}")

        update_year = science["last_scientific_update"]
        if update_year:
            flag = "  ⚠  POTENTIALLY OUTDATED — check for publications after 2020" if update_year < OUTDATED_THRESHOLD else ""
            print(f"  Last updated: {update_year}{flag}")

    prompt_notes = [n for n in notes if n["affects_prompt"]]
    all_notes    = [n for n in notes if not n["affects_prompt"]]

    if prompt_notes:
        print(f"\n  PROMPT-RELEVANT FINDINGS ({len(prompt_notes)}):")
        for n in prompt_notes:
            year_tag = f"[{n['year']}] " if n["year"] else ""
            author   = f"{n['author']} — " if n["author"] else ""
            print(f"    ! {year_tag}{author}{n['finding'][:100]}{'…' if len(n['finding']) > 100 else ''}")

    if all_notes:
        print(f"  Background notes: {len(all_notes)} (not prompt-affecting — use research_notes table to review)")

    print()


def print_prompt_box(prompt_text: str) -> None:
    """Word-wrap and box the prompt for easy reading."""
    print("  ┌" + "─" * 62 + "┐")
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
        print(f"  │  {l:<60}│")
    print("  └" + "─" * 62 + "┘")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactively build a Midjourney dinosaur art prompt."
    )
    parser.add_argument("--db",       type=Path,  default=DB_DEFAULT, metavar="PATH")
    parser.add_argument("--version",  default="6.1",  metavar="VER",  help="MJ model version (default: 6.1)")
    parser.add_argument("--style",    default="raw",  choices=["raw", "default"], help="--style flag (default: raw)")
    parser.add_argument("--ar",       default="3:2",  metavar="W:H",  help="Aspect ratio (default: 3:2)")
    parser.add_argument("--stylize",  type=int,   default=100,  metavar="N",   help="--stylize 0-1000 (default: 100)")
    parser.add_argument("--chaos",    type=int,   default=0,    metavar="N",   help="--chaos 0-100 (default: 0)")
    parser.add_argument("--quality",  type=float, default=1.0,  choices=[0.25, 0.5, 1.0], help="--q (default: 1.0)")
    args = parser.parse_args()

    conn = connect(args.db)
    global_rules = fetch_global_rules(conn)

    # --- Startup: reference image scan ---
    display_reference_scan()

    # --- Mode selection (first thing the user sees) ---
    mode = select_mode()
    canvas_mode = (mode == "canvas")

    canvas_placement = canvas_space_side = ""
    if canvas_mode:
        canvas_placement, canvas_space_side = select_canvas_placement()

    # --- Species ---
    species = pick_species(conn)
    science = fetch_species_science(conn, species["id"])
    notes   = fetch_research_notes(conn, species["id"])
    display_science_brief(species, science, notes)

    required_params = fetch_species_required_params(conn, species["id"])
    if required_params:
        print(f"\n  AUTO-APPLIED ({len(required_params)} required parameter(s) for {species['name']}):")
        for rp in required_params:
            print(f"    + [{rp['category']}] {rp['name']}")
    if canvas_mode and species["name"] in CANVAS_SPECIES_EXTRAS:
        print(f"  AUTO-APPLIED (canvas extras for {species['name']}):")
        print(f"    + [canvas] {CANVAS_SPECIES_EXTRAS[species['name']]}")

    # --- Style, lighting, mood (always picked) ---
    style_param    = pick_parameter(conn, "style")
    lighting_param = pick_parameter(conn, "lighting")

    # Camera is fixed in canvas mode; user picks in portrait mode
    if canvas_mode:
        camera_param = None
        print(f"\n  CAMERA (fixed for canvas print):")
        print(f"    {CANVAS_CAMERA}")
    else:
        camera_param = pick_parameter(conn, "camera")

    mood_param = pick_parameter(conn, "mood")

    # --- Build prompt ---
    prompt_text = assemble_prompt(
        species, style_param, lighting_param, camera_param, mood_param,
        required_params=required_params,
        global_rules=global_rules,
        mj_version=args.version,
        mj_style=args.style,
        ar=args.ar,
        stylize=args.stylize,
        chaos=args.chaos,
        quality=args.quality,
        canvas_mode=canvas_mode,
        canvas_placement=canvas_placement,
        canvas_space_side=canvas_space_side,
    )

    title = make_title(species, mood_param, canvas_mode=canvas_mode)
    tags  = make_tags(species, style_param, lighting_param, camera_param, mood_param,
                      canvas_mode=canvas_mode)

    # --- Display ---
    mode_label = "FULL BODY CANVAS PRINT" if canvas_mode else "PORTRAIT CLOSE-UP"
    print("\n" + "=" * 64)
    print(f"  GENERATED PROMPT  [{mode_label}]")
    print("=" * 64)
    print(f"\n  Title : {title}")
    print(f"  Tags  : {tags}\n")
    print_prompt_box(prompt_text)
    print(f"\n  /imagine prompt: {prompt_text}\n")

    # --- Save ---
    saved_param_ids = (
        [rp["id"] for rp in required_params]
        + [style_param["id"], lighting_param["id"], mood_param["id"]]
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
    print(f"  Saved to prompts table — id={prompt_id}, status=pending")
    print()


if __name__ == "__main__":
    main()
