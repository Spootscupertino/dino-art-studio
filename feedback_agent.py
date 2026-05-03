#!/usr/bin/env python3
"""
MJ Feedback Agent — terminal interview for rating Midjourney dinosaur art.

Usage:
  python feedback_agent.py <image_path> [--species NAME] [--prompt-id ID]
  python feedback_agent.py --history [--species NAME]
  python feedback_agent.py --winners

Requires Ollama + llama3.2-vision for auto image analysis (optional):
  brew install ollama
  ollama pull llama3.2-vision
  pip install ollama
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

DB_DEFAULT = Path(__file__).parent / "dino_art.db"
VISION_MODEL = "llama3.2-vision"

DIMENSIONS: List[Tuple[str, str, str, float]] = [
    ("anatomy",     "Anatomy",          "Proportions, posture, limbs, key features",  0.35),
    ("accuracy",    "Species accuracy", "Does it match the intended species?",         0.25),
    ("realism",     "Realism/quality",  "Texture, lighting, detail, no AI mush",      0.25),
    ("composition", "Composition",      "Framing, perspective, focal point, balance",  0.15),
]

FOLLOWUP_HINTS = {
    "anatomy":     "e.g. bent wrists, dragging tail, wrong proportions, bad posture",
    "accuracy":    "e.g. wrong skull shape, missing feathers, extra fingers, wrong build",
    "realism":     "e.g. smeared textures, plastic look, weird lighting, blurry areas",
    "composition": "e.g. limbs cut off, too centered, awkward angle, bad framing",
}

USABLE_THRESHOLD = 8.0
WEIGHT_DELTA = 0.05

FEEDBACK_TABLE = """
CREATE TABLE IF NOT EXISTS feedback_sessions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    image_path          TEXT NOT NULL,
    species             TEXT,
    prompt_id           INTEGER REFERENCES prompts(id) ON DELETE SET NULL,
    score_anatomy       INTEGER CHECK(score_anatomy BETWEEN 1 AND 10),
    score_accuracy      INTEGER CHECK(score_accuracy BETWEEN 1 AND 10),
    score_realism       INTEGER CHECK(score_realism BETWEEN 1 AND 10),
    score_composition   INTEGER CHECK(score_composition BETWEEN 1 AND 10),
    final_score         REAL NOT NULL,
    is_usable           INTEGER NOT NULL DEFAULT 0,
    issues              TEXT,
    strengths           TEXT,
    vision_analysis     TEXT,
    mj_params           TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


# ─── Color palette ─────────────────────────────────────────────────────────────

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    TEAL    = "\033[96m"   # bright cyan  — headers, borders, bar fills
    BLUE    = "\033[94m"   # bright blue  — labels, prompts, section titles
    DBLUE   = "\033[34m"   # dark blue    — bar empties, secondary text
    WHITE   = "\033[97m"   # bright white — regular text
    GREEN   = "\033[92m"   # bright green — ✓ winner / usable
    YELLOW  = "\033[93m"   # yellow       — issues / warnings
    RED     = "\033[91m"   # red          — ✗ not usable

    @staticmethod
    def teal(s: str) -> str:   return f"{C.TEAL}{s}{C.RESET}"
    @staticmethod
    def blue(s: str) -> str:   return f"{C.BLUE}{s}{C.RESET}"
    @staticmethod
    def bold(s: str) -> str:   return f"{C.BOLD}{s}{C.RESET}"
    @staticmethod
    def dim(s: str) -> str:    return f"{C.DIM}{s}{C.RESET}"
    @staticmethod
    def green(s: str) -> str:  return f"{C.GREEN}{s}{C.RESET}"
    @staticmethod
    def yellow(s: str) -> str: return f"{C.YELLOW}{s}{C.RESET}"
    @staticmethod
    def red(s: str) -> str:    return f"{C.RED}{s}{C.RESET}"
    @staticmethod
    def header(s: str) -> str: return f"{C.BOLD}{C.TEAL}{s}{C.RESET}"


# ─── DB helpers ────────────────────────────────────────────────────────────────

def get_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_table(conn: sqlite3.Connection):
    conn.execute(FEEDBACK_TABLE)
    conn.commit()


# ─── Terminal helpers ───────────────────────────────────────────────────────────

WIDTH = 62

