"""Carnotaurus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Carnotaurus sastrei",
    common_name="Carnotaurus",
    period="Late Cretaceous (72–69 Ma)",
    habitat="terrestrial",

    skull=SkullAnatomy(
        overall_shape="extremely deep, short, blunt bulldog-like skull — tall and stubby, not long like other large theropods",
        distinctive_features="pair of thick conical horns projecting sideways above the eyes — the only known horned carnivorous dinosaur",
        eye_description="forward-facing eyes set in a short face, possible partial binocular vision",
        nostril_position="nares set high and far forward on the short snout",
        crest_or_horn="two stout bull-like brow horns above the orbits, made of bone covered in keratin",
    ),

    dentition=DentitionProfile(
        tooth_shape="slender, blade-like, recurved teeth — relatively thin for the skull size",
        tooth_count_note="rows of sharp serrated teeth in a short deep jaw",
        jaw_mechanics="weak slow bite but rapid wide gape — likely slashing and bolting prey rather than crushing",
        bite_force_note="surprisingly weak bite force for its size; lightly built skull tuned for fast snapping attacks",
    ),

    limbs=LimbStructure(
        forelimb="absurdly tiny vestigial forelimbs, even smaller and more reduced than T. rex, with four short fingers and no functional grasp — arms barely project from the body",
        hindlimb="long, slender, powerfully muscled hindlimbs built for running, with elongated lower leg",
        stance="upright bipedal, horizontal spine, body balanced over the hips",
        digit_count="four-fingered vestigial hands, three-toed running feet",
        special_appendage="enormous caudofemoralis muscle anchoring the tail to the thighs for explosive sprinting power",
    ),

    integument=Integument(
        primary_covering="scaly reptilian hide — NO feathers; well-preserved skin impressions confirm a pebbly scale covering",
        texture_detail="fine non-overlapping pebbly scales across the body, interrupted by rows of larger conical raised bumps running along the flanks from neck to tail",
        special_structures="parallel rows of low feature-scale bumps along the sides — bumpy studded flanks, not bony plates",
    ),

    body=BodyProportions(
        body_length_m=8.5,
        body_mass_kg=1500,
        build="lightly built, slender and athletic for a large theropod — deep narrow chest, long body tapering to a stiff tail",
        neck="muscular S-curved neck supporting the heavy short skull",
        tail="thick deep-based stiff tail held horizontally as a counterbalance, with large hip-anchored running muscles",
        silhouette="slender fast-running theropod with a short deep horned bull-head, horizontal back, tiny arms, long legs, stiff outstretched tail",
        size_comparison="about 8–9m long but far lighter and leaner than T. rex — built for speed, not bulk",
    ),

    coloration=ColorationEvidence(
        likely_pattern="drab countershaded earth tones — reddish-brown to grey-tan dorsal, paler underside",
        display_structures="brow horns possibly keratin-sheathed in a contrasting tone for display and head-butting contests",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fast cursorial bipedal runner — likely one of the swiftest large theropods",
        gait_detail="long-strided upright bipedal gait, horizontal spine, tail rigid and outstretched for balance",
        speed_note="estimated among the fastest large predators, aided by massive tail-base running muscles",
        special="caudofemoralis-driven sprint; lightweight frame for a 1.5-tonne predator",
    ),

    flora=FloraAssociation(
        primary_flora=["southern conifers (Araucaria)", "podocarps", "Cretaceous ferns", "cycads"],
        ground_cover="open Patagonian floodplain ferns and low scrub",
        canopy="scattered conifer and araucaria stands",
        banned_flora=["grass", "broadleaf flowering trees", "open grassland", "deciduous autumn forest"],
    ),

    unique_features=[
        "only known carnivorous dinosaur with true brow horns — the 'meat-eating bull'",
        "most complete skin impressions of any large theropod, confirming scaly hide and flank scale-rows",
        "forelimbs so reduced they are functionally useless — even tinier than T. rex arms",
    ],

    mj_shorthand=[
        "two thick bull horns projecting sideways above the eyes",
        "short deep blunt bulldog-like skull, not a long snout",
        "tiny vestigial four-fingered arms, even smaller than T-rex arms",
        "slender lightweight fast-runner build, long muscular legs",
        "rows of conical raised bumps studding the flanks, pebbly scaly hide",
        "horizontal back and stiff outstretched counterbalancing tail",
    ],

    bias_corrections=[
        "short deep horned bull-head NOT long T-rex snout",
        "tiny useless four-fingered arms NOT T-rex two-fingered hands",
        "slender lightweight speed build NOT bulky heavy T-rex",
        "scaly pebbly hide NOT feathered",
    ],

    coloration_phrase="drab reddish-brown to grey-tan dorsal, pale underbelly, naturalistic earth tones",

    scale_anchor="8-9 meters long, slender 1.5-tonne speed predator",

    recommended_stylize=(50, 75, 150),

    known_failures=[
        "long snout — Carnotaurus skull is SHORT and DEEP; MJ defaults to a T-rex-style long jaw",
        "big arms — forelimbs are vestigial, must be rendered tiny; even smaller than T. rex",
        "feathers — abelisaurid with confirmed scaly skin, never feathered",
        "osteoderm/bony plates — flank bumps are raised conical SCALES in rows, not armor plates",
        "Triceratops-style horns — horns are short bull-like brow horns above the eyes, not facial/frill horns",
    ],
)
