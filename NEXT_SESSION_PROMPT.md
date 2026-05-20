# Next Session Prompt — Session 23 Close

## T. rex MJ Prompt: LOCKED

Anatomy quality is production-ready. Ref strategy proved out. Pick this up and iterate poses/environments, or move to next species.

### Locked Base Prompt (text only — refs must be refreshed each session)
```
solitary Tyrannosaurus rex, massive deep skull forward binocular eyes rugose brow ridges, conical honey-gold serrated teeth visible along jaw, tight pebbly scaly hide olive-brown dorsal tawny underbelly, vestigial forearms two curved dark keratin claws, pillar-like hindlimbs digitigrade three-toed feet dark curved claws, thick muscular tail held rigidly horizontal, 12 meters long 8-tonne apex predator --no three-fingered, extra fingers, fused digits, dragging tail, skeleton, fossilized, feathered, pair of animals --style raw --stylize 75 --sw 50 --q 1 --sref <refs>
```

### Locked Ref Set (4 files — refresh CDN tokens at session start)
Run `python3 upload_gallery_refs.py` first, then look up URLs:
1. `tyrannosaurus_wikimedia_paleo_art_side_profile.png` — full body proportions
2. `spootscupertino_A_cinematic_macro_shot_of_the_interior_mouth__9c1213c1...` — interior mouth/teeth
3. `spootscupertino_A_frontal_binocular_view_portrait_of_a_Tyrannos_45c56d6b...` — frontal skull angle
4. `Tyrannosaurus_arm_bone_and_flesh.jpg` — forelimb anatomy (two-finger anchor)

Lookup command:
```bash
python3 -c "
import json
sref = json.load(open('sref_urls.json'))
trex = sref.get('Tyrannosaurus rex', [])
for term in ['tyrannosaurus_wikimedia_paleo_art_side_profile.png', '9c1213c1', '45c56d6b', 'Tyrannosaurus_arm_bone_and_flesh']:
    m = next((e for e in trex if term in e.get('label','')), None)
    if m: print(m['url'])
"
```

### What's Still Soft
- Forelimb finger count: 2 fingers landing ~60% of frames — acceptable, LoRA will fix the rest
- Teeth: slightly too fang-like in some frames, honey-gold coloring is locked in
- Arms mostly hidden in frontal angles — fine for portraits

### Next Steps (priority order)
1. **Save best outputs from this session** into `assets/gallery/flux/training_refs/tyrannosaurus/round8_winners/` and run `upload_gallery_refs.py` to add to ref pool (self-improving loop)
2. **Vary environment** — add `hellcreek formation, fern ground cover, conifer canopy, overcast Cretaceous sky` to prompt for non-grey backgrounds
3. **Try a full-body wide shot** — add `full body visible head to tail tip, wide establishing shot` — current 4-pack skews portrait/bust
4. **Next species** — Mosasaurus or Brachiosaurus using same ref-first strategy

### What This Session Proved
- gallery_best/ refs >> Wikimedia paleoart refs as MJ --sref anchors
- 4 targeted refs (proportions + mouth + angle + anatomy diagram) > 1 general ref
- Minimal text + strong refs = best anatomy hit rate
- upload_gallery_refs.py is the key workflow tool — run it every session