def hr(char: str = "─", color: str = C.TEAL):
    print(f"{color}{char * WIDTH}{C.RESET}")


def section(title: str):
    hr("─")
    print(f"  {C.BOLD}{C.BLUE}{title}{C.RESET}")
    hr("─")


def banner(lines: List[str]):
    hr("═")
    for line in lines:
        print(f"  {line}")
    hr("═")


def ask_score(label: str, hint: str) -> Tuple[int, str]:
    while True:
        raw = input(f"  {C.BLUE}{label}{C.RESET} {C.DIM}[1-10]{C.RESET}: ").strip()
        try:
            score = int(raw)
            if 1 <= score <= 10:
                break
            print(f"  {C.YELLOW}Please enter a number between 1 and 10.{C.RESET}")
        except ValueError:
            print(f"  {C.YELLOW}Please enter a number between 1 and 10.{C.RESET}")

    notes = ""
    if score < 7:
        notes = input(
            f"  {C.YELLOW}What's wrong?{C.RESET} {C.DIM}({hint}){C.RESET}\n"
            f"  {C.TEAL}›{C.RESET} "
        ).strip()

    return score, notes


def ask_yes(prompt: str, default_yes: bool = True) -> bool:
    suffix = C.dim("[Y/n]") if default_yes else C.dim("[y/N]")
    answer = input(f"  {C.BLUE}{prompt}{C.RESET} {suffix}: ").strip().lower()
    if answer == "":
        return default_yes
    return answer.startswith("y")


def render_score_bar(score: int, width: int = 10) -> str:
    filled = f"{C.TEAL}{'█' * score}{C.RESET}"
    empty  = f"{C.DBLUE}{'░' * (width - score)}{C.RESET}"
    return filled + empty


# ─── Vision analysis ───────────────────────────────────────────────────────────

def analyze_with_vision(image_path: str, species: Optional[str]) -> Optional[str]:
    if not OLLAMA_AVAILABLE:
        return None

    species_ctx = f" intended to depict a {species}" if species else ""
    prompt = (
        f"You are a paleontological art critic reviewing AI-generated dinosaur art{species_ctx}. "
        "Analyze this image and briefly note: "
        "1) What species appears to be depicted, "
        "2) Any obvious anatomical issues (posture, limb proportions, distinctive features), "
        "3) Overall realism and image quality, "
        "4) Composition strengths or weaknesses. "
        "Be specific. 3-5 sentences total."
    )

    try:
        response = ollama.chat(
            model=VISION_MODEL,
            messages=[{"role": "user", "content": prompt, "images": [image_path]}],
        )
        return response["message"]["content"]
    except Exception:
        return None


# ─── Scoring ───────────────────────────────────────────────────────────────────

def compute_final_score(scores: Dict[str, int]) -> float:
    return round(sum(scores[key] * weight for key, _, _, weight in DIMENSIONS), 2)


def score_color(score: float) -> str:
    if score >= 8:
        return C.GREEN
    if score >= 6:
        return C.TEAL
    if score >= 4:
        return C.YELLOW
    return C.RED


# ─── Weight self-training ──────────────────────────────────────────────────────

def update_parameter_weights(conn: sqlite3.Connection, prompt_id: int, direction: int):
    delta = WEIGHT_DELTA * direction
    rows = conn.execute(
        "SELECT parameter_id FROM prompt_parameters WHERE prompt_id = ?", (prompt_id,)
    ).fetchall()

    for row in rows:
        conn.execute(
            "UPDATE parameters SET weight = MAX(0.0, MIN(2.0, weight + ?)) WHERE id = ?",
            (delta, row["parameter_id"]),
        )

    if rows:
        conn.commit()
        verb = C.green("↑ increased") if direction > 0 else C.yellow("↓ decreased")
        print(f"\n  Parameter weights {verb} for {C.bold(str(len(rows)))} parameters linked to this prompt.")


# ─── Interview ─────────────────────────────────────────────────────────────────

