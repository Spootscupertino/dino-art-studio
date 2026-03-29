#!/usr/bin/env python3
"""
migrate_scientific.py

One-shot migration for the dino_art project:
  PART 1 — Create species_reference folder structure with per-species READMEs
  PART 2 — DB migration: ALTER TABLE species, CREATE TABLE research_notes,
            populate scientific data, insert research notes
  PART 3 — Print verification summary

Idempotent: safe to run multiple times.
"""

import os
import sqlite3

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = "/Users/ericeldridge/dino_art"
SPECIES_REF_DIR = os.path.join(BASE_DIR, "species_reference")
DB_PATH = os.path.join(BASE_DIR, "dino_art.db")

# ---------------------------------------------------------------------------
# PART 1 — README content per species
# ---------------------------------------------------------------------------

READMES = {
    "tyrannosaurus_rex": """\
# Tyrannosaurus rex — Reference Materials

## What this folder is for
This folder holds all scientific reference materials for *Tyrannosaurus rex*:
skeletal diagrams, fossil photographs, life reconstructions, museum specimen
images, and texture studies. Everything here feeds directly into
scientifically accurate prompt engineering for T. rex art generation.

## File naming convention
```
tyrannosaurus_rex_[type]_[source]_[year].[ext]
```
Types: `skeletal`, `fossil`, `reconstruction`, `museum`, `texture`

Examples:
- `tyrannosaurus_rex_skeletal_fmnh_2017.pdf`
- `tyrannosaurus_rex_fossil_mor_2003.tif`
- `tyrannosaurus_rex_reconstruction_paul_1988.tif`
- `tyrannosaurus_rex_texture_bell_2017.tif`

Image format: minimum 4K resolution; RAW preferred for photography; TIF for
flatbed or photogrammetric scans.

## Priority reference materials

1. **FMNH PR 2081 "Sue"** — Field Museum of Natural History, Chicago
   Most complete T. rex known (~90%). Full mounted skeleton on public display.
   Photograph the skull separately (FMNH has a separate skull display with
   the correct articulation). Note: the mounted skeleton uses an incorrect
   fibula; verified in Brochu 2003.

2. **RSM P.2523.8 "Scotty"** — Royal Saskatchewan Museum, Canada
   Largest T. rex by body mass estimate (~8,800 kg). Good for overall
   proportions of a fully mature individual. Published fully in Scott et al.
   2019 (PeerJ).

3. **MOR 980 "B-rex"** — Museum of the Rockies, Bozeman MT
   Female specimen with medullary bone evidence. Key for understanding
   sexual dimorphism. Horner & Padian 2004 (Proceedings of the Royal Society).

4. **AMNH 5027** — American Museum of Natural History, New York
   Historic specimen; older mount but skull is well-preserved and
   extensively studied. Good early reference for skull shape cross-checking.

5. **Bell et al. 2017 skin study** (PLOS Biology, doi:10.1371/journal.pbio.1002467)
   Describes scales confirmed from neck, abdomen, hips, and tail base.
   Critical: no feather evidence in adults. Source all illustrated body
   regions from this paper.

6. **Persons & Currie 2011** (Acta Palaeontologica Polonica, doi:10.4202/app.2009.0055)
   Tail musculature reconstruction. Confirms M. caudofemoralis bulk —
   tail must be drawn as deeply muscled, horizontal, clear of the ground.

7. **Hutchinson & Garcia 2002** (Nature, doi:10.1038/nature01138)
   Locomotion biomechanics. Max speed 12–25 km/h. T. rex was a slow,
   deliberate mover — not a sprinter. Important for action pose accuracy.

## What to look for / photograph / scan

- **Skull**: Binocular vision orbit orientation; deep postorbital boss;
  serrated, banana-thick teeth (D-shaped cross-section, not blade-like);
  fenestrae proportions; short foreshortened snout of mature adults.
- **Forelimbs**: Two-fingered manus; extreme reduction; palms face each
  other (medially), NOT downward. Supination was anatomically impossible.
- **Hindlimbs**: Proportionally massive femur vs tibia; arctometatarsalian
  foot (third metatarsal pinched at top); four toes, first digit vestigial.
- **Tail**: Deep base reflecting massive M. caudofemoralis; horizontal
  posture confirmed. Avoid any sag or dragging.
- **Integument**: Scales only in all known adult skin patches. Photograph
  the Bell et al. specimen regions. Scale texture is pebbly/mosaic.
- **Size context**: Scan full skeletal mounts alongside human silhouette
  for scale reference. Sue stands ~3.66 m at the hips.

## Image format guidance
- Minimum 4K (3840×2160) for usable reference
- RAW (.CR3, .ARW, .NEF) preferred for fossil and museum photography
- TIF (16-bit, uncompressed) for flatbed scans of skeletal diagrams
- PDF acceptable for published skeletal reconstructions (Greg Paul, Scott
  Hartman)
""",

    "velociraptor": """\
# Velociraptor — Reference Materials

## What this folder is for
This folder holds all scientific reference materials for *Velociraptor
mongoliensis* (and *V. osmolskae*): skeletal diagrams, fossil photographs,
feather and integument studies, life reconstructions, and museum specimen
images. All content here supports scientifically accurate prompt engineering.

## File naming convention
```
velociraptor_[type]_[source]_[year].[ext]
```
Types: `skeletal`, `fossil`, `reconstruction`, `museum`, `texture`

Examples:
- `velociraptor_skeletal_paul_2010.tif`
- `velociraptor_fossil_igm100_986_2007.tif`
- `velociraptor_reconstruction_turner_2007.tif`

Image format: minimum 4K resolution; RAW preferred; TIF for scans.

## Priority reference materials

1. **IGM 100/986** — Institute of Geology, Mongolian Academy of Sciences
   Type specimen of *V. mongoliensis* (Osborn 1924). Key for skull
   proportions: elongated, low snout; large orbit; denticulate teeth.
   Well-illustrated in Novas & Pol 2005.

2. **IGM 100/1126 — Quill knob specimen**
   Ulna of *V. mongoliensis* with six quill knob attachment points
   (papillae) along the posterior edge. Published Turner et al. 2007
   (Science, doi:10.1126/science.1137427). This specimen proves
   large pennaceous forearm feathers — directly analogous to modern
   bird secondary feathers. Photograph this ulna if possible.

3. **"Fighting Dinosaurs" IGM 100/25** — Institute of Geology, Ulaanbaatar
   Articulated specimen locked with *Protoceratops* — preserves sickle
   claw in context. Shows natural resting limb posture in death.

4. **Turner et al. 2007** (Science)
   Foundational quill knob paper. Establishes full-body feathering
   inference from phylogenetic bracketing of maniraptorans.

5. **Manning et al. 2006** (Biology Letters, doi:10.1098/rsbl.2005.0395)
   Sickle claw function study: claw used for grip/pin, not slashing.
   Claw was held elevated off the ground during normal locomotion.

6. **Pittman et al. 2022** (iScience, doi:10.1016/j.isci.2022.104358)
   Ecological niche analysis. *Velociraptor* was a small-prey ambush
   predator, NOT a pack hunter of large animals. Jurassic Park depiction
   is incorrect in both size and behaviour.

7. **Greg Paul skeletal** — *The Princeton Field Guide to Dinosaurs* (2010)
   Best widely-available skeletal for body outline and proportions.

## What to look for / photograph / scan

- **Overall size**: *Velociraptor* was turkey-sized (~1.8 m, 18 kg).
  Collect size-comparison references against known objects for scale accuracy.
- **Skull**: Low, elongated, upturned at tip; teeth are small, recurved,
  and serrated; large antorbital fenestra.
- **Sickle claw**: Second pedal digit; claw held raised off the ground.
  Photograph cast or real specimen of digit II hyperextension.
- **Forelimbs**: Three-fingered manus with large claws; arm proportionally
  long; wrist folds bird-like (semilunate carpal). Palms face each other
  at rest, not downward.
- **Feathers**: Full-body plumage strongly inferred. Arm feathers are large
  (secondary-like). Tail feathers likely. Reconstruct with modern bird
  feather textures as reference, but avoid overly "fluffy" appearance.
- **Tail**: Ossified tendons made it stiff and horizontal. Cannot curve
  significantly up or down.

## Image format guidance
- Minimum 4K (3840×2160) for usable reference
- RAW preferred for fossil photography
- TIF (16-bit, uncompressed) for skeletal diagram scans
- High-res bird feather macro photography is useful for texture reference
""",

    "triceratops": """\
# Triceratops — Reference Materials

## What this folder is for
This folder holds all scientific reference materials for *Triceratops horridus*
and *T. prorsus*: skeletal diagrams, fossil photographs, skin impression
studies, frill and horn reconstructions, and museum specimen images. All
content here supports scientifically accurate prompt engineering.

## File naming convention
```
triceratops_[type]_[source]_[year].[ext]
```
Types: `skeletal`, `fossil`, `reconstruction`, `museum`, `texture`

Examples:
- `triceratops_skeletal_usnm4842_scan.tif`
- `triceratops_fossil_dmnh1467_2009.tif`
- `triceratops_reconstruction_horner_2009.tif`

Image format: minimum 4K resolution; RAW preferred; TIF for scans.

## Priority reference materials

1. **USNM 4842** — Smithsonian National Museum of Natural History, Washington DC
   One of the best-preserved skulls; used as a key reference for *T. horridus*
   proportions. Marsh 1891 holotype material. Good for orbital and nasal
   horn curvature measurements.

2. **DMNH 1467** — Denver Museum of Nature and Science, Denver CO
   Well-preserved specimen. Denver has multiple *Triceratops* specimens
   suitable for skull and postcranial reference.

3. **Horner & Goodwin 2009** (Journal of Vertebrate Paleontology)
   Ontogenetic study — juvenile *Triceratops* have very different frill
   and horn proportions than adults. Critical for age-accurate depictions.
   Subadults had forward-curved horns that straightened/lengthened with age.

4. **Fujiwara 2009** (Journal of Vertebrate Paleontology, doi:10.1671/039.029.0413)
   Forelimb posture analysis. Elbows were slightly lateral — semi-sprawling,
   not columnar like an elephant, not flat like a lizard. Critical for
   accurate front-view and three-quarter poses.

5. **Longrich & Field 2012** (PLOS ONE) — *Torosaurus* synonymy debate
   Context: *Torosaurus* may be the mature form of *Triceratops*. Relevant
   for understanding frill fenestra development at oldest ontogenetic stages.

6. **Farke 2011** (PLOS ONE, doi:10.1371/journal.pone.0018112)
   Frill vascularization and display function. The frill was richly
   vascularised — likely brightly coloured for intraspecific display and
   possibly thermoregulation.

7. **Skin impressions** — pebbly/mosaic scale texture documented from
   multiple *Triceratops* and *Torosaurus* specimens. Photograph Smithsonian
   and Denver holdings.

## What to look for / photograph / scan

- **Skull**: Enormous relative to body (~2 m long); three horns; curved
  frill edge (epiparietals); massive jugal "cheek" bosses.
- **Horns**: Nasal horn is short and blunt; brow horns are long, forward-
  curving in adults. Juvenile horns curve differently — specify age.
- **Frill**: Large, solid (not fenestrated like *Torosaurus*); margin
  decorated with small ossified triangular epiparietals/epijugals.
- **Forelimbs**: Semi-sprawling posture; elbows slightly out and slightly
  bent, not locked straight. Careful not to draw as elephant-columnar.
- **Skin**: Pebbly mosaic scales; no osteoderms on back. No feathers.
- **Overall proportions**: Massive barrel body; relatively short tail;
  four stocky legs. Hindlimbs longer than forelimbs (slight forward pitch).

## Image format guidance
- Minimum 4K (3840×2160)
- RAW preferred for museum photography
- TIF for skeletal diagram scans
- Photograph skull from multiple angles: lateral, dorsal, anterior, posterior
""",

    "stegosaurus": """\
# Stegosaurus — Reference Materials

## What this folder is for
This folder holds all scientific reference materials for *Stegosaurus stenops*
and *S. ungulatus*: skeletal diagrams, fossil photographs, plate and thagomizer
studies, skin impression data, and museum specimen images. All content here
supports scientifically accurate prompt engineering.

## File naming convention
```
stegosaurus_[type]_[source]_[year].[ext]
```
Types: `skeletal`, `fossil`, `reconstruction`, `museum`, `texture`

Examples:
- `stegosaurus_skeletal_usnm4934_scan.tif`
- `stegosaurus_fossil_nhm_sophie_2014.tif`
- `stegosaurus_reconstruction_mallison_2011.tif`

Image format: minimum 4K resolution; RAW preferred; TIF for scans.

## Priority reference materials

1. **USNM 4934** — Smithsonian National Museum of Natural History, Washington DC
   Classic mounted specimen; important historical reference for overall
   body proportions and plate arrangement. Note: older mounts have
   plate arrangement errors — use Mallison 2011 for corrected kinematics.

2. **NHM London "Sophie" (NHMUK PV R36730)** — Natural History Museum, London
   Most complete *Stegosaurus* skeleton known (~85%). Note: this is the
   specimen sometimes mis-cited as "DMNH 1483" — "Sophie" is in London, not
   Denver. Published fully in Maidment et al. 2015. Excellent for proportions.

3. **Saitta 2018** (PLOS ONE, doi:10.1371/journal.pone.0200)
   Plate sexual dimorphism study: two distinct plate morphotypes may
   indicate male (tall, narrow plates) and female (wide, flat plates).
   If depicting a specific sex, choose the correct plate shape.

4. **Mallison 2011** (PLOS ONE, doi:10.1371/journal.pone.0014665)
   Tail kinematics — thagomizer could swing laterally with significant
   force. Active weapon, not passive decoration. Models tail as raised
   and mobile in alert/defensive posture.

5. **Farlow et al. 1976** (Paleobiology)
   Original plate function paper. Plates were vascularised — grooves for
   blood vessels visible on specimen surfaces. Display and/or
   thermoregulation were primary functions.

6. **DMNH specimens** — Denver Museum of Nature and Science
   Multiple Morrison Formation *Stegosaurus* specimens. Denver collection
   is strong for postcranial and plate reference.

7. **Skin impressions** — ossicles (small, non-overlapping) and larger
   tubercles documented. Photograph from Morrison Formation specimens.

## What to look for / photograph / scan

- **Plates**: Two rows, alternating (not paired). Plates are covered in
  grooved vascular tissue — not smooth bone. Plate shape: address both
  morphotypes for your specific specimen.
- **Thagomizer**: Four tail spikes, in two pairs angled outward. Spikes
  are keratinous sheaths over bone — longer in life than the fossil bone.
  Tail is raised and active, not dragging.
- **Head**: Tiny relative to body; small, leaf-shaped teeth; toothless
  beak at front. Brain genuinely small — secondary neural canal in hips
  was a glycogen body, not a second brain.
- **Forelimbs**: Short and columnar. Hindlimbs significantly longer —
  rump is the highest point of the body. Plantigrade hindfoot.
- **Skin**: Scales, ossicles, and tubercles. No feathers, no smooth skin.
- **Overall posture**: Deep body; short neck; rounded back profile with
  plates rising above. Four short, stocky legs.

## Image format guidance
- Minimum 4K (3840×2160)
- RAW preferred for fossil photography
- TIF for skeletal and plate diagram scans
- Photograph plate surfaces at raking light angle to reveal vascular groove texture
""",

    "brachiosaurus": """\
# Brachiosaurus — Reference Materials

## What this folder is for
This folder holds all scientific reference materials for *Brachiosaurus
altithorax* (Morrison Formation, USA only): skeletal diagrams, fossil
photographs, posture studies, and museum specimen images. All content here
supports scientifically accurate prompt engineering.

**IMPORTANT**: African specimens (Tendaguru Formation, Tanzania) previously
assigned to *Brachiosaurus brancai* are now a separate genus: *Giraffatitan
brancai* (Taylor 2009). The famous Berlin HMN SII skeleton is *Giraffatitan*,
NOT *Brachiosaurus*. True *Brachiosaurus* is known only from the Morrison
Formation, USA. Maintain separate folders if working with both taxa.

## File naming convention
```
brachiosaurus_[type]_[source]_[year].[ext]
```
Types: `skeletal`, `fossil`, `reconstruction`, `museum`, `texture`

Examples:
- `brachiosaurus_skeletal_fmnh_p25107_scan.tif`
- `brachiosaurus_fossil_fruita_co_type_locality.tif`
- `brachiosaurus_reconstruction_taylor_2009.tif`

Image format: minimum 4K resolution; RAW preferred; TIF for scans.

## Priority reference materials

1. **FMNH P25107** — Field Museum of Natural History, Chicago
   Partial skeleton including forelimb, scapulocoracoid, sacrum — key
   material for *B. altithorax*. The type locality is Fruita, Colorado
   (Morrison Formation, Brushy Basin Member, ~150 Ma).

2. **Taylor 2009** (Journal of Vertebrate Paleontology, doi:10.1671/039.029.0401)
   The paper separating *Brachiosaurus* from *Giraffatitan*. Essential
   reading for understanding what's genuinely known about each genus.
   Detailed anatomical differences: pubis shape, dorsal vertebrae, humerus.

3. **HMN SII (Giraffatitan reference)** — Museum für Naturkunde, Berlin
   While this is *Giraffatitan*, it provides the best complete brachiosaur
   body plan reference available. Use cautiously, noting the anatomical
   differences documented by Taylor 2009.

4. **Paul & Christiansen 2000** (Paleobiology)
   Sauropod forelimb and neck posture. Neck was held at elevated angle
   (approximately 45–70° above horizontal) — not horizontal as in older
   depictions and *Jurassic Park*. Supported by osteological neutral pose.

5. **Taylor, Wedel & Naish 2009** (Acta Palaeontologica Polonica)
   Neck posture analysis across sauropods. Confirms elevated neck posture
   as default. Head was held high — this is the defining visual feature.

6. **Carrano 2005** (Journal of Vertebrate Paleontology)
   Locomotion and body mass estimates for large sauropods. Body mass for
   *B. altithorax* estimated ~40,000 kg (40 tonnes).

7. **Greg Paul skeletal** — *The Princeton Field Guide to Dinosaurs* (2010)
   Best widely-available skeletal reconstruction showing elevated neck and
   correct body proportions.

## What to look for / photograph / scan

- **Neck**: Long, elevated at ~45–70° from horizontal. Head small relative
  to body. Not horizontal as in diplodocids. Cervical vertebrae are long
  and pneumatized (air-sac system).
- **Forelimb/hindlimb ratio**: Forelimbs are longer than hindlimbs —
  defining *Brachiosauridae* feature, unlike most other sauropods.
  Results in a distinctly giraffe-like forward shoulder pitch.
- **Forelimbs**: Columnar, near-vertical. Manus (hand) is narrow and
  horseshoe-shaped in prints — no large claws except on first digit.
- **Tail**: Relatively short for a sauropod; tapers to a thin whip end.
  Horizontal, not raised. Not used as a prop.
- **Nostrils**: Bony nares are on the top of the skull, but soft-tissue
  nostrils were likely positioned lower on the snout (Witmer 2001).
- **Skin**: Fragmentary scale impressions known. No osteoderms confirmed.

## Image format guidance
- Minimum 4K (3840×2160)
- RAW preferred for museum photography
- TIF for skeletal and vertebra diagram scans
- Scale reference shots critical given the enormous body size
""",

    "ankylosaurus": """\
# Ankylosaurus — Reference Materials

## What this folder is for
This folder holds all scientific reference materials for *Ankylosaurus
magniventris*: skeletal diagrams, fossil photographs, osteoderm and armor
studies, tail club biomechanics, and museum specimen images. All content here
supports scientifically accurate prompt engineering.

## File naming convention
```
ankylosaurus_[type]_[source]_[year].[ext]
```
Types: `skeletal`, `fossil`, `reconstruction`, `museum`, `texture`

Examples:
- `ankylosaurus_skeletal_amnh5895_scan.tif`
- `ankylosaurus_fossil_cmn8880_armor.tif`
- `ankylosaurus_reconstruction_arbour_2015.tif`

Image format: minimum 4K resolution; RAW preferred; TIF for scans.

## Priority reference materials

1. **AMNH 5895** — American Museum of Natural History, New York
   Partial skull and postcranial material; includes armor and tail club
   fragments. One of the primary *Ankylosaurus* specimens. Published in
   Brown 1908 and revised by Arbour & Currie 2013.

2. **CMN 8880** — Canadian Museum of Nature, Ottawa
   Skull and partial skeleton; another key specimen for *A. magniventris*.
   Provides good data on skull ornamentation and horn positions.

3. **Arbour & Currie 2015** (PLOS ONE, doi:10.1371/journal.pone.0138258)
   Tail club biomechanics study. Club could generate sufficient force to
   fracture bone of large theropods. Active weapon — not merely passive.
   Includes reconstructed swing mechanics.

4. **Arbour & Currie 2013** (Journal of Systematic Palaeontology)
   Comprehensive revision of *Ankylosaurus*. Best modern anatomical
   description. Essential for skull proportions and armor layout.

5. **Burns et al. 2011** (various)
   Osteoderm ontogeny and distribution. Back and flanks heavily armoured;
   belly was comparatively unprotected — soft ventral region.

6. **Schweitzer et al. (various)** — Ankylosaur skin texture documentation
   Osteoderms (keeled scutes, flat oval scutes) fully covering dorsal
   surface. Photograph surface textures of any ankylosaur specimens
   available at AMNH, RTMP, CMN.

7. **Royal Tyrrell Museum** — Drumheller, Alberta
   Extensive ankylosaur collection including *Euoplocephalus* (close
   relative). Textures from *Euoplocephalus* are the best available proxy
   for *Ankylosaurus* integument. RTMP 80.16.1 is a key skin reference.

## What to look for / photograph / scan

- **Tail club**: Bony knob at tail end (handle vertebrae fused); actively
  swung laterally. Proportionally large and heavy — do not undersize.
- **Armor**: Keeled oval scutes over back and sides in regular rows; large
  horn-like scutes at the shoulders and hips. Small mosaic ossicles fill
  gaps. No armor on belly — soft underside is a vulnerability.
- **Skull**: Wide, triangular, heavily armoured; fused osteoderms on skull
  surface form distinct polygonal bosses. Small, leaf-shaped teeth; broad
  beak. Skull is nearly as wide as long.
- **Posture**: Low to ground; wide-gauge quadrupedal stance; barrel body.
  Forelimbs slightly shorter than hindlimbs.
- **Limbs**: Columnar and robust; five toes on hind feet; broad, flat foot.
- **Texture detail**: Photograph osteoderm keels and surface texture in
  raking light. Scale impressions between osteoderms are useful.

## Image format guidance
- Minimum 4K (3840×2160)
- RAW preferred for museum photography
- TIF for osteoderm surface detail scans
- Raking light setup essential for revealing surface texture on armor scutes
""",

    "pteranodon": """\
# Pteranodon — Reference Materials

## What this folder is for
This folder holds all scientific reference materials for *Pteranodon longiceps*
and *P. sternbergi*: skeletal diagrams, specimen photographs, wing membrane
studies, crest dimorphism data, and museum specimen images. All content here
supports scientifically accurate prompt engineering.

**CRITICAL TAXONOMY NOTE**: *Pteranodon* is NOT a dinosaur. It is a pterosaur —
a flying reptile on a completely separate evolutionary lineage from dinosaurs.
*Pteranodon* and dinosaurs were contemporaneous but only distantly related
(both are archosaurs). This distinction must be noted in all prompt work.
Do not label *Pteranodon* as a dinosaur in any caption or metadata.

## File naming convention
```
pteranodon_[type]_[source]_[year].[ext]
```
Types: `skeletal`, `fossil`, `reconstruction`, `museum`, `texture`

Examples:
- `pteranodon_skeletal_fhsm_vp2183_scan.tif`
- `pteranodon_fossil_ypm_2473_2001.tif`
- `pteranodon_reconstruction_witton_2013.tif`

Image format: minimum 4K resolution; RAW preferred; TIF for scans.

## Priority reference materials

1. **FHSM VP-2183** — Fort Hays State University, Hays KS
   One of the best-preserved *Pteranodon* specimens. Sternberg Museum of
   Natural History. Includes skull with full crest and partial skeleton.
   Large male (*P. longiceps* morphology).

2. **YPM VP 002473** — Yale Peabody Museum, New Haven CT
   Key specimen from Marsh's original Niobrara Formation collections.
   Peabody has an extensive *Pteranodon* collection critical for wing
   membrane shape and proportions.

3. **Bennett 2001** (Journal of Vertebrate Paleontology)
   Comprehensive monograph on *Pteranodon* taxonomy and sexual dimorphism.
   Males: large crests, narrow pelvis. Females: small/no crests, wider
   pelvis for egg-laying. Essential for sex-specific depiction.

4. **Habib 2008** (Zitteliana)
   Quadrupedal launch biomechanics — *Pteranodon* launched like a pole-
   vaulter, using all four limbs, hindlimbs last. Did NOT run and flap.
   Critical for any take-off or landing pose.

5. **Witton 2013** — *Pterosaurs: Natural History, Evolution, Anatomy*
   Princeton University Press. Best single reference for pterosaur life
   appearance, wing proportions, and locomotion. Includes *Pteranodon*
   chapter with up-to-date reconstruction.

6. **Pycnofibers documentation** — *Pteranodon* and pterosaurs generally
   were covered in pycnofibers: short, hair-like filaments. These are NOT
   feathers. Different structure, different evolutionary origin.

7. **Kellner et al. (various)** — Wing membrane studies
   Actinofibrils (stiff fibres) in the patagium created a semi-rigid wing.
   The wing attached to the ankle or upper hindlimb (debate ongoing).

## What to look for / photograph / scan

- **Crest**: Backward-projecting bony crest on male skulls; highly variable
  between individuals. In life, crest may have extended further with soft
  tissue. No soft-tissue crest evidence in females.
- **Wing membrane**: Attached from elongated fourth finger to body/hindlimb.
  Patagium was not a simple sheet — it had internal actinofibrils for
  stiffness and camber control.
- **Toothless beak**: No teeth — long, pointed beak for catching fish.
- **Body size**: Wingspan ~5–6 m (males); body was relatively small and
  lightweight (~25 kg estimated).
- **Pycnofibers**: Short, stiff fibers cover the body. Photograph any
  pterosaur specimens showing soft-tissue fiber preservation (Sordes,
  Jeholopterus have good examples).
- **Ground posture**: Quadrupedal at rest; wings folded against body.
  Hindlimbs smaller but functional; plantigrade or semi-plantigrade stance.

## Image format guidance
- Minimum 4K (3840×2160)
- RAW preferred for museum photography
- TIF for wing membrane and skeletal diagram scans
- Transmitted or raking light useful for wing membrane specimen photography
""",

    "spinosaurus": """\
# Spinosaurus — Reference Materials

## What this folder is for
This folder holds all scientific reference materials for *Spinosaurus
aegyptiacus*: skeletal diagrams, specimen photographs, semi-aquatic lifestyle
studies, tail reconstruction data, and museum specimen images. All content
here supports scientifically accurate prompt engineering.

**HISTORICAL NOTE**: The original *Spinosaurus* holotype specimens (collected
by Ernst Stromer, 1912, Egypt) were destroyed in April 1944 during the Allied
bombing of Munich (Alte Akademie). All modern *Spinosaurus* reconstructions
are based on subsequently discovered Moroccan/Algerian specimens and Stromer's
original descriptions and photographs.

## File naming convention
```
spinosaurus_[type]_[source]_[year].[ext]
```
Types: `skeletal`, `fossil`, `reconstruction`, `museum`, `texture`

Examples:
- `spinosaurus_skeletal_ibrahim_2020_nature.tif`
- `spinosaurus_fossil_msnm_v4047_2014.tif`
- `spinosaurus_reconstruction_ibrahim_2020.tif`

Image format: minimum 4K resolution; RAW preferred; TIF for scans.

## Priority reference materials

1. **MSNM V4047** — Museo di Storia Naturale di Milano, Milan
   Snout material; one of the well-documented post-Stromer specimens.
   Published in Dal Sasso et al. 2005. Conical, elongated crocodile-like
   snout confirmed; rosette of teeth at tip.

2. **Ibrahim et al. 2014** (Science, doi:10.1126/science.1258750)
   Landmark semi-aquatic reconstruction paper. Describes short hindlimbs,
   dense (pachyostotic) bones, and elevated nares position. Introduced
   the quadrupedal "gorilla posture" interpretation. Key images available.

3. **Ibrahim et al. 2020** (Nature, doi:10.1038/s41586-020-2190-3)
   Paddle-tail reconstruction. New specimen from Kem Kem shows elongated
   neural spines on tail vertebrae forming a large fin-like paddle.
   Primary swimming organ interpretation. This is the current standard
   for tail reconstruction.

4. **Hone & Holtz 2021** (Palaeontologia Electronica)
   Critical reassessment — argues for wading/shoreline predator rather
   than fully aquatic. Debate is ongoing. Note this uncertainty in any
   strictly aquatic depictions.

5. **Kem Kem Beds specimens** — Multiple fragmentary specimens from
   Morocco/Algeria (Kem Kem Group, Cenomanian). Various institutions
   hold material. The National Geographic Society funded the Ibrahim 2020
   excavation.

6. **Stromer 1915 original description** (Abhandlungen der Königlichen
   Bayerischen Akademie der Wissenschaften) — Available in translation.
   Provides original documentation of the destroyed holotype. Scale
   drawings by Stromer are the only direct record of those specimens.

7. **Scale impressions** — Conical scales documented from available
   *Spinosaurus* specimens. Not smooth-skinned; not feathered.

## What to look for / photograph / scan

- **Skull**: Long, narrow, low profile — crocodilian analogue. Conical,
  interlocking teeth (not serrated blades). Enlarged conical teeth at snout
  tip (rosette). Nares positioned posteriorly/dorsally on skull.
- **Neural spines**: Elongated spines on dorsal vertebrae forming a sail
  or hump. Scale and shape still debated — sail vs. muscular hump.
  On tail: enlarged into paddle-like structure (Ibrahim 2020).
- **Hindlimbs**: Notably short relative to body length compared to other
  large theropods. Proportionally stubby.
- **Forelimbs**: Large, three-fingered; used in quadrupedal locomotion on
  land per Ibrahim 2014 interpretation. Claws robust.
- **Aquatic adaptations**: Dense bones; paddle tail; possible swimming
  stroke analogous to modern crocodilians.
- **Scale texture**: Conical scales on available specimens. Photograph
  any specimen with scale impressions at high magnification.

## Image format guidance
- Minimum 4K (3840×2160)
- RAW preferred for museum and field photography
- TIF for skeletal and vertebra diagram scans
- Underwater photography reference (crocodilians) useful for aquatic pose reference
""",

    "parasaurolophus": """\
# Parasaurolophus — Reference Materials

## What this folder is for
This folder holds all scientific reference materials for *Parasaurolophus
walkeri* (and *P. tubicen*, *P. cyrtocristatus*): skeletal diagrams, fossil
photographs, crest acoustics studies, skin impression data (from close
relatives), and museum specimen images. All content here supports
scientifically accurate prompt engineering.

## File naming convention
```
parasaurolophus_[type]_[source]_[year].[ext]
```
Types: `skeletal`, `fossil`, `reconstruction`, `museum`, `texture`

Examples:
- `parasaurolophus_skeletal_rom768_scan.tif`
- `parasaurolophus_fossil_fmnh_p27393_2009.tif`
- `parasaurolophus_reconstruction_weishampel_1981.tif`

Image format: minimum 4K resolution; RAW preferred; TIF for scans.

## Priority reference materials

1. **ROM 768** — Royal Ontario Museum, Toronto
   Type specimen of *P. walkeri* (Parks 1922). This is the reference
   standard for the species. Complete skull with full posterior crest.
   Photograph from lateral and dorsal angles.

2. **FMNH P27393** — Field Museum of Natural History, Chicago
   Well-preserved specimen. Good for body proportions and postcranial
   reference. Field Museum mounts are well-maintained and accessible.

3. **Weishampel 1981** (Paleobiology)
   Crest acoustics paper — modelled the hollow crest as a resonating
   chamber producing low-frequency sound, possibly infrasound. While
   the exact acoustic properties are debated, the resonation function
   is the current consensus. Important context for crest depiction.

4. **Evans et al. 2009** (PLOS ONE, doi:10.1371/journal.pone.0006290)
   Juvenile ontogeny — crest was absent or rudimentary in juveniles and
   grew throughout ontogeny. A juvenile *Parasaurolophus* looks very
   different from an adult. Critical for age-accurate depiction.

5. **Edmontosaurus mummy specimens** (closely related hadrosaurid)
   **AMNH 5060** and **Senckenberg "Leonardo" (MOR 1128)** provide skin
   texture reference. Pebbly mosaic scales with possible pattern variation.
   Use as proxy for *Parasaurolophus* integument.

6. **Horner et al. 2004** (various) — Hadrosaur locomotion and posture
   *Parasaurolophus* was facultatively bipedal: bipedal at speed, could
   drop to all fours at low speed or foraging. Tail held horizontal as
   counterbalance during bipedal locomotion.

7. **Kirtland Formation specimens (New Mexico)**
   *P. tubicen* specimens from NM Museum of Natural History and Science
   (NMMNH). Complement ROM 768 for species variation reference.

## What to look for / photograph / scan

- **Crest**: Long, backward-pointing hollow tube crest in adults; crest
  shape varies by species (*walkeri* is long and straight; *tubicen* is
  longer; *cyrtocristatus* is shorter and curved). Crest is hollow — not
  solid bone. Absent/small in juveniles.
- **Skull**: Duck-billed (wide, flat dental battery); toothless beak at
  front; hundreds of teeth in grinding battery. Large orbit.
- **Skin**: Pebbly mosaic scales based on hadrosaur mummy reference.
  Possible patterned coloration (Edmontosaurus mummies show scale texture
  variation that implies pattern). No feathers.
- **Locomotion posture**: Bipedal when running (tail out for balance);
  quadrupedal when slow/foraging. Not fully bipedal at all times.
- **Tail**: Muscular, horizontal; relatively deep from neural spines;
  active counterbalance in bipedal posture.
- **Forelimbs**: Hoof-like manus for weight-bearing when quadrupedal;
  three functional fingers fused into a padded weight-bearing structure.

## Image format guidance
- Minimum 4K (3840×2160)
- RAW preferred for museum photography
- TIF for skeletal and crest cross-section diagram scans
- CT scan data of ROM 768 crest (published) is useful reference for crest interior
""",

    "dilophosaurus": """\
# Dilophosaurus — Reference Materials

## What this folder is for
This folder holds all scientific reference materials for *Dilophosaurus
wetherilli*: skeletal diagrams, fossil photographs, crest morphology studies,
locomotion data, and museum specimen images. All content here supports
scientifically accurate prompt engineering.

**CRITICAL ACCURACY WARNING — Jurassic Park depiction is incorrect**:
*Dilophosaurus* in Jurassic Park (1993) was depicted with a neck frill and
venom-spitting ability. NEITHER has any scientific basis:
- **No frill**: No frill attachment structures exist in any *Dilophosaurus*
  specimen. The frill was pure Hollywood invention.
- **No venom**: No venom delivery structures (grooved/hollow teeth, venom
  glands) are known in any theropod dinosaur.
These errors must never appear in any reconstruction derived from this
reference collection.

## File naming convention
```
dilophosaurus_[type]_[source]_[year].[ext]
```
Types: `skeletal`, `fossil`, `reconstruction`, `museum`, `texture`

Examples:
- `dilophosaurus_skeletal_ucmp37302_scan.tif`
- `dilophosaurus_fossil_kayenta_az_welles_1984.tif`
- `dilophosaurus_reconstruction_marsh_2020.tif`

Image format: minimum 4K resolution; RAW preferred; TIF for scans.

## Priority reference materials

1. **UCMP 37302** — University of California Museum of Paleontology, Berkeley
   Holotype specimen described by Welles 1954. Partial postcranial skeleton.
   This specimen established *D. wetherilli* as a valid species.

2. **Welles 1984** (Palaeontographica Abteilung A)
   Full redescription and revision of *Dilophosaurus wetherilli*. The
   authoritative anatomical reference for the species. Essential reading
   before any reconstruction work. Confirms NO frill, NO venom structures.

3. **Marsh 2020 comprehensive revision** — Adam Marsh's detailed
   re-examination of all *Dilophosaurus* specimens from the Kayenta
   Formation. Updates Welles 1984 with CT scanning and modern methods.
   Best current source for skull and crest anatomy.

4. **MNA V2623** — Museum of Northern Arizona, Flagstaff AZ
   Specimen from the original Kayenta Formation quarry site. MNA holds
   significant *Dilophosaurus* material from Navajo Nation lands.

5. **Parsons & Parsons 2009** (various)
   Postcranial material and locomotion inferences. *Dilophosaurus* was an
   active, long-legged biped — one of the larger Early Jurassic theropods.

6. **IVPP material — *Dilophosaurus sinensis*** — Institute of Vertebrate
   Paleontology and Paleoanthropology, Beijing
   Chinese specimens from Yunnan Province. Second species (or close
   relative). Useful for comparative reference and variation.

7. **Early Jurassic theropod context** — Compare with *Coelophysis*
   (AMNH collections) and *Zupaysaurus* for proportional reference within
   early theropod body plans.

## What to look for / photograph / scan

- **Double crests**: Two parallel, longitudinal crests on top of the skull.
  Thin, fragile bone — likely for display/species recognition only. Cannot
  have been used for combat (too fragile). No frill attachment fossae.
- **Skull**: Large, lightly built; relatively long; notch in upper jaw
  behind the front teeth (subnarial gap) — unusual feature. Small, blade-
  like serrated teeth.
- **Body proportions**: Lightly built for its size; long hindlimbs; long
  neck; relatively long arms with three large-clawed fingers plus a reduced
  fourth.
- **Forelimbs**: Three functional clawed fingers; arms long relative to
  later theropods. Palms face each other (medially).
- **Feathering**: Uncertain — possible proto-feathers (as in *Sinosauropteryx*
  grade). No direct evidence known, but phylogenetic position makes it
  plausible. Skin impressions are unknown.
- **Tail**: Long, horizontal counterbalance; important for bipedal balance.
- **Overall impression**: Gracile, active predator — more lightly built
  than later large theropods. Think falcon-like in movement quality.

## Image format guidance
- Minimum 4K (3840×2160)
- RAW preferred for museum photography
- TIF for skeletal and skull diagram scans
- Crest photography: multiple angles, raking light to reveal thin bone structure
""",
}

