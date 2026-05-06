# Phase C: LoRA Training Pipeline

## Status: Structure in place, awaiting real winners

### What's ready
- `winners.json` schema updated to track `source` (mj vs flux) and Flux-specific metadata
- `flux/train_lora.py` configured to read winners and train per-species LoRAs
- M1 optimizations in place (bfloat16, memory-mapped loading)
- LoRA config: rank=8, alpha=16 (conservative for 24GB)

### How to run (once you have winning Flux images)

```bash
# After rating a Flux image as usable (score ≥ 8), it auto-saves to winners.json

# Train LoRA on all winners
python flux/train_lora.py

# Train LoRA on specific species (e.g., Tyrannosaurus)
python flux/train_lora.py --species "Tyrannosaurus"

# Use trained LoRA in next generation
python flux/generate_image.py \
  --prompt "a new T-rex pose" \
  --lora dino_winners \
  --seed 999

# Then rate the new image → if usable, it trains the next LoRA iteration → loop tightens
```

### Data flow

```
unified_feedback.py (user rates image ≥ 8)
  → winners.json (auto-append winner entry)
    → flux/train_lora.py (scheduled or manual)
      → flux/loras/dino_winners.safetensors
        → flux/generate_image.py (next generation uses updated LoRA)
          → better dinosaurs → next rating
```

### Next session: First real LoRA training

1. **Generate test images** on M1 (flux/generate_image.py with a species)
2. **Rate them** with unified_feedback.py (score ≥ 8 auto-saves winners)
3. **Train LoRA** (python flux/train_lora.py)
4. **Compare** output with/without LoRA to verify improvement

### Known limitations

- Current `train_lora.py` has a placeholder training loop (line 198: `pass`)
  - Full diffusion training needed for real fine-tuning
  - ComfyUI AI Toolkit trainer recommended for actual training
  - Alternative: Run training via Hugging Face diffusers trainer loop

- M1 constraint: BATCH_SIZE=1, limited by 24GB unified memory
  - Gradient accumulation (4 steps) helps compensate
  - ~10 min per epoch expected for 10–20 images

### Quick test (Phase C validation)

```bash
# Without real images, verify the pipeline structure:
python -c "
import json
from pathlib import Path

with open('winners.json') as f:
    winners = json.load(f)

print(f'✓ Winners.json valid')
print(f'  Species: {list(winners.keys())}')
for species, entries in winners.items():
    for entry in entries:
        print(f'    {species}: source={entry[\"source\"]}, score={entry[\"score\"]}')
"
```

### To complete Phase C next session

1. Generate real Flux images (seed varies, same prompt)
2. Rate best-of-5 as winners
3. Run `python flux/train_lora.py --species "Mosasaurus"`
4. Generate with new LoRA: `--lora dino_winners`
5. Compare output quality before/after LoRA

---

**Phase A–C plan complete.** Sidecar metadata → auto-rating → LoRA training loop is wired. Ready to feed real winners through the pipeline.
