"""Glossopteris — scientifically accurate morphology module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Glossopteris",
    common_name="Glossopteris",
    period="Permian (300–252 Ma)",
    habitat="plant",

    integument=Integument(
        primary_covering="thick woody trunk with deciduous broad tongue-shaped leaves",
        texture_detail="broad tongue-shaped leaves with prominent central midvein and net-like (reticulate) venation pattern",
        special_structures="dense leaf canopy of broad tongue-shaped leaves, deciduous — shed leaves seasonally",
    ),

    body=BodyProportions(
        body_length_m=25.0,
        build="large deciduous tree with thick woody trunk and dense leaf canopy",
        neck="spreading canopy of broad tongue-shaped leaves",
        silhouette="large broad-canopied tree with distinctive tongue-shaped leaves",
        size_comparison="large tree up to 25m, dominated Southern Hemisphere (Gondwana) forests",
    ),

    flora=FloraAssociation(
        primary_flora=["Permian Gondwanan forest dominant species"],
        ground_cover="fallen tongue-shaped leaves covering forest floor, seed fern understory",
        canopy="dense deciduous canopy of tongue-shaped leaves",
        banned_flora=["grass", "flowering plants", "modern broadleaf trees"],
    ),

    unique_features=[
        "tongue-shaped leaves with net-like venation are the key visual identifier",
        "its distribution across multiple continents was key evidence for continental drift / Gondwana",
        "went extinct at the end-Permian mass extinction — replaced by seed ferns and early conifers",
        "seed fern — reproduced with seeds not spores, despite being called a fern",
    ],

    mj_shorthand=[
        "broad tongue-shaped leaves net-like venation",
        "thick woody deciduous canopy tree",
        "prominent central midvein on each leaf",
        "fallen tongue leaves covering ground",
        "25m Permian Gondwanan forest dominant",
    ],
)