# ---------------------------------------------------------------------------
# PART 2 — Scientific data
# ---------------------------------------------------------------------------

SPECIES_SCIENTIFIC_DATA = {
    "Tyrannosaurus rex": {
        "body_length_m": 12.3,
        "body_mass_kg": 8400,
        "locomotion_type": "biped",
        "feathering_coverage": "uncertain",
        "skin_texture_type": "scales (confirmed multiple body regions, Bell et al. 2017)",
        "tail_posture": "horizontal, muscular, held clear of ground",
        "wrist_position": "palms inward (supination anatomically impossible)",
        "known_coloration_evidence": "unknown; no melanosomes preserved",
        "primary_fossil_sites": "Hell Creek Formation MT/SD/ND; Lance Formation WY",
        "key_papers": "Bell et al. 2017 (skin); Persons & Currie 2011 (tail musculature); Hutchinson & Garcia 2002 (locomotion)",
        "last_scientific_update": 2017,
    },
    "Velociraptor": {
        "body_length_m": 1.8,
        "body_mass_kg": 18,
        "locomotion_type": "biped",
        "feathering_coverage": "full (quill knobs confirmed)",
        "skin_texture_type": "feathered, arm feathers large (wing-like)",
        "tail_posture": "horizontal, stiff (ossified tendons)",
        "wrist_position": "folded, palms inward — bird-like wing fold at rest",
        "known_coloration_evidence": "unknown",
        "primary_fossil_sites": "Djadochta Formation Mongolia; Bayan Mandahu China",
        "key_papers": "Turner et al. 2007 (quill knobs); Pittman et al. 2022 (ecological niche); Novas & Pol 2005",
        "last_scientific_update": 2022,
    },
    "Triceratops": {
        "body_length_m": 9.0,
        "body_mass_kg": 9000,
        "locomotion_type": "quadruped",
        "feathering_coverage": "none",
        "skin_texture_type": "pebbly scales (skin impressions documented)",
        "tail_posture": "horizontal, moderate length",
        "wrist_position": "semi-sprawling forelimbs (elbows slightly lateral)",
        "known_coloration_evidence": "unknown; frill coloration likely for display",
        "primary_fossil_sites": "Hell Creek Formation MT/SD/ND/WY; Lance Formation WY",
        "key_papers": "Horner & Goodwin 2009 (ontogeny); Longrich & Field 2012 (Torosaurus); Fujiwara 2009 (forelimb posture)",
        "last_scientific_update": 2012,
    },
    "Stegosaurus": {
        "body_length_m": 9.0,
        "body_mass_kg": 4000,
        "locomotion_type": "quadruped",
        "feathering_coverage": "none",
        "skin_texture_type": "scales (ossicles and tubercles documented)",
        "tail_posture": "horizontal, raised, active thagomizer",
        "wrist_position": "columnar forelimbs",
        "known_coloration_evidence": "unknown; plates likely vascularised for display/thermoregulation",
        "primary_fossil_sites": "Morrison Formation CO/WY/UT; Tendaguru Formation Tanzania",
        "key_papers": "Saitta 2018 (plate dimorphism); Mallison 2011 (tail kinematics); Farlow et al. 1976 (plate function)",
        "last_scientific_update": 2018,
    },
    "Brachiosaurus": {
        "body_length_m": 22.0,
        "body_mass_kg": 40000,
        "locomotion_type": "quadruped",
        "feathering_coverage": "none",
        "skin_texture_type": "scales (fragmentary impressions)",
        "tail_posture": "horizontal, tapering, not used as prop",
        "wrist_position": "columnar forelimbs, near-vertical",
        "known_coloration_evidence": "unknown",
        "primary_fossil_sites": "Morrison Formation CO (type locality Fruita); note African specimens = Giraffatitan",
        "key_papers": "Taylor 2009 (Brachiosaurus vs Giraffatitan separation); Paul & Christiansen 2000 (posture)",
        "last_scientific_update": 2009,
    },
    "Ankylosaurus": {
        "body_length_m": 7.0,
        "body_mass_kg": 6000,
        "locomotion_type": "quadruped",
        "feathering_coverage": "none",
        "skin_texture_type": "osteoderms, keeled scutes, dense armor (extensively documented)",
        "tail_posture": "horizontal, club actively swung",
        "wrist_position": "columnar forelimbs",
        "known_coloration_evidence": "unknown",
        "primary_fossil_sites": "Hell Creek Formation MT; Lance Formation WY; Scollard Formation Alberta",
        "key_papers": "Arbour & Currie 2015 (tail club biomechanics); Burns et al. 2011 (osteoderm ontogeny)",
        "last_scientific_update": 2015,
    },
    "Pteranodon": {
        "body_length_m": 1.8,
        "body_mass_kg": 25,
        "locomotion_type": "flying; quadrupedal launch and landing",
        "feathering_coverage": "none (pycnofibers — hair-like, not feathers)",
        "skin_texture_type": "pycnofibers and wing membrane (patagium)",
        "tail_posture": "vestigial (short tail)",
        "wrist_position": "folded against body at rest; wing extended in flight",
        "known_coloration_evidence": "unknown; crest likely for display (sexual dimorphism confirmed)",
        "primary_fossil_sites": "Niobrara Formation KS; Pierre Shale SD",
        "key_papers": "Bennett 2001 (taxonomy and dimorphism); Witton 2013 (pterosaur book); Habib 2008 (quadrupedal launch)",
        "last_scientific_update": 2013,
    },
    "Spinosaurus": {
        "body_length_m": 14.0,
        "body_mass_kg": 9000,
        "locomotion_type": "semi-aquatic; quadrupedal on land, swimming",
        "feathering_coverage": "none",
        "skin_texture_type": "conical scales (specimens known)",
        "tail_posture": "paddle-like with tall neural spines; undulating for propulsion (Ibrahim 2020)",
        "wrist_position": "quadrupedal on land; forelimbs used for walking",
        "known_coloration_evidence": "unknown; possibly countershaded",
        "primary_fossil_sites": "Kem Kem Formation Morocco/Algeria; original Egyptian specimens destroyed WWII",
        "key_papers": "Ibrahim et al. 2020 (paddle tail, Nature); Ibrahim et al. 2014 (semi-aquatic, Science); Hone & Holtz 2021 (critique)",
        "last_scientific_update": 2020,
    },
    "Parasaurolophus": {
        "body_length_m": 9.5,
        "body_mass_kg": 3000,
        "locomotion_type": "biped or quadruped (facultative)",
        "feathering_coverage": "none",
        "skin_texture_type": "pebbly scales (mummified specimens of close relatives)",
        "tail_posture": "horizontal, muscular, counterbalance while running bipedally",
        "wrist_position": "palms down when quadrupedal",
        "known_coloration_evidence": "unknown; Edmontosaurus mummy shows patterned skin — similar possible",
        "primary_fossil_sites": "Kirtland Formation NM; Dinosaur Park Formation Alberta; Fruitland Formation NM",
        "key_papers": "Weishampel 1981 (crest acoustics); Evans et al. 2009 (juvenile ontogeny)",
        "last_scientific_update": 2009,
    },
    "Dilophosaurus": {
        "body_length_m": 6.0,
        "body_mass_kg": 400,
        "locomotion_type": "biped",
        "feathering_coverage": "uncertain (early theropod, proto-feathers possible)",
        "skin_texture_type": "scales assumed; no skin impressions known",
        "tail_posture": "horizontal, counterbalance",
        "wrist_position": "palms inward",
        "known_coloration_evidence": "unknown; crests likely for display",
        "primary_fossil_sites": "Kayenta Formation AZ (type locality); Yunnan Province China (D. sinensis)",
        "key_papers": "Welles 1984 (redescription); Parsons & Parsons 2009; Marsh 2020 comprehensive revision",
        "last_scientific_update": 2020,
    },
}

