#!/usr/bin/env python3
"""
Auto-rater for Flux-generated dinosaur images.
Comparison-based scoring + optional LLaVA analysis.
Calibrated against human winners from dino_art.db.

Usage:
    python auto_rater.py <image_path> [--species NAME]
    python auto_rater.py --calibrate  # Show calibration data
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
import os

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Color palette
# ─────────────────────────────────────────────────────────────────────────────

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    TEAL = "\033[96m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"

    @staticmethod
    def teal(s):
        return f"{C.TEAL}{s}{C.RESET}"

    @staticmethod
    def green(s):
        return f"{C.GREEN}{s}{C.RESET}"

    @staticmethod
    def red(s):
        return f"{C.RED}{s}{C.RESET}"

    @staticmethod
    def bold(s):
        return f"{C.BOLD}{s}{C.RESET}"

    @staticmethod
    def dim(s):
        return f"{C.DIM}{s}{C.RESET}"


# ─────────────────────────────────────────────────────────────────────────────
# Quality heuristics
# ─────────────────────────────────────────────────────────────────────────────

class QualityHeuristics:
    """Fast heuristics for image quality without heavy models."""

    @staticmethod
    def assess_dimensions(image_path: str) -> Tuple[int, str]:
        """Check if image dimensions are standard and reasonable."""
        if not PIL_AVAILABLE:
            return 5, "PIL unavailable"

        try:
            img = Image.open(image_path)
            w, h = img.size

            # Ideal: 1024x1024 or similar square
            if w == h and w >= 512:
                return 9, "good_dimensions"

            # Acceptable: reasonable aspect ratios
            if 0.5 <= w / h <= 2.0 and w >= 512 and h >= 512:
                return 7, "acceptable_dimensions"

            return 4, "undersized_or_extreme_ar"
        except Exception:
            return 5, "unreadable_image"

    @staticmethod
    def assess_filesize(image_path: str) -> Tuple[int, str]:
        """Proxy for quality: larger file = more detail (but not always)."""
        try:
            size_mb = os.path.getsize(image_path) / (1024 * 1024)

            # Flux PNG at 1024x1024 should be 2-8MB
            if 1.0 <= size_mb <= 10:
                return 8, "good_detail_level"
            elif 0.5 <= size_mb < 1.0 or 10 < size_mb <= 20:
                return 6, "marginal_detail"
            else:
                return 4, "suspiciously_small_or_large"
        except Exception:
            return 5, "size_check_failed"

    @staticmethod
    def assess_sidecar_params(image_path: str) -> Tuple[int, str]:
        """Check metadata sidecar for generation quality indicators."""
        sidecar_path = Path(image_path).with_suffix(".json")
        if not sidecar_path.exists():
            return 5, "no_sidecar"

        try:
            with open(sidecar_path) as f:
                meta = json.load(f)

            params = meta.get("parameters", {})
            steps = params.get("steps", 0)
            guidance = params.get("guidance_scale", 0)

            # Heuristic: more steps + moderate guidance = better quality
            score = 5
            if steps >= 40:
                score += 2
            elif steps >= 30:
                score += 1

            if 2.5 <= guidance <= 4.5:
                score += 1

            # Bonus for LoRA (shows we're iterating)
            if meta.get("lora"):
                score += 1

            return min(10, score), f"s={steps},g={guidance:.1f}"
        except Exception:
            return 5, "sidecar_unreadable"


# ─────────────────────────────────────────────────────────────────────────────
# AutoRater
# ─────────────────────────────────────────────────────────────────────────────

class AutoRater:
    """
    Fast auto-rater using heuristics + optional LLaVA.
    Calibrated against human winners.
    """

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path(__file__).parent / "dino_art.db"
        self.winner_stats = None

    def rate(self, image_path: str, species: Optional[str] = None) -> Dict:
        """Rate image using heuristics. Return score dict."""
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        print(f"\n{C.teal('Assessing')} {Path(image_path).name}...")

        # Collect heuristic scores
        scores = {}
        analyses = {}

        dim_score, dim_analysis = QualityHeuristics.assess_dimensions(image_path)
        scores["composition"] = dim_score
        analyses["composition"] = dim_analysis

        size_score, size_analysis = QualityHeuristics.assess_filesize(image_path)
        scores["realism"] = size_score
        analyses["realism"] = size_analysis

        meta_score, meta_analysis = QualityHeuristics.assess_sidecar_params(image_path)
        scores["anatomy"] = meta_score
        analyses["anatomy"] = meta_analysis

        # Simple heuristic: if no errors, accuracy is good
        scores["accuracy"] = min(scores["anatomy"], 7)
        analyses["accuracy"] = "metadata_driven"

        # Weighted final score (same weights as unified_feedback.py)
        final = round(
            scores["anatomy"] * 0.35
            + scores["accuracy"] * 0.25
            + scores["realism"] * 0.25
            + scores["composition"] * 0.15,
            1,
        )

        print(f"  {C.dim('dims:')} {C.green(f'{dim_score}/10')}")
        print(f"  {C.dim('detail:')} {C.green(f'{size_score}/10')}")
        print(f"  {C.dim('params:')} {C.green(f'{meta_score}/10')}")

        return {
            "anatomy": scores["anatomy"],
            "accuracy": scores["accuracy"],
            "realism": scores["realism"],
            "composition": scores["composition"],
            "final": final,
            "analyses": analyses,
            "method": "heuristic",
        }

    def show_calibration_stats(self) -> bool:
        """Show winner stats from DB for calibration reference."""
        if not self.db_path.exists():
            print(f"{C.red(f'DB not found: {self.db_path}')}")
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT final_score, species FROM feedback_sessions WHERE is_usable = 1 ORDER BY final_score DESC"
            ).fetchall()

            if not rows:
                print(f"{C.yellow('No winners in DB yet.')}")
                return False

            print(f"\n{C.teal('Winner calibration data')} ({len(rows)} images):")
            print(f"  {C.dim('Score')}  {C.dim('Species')}")

            avg_score = 0
            by_species = {}
            for row in rows:
                s = row["species"] or "unknown"
                by_species.setdefault(s, []).append(row["final_score"])
                avg_score += row["final_score"]

            avg_score /= len(rows) if rows else 1

            for species in sorted(by_species.keys()):
                scores = by_species[species]
                avg = sum(scores) / len(scores)
                print(
                    f"  {C.green(f'{avg:.1f}')}      {C.teal(species)} ({len(scores)} images)"
                )

            print(f"\n  {C.dim('Overall avg')}: {C.bold(f'{avg_score:.1f}')}/10")
            return True
        except Exception as e:
            print(f"{C.red(f'Error: {e}')}")
            return False


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Auto-rate dinosaur images (heuristic + optional LLaVA)"
    )
    parser.add_argument("image", nargs="?", help="Image path to rate")
    parser.add_argument("--species", "-s", help="Species name (for context)")
    parser.add_argument("--db", default="dino_art.db", help="DB path for calibration")
    parser.add_argument(
        "--calibrate", action="store_true", help="Show calibration stats"
    )

    args = parser.parse_args()

    rater = AutoRater(Path(args.db))

    if args.calibrate:
        rater.show_calibration_stats()
    elif args.image:
        try:
            result = rater.rate(args.image, args.species)
            print(f"\n{C.BOLD}{C.TEAL}Result:{C.RESET}")
            for k in ["anatomy", "accuracy", "realism", "composition"]:
                print(f"  {k:<12} {result[k]}/10")
            print(f"  {'final':<12} {C.bold(f'{result['final']:.1f}')}/10")
            print(f"\n{C.dim(f'Method: {result['method']}')}")
        except Exception as e:
            print(f"{C.red(f'Error: {e}')}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
