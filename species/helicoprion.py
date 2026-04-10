"""Helicoprion — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Helicoprion",
    common_name="Helicoprion",
    period="Permian–Early Triassic (290–250 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="ratfish-like head with spiral tooth whorl incorporated into lower jaw",
        distinctive_features="single spiral whorl of teeth curling under lower jaw like a circular saw — older smaller teeth at center, newest largest at outer edge",
        eye_description="moderate-sized eyes, ratfish-like",
    ),

    dentition=DentitionProfile(
        tooth_shape="spiral tooth whorl — teeth arranged in a spiral coil in the lower jaw, progressively larger toward outer edge",
        tooth_count_note="tooth whorl contains over 100 teeth in spiral, only outer teeth functional for cutting",
        jaw_mechanics="lower jaw closes upward, tooth whorl acts as rotating cutting surface against upper jaw cartilage",
        bite_force_note="moderate — designed for slicing soft-bodied prey like ammonites and squid",
        visible_teeth="tooth whorl mostly concealed within lower jaw when closed, only newest largest teeth exposed",
    ),

    limbs=LimbStructure(
        wing_or_flipper="typical chimaera-like paired fins for swimming",
        stance="fully aquatic, cartilaginous body",
    ),

    integument=Integument(
        primary_covering="smooth cartilaginous body, shark-relative skin",
        texture_detail="smooth skin without heavy dermal denticles, ratfish-like texture",
    ),

    body=BodyProportions(
        body_length_m=4.0,
        body_mass_kg=300,
        build="elongated streamlined body, chimaera/ratfish body plan, not classic shark shape",
        tail="heterocercal tail, upper lobe elongated",
        silhouette="bizarre profile — ratfish-like body with spiral tooth whorl visible in lower jaw",
        size_comparison="about 4m long, moderate-sized deep ocean predator",
    ),

    coloration=ColorationEvidence(
        likely_pattern="dark deep-water coloration probable, possibly uniform dark grey or brown",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic",
        swimming="steady cruising, chimaera-like swimming pattern",
        speed_note="not built for burst speed, cruising predator of soft-bodied prey",
        special="deep ocean dweller, not a surface or reef animal",
    ),

    flora=FloraAssociation(
        water_plants="deep Permian ocean, open water column",
        banned_flora=["reefs", "shallow coastal waters"],
    ),

    unique_features=[
        "tooth whorl is NOT external like a circular saw — CT scans confirm it sits inside the lower jaw symphysis",
        "no upper teeth — upper jaw is smooth cartilage that the whorl closes against",
        "closely related to modern ratfish and chimaeras, NOT a true shark",
    ],

    mj_shorthand=[
        "spiral tooth whorl in lower jaw",
        "ratfish-like elongated body",
        "smooth cartilaginous skin",
        "whorl teeth concealed inside jaw",
        "heterocercal tail upper lobe extended",
        "4m deep-ocean chimaera relative",
    ],
)
