# Ichthyosaurus — Reference Materials

## What this folder is for
This folder holds all scientific reference materials for *Ichthyosaurus communis*:
skeletal diagrams, fossil photographs, life reconstructions, museum specimen
images, and texture studies. Everything here feeds directly into
scientifically accurate prompt engineering for Ichthyosaurus art generation.

## File naming convention
```
ichthyosaurus_[type]_[source]_[year].[ext]
```
Types: `skeletal`, `fossil`, `reconstruction`, `museum`, `texture`

Examples:
- `ichthyosaurus_skeletal_nhmuk_2015.pdf`
- `ichthyosaurus_fossil_anning_1821.tif`
- `ichthyosaurus_reconstruction_motani_2005.tif`
- `ichthyosaurus_texture_skin_impression_2010.tif`

Image format: minimum 4K resolution; RAW preferred for photography; TIF for
flatbed or photogrammetric scans.

## Real Animal Analogues for --sref

Use photographs of these living animals to supply `--sref` style references
for specific body regions and surface qualities:

- **Dolphin** (*Tursiops* / *Delphinus* spp.) — overall fusiform body shape
  and swimming posture. Photograph full lateral profile underwater and at
  the surface; capture dorsal fin shape and tail fluke orientation
  (note: ichthyosaur tail is vertical, unlike horizontal dolphin fluke --
  use for body contour only).
- **Tuna** (*Thunnus* spp.) — streamlined hydrodynamic body shape and
  smooth skin surface. Photograph lateral profile showing the torpedo-like
  cross-section; detail shots of skin texture for surface quality reference.
- **Porpoise** (*Phocoena* spp.) — snout shape and head proportions.
  Photograph head from lateral and dorsal angles; focus on the blunt,
  rounded rostrum shape and eye placement.

## Image format guidance
- Minimum 4K (3840x2160) for usable reference
- RAW (.CR3, .ARW, .NEF) preferred for fossil and museum photography
- TIF (16-bit, uncompressed) for flatbed scans of skeletal diagrams
- PDF acceptable for published skeletal reconstructions
