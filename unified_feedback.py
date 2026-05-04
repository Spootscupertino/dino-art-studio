#!/usr/bin/env python3
"""
Unified MJ Feedback — paste prompt → rate → learn → insights.

Usage:
  python3 unified_feedback.py <image_path>
  python3 unified_feedback.py --history [--species NAME]
  python3 unified_feedback.py --winners
  python3 unified_feedback.py --trends SPECIES
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    import optuna
    import optuna.distributions as optuna_dist
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

DB_DEFAULT = Path(__file__).parent / "dino_art.db"
OPTUNA_DB  = Path(__file__).parent / "optuna_studies.db"
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

# Categorical choices for Optuna — must stay consistent across trials per study.
AR_CHOICES     = ["1:1", "3:2", "2:3", "4:3", "3:4", "16:9", "9:16", "other"]
STYLE_CHOICES  = ["raw", "default", "cute", "expressive", "scenic", "other"]


# ─── Color palette ──────────────────────────────────────────────────────────────

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    TEAL   = "\033[96m"
    BLUE   = "\033[94m"
    DBLUE  = "\033[34m"
    WHITE  = "\033[97m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"

    @staticmethod
    def teal(s):   return f"{C.TEAL}{s}{C.RESET}"
    @staticmethod
    def blue(s):   return f"{C.BLUE}{s}{C.RESET}"
    @staticmethod
    def bold(s):   return f"{C.BOLD}{s}{C.RESET}"
    @staticmethod
    def dim(s):    return f"{C.DIM}{s}{C.RESET}"
    @staticmethod
    def green(s):  return f"{C.GREEN}{s}{C.RESET}"
    @staticmethod
    def yellow(s): return f"{C.YELLOW}{s}{C.RESET}"
    @staticmethod
    def red(s):    return f"{C.RED}{s}{C.RESET}"
    @staticmethod
    def header(s): return f"{C.BOLD}{C.TEAL}{s}{C.RESET}"


# ─── DB helpers ─────────────────────────────────────────────────────────────────

FEEDBACK_DDL = """
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
    mj_prompt           TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


