"""Megarachne — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Megarachne",
    common_name="Giant Spider",
    period="Carboniferous (305 Ma)",
    habitat="arthropod",

    skull=SkullAnatomy(
        overall_shape="broad oval prosoma with small chelicerae and compound eyes",
        distinctive_features="broad oval body, NOT a spider despite common name — actually a eurypterid (sea scorpion relative)",
        eye_description="compound eyes on top of prosoma",
    ),

    dentition=DentitionProfile(
        tooth_shape="small chelicerae for processing prey",
        jaw_mechanics="chelicerae and appendages for processing food",
    ),

    limbs=LimbStructure(
        forelimb="strong walking legs thick as fingers, robust and segmented",
        hindlimb="multiple pairs of walking legs",
        stance="multi-legged aquatic/semi-aquatic stance",
        digit_count="multiple paired walking legs with pointed tips",
    ),

    integument=Integument(
        primary_covering="dark segmented exoskeleton",
        texture_detail="thick armored chitinous exoskeleton with segmented plates",
    ),

    body=BodyProportions(
        body_length_m=0.5,
        body_mass_kg=5,
        build="broad oval armored body, eurypterid body plan",
        tail="short segmented post-abdomen",
        silhouette="broad oval armored arthropod, dog-sized, standing on forest floor dwarfing leaf litter",
        size_comparison="large dog-sized eurypterid, 50cm body length",
    ),

    coloration=ColorationEvidence(
        likely_pattern="dark brown to black exoskeleton",
    ),

    locomotion=LocomotionProfile(
        primary_mode="semi-aquatic — primarily aquatic with terrestrial capability",
        gait_detail="multi-legged walking on substrate",
        swimming="capable swimmer using legs and body undulation",
    ),

    flora=FloraAssociation(
        primary_flora=["Carboniferous coal swamp vegetation", "giant club mosses", "ferns"],
        ground_cover="leaf litter and fern ground cover on swamp floor",
        canopy="dense Carboniferous swamp canopy",
        banned_flora=["grass", "flowering plants", "modern trees"],
    ),

    unique_features=[
        "originally thought to be a giant spider — ACTUALLY a eurypterid (sea scorpion relative), reclassified",
        "photograph at ground level showing scale against vegetation",
        "dark segmented exoskeleton, NOT a spider — no spinnerets, no web",
    ],

    mj_shorthand=[
        "broad oval armored eurypterid body",
        "dark segmented chitinous exoskeleton",
        "multiple paired walking legs",
        "dog-sized dwarfing leaf litter",
        "NOT a spider no web no spinnerets",
    ],
)
