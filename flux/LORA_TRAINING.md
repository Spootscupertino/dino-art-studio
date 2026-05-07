# LoRA Fine-Tuning Pipeline for Flux-dev

This guide walks through collecting scientifically accurate reference images, preparing a training dataset, and fine-tuning a LoRA model to improve dinosaur generation quality.

## The Three-Step Workflow

### Step 1: Collect & Interview Reference Images

**Command:**
```bash
python3 reference.py
```

This script handles batch intake of reference images with a guided interview:

1. **Drag-drop (or paste path)** — Add one or more images in a single session
2. **Species detection** — Auto-guesses from filename; you confirm or correct
3. **Source metadata** — URL/attribution and source type (paleoart, museum, living analog, wildlife)
4. **Anatomy review** — You describe what's anatomically accurate (tooth shape, claws, posture, etc.)
5. **Caveats** — Optional notes on inaccuracies or limitations
6. **LLaVA analysis** — Auto-runs if Ollama + llava are available
7. **Caption generation** — Creates `.txt` file: `"a photo of [species], [anatomy notes]"`
8. **Storage** — Copies image + caption to `assets/gallery/flux/training_refs/`
9. **Logging** — Records entry in `winners.json` with `source_type="reference"`

**Output:**
```
assets/gallery/flux/training_refs/
├── trex_20260505_123456_museum_photo.png
├── trex_20260505_123456_museum_photo.txt
├── velociraptor_20260505_234567_paleoart.png
├── velociraptor_20260505_234567_paleoart.txt
└── ...
```

Each `.txt` file contains: `"a photo of [species], [anatomy notes]"`

**Batch mode:**
The script asks "Add another image?" after each one, so you can intake multiple images without restarting.

---

### Step 2: Export Training Dataset

**Command:**
```bash
python3 flux/export_dataset.py
```

This script reads all reference images + captions and prepares them for ai-toolkit:

1. **Scans** `assets/gallery/flux/training_refs/` for `.png` + `.txt` pairs
2. **Filters** for reference images (checks `winners.json` for `source_type="reference"`)
3. **Creates** `flux/datasets/dino_refs/` with:
   - `images/` — symlinks to actual training data (no duplication)
   - `dataset.json` — metadata (species counts, captions, image paths)
   - `summary.txt` — human-readable report

**Output:**
```
flux/datasets/dino_refs/
├── images/
│   ├── trex_20260505_123456_museum_photo.png → ../../assets/gallery/flux/training_refs/...
│   ├── trex_20260505_123456_museum_photo.txt → ../../assets/gallery/flux/training_refs/...
│   ├── velociraptor_20260505_234567_paleoart.png → ...
│   ├── velociraptor_20260505_234567_paleoart.txt → ...
│   └── ...
├── dataset.json
└── summary.txt
```

**Example summary:**
```
LORA Training Dataset Summary
==================================================

Total images: 12
Unique species: 4

Breakdown by species:
  Tyrannosaurus rex: 5 images
  Velociraptor: 4 images
  Triceratops: 2 images
  Stegosaurus: 1 image

Dataset ready for ai-toolkit training:
  → Images (with captions): flux/datasets/dino_refs/images
  → Metadata: flux/datasets/dino_refs/dataset.json
```

---

### Step 3: Train LoRA with ai-toolkit

**Install ai-toolkit:**
```bash
# Clone the repo (or follow official instructions)
git clone https://github.com/ostris/ai-toolkit.git
cd ai-toolkit
pip install -r requirements.txt
```

**Point ai-toolkit at your dataset:**
```bash
# Example: ai-toolkit config.yaml should reference the images folder
# Edit config.yaml to point at:
#   dataset_path: /path/to/dino_art/flux/datasets/dino_refs/images/
# (ai-toolkit will find image + caption pairs automatically)

# Then run training (exact command depends on ai-toolkit version)
python train.py --config config.yaml
```