def get_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_table(conn: sqlite3.Connection):
    conn.execute(FEEDBACK_DDL)
    # Add mj_prompt column to existing DBs that predate this field.
    try:
        conn.execute("ALTER TABLE feedback_sessions ADD COLUMN mj_prompt TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.commit()


# ─── Terminal helpers ────────────────────────────────────────────────────────────

WIDTH = 62


def hr(char="─", color=C.TEAL):
    print(f"{color}{char * WIDTH}{C.RESET}")


def section(title: str):
    hr()
    print(f"  {C.BOLD}{C.BLUE}{title}{C.RESET}")
    hr()


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
            print(f"  {C.YELLOW}Enter a number 1–10.{C.RESET}")
        except ValueError:
            print(f"  {C.YELLOW}Enter a number 1–10.{C.RESET}")

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
    return answer.startswith("y") if answer else default_yes


def render_bar(score: int, width: int = 10) -> str:
    return f"{C.TEAL}{'█' * score}{C.RESET}{C.DBLUE}{'░' * (width - score)}{C.RESET}"


def score_color(score: float) -> str:
    if score >= 8:   return C.GREEN
    if score >= 6:   return C.TEAL
    if score >= 4:   return C.YELLOW
    return C.RED


# ─── Prompt parsing ─────────────────────────────────────────────────────────────

SPECIES_KEYS = [
    "tyrannosaurus rex", "tyrannosaurus", "t-rex", "triceratops", "stegosaurus",
    "velociraptor", "carnotaurus", "dilophosaurus", "brachiosaurus", "allosaurus",
    "spinosaurus", "apatosaurus", "iguanodon", "parasaurolophus", "ankylosaurus",
    "pachycephalosaurus", "deinonychus", "utahraptor", "diplodocus", "gallimimus",
    "oviraptor", "therizinosaurus", "compsognathus", "dimetrodon", "smilodon",
    "mammoth", "pteranodon", "quetzalcoatlus", "archaeopteryx", "rhamphorhynchus",
    "pterodactyl", "pterodactylus", "pterosaur", "dimorphodon", "liopleurodon",
    "ammonite", "plesiosaurus", "mosasaurus", "ichthyosaurus", "megalodon",
    "elasmosaurus", "kronosaurus", "pliosaurus", "dunkleosteus", "nautilus",
    "anomalocaris", "meganeura", "arthropleura", "pulmonoscorpius", "eurypterus",
    "helicoprion", "xiphactinus", "cretoxyrhina", "archelon",
]


def extract_species_from_prompt(text: str, conn: Optional[sqlite3.Connection] = None) -> Optional[str]:
    """Try DB species table first, then built-in list."""
    haystack = text.lower()

    if conn:
        try:
            rows = conn.execute(
                "SELECT name FROM species ORDER BY LENGTH(name) DESC"
            ).fetchall()
            for row in rows:
                if row["name"].lower() in haystack:
                    return row["name"]
        except sqlite3.OperationalError:
            pass

    for key in sorted(SPECIES_KEYS, key=len, reverse=True):
        if key in haystack:
            return key.replace("-", " ").title()

    return None


def extract_mj_flags(text: str) -> Dict[str, str]:
    flags = {}

    m = re.search(r"--stylize\s+(\d+)", text)
    if m:
        flags["stylize"] = m.group(1)

    m = re.search(r"--chaos\s+(\d+)", text)
    if m:
        flags["chaos"] = m.group(1)

    m = re.search(r"--ar\s+([\d:]+)", text)
    if m:
        flags["aspect_ratio"] = m.group(1)

    m = re.search(r"--quality\s+([\d.]+)", text)
    if m:
        flags["quality"] = m.group(1)

    m = re.search(r"--sref\s+(\S+)", text)
    if m:
        flags["sref"] = m.group(1)

    m = re.search(r"--style\s+(\w+)", text)
    if m:
        flags["style"] = m.group(1)

    m = re.search(r"--niji\s+(\d+)|--v\s+([\d.]+)", text)
    if m:
        flags["mj_version"] = f"niji {m.group(1)}" if m.group(1) else m.group(2)

    return flags


def paste_prompt() -> str:
    """Read a multi-line prompt paste; end on blank line."""
    print(f"\n  {C.BLUE}Paste the MJ prompt:{C.RESET} {C.DIM}(blank line to finish){C.RESET}")
    lines = []
    while True:
        try:
            line = input("  ")
            if not line.strip():
                if lines:
                    break
            else:
                lines.append(line)
        except EOFError:
            break
    return "\n".join(lines).strip()


# ─── Vision analysis ─────────────────────────────────────────────────────────────

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


def targeted_followup(dimension: str, vision: Optional[str]) -> str:
    if not vision:
        return FOLLOWUP_HINTS[dimension]

    kw_map = {
        "anatomy":     ["wrist", "tail", "posture", "proportion", "limb", "joint", "spine", "neck", "bent", "dragging"],
        "accuracy":    ["skull", "feather", "spine", "teeth", "claw", "finger", "build", "wrong", "missing", "extra"],
        "realism":     ["texture", "plastic", "smear", "blur", "lighting", "shadow", "artifact", "noise", "mush"],
        "composition": ["cut off", "crop", "frame", "centered", "angle", "awkward", "perspective"],
    }

    v = vision.lower()
    for kw in kw_map.get(dimension, []):
        if kw in v:
            return f"Vision noted '{kw}' — is that the issue? {FOLLOWUP_HINTS[dimension]}"

    return FOLLOWUP_HINTS[dimension]


# ─── Scoring ─────────────────────────────────────────────────────────────────────

def compute_final_score(scores: Dict[str, int]) -> float:
    return round(sum(scores[k] * w for k, _, _, w in DIMENSIONS), 2)


# ─── Optuna integration ──────────────────────────────────────────────────────────

def optuna_log(species: str, mj_flags: Dict[str, str], final_score: float) -> bool:
    """Log a completed trial to the per-species Optuna study. Returns True on success."""
    if not OPTUNA_AVAILABLE or not mj_flags:
        return False

    study_name = re.sub(r"[^a-z0-9]+", "_", species.lower()).strip("_")
    storage    = f"sqlite:///{OPTUNA_DB}"

    try:
        study = optuna.create_study(
            study_name=study_name,
            storage=storage,
            direction="maximize",
            load_if_exists=True,
        )

        params = {}
        dists  = {}

        if "stylize" in mj_flags:
            try:
                params["stylize"] = int(mj_flags["stylize"])
                dists["stylize"]  = optuna_dist.IntDistribution(0, 1000)
            except ValueError:
                pass

        if "chaos" in mj_flags:
            try:
                params["chaos"] = int(mj_flags["chaos"])
                dists["chaos"]  = optuna_dist.IntDistribution(0, 100)
            except ValueError:
                pass

        if "aspect_ratio" in mj_flags:
            ar = mj_flags["aspect_ratio"]
            if ar not in AR_CHOICES:
                ar = "other"
            params["aspect_ratio"] = ar
            dists["aspect_ratio"]  = optuna_dist.CategoricalDistribution(AR_CHOICES)

        if "style" in mj_flags:
            st = mj_flags["style"]
            if st not in STYLE_CHOICES:
                st = "other"
            params["style"] = st
            dists["style"]  = optuna_dist.CategoricalDistribution(STYLE_CHOICES)

        if not params:
            return False

        trial = optuna.trial.create_trial(
            params=params,
            distributions=dists,
            value=final_score,
        )
        study.add_trial(trial)
        return True

    except Exception:
        return False


def optuna_show_best(species: str) -> bool:
    """Print best params from the Optuna study for this species."""
    if not OPTUNA_AVAILABLE:
        return False

    study_name = re.sub(r"[^a-z0-9]+", "_", species.lower()).strip("_")
    storage    = f"sqlite:///{OPTUNA_DB}"

    try:
        study  = optuna.load_study(study_name=study_name, storage=storage)
        trials = [t for t in study.trials if t.value is not None]
        if len(trials) < 2:
            return False

        best = study.best_trial
        avg  = sum(t.value for t in trials) / len(trials)

        print(f"\n  {C.BLUE}Optuna Study: {C.teal(species)} {C.dim(f'({len(trials)} trials)')}{C.RESET}")
        print(f"  {C.DBLUE}{'─' * 50}{C.RESET}")
        print(f"    {C.dim('Best score')}: {C.green(f'{best.value:.1f}')}{C.dim('/10')}")
        print(f"    {C.dim('Avg score')} : {score_color(avg)}{avg:.1f}{C.RESET}{C.dim('/10')}")
        print(f"    {C.dim('Best params')}:")
        for k, v in best.params.items():
            print(f"      {C.blue(f'{k:<16}')} {C.teal(str(v))}")

        return True
    except Exception:
        return False


# ─── DB trends (fallback / supplement to Optuna) ─────────────────────────────────

def show_trends_inline(conn: sqlite3.Connection, species: str):
    """Show top MJ params from feedback_sessions for this species (DB-based)."""
    rows = conn.execute(
        """
        SELECT mj_params, COUNT(*) as n, AVG(final_score) as avg, MAX(final_score) as best
        FROM feedback_sessions
        WHERE species LIKE ? AND is_usable = 1 AND mj_params IS NOT NULL
        GROUP BY mj_params
        ORDER BY avg DESC
        LIMIT 5
        """,
        (f"%{species}%",),
    ).fetchall()

    if not rows:
        return

    print(f"\n  {C.BLUE}Top winning param sets for {C.teal(species)}:{C.RESET}")
    print(f"  {C.DBLUE}{'─' * 50}{C.RESET}")
    for row in rows:
        try:
            flags = json.loads(row["mj_params"])
        except (json.JSONDecodeError, TypeError):
            continue
        flag_str = "  ".join(f"{k}={v}" for k, v in flags.items() if k != "sref")
        sc = row["avg"]
        n  = row["n"]
        print(f"    {score_color(sc)}{sc:.1f}{C.RESET}{C.dim('/10')}  {C.dim(f'(×{n})')}  {C.teal(flag_str)}")


# ─── Main interview flow ──────────────────────────────────────────────────────────

def run_interview(image_path: str, db_path: Path):
    conn = get_db(db_path)
    ensure_table(conn)

    # Header
    banner([
        C.header("🦕  MJ FEEDBACK"),
        f"{C.dim('image')}  {C.teal(Path(image_path).name)}",
    ])

    # ── Step 1: Paste the MJ prompt ─────────────────────────────────────────────
    section("STEP 1 — MJ PROMPT")
    mj_prompt = paste_prompt()

    if not mj_prompt:
        print(f"  {C.dim('No prompt entered — continuing without prompt analysis.')}\n")
        mj_flags  = {}
        species   = None
    else:
        mj_flags = extract_mj_flags(mj_prompt)
        species  = extract_species_from_prompt(mj_prompt, conn)

        print()
        if species:
            print(f"  {C.green('✓')} Species detected: {C.teal(species)}")
        if mj_flags:
            flag_line = "  ".join(f"{k}={v}" for k, v in mj_flags.items())
            print(f"  {C.green('✓')} Flags: {C.teal(flag_line)}")
        elif mj_prompt:
            print(f"  {C.dim('No MJ flags detected in prompt.')}")

    # ── Step 2: Confirm species ──────────────────────────────────────────────────
    print()
    if not species:
        raw = input(f"  {C.BLUE}What species was this intended to be?{C.RESET}  ").strip()
        species = raw or "Unknown"
    else:
        if not ask_yes(f"Species: '{C.teal(species)}' — correct?"):
            raw = input(f"  {C.BLUE}Correct species:{C.RESET} ").strip()
            if raw:
                species = raw

    # ── Step 3: Vision analysis ──────────────────────────────────────────────────
    vision = None
    if OLLAMA_AVAILABLE:
        print(f"\n  {C.dim('Analyzing with llama3.2-vision...')}")
        vision = analyze_with_vision(image_path, species)
        if vision:
            section("VISION ANALYSIS")
            for sentence in vision.strip().split(". "):
                s = sentence.strip().rstrip(".")
                if s:
                    print(f"  {C.teal('•')} {s}.")
        else:
            print(f"  {C.yellow('⚠')}  Vision failed — is {C.dim('ollama serve')} running?\n")
    else:
        print(f"  {C.dim('ℹ  Ollama not installed — skipping vision analysis')}")

    # ── Step 4: Rating interview ─────────────────────────────────────────────────
    section("STEP 2 — RATE (1-10 each)")
    print(f"  {C.dim('Scores below 7 trigger a follow-up question.')}\n")

    scores:      Dict[str, int] = {}
    all_issues:  List[str]      = []
    all_strengths: List[str]    = []

    for key, label, description, _w in DIMENSIONS:
        print(f"\n  {C.BOLD}{C.TEAL}[{label}]{C.RESET}  {C.dim(description)}")
        hint  = targeted_followup(key, vision)
        score, notes = ask_score(label, hint)
        scores[key] = score

        if notes:
            all_issues.append(f"{label}: {notes}")
        if score >= 8:
            strength = input(
                f"  {C.TEAL}What works well here?{C.RESET} {C.dim('(Enter to skip)')}: "
            ).strip()
            if strength:
                all_strengths.append(f"{label}: {strength}")

    # ── Step 5: Score summary ────────────────────────────────────────────────────
    final   = compute_final_score(scores)
    usable  = final >= USABLE_THRESHOLD
    sc      = score_color(final)

    print()
    hr("═")
    verdict = C.green("✓  USABLE  (≥ 8)") if usable else C.red("✗  NOT USABLE  (< 8)")
    print(f"\n  {C.dim('FINAL SCORE')}  {C.BOLD}{sc}{final:.1f}{C.RESET}{C.dim('/10')}   {verdict}\n")

    for key, label, _, _ in DIMENSIONS:
        bar = render_bar(scores[key])
        col = score_color(scores[key])
        print(f"    {C.blue(f'{label:<20}')} {bar}  {col}{scores[key]}{C.RESET}{C.dim('/10')}")

    if all_issues:
        print(f"\n  {C.YELLOW}ISSUES:{C.RESET}")
        for issue in all_issues:
            print(f"    {C.yellow('•')} {issue}")

    if all_strengths:
        print(f"\n  {C.TEAL}STRENGTHS:{C.RESET}")
        for s in all_strengths:
            print(f"    {C.teal('✓')} {s}")

    print()
    hr("═")

    # ── Step 6: Save ─────────────────────────────────────────────────────────────
    if not ask_yes("Save this feedback?"):
        print(f"  {C.dim('Discarded.')}\n")
        return

    conn.execute(
        """
        INSERT INTO feedback_sessions
            (image_path, species, score_anatomy, score_accuracy,
             score_realism, score_composition, final_score, is_usable,
             issues, strengths, vision_analysis, mj_params, mj_prompt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            image_path, species or None,
            scores["anatomy"], scores["accuracy"], scores["realism"], scores["composition"],
            final, int(usable),
            json.dumps(all_issues)   if all_issues    else None,
            json.dumps(all_strengths) if all_strengths else None,
            vision,
            json.dumps(mj_flags) if mj_flags else None,
            mj_prompt or None,
        ),
    )
    conn.commit()
    session_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(f"\n  {C.teal('✓')} Saved as feedback session {C.bold(f'#{session_id}')}")

    # ── Step 7: Optuna logging ───────────────────────────────────────────────────
    if mj_flags:
        logged = optuna_log(species, mj_flags, final)
        if logged:
            print(f"  {C.teal('✓')} Optuna trial logged for {C.bold(species)}")
        elif not OPTUNA_AVAILABLE:
            print(f"  {C.dim('ℹ  pip install optuna to enable study tracking')}")

    # Archive winners
    if usable and ask_yes("Archive to results table?"):
        conn.execute(
            "INSERT OR IGNORE INTO results (prompt_id, image_path, rating) VALUES (?, ?, ?)",
            (None, image_path, min(5, round(final / 2))),
        )
        conn.commit()
        print(f"  {C.green('✓')} Archived.")

    # ── Step 8: Species insights ─────────────────────────────────────────────────
    section(f"INSIGHTS — {species.upper()}")
    shown_optuna = optuna_show_best(species)
    show_trends_inline(conn, species)
    if not shown_optuna and not OPTUNA_AVAILABLE:
        print(f"  {C.dim('Tip: pip install optuna for per-species parameter optimization.')}")
    print()


# ─── History / winners / trends views ───────────────────────────────────────────

def show_history(db_path: Path, species_filter: Optional[str]):
    conn = get_db(db_path)
    ensure_table(conn)

    q      = "SELECT * FROM feedback_sessions"
    params: list = []
    if species_filter:
        q += " WHERE species LIKE ?"
        params.append(f"%{species_filter}%")
    q += " ORDER BY final_score DESC, created_at DESC"

    rows = conn.execute(q, params).fetchall()
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


def show_trends(db_path: Path, species: str, category_filter: Optional[str]):
    conn = get_db(db_path)
    ensure_table(conn)

    prompts = conn.execute(
        """
        SELECT DISTINCT prompts.id, feedback_sessions.final_score
        FROM feedback_sessions
        JOIN prompts ON feedback_sessions.prompt_id = prompts.id
        WHERE feedback_sessions.species LIKE ? AND feedback_sessions.final_score >= 8
        ORDER BY feedback_sessions.final_score DESC
        """,
        (f"%{species}%",),
    ).fetchall()

    banner([C.header(f"📊  TRENDS: {species}") + f"  {C.dim(f'({len(prompts)} winning prompts)')}"])

    if not prompts:
        print(f"  {C.dim(f'No winning prompts in DB for \"{species}\".')}")
    else:
        param_stats: Dict[str, dict] = {}
        for p in prompts:
            params = conn.execute(
                """
                SELECT parameters.category, parameters.value
                FROM prompt_parameters
                JOIN parameters ON prompt_parameters.parameter_id = parameters.id
                WHERE prompt_parameters.prompt_id = ?
                """,
                (p["id"],),
            ).fetchall()
            for param in params:
                key = f"{param['category']}:{param['value']}"
                if key not in param_stats:
                    param_stats[key] = {"category": param["category"], "value": param["value"], "wins": 0, "total": 0.0}
                param_stats[key]["wins"]  += 1
                param_stats[key]["total"] += p["final_score"]

        by_cat: Dict[str, list] = {}
        for stats in param_stats.values():
            cat = stats["category"]
            stats["avg"] = round(stats["total"] / stats["wins"], 2)
            by_cat.setdefault(cat, []).append(stats)

        for cat in sorted(by_cat.keys()):
            if category_filter and category_filter.lower() != cat.lower():
                continue
            print(f"\n  {C.BOLD}{C.BLUE}{cat.title()}{C.RESET}")
            print(f"  {C.DBLUE}{'─' * 50}{C.RESET}")
            for s in sorted(by_cat[cat], key=lambda x: x["wins"], reverse=True)[:10]:
                bar = f"{C.TEAL}{'█' * min(20, s['wins'] * 2)}{C.RESET}"
                val = s["value"]
                print(f"    {C.teal(f'{val:<25}')} {s['wins']:2d} wins (avg {s['avg']:.1f})  {bar}")

    # Always show Optuna best if available
    optuna_show_best(species)
    hr()


# ─── Entry point ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Unified MJ feedback: paste prompt → rate → learn → insights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 unified_feedback.py path/to/trex.png
  python3 unified_feedback.py --history
  python3 unified_feedback.py --history --species trex
  python3 unified_feedback.py --winners
  python3 unified_feedback.py --trends velociraptor
        """,
    )
    parser.add_argument("image",    nargs="?", help="Path to the image to review")
    parser.add_argument("--db",     default=str(DB_DEFAULT), help="SQLite DB path")
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--species", "-s", help="Filter history by species")
    parser.add_argument("--winners", action="store_true")
    parser.add_argument("--trends",  metavar="SPECIES")
    parser.add_argument("--category", help="Filter --trends by parameter category")

    args    = parser.parse_args()
    db_path = Path(args.db)

    if args.history:
        show_history(db_path, args.species)
    elif args.winners:
        show_winners(db_path)
    elif args.trends:
        show_trends(db_path, args.trends, args.category)
    elif args.image:
        path = Path(args.image)
        if not path.exists():
            print(f"{C.RED}Error:{C.RESET} not found: {args.image}", file=sys.stderr)
            sys.exit(1)
        run_interview(str(path.resolve()), db_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
