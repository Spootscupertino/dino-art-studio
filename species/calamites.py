"""Calamites — scientifically accurate morphology module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Calamites",
    common_name="Giant Horsetail",
    period="Carboniferous (360–300 Ma)",
    habitat="plant",

    integument=Integument(
        primary_covering="tall jointed trunk with visible nodes and ribbed surface, like giant bamboo",
        texture_detail="ribbed trunk surface with prominent longitudinal ridges between nodes, bamboo-like segmented appearance",
        special_structures="whorls of thin needle-like branches radiating from each node, giving feathery tiered appearance",
    ),

    body=BodyProportions(
        body_length_m=20.0,
        build="tall jointed segmented trunk with regular node intervals, bamboo-like",
        neck="tiered whorls of needle-like branches at each node",
        silhouette="giant segmented bamboo-like trunk with feathery whorls of branches at regular intervals",
        size_comparison="up to 20m tall — giant version of modern horsetails (which are now rarely above 1m)",
    ),

    flora=FloraAssociation(
        primary_flora=["Carboniferous swamp forest understory and mid-canopy"],
        ground_cover="swamp water, fern floor, fallen horsetail branches",
        canopy="mid-canopy between Lepidodendron giants",
        banned_flora=["grass", "flowering plants", "modern broadleaf trees"],
    ),

    unique_features=[
        "giant version of modern horsetails — same genus Equisetum still exists but now tiny",
        "jointed segmented trunk with regular nodes is the key visual identifier — looks like bamboo",
        "whorls of thin needle-like branches radiate from each node like wagon wheel spokes",
    ],

    mj_shorthand=[
        "jointed bamboo-like segmented trunk",
        "needle-branch whorls at each node",
        "ribbed longitudinal trunk surface",
        "feathery tiered canopy silhouette",
        "20m giant Carboniferous horsetail",
    ],
)
