"""Sigillaria — scientifically accurate morphology module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Sigillaria",
    common_name="Seal Tree",
    period="Carboniferous (383–299 Ma)",
    habitat="plant",

    integument=Integument(
        primary_covering="tall columnar trunk covered in distinctive hexagonal seal-like leaf scars in vertical rows",
        texture_detail="smooth bark with regularly-spaced hexagonal to round raised leaf scars — signature feature giving it the name 'seal tree'",
        special_structures="grass-like leaves in a tuft at the very top, Stigmaria root system spreading laterally underground",
    ),

    body=BodyProportions(
        body_length_m=30.0,
        build="tall straight columnar trunk, rarely branched, very different from its cousin Lepidodendron",
        neck="minimal branching — occasionally forked at the very top unlike the heavily branched Lepidodendron",
        silhouette="tall pillar-like trunk with hexagonal seal scars and a small tuft of grass-like leaves at the summit",
        size_comparison="up to 30m tall — massive Carboniferous club moss, a dominant coal swamp tree",
    ),

    flora=FloraAssociation(
        primary_flora=["co-dominant with Lepidodendron in Carboniferous coal swamp forests"],
        ground_cover="ferns, horsetails, and primitive ground cover plants in swampy conditions",
        canopy="formed tall canopy in coal swamp forests alongside Lepidodendron and Calamites",
        banned_flora=["grass", "flowers", "broadleaf trees"],
    ),

    unique_features=[
        "distinctive hexagonal seal-like leaf scars in vertical rows on trunk — key visual identifier",
        "NOT a true tree — a giant lycopsid (club moss) like Lepidodendron",
        "less branched than Lepidodendron — typically a single tall column with minimal forking",
        "grass-like leaves clustered only at the very top of the trunk",
        "Stigmaria root system — distinctive branching root structure spreading laterally",
        "major component of Carboniferous coal deposits — these trees literally became coal",
    ],

    mj_shorthand=[
        "hexagonal seal-like leaf scars in vertical rows",
        "tall straight rarely-branched column trunk",
        "grass-like leaf tuft at summit only",
        "smooth bark with raised round scars",
        "30m Carboniferous coal-swamp pillar tree",
    ],
)
