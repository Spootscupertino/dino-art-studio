"""Velociraptor — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Velociraptor",
    common_name="Raptor",
    period="Late Cretaceous (75–71 Ma)",
    habitat="terrestrial",

    skull=SkullAnatomy(
        overall_shape="long low narrow snout, laterally compressed skull, about 25cm long",
        distinctive_features="long narrow snout with slight upward curve, laterally placed eyes",
        eye_description="large laterally placed eyes with good binocular overlap forward",
    ),

    dentition=DentitionProfile(
        tooth_shape="small serrated blade-like teeth, recurved and laterally compressed",
        tooth_count_note="approximately 28 widely-spaced serrated teeth per side",
        jaw_mechanics="relatively weak bite — velociraptor relied on sickle claw not jaw strength",
    ),

    limbs=LimbStructure(
        forelimb="long feathered arms with three-clawed hands, propatagium confirmed — forearm folds inward at rest in bird-like wing fold, NOT held straight out",
        hindlimb="powerful digitigrade legs, second toe bearing the famous sickle claw held retracted off the ground",
        stance="obligate biped, digitigrade, sickle claw on digit II raised off ground while walking",
        digit_count="three clawed fingers, four toes with retractable sickle claw on second toe",
        special_appendage="enlarged sickle claw on second toe — held retracted off ground during locomotion, used for pinning prey",
    ),

    integument=Integument(
        primary_covering="fully feathered body — quill knobs confirmed on ulna (forearm), proving large feathers attached",
        texture_detail="dense plumage covering entire body, pennaceous feathers on arms forming wing-like structures, possibly bare scaly snout and feet",
        special_structures="quill knobs on ulna — definitive proof of large pennaceous feathers on arms; tail fan of feathers likely",
    ),

    body=BodyProportions(
        body_length_m=2.0,
        body_mass_kg=15,
        build="small lightweight low-slung feathered biped, turkey-sized — NOT the 2m-tall monsters from Jurassic Park",
        neck="long sinuous S-curved neck",
        tail="long rigid tail stiffened by interlocking bony rods (prezygapophyses) — used as dynamic counterbalance during running and attacks",
        silhouette="small low-slung feathered biped with long stiff tail, sickle-clawed feet, wing-like feathered arms",
        size_comparison="only 2m long and 15kg — about the size of a large turkey, hip height about 50cm",
    ),

    coloration=ColorationEvidence(
        likely_pattern="desert camouflage likely — tawny/sandy base with disruptive patterning, based on arid Djadochta Formation environment",
        display_structures="arm and tail feathers may have had contrasting patterns for display — similar to modern ground birds",
    ),

    locomotion=LocomotionProfile(
        primary_mode="obligate biped, digitigrade, sickle claw retracted during walking",
        gait_detail="fast agile runner, low center of gravity, stiff tail for balance during rapid direction changes",
        speed_note="fast and agile, estimated 40+ km/h in short bursts",
        special="sickle claw used for pinning prey rather than slashing — claw tip would pin struggling prey while jaws and hands processed it (Fowler RPR model)",
    ),

    flora=FloraAssociation(
        primary_flora=["arid Djadochta Formation — scrubby low vegetation", "conifers", "sparse desert vegetation"],
        ground_cover="sparse desert scrub, sand dunes, dry riverbeds",
        canopy="minimal — arid open environment with scattered low trees",
        banned_flora=["grass", "dense tropical jungle", "broadleaf deciduous forest"],
    ),

    unique_features=[
        "fully feathered body confirmed by quill knobs — looks like a ground-running bird of prey, NOT a scaly reptile",
        "only turkey-sized (2m, 15kg) — Jurassic Park's 'raptors' are actually based on Deinonychus/Utahraptor",
        "sickle claw on second toe held retracted off ground — NOT dragging, flicks downward only during prey capture",
        "palms face INWARD (clapping position) — wrists cannot pronate, arms fold like bird wings at rest",
    ],

    mj_shorthand=[
        "fully feathered turkey-sized raptor",
        "sickle claw on raised second toe",
        "long narrow feathered snout",
        "feathered wing-like arms folded at rest",
        "long rigid bony-rod tail",
        "desert-camouflage plumage",
    ],
)
