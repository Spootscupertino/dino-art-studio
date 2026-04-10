"""Megalograptus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Megalograptus",
    common_name="Megalograptus",
    period="Ordovician (460–444 Ma)",
    habitat="arthropod",

    skull=SkullAnatomy(
        overall_shape="broad prosoma with compound eyes and distinctive long spiny chelicerae extending forward",
        distinctive_features="long spiny claws extending forward like weapons — the defining visual feature, much larger and spinier than other eurypterids",
        eye_description="compound eyes on dorsal prosoma",
    ),

    dentition=DentitionProfile(
        tooth_shape="spiny chelicerae with multiple sharp projections along inner edge",
        jaw_mechanics="spiny chelicerae for impaling and processing prey, walking legs also had gnathobases",
    ),

    limbs=LimbStructure(
        forelimb="massively elongated spiny chelicerae extending forward, longer than a human hand, covered in sharp spines",
        hindlimb="walking legs and swimming paddles",
        wing_or_flipper="swimming paddles on rear pair of legs",
        special_appendage="chelicerae are long, spine-covered, and extend forward like grasping weapons — key visual identifier",
    ),

    integument=Integument(
        primary_covering="dark segmented exoskeleton",
        texture_detail="robust chitinous exoskeleton with segmented plates, scorpion/lobster coloring reference",
    ),

    body=BodyProportions(
        body_length_m=1.0,
        body_mass_kg=10,
        build="elongated eurypterid body with distinctively large spiny front claws",
        tail="segmented post-abdomen with pointed telson",
        silhouette="sea scorpion with dramatically oversized spiny front claws — the spiny chelicerae dominate the profile",
        size_comparison="over one metre long, large lobster to small alligator scale",
    ),

    coloration=ColorationEvidence(
        likely_pattern="use scorpion and lobster colour reference — dark brown to olive",
    ),

    locomotion=LocomotionProfile(
        primary_mode="primarily aquatic, bottom-walking predator",
        swimming="swimming paddles on rear legs for aquatic locomotion",
        gait_detail="multi-legged bottom walking, claws extended forward for prey capture",
    ),

    flora=FloraAssociation(
        water_plants="Ordovician shallow marine environments, no land plants existed yet",
        banned_flora=["ALL land plants (did not exist in Ordovician)", "seagrass", "kelp"],
    ),

    unique_features=[
        "low angle emphasizing the massive spiny claws is the key composition direction",
        "one of the earliest large predators — Ordovician period, before fish dominated the seas",
        "spiny chelicerae are unique among eurypterids and the primary visual identifier",
    ],

    mj_shorthand=[
        "massively elongated spiny chelicerae claws",
        "dark segmented eurypterid body",
        "swimming paddles on rear legs",
        "pointed telson tail spine",
        "1m Ordovician sea scorpion predator",
    ],
)
