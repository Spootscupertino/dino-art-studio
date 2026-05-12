# Reference Image Sourcing & Curation Plan

**Goal:** 50+ legally-licensed T. rex reference images, organized by anatomy zone, validated against [tyrannosaurus.md](refs/anatomy_theses/tyrannosaurus.md), ready for LoRA training.

**Timeline:** 2–3 weeks (part-time sourcing + curation)  
**Outcome:** 50+ images in `assets/gallery/flux/training_refs/trex_v2/` with captions + metadata

---

## Legal Framework

**What's allowed:**
- ✅ Museum high-res photos (Smithsonian, Natural History Museum London, etc.) — public domain or CC0
- ✅ Academic paleoart (peer-reviewed publications, author-licensed CC-BY)
- ✅ Professional paleoart (Mark Norell, Julius Csotonyi, etc.) — ask for permission, cite author
- ✅ Living analog wildlife (cassowary, emu, ostrich legs; crocodile jaws; eagle talons) — wildlife photographers CC-BY or purchased rights
- ✅ Your own generated images (Flux/MJ outputs from Phase 1–2) — you own them
- ✅ Skeletal diagrams from open-access papers (PalArch, PeerJ)

**What's NOT allowed:**
- ❌ Copyrighted museum photos without permission (Getty Images, Alamy, etc.)
- ❌ Stock dinosaur art (Adobe Stock, Shutterstock)
- ❌ Fan art without explicit author permission
- ❌ Screenshots from documentaries (BBC, Netflix)

---

## Source Categories & Where to Find Them

### 1. Museum Specimens (High-Res Photography) — 10–15 images

| Source | URL | What to look for |
|---|---|---|
| **Smithsonian (NMNH)** | https://collections.si.edu | Search "Tyrannosaurus" — high-res skeletal specimens, posture photos |
| **Natural History Museum London** | http://www.nhm.ac.uk | Specimen database, full skeletons, tooth close-ups |
| **American Museum of Natural History** | https://www.amnh.org/exhibitions | Public domain specimen photography |
| **University of Chicago PaleoLab** | http://paleolabs.uchicago.edu | T. rex skeletal anatomy, casts, proportions |

**What to collect:**
- Full skeleton overhead shots (for posture + proportions)
- Skull from multiple angles (dorsal, ventral, lateral)
- Hand/foot close-ups (claw morphology, digit arrangement)
- Tail vertebrae (for rigidity assessment)

**Licensing check:** Always verify CC0 or public domain. Screenshot + note license URL.

---

### 2. Paleoart (Licensed Scientific Illustration) — 15–20 images

| Artist | Portfolio/Paper | How to contact |
|---|---|---|
| **Julius Csotonyi** | https://www.csotonyi.com | Professional paleoartist; ask via website |
| **Mark Norell** | AMNH staff; publications | Co-author on many T. rex papers, cite papers |
| **Nizar Ibrahim** | University of Detroit Mercy | Email institutional address for research use |
| **Emily Willoughby** | https://emilywilloughby.com | Licensed paleoart, CC-BY available |
| **Matt Martyniuk** | DeviantArt / Archosaur Musings | Creative Commons license on many pieces |