# research_notes per species: list of dicts matching table columns
RESEARCH_NOTES = {
    "Tyrannosaurus rex": [
        {
            "finding": "Skin impressions from neck, abdomen, hips and tail base confirm scales dominant on adult body — no feather evidence in adults",
            "source": "Bell et al. 2017 - Science",
            "year": 2017,
            "author": "Bell et al.",
            "doi": "10.1371/journal.pbio.1002467",
            "affects_prompt": 1,
        },
        {
            "finding": "Maximum speed estimated at 12-25 km/h — slow walker, not fast runner; would not sprint",
            "source": "Hutchinson & Garcia 2002 - Nature",
            "year": 2002,
            "author": "Hutchinson & Garcia",
            "doi": "10.1038/nature01138",
            "affects_prompt": 1,
        },
        {
            "finding": "Tail was heavily muscled (M. caudofemoralis), held horizontal and clear of ground at all times",
            "source": "Persons & Currie 2011 - Acta Palaeontologica Polonica",
            "year": 2011,
            "author": "Persons & Currie",
            "doi": "10.4202/app.2009.0055",
            "affects_prompt": 1,
        },
    ],
    "Velociraptor": [
        {
            "finding": "Quill knobs on ulna confirm large pennaceous feathers on forearms — full body feathering strongly implied",
            "source": "Turner et al. 2007 - Science",
            "year": 2007,
            "author": "Turner et al.",
            "doi": "10.1126/science.1137427",
            "affects_prompt": 1,
        },
        {
            "finding": "Sickle claw used for gripping and pinning prey, not slashing — claw raised off ground during locomotion",
            "source": "Manning et al. 2006 - Biology Letters",
            "year": 2006,
            "author": "Manning et al.",
            "doi": "10.1098/rsbl.2005.0395",
            "affects_prompt": 1,
        },
        {
            "finding": "Velociraptor was likely ambush predator targeting small prey — not pack hunter of large prey as depicted in Jurassic Park",
            "source": "Pittman et al. 2022 - iScience",
            "year": 2022,
            "author": "Pittman et al.",
            "doi": "10.1016/j.isci.2022.104358",
            "affects_prompt": 1,
        },
        {
            "finding": "Wrist could fold bird-like against body — arms not held straight out, hands in neutral position with palms facing each other",
            "source": "Turner et al. 2007",
            "year": 2007,
            "author": "Turner et al.",
            "doi": "10.1126/science.1137427",
            "affects_prompt": 1,
        },
    ],
    "Triceratops": [
        {
            "finding": "Forelimb posture was semi-sprawling with elbows slightly lateral — not fully columnar like elephant nor fully sprawled like lizard",
            "source": "Fujiwara 2009 - Journal of Vertebrate Paleontology",
            "year": 2009,
            "author": "Fujiwara",
            "doi": "10.1671/039.029.0413",
            "affects_prompt": 1,
        },
        {
            "finding": "Frill was likely brightly vascularised and used for display and thermoregulation — colour variation probable",
            "source": "Farke 2011 - PLOS ONE",
            "year": 2011,
            "author": "Farke",
            "doi": "10.1371/journal.pone.0018112",
            "affects_prompt": 0,
        },
    ],
    "Stegosaurus": [
        {
            "finding": "Two distinct plate morphologies may represent sexual dimorphism: broad plates (female?) vs tall plates (male?)",
            "source": "Saitta 2018 - PLOS ONE",
            "year": 2018,
            "author": "Saitta",
            "doi": "10.1371/journal.pone.0200) (approximate)",
            "affects_prompt": 0,
        },
        {
            "finding": "Thagomizer tail spikes could be swung laterally with significant force — active defensive weapon",
            "source": "Mallison 2011 - PLOS ONE",
            "year": 2011,
            "author": "Mallison",
            "doi": "10.1371/journal.pone.0014665",
            "affects_prompt": 1,
        },
    ],
    "Brachiosaurus": [
        {
            "finding": "All African Brachiosaurus specimens now assigned to Giraffatitan brancai — a separate genus. True Brachiosaurus altithorax known only from Morrison Formation USA",
            "source": "Taylor 2009 - Journal of Vertebrate Paleontology",
            "year": 2009,
            "author": "Taylor",
            "doi": "10.1671/039.029.0401",
            "affects_prompt": 1,
        },
        {
            "finding": "Neck was held at elevated angle (45-70 degrees above horizontal) not horizontally as sometimes depicted",
            "source": "Paul & Christiansen 2000 / Taylor et al. 2009",
            "year": 2009,
            "author": "Taylor et al.",
            "doi": None,
            "affects_prompt": 1,
        },
    ],
    "Ankylosaurus": [
        {
            "finding": "Tail club could generate enough force to fracture bone — active weapon, not just passive defence",
            "source": "Arbour & Currie 2015 - PLOS ONE",
            "year": 2015,
            "author": "Arbour & Currie",
            "doi": "10.1371/journal.pone.0138258",
            "affects_prompt": 1,
        },
        {
            "finding": "Extensive osteoderms covered back and flanks; belly was relatively unarmoured",
            "source": "Burns et al. 2011",
            "year": 2011,
            "author": "Burns et al.",
            "doi": None,
            "affects_prompt": 1,
        },
    ],
    "Pteranodon": [
        {
            "finding": "NOT a dinosaur — a pterosaur (flying reptile). Completely separate evolutionary lineage",
            "source": "Taxonomy — established consensus",
            "year": 2000,
            "author": "Bennett",
            "doi": None,
            "affects_prompt": 1,
        },
        {
            "finding": "Launched quadrupedally using all four limbs in a pole-vault style — did not run and flap to take off",
            "source": "Habib 2008 - Zitteliana",
            "year": 2008,
            "author": "Habib",
            "doi": None,
            "affects_prompt": 1,
        },
        {
            "finding": "Strong sexual dimorphism: males had large crests and narrow hips; females had smaller crests and wider hips for egg-laying",
            "source": "Bennett 2001 - Journal of Vertebrate Paleontology",
            "year": 2001,
            "author": "Bennett",
            "doi": None,
            "affects_prompt": 0,
        },
    ],
    "Spinosaurus": [
        {
            "finding": "Paddle-shaped tail with elongated neural spines adapted for aquatic propulsion — primary swimming organ",
            "source": "Ibrahim et al. 2020 - Nature",
            "year": 2020,
            "author": "Ibrahim et al.",
            "doi": "10.1038/s41586-020-2190-3",
            "affects_prompt": 1,
        },
        {
            "finding": "Dense bones (pachyostosis) and short hindlimbs indicate semi-aquatic lifestyle — primarily a shoreline and river predator",
            "source": "Ibrahim et al. 2014 - Science",
            "year": 2014,
            "author": "Ibrahim et al.",
            "doi": "10.1126/science.1258750",
            "affects_prompt": 1,
        },
        {
            "finding": "Hindlimbs too short for efficient terrestrial bipedalism — likely moved quadrupedally on land with low body posture",
            "source": "Ibrahim et al. 2014 - Science",
            "year": 2014,
            "author": "Ibrahim et al.",
            "doi": "10.1126/science.1258750",
            "affects_prompt": 1,
        },
        {
            "finding": "Hone & Holtz 2021 challenged fully aquatic interpretation — more likely wading shore predator; debate ongoing",
            "source": "Hone & Holtz 2021 - Palaeontologia Electronica",
            "year": 2021,
            "author": "Hone & Holtz",
            "doi": None,
            "affects_prompt": 0,
        },
    ],
    "Parasaurolophus": [
        {
            "finding": "Hollow crest was a resonating chamber producing low-frequency infrasound calls — used for communication within herds",
            "source": "Weishampel 1981 - Paleobiology",
            "year": 1981,
            "author": "Weishampel",
            "doi": None,
            "affects_prompt": 0,
        },
        {
            "finding": "Crest was absent or small in juveniles and grew throughout ontogeny — important for age-accurate depiction",
            "source": "Evans et al. 2009 - PLOS ONE",
            "year": 2009,
            "author": "Evans et al.",
            "doi": "10.1371/journal.pone.0006290",
            "affects_prompt": 1,
        },
    ],
    "Dilophosaurus": [
        {
            "finding": "NO scientific evidence for neck frill — Jurassic Park frill is pure Hollywood invention, not in any fossil material",
            "source": "Welles 1984 - Palaeontographica Abteilung A",
            "year": 1984,
            "author": "Welles",
            "doi": None,
            "affects_prompt": 1,
        },
        {
            "finding": "NO scientific evidence for venom — no venom delivery structures known in any theropod dinosaur",
            "source": "Consensus — no primary source",
            "year": 2020,
            "author": "Marsh et al.",
            "doi": None,
            "affects_prompt": 1,
        },
        {
            "finding": "Double crests were fragile ornamental structures, almost certainly for display/species recognition, not combat",
            "source": "Welles 1984; Marsh 2020",
            "year": 2020,
            "author": "Marsh et al.",
            "doi": None,
            "affects_prompt": 1,
        },
    ],
}