**Output:**
The trained LoRA will be saved to a `.safetensors` file. Place it in `flux/loras/`:
```bash
cp ~/ai-toolkit/output/dino_winners.safetensors flux/loras/
```

---

## Data Format

**Image files:**
- Format: PNG, JPG, WEBP (any standard image format)
- Location: `assets/gallery/flux/training_refs/`
- Naming: `{species}_{timestamp}_{original_filename}.{ext}`

**Caption files:**
- Format: Plain text (`.txt`)
- Location: Same folder as image (same base filename)
- Content: `"a photo of [species], [anatomy notes]"`
- Example: `a photo of Tyrannosaurus rex, massive 2-fingered hands, powerful hindquarters, correct tooth structure, balanced skull`

**Metadata:**
- `winners.json` — Stores full interview notes (anatomy analysis, caveats, source URL, LLaVA analysis)
- `dataset.json` — Export-time snapshot (species, image counts, training metadata)

---

## Workflow Integration

The reference images feed into the broader feedback loop:

```
reference.py (collect + interview)
       ↓
assets/gallery/flux/training_refs/ (+ .txt captions)
       ↓
winners.json (logged with source_type="reference")
       ↓
export_dataset.py (prepare for training)
       ↓
flux/datasets/dino_refs/images/ (ai-toolkit input)
       ↓
ai-toolkit (external training)
       ↓
flux/loras/dino_winners.safetensors
       ↓
flux/generate_image.py (load LoRA during generation)
       ↓
Better dinosaur anatomy → higher auto-rated scores → reinforce the loop
```

---

## Best Practices

### Collecting Reference Images

1. **Source diversity:** Mix paleoart, museum specimens, and living analogs (crocs, birds) for robustness
2. **Anatomy focus:** Prioritize images with clear tooth structure, claw morphology, posture, and proportions
3. **Attribution:** Always record source URL — helps with reproducibility and respects creators
4. **Accuracy notes:** Be specific in the interview (e.g., "sickle claw morphology on hind foot" vs. generic "looks good")

### Training Dataset

- **Minimum:** 5–10 reference images per species (more is better)
- **Balance:** Try to keep species representation balanced (avoid 1 species dominating)
- **Captions:** Keep them under 200 words; focus on anatomical features, not artistic style
- **Versioning:** Date-stamped filenames in `training_refs/` make it easy to track which images were used for which LoRA

### LoRA Hyperparameters (ai-toolkit)

Common starting values (adjust based on ai-toolkit docs):
- **Rank (r):** 8–16 (lower = smaller model, less memory)
- **Learning rate:** 1e-4 to 5e-5 (start lower for M1 memory)
- **Epochs:** 10–20 (more if dataset is small)
- **Batch size:** 1 (M1 constraint; increase on GPU if available)

---

## Troubleshooting

**"No reference images found"**
- Run `python3 reference.py` to add images first
- Check that `assets/gallery/flux/training_refs/` exists and contains `.png` + `.txt` pairs

**Missing caption files**
- Each image needs a matching `.txt` file with the same base name
- `reference.py` creates these automatically; check for errors during intake

**winners.json issues**
- Make sure `reference.py` successfully logged entries with `source_type="reference"`
- View `winners.json` to verify entries exist

**ai-toolkit training fails**
- Consult ai-toolkit documentation (https://github.com/ostris/ai-toolkit)
- Check that `dataset/images/` contains paired image + caption files
- Verify image paths are absolute or relative correctly in `dataset.json`

---

## Future Enhancements

- **Auto-caption from LLaVA:** Use vision analysis to auto-generate better captions
- **Anatomy validation:** Pre-check captions for anatomy keywords (claw, tooth, feather, etc.)
- **Multi-species LoRA:** Train a single LoRA across multiple species vs. species-specific models
- **LoRA versioning:** Tag trained models with dataset snapshot (date, species, image count)
- **Comparison metrics:** A/B test generated images with/without new LoRA to measure improvement
