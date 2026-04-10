"""Anomalocaris — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Anomalocaris",
    common_name="Anomalocaris",
    period="Cambrian (520–500 Ma)",
    habitat="arthropod",

    skull=SkullAnatomy(
        overall_shape="flattened oval head with two large stalked compound eyes and two grasping frontal appendages",
        distinctive_features="two large grasping appendages at front, each the length of a human forearm, stalked compound eyes on top of head",
        eye_description="large stalked compound eyes — among the most complex eyes of the Cambrian, each with 16,000+ lenses",
    ),

    dentition=DentitionProfile(
        tooth_shape="circular mouth with overlapping hardened plates forming a pineapple-ring-like structure",
        jaw_mechanics="circular mouth constricts to crush prey, plates squeeze inward — cannot close fully (gap in center)",
        bite_force_note="strong enough to crack trilobite exoskeletons",
    ),

    limbs=LimbStructure(
        forelimb="two large frontal grasping appendages with spine-like projections along inner edge for seizing prey",
        wing_or_flipper="lateral swimming lobes (flaps) running along both sides of body, rippling in wave-like motion for propulsion",
        stance="fully aquatic, no walking legs",
    ),

    integument=Integument(
        primary_covering="semi-translucent body showing internal structures",
        texture_detail="smooth body surface with lateral lobes, partially translucent in life",
        special_structures="lateral swimming lobes (flaps) along entire body length used for locomotion, flexible and undulating",
    ),

    body=BodyProportions(
        body_length_m=1.0,
        body_mass_kg=5,
        build="flattened oval body, broad and streamlined for swimming",
        tail="fan-shaped tail with multiple lobes for steering",
        silhouette="Cambrian predator — flattened oval body with rippling side-lobes, two grasping arms, stalked eyes, circular mouth",
        size_comparison="one metre long — absolute giant of the Cambrian, apex predator when most life was centimetre-scale",
    ),

    coloration=ColorationEvidence(
        likely_pattern="mantis shrimp and cuttlefish colour reference — translucent body with possible iridescent or colorful patterns",
        additional_notes="use mantis shrimp and cuttlefish as color reference, translucent body showing internal structures",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic — undulating lateral lobe swimmer",
        swimming="lateral lobes ripple in wave-like sequence from front to back, graceful undulating locomotion",
        speed_note="fast and agile for Cambrian standards, dominant predator",
        special="apex predator of the Cambrian Explosion — when this animal appeared, it was the most complex predator Earth had ever seen",
    ),

    flora=FloraAssociation(
        water_plants="Cambrian ocean floor and water column — no land plants existed yet",
        banned_flora=["ALL land plants (did not exist in Cambrian)", "seagrass", "kelp"],
    ),

    unique_features=[
        "apex predator of the Cambrian — the first major predator in Earth's history",
        "translucent body showing internal structures is a key visual feature",
        "circular mouth could NOT close fully — always has a small gap in the center",
    ],

    mj_shorthand=[
        "two large spiny grasping frontal appendages",
        "circular pineapple-ring mouth",
        "stalked compound eyes 16000 lenses",
        "rippling lateral swimming lobes",
        "semi-translucent flattened oval body",
        "1m Cambrian apex predator",
    ],
)