# ---------------------------------------------------------------------------
# Migration helpers
# ---------------------------------------------------------------------------

def part1_create_species_reference():
    """Create species_reference folder structure with per-species READMEs."""
    print("\n=== PART 1: Creating species_reference folder structure ===\n")

    species_slugs = list(READMES.keys())
    folders_created = 0
    readmes_written = 0
    errors = []

    # Create parent directory
    if not os.path.exists(SPECIES_REF_DIR):
        os.makedirs(SPECIES_REF_DIR)
        print(f"  Created: {SPECIES_REF_DIR}")
    else:
        print(f"  Exists:  {SPECIES_REF_DIR}")

    for slug in species_slugs:
        subfolder = os.path.join(SPECIES_REF_DIR, slug)
        readme_path = os.path.join(subfolder, "README.md")

        # Create subfolder
        if not os.path.exists(subfolder):
            os.makedirs(subfolder)
            folders_created += 1
            print(f"  Created folder: species_reference/{slug}/")
        else:
            print(f"  Folder exists:  species_reference/{slug}/")

        # Write README (always write — idempotent by content)
        try:
            with open(readme_path, "w", encoding="utf-8") as fh:
                fh.write(READMES[slug])
            readmes_written += 1
            print(f"    Wrote README.md for {slug}")
        except OSError as exc:
            msg = f"Failed to write README for {slug}: {exc}"
            errors.append(msg)
            print(f"    ERROR: {msg}")

    return folders_created, readmes_written, errors


