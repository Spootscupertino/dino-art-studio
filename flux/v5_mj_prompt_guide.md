# v5 Dataset — MJ Prompt Guide

Pure MJ references only. No skeletons, no living analogs, no birds.
Drop images into the folder that matches what's in the shot.

---

## Hard digit rules (enforce in every prompt that shows limbs)

**Forelimb:** `two-fingered forelimb, digits I and II only, no third finger, short arm, wrist barely clears chest, palms facing inward`

**Hindfoot:** `four-toed foot, elevated hallux dewclaw at rear, three load-bearing toes II III IV, digitigrade stance on toe tips, laterally compressed recurved claws`

---

## v5_portrait_frontal
**What:** Frontal face, both eyes visible, full skull width, jaw slightly open or closed.  
**Target:** 8–10 images

**Prompt skeleton:**
```
Hyper-realistic frontal portrait of a Tyrannosaurus rex, both amber eyes staring forward, 
full skull width visible, [jaw open showing teeth / jaw closed], 
interlocking polygon scale mosaic across snout and orbital ridges, 
raised keeled scutes casting micro-shadows, warm amber-brown-grey coloration, 
cinematic macro photography, shallow depth of field, dark moody background, 
8K photorealistic --ar 2:3 --stylize 750
```

**Vary:** jaw open vs closed, eye color (amber / gold / pale green), background (water / jungle mist / dark studio), lighting direction.

---

## v5_portrait_3quarter
**What:** 3/4 angle, jaw line and one eye dominant, neck visible.  
**Target:** 8–10 images

**Prompt skeleton:**
```
Hyper-realistic three-quarter portrait of a Tyrannosaurus rex, 
powerful jaw line prominent, single amber eye in sharp focus, 
neck musculature visible, polygon scale mosaic with keeled ridges, 
[open jaw exposing recurved teeth / closed jaw, lips present], 
cinematic rim lighting, volumetric atmosphere, 8K photorealistic --ar 3:4 --stylize 750
```

**Vary:** jaw state, lighting (golden hour / cool overcast / rim only), neck twist direction.

---

## v5_mouth_macro
**What:** Extreme close-up inside or at the mouth. This is our weakest area — shoot the most of these.  
**Target:** 10–12 images

**Priority sub-shots:**
- Corner of the lip / jaw hinge
- Full open jaw from front — teeth + gumline + palate + tongue
- Single tooth in focus — root visible in gumline, tip recurved
- Saliva / moisture detail at jaw corner
- Inside palate looking out

**Prompt skeleton:**
```
Hyper-realistic extreme macro of Tyrannosaurus rex open mouth, 
individual recurved conical teeth anchored visibly in exposed grey-pink gumline, 
fleshy soft tissue lining jaw margin, saliva beading at jaw corner, 
mottled tongue surface, ridged palate, wet tooth enamel with specular highlights, 
macro lens compression, razor-thin depth of field, photorealistic 8K --ar 1:1 --stylize 800
```

**Vary:** gape angle (slight / 45° / wide open), moisture level (dry / wet / saliva strands), foreground tooth vs background palate in focus.

---

## v5_eye_detail
**What:** Single eye, close enough to see sclera/iris boundary, orbital ridge scales.  
**Target:** 6–8 images

**Prompt skeleton:**
```
Hyper-realistic macro of Tyrannosaurus rex eye, 
vertical slit pupil in amber-gold iris, visible sclera ring, 
supraorbital ridge scales framing eye socket, 
individual scale facets in sharp relief around orbital margin, 
specular catchlight in pupil, photorealistic macro photography --ar 1:1 --stylize 750
```

**Vary:** pupil dilation (constricted in sunlight / dilated in shadow), iris color, lighting angle.

---

## v5_integument_head
**What:** Scale texture on skull surface — snout, top of head, jaw. No teeth or eye needed.  
**Target:** 8–10 images

