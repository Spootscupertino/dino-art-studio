"""Arthropleura — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Arthropleura",
    common_name="Arthropleura",
    period="Carboniferous (345–295 Ma)",
    habitat="arthropod",

    skull=SkullAnatomy(
        overall_shape="rounded head with antennae, small relative to massive segmented body",
        distinctive_features="small rounded head with sensory antennae, simple eyes",
        eye_description="small simple eyes, relied more on antennae for sensing environment",
    ),

    dentition=DentitionProfile(
        tooth_shape="herbivorous mouthparts for processing fern fronds and plant material",
        jaw_mechanics="mandibles for cropping and chewing vegetation",
    ),

    limbs=LimbStructure(
        forelimb="dozens of thick paired legs — two pairs per body segment",
        stance="low multi-legged stance, body filling forest floor path between trees",
        digit_count="each leg ends in a simple pointed tip for gripping substrate",
    ),

    integument=Integument(
        primary_covering="segmented armored body plates, each the size of a dinner plate",
        texture_detail="dark chitinous segments with natural wear, thick armored exoskeleton",
        armor="interlocking armored tergite plates across back, rigid but articulated at segment joints",
    ),

    body=BodyProportions(
        body_length_m=2.6,
        body_mass_kg=50,
        build="enormously elongated multi-segmented body, wider than a human torso",
        silhouette="giant millipede profile — endless segmented armored body with rows of paired legs",
        size_comparison="longer than a car at 2.6m, largest land arthropod in Earth's history",
    ),

    coloration=ColorationEvidence(
        likely_pattern="dark brown to black chitinous exoskeleton with natural weathering",
    ),

    locomotion=LocomotionProfile(
        primary_mode="multi-legged terrestrial crawler",
        gait_detail="rippling wave of leg movement, numerous paired legs in coordinated sequence",
        speed_note="slow deliberate movement through forest undergrowth",
        special="could only exist in high-oxygen Carboniferous atmosphere — 35% O2 enabled giant arthropod respiration",
    ),

    flora=FloraAssociation(
        primary_flora=["giant club mosses (Lepidodendron)", "Sigillaria", "tree ferns", "Calamites"],
        ground_cover="dense fern floor in humid coal swamp, leaf litter and rotting plant material",
        canopy="dense Carboniferous coal swamp canopy, dark and humid",
        banned_flora=["grass", "flowering plants", "modern trees"],
    ),

    unique_features=[
        "photograph like a large reptile, not a bug — ground-level perspective showing it dwarfing surrounding vegetation",
        "herbivore despite terrifying appearance — fed on fern fronds and decaying plant matter",
        "largest known land arthropod in Earth's history",
    ],

    mj_shorthand=[
        "car-length giant millipede",
        "dinner-plate-sized armored body segments",
        "dozens of thick paired legs",
        "dark chitinous interlocking plates",
        "2.6m longest land arthropod ever",
        "low ground-level dwarfing ferns",
    ],
)
