"""Araucaria — scientifically accurate morphology module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Araucaria",
    common_name="Monkey Puzzle",
    period="Jurassic–present (living fossil, 200+ Ma lineage)",
    habitat="plant",

    integument=Integument(
        primary_covering="deeply furrowed thick bark on tall straight trunk",
        texture_detail="stiff triangular overlapping scale-like leaves densely covering all branches, sharp and leathery",
        special_structures="large round seed cones, horizontal branch tiers with symmetrical spiral branching pattern",
    ),

    body=BodyProportions(
        body_length_m=50.0,
        build="tall straight trunk with horizontal branches in distinct tiers, pyramidal crown",
        neck="symmetrical tiered horizontal branches creating pagoda-like canopy",
        silhouette="tall conifer with distinctive tiered horizontal branches and scale-covered branchlets",
        size_comparison="up to 50m tall, massive ancient conifer — still alive today as monkey puzzle trees",
    ),

    flora=FloraAssociation(
        primary_flora=["dominant Jurassic–Cretaceous conifer, co-existed with dinosaurs"],
        ground_cover="fern and cycad understory beneath araucaria canopy",
        canopy="formed tall closed canopy in Mesozoic forests, fed upon by sauropods",
        banned_flora=["grass", "modern broadleaf deciduous forest"],
    ),

    unique_features=[
        "living fossil — still alive today as monkey puzzle trees (Araucaria araucana) in South America",
        "stiff triangular overlapping scale-like leaves are the key visual identifier",
        "large round seed cones — food source for Mesozoic animals",
        "the tree that sauropods like Brachiosaurus fed upon in Jurassic forests",
    ],

    mj_shorthand=[
        "stiff triangular overlapping scale-leaves",
        "tiered horizontal pagoda-like branches",
        "deeply furrowed thick bark",
        "large round seed cones on branches",
        "50m tall Mesozoic monkey puzzle conifer",
    ],
)
