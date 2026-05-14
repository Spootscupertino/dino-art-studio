#!/usr/bin/env python3
"""
Blind-scoring CLI for the frozen eval harness.

Shows each image (via `open`) with LoRA identity hidden behind a hash.
You score on the 5-axis anatomy rubric (1–5 each, max 25).
After all scores are committed for a session, reveals which LoRA made what.
Persists scores to flux/eval/scores.json.

Rubric axes:
  proportions  — horizontal spine, tiny forelimbs, massive head, raised tail,
                 appropriate skull depth for binocular vision
  hands        — two-fingered manus, strongly recurved claws, medially-facing palm
  feet         — three weight-bearing toes, digitigrade stance, large recurved claws
  mouth_teeth  — lipped jaw, recurved serrated teeth, exposed gumline, tongue/palate
  integument   — mosaic polygon scales, no trunk feathers on adult, appropriate
                 colour/texture

Usage:
  python3 flux/eval/score.py                          # score any unscored images
  python3 flux/eval/score.py --lora trex_v3           # score one LoRA
  python3 flux/eval/score.py --leaderboard            # print score summary
  python3 flux/eval/score.py --reveal                 # reveal all hashes → LoRA names
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = REPO_ROOT / "assets" / "gallery" / "flux" / "evals"
PROMPTS_PATH = Path(__file__).parent / "prompts.json"
SCORES_PATH = Path(__file__).parent / "scores.json"
REGISTRY_PATH = REPO_ROOT / "flux" / "loras" / "registry.json"

AXES = ["proportions", "hands", "feet", "mouth_teeth", "integument"]


def load_scores() -> list[dict]:
    if SCORES_PATH.exists():
        return json.loads(SCORES_PATH.read_text())
    return []


def save_scores(scores: list[dict]):
    SCORES_PATH.write_text(json.dumps(scores, indent=2))


def blind_hash(lora: str) -> str:
    return hashlib.sha1(lora.encode()).hexdigest()[:8]


def open_image(path: Path):
    """Open image in default viewer (macOS `open`, Linux `xdg-open`)."""
    cmd = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([cmd, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def score_one(image_path: Path, lora: str, prompt_id: str, seed: int, scorer: str) -> dict | None:
    """Interactive scoring session for one image. Returns score dict or None if skipped."""
    token = blind_hash(lora)
    print(f"\n{'─'*60}")
    print(f"  Prompt : {prompt_id}")
    print(f"  Seed   : {seed}")
    print(f"  Source : [hidden — {token}]")
    print(f"  File   : {image_path.relative_to(REPO_ROOT)}")
    print(f"{'─'*60}")
    open_image(image_path)

    scores = {}
    for axis in AXES:
        while True:
            raw = input(f"  {axis:12s} (1–5, 0=not visible, Enter=skip image): ").strip()
            if raw == "":
                print("  Skipped.")
                return None
            try:
                v = int(raw)
                if v == 0:
                    scores[axis] = None  # not visible in this image
                    print("  Not visible — excluded from axis average.")
                    break
                if 1 <= v <= 5:
                    scores[axis] = v
                    break
                print("  Enter 1–5 (or 0 if not visible).")
            except ValueError:
                print("  Enter a number.")

    notes = input("  Notes (optional): ").strip()
    total = sum(v for v in scores.values() if v is not None)
    return {
        "lora": lora,
        "lora_token": token,
        "prompt_id": prompt_id,
        "seed": seed,
        "scorer": scorer,
        "scored_at": datetime.now().isoformat(timespec="seconds"),
        "image_path": str(image_path.relative_to(REPO_ROOT)),
        "scores": scores,
        "total": total,
        "notes": notes,
    }


def already_scored(scores: list[dict], lora: str, prompt_id: str, seed: int, scorer: str) -> bool:
    return any(
        s["lora"] == lora and s["prompt_id"] == prompt_id
        and s["seed"] == seed and s["scorer"] == scorer
        for s in scores
    )


def find_images(lora_filter: str | None) -> list[tuple[str, Path, str, int]]:
    """Return list of (lora, image_path, prompt_id, seed) tuples."""
    results = []
    if not EVAL_DIR.exists():
        return results
    prompts = {p["id"]: p for p in json.loads(PROMPTS_PATH.read_text())}
    for lora_dir in sorted(EVAL_DIR.iterdir()):
        if not lora_dir.is_dir():
            continue
        lora = lora_dir.name
        if lora_filter and lora != lora_filter:
            continue
        for png in sorted(lora_dir.glob("*.png")):
            # filename: <prompt_id>_seed_<NNNN>.png
            parts = png.stem.rsplit("_seed_", 1)
            if len(parts) != 2:
                continue
            prompt_id, seed_str = parts
            if prompt_id not in prompts:
                continue
            try:
                seed = int(seed_str)
            except ValueError:
                continue
            results.append((lora, png, prompt_id, seed))
    return results


def _bar(val: float, max_val: float = 5.0, width: int = 10) -> str:
    filled = round((val / max_val) * width)
    return "█" * filled + "░" * (width - filled)


def _medal(rank: int) -> str:
    return ["🥇", "🥈", "🥉", " 4"][min(rank, 3)]


def _trend(val: float, baseline: float) -> str:
    delta = val - baseline
    if abs(delta) < 0.05:
        return "  —  "
    return f" +{delta:.1f}" if delta > 0 else f" {delta:.1f}"


def print_leaderboard(scores: list[dict]):
    if not scores:
        print("No scores yet.")
        return
    from collections import defaultdict
    by_lora: dict[str, list] = defaultdict(list)
    for s in scores:
        by_lora[s["lora"]].append(s)

    rows = []
    for lora, entries in by_lora.items():
        n = len(entries)
        mean = sum(e["total"] for e in entries) / n
        axis_means = {}
        for axis in AXES:
            vals = [e["scores"][axis] for e in entries if e["scores"].get(axis) is not None]
            axis_means[axis] = sum(vals) / len(vals) if vals else 0.0
        rows.append((mean, lora, n, axis_means))
    rows.sort(reverse=True)

    baseline_mean = next((m for m, l, _, _ in rows if l == "baseline"), None)
    baseline_axes = next((a for m, l, _, a in rows if l == "baseline"), {})

    AXIS_ICONS = {
        "proportions": "📐",
        "hands":       "🤏",
        "feet":        "🦶",
        "mouth_teeth": "🦷",
        "integument":  "🐊",
    }

    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║              J U R A S S I N K A R T   E V A L   B O A R D          ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")

    for rank, (mean, lora, n, axis_means) in enumerate(rows):
        pct = (mean / 25) * 100
        overall_bar = _bar(mean, max_val=25, width=16)
        trend = _trend(mean, baseline_mean) if lora != "baseline" else "  base"
        medal = _medal(rank)

        print(f"║                                                                      ║")
        print(f"║  {medal}  {lora:<12}  {overall_bar}  {mean:4.1f}/25  ({pct:4.1f}%)  {trend}     ║")
        print(f"║      n={n}  ──────────────────────────────────────────────────────  ║")

        for axis in AXES:
            v = axis_means.get(axis, 0.0)
            bar = _bar(v, max_val=5.0, width=12)
            icon = AXIS_ICONS[axis]
            at = _trend(v, baseline_axes.get(axis, v)) if lora != "baseline" else ""
            print(f"║        {icon} {axis:<12}  {bar}  {v:.1f}  {at:<6}                 ║")

    print(f"║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(f"  Scored by: {scores[0]['scorer'] if scores else '?'}   |"
          f"  Max possible: 25/25  |  Axes scored 1–5 (0 = not visible)")
    print()


def print_reveal(scores: list[dict]):
    tokens = {s["lora_token"]: s["lora"] for s in scores}
    print("\nToken → LoRA reveal:")
    for token, lora in sorted(tokens.items()):
        print(f"  {token}  →  {lora}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Blind-score eval images")
    parser.add_argument("--lora", help="Only score this LoRA")
    parser.add_argument("--leaderboard", action="store_true", help="Print score leaderboard")
    parser.add_argument("--reveal", action="store_true", help="Reveal token → LoRA mapping")
    parser.add_argument("--scorer", default=os.environ.get("USER", "scorer"), help="Your name/handle")
    args = parser.parse_args()

    scores = load_scores()

    if args.leaderboard:
        print_leaderboard(scores)
        return

    if args.reveal:
        print_reveal(scores)
        return

    images = find_images(args.lora)
    if not images:
        if EVAL_DIR.exists():
            print(f"No eval images found in {EVAL_DIR}.")
            print("Run: python3 flux/eval/run.py")
        else:
            print(f"Eval directory not found: {EVAL_DIR}")
            print("Run: python3 flux/eval/run.py")
        return

    pending = [
        (lora, img, pid, seed)
        for lora, img, pid, seed in images
        if not already_scored(scores, lora, pid, seed, args.scorer)
    ]

    if not pending:
        print(f"All {len(images)} images already scored by '{args.scorer}'.")
        print("Run with --leaderboard to see results.")
        return

    print(f"Scoring session: {len(pending)} images to score (scorer: {args.scorer})")
    print("Rubric: proportions / hands / feet / mouth_teeth / integument  (1–5 each, max 25)")
    print("Press Enter on any axis to skip the whole image.\n")

    session_scores = []
    for i, (lora, img, pid, seed) in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}]", end="")
        result = score_one(img, lora, pid, seed, args.scorer)
        if result:
            session_scores.append(result)
            scores.append(result)
            save_scores(scores)
            print(f"  Saved. Total: {result['total']}/25")

    print(f"\n✓ Session complete. Scored {len(session_scores)}/{len(pending)} images.")

    if session_scores:
        print("\nReveal: run `python3 flux/eval/score.py --reveal` to see token → LoRA mapping.")
        print("Leaderboard: run `python3 flux/eval/score.py --leaderboard`")


if __name__ == "__main__":
    main()
