"""Elasmosaurus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Elasmosaurus",
    common_name="Elasmosaur",
    period="Late Cretaceous (80–65 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="tiny skull relative to body, only about 30cm long, flat and triangular",
        distinctive_features="extremely small head at end of absurdly long neck — head barely larger than neck width",
        eye_description="large eyes for spotting fish in murky water, set laterally",
    ),

    dentition=DentitionProfile(
        tooth_shape="long needle-like interlocking teeth that mesh when jaws close — fish trap",
        jaw_mechanics="jaws snap shut rapidly, interlocking needle teeth form a cage preventing fish escape",
    ),

    limbs=LimbStructure(
        wing_or_flipper="four large broad paddle-shaped flippers — primary propulsion organs, underwater flight similar to sea turtles and penguins",
        stance="fully aquatic, four-flipper underwater flight",
    ),

    integument=Integument(
        primary_covering="smooth skin, possibly with fine pebbled texture",
        texture_detail="smooth marine reptile hide, likely countershaded",
    ),

    body=BodyProportions(
        body_length_m=14.0,
        body_mass_kg=3000,
        build="enormously long neck (over half of total body length), compact rounded torso, four large flippers, short tail",
        neck="absurdly long neck with 72 cervical vertebrae — longest neck relative to body of any animal ever, flexible for ambush darting at fish",
        tail="relatively short tail, not used for primary propulsion",
        silhouette="tiny head on impossibly long sinuous neck, compact rounded body with four large flippers, short tail",
        size_comparison="14m total but most is neck — body itself is compact, neck alone over 7m long",
    ),

    coloration=ColorationEvidence(
        likely_pattern="likely countershaded — dark above, light below, standard marine camouflage",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic, four-flipper underwater flight",
        swimming="four large flippers used in coordinated underwater flight — front flippers provide thrust, rear flippers steer, similar to sea turtle locomotion",
        speed_note="moderate swimmer, not built for speed — ambush predator using neck strike from concealment",
        special="could NOT raise head swan-like above water — neck was stiff laterally, primarily moved up-down for striking at fish below",
    ),

    flora=FloraAssociation(
        water_plants="open ocean and shallow coastal seas, Western Interior Seaway",
        banned_flora=["grass", "terrestrial forest"],
    ),

    unique_features=[
        "could NOT raise head high out of water like a swan — the classic image is wrong, neck moved primarily in horizontal and vertical planes for fish-catching",
        "NOT a dinosaur — a plesiosaur, a marine reptile from a completely different lineage",
        "72 cervical vertebrae — more neck bones than any other animal ever discovered",
        "four-flipper underwater flight — swam like a sea turtle or penguin, not like a fish",
    ],

    mj_shorthand=[
        "impossibly long sinuous neck tiny head",
        "four large paddle-shaped flippers",
        "needle-like interlocking fish-trap teeth",
        "compact rounded torso short tail",
        "smooth countershaded marine hide",
        "14m plesiosaur neck over half body length",
    ],
)
