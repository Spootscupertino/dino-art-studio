# Flux Domain — Local Image Generation

Owner: `prompt-crafter` (shared with mj domain for now, can split to dedicated agent)

## Goal
Generate photorealistic dinosaur images locally on M1 Mac mini using **Flux-dev** + **LoRA fine-tuning** + **ControlNet anatomy guidance**. Replace or complement Midjourney with quality-first local generation.

## What Lives Here

| File | Purpose |
|---|---|
| `generate_image.py` | Core image generation: Flux-dev + LoRA + ControlNet, M1-optimized |
| `train_lora.py` | Fine-tune LoRA on high-scoring winners from unified_feedback.py |
| `comfyui_server.py` | Headless ComfyUI server (teal/blue themed API) |
| `comfyui_ui/` | Branded ComfyUI frontend (teal + blue + complementary colors) |
| `requirements.txt` | M1-optimized PyTorch + diffusers dependencies |
| `loras/` | Trained LoRA models (`dino_winners.safetensors`, etc.) |
| `controlnets/` | ControlNet models for anatomy constraint (skeletal references) |

## Tech Stack

**Core generation:**
- Flux-dev (24GB model, M1 runs at ~bfloat16)
- Diffusers library (HuggingFace)
- LoRA for fine-tuning
- ControlNet for structural guidance

**M1 Optimization:**
- PyTorch Metal acceleration (native GPU backend)
- bfloat16 precision (saves memory, keeps quality)
- Attention optimization (xformers or native sdpa)
- Memory-mapped loading
- Inference in ~30–60 seconds per image

**UI:**
- ComfyUI headless server
- Custom teal/blue/complementary color theme
- REST API for integration with feedback loop

## Workflow Integration

**Feedback loop:**
```
unified_feedback.py rates image (8+ = winner)
  ↓
save_winner() stores to winners.json
  ↓
train_lora.py (runs on schedule or manually)
  → Reads winners from past 24 hours
  → Fine-tunes dino_winners.safetensors
  → Uploads to flux/loras/
  ↓
Next generation in ComfyUI loads updated LoRA
  → Better dinosaur anatomy
  → Loop tightens
```

**Output compatibility:**
- Images saved to `assets/gallery/<category>/<timestamp>.png`
- Same format as sync_gallery.py expects
- Directly compatible with printify-publisher (no format conversion)

## CLI Usage

### Generate a single image
```bash
python flux/generate_image.py \
  --prompt "a Tyrannosaurus rex in a river delta" \
  --lora dino_winners \
  --controlnet skeletal_anatomy \
  --seed 42 \
  --output assets/gallery/dinosaurs/tx_river_001.png
```

### Train LoRA on winners
```bash
python flux/train_lora.py \
  --winners winners.json \
  --species "Tyrannosaurus" \
  --output flux/loras/dino_winners.safetensors
```

### Start ComfyUI server
```bash
python flux/comfyui_server.py --port 8888 --theme teal_blue
# Open http://localhost:8888 in browser
```

## Contract with Other Domains

**Input:**
- `winners.json` (from unified_feedback.py) — high-scoring images to train on
- `generate_prompt.py` output — prompts that can be used locally
- `--sref` / `--cref` URLs (converted to local refs)

**Output:**
- `assets/gallery/<category>/*.png` — images ready for sync_gallery.py
- LoRA models in `flux/loras/` (can be versioned, shared)
- ComfyUI UI at http://localhost:8888 (visual feedback during iteration)

## M1 Performance Target

- **Flux-dev generation:** ~45 seconds per image (bfloat16, attention optimization)
- **LoRA training:** ~10 min per 10-image batch on winners
- **Memory usage:** ~22–23GB peak (leaves 1–2GB headroom)

## Philosophy

**Local-first, not MJ-first:**
- Flux is now the primary generator
- Fast iteration: adjust prompts, parameters, LoRA weights live in ComfyUI
- Optuna optimizes parameters locally instead of guessing at MJ
- MJ becomes optional comparison tool ("how does this match MJ quality?")
- Winners train better LoRA → next generation is better → compound improvement

**Generator as the star agent:**
- This domain owns image generation quality
- Specialized in dinosaur anatomy via LoRA
- Can experiment with ControlNets, samplers, schedulers
- Decoupled from MJ, fully under your control
