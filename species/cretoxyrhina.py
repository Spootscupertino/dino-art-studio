"""Cretoxyrhina — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Cretoxyrhina",
    common_name="Ginsu Shark",
    period="Late Cretaceous (107–73 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="streamlined torpedo-shaped head, similar to modern mako shark",
        distinctive_features="large dark eye relative to head size, built for speed and visual hunting",
        eye_description="large dark eye, excellent vision for pursuit predation",
    ),

    dentition=DentitionProfile(
        tooth_shape="blade-like teeth with smooth cutting edges, no serrations — razor sharp, clean slicing",
        tooth_count_note="rows of large blade-like teeth",
        jaw_mechanics="fast-closing jaw for high-speed prey interception",
        bite_force_note="slicing bite rather than crushing — teeth cut cleanly through flesh and bone",
    ),

    limbs=LimbStructure(
        wing_or_flipper="large pectoral fins for high-speed maneuvering, mako shark fin plan",
        stance="fully aquatic, built for speed",
    ),

    integument=Integument(
        primary_covering="smooth skin with fine dermal denticles",
        texture_detail="hydrodynamic skin texture, smoother than most sharks due to denticle arrangement",
        special_structures="tall dorsal fin, powerful lunate caudal fin for burst speed",
    ),

    body=BodyProportions(
        body_length_m=6.0,
        body_mass_kg=1000,
        build="sleek muscular torpedo body, built for speed and ambush",
        tail="powerful crescent-shaped tail, high aspect ratio for speed",
        silhouette="mako shark body plan — streamlined, muscular, built for explosive speed",
        size_comparison="great white-sized at 6m, one of the largest Cretaceous sharks",
    ),

    coloration=ColorationEvidence(
        likely_pattern="countershaded — dark above, light below for open-water camouflage",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic",
        swimming="high-speed pursuit predator, thunniform swimming with powerful tail strokes",
        speed_note="one of the fastest sharks of the Cretaceous, ambush-and-speed predator",
    ),

    flora=FloraAssociation(
        water_plants="open ocean Cretaceous Western Interior Seaway",
    ),

    unique_features=[
        "nicknamed Ginsu Shark for blade-like teeth that cut cleanly — preserved prey with clean cut marks",
        "known to prey on mosasaurs, plesiosaurs, and large fish — apex predator of Cretaceous seas",
    ],

    mj_shorthand=[
        "sleek torpedo mako-shark body",
        "smooth unserrated blade-like teeth",
        "large dark hunting eye",
        "powerful lunate tail fin",
        "hydrodynamic smooth denticle skin",
        "great-white-sized 6m Cretaceous shark",
    ],
)
