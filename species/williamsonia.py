"""Williamsonia — scientifically accurate morphology module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Williamsonia",
    common_name="Bennettitale",
    period="Jurassic–Cretaceous (200–70 Ma)",
    habitat="plant",

    integument=Integument(
        primary_covering="short thick trunk covered in old leaf bases, diamond-patterned bark",
        texture_detail="trunk covered in persistent leaf bases giving rough textured surface, armor-like bark",
        special_structures="large flower-like reproductive cone structures nestled between palm-like fronds — look like primitive flowers but are NOT true flowers",
    ),

    body=BodyProportions(
        body_length_m=3.0,
        build="short stocky trunk with crown of palm-like fronds at top, cycad-like overall form",
        neck="crown of pinnate (feather-like) fronds spreading from trunk top",
        silhouette="resembles a stocky palm or cycad with flower-like cones between fronds",
        size_comparison="up to 3m tall, stocky and robust, palm-like in garden settings",
    ),

    flora=FloraAssociation(
        primary_flora=["Jurassic–Cretaceous understory and mid-canopy alongside conifers and ferns"],
        ground_cover="ferns and cycads at ground level",
        canopy="beneath conifer canopy, open woodland settings",
        banned_flora=["grass", "modern broadleaf deciduous trees"],
    ),

    unique_features=[
        "flower-like cone structures are NOT true flowers — convergent evolution, bennettitalean reproductive organs",
        "often confused with true cycads but completely separate lineage (Bennettitales)",
        "went extinct in the Cretaceous — replaced by true flowering plants",
    ],

    mj_shorthand=[
        "flower-like cones between palm fronds",
        "short stocky trunk with leaf-base armor",
        "crown of pinnate feather-like fronds",
        "cycad-like palm-like overall form",
        "3m stocky Mesozoic bennettitale",
    ],
)
