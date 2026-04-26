"""Quetzalcoatlus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Quetzalcoatlus",
    common_name="Quetzal",
    period="Late Cretaceous (68–66 Ma)",
    habitat="aerial",

    skull=SkullAnatomy(
        overall_shape="enormously elongated skull with long pointed toothless beak, overall length exceeding 2.5m",
        distinctive_features="long rigid toothless beak, small cranial crest, skull longer than many entire pterosaurs",
        eye_description="relatively small eyes for skull size, set far back",
        crest_or_horn="small backward-pointing crest on skull, less prominent than Pteranodon",
        beak="extremely long pointed toothless beak, lancet-shaped, used for terrestrial stalking predation",
    ),

    dentition=DentitionProfile(
        tooth_shape="completely toothless — long beak used for spearing and seizing prey on ground",
        jaw_mechanics="long beak acted like forceps for picking up small animals and carrion from ground",
    ),

    limbs=LimbStructure(
        forelimb="enormously long wing arms with elongated fourth finger supporting massive leathery wing membrane, bat-like wings with no feathers",
        hindlimb="proportionally long and robust hindlimbs compared to other pterosaurs, adapted for quadrupedal terrestrial locomotion",
        wing_or_flipper="massive leathery skin wing membrane spanning up to 10–11m tip-to-tip when spread, bat-like wings, no feathers, no plumage",
        stance="quadrupedal stance, walking on folded wing knuckles, front limbs acting as front legs supporting weight, bat-like terrestrial crawling — NOT bipedal, NOT bird-like",
        digit_count="three small clawed fingers at wing wrist, elongated fourth finger supports membrane",
    ),

    integument=Integument(
        primary_covering="hair-like pycnofibers covering body, fuzz, mammalian-like hair — NOT feathers, NOT plumage, NOT avian",
        texture_detail="dense hair-like pycnofiber fuzz across body, leathery bat-like wing membrane, mammalian-hair texture not feather texture",
        membrane="leathery skin wing membrane, bat-like wings, thin and translucent, supported by elongated fourth finger, no feathers",
    ),

    body=BodyProportions(
        body_length_m=3.0,
        body_mass_kg=250,
        build="extremely tall when quadrupedal, lightweight hollow-boned body, giraffe-height on ground standing on four limbs",
        neck="extremely long stiff neck, held nearly vertical when quadrupedal",
        tail="vestigial short tail",
        silhouette="giraffe-sized pterosaur in quadrupedal stance walking on folded wing knuckles, impossibly long neck and beak, massive bat-like leathery wings in flight, no feathers",
        size_comparison="largest known flying animal ever — 10–11m wingspan, standing height of a giraffe (5m+), yet only ~250kg",
    ),

    coloration=ColorationEvidence(
        likely_pattern="uncertain, possible display coloration on beak and crest",
    ),

    locomotion=LocomotionProfile(
        primary_mode="soaring flight and quadrupedal terrestrial stalking predation",
        flight="soaring flight using thermals and slope lift, minimal flapping at this scale",
        gait_detail="quadrupedal terrestrial stalking — walked on folded wing knuckles, bat-like crawling stance with front limbs supporting body weight",
        special="launched quadrupedally from all fours — quad launch essential at this body size, no running takeoff possible",
    ),

    flora=FloraAssociation(
        primary_flora=["open floodplains", "river margins", "sparse woodland"],
        ground_cover="low vegetation on floodplains, open terrain for terrestrial stalking",
        banned_flora=["dense forest (too large to navigate)", "open ocean far from land"],
    ),

    unique_features=[
        "largest flying animal in Earth's history — giraffe-height when quadrupedal, fighter-jet wingspan",
        "primarily a quadrupedal terrestrial stalking predator, NOT a bird-like biped",
        "quadrupedal launch was the ONLY way it could take off — biomechanically impossible to run-and-flap",
    ],

    mj_shorthand=[
        "quadrupedal stance walking on folded wing knuckles",
        "extremely long lancet-shaped toothless beak",
        "10-11m leathery bat-like wings no feathers",
        "hair-like pycnofibers fuzz mammalian-like hair",
        "long stiff vertical neck when quadrupedal",
        "bat-like terrestrial crawling on four limbs",
    ],

    recommended_stylize=(75, 125, 250),

    known_failures=[
        "teeth — Quetzalcoatlus is TOOTHLESS",
        "small size — giraffe-height when quadrupedal; must not look small",
        "bird morphology — NOT a stork, heron, or pelican; quadrupedal with bat-like wings",
        "feathers — pycnofibers are hair-like fuzz, not plumage or flight feathers",
        "bipedal standing — quadrupedal on ground, walking on folded wing knuckles",
    ],
)
