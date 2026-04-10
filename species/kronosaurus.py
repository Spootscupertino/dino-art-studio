"""Kronosaurus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Kronosaurus",
    common_name="Kronosaurus",
    period="Early Cretaceous (125–100 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="enormous skull, broad and powerful, roughly 2.4m long",
        distinctive_features="one of the largest skulls of any marine reptile, massive jaw muscles",
        eye_description="set laterally in robust skull",
        nostril_position="nares set back on skull for breathing while mostly submerged",
    ),

    dentition=DentitionProfile(
        tooth_shape="large robust conical teeth, largest reaching 30cm with root, rounded in cross-section",
        tooth_count_note="large widely-spaced teeth along massive jaws",
        jaw_mechanics="extremely powerful closing bite, built for crushing large prey",
        bite_force_note="immensely powerful bite force for dispatching large marine animals and crushing turtle shells",
    ),

    limbs=LimbStructure(
        wing_or_flipper="four broad powerful flippers, paddle-shaped for underwater flight locomotion",
        stance="fully aquatic, robust powerful swimmer",
    ),

    integument=Integument(
        primary_covering="smooth hydrodynamic skin",
        texture_detail="robust marine predator skin, smooth with possible scarring from combat",
    ),

    body=BodyProportions(
        body_length_m=10.0,
        body_mass_kg=10000,
        build="massive barrel-shaped body, short thick neck, enormous head",
        neck="short thick powerful neck supporting massive skull",
        tail="short broad tail",
        silhouette="giant pliosaur profile — dominated by enormous head, barrel body, four broad flippers",
        size_comparison="large truck-sized apex marine predator",
    ),

    coloration=ColorationEvidence(
        likely_pattern="countershaded — dark above, lighter below",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic",
        swimming="four-flipper powered swimming, highly maneuverable for its size",
        speed_note="capable of powerful burst acceleration for ambush attacks",
    ),

    flora=FloraAssociation(
        water_plants="shallow Cretaceous inland seas and coastal waters",
        banned_flora=["kelp forests", "modern coral reefs"],
    ),

    unique_features=[
        "original Harvard mount over-reconstructed with too many vertebrae — actual size smaller than early estimates",
        "apex predator of Early Cretaceous Australian inland sea",
    ],

    mj_shorthand=[
        "enormous skull on short thick neck",
        "four broad powerful paddle flippers",
        "massive barrel-shaped body",
        "robust conical 30cm teeth",
        "smooth scarred marine predator skin",
        "10m truck-sized pliosaur",
    ],
)
