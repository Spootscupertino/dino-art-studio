"""Tyrannosaurus rex — scientifically accurate anatomy module.

Integument hypothesis: hybrid scaly + sparse dorsal filaments.
Direct evidence: Bell et al. 2017 (Biology Letters) — scale impressions
from neck, pelvis, and tail of multiple tyrannosaurines (T. rex, Tarbosaurus,
Albertosaurus, Daspletosaurus, Gorgosaurus). All scaly, no feather impressions.
Inference: Yutyrannus huali (earlier tyrannosauroid) had extensive filaments,
so a sparse retained dorsal-midline filament ridge is defensible as a display
structure in unsampled body regions. Body is otherwise scaly and pebbly,
comparable to a Komodo dragon or Nile crocodile.
"""

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
        primary_covering="predominantly scaly hide across body, pebbly skin texture on flanks, belly, and tail; sparse coarse filamentous ridge along dorsal midline (nape to mid-back) as display structure; bare pebbly skin on head and lower legs",
        texture_detail="tight pebbly non-overlapping scales like Komodo dragon or Nile crocodile across most of body, coarse dark hair-like filaments only along dorsal ridge from nape to shoulders, scaly hide elsewhere — Bell et al. 2017 skin impressions",
        special_structures="sparse dark dorsal filament ridge as low display structure (think bristle-mane, not plumes), bare pebbly facial skin with possible flushed coloration like cassowary or vulture head, no feathers on arms or tail",
    ),

    body=BodyProportions(
        body_length_m=12.3,
        body_mass_kg=8400,
        build="massive deep-chested body, enormous skull relative to body, powerful haunches, robust and muscular throughout",
        neck="short thick muscular S-curved neck supporting massive skull",
        tail="long heavy muscular tail held rigidly horizontal as counterbalance — caudofemoralis muscle powered locomotion",
        silhouette="massive scaly bipedal predator with giant skull, tiny arms, thick horizontal tail, deep chest, sparse dark dorsal filament ridge along back",
        size_comparison="12m long, 4m at hip, 8+ tonnes — one of the largest land predators ever",
    ),

    coloration=ColorationEvidence(
        likely_pattern="earth-toned scaly hide — dark olive-brown to slate-grey dorsal scales, tawny or buff underbelly, countershaded like a Nile crocodile or large monitor lizard",
        display_structures="dark dorsal filament ridge in contrasting tone, bare facial skin flushed red-orange or rust like cassowary wattle, possible facial markings around orbits and snout",
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
        "predominantly scaly hide per Bell et al. 2017 skin impressions — NOT fully feathered like Yutyrannus",
    ],

    mj_shorthand=[
        "massive deep skull with binocular eyes",
        "tiny two-fingered arms",
        "tight pebbly scaly hide like Komodo dragon or Nile crocodile",
        "earth-toned olive-brown scales, countershaded with tawny underbelly",
        "sparse dark filamentous ridge along dorsal midline only",
        "bare pebbly facial skin flushed red-orange like cassowary head",
        "thick horizontal scaly tail as counterbalance",
        "powerful pillar-like biped legs with bare scaly feet",
        "12m long bus-sized predator",
    ],

    recommended_stylize=(50, 100, 200),

    known_failures=[
        "three-fingered arms — MJ defaults to three fingers; must specify two",
        "dragging tail — MJ defaults to tail on ground; must specify horizontal",
        "pronated wrists — MJ renders palms-down; correct is palms-inward",
        "exposed teeth when mouth closed — lips probable, teeth covered",
        "fully feathered body — adult T. rex was predominantly scaly per Bell et al. 2017; only a sparse dorsal-midline filament ridge is defensible, NOT shaggy plumage over the whole body",
        "rainbow/parrot coloration — keep palette earth-toned (olive, slate, tawny) like a large monitor or crocodile",
    ],
)