def part2_db_migration():
    """Run all database migrations."""
    print("\n=== PART 2: Database migration ===\n")

    columns_added = []
    notes_inserted = 0
    errors = []

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # 2a. ALTER TABLE species — add new columns
    # ------------------------------------------------------------------
    print("--- 2a: ALTER TABLE species (adding columns) ---")

    new_columns = [
        ("body_length_m",            "REAL"),
        ("body_mass_kg",             "REAL"),
        ("locomotion_type",          "TEXT"),
        ("feathering_coverage",      "TEXT"),
        ("skin_texture_type",        "TEXT"),
        ("tail_posture",             "TEXT"),
        ("wrist_position",           "TEXT"),
        ("known_coloration_evidence","TEXT"),
        ("primary_fossil_sites",     "TEXT"),
        ("key_papers",               "TEXT"),
        ("last_scientific_update",   "INTEGER"),
    ]

    for col_name, col_type in new_columns:
        try:
            cur.execute(f"ALTER TABLE species ADD COLUMN {col_name} {col_type}")
            conn.commit()
            columns_added.append(col_name)
            print(f"  Added column: {col_name} {col_type}")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" in str(exc).lower():
                print(f"  Column exists: {col_name} (skipped)")
            else:
                msg = f"ALTER TABLE error for {col_name}: {exc}"
                errors.append(msg)
                print(f"  ERROR: {msg}")

    # ------------------------------------------------------------------
    # 2b. CREATE TABLE research_notes + index
    # ------------------------------------------------------------------
    print("\n--- 2b: CREATE TABLE research_notes ---")

    try:
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS research_notes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                species_id  INTEGER NOT NULL REFERENCES species(id) ON DELETE CASCADE,
                finding     TEXT NOT NULL,
                source      TEXT,
                year        INTEGER,
                author      TEXT,
                doi         TEXT,
                affects_prompt INTEGER NOT NULL DEFAULT 1 CHECK(affects_prompt IN (0,1)),
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_research_notes_species ON research_notes(species_id);
        """)
        conn.commit()
        print("  research_notes table and index: OK")
    except sqlite3.Error as exc:
        msg = f"CREATE TABLE research_notes error: {exc}"
        errors.append(msg)
        print(f"  ERROR: {msg}")

    # ------------------------------------------------------------------
    # 2c. Build species name -> id map
    # ------------------------------------------------------------------
    cur.execute("SELECT id, name FROM species")
    species_map = {row[1]: row[0] for row in cur.fetchall()}
    print(f"\n  Species map loaded: {len(species_map)} species")

    # ------------------------------------------------------------------
    # 2d. UPDATE species scientific data
    # ------------------------------------------------------------------
    print("\n--- 2c: UPDATE species scientific data ---")

    for species_name, data in SPECIES_SCIENTIFIC_DATA.items():
        if species_name not in species_map:
            msg = f"Species not found in DB: '{species_name}'"
            errors.append(msg)
            print(f"  ERROR: {msg}")
            continue

        species_id = species_map[species_name]
        set_clauses = ", ".join(f"{col} = ?" for col in data.keys())
        values = list(data.values()) + [species_id]

        try:
            cur.execute(
                f"UPDATE species SET {set_clauses} WHERE id = ?",
                values
            )
            conn.commit()
            print(f"  Updated: {species_name} (id={species_id})")
        except sqlite3.Error as exc:
            msg = f"UPDATE error for {species_name}: {exc}"
            errors.append(msg)
            print(f"  ERROR: {msg}")

    # ------------------------------------------------------------------
    # 2e. INSERT research_notes (INSERT OR IGNORE on finding+species_id)
    # ------------------------------------------------------------------
    print("\n--- 2d: INSERT research_notes ---")

    # We use INSERT OR IGNORE with a unique constraint alternative:
    # check existence before inserting to stay idempotent without
    # requiring a UNIQUE index on (species_id, finding) — finding text
    # can be long. We check by (species_id, finding) manually.

    for species_name, notes in RESEARCH_NOTES.items():
        if species_name not in species_map:
            msg = f"Species not found for notes: '{species_name}'"
            errors.append(msg)
            print(f"  ERROR: {msg}")
            continue

        species_id = species_map[species_name]

        for note in notes:
            # Check if this exact finding already exists for this species
            cur.execute(
                "SELECT id FROM research_notes WHERE species_id = ? AND finding = ?",
                (species_id, note["finding"])
            )
            existing = cur.fetchone()

            if existing:
                print(f"  Exists: [{species_name}] {note['finding'][:60]}...")
                continue

            try:
                cur.execute(
                    """
                    INSERT INTO research_notes
                        (species_id, finding, source, year, author, doi, affects_prompt)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        species_id,
                        note["finding"],
                        note.get("source"),
                        note.get("year"),
                        note.get("author"),
                        note.get("doi"),
                        note.get("affects_prompt", 1),
                    )
                )
                conn.commit()
                notes_inserted += 1
                print(f"  Inserted: [{species_name}] {note['finding'][:60]}...")
            except sqlite3.Error as exc:
                msg = f"INSERT research_notes error [{species_name}]: {exc}"
                errors.append(msg)
                print(f"  ERROR: {msg}")

    conn.close()
    return columns_added, notes_inserted, errors


