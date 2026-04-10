"""Ichthyosaurus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Ichthyosaurus",
    common_name="Ichthyosaur",
    period="Early Jurassic (200–190 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="elongated narrow snout with enormous round eyes protected by sclerotic ring of bony plates",
        distinctive_features="enormous eyes — among the largest relative to body of any vertebrate, surrounded by protective bony sclerotic ring",
        eye_description="enormously large round eyes with bony sclerotic ring — adapted for deep diving and low-light hunting",
    ),

    dentition=DentitionProfile(
        tooth_shape="small conical teeth in long narrow jaws for catching fish and squid",
        jaw_mechanics="rapid snapping jaws for catching small fast prey — similar to modern dolphins",
    ),

    limbs=LimbStructure(
        wing_or_flipper="four hydrofoil-shaped flippers, front pair larger — crescent-shaped for efficient cruising",
        stance="fully aquatic, flippers for steering and stabilization",
    ),

    integument=Integument(
        primary_covering="smooth skin, no scales — convergently similar to dolphin skin",
        texture_detail="smooth streamlined skin with possible countershading, dorsal fin made of soft tissue (no bone support)",
        special_structures="soft-tissue dorsal fin and crescent tail fluke — both confirmed by exceptional preservation, no bony support",
    ),

    body=BodyProportions(
        body_length_m=2.0,
        body_mass_kg=90,
        build="dolphin-shaped streamlined body — textbook example of convergent evolution with dolphins and tuna",
        neck="no visible neck — head merges smoothly into torpedo-shaped body",
        tail="crescent-shaped (lunate) tail fluke — lower lobe supported by vertebral column bending downward (reversed from sharks)",
        silhouette="dolphin-shaped with elongated snout, enormous eyes, dorsal fin, and crescent tail",
        size_comparison="about 2m long — dolphin-sized, but some ichthyosaur species reached 20m+",
    ),

    coloration=ColorationEvidence(
        likely_pattern="countershaded — dark above, light below, exactly like modern dolphins and tuna",
        fossil_evidence="preserved melanophores confirm dark dorsal coloration in some ichthyosaur specimens",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic, thunniform (tuna-like) tail-driven swimming",
        swimming="crescent tail fluke provides main thrust — swam like a tuna or dolphin, not like an eel",
        speed_note="fast efficient cruiser, built for sustained swimming at moderate speeds with burst capability",
        special="gave birth to live young — confirmed by fossils preserving babies emerging tail-first, like modern dolphins",
    ),

    flora=FloraAssociation(
        water_plants="open ocean, pelagic environment",
        banned_flora=["grass", "terrestrial forest"],
    ),

    unique_features=[
        "textbook convergent evolution — independently evolved dolphin-like body shape despite being a reptile",
        "enormous eyes with bony sclerotic ring — adapted for deep diving in low light conditions",
        "gave birth to live young tail-first — confirmed by extraordinary fossils preserving the birth moment",
        "dorsal fin and tail fluke are soft tissue only — no bony support, only known from exceptional preservation",
    ],

    mj_shorthand=[
        "dolphin-shaped with enormous round eyes",
        "bony sclerotic eye ring",
        "smooth scaleless skin like dolphin",
        "soft-tissue dorsal fin no bone",
        "crescent tail fluke vertebrae bend down",
        "2m dolphin-sized marine reptile",
    ],
)
