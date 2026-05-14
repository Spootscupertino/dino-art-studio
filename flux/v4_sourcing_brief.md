# v4 Dataset — Sourcing Brief for Gemini

## Goal
Find 13 reference images for a T-rex LoRA training dataset. These replace generic MJ self-generations with real anatomical references. The model learns from what it sees + what the caption says — so both need to be specific.

## Output format
Return a JSON array. I'll feed it directly into an ingest script.

```json
[
  {
    "url": "https://...",
    "filename": "nile_crocodile_mouth_gumline.jpg",
    "caption": "<anatomy-specific caption — see instructions below>",
    "source_type": "living_analog",
    "species": "tyrannosaurus",
    "license": "CC BY-SA 4.0"
  }
]
```

`source_type` must be one of: `living_analog`, `skeletal`, `paleoart`, `integument`

## Caption instructions — CRITICAL
**Look at each image before writing the caption.**
Describe exactly what anatomical detail is visible — specific, not generic.

Good: `"Nile crocodile open mouth showing recurved conical teeth anchored in exposed gumline, fleshy soft tissue visible along jaw margin, tongue and palate detail, high resolution"`
Bad: `"crocodile mouth open"` or `"T-rex anatomy reference"`

The caption should read like a paleontologist describing what a Tyrannosaurus feature looks like, using this image as a visual analog.

## License requirement
Only include images that are:
- Wikimedia Commons (CC BY, CC BY-SA, CC BY 4.0, public domain)
- Museums with open-access image policies (Smithsonian, AMNH, Field Museum open access)
- NO Getty, Alamy, Shutterstock, or watermarked images

## The 13 images needed

### Mouth/jaw analogs (3 images)
1. Nile crocodile OR saltwater crocodile: mouth open, teeth + exposed gumline + soft tissue visible
   - Search: `site:commons.wikimedia.org crocodile open mouth teeth gumline`
2. Same crocodilian from a different angle OR Komodo dragon mouth open showing palate + tongue
3. Monitor lizard (Varanus) mouth open — teeth, tongue, soft tissue

### Foot/claw analogs (3 images)
4. Cassowary foot close-up, three toes, digitigrade stance — NOT just feathers
   - Search: `site:commons.wikimedia.org cassowary foot claw`
5. Emu OR ostrich foot: three-toed, digitigrade, close enough to see claw curvature
6. Secretary bird OR any large raptor: foot showing recurved talon geometry

### Integument analogs (2 images)
7. Monitor lizard (Varanus salvator or komodoensis) body scales — mosaic polygon pattern
   - Search: `site:commons.wikimedia.org monitor lizard scales close-up`
8. Crocodile dorsal scutes OR Gila monster skin — large dome osteoderms interspersed in finer scales

### Skeletal mounts (3 images)
9. T-rex skull FRONTAL view (not profile) — shows binocular eye socket depth
   - Museums with open access: Field Museum (SUE), AMNH, ROM, Smithsonian
   - Search: `site:commons.wikimedia.org Tyrannosaurus skull frontal`
10. T-rex forelimb/manus bones — shows two-fingered hand, metacarpal stub of missing third digit
    - Search: `site:commons.wikimedia.org Tyrannosaurus forelimb manus`
11. T-rex complete skeleton, lateral, in active/horizontal posture (not upright Godzilla pose)

### Scientific paleoart (2 images)
12. Full-body T-rex reconstruction, horizontal spine, tail counterbalancing head — CC licensed
    - Artists known for CC: Matt Martyniuk (Dinogoss), Emily Willoughby, Nobu Tamura (Wikimedia)
    - Search: `site:commons.wikimedia.org Tyrannosaurus rex reconstruction Tamura` OR `Martyniuk`
13. T-rex skin impression fossil photograph (not the Wyrex/Wankel specimen — find a different one)
    - Search: `site:commons.wikimedia.org Tyrannosaurus skin impression fossil`

## What NOT to include
- Jurassic Park / movie T-rex (upright posture, wrong proportions)
- Any image with a watermark
- Any image where license is unclear
- Generic "dinosaur" images without clear T-rex anatomy
