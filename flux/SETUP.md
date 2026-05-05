# Flux Domain Setup — M1 Mac Mini

## One-Time Setup

### 1. Install dependencies
```bash
cd /Users/ericeldridge/dino_art
pip install -r flux/requirements.txt
```

**Expect:** ~5-10 minutes. PyTorch will auto-detect Metal GPU support on M1.

### 2. Verify Flux model download
```bash
python -c "from diffusers import FluxPipeline; FluxPipeline.from_pretrained('black-forest-labs/FLUX.1-dev')"
```

**Expect:** ~30 seconds first run (downloads 24GB), then cached. **Total disk space needed: ~30GB.**

### 3. Create directories
```bash
mkdir -p flux/loras flux/controlnets
mkdir -p assets/gallery/flux
```

## Daily Usage

### Generate images via ComfyUI (recommended)
```bash
python flux/comfyui_server.py --port 8888
# Open http://localhost:8888 in browser
# Adjust prompt/parameters live, watch generation in real-time
```

### Generate images via CLI
```bash
python flux/generate_image.py --prompt "a Tyrannosaurus in a river delta" --lora dino_winners
```

### Train LoRA on winners
```bash
python flux/train_lora.py --species "Tyrannosaurus" --epochs 5
```

## Performance on M1 24GB

| Task | Time | Memory |
|---|---|---|
| Load Flux-dev | ~10 seconds | 20GB |
| Single image generation | ~45 seconds | 22GB peak |
| LoRA training (10 images) | ~15 minutes | 23GB peak |

## Troubleshooting

### Out of memory errors
- Reduce `num_inference_steps` from 50 to 30
- Reduce image size from 1024×1024 to 768×768
- Close other apps to free memory

### Model download stuck
- Check internet connection
- Try: `huggingface-cli download black-forest-labs/FLUX.1-dev`

### ComfyUI server won't start
- Check port 8888 is free: `lsof -i :8888`
- Try different port: `python flux/comfyui_server.py --port 9999`

## Architecture Notes

- **Flux-dev** — 24B parameters, bfloat16 precision on M1
- **LoRA** — 8-rank fine-tuning on attention layers, low memory overhead
- **ComfyUI** — Headless FastAPI server + branded UI
- **Output** — Compatible with existing printify-publisher pipeline

## Integration with Feedback Loop

```
Rate image in unified_feedback.py (8+ = winner)
  ↓
save_winner() stores to winners.json + LLaVA anatomy analysis
  ↓
python flux/train_lora.py (trains on recent winners)
  ↓
ComfyUI loads updated LoRA
  ↓
Next generation uses better anatomy
```

## Next: Porting to Printify

Once you have high-quality Flux generations:
1. Rate them in `unified_feedback.py --local`
2. Sync to `assets/gallery/flux/`
3. Run `sync_gallery.py` (Vercel deploy)
4. `printify/printify_publisher.py` publishes to Printify automatically

No code changes needed — same output format.
