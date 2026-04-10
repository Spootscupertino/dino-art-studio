"""Wattieza — scientifically accurate morphology module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Wattieza",
    common_name="First Tree",
    period="Middle Devonian (385 Ma — oldest known tree)",
    habitat="plant",

    integument=Integument(
        primary_covering="trunk covered in a pattern of leaf-base scars arranged in spirals",
        texture_detail="rough textured trunk with diamond-shaped leaf scars, no true bark like modern trees",
        special_structures="crown of fernlike fronds at the very top — resembles a tree fern more than a modern tree",
    ),

    body=BodyProportions(
        body_length_m=8.0,
        build="tall slender unbranched trunk topped with a crown of fernlike fronds",
        neck="no branches along trunk — all foliage concentrated at the top in a spreading crown",
        silhouette="tall columnar trunk with flared spreading crown of fronds — like a giant tree fern",
        size_comparison="up to 8m tall — the earliest known tree, part of the first forests on Earth",
    ),

    flora=FloraAssociation(
        primary_flora=["formed the first forests on Earth in the Devonian period"],
        ground_cover="primitive low plants, early ferns, lycopsids on Devonian forest floor",
        canopy="open canopy of Wattieza crowns — the first forest canopies on Earth",
        banned_flora=["grass", "flowers", "conifers", "broadleaf trees"],
    ),

    unique_features=[
        "the oldest known tree — formed the first forests on Earth 385 million years ago",
        "NOT a true tree in the modern sense — a cladoxylopsid fern ally",
        "tall unbranched trunk with ALL fronds concentrated at the very top",
        "trunk surface covered in spiral pattern of diamond-shaped leaf scars",
        "resembles a giant tree fern more than any modern tree",
        "grew in coastal swamp environments during the Devonian",
    ],

    mj_shorthand=[
        "crown of fernlike fronds at very top only",
        "tall slender unbranched columnar trunk",
        "spiral diamond leaf-scar trunk pattern",
        "giant tree-fern silhouette",
        "8m oldest known tree Devonian",
    ],
)
