"""Rhamphorhynchus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Rhamphorhynchus",
    common_name="Rhampho",
    period="Late Jurassic (150–148 Ma)",
    habitat="aerial",

    skull=SkullAnatomy(
        overall_shape="elongated narrow skull with forward-projecting interlocking teeth",
        distinctive_features="teeth project forward and interlock when jaw closes, forming a fish-catching basket",
        eye_description="large eyes for spotting fish from above",
    ),

    dentition=DentitionProfile(
        tooth_shape="long forward-pointing needle-like teeth that interlock like a cage when jaws close",
        tooth_count_note="numerous forward-angled teeth in both jaws",
        jaw_mechanics="rapid jaw closure trapping slippery fish in interlocking tooth basket",
    ),

    limbs=LimbStructure(
        wing_or_flipper="wing membrane supported by elongated fourth finger, relatively short wingspan compared to later pterosaurs",
        hindlimb="small hindlimbs, five-toed feet",
        stance="quadrupedal on ground with folded wings",
        digit_count="three clawed fingers free at wing joint, elongated fourth finger",
    ),

    integument=Integument(
        primary_covering="pycnofibers covering body, exceptionally preserved in some Solnhofen specimens",
        texture_detail="dense pycnofiber body covering, leathery wing membrane",
        membrane="wing membrane stretched from elongated finger to ankle, thin and leathery",
    ),

    body=BodyProportions(
        body_length_m=0.4,
        body_mass_kg=1,
        build="small compact body, typical of early long-tailed pterosaurs",
        neck="moderate-length flexible neck",
        tail="long bony tail with diamond-shaped vane at tip — key identifier, tail longer than body",
        silhouette="small pterosaur with long tail ending in diamond-shaped vane, forward-pointing teeth visible",
        size_comparison="crow-sized body with 1.8m wingspan, very small compared to Cretaceous pterosaurs",
    ),

    coloration=ColorationEvidence(
        likely_pattern="dark dorsal, lighter ventral probable",
    ),

    locomotion=LocomotionProfile(
        primary_mode="active flapping flight over water, fish-catching specialist",
        flight="active flapping flight, not purely soaring — smaller body size requires more active wing beats",
        gait_detail="quadrupedal on ground, awkward terrestrial locomotion",
        special="tail vane likely acted as rudder/stabilizer during flight maneuvers — critical for fishing dives",
    ),

    flora=FloraAssociation(
        primary_flora=["coastal Jurassic lagoons", "limestone island shores"],
        banned_flora=["dense inland forest", "open grassland"],
    ),

    unique_features=[
        "long bony tail with diamond-shaped vane — the defining feature of rhamphorhynchoid pterosaurs",
        "exceptionally preserved Solnhofen specimens show wing membrane details and pycnofiber impressions",
        "forward-interlocking teeth formed perfect fish-catching basket",
    ],

    mj_shorthand=[
        "long bony tail with diamond vane tip",
        "forward-projecting interlocking needle teeth",
        "leathery wing membrane to ankles",
        "dense pycnofiber body fuzz",
        "crow-sized 1.8m wingspan pterosaur",
    ],

    recommended_stylize=(100, 150, 300),

    known_failures=[
        "no tail — long bony tail with diamond vane is THE defining feature",
        "bat wings — membrane on elongated fourth finger, not between multiple fingers",
    ],
)
