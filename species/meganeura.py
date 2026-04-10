"""Meganeura — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Meganeura",
    common_name="Meganeura",
    period="Carboniferous (305–299 Ma)",
    habitat="arthropod",

    skull=SkullAnatomy(
        overall_shape="large insect head dominated by enormous compound eyes",
        distinctive_features="compound eyes the size of golf balls, mandibles for catching prey in flight",
        eye_description="enormous compound eyes covering most of head, each with thousands of facets, iridescent surface",
    ),

    dentition=DentitionProfile(
        tooth_shape="powerful mandibles for seizing and consuming prey, articulated crushing mouthparts",
        jaw_mechanics="raptorial mouthparts for catching and processing insects and small vertebrates in flight",
    ),

    limbs=LimbStructure(
        forelimb="six bristled legs thick as pencils, held forward in flight basket for catching prey",
        special_appendage="spined legs forming aerial prey-catching basket during flight",
    ),

    integument=Integument(
        primary_covering="hard chitinous exoskeleton with segmented body",
        texture_detail="segmented exoskeleton with natural wear and texture, hard glossy chitin",
        special_structures="two pairs of long veined transparent wings with 70cm total wingspan, iridescent wing veins catching light",
    ),

    body=BodyProportions(
        body_length_m=0.4,
        body_mass_kg=0.15,
        build="elongated segmented dragonfly body plan, massive for an insect",
        tail="elongated abdomen with segmented exoskeleton, used as rudder in flight",
        silhouette="giant dragonfly silhouette — four transparent veined wings, elongated body, massive compound eyes",
        size_comparison="eagle-sized dragonfly with 70cm wingspan, largest flying insect ever to have lived",
    ),

    coloration=ColorationEvidence(
        likely_pattern="iridescent wing veins, body likely dark with possible metallic sheen like modern dragonflies",
        additional_notes="wings transparent with prominent veined pattern, body glossy dark chitin with possible iridescence",
    ),

    locomotion=LocomotionProfile(
        primary_mode="powerful aerial predator",
        flight="four independently moving wings allowing hovering, rapid direction changes, and high-speed pursuit",
        speed_note="fast agile flyer, aerial pursuit predator",
        special="could only exist in Carboniferous atmosphere with ~35% oxygen — higher oxygen enabled gigantic insect respiration",
    ),

    flora=FloraAssociation(
        primary_flora=["giant club mosses (Lepidodendron)", "tree ferns", "Calamites horsetails", "Sigillaria"],
        ground_cover="dense fern undergrowth in swamp forest",
        canopy="Carboniferous coal swamp canopy, humid and oxygen-rich",
        banned_flora=["grass", "flowering plants", "conifers (very rare in Carboniferous)"],
    ),

    unique_features=[
        "photograph like a bird of prey, not an insect — low angle looking up to emphasize scale",
        "iridescent wing veins catching light are key visual feature",
        "only possible in high-oxygen Carboniferous atmosphere",
    ],

    mj_shorthand=[
        "eagle-sized giant dragonfly",
        "four transparent veined iridescent wings",
        "enormous compound eyes golf-ball sized",
        "glossy dark chitinous segmented body",
        "six bristled legs in prey-catching basket",
        "70cm wingspan largest flying insect ever",
    ],
)
