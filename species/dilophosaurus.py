"""Dilophosaurus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Dilophosaurus",
    common_name="Dilopho",
    period="Early Jurassic (193 Ma)",
    habitat="terrestrial",

    skull=SkullAnatomy(
        overall_shape="large lightly-built skull with two parallel bony crests running along the top — about 60cm long",
        distinctive_features="twin parallel longitudinal bony crests along top of skull — thin delicate bony ridges, NOT heavy horns",
        eye_description="large laterally placed eyes, good vision",
        crest_or_horn="two thin parallel bony crests running longitudinally along skull top — display structures, too thin for combat",
    ),

    dentition=DentitionProfile(
        tooth_shape="long recurved serrated teeth, laterally compressed blade-like",
        tooth_count_note="notch between premaxillary and maxillary teeth (subnarial gap) gives distinctive kinked jaw profile",
        jaw_mechanics="relatively weak bite for its size — notch in jaw may indicate less powerful jaw muscles than later theropods",
    ),

    limbs=LimbStructure(
        forelimb="moderate-length forelimbs with three clawed fingers, relatively robust for an early theropod",
        hindlimb="long powerful hindlimbs for bipedal locomotion",
        stance="obligate biped, digitigrade, held body horizontal with tail counterbalance",
        digit_count="three functional clawed fingers, four toes (three weight-bearing)",
    ),

    integument=Integument(
        primary_covering="filamentous proto-feathers covering body like emu plumage, longer display plumes along arms and tail, bare scaly legs and snout",
        texture_detail="shaggy hair-like filaments over torso and neck, coarser quilled feathers on forearms, bare leathery skin on lower legs",
        special_structures="vivid display plumes framing twin head crests like secretary bird head feathers, crest skin possibly flushed bright for display",
    ),

    body=BodyProportions(
        body_length_m=7.0,
        body_mass_kg=400,
        build="large lightly-built theropod, gracile compared to later predators, long and lean",
        neck="long flexible S-curved neck",
        tail="long thin tail held horizontal as counterbalance",
        silhouette="gracile feathered bipedal predator with distinctive twin parallel head crests, long neck, lean build",
        size_comparison="7m long, 400kg — one of the largest Early Jurassic predators, much larger than Jurassic Park depicted",
    ),

    coloration=ColorationEvidence(
        likely_pattern="earth-toned body plumage like emu — grey-brown filaments, countershaded lighter underside",
        display_structures="twin crests with vivid red-orange skin like cassowary casque, contrasting display plumes framing crests",
    ),

    locomotion=LocomotionProfile(
        primary_mode="obligate biped, digitigrade, active predator",
        gait_detail="long-strided runner, gracile build suggests agility",
        speed_note="estimated 30+ km/h — fast and agile for its time",
    ),

    flora=FloraAssociation(
        primary_flora=["Early Jurassic Kayenta Formation — conifers", "ferns", "cycads"],
        ground_cover="ferns, horsetails, early vegetation",
        canopy="conifer and tree fern canopy",
        banned_flora=["grass", "flowering plants (did not exist yet)", "broadleaf deciduous forest"],
    ),

    unique_features=[
        "NO frill — the neck frill in Jurassic Park is completely fictional, Dilophosaurus had no frill whatsoever",
        "NO venom — the spitting venom in Jurassic Park is completely fictional",
        "NOT small — Jurassic Park showed it as dog-sized but real Dilophosaurus was 7m long and 400kg",
        "twin parallel bony crests were thin delicate display structures, NOT heavy horns or weapons",
    ],

    mj_shorthand=[
        "twin parallel bony head crests with flushed display skin",
        "shaggy emu-like proto-feather plumage covering body",
        "gracile lean 7-meter feathered biped predator",
        "kinked jaw with subnarial notch in upper jaw",
        "long thin feathered horizontal tail",
        "bare scaly legs and snout",
    ],

    bias_corrections=[
        "no neck frill, no venom spitting (Jurassic Park inventions)",
        "human-sized predator NOT small dog-sized",
        "feathered emu-like NOT scaly reptile",
        "twin straight crests NOT fan crest",
    ],

    coloration_phrase="drab tawny-brown feathers with vivid flushed crests, drab body display-color head palette",

    scale_anchor="7 meters long, 400kg lean biped predator",

    recommended_stylize=(50, 75, 150),

    known_failures=[
        "neck frill — Jurassic Park invention, Dilophosaurus had NO frill whatsoever",
        "spitting venom — Jurassic Park invention, no venom capability",
        "small size — JP version is dog-sized; real Dilophosaurus was 7m and 400kg",
        "rainbow/parrot feathers — use emu/secretary bird references to keep plumage realistic",
    ],
)
