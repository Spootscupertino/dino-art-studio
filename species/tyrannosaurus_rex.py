"""Tyrannosaurus rex — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Tyrannosaurus rex",
    common_name="T. rex",
    period="Late Cretaceous (68–66 Ma)",
    habitat="terrestrial",

    skull=SkullAnatomy(
        overall_shape="massive deep skull, 1.5m long, broad at rear with powerful jaw muscles",
        distinctive_features="forward-facing eyes providing binocular vision, rugose bony ridges above orbits, lacrimal horns",
        eye_description="forward-facing eyes with excellent binocular depth perception, proportionally large",
        nostril_position="large nares at front of snout",
    ),

    dentition=DentitionProfile(
        tooth_shape="thick banana-shaped serrated teeth, D-shaped in cross section at front (incisiform premaxillary teeth), laterally compressed blades at sides",
        tooth_count_note="approximately 50–60 teeth, largest up to 30cm including root",
        jaw_mechanics="extremely powerful bite — 6+ metric tons of force, bone-crushing capability confirmed by coprolites containing pulverized bone",
        bite_force_note="strongest bite force of any terrestrial animal ever measured — could pulverize bone",
    ),

    limbs=LimbStructure(
        forelimb="tiny two-fingered arms, only 1m long on a 12m animal — vestigial but muscular",
        hindlimb="massively powerful pillar-like legs with elongated metatarsals, built for sustained walking and short bursts",
        stance="obligate biped, digitigrade stance, tail held horizontally as counterbalance",
        digit_count="two functional fingers on hand, three weight-bearing toes on foot with vestigial hallux",
    ),

    integument=Integument(
        primary_covering="predominantly pebbly non-overlapping scales across most of body, confirmed by skin impressions",
        texture_detail="small pebbly tuberculate scales similar to lizard belly scales, skin impressions from multiple specimens confirm scale covering on neck, torso, tail",
        special_structures="possible sparse filamentous integument on dorsal midline — debated; related tyrannosaurids had feathers but adult T. rex skin impressions show scales",
    ),

    body=BodyProportions(
        body_length_m=12.3,
        body_mass_kg=8400,
        build="massive deep-chested body, enormous skull relative to body, powerful haunches, robust and muscular throughout",
        neck="short thick muscular S-curved neck supporting massive skull",
        tail="long heavy muscular tail held rigidly horizontal as counterbalance — caudofemoralis muscle powered locomotion",
        silhouette="massive bipedal predator with giant skull, tiny arms, thick horizontal tail, deep chest",
        size_comparison="12m long, 4m at hip, 8+ tonnes — one of the largest land predators ever",
    ),

    coloration=ColorationEvidence(
        likely_pattern="countershaded — darker dorsal surface, lighter ventral, disruptive pattern possible for woodland ambush",
        display_structures="rugose bony ridges and lacrimal horns possibly brightly colored for species recognition or display",
    ),

    locomotion=LocomotionProfile(
        primary_mode="obligate biped, digitigrade, tail-balanced",
        gait_detail="walked with relatively narrow trackway, possibly surprisingly quiet — bird-like foot placement",
        speed_note="maximum ~28 km/h (debated), sustained efficient walking speed 8–11 km/h, NOT a sprinter despite pop culture",
        special="caudofemoralis muscle attachment on tail powered legs — tail was part of the locomotor system, not just a counterweight",
    ),

    flora=FloraAssociation(
        primary_flora=["Late Cretaceous Hell Creek flora", "conifer forests", "ferns", "palms", "flowering plants (angiosperms) emerging"],
        ground_cover="ferns and low angiosperms",
        canopy="mixed conifer and angiosperm canopy",
        banned_flora=["grass (very minimal in Late Cretaceous)", "modern broadleaf deciduous forest"],
    ),

    unique_features=[
        "tiny two-fingered arms — NOT three-fingered, NOT grasping, vestigial but heavily muscled",
        "tail held rigidly horizontal as active counterbalance — NEVER dragging on the ground",
        "lips probable — teeth not permanently exposed; keratinous lip tissue covered teeth when mouth closed",
        "no pronated wrists — palms face inward (clapping position), NOT downward",
    ],

    mj_shorthand=[
        "massive deep skull with binocular eyes",
        "tiny two-fingered arms",
        "pebbly non-overlapping scales",
        "thick horizontal tail as counterbalance",
        "powerful pillar-like biped legs",
        "serrated banana-shaped teeth",
        "12m long bus-sized predator",
    ],
)
