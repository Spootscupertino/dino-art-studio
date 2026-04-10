"""Eurypterus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Eurypterus",
    common_name="Eurypterid",
    period="Silurian (432–418 Ma)",
    habitat="arthropod",

    skull=SkullAnatomy(
        overall_shape="streamlined oval prosoma with centrally placed compound eyes",
        distinctive_features="compact streamlined body, classic sea scorpion shape, small chelicerae",
        eye_description="compound eyes on top of prosoma, kidney-shaped",
    ),

    dentition=DentitionProfile(
        tooth_shape="small chelicerae for processing prey",
        jaw_mechanics="chelicerae and walking legs with gnathobases (jaw-like bases) for processing food",
    ),

    limbs=LimbStructure(
        forelimb="small chelicerae, four pairs of walking legs",
        hindlimb="rear-most pair of legs modified into broad swimming paddles",
        wing_or_flipper="paddle-shaped rear legs for swimming propulsion",
        stance="multi-legged aquatic stance, capable of resting on bottom substrate",
        digit_count="small chelicerae, four pairs of walking legs, one pair of swimming paddles",
    ),

    integument=Integument(
        primary_covering="olive-brown chitinous exoskeleton",
        texture_detail="smooth streamlined exoskeleton with segmented body plates, well-preserved in many fossils",
    ),

    body=BodyProportions(
        body_length_m=0.3,
        body_mass_kg=0.5,
        build="streamlined compact body, classic eurypterid shape",
        tail="segmented post-abdomen ending in telson spike, used for defense and steering",
        silhouette="compact sea scorpion — oval body, walking legs, swimming paddles, tail spike",
        size_comparison="30cm long — smallest of our eurypterids but still dramatic, horseshoe crab-sized",
    ),

    coloration=ColorationEvidence(
        likely_pattern="olive-brown exoskeleton, dark and muted",
    ),

    locomotion=LocomotionProfile(
        primary_mode="aquatic with ability to rest on substrate",
        swimming="paddle-legged swimming, capable of both bottom-walking and open water swimming",
        gait_detail="multi-legged bottom walking, swimming with paddle legs",
    ),

    flora=FloraAssociation(
        primary_flora=["Silurian shallow marine and brackish environments"],
        water_plants="no significant vegetation — early Silurian period",
        banned_flora=["land plants (barely existed)", "trees", "ferns"],
    ),

    unique_features=[
        "New York state fossil — one of the best-known and most-collected eurypterids",
        "photograph like a horseshoe crab on a beach — resting on rocks at water's edge",
        "most common eurypterid in the fossil record, thousands of specimens known",
    ],

    mj_shorthand=[
        "compact olive-brown sea scorpion",
        "paddle-shaped rear swimming legs",
        "streamlined oval segmented body",
        "tail spike telson for defense",
        "horseshoe-crab-sized 30cm eurypterid",
    ],
)
