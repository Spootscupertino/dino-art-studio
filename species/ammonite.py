"""Ammonite — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Ammonite",
    common_name="Ammonite",
    period="Jurassic–Cretaceous (widespread across Mesozoic)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="soft cephalopod head emerging from coiled shell aperture",
        distinctive_features="large intelligent eye visible at shell opening, tentacles extending outward",
        eye_description="large cephalopod eye with W-shaped pupil (nautilus analogy), intelligent and alert",
    ),

    dentition=DentitionProfile(
        tooth_shape="central beak (radula) hidden among tentacles, similar to nautilus",
        jaw_mechanics="beak and radula for tearing soft prey and scavenged material",
    ),

    limbs=LimbStructure(
        wing_or_flipper="soft muscular tentacles extending from shell aperture, used for locomotion and prey capture",
    ),

    integument=Integument(
        primary_covering="coiled chambered shell with ribbed external surface",
        texture_detail="shell surface varies — ribbed, knobbed, smooth, or ornamented depending on species",
        special_structures="iridescent nacre (mother-of-pearl) sheen on shell surface, chambered interior with siphuncle for buoyancy control",
    ),

    body=BodyProportions(
        body_length_m=0.5,
        body_mass_kg=5,
        build="coiled chambered shell housing squid-like soft body",
        silhouette="classic coiled spiral shell with tentacles and eye emerging from opening",
        size_comparison="typical species 10–50cm diameter, some species reached 2m+",
    ),

    coloration=ColorationEvidence(
        fossil_evidence="shell preserves iridescent nacre in many fossils — confirmed pearlescent sheen",
        likely_pattern="living shell likely displayed iridescent nacre sheen with species-specific color patterns",
        additional_notes="soft body coloration unknown but likely dark, cephalopod-like color-changing ability possible",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic",
        swimming="jet propulsion by expelling water through hyponome (siphon), similar to nautilus",
        speed_note="slow but maneuverable, drifting and jet-pulsing through water column",
        special="buoyancy controlled by gas-filled chambers in shell — could adjust depth by changing gas/liquid ratio",
    ),

    flora=FloraAssociation(
        water_plants="open ocean water column, all depths",
    ),

    unique_features=[
        "shell patterns (ribbing, knobs, spines) vary enormously between species — key identifier",
        "iridescent nacre on shell is preserved in fossils and would have been visible in life",
        "closer related to squid and octopus than to nautilus, despite superficial similarity",
    ],

    mj_shorthand=[
        "coiled ribbed iridescent nacre shell",
        "tentacles and large eye at shell opening",
        "mother-of-pearl pearlescent sheen",
        "chambered spiral nautilus-like form",
        "squid-like soft body in shell",
    ],
)
