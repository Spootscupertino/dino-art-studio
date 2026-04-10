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
        primary_covering="likely small scales covering body, possibly with filamentous integument — early coelurosaur-line theropod",
        texture_detail="small pebbly scales assumed, limited direct evidence",
    ),

    body=BodyProportions(
        body_length_m=7.0,
        body_mass_kg=400,
        build="large lightly-built theropod, gracile compared to later predators, long and lean",
        neck="long flexible S-curved neck",
        tail="long thin tail held horizontal as counterbalance",
        silhouette="gracile bipedal predator with distinctive twin parallel head crests, long neck, lean build",
        size_comparison="7m long, 400kg — one of the largest Early Jurassic predators, much larger than Jurassic Park depicted",
    ),

    coloration=ColorationEvidence(
        likely_pattern="no direct evidence — crests likely brightly colored for display given their delicate non-combat structure",
        display_structures="twin crests almost certainly display structures — too thin for combat, likely brightly colored or patterned",
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
        "twin parallel bony head crests",
        "gracile lean 7m biped predator",
        "kinked jaw with subnarial notch",
        "no frill no venom",
        "recurved serrated blade teeth",
        "long thin horizontal tail",
    ],
)
