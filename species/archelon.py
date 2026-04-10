"""Archelon — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Archelon",
    common_name="Archelon",
    period="Late Cretaceous (80–74 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="large sea turtle head with hooked beak",
        distinctive_features="powerful hooked beak for crushing shellfish, sea turtle head profile",
        eye_description="large eyes adapted for underwater vision",
        beak="strong hooked keratinous beak, no teeth, similar to modern sea turtles but scaled up",
    ),

    dentition=DentitionProfile(
        tooth_shape="no teeth — powerful hooked beak for crushing and tearing",
        jaw_mechanics="strong beak musculature for crushing hard-shelled prey like ammonites",
    ),

    limbs=LimbStructure(
        wing_or_flipper="massive front flippers for open-ocean swimming, much larger than rear flippers, span up to 5m tip-to-tip",
        stance="fully aquatic, leatherback turtle-style locomotion",
    ),

    integument=Integument(
        primary_covering="leathery skin-covered shell, NOT hard scutes like most turtles",
        texture_detail="soft leathery carapace similar to modern leatherback turtle, ridged and streamlined",
        special_structures="shell up to 4m wide, barnacles and algae growing on shell surface in life — biofouled appearance natural",
    ),

    body=BodyProportions(
        body_length_m=4.6,
        body_mass_kg=2200,
        build="massive sea turtle body plan, broad flat carapace, powerful front flippers",
        tail="short stubby tail",
        silhouette="oversized leatherback sea turtle — massive flipper span, leathery shell, hooked beak",
        size_comparison="largest sea turtle ever, shell 4m+ wide, flipper span rivaling a small aircraft",
    ),

    coloration=ColorationEvidence(
        likely_pattern="dark dorsal shell surface, lighter plastron (underside), similar to modern leatherbacks",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic, came ashore only to nest",
        swimming="powerful underwater flight using large front flippers in figure-eight pattern",
        speed_note="slow cruiser in open ocean, capable of deep dives",
        special="likely migrated thousands of kilometers like modern sea turtles, nested on beaches",
    ),

    flora=FloraAssociation(
        water_plants="open Cretaceous Western Interior Seaway and coastal waters",
    ),

    unique_features=[
        "resembles oversized leatherback turtle — leathery shell not hard scutes",
        "barnacles, algae, and marine growth covering shell was natural living condition",
    ],

    mj_shorthand=[
        "leathery ridged shell not hard scutes",
        "massive front flippers 5m span",
        "hooked keratinous beak no teeth",
        "barnacles and algae on shell biofouled",
        "oversized leatherback turtle body plan",
        "4.6m largest sea turtle ever",
    ],
)
