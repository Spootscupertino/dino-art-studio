#!/usr/bin/env python3
"""
caption_draft.py — draft anatomy-only training captions from images using a local vision model via Ollama.

Run this on the 2016 Intel MBP or the M1 mini. Drafts are saved as `<stem>.draft.txt`
next to each image. The `caption-polisher` subagent then polishes drafts into final captions.

Usage:
    ollama pull llava:13b                              # one-time setup
    python3 tools/caption_draft.py --folder assets/staging/tyrannosaurus/v5_mouth_macro
    python3 tools/caption_draft.py --folder <path> --model llama3.2-vision:11b
    python3 tools/caption_draft.py --folder <path> --overwrite           # redo existing drafts

The prompt to the local vision model enforces anatomy-only output by listing
the strip-words in the system prompt. Caption-polisher still rewrites — Ollama
drafts are seeds, not finals.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SYSTEM_PROMPT = """You are drafting anatomical training captions for a dinosaur LoRA.

RULES (strict):
- Describe ONLY what is anatomically visible in the image.
- Use scientific terms when applicable (manus, ungual, metatarsal, supraorbital, rostrum, etc).
- NEVER include lighting words (cinematic, dramatic, studio, golden hour, moody).
- NEVER include environment (forest, white background, mist, mud).
- NEVER include style words (photorealistic, hyper-realistic, 8K, high resolution, highly detailed).
- NEVER include aesthetic adjectives (beautiful, menacing, stunning, epic).
- NEVER include camera language (depth of field, bokeh, macro lens).
- Output ONE long sentence, ~80-150 words, comma-separated clauses.
- Lead with species + view type, then cascade anatomy from prominent to subtle.
- If you cannot identify a structure with confidence, leave it out.

Output the caption only. No preamble, no quotes, no explanation."""

USER_PROMPT_TEMPLATE = """Image is a reference for category: {category}
Species: {species}

Draft the anatomy caption per the rules."""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", required=True, help="folder of images to caption")
    parser.add_argument("--model", default="llava:13b", help="ollama model tag")
    parser.add_argument("--overwrite", action="store_true", help="redo even if draft exists")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_absolute():
        folder = REPO_ROOT / folder
    if not folder.exists():
        sys.exit(f"Folder does not exist: {folder}")

    # Infer species and category from path: training_refs/<species>/<category>/
    parts = folder.parts
    try:
        species = parts[parts.index("training_refs") + 1] if "training_refs" in parts else parts[-2]
        category = folder.name
    except (ValueError, IndexError):
        species = "unknown"
        category = folder.name

    # TODO(v6): implement Ollama HTTP call to localhost:11434/api/generate
    # TODO(v6): handle base64-encoded image input per Ollama vision-model spec
    # TODO(v6): write <stem>.draft.txt for each image

    print(f"[stub] Would draft captions for {folder}")
    print(f"[stub] Species={species}, category={category}, model={args.model}")
    print(f"[stub] Ollama endpoint: http://localhost:11434/api/generate")
    print()
    print("Not yet implemented. v6 work item.")
    print("Interface contract:")
    print("  - Reads each .{png,jpg,jpeg,webp} in folder")
    print("  - Sends to Ollama vision model with the strict anatomy-only system prompt")
    print("  - Writes <stem>.draft.txt next to each image")
    print("  - caption-polisher subagent reads .draft.txt + the image, writes final <stem>.txt")


if __name__ == "__main__":
    main()