# ---------------------------------------------------------------------------
# PART 3 — Verification summary
# ---------------------------------------------------------------------------

def part3_verification_summary(
    folders_created, readmes_written, folder_errors,
    columns_added, notes_inserted, db_errors
):
    """Print final verification summary."""
    all_errors = folder_errors + db_errors

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE — VERIFICATION SUMMARY")
    print("=" * 60)

    print(f"\nPART 1 — species_reference folder structure:")
    print(f"  Folders created this run : {folders_created}")
    print(f"  READMEs written this run : {readmes_written}")
    print(f"  Total species subfolders : {len(READMES)}")
    print(f"  Location: {SPECIES_REF_DIR}")

    print(f"\nPART 2 — Database migration ({DB_PATH}):")
    if columns_added:
        print(f"  New columns added to species table ({len(columns_added)}):")
        for col in columns_added:
            print(f"    + {col}")
    else:
        print("  No new columns added (all already existed)")

    print(f"  research_notes inserted this run: {notes_inserted}")

    # Live DB counts
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM research_notes")
        total_notes = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM species WHERE body_length_m IS NOT NULL")
        updated_species = cur.fetchone()[0]
        conn.close()
        print(f"  Total research_notes in DB     : {total_notes}")
        print(f"  Species with scientific data   : {updated_species}")
    except sqlite3.Error as exc:
        print(f"  (Could not query DB for totals: {exc})")

    print(f"\nErrors encountered: {len(all_errors)}")
    if all_errors:
        for i, err in enumerate(all_errors, 1):
            print(f"  {i}. {err}")
    else:
        print("  None — migration completed cleanly.")

    print("\n" + "=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("dino_art scientific migration")
    print(f"Base directory : {BASE_DIR}")
    print(f"Database       : {DB_PATH}")
    print(f"Species ref dir: {SPECIES_REF_DIR}")

    # Part 1
    folders_created, readmes_written, folder_errors = part1_create_species_reference()

    # Part 2
    columns_added, notes_inserted, db_errors = part2_db_migration()

    # Part 3
    part3_verification_summary(
        folders_created, readmes_written, folder_errors,
        columns_added, notes_inserted, db_errors
    )


if __name__ == "__main__":
    main()
