"""Xiphactinus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Xiphactinus",
    common_name="Bulldog Fish",
    period="Late Cretaceous (100–66 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="large upturned jaw giving bulldog-like underbite profile",
        distinctive_features="prominent upturned lower jaw with large fangs protruding forward, bulldog underbite",
        eye_description="moderately large eyes, set laterally",
    ),

    dentition=DentitionProfile(
        tooth_shape="large prominent fangs in front of jaws, recurved and pointed",
        tooth_count_note="prominent anterior fangs supplemented by smaller teeth along jaw",
        jaw_mechanics="large gape for swallowing prey up to 2m long whole",
        bite_force_note="powerful grip-and-swallow feeding strategy",
        visible_teeth="fang tips visible protruding above and below jaw line when closed",
    ),

    limbs=LimbStructure(
        wing_or_flipper="large pectoral fins, forked caudal fin, typical bony fish fin plan",
        stance="fully aquatic, powerful predatory bony fish",
    ),

    integument=Integument(
        primary_covering="silvery scales covering body",
        texture_detail="large cycloid scales with silvery reflective surface, typical bony fish scale pattern",
    ),

    body=BodyProportions(
        body_length_m=6.0,
        body_mass_kg=500,
        build="elongated torpedo body, streamlined and muscular",
        tail="large forked caudal fin for powerful swimming",
        silhouette="large predatory bony fish with bulldog underbite and torpedo body",
        size_comparison="up to 6m long, one of the largest bony fish of the Cretaceous",
    ),

    coloration=ColorationEvidence(
        likely_pattern="silvery body with countershading — darker dorsal, brilliant silver flanks, white ventral",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic",
        swimming="powerful tail-driven swimming, burst predator",
        speed_note="fast pursuit predator in open waters of the Western Interior Seaway",
    ),

    flora=FloraAssociation(
        water_plants="open water Western Interior Seaway, Cretaceous inland sea",
    ),

    unique_features=[
        "famous fossil preserves 2m Gillicus fish swallowed whole inside Xiphactinus body cavity — prey killed the predator",
        "nicknamed Bulldog Fish for upturned jaw profile",
    ],

    mj_shorthand=[
        "bulldog underbite upturned jaw",
        "large protruding front fangs",
        "silvery cycloid scales",
        "torpedo-shaped predatory bony fish",
        "large forked caudal fin",
        "6m largest Cretaceous bony fish",
    ],
)
