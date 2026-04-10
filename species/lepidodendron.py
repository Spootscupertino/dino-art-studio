"""Lepidodendron — scientifically accurate morphology module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Lepidodendron",
    common_name="Scale Tree",
    period="Carboniferous (360–300 Ma)",
    habitat="plant",

    integument=Integument(
        primary_covering="trunk covered in distinctive diamond-shaped leaf scars arranged in spiral pattern",
        texture_detail="bark surface like reptile scales — regular diamond-shaped pattern from fallen microphyll leaf bases",
        special_structures="trunk covered in perfectly regular diamond-shaped leaf scar pattern, each scar with visible vascular bundle marks",
    ),

    body=BodyProportions(
        body_length_m=40.0,
        build="tall straight columnar trunk with no branches until crown, club moss biology despite tree form",
        neck="crown of grass-like drooping leaves only at very top of trunk",
        tail="extensive root system (Stigmaria) spreading horizontally through swamp substrate",
        silhouette="tall straight trunk with diamond-patterned bark, grass-like leaf crown only at very top",
        size_comparison="up to 40m tall — towering tree-sized club moss, one of the tallest Carboniferous plants",
    ),

    flora=FloraAssociation(
        primary_flora=["Carboniferous coal swamp dominant canopy species", "grew alongside Sigillaria and Calamites"],
        ground_cover="swamp water at base, fern understory",
        canopy="formed dominant canopy of Carboniferous coal swamp forests",
        banned_flora=["grass", "flowering plants", "modern broadleaf trees", "conifers (co-existed but rare in swamps)"],
    ),

    unique_features=[
        "NOT a true tree — a giant club moss (lycopsid), reproduced with spores not seeds",
        "diamond-shaped leaf scar pattern on trunk is the key visual identifier — looks like reptile scales",
        "grew rapidly and died young — trunk was mostly bark with little actual wood",
        "dominant canopy tree of Carboniferous coal swamps — the coal we burn today is largely from these trees",
    ],

    mj_shorthand=[
        "diamond-shaped spiral leaf scars on trunk",
        "tall straight unbranched columnar trunk",
        "grass-like drooping leaf crown at top only",
        "reptile-scale-patterned bark texture",
        "40m towering Carboniferous club moss",
    ],
)
