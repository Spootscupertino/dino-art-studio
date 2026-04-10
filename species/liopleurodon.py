"""Liopleurodon — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Liopleurodon",
    common_name="Liopleurodon",
    period="Middle to Late Jurassic (165–155 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="enormous heavy skull up to 1.5m long, broad and robust with massive jaw muscles",
        distinctive_features="massive head relative to body — head is roughly one-quarter of total body length, incredibly robust and powerful",
        eye_description="small eyes set laterally on broad skull",
        nostril_position="internal nares allowed water flow through nasal passages for directional smell — could 'taste' the water to locate prey",
    ),

    dentition=DentitionProfile(
        tooth_shape="large robust conical teeth, round in cross-section, designed for gripping large struggling prey",
        jaw_mechanics="enormous crushing bite force — among the most powerful bites of any marine predator",
        bite_force_note="massive jaw muscles filling the skull fenestrae, powerful enough to crush bone",
    ),

    limbs=LimbStructure(
        wing_or_flipper="four large powerful hydrofoil-shaped flippers — primary propulsion organs, front pair larger than rear",
        stance="fully aquatic, four-flipper underwater flight propulsion",
    ),

    integument=Integument(
        primary_covering="smooth marine reptile skin, likely similar to other pliosaurs",
        texture_detail="smooth hydrodynamic skin, possibly countershaded",
    ),

    body=BodyProportions(
        body_length_m=6.5,
        body_mass_kg=3000,
        build="short-necked pliosaur — massive head on short thick neck, robust barrel-shaped body, four large flippers, short tail",
        neck="very short thick muscular neck — pliosaurs are the short-necked cousins of plesiosaurs",
        tail="short tapered tail, not primary propulsion",
        silhouette="massive-headed short-necked marine predator with four powerful flippers and barrel-shaped body",
        size_comparison="6–7m long — NOT 25m as shown in Walking With Dinosaurs, which wildly exaggerated its size",
    ),

    coloration=ColorationEvidence(
        likely_pattern="likely countershaded — dark above, light below, typical of marine predators",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic, four-flipper underwater flight",
        swimming="four large flippers used in coordinated underwater flight — powerful and maneuverable, fast ambush predator",
        speed_note="fast and powerful swimmer, apex predator of Jurassic seas",
    ),

    flora=FloraAssociation(
        water_plants="open ocean and shallow seas of Jurassic Europe",
        banned_flora=["grass", "terrestrial forest"],
    ),

    unique_features=[
        "NOT 25 metres long — Walking With Dinosaurs massively exaggerated its size, real Liopleurodon was 6–7m",
        "short-necked pliosaur — the opposite body plan to long-necked plesiosaurs like Elasmosaurus",
        "could smell directionally through water flow — internal nares created water-flow nasal system for tracking prey",
        "one of the apex predators of Jurassic seas despite being smaller than pop culture suggests",
    ],

    mj_shorthand=[
        "massive head quarter of body length",
        "short thick neck barrel body",
        "four powerful hydrofoil flippers",
        "robust conical gripping teeth",
        "smooth hydrodynamic marine hide",
        "6-7m short-necked pliosaur",
    ],
)
