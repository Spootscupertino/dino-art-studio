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
        overall_shape="disproportionately large deep skull relative to small body, laterally compressed narrow profile",
        distinctive_features="oversized deep narrow skull, laterally compressed, two types of teeth (dimorphic dentition) — NOT a puffin-like or bird-like head",
        eye_description="large eyes in deep skull, set laterally",
        beak="deep narrow beak with keratinous covering, NOT a bird beak, NOT a puffin beak",
    ),

    dentition=DentitionProfile(
        tooth_shape="two distinct tooth types — large fang-like teeth in front, smaller pointed teeth behind (hence name 'two-form tooth')",
        tooth_count_note="dimorphic dentition: prominent front fangs and smaller rear teeth",
        jaw_mechanics="strong bite for body size, adapted for catching insects and small vertebrates",
    ),

    limbs=LimbStructure(
        wing_or_flipper="short broad leathery skin wing membrane supported by elongated fourth finger, bat-like wings with no feathers, built for maneuverability not distance",
        hindlimb="relatively long strong hindlimbs compared to most pterosaurs, used as rear legs in quadrupedal walking",
        stance="quadrupedal stance, walking on folded wing knuckles, front limbs acting as front legs supporting weight, bat-like terrestrial crawling — NOT bipedal, NOT bird-like",
        digit_count="three clawed fingers at wing wrist, five-toed feet with clawed grasping toes",
    ),

    integument=Integument(
        primary_covering="hair-like pycnofibers covering body, fuzz, mammalian-like hair — NOT feathers, NOT plumage, NOT avian",
        texture_detail="dense hair-like pycnofiber fuzz, leathery bat-like wing membrane, mammalian-hair texture not feather texture",
        membrane="short broad leathery bat-like wing membrane for close-quarters maneuverable flight, no feathers",
    ),

    body=BodyProportions(
        body_length_m=1.0,
        body_mass_kg=1.5,
        build="compact small body with disproportionately large head",
        neck="short neck supporting oversized skull",
        tail="long bony tail, stiffened",
        silhouette="oversized deep narrow skull on small pterosaur body, long stiffened bony tail, short broad bat-like leathery wings, quadrupedal walking on folded wing knuckles, no feathers",
        size_comparison="small body with 1.4m wingspan, head looks too large for body",
    ),

    coloration=ColorationEvidence(
        likely_pattern="uncertain, beak may have been colorful for display",
    ),

    locomotion=LocomotionProfile(
        primary_mode="active flapping flight, possibly good at quadrupedal terrestrial locomotion",
        flight="short broad wings suggest maneuverable flight in cluttered environments, not long-distance soaring",
        gait_detail="quadrupedal terrestrial locomotion — walked on folded wing knuckles as front limbs, bat-like crawling stance, may have been relatively agile compared to other pterosaurs",
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
        "oversized deep narrow skull laterally compressed",
        "two tooth types large front fangs small rear",
        "short broad bat-like wing membranes no feathers",
        "hair-like pycnofibers fuzz mammalian-like hair",
        "long stiffened bony tail",
        "small 1.4m wingspan early pterosaur quadrupedal",
    ],

    recommended_stylize=(100, 150, 300),

    known_failures=[
        "normal-sized head — head must appear OVERSIZED relative to body",
        "no tail — has a long stiffened bony tail",
        "bird morphology — NOT a puffin, stork, or heron; bat-like wings, not feathered",
        "feathers — pycnofibers are hair-like fuzz, not plumage or flight feathers",
        "bipedal standing — quadrupedal on ground, walking on folded wing knuckles",
    ],
)
