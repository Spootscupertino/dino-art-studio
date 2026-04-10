"""Pulmonoscorpius — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Pulmonoscorpius",
    common_name="Giant Scorpion",
    period="Carboniferous (336–326 Ma)",
    habitat="arthropod",

    skull=SkullAnatomy(
        overall_shape="scorpion prosoma (head-thorax) with median and lateral eyes",
        distinctive_features="typical scorpion head with multiple eye clusters on carapace",
        eye_description="median pair of eyes on top of prosoma plus lateral eye clusters, typical scorpion eye arrangement",
    ),

    dentition=DentitionProfile(
        tooth_shape="chelicerae (small pincers near mouth) for processing prey, supplemented by large pedipalp pincers",
        jaw_mechanics="chelicerae tear prey apart, pre-oral cavity for external digestion",
    ),

    limbs=LimbStructure(
        forelimb="robust pedipalps with pincers the size of human fists, primary prey-capture appendages",
        hindlimb="eight thick walking legs",
        special_appendage="large chelate pedipalps (pincers) for grabbing and crushing prey",
        stance="eight-legged terrestrial stance, body raised off ground",
        digit_count="two pedipalp pincers, eight walking legs, telson stinger",
    ),

    integument=Integument(
        primary_covering="glossy dark chitinous exoskeleton",
        texture_detail="smooth glossy dark exoskeleton with segmented plates, typical scorpion armor",
    ),

    body=BodyProportions(
        body_length_m=0.7,
        body_mass_kg=5,
        build="robust scorpion body plan, dog-sized",
        tail="segmented metasoma (tail) with five segments and curved venomous stinger at tip",
        silhouette="classic scorpion silhouette scaled up to dog size — pincers, eight legs, curved stinger tail",
        size_comparison="as long as a dog at 70cm, largest terrestrial scorpion known",
    ),

    coloration=ColorationEvidence(
        likely_pattern="glossy dark brown to black exoskeleton, typical scorpion coloring",
    ),

    locomotion=LocomotionProfile(
        primary_mode="eight-legged terrestrial crawler",
        gait_detail="typical scorpion locomotion — coordinated eight-legged walking",
        speed_note="capable of quick bursts when hunting or threatened",
        special="likely nocturnal or crepuscular like modern scorpions",
    ),

    flora=FloraAssociation(
        primary_flora=["giant club mosses", "tree ferns", "Calamites"],
        ground_cover="ferns that barely reach its back, leaf litter on coal swamp floor",
        canopy="Carboniferous coal swamp forest",
        banned_flora=["grass", "flowering plants", "modern trees"],
    ),

    unique_features=[
        "photograph like a medium-sized animal, not a small bug — eye-level ground perspective",
        "stinger was venomous — functional venom delivery system just like modern scorpions",
        "glossy dark exoskeleton should catch light realistically",
    ],

    mj_shorthand=[
        "glossy dark scorpion scaled to dog size",
        "curved venomous stinger tail",
        "robust pedipalp pincers fist-sized",
        "eight thick segmented walking legs",
        "smooth glossy chitinous exoskeleton",
        "70cm largest terrestrial scorpion",
    ],
)