def run_interview(image_path: str, species: Optional[str], prompt_id: Optional[int], db_path: Path):
    conn = get_db(db_path)
    ensure_table(conn)

    # Header
    meta = [C.header("🦕  MJ FEEDBACK AGENT")]
    meta.append(f"{C.dim('image  ')} {C.teal(Path(image_path).name)}")
    if species:
        meta.append(f"{C.dim('species')} {C.teal(species)}")
    if prompt_id:
        meta.append(f"{C.dim('prompt ')} {C.teal(f'#{prompt_id}')}")
    banner(meta)

    # Vision analysis
    vision_analysis = None
    if OLLAMA_AVAILABLE:
        print(f"\n  {C.dim('Analyzing image with llama3.2-vision...')}")
        vision_analysis = analyze_with_vision(image_path, species)
        if vision_analysis:
            section("VISION ANALYSIS")
            for line in vision_analysis.strip().split(". "):
                line = line.strip().rstrip(".")
                if line:
                    print(f"  {C.teal('•')} {line}.")
            print()
        else:
            print(f"  {C.yellow('⚠')}  Vision analysis failed — check {C.dim('ollama serve')} is running\n")
    else:
        print(f"  {C.dim('ℹ  Ollama not installed — skipping vision analysis')}\n")

    # Confirm species
    if not species:
        species = input(f"  {C.BLUE}What species was this intended to be?{C.RESET}  ").strip()
    else:
        if not ask_yes(f"Species is '{C.teal(species)}' — correct?"):
            species = input(f"  {C.BLUE}Correct species:{C.RESET} ").strip()

    # Interview loop
    print(f"\n  {C.dim('Rate each dimension 1–10.  Scores below 7 trigger a follow-up.')}\n")
    hr()

    scores: Dict[str, int] = {}
    all_issues: List[str] = []
    all_strengths: List[str] = []

    for key, label, description, _weight in DIMENSIONS:
        print(f"\n  {C.BOLD}{C.TEAL}[{label}]{C.RESET}  {C.dim(description)}")
        score, notes = ask_score(label, FOLLOWUP_HINTS[key])
        scores[key] = score

        if notes:
            all_issues.append(f"{label}: {notes}")
        if score >= 8:
            strength = input(
                f"  {C.TEAL}What works well here?{C.RESET} {C.dim('(Enter to skip)')}: "
            ).strip()
            if strength:
                all_strengths.append(f"{label}: {strength}")

    # Results
    final_score = compute_final_score(scores)
    is_usable   = final_score >= USABLE_THRESHOLD
    sc          = score_color(final_score)

    print()
    hr("═")
    verdict = C.green("✓  USABLE  (8+)") if is_usable else C.red("✗  NOT USABLE  (< 8)")
    print(f"\n  {C.dim('FINAL SCORE')}  {C.BOLD}{sc}{final_score:.1f}{C.RESET}{C.dim('/10')}   {verdict}\n")

    for key, label, _, _ in DIMENSIONS:
        bar = render_score_bar(scores[key])
        s   = scores[key]
        col = score_color(s)
        print(f"    {C.blue(f'{label:<20}')} {bar}  {col}{s}{C.RESET}{C.dim('/10')}")

    if all_issues:
        print(f"\n  {C.YELLOW}ISSUES:{C.RESET}")
        for issue in all_issues:
            print(f"    {C.yellow('•')} {issue}")

    if all_strengths:
        print(f"\n  {C.TEAL}STRENGTHS:{C.RESET}")
        for strength in all_strengths:
            print(f"    {C.teal('✓')} {strength}")

    print()
    hr("═")

    if not ask_yes("Save this feedback?"):
        print(f"  {C.dim('Discarded.')}\n")
        return

    # Optional MJ params
    mj_params: Dict[str, str] = {}
    if ask_yes("Log MJ generation params? (stylize/chaos/ar/version)", default_yes=False):
        for param in ["mj_version", "stylize", "chaos", "aspect_ratio", "sref"]:
            val = input(f"    {C.dim(param)}: ").strip()
            if val:
                mj_params[param] = val

    # Write to DB
    conn.execute(
        """
        INSERT INTO feedback_sessions
            (image_path, species, prompt_id,
             score_anatomy, score_accuracy, score_realism, score_composition,
             final_score, is_usable, issues, strengths, vision_analysis, mj_params)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            image_path, species or None, prompt_id,
            scores["anatomy"], scores["accuracy"], scores["realism"], scores["composition"],
            final_score, int(is_usable),
            json.dumps(all_issues) if all_issues else None,
            json.dumps(all_strengths) if all_strengths else None,
            vision_analysis,
            json.dumps(mj_params) if mj_params else None,
        ),
    )
    conn.commit()
    session_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(f"\n  {C.teal('✓')} Saved as feedback session {C.bold(f'#{session_id}')}")

    # Self-training
    if prompt_id:
        if is_usable:
            update_parameter_weights(conn, prompt_id, +1)
        elif final_score <= 4:
            update_parameter_weights(conn, prompt_id, -1)

    # Archive winners
    if is_usable and prompt_id:
        if ask_yes("Archive this as a winner in the results table?"):
            conn.execute(
                "INSERT OR IGNORE INTO results (prompt_id, image_path, rating) VALUES (?, ?, ?)",
                (prompt_id, image_path, min(5, round(final_score / 2))),
            )
            conn.commit()
            print(f"  {C.green('✓')} Archived to results table.")

    print()


# ─── History / winners views ───────────────────────────────────────────────────

def show_history(db_path: Path, species_filter: Optional[str]):
    conn = get_db(db_path)
    ensure_table(conn)

    query = "SELECT * FROM feedback_sessions"
    params: list = []
    if species_filter:
        query += " WHERE species LIKE ?"
        params.append(f"%{species_filter}%")
    query += " ORDER BY final_score DESC, created_at DESC"

    rows = conn.execute(query, params).fetchall()
    if not rows:
        print(f"  {C.dim('No feedback sessions found.')}")
        return

    banner([C.header(f"📋  FEEDBACK HISTORY  ({len(rows)} sessions)")])

    for row in rows:
        sc   = score_color(row["final_score"])
        mark = C.green("✓") if row["is_usable"] else C.red("✗")
        sp   = (row["species"] or "unknown")[:20]
        date = C.dim(row["created_at"][:10])
        num  = C.dim(f"#{row['id']:3d}")
        print(f"  {num}  {mark}  {sc}{row['final_score']:4.1f}{C.RESET}{C.dim('/10')}  {C.blue(f'{sp:<20}')}  {date}")
        if row["issues"]:
            for issue in json.loads(row["issues"])[:2]:
                print(f"           {C.yellow('↳')} {C.dim(issue)}")

    hr()


def show_winners(db_path: Path):
    conn = get_db(db_path)
    ensure_table(conn)

    rows = conn.execute(
        "SELECT * FROM feedback_sessions WHERE is_usable = 1 ORDER BY final_score DESC"
    ).fetchall()

    if not rows:
        print(f"  {C.dim('No winners yet — need final_score ≥ 8.')}")
        return

    banner([C.header(f"🏆  WINNERS  (score ≥ 8)  —  {len(rows)} images")])

    for row in rows:
        sp    = (row["species"] or "unknown")[:20]
        fname = Path(row["image_path"]).name[:28]
        sc    = score_color(row["final_score"])
        print(f"  {sc}{C.BOLD}{row['final_score']:4.1f}{C.RESET}{C.dim('/10')}  {C.teal(f'{sp:<20}')}  {C.dim(fname)}")
        if row["strengths"]:
            for s in json.loads(row["strengths"])[:1]:
                print(f"                {C.green('✓')} {C.dim(s)}")

    hr()


# ─── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="MJ Feedback Agent — interview-style rating for Midjourney dinosaur art",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python feedback_agent.py path/to/trex.png
  python feedback_agent.py path/to/trex.png --species "T-rex" --prompt-id 42
  python feedback_agent.py --history
  python feedback_agent.py --history --species trex
  python feedback_agent.py --winners
        """,
    )
    parser.add_argument("image", nargs="?", help="Path to image file to review")
    parser.add_argument("--species", "-s", help="Intended species name")
    parser.add_argument("--prompt-id", "-p", type=int, help="Linked prompt ID from dino_art.db")
    parser.add_argument("--db", default=str(DB_DEFAULT), help="Path to SQLite database")
    parser.add_argument("--history", action="store_true", help="Show past feedback sessions")
    parser.add_argument("--winners", action="store_true", help="Show winning images (score ≥ 8)")

    args = parser.parse_args()
    db_path = Path(args.db)

    if args.history:
        show_history(db_path, args.species)
    elif args.winners:
        show_winners(db_path)
    elif args.image:
        if not Path(args.image).exists():
            print(f"{C.red('Error:')} image not found: {args.image}", file=sys.stderr)
            sys.exit(1)
        run_interview(str(Path(args.image).resolve()), args.species, args.prompt_id, db_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
