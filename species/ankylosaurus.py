"""Ankylosaurus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Ankylosaurus",
    common_name="Ankylosaurus",
    period="Late Cretaceous (68–66 Ma)",
    habitat="terrestrial",

    skull=SkullAnatomy(
        overall_shape="wide flat triangular skull covered in bony armor tiles, about 60cm long and equally wide",
        distinctive_features="four prominent pyramidal horns at skull corners — two at rear, two above eyes, entire skull surface armored",
        eye_description="small laterally placed eyes set behind bony orbital horns",
    ),

    dentition=DentitionProfile(
        tooth_shape="tiny leaf-shaped teeth, absurdly small relative to body size — about the size of a fingernail",
        jaw_mechanics="weak jaw muscles, minimal chewing — selected soft low-growing vegetation, gut fermentation for processing",
    ),

    limbs=LimbStructure(
        forelimb="short robust forelimbs, shorter than hindlimbs",
        hindlimb="short powerful columnar hindlimbs",
        stance="obligate quadruped, very low and wide stance, body held close to ground",
        digit_count="five fingers on hand, three toes on foot, all with blunt hooflike claws",
    ),

    integument=Integument(
        primary_covering="entire dorsal surface covered in bony osteoderms (armor plates) embedded in skin, interlocking like chain mail",
        texture_detail="varying sizes of bony osteoderms — large oval scutes along flanks, smaller knobby armor across back, triangular spikes along body sides",
        armor="head to tail dorsal armor with rows of bony scutes, lateral triangular spikes along body sides, armored eyelids",
        special_structures="massive bony tail club formed by fused osteoderms at tail tip — a solid bony mass used as a weapon",
    ),

    body=BodyProportions(
        body_length_m=8.0,
        body_mass_kg=6000,
        build="extremely wide flat body, low to ground, built like a living tank — widest point at hips",
        neck="short thick armored neck, limited range of motion",
        tail="muscular tail with massive bony club at tip — swung laterally as defensive weapon capable of shattering bone",
        silhouette="wide flat armored tank on four short legs, rows of lateral spikes, massive bony tail club",
        size_comparison="8m long, only 1.7m at hip but extremely wide — low-slung armored tank, heavier than African elephant",
    ),

    coloration=ColorationEvidence(
        likely_pattern="possibly disruptive countershading despite armor — nodosaur Borealopelta preserves reddish-brown countershaded coloration, Ankylosaurus may have been similar",
        fossil_evidence="related Borealopelta preserves countershaded coloration (dark above, light below) — suggests large armored dinosaurs still needed camouflage from predators",
    ),

    locomotion=LocomotionProfile(
        primary_mode="obligate quadruped, slow graviportal",
        gait_detail="wide slow gait, very low center of gravity, nearly impossible to flip over",
        speed_note="estimated maximum 6–10 km/h — slow but heavily armored, stood its ground rather than fleeing",
    ),

    flora=FloraAssociation(
        primary_flora=["Late Cretaceous Hell Creek flora", "ferns", "conifers", "low angiosperms"],
        ground_cover="ferns, low flowering plants, ground-level vegetation",
        canopy="mixed conifer and angiosperm woodland",
        banned_flora=["grass", "modern broadleaf deciduous forest"],
    ),

    unique_features=[
        "tail club was a solid mass of fused bone — could generate enough force to shatter the leg bones of a tyrannosaur",
        "entire dorsal surface armored — even the eyelids had bony armor",
        "ventral surface unarmored — belly was the only vulnerability, hence the wide low stance making it nearly impossible to flip",
        "despite heavy armor, related species Borealopelta shows countershaded camouflage — even armored tanks needed to hide from predators",
    ],

    mj_shorthand=[
        "massive bony tail club",
        "interlocking dorsal armor osteoderms",
        "low flat wide tank body",
        "four pyramidal skull horns",
        "lateral triangular body spikes",
        "armored eyelids",
    ],
)
