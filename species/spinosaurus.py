"""Spinosaurus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Spinosaurus",
    common_name="Spinosaurus",
    period="Late Cretaceous (99–93 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="elongated narrow crocodile-like snout, 1.5m+ long",
        distinctive_features="rosette of interlocking teeth at snout tip for gripping fish, conical teeth, pressure sensors in snout possible",
        eye_description="small eyes relative to skull size, set laterally",
        nostril_position="nares elevated on snout ridge, set back from tip — adapted for breathing while partially submerged",
        crest_or_horn="low sagittal crest along skull midline",
    ),

    dentition=DentitionProfile(
        tooth_shape="conical unserrated teeth, round in cross-section — fish-catching teeth not meat-slicing",
        tooth_count_note="numerous conical teeth along elongated snout, rosette at tip",
        jaw_mechanics="long narrow jaws for rapid lateral snapping at fish, similar to gharial",
        bite_force_note="moderate bite designed for grip, not crushing — piscivore jaw mechanics",
    ),

    limbs=LimbStructure(
        forelimb="robust powerful forelimbs with large claws, used for walking quadrupedally on land and possibly catching fish",
        hindlimb="disproportionately small hindlimbs for body size, short and robust",
        stance="quadrupedal on land with low body posture — hindlimbs too short for efficient bipedal locomotion",
        digit_count="three-clawed hands, four-toed feet with possible webbing between toes",
    ),

    integument=Integument(
        primary_covering="conical raised scales covering body",
        texture_detail="rough interlocking hide with each scale individually defined, dense pachyostotic bones beneath",
        special_structures="massive dorsal sail formed by elongated neural spines along entire back, reaching 1.7m tall at apex — function debated (display, thermoregulation, fat storage, or swimming aid)",
    ),

    body=BodyProportions(
        body_length_m=14.0,
        body_mass_kg=9000,
        build="elongated torso with disproportionately small hindlimbs, heavily built anterior body",
        neck="moderately long muscular neck",
        tail="deep paddle-shaped tail with tall neural spines forming fin-like structure — primary swimming organ, undulates like an eel tail",
        silhouette="massive sail-backed semi-aquatic predator with crocodile snout, low quadrupedal stance on land",
        size_comparison="one of the largest theropods at 14m, but built very differently from T. rex — elongated, low-slung, semi-aquatic",
    ),

    coloration=ColorationEvidence(
        likely_pattern="possibly countershaded — darker above, lighter below, adaptive for semi-aquatic lifestyle",
        display_structures="sail likely brightly colored or patterned for display — highly vascularized",
    ),

    locomotion=LocomotionProfile(
        primary_mode="semi-aquatic — swimming in rivers and coastal waters, quadrupedal on land",
        swimming="paddle-tail propulsion, undulating deep tail through water, dense bones for ballast control",
        gait_detail="low-slung quadrupedal stance on land, forelimbs used for walking",
        speed_note="slow and ungainly on land, powerful in water",
        special="dense pachyostotic bones act as ballast for buoyancy control — could submerge easily",
    ),

    flora=FloraAssociation(
        primary_flora=["mangrove-like coastal vegetation", "river-edge ferns", "conifers"],
        ground_cover="riverside vegetation, mudflats, tidal zones",
        water_plants="aquatic vegetation in river deltas",
        banned_flora=["grass", "broadleaf deciduous forest", "open grassland"],
    ),

    unique_features=[
        "original holotype specimens destroyed in WWII Munich bombing — all modern knowledge from newer Moroccan/Algerian specimens",
        "debate ongoing: fully aquatic diver vs wading shore predator (Ibrahim vs Hone & Holtz)",
        "closed mouth option — snout tip teeth interlock even when jaws shut",
    ],

    mj_shorthand=[
        "massive dorsal sail 1.7m tall neural spines",
        "elongated crocodile-like narrow snout",
        "deep paddle-shaped eel-like tail fin",
        "conical unserrated fish-catching teeth",
        "low quadrupedal stance small hindlimbs",
        "14m semi-aquatic sail-backed predator",
    ],
)
