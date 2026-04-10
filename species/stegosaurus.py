"""Stegosaurus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Stegosaurus",
    common_name="Stegosaurus",
    period="Late Jurassic (155–150 Ma)",
    habitat="terrestrial",

    skull=SkullAnatomy(
        overall_shape="tiny narrow skull, proportionally one of the smallest skulls relative to body of any dinosaur — only about 40cm long",
        distinctive_features="extremely small head relative to body, narrow tubular snout, tiny brain case",
        eye_description="small laterally placed eyes",
        beak="narrow keratinous beak at front of mouth for selective low-browse cropping",
    ),

    dentition=DentitionProfile(
        tooth_shape="small leaf-shaped cheek teeth with coarse denticles, weak and not designed for heavy chewing",
        jaw_mechanics="simple orthal (up-down) jaw motion, minimal chewing — food processing likely done in gizzard",
    ),

    limbs=LimbStructure(
        forelimb="short robust forelimbs, much shorter than hindlimbs, giving the body a distinctive forward-sloping profile",
        hindlimb="long powerful columnar hindlimbs, significantly longer than forelimbs",
        stance="obligate quadruped despite longer hindlimbs — body slopes steeply downward from hips to shoulders",
        digit_count="five fingers on short hands, three weight-bearing toes on feet",
    ),

    integument=Integument(
        primary_covering="pebbly non-overlapping scales, skin impressions show small polygonal tubercles with occasional larger osteoderms scattered across body",
        texture_detail="small ground scales with larger round osteoderms embedded in skin across throat and flanks",
        special_structures="two staggered rows of large diamond-shaped bony dorsal plates along back and neck — plates covered in keratinous sheath and richly vascularized for thermoregulation/display, PLUS four tail spikes (thagomizer)",
    ),

    body=BodyProportions(
        body_length_m=9.0,
        body_mass_kg=5000,
        build="massive barrel body with dramatically arched back peaking over hips, tiny head at the end of a short low neck",
        neck="short low neck holding tiny head near ground level — low browser",
        tail="muscular tail held high, armed with four long bony spikes (the thagomizer) — active defensive weapon swung side-to-side",
        silhouette="massive arched-back quadruped with staggered dorsal plates, tiny head held low, four-spiked tail held high",
        size_comparison="9m long, 4m tall at hip arch, 5 tonnes — bus-sized with absurdly tiny head",
    ),

    coloration=ColorationEvidence(
        likely_pattern="dorsal plates almost certainly brightly colored or patterned — richly vascularized for display, could flush with blood to change color",
        display_structures="dorsal plates were primarily display organs with thermoregulatory secondary function — too thin and vascularized for armor",
    ),

    locomotion=LocomotionProfile(
        primary_mode="obligate quadruped, slow-moving grazer",
        gait_detail="slow deliberate walking, hindlimb-dominated locomotion, body rocking side to side",
        speed_note="estimated maximum 6–7 km/h — very slow, relied on armor and thagomizer for defense",
    ),

    flora=FloraAssociation(
        primary_flora=["Late Jurassic Morrison Formation flora", "conifers", "tree ferns", "cycads", "ginkgoes"],
        ground_cover="ferns, horsetails, mosses — low-browse vegetation",
        canopy="tall conifer and tree-fern canopy",
        banned_flora=["grass", "flowering plants (angiosperms barely existed yet)", "broadleaf deciduous forest"],
    ),

    unique_features=[
        "dorsal plates in two staggered rows — NOT paired side-by-side, alternating left-right down the back",
        "plates were NOT armor — too thin and fragile, richly vascularized for thermoregulation and display",
        "four tail spikes (thagomizer) were lethal defensive weapons — fossil evidence of stegosaur tail spike puncturing Allosaurus bone",
        "tiny head with brain the size of a walnut — one of the lowest brain-to-body ratios of any dinosaur",
    ],

    mj_shorthand=[
        "staggered diamond dorsal plates alternating left-right",
        "four tail spikes thagomizer",
        "absurdly tiny head held low",
        "arched back peaking over hips",
        "pebbly scales with embedded osteoderms",
        "bus-sized quadruped sloping forward",
    ],
)
