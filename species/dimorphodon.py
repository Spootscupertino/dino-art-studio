"""Dimorphodon — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Dimorphodon",
    common_name="Dimorphodon",
    period="Early Jurassic (195–190 Ma)",
    habitat="aerial",

    skull=SkullAnatomy(
        overall_shape="disproportionately large deep skull relative to small body, puffin-like beak profile",
        distinctive_features="oversized deep narrow skull, laterally compressed like a puffin, two types of teeth (dimorphic dentition)",
        eye_description="large eyes in deep skull, set laterally",
        beak="deep narrow beak with keratinous covering, puffin-like profile",
    ),

    dentition=DentitionProfile(
        tooth_shape="two distinct tooth types — large fang-like teeth in front, smaller pointed teeth behind (hence name 'two-form tooth')",
        tooth_count_note="dimorphic dentition: prominent front fangs and smaller rear teeth",
        jaw_mechanics="strong bite for body size, adapted for catching insects and small vertebrates",
    ),

    limbs=LimbStructure(
        wing_or_flipper="short broad wings with elongated fourth finger, built for maneuverability not distance",
        hindlimb="relatively long strong hindlimbs compared to most pterosaurs",
        stance="quadrupedal on ground, possibly more agile terrestrially than most pterosaurs",
        digit_count="three clawed fingers at wing wrist, five-toed feet with clawed grasping toes",
    ),

    integument=Integument(
        primary_covering="pycnofibers covering body",
        texture_detail="dense pycnofiber covering, leathery wing membrane",
        membrane="short broad wing membrane for close-quarters maneuverable flight",
    ),

    body=BodyProportions(
        body_length_m=1.0,
        body_mass_kg=1.5,
        build="compact small body with disproportionately large head",
        neck="short neck supporting oversized skull",
        tail="long bony tail, stiffened",
        silhouette="oversized puffin-like head on small pterosaur body with long tail and short broad wings",
        size_comparison="pigeon-to-crow-sized body with 1.4m wingspan, head looks too large for body",
    ),

    coloration=ColorationEvidence(
        likely_pattern="uncertain, beak may have been colorful for display like modern puffins",
    ),

    locomotion=LocomotionProfile(
        primary_mode="active flapping flight, possibly good at terrestrial locomotion",
        flight="short broad wings suggest maneuverable flight in cluttered environments, not long-distance soaring",
        gait_detail="quadrupedal on ground, may have been relatively agile compared to other pterosaurs",
        special="early pterosaur — one of the first discovered, named by Mary Anning's discovery site (Lyme Regis)",
    ),

    flora=FloraAssociation(
        primary_flora=["coastal Jurassic cliffs", "Early Jurassic shorelines"],
        banned_flora=["dense inland forest"],
    ),

    unique_features=[
        "disproportionately large skull is the key visual identifier — head appears too big for body",
        "dimorphic dentition (two tooth types) is unusual among pterosaurs and gives the genus its name",
        "associated with Mary Anning and early pterosaur paleontology — discovered at Lyme Regis, England",
    ],

    mj_shorthand=[
        "oversized deep puffin-like skull",
        "two tooth types large front fangs small rear",
        "short broad maneuverable wings",
        "pycnofiber-covered compact body",
        "long stiffened bony tail",
        "pigeon-sized 1.4m wingspan early pterosaur",
    ],

    recommended_stylize=(100, 150, 300),

    known_failures=[
        "normal-sized head — head must appear OVERSIZED relative to body",
        "no tail — has a long stiffened bony tail",
    ],
)
