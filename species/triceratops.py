"""Triceratops — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Triceratops",
    common_name="Triceratops",
    period="Late Cretaceous (68–66 Ma)",
    habitat="terrestrial",

    skull=SkullAnatomy(
        overall_shape="massive skull up to 2.5m long with solid bony frill and three horns — one of the largest skulls of any land animal",
        distinctive_features="two long brow horns above eyes (up to 1m), one short nasal horn on snout, solid bony frill with scalloped edge",
        eye_description="laterally placed eyes set below the brow horns, relatively small for skull size",
        crest_or_horn="solid bony frill (NOT fenestrated like Torosaurus), edged with triangular epoccipitals, two long brow horns curving forward",
        beak="large parrot-like keratinous beak at front of mouth for cropping vegetation",
    ),

    dentition=DentitionProfile(
        tooth_shape="dental batteries — columns of tightly packed leaf-shaped teeth forming a shearing surface",
        tooth_count_note="hundreds of teeth arranged in dental batteries, continuously replaced",
        jaw_mechanics="powerful orthal (up-down) jaw motion with slight lateral shearing — designed for processing tough Cretaceous vegetation",
    ),

    limbs=LimbStructure(
        forelimb="robust forelimbs with five fingers, slightly splayed outward — semi-erect, NOT fully sprawled but NOT fully columnar",
        hindlimb="powerful columnar hindlimbs, larger than forelimbs, weight-bearing",
        stance="quadrupedal with semi-erect forelimb posture — elbows slightly bowed outward, hindlimbs fully erect",
        digit_count="five fingers on hand, three weight-bearing toes on foot",
    ),

    integument=Integument(
        primary_covering="pebbly non-overlapping scales across body, large feature scales in rosette patterns along flanks",
        texture_detail="varying scale sizes — large circular feature scales surrounded by smaller ground scales, similar to pattern seen in ceratopsid skin impressions",
        special_structures="possible nipple-like bristle structures along dorsal midline — based on Psittacosaurus relative with confirmed tail bristles",
    ),

    body=BodyProportions(
        body_length_m=9.0,
        body_mass_kg=9000,
        build="massive barrel-chested quadruped, enormous head, robust muscular body",
        neck="short thick neck supporting the massive skull, powerful neck muscles anchored to frill",
        tail="relatively short thick tapering tail, not used as weapon",
        silhouette="stocky four-legged tank with enormous three-horned skull and bony frill, rhino-like proportions",
        size_comparison="9m long, 3m at hip, 9 tonnes — rhino-sized armored herbivore",
    ),

    coloration=ColorationEvidence(
        likely_pattern="possibly dappled or countershaded — large animal in mixed woodland, frill possibly brightly patterned for display/species recognition",
        display_structures="frill almost certainly used for display — may have been brightly colored, horns and frill edging for visual signaling",
    ),

    locomotion=LocomotionProfile(
        primary_mode="obligate quadruped, semi-erect forelimbs, erect hindlimbs",
        gait_detail="relatively slow but powerful, rhino-like locomotion, capable of short charges",
        speed_note="estimated 25–32 km/h in short charges — fast for its size, like a rhino",
    ),

    flora=FloraAssociation(
        primary_flora=["Late Cretaceous Hell Creek flora", "ferns", "conifers", "palms", "early flowering plants"],
        ground_cover="ferns, low angiosperms",
        canopy="mixed conifer and angiosperm woodland",
        banned_flora=["grass (minimal in Late Cretaceous)", "modern broadleaf deciduous forest"],
    ),

    unique_features=[
        "solid bony frill — NOT fenestrated (windowed) like many other ceratopsians",
        "frill was NOT a shield — too thin and vascularized, almost certainly a display structure",
        "forelimbs semi-erect with elbows slightly bowed outward — NOT fully columnar like an elephant and NOT fully sprawled",
        "parrot-like beak at front of mouth, dental batteries for processing tough vegetation behind it",
    ],

    mj_shorthand=[
        "three-horned skull with solid bony frill",
        "parrot-like keratinous beak",
        "pebbly rosette-patterned scales",
        "rhino-proportioned stocky quadruped",
        "semi-erect forelimbs elbows bowed out",
        "9m long 9-tonne ceratopsian",
    ],
)