**What to look for:**
- Anatomically-corrected posture (bipedal, slight forward lean, elevated tail)
- Accurate hand morphology (3 digits with claws, correct orientation)
- Realistic skin texture (reptilian, not feathered)
- Proportional skull-to-body ratio
- Natural habitat context (but you'll crop reference focus)

**How to source:**
1. Google "[artist name] + T. rex + CC-BY"
2. Check the paper license (many are open-access)
3. Email the artist: "Using your paleoart for LoRA training on a commercial dinosaur site, can I license image X?"
4. Keep a CSV: `artist, image_title, license_type, permission_email, date_obtained`

---

### 3. Living Analog Wildlife — 10–15 images

These teach anatomy features that are hard to sculpt from fossils alone.

| Feature | Living Analog | Where to find |
|---|---|---|
| **Leg posture & foot structure** | Cassowary, Emu | Wikimedia Commons (search "cassowary foot"), Flickr (CC-BY wildlife photographers) |
| **Jaw mechanics & dentition** | Saltwater Crocodile, Alligator | Smithsonian Photo Initiative, National Geographic open-access |
| **Claw morphology** | Harpy Eagle, Velociraptor-sized raptors | Wikimedia Commons, Audubon Society |
| **Skin texture** | Saltwater Croc, Monitor Lizard | Wildlife photography databases |
| **Eye position & skull shape** | Cassowary (similar head crest + eye placement) | Natural history museum collections |

**Quality sources:**
- **Wikimedia Commons** — https://commons.wikimedia.org (search by license: CC-BY, CC0)
- **Flickr CC Pool** — https://www.flickr.com/search/?license=2,3,4,5,6,9 (CC-BY photographers)
- **iNaturalist** — https://www.inaturalist.org (wildlife with CC licenses)
- **Smithsonian Photo Initiative** — https://www.si.edu/collections-search (open-access photos)

**CSV tracking:** `source_type, animal, feature, license, url, date_accessed`

---

### 4. Your Own Generated Outputs — 5–10 images

Use Phase 1–2 Flux/MJ images that scored 8+ on anatomy and didn't ship to Etsy yet (call them "training-use-only").

**Why include:** They anchor to your target style (telephoto, natural light, habitat).

---

## Curation Workflow

### Step 1: Batch Download (~1 week)
```
~/Desktop/Jurassinkart/Source Images/
├── museums/
│   ├── smithsonian_trex_skeleton_1.jpg
│   ├── nhm_london_skull_dorsal.jpg
│   └── ... (10–15 images)
├── paleoart/
│   ├── csotonyi_trex_posture_1.jpg
│   ├── willoughby_trex_habitat_1.jpg
│   └── ... (15–20 images)
├── living_analogs/
│   ├── cassowary_foot_lateral.jpg
│   ├── crocodile_jaw_ventral.jpg
│   └── ... (10–15 images)
└── metadata.csv
```

**Metadata CSV format:**
```
source_type,filename,original_source,artist,license_type,license_url,permission_email,notes,anatomy_zone
museum,smithsonian_trex_skull_dorsal.jpg,Smithsonian NMNH,—,CC0,https://collections.si.edu,—,Full dorsal view,skull
paleoart,csotonyi_trex_habitat.jpg,Csotonyi.com,Julius Csotonyi,CC-BY,https://csotonyi.com,julius@csotonyi.com,Good posture reference,full_body
living_analog,cassowary_foot_1.jpg,Wikimedia Commons,[photographer],CC-BY,https://commons.wikimedia.org,—,Bipedal foot structure,feet
```

---

### Step 2: Anatomy-Zone Tagging (~1 week)

Tag each image by which anatomy zone it best teaches:

| Zone | What's scored | Example refs |
|---|---|---|
| **skull** | Dorsal/ventral profiles, eye placement, tooth row, crest proportions | Museum photos, paleoart closeups |
| **hands** | 3-finger arrangement, claw morphology, palm orientation | Museum skeletal, eagle talons, museum photos |
| **feet** | Digitigrade posture, toe alignment, claw size vs. hand | Cassowary legs, museum skeletal, museum photos |
| **posture** | Forward-leaning trunk, tail elevation, limb angles | Paleoart full-body, cassowary side view |
| **skin** | Reptilian texture, scale patterns, color tone | Crocodile photos, Csotonyi paleoart, your Flux outputs |

**How to tag:** Run `reference.py` with `--zone skull` flag, or add to CSV:

```
anatomy_zone,strength_1_10
skull,9
hands,7
feet,8
posture,6
skin,5
```

---

### Step 3: Validate Against Anatomy Thesis

Read [refs/anatomy_theses/tyrannosaurus.md](refs/anatomy_theses/tyrannosaurus.md), then for each image, check:

**5 scoring categories (from thesis):**
1. ✅ Posture: Forward-leaning trunk, elevated tail, bent-knee stance?
2. ✅ Hands: 3 digits, claws forward-facing, correct proportions?
3. ✅ Feet: Digitigrade, 3 main toes + dewclaw, correct stride?
4. ✅ Skull-body ratio: Head ~1/10 of body length?
5. ✅ Realism: Natural lighting, habitat plausible?

**Auto-reject if:**
- Kangaroo posture (tail dragging, upright spine)
- 2-finger or 4-finger hands
- Feathered T. rex (except small proto-feathers on back)
- Incorrect skull proportions (too small/large)

**How to score:** Use `feedback` command on each image:
```bash
$ feedback ~/Desktop/Jurassinkart/Source\ Images/museums/smithsonian_trex_skull.jpg
Rating (1-10)? 8
Anatomy notes? Museum dorsal skull profile, correct crest proportions, eye placement good
Source type? museum
Anatomy zones (comma-separated)? skull,posture
```

This auto-populates `winners.json` with `signal_type: anatomy_ref`.

---

### Step 4: Ingest via Drop-Folder Pipeline

Once validated, move images to the standard training pipeline:

```bash
mkdir -p ~/Desktop/Jurassinkart/Training\ Drops/tyrannosaurus/museum
mkdir -p ~/Desktop/Jurassinkart/Training\ Drops/tyrannosaurus/paleoart
mkdir -p ~/Desktop/Jurassinkart/Training\ Drops/tyrannosaurus/living_analog

# Move validated images
mv ~/Desktop/Jurassinkart/Source\ Images/museums/*.jpg ~/Desktop/Jurassinkart/Training\ Drops/tyrannosaurus/museum/
mv ~/Desktop/Jurassinkart/Source\ Images/paleoart/*.jpg ~/Desktop/Jurassinkart/Training\ Drops/tyrannosaurus/paleoart/
mv ~/Desktop/Jurassinkart/Source\ Images/living_analog/*.jpg ~/Desktop/Jurassinkart/Training\ Drops/tyrannosaurus/living_analog/

# Run the ingest pipeline
python3 flux/ingest_training_drops.py --species tyrannosaurus --auto-caption
```

This moves images to `assets/gallery/flux/training_refs/tyrannosaurus/` and auto-generates `.txt` captions.

---

### Step 5: Export for LoRA Training

```bash
python3 flux/export_dataset.py --species tyrannosaurus --output-path flux/datasets/dino_refs_v2/
```

Output: `flux/datasets/dino_refs_v2/` with symlinked images, `dataset.json` metadata, species summary.

---

## Tracking & Accountability

### Metadata CSV (as you go)
Keep one CSV at `refs/sourcing_log.csv`:

```
date_added,source_type,filename,artist,license_type,license_url,permission_email,permission_date,anatomy_zones,thesis_score,notes
2026-05-15,museum,smithsonian_trex_skull.jpg,—,CC0,https://collections.si.edu,—,—,skull|posture,9,Perfect dorsal profile
2026-05-15,paleoart,csotonyi_habitat_v1.jpg,Julius Csotonyi,CC-BY,https://csotonyi.com,julius@csotonyi.com,2026-05-14,full_body|posture,8,Permission granted for LoRA training
2026-05-16,living_analog,cassowary_foot.jpg,[photographer],CC-BY,https://commons.wikimedia.org,—,—,feet|posture,8,Flickr CC search result
```

### Winners.json Validation

Every image ingested should appear in `winners.json` with:
```json
{
  "signal_type": "anatomy_ref",
  "species": "tyrannosaurus",
  "filename": "smithsonian_trex_skull.jpg",
  "source_type": "museum",
  "license": "CC0",
  "license_url": "https://collections.si.edu",
  "anatomy_zones": ["skull", "posture"],
  "thesis_score": 9,
  "notes": "Perfect dorsal profile for skull validation"
}
```

---

## Timeline Estimate

| Phase | Duration | Tasks |
|---|---|---|
| **Sourcing** | 5–7 days | Batch download + metadata logging |
| **Tagging** | 3–4 days | Anatomy zone assignment + thesis validation |
| **Ingestion** | 2–3 days | Move to pipeline, run captions, export dataset |
| **Testing** | 3–5 days | Train LoRA on 50+ refs, generate test batch, rate vs. thesis |

**Total:** 2–3 weeks (working 1–2 hours per day).

---

## Success Criteria

- ✅ 50+ images in `assets/gallery/flux/training_refs/tyrannosaurus/`
- ✅ 100% of images scored & tagged in `winners.json` (signal_type: anatomy_ref)
- ✅ Anatomy zones (skull, hands, feet, posture, skin) distributed evenly (8–12 images per zone)
- ✅ License URLs logged + permission emails sent where needed
- ✅ Zero auto-reject violations (no kangaroo posture, no 2-finger hands, no feathered T. rex)
- ✅ `sourcing_log.csv` complete + committed to repo
- ✅ LoRA trains without errors on resulting dataset

---

## Next After This

Once 50+ refs are ingested & LoRA is trained:
- **A/B test:** 25 paired seeds with/without LoRA
- **LLaVA validation:** Auto-check generated images for anatomical errors
- **Species expansion:** Repeat sourcing for Trike + Stego
