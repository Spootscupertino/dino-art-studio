"""Leedsichthys — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Leedsichthys",
    common_name="Leedsichthys",
    period="Middle–Late Jurassic (165–152 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="broad flat head with wide gaping mouth for filter feeding",
        distinctive_features="enormous gaping mouth for engulfing water and filtering plankton, whale shark-like feeding posture",
        eye_description="relatively small eyes for body size",
    ),

    dentition=DentitionProfile(
        tooth_shape="no functional teeth — gill rakers instead, fine comb-like structures for filtering plankton",
        jaw_mechanics="ram filter feeding — swimming with mouth open to strain plankton from water",
    ),

    limbs=LimbStructure(
        wing_or_flipper="broad paddle-like pectoral fins, large caudal fin",
        stance="fully aquatic, gentle filter-feeding giant",
    ),

    integument=Integument(
        primary_covering="thin bony scales, fragile and poorly preserved",
        texture_detail="dark mottled skin, possible pattern similar to whale shark",
    ),

    body=BodyProportions(
        body_length_m=16.0,
        body_mass_kg=20000,
        build="enormous barrel-bodied bony fish, largest bony fish ever to have lived",
        tail="large forked caudal fin for steady cruising",
        silhouette="whale-sized gentle giant with enormous gaping mouth, massive body, paddle-like fins",
        size_comparison="up to 16m — whale-sized, largest bony fish in Earth's history",
    ),

    coloration=ColorationEvidence(
        likely_pattern="dark mottled pattern possible, similar to modern whale sharks or basking sharks",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic",
        swimming="slow steady cruising with mouth open for filter feeding",
        speed_note="slow cruiser, not built for speed — gentle plankton feeder",
        special="whale shark-like feeding behavior — mouth gaping open while cruising through plankton-rich water",
    ),

    flora=FloraAssociation(
        water_plants="open Jurassic ocean, plankton-rich surface waters",
    ),

    unique_features=[
        "convergent with modern whale sharks and baleen whales despite being a bony fish",
        "extremely fragmentary fossil record — size estimates based on scaling from partial remains",
    ],

    mj_shorthand=[
        "enormous gaping filter-feeding mouth",
        "whale-shark-like mottled dark skin",
        "massive barrel body paddle fins",
        "gill rakers for straining plankton",
        "gentle slow-cruising giant",
        "16m whale-sized bony fish",
    ],
)
