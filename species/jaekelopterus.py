"""Jaekelopterus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Jaekelopterus",
    common_name="Sea Scorpion",
    period="Early Devonian (390 Ma)",
    habitat="arthropod",

    skull=SkullAnatomy(
        overall_shape="broad flattened head with massive frontal chelicerae pincers",
        distinctive_features="enormous chelicerae (pincers) each longer than a human arm, extending forward from head",
        eye_description="large compound eyes set on top of flattened head",
    ),

    dentition=DentitionProfile(
        tooth_shape="massive chelicera pincers with serrated inner edges for seizing and dismembering prey",
        jaw_mechanics="powerful chelicerae for gripping and tearing, supplemented by smaller head appendages for processing food",
    ),

    limbs=LimbStructure(
        forelimb="massive chelicerae pincers projecting forward, largest appendages on the body",
        hindlimb="multiple walking legs plus posterior paddle-like swimming legs",
        wing_or_flipper="rear pair of legs modified into broad swimming paddles",
        stance="primarily aquatic, could venture onto land briefly",
        digit_count="chelicerae with serrated pincers, walking legs with pointed tips, paddle legs flattened",
    ),

    integument=Integument(
        primary_covering="dark exoskeleton with natural scratches and battle scars",
        texture_detail="heavy chitinous exoskeleton, segmented body with articulated plates",
        armor="thick exoskeletal armor across dorsal surface, segmented along body",
    ),

    body=BodyProportions(
        body_length_m=2.5,
        body_mass_kg=100,
        build="broad flattened body, scorpion-like body plan at crocodile scale",
        tail="segmented post-abdomen ending in telson (tail spine), scorpion-like tail",
        silhouette="giant sea scorpion profile — massive front pincers, broad flat body, segmented tail, swimming paddles",
        size_comparison="crocodile-sized at 2.5m, largest arthropod predator ever discovered",
    ),

    coloration=ColorationEvidence(
        likely_pattern="dark exoskeleton, scorpion-like coloring — dark brown to black with possible lighter underbelly",
    ),

    locomotion=LocomotionProfile(
        primary_mode="primarily aquatic with swimming paddles, capable of brief terrestrial movement",
        swimming="rear paddle legs provide propulsion, body undulates for additional thrust",
        gait_detail="multi-legged walking on substrate, swimming with paddle legs in open water",
        special="could likely venture onto land briefly like modern horseshoe crabs",
    ),

    flora=FloraAssociation(
        primary_flora=["early Devonian coastal vegetation", "primitive land plants"],
        water_plants="freshwater rivers and estuaries, not deep ocean",
        banned_flora=["trees (barely existed in Early Devonian)", "ferns", "grass", "flowering plants"],
    ),

    unique_features=[
        "photograph like an alligator-sized predator, not a bug — low water-level angle",
        "largest arthropod predator ever discovered — chelicerae alone are terrifying",
        "dark exoskeleton with natural scratches and battle scars for realism",
    ],

    mj_shorthand=[
        "massive serrated chelicerae pincers",
        "crocodile-sized sea scorpion",
        "broad flat segmented body",
        "rear paddle-shaped swimming legs",
        "dark scarred chitinous exoskeleton",
        "2.5m largest arthropod predator ever",
    ],
)
