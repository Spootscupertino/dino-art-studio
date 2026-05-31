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
        tooth_shape="thick banana-shaped serrated conical teeth, D-shaped in cross section at front (incisiform premaxillary teeth), laterally compressed blades at sides, honey-gold to cream colored",
        tooth_count_note="approximately 50–60 teeth total: ~13 premaxillary incisors (front), ~17 maxillary (upper jaw), ~15 dentary (lower jaw), largest up to 30cm including root; anterior teeth visibly prominent when mouth slightly open",
        jaw_mechanics="extremely powerful bite — 6+ metric tons of force, bone-crushing capability confirmed by coprolites containing pulverized bone, jaw muscles visible at angle of jaw",
        bite_force_note="strongest bite force of any terrestrial animal ever measured — could pulverize bone",
        visible_teeth="conical teeth visible along jaw line, slight wear facets and striations on working edges, honey-gold coloration from taphonomy, anterior teeth prominent and visible when mouth slightly open",
    ),

    limbs=LimbStructure(
        forelimb="tiny two-fingered arms, only 1m long on a 12m animal — vestigial but heavily muscled, digits I and II with pronounced curved claws",
        hindlimb="massively powerful pillar-like legs with elongated metatarsals, built for sustained walking and short bursts, three weight-bearing toes each with pronounced curved claws",
        stance="obligate biped, digitigrade stance, tail held horizontally as counterbalance",
        digit_count="two functional fingers on hand with prominent curved claws, three weight-bearing toes on foot with vestigial hallux",
        special_appendage="forelimb claws: 4-5 inches long, curved sickle-like, dark keratin with rough texture, claw angle 45°–60° downward; hindlimb claws: large and prominent on digits II–IV, dark keratin with wear striations",
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
        "tiny two-fingered arms — NOT three-fingered, NOT grasping, vestigial but heavily muscled with prominent dark curved claws 4–5 inches long",
        "forelimb claws: curved sickle-like keratin, angled 45°–60° downward, visible even when arm at rest, rough dark texture with striations",
        "hindlimb claws: large and sharp, digits II–IV carry weight, visible claw wear and striations, dark keratin with rough texture",
        "teeth: 50–60 conical honey-gold serrated teeth visible along jaw line when mouth slightly open, wear facets and edge striations visible, pronounced jaw musculature at angle",
        "tail held rigidly horizontal as active counterbalance — NEVER dragging on the ground",
        "lips probable — teeth not permanently exposed; keratinous lip tissue covered teeth when mouth closed, slight jaw gap shows conical anterior teeth",
        "no pronated wrists — palms face inward (clapping position), NOT downward",
        "predominantly scaly hide per Bell et al. 2017 skin impressions — NOT fully feathered like Yutyrannus",
    ],

    mj_shorthand=[
        "dark curved keratin claws 4-5 inches on hands and feet, angled downward",
        "conical honey-gold teeth visible along jaw, wear striations",
        "tiny two-fingered muscular arms, palms inward",
        "massive deep skull with forward binocular eyes",
        "tight pebbly scaly hide, sparse dark dorsal filament ridge",
        "thick muscular tail held horizontal counterbalance",
        "pillar-like hindlimbs digitigrade stance",
    ],

    bias_corrections=[
        "two-fingered hands NOT three-fingered",
        "horizontal tail NOT dragging on ground",
        "predominantly scaly hide NOT shaggy feathered",
        "honey-gold teeth NOT bright white",
    ],

    coloration_phrase="earth-toned olive-brown dorsal, tawny countershaded underbelly, drab naturalistic palette",

    scale_anchor="12 meters long, 4m at hip, 8-tonne apex predator",

    recommended_stylize=(50, 75, 150),

    known_failures=[
        "three-fingered arms — MJ defaults to three fingers; must specify two-fingered with claws",
        "missing or tiny forelimb claws — must explicitly specify 4-5 inch curved keratin claws on fingers",
        "claws too long (>6 inches) or too short (<3 inches) — specify 4-5 inch curved sickle",
        "claws blunt or rounded — must specify curved, pointed, keratin texture, rough",
        "claws pointing forward — must specify 45°–60° downward angle, sickle-like curve",
        "missing or blunt hindlimb claws — must specify sharp dark curved claws on feet",
        "teeth hidden completely — must specify conical visible teeth along jaw line when mouth slightly open",
        "teeth too small or not visible — must specify 50-60 conical honey-gold teeth with wear facets",
        "teeth look artificial/plastic — must specify natural serrated edges, wear striations, honey-gold color",
        "bright white teeth — use honey-gold, cream, or natural fossil-weathered coloration, never bright white",
        "dragging tail — MJ defaults to tail on ground; must specify horizontal",
        "pronated wrists — MJ renders palms-down; correct is palms-inward",
        "fully feathered body — adult T. rex was predominantly scaly per Bell et al. 2017; only a sparse dorsal-midline filament ridge is defensible, NOT shaggy plumage over the whole body",
        "rainbow/parrot coloration — keep palette earth-toned (olive, slate, tawny) like a large monitor or crocodile",
    ],
)
