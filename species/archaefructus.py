"""Archaefructus — scientifically accurate morphology module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Archaefructus",
    common_name="First Flower",
    period="Early Cretaceous (125 Ma, Yixian Formation)",
    habitat="plant",

    integument=Integument(
        primary_covering="slender herbaceous stems with small dissected leaves",
        texture_detail="delicate fine-stemmed aquatic plant, no bark, thin flexible stems",
        special_structures="tiny primitive flower-like reproductive structures at stem tips — among earliest known angiosperms",
    ),

    body=BodyProportions(
        body_length_m=0.5,
        build="small slender herbaceous aquatic plant, rooted in shallow lake sediment with stems reaching above water",
        neck="thin branching stems with finely dissected compound leaves",
        silhouette="small aquatic herb with feathery dissected leaves and tiny fruit clusters at tips",
        size_comparison="about 50 cm tall, small delicate aquatic plant — one of the earliest flowering plants",
    ),

    flora=FloraAssociation(
        primary_flora=["shallow Cretaceous lake margins alongside horsetails and ferns"],
        ground_cover="aquatic — grows rooted in lake-bottom sediment with stems emerging from shallow water",
        canopy="none — low aquatic herb growing in open water and lake margins",
        banned_flora=["grass", "large modern flowers"],
    ),

    unique_features=[
        "among the earliest known flowering plants (angiosperms)",
        "aquatic lifestyle — rooted in shallow lake sediment with stems reaching above water",
        "tiny primitive flower-like reproductive structures, NOT large showy blossoms",
        "finely dissected fernlike compound leaves give a feathery appearance",
        "preserved in the Yixian Formation of China alongside feathered dinosaurs",
    ],

    mj_shorthand=[
        "tiny primitive flower-like structures at tips",
        "slender herbaceous aquatic stems",
        "finely dissected feathery compound leaves",
        "rooted in shallow lake sediment",
        "50cm earliest known flowering plant",
    ],
)
