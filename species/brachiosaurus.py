"""Brachiosaurus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Brachiosaurus",
    common_name="Brachiosaurus",
    period="Late Jurassic (154–150 Ma)",
    habitat="terrestrial",

    skull=SkullAnatomy(
        overall_shape="small broad skull with arched nasal crest above eyes, wide flat snout",
        distinctive_features="distinctive arched nasal crest above and between eyes, broad spatulate snout",
        eye_description="laterally placed eyes set below the nasal arch",
        nostril_position="nares high on the nasal arch — originally thought to be a snorkel, now known to be just anatomy",
    ),

    dentition=DentitionProfile(
        tooth_shape="spatulate (spoon-shaped) chisel-like teeth for stripping foliage from branches",
        jaw_mechanics="simple raking jaw motion — stripped foliage rather than chewing, food processing in gizzard",
    ),

    limbs=LimbStructure(
        forelimb="extremely long columnar forelimbs — LONGER than hindlimbs (unique among sauropods), giving steep upward body slope",
        hindlimb="shorter columnar hindlimbs, massive but notably shorter than forelimbs",
        stance="obligate quadruped, fully columnar graviportal limbs, elephant-like weight distribution",
        digit_count="one claw on thumb only (no other hand claws visible), feet with broad elephant-like pad",
    ),

    integument=Integument(
        primary_covering="small non-overlapping pebbly scales across body",
        texture_detail="small hexagonal ground scales, possibly wrinkled hide on neck and flanks like elephant skin",
    ),

    body=BodyProportions(
        body_length_m=22.0,
        body_mass_kg=56000,
        build="enormous long-necked sauropod with distinctively LONGER forelimbs than hindlimbs — gives giraffe-like upward slope from hips to shoulders",
        neck="extremely long neck (9m+) held at a steep upward angle due to elevated shoulder position — highest feeding reach of any dinosaur",
        tail="relatively short for a sauropod, tapering, held roughly horizontal",
        silhouette="giraffe-proportioned giant with forequarters higher than rear, long steep neck, small head held high",
        size_comparison="22m long, 13m tall, 56 tonnes — could peer into fifth-story windows, one of the tallest dinosaurs known",
    ),

    coloration=ColorationEvidence(
        likely_pattern="possibly dappled countershading — large herbivore in conifer woodland",
    ),

    locomotion=LocomotionProfile(
        primary_mode="obligate quadruped, slow graviportal walker",
        gait_detail="wide-gauge trackway, columnar limbs, elephant-like locomotion but with longer stride",
        speed_note="estimated 3–5 km/h cruising speed — slow but covered ground with enormous strides",
    ),

    flora=FloraAssociation(
        primary_flora=["Late Jurassic Morrison Formation conifers", "araucaria conifers", "tree ferns", "cycads", "ginkgoes"],
        ground_cover="ferns, horsetails, low cycads",
        canopy="tall conifer canopy — Brachiosaurus was the high-browser, reaching treetops others could not",
        banned_flora=["grass", "flowering plants (angiosperms barely existed)", "broadleaf deciduous forest"],
    ),

    unique_features=[
        "forelimbs LONGER than hindlimbs — gives distinctive giraffe-like upward-sloping body, unique among common sauropods",
        "highest feeding reach of any dinosaur — could browse at 13m+ height",
        "nasal arch above eyes gives the skull a distinctive crested appearance",
        "NOT depicted in water up to its neck — fully terrestrial, the snorkel hypothesis was abandoned decades ago",
    ],

    mj_shorthand=[
        "giraffe-proportioned sauropod forequarters higher than rear",
        "extremely long steep-angled neck",
        "arched nasal crest above eyes",
        "columnar elephant-like legs",
        "small spatulate-toothed head",
        "22m long 56-tonne giant",
    ],
)
