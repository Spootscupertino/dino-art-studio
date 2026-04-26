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
        wing_or_flipper="leathery skin wing membrane supported by elongated fourth finger, bat-like wings with no feathers, relatively short wingspan compared to later pterosaurs",
        hindlimb="small hindlimbs, five-toed feet, used as rear legs in quadrupedal walking",
        stance="quadrupedal stance, walking on folded wing knuckles, front limbs acting as front legs supporting weight, bat-like terrestrial crawling — NOT bipedal, NOT bird-like",
        digit_count="three clawed fingers free at wing joint, elongated fourth finger",
    ),

    integument=Integument(
        primary_covering="hair-like pycnofibers covering body, fuzz, mammalian-like hair — NOT feathers, NOT plumage, NOT avian; exceptionally preserved in some Solnhofen specimens",
        texture_detail="dense hair-like pycnofiber fuzz, leathery bat-like wing membrane, mammalian-hair texture not feather texture",
        membrane="leathery skin wing membrane, bat-like wings, stretched from elongated finger to ankle, thin and translucent, no feathers",
    ),

    body=BodyProportions(
        body_length_m=0.4,
        body_mass_kg=1,
        build="small compact body, typical of early long-tailed pterosaurs",
        neck="moderate-length flexible neck",
        tail="long bony tail with diamond-shaped vane at tip — key identifier, tail longer than body",
        silhouette="small quadrupedal pterosaur walking on folded wing knuckles, long bony tail ending in diamond-shaped vane, forward-pointing teeth visible, bat-like leathery wings, no feathers",
        size_comparison="small body with 1.8m wingspan, very small compared to Cretaceous pterosaurs",
    ),

    coloration=ColorationEvidence(
        likely_pattern="dark dorsal, lighter ventral probable",
    ),

    locomotion=LocomotionProfile(
        primary_mode="active flapping flight over water, fish-catching specialist",
        flight="active flapping flight, not purely soaring — smaller body size requires more active wing beats",
        gait_detail="quadrupedal terrestrial locomotion — walked on folded wing knuckles as front limbs, awkward bat-like crawling stance on ground",
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
        "leathery bat-like wing membrane no feathers",
        "hair-like pycnofibers fuzz mammalian-like hair",
        "quadrupedal stance walking on folded wing knuckles",
        "small 1.8m wingspan pterosaur not a bird",
    ],

    recommended_stylize=(100, 150, 300),

    known_failures=[
        "no tail — long bony tail with diamond vane is THE defining feature",
        "bat-wing error — membrane on elongated fourth finger, not between multiple fingers",
        "bird morphology — NOT a stork, heron, or pelican; bat-like wings, not feathered",
        "feathers — pycnofibers are hair-like fuzz, not plumage or flight feathers",
        "bipedal standing — quadrupedal on ground, walking on folded wing knuckles",
    ],
)
