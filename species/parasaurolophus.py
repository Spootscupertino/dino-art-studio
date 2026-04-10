"""Parasaurolophus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Parasaurolophus",
    common_name="Para",
    period="Late Cretaceous (76–73 Ma)",
    habitat="terrestrial",

    skull=SkullAnatomy(
        overall_shape="elongated skull with long tubular hollow crest extending backward 1m+ from top of head",
        distinctive_features="long backward-sweeping tubular crest — hollow, containing looping nasal passages used as resonating chamber for low-frequency calls",
        eye_description="large laterally placed eyes",
        crest_or_horn="long hollow tubular cranial crest sweeping backward — internally contains looping nasal passages, functions as sound resonator",
        beak="broad flat duck-like keratinous beak for cropping vegetation",
    ),

    dentition=DentitionProfile(
        tooth_shape="dental batteries — hundreds of tightly packed diamond-shaped teeth forming efficient shearing surface",
        tooth_count_note="hundreds of teeth in dental batteries, continuously replaced throughout life",
        jaw_mechanics="complex jaw mechanics allowing both vertical and lateral shearing motion — very efficient plant processing",
    ),

    limbs=LimbStructure(
        forelimb="moderate forelimbs, could walk on all fours or stand bipedally",
        hindlimb="powerful columnar hindlimbs for bipedal locomotion and running",
        stance="facultatively bipedal — walked on all fours when browsing, ran on hindlimbs when fleeing",
        digit_count="four fingers on hand, three weight-bearing toes with hooflike tips",
    ),

    integument=Integument(
        primary_covering="pebbly non-overlapping scales, skin impressions show uniform small polygonal tubercles",
        texture_detail="small uniform ground scales, possible larger feature scales along midline",
        special_structures="possible fleshy web or skin flap connecting crest to neck — debated but possible soft-tissue display structure",
    ),

    body=BodyProportions(
        body_length_m=9.5,
        body_mass_kg=3500,
        build="large robust hadrosaur with broad flat beak and distinctive long tubular crest, muscular body",
        neck="moderately long flexible neck for browsing at various heights",
        tail="long deep tail, laterally compressed, possibly used for swimming",
        silhouette="large duck-billed dinosaur with enormously long backward-sweeping hollow cranial crest, broad body, deep tail",
        size_comparison="9.5m long, 5m tall, 3.5 tonnes — large hadrosaur, most recognizable for its long crest",
    ),

    coloration=ColorationEvidence(
        likely_pattern="possibly striped or banded for herd recognition — herd animal in open woodland, crest likely brightly marked for species identification",
        display_structures="crest almost certainly served visual AND acoustic display functions — may have been brightly colored or patterned",
    ),

    locomotion=LocomotionProfile(
        primary_mode="facultatively bipedal — browsed on all fours, fled on hindlimbs",
        gait_detail="efficient walker on all fours, powerful bipedal runner when alarmed",
        speed_note="estimated 40+ km/h in bipedal sprint — fast for its size",
    ),

    flora=FloraAssociation(
        primary_flora=["Late Cretaceous woodland and river plains", "conifers", "ferns", "early angiosperms"],
        ground_cover="ferns, low vegetation, riverbank plants",
        canopy="mixed conifer and early flowering plant canopy",
        banned_flora=["grass", "modern broadleaf deciduous forest"],
    ),

    unique_features=[
        "hollow tubular crest containing looping nasal passages — functioned as a resonating chamber for low-frequency calls, estimated around 48 Hz",
        "crest is NOT filled with bone — it's a hollow sound-producing organ",
        "duck-billed beak at front of mouth with dental batteries behind — one of the most efficient plant-processing systems in the Mesozoic",
        "possible skin flap or fleshy web connecting crest base to neck — would enhance visual display",
    ],

    mj_shorthand=[
        "long backward-sweeping hollow tubular crest",
        "broad flat duck-billed beak",
        "pebbly uniform polygonal scales",
        "robust hadrosaur body deep tail",
        "facultative biped browsing on all fours",
        "9.5m long herd animal",
    ],
)
