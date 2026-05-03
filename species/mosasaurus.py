"""Mosasaurus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Mosasaurus",
    common_name="Mosasaur",
    period="Late Cretaceous (82–66 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="elongated heavy skull with rounded snout, 1.5m long, loose jaw hinge allowing wide gape",
        distinctive_features="rounded conical snout, loose jaw articulation (like snakes) allowing wide gape, pterygoid teeth on palate for gripping prey",
        eye_description="moderate-sized laterally placed eyes with sclerotic ring",
    ),

    dentition=DentitionProfile(
        tooth_shape="conical recurved teeth varying in size, robust and designed for grip-and-swallow feeding",
        tooth_count_note="teeth on both jaw margins AND on pterygoid bones on palate — double row of teeth for gripping prey",
        jaw_mechanics="loose jaw hinge allowed wide gape — similar to snake mechanics, could swallow large prey whole",
        bite_force_note="powerful bite designed for gripping and crushing, not slicing",
    ),

    limbs=LimbStructure(
        wing_or_flipper="four short paddle-shaped flippers, forelimb flippers larger than hindlimb — used for steering not propulsion",
        stance="fully aquatic, flippers for steering and stabilization only",
    ),

    integument=Integument(
        primary_covering="keeled overlapping scales along dorsal surface — confirmed by skin impressions",
        texture_detail="diamond-shaped keeled scales similar to snake scales, smooth belly scales, countershaded coloration preserved in some specimens",
    ),

    body=BodyProportions(
        body_length_m=13.0,
        body_mass_kg=15000,
        build="elongated barrel-shaped torso tapering to deep crescent-shaped tail, four short flippers",
        neck="short thick neck, head in line with body",
        tail="deep laterally compressed tail with crescent-shaped fluke — primary propulsion organ, eel-like undulation",
        silhouette="massive elongated marine reptile with rounded snout, four short flippers, deep crescent tail fluke",
        size_comparison="13m long, 15 tonnes — apex predator of Cretaceous seas, longer than a bus",
    ),

    coloration=ColorationEvidence(
        likely_pattern="countershaded — dark dorsal, light ventral, confirmed in some mosasaur skin impressions",
        fossil_evidence="some mosasaur specimens preserve countershaded coloration pattern with melanosomes",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic, tail-driven swimmer",
        swimming="lateral undulation of deep tail with crescent fluke — similar to shark propulsion, flippers for steering",
        speed_note="fast open-water predator, burst speeds for ambush attacks",
    ),

    flora=FloraAssociation(
        water_plants="open ocean and coastal marine environment",
        banned_flora=["grass", "terrestrial forest"],
    ),

    unique_features=[
        "NOT a dinosaur — a giant marine lizard related to modern monitor lizards and snakes",
        "crescent tail fluke confirmed by soft tissue preservation — swam like a shark, not like an eel",
        "double row of palatal pterygoid teeth — once prey was gripped, palatal teeth walked it into the throat",
        "keeled overlapping scales confirmed by exceptional skin impressions",
    ],

    mj_shorthand=[
        "keeled overlapping snake-like scales",
        "rounded conical snout with loose jaw hinge",
        "deep crescent tail fluke",
        "four short paddle flippers",
        "conical recurved gripping teeth",
        "13m elongated barrel-bodied marine lizard",
    ],

    recommended_stylize=(75, 125, 250),

    known_failures=[
        "crocodile head — MJ renders crocodilian snout; Mosasaurus has a rounded monitor-lizard-like snout",
        "eel-like tail — tail has a crescent FLUKE like a shark, not an eel undulation",
        "dry land — fully aquatic, never on land",
    ],
)