**Prompt skeleton:**
```
Hyper-realistic macro of Tyrannosaurus rex head skin surface, 
interlocking polygon scale mosaic, individual scales 2–8cm diameter, 
raised keeled ridges casting micro-shadows between scales, 
larger dome osteoderms interspersed among smaller scales, 
warm brown-grey with amber and rust undertones, subsurface scattering, 
macro lens 8K photorealistic --ar 1:1 --stylize 700
```

**Vary:** skull zone (snout / top of head / jaw lateral / behind eye), scale size variation, moisture (dry / slightly moist).

---

## v5_integument_body
**What:** Neck, flank, or shoulder scale patterns — NOT head.  
**Target:** 6–8 images

**Prompt skeleton:**
```
Hyper-realistic macro of Tyrannosaurus rex body integument, 
[neck / flank / shoulder] scale mosaic, 
larger tubercle scales scattered among fine background scales, 
color gradient from [warm brown to cool grey / amber to slate], 
subtle iridescence in direct light, deep shadow between individual scales, 
photorealistic macro 8K --ar 3:2 --stylize 700
```

**Vary:** body zone, color temperature, scale size ratio (fine / coarse).

---

## v5_forelimb_hand
**What:** The 2-finger arm. Hardest to get right — be strict about digit count.  
**Target:** 8–10 images

**Critical:** 2 fingers ONLY. Reject any MJ output showing 3 fingers.

**Prompt skeleton:**
```
Hyper-realistic close-up of Tyrannosaurus rex forelimb, 
two-fingered hand with digits I and II only, no third digit, 
short muscular arm, wrist barely clearing chest, 
palms facing inward toward each other, 
recurved claws on each finger, 
scale texture on arm and hand dorsum, 
cinematic lighting, photorealistic 8K --ar 2:3 --stylize 750
```

**Vary:** hand position (relaxed / grasping / extended), lighting, background (body flank / mid-air / ground).

---

## v5_hindfoot_claw
**What:** T-rex foot from various angles — hallux visible, digitigrade stance.  
**Target:** 8–10 images

**Prompt skeleton:**
```
Hyper-realistic close-up of Tyrannosaurus rex foot, 
four toes: hallux dewclaw elevated at rear, three load-bearing toes II III IV, 
digitigrade stance on toe tips, 
laterally compressed recurved claws, 
scale mosaic on foot dorsum and toe tops, 
[standing on soil / mid-stride lifted / gripping ground], 
cinematic photorealistic 8K --ar 2:3 --stylize 750
```

**Vary:** ground surface (mud / rock / wet riverbed), stride phase (planted / lifting), claw focus (tip sharpness vs full toe).

---

## v5_full_body_action
**What:** Complete animal — head to tail tip. Horizontal spine, tail as counterbalance.  
**Target:** 6–8 images

**Critical posture:** spine horizontal, NOT Godzilla upright. Tail straight back as counterweight to head.

**Prompt skeleton:**
```
Hyper-realistic full-body Tyrannosaurus rex, 
horizontal spine with head forward and tail straight back as counterbalance, 
digitigrade hindlimbs, two-fingered forelimbs held close to chest, 
[hunting stride / standing alert / head lowered at water], 
[misty river delta / open floodplain / dense fern undergrowth], 
cinematic wide shot, golden hour side lighting, photorealistic 8K --ar 16:9 --stylize 750
```

**Vary:** environment, behavior, time of day lighting, camera angle (eye level / low angle / elevated).

---

## Drop protocol

1. Generate in MJ, pick the best 1–2 variants from each quad
2. Drop PNG into the matching `v5_*` folder
3. Tell Claude which folder is ready — captioning happens folder by folder
4. Reject any image with wrong digit count before dropping

## Quality bar

- Wrong finger count → reject immediately
- Upright "Godzilla" posture → reject for full_body, OK for portrait crops
- Visible watermark → reject
- Blurry / composited / AI artifacts → reject
