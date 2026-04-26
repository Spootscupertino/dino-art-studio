"""Pteranodon — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Pteranodon",
    common_name="Pteranodon",
    period="Late Cretaceous (86–84 Ma)",
    habitat="aerial",

    skull=SkullAnatomy(
        overall_shape="elongated skull with long backward-sweeping cranial crest and toothless pointed beak",
        distinctive_features="long bony crest extending backward from skull — size varies by sex, males have much larger crests",
        eye_description="large eyes set laterally, good vision for spotting fish from height",
        nostril_position="nares set back along beak",
        crest_or_horn="long backward-sweeping bony cranial crest, sexually dimorphic — males with tall crest, females with smaller",
        beak="long narrow toothless pointed beak with keratinous sheath, used for fish-catching — NOT bird-like, not a pelican beak",
    ),

    dentition=DentitionProfile(
        tooth_shape="completely toothless — beak only",
        jaw_mechanics="long pointed beak for spearing or scooping fish from water surface",
    ),

    limbs=LimbStructure(
        forelimb="enormously elongated fourth finger supporting leathery wing membrane, bat-like wings with no feathers",
        hindlimb="relatively small hindlimbs, plantigrade foot, used as rear legs in quadrupedal walking",
        wing_or_flipper="leathery skin wing membrane stretched taut between elongated fourth finger and ankles, bat-like wings, no feathers, no plumage, no primary feathers",
        stance="quadrupedal stance, walking on folded wing knuckles, front limbs acting as front legs supporting weight, bat-like terrestrial crawling — NOT bipedal standing, NOT bird-like",
        digit_count="three small clawed fingers free at wing wrist, elongated fourth finger supports membrane",
    ),

    integument=Integument(
        primary_covering="hair-like pycnofibers covering body, fuzz, mammalian-like hair — NOT feathers, NOT plumage, NOT avian",
        texture_detail="fine fuzzy pycnofiber texture visible at skin surface, similar to bat fur but finer, mammalian-hair texture not feather texture",
        membrane="leathery skin wing membrane, bat-like wings, translucent and thin, stretched taut between elongated finger and flank, no feathers",
    ),

    body=BodyProportions(
        body_length_m=1.8,
        body_mass_kg=25,
        build="extremely lightweight for wingspan, hollow pneumatic bones",
        neck="long stiff neck for aerial fish snatching",
        tail="vestigial short tail — very short compared to earlier pterosaurs",
        silhouette="huge bat-like leathery wings with pointed beak and backward crest, small body, quadrupedal on ground walking on folded wing knuckles, no feathers",
        size_comparison="body only 1.8m but wingspan up to 7m, weight just 25kg — extraordinarily light",
    ),

    coloration=ColorationEvidence(
        likely_pattern="uncertain, crest likely brightly colored for sexual display",
        display_structures="cranial crest was primary display structure — sexually dimorphic, likely vivid colors",
    ),

    locomotion=LocomotionProfile(
        primary_mode="soaring flight, quadrupedal terrestrial locomotion",
        flight="dynamic soaring over ocean like albatross, minimal flapping, used wind and thermals",
        gait_detail="quadrupedal terrestrial locomotion — walked on folded wing knuckles as front limbs, plantigrade hindlimbs as rear legs, bat-like crawling stance",
        special="launched quadrupedally using all four limbs in pole-vault style — did NOT run and flap to take off",
    ),

    flora=FloraAssociation(
        primary_flora=["coastal cliffs", "open ocean over Cretaceous Western Interior Seaway"],
        banned_flora=["dense forest (would impede flight and launch)"],
    ),

    unique_features=[
        "NOT a dinosaur, NOT a bird — a pterosaur, completely separate evolutionary lineage",
        "quadrupedal launch from all fours, not bipedal running takeoff",
        "strong sexual dimorphism — males with large crests and narrow hips, females smaller crests wider hips",
    ],

    mj_shorthand=[
        "long backward-sweeping bony cranial crest",
        "toothless pointed beak with keratin sheath",
        "leathery bat-like wing membrane to ankles, no feathers",
        "hair-like pycnofibers fuzz mammalian-like hair",
        "tiny body 7m wingspan 25kg",
        "quadrupedal stance walking on folded wing knuckles",
    ],

    recommended_stylize=(75, 125, 250),

    known_failures=[
        "teeth — Pteranodon is TOOTHLESS; name literally means 'toothless wing'",
        "bat-wing error — membrane attaches to single elongated fourth finger, not between multiple fingers",
        "bird morphology — NOT a pelican, stork, or heron; bat-like wings, not feathered",
        "feathers — pycnofibers are hair-like fuzz, not plumage or flight feathers",
        "bipedal standing — quadrupedal on ground, walking on folded wing knuckles",
        "dinosaur — NOT a dinosaur; a pterosaur, completely separate lineage",
    ],
)
