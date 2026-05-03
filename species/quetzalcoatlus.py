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
        forelimb="enormously long wing arms with elongated fourth finger supporting massive wing membrane",
        hindlimb="proportionally long and robust hindlimbs compared to other pterosaurs, adapted for terrestrial stalking",
        wing_or_flipper="massive wing membrane spanning up to 10–11m tip-to-tip when spread",
        stance="quadrupedal on ground — walked upright on folded wings and long hindlimbs, giraffe-like terrestrial posture",
        digit_count="three small clawed fingers at wing wrist, elongated fourth finger supports membrane",
    ),

    integument=Integument(
        primary_covering="pycnofibers covering body, hair-like filaments",
        texture_detail="dense pycnofiber covering, leathery wing membrane",
        membrane="massive wing membrane, thin and leathery, supported by elongated fourth finger",
    ),

    body=BodyProportions(
        body_length_m=3.0,
        body_mass_kg=250,
        build="extremely tall when standing, lightweight hollow-boned body, giraffe-height on ground",
        neck="extremely long stiff neck, held nearly vertical when standing",
        tail="vestigial short tail",
        silhouette="giraffe-sized pterosaur standing on folded wings, impossibly long neck and beak, massive wingspan in flight",
        size_comparison="largest known flying animal ever — 10–11m wingspan, standing height of a giraffe (5m+), yet only ~250kg",
    ),

    coloration=ColorationEvidence(
        likely_pattern="uncertain, possible display coloration on beak and crest",
    ),

    locomotion=LocomotionProfile(
        primary_mode="soaring flight and terrestrial stalking predation",
        flight="soaring flight using thermals and slope lift, minimal flapping at this scale",
        gait_detail="quadrupedal terrestrial stalking — walked on ground hunting small prey like a giant stork",
        special="launched quadrupedally from all fours — quad launch essential at this body size, no running takeoff possible",
    ),

    flora=FloraAssociation(
        primary_flora=["open floodplains", "river margins", "sparse woodland"],
        ground_cover="low vegetation on floodplains, open terrain for terrestrial stalking",
        banned_flora=["dense forest (too large to navigate)", "open ocean far from land"],
    ),

    unique_features=[
        "largest flying animal in Earth's history — giraffe-height when standing, fighter-jet wingspan",
        "primarily a terrestrial stalking predator like a giant stork, not exclusively a fish-catcher",
        "quadrupedal launch was the ONLY way it could take off — biomechanically impossible to run-and-flap",
    ],

    mj_shorthand=[
        "giraffe-height standing on folded wings",
        "extremely long lancet-shaped toothless beak",
        "10-11m wingspan largest flying animal ever",
        "pycnofiber-covered lightweight hollow bones",
        "long stiff vertical neck when standing",
        "terrestrial stork-like stalking posture",
    ],

    recommended_stylize=(75, 125, 250),

    known_failures=[
        "teeth — Quetzalcoatlus is TOOTHLESS",
        "small size — giraffe-height when standing; must not look small",
        "exclusively aquatic — primarily a terrestrial stalking predator, like a giant stork",
    ],
)
