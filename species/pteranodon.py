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
        beak="long narrow toothless pointed beak, keratinous sheath, pelican-like fish-catching tool",
    ),

    dentition=DentitionProfile(
        tooth_shape="completely toothless — beak only",
        jaw_mechanics="long pointed beak for spearing or scooping fish from water surface",
    ),

    limbs=LimbStructure(
        forelimb="enormously elongated fourth finger supporting wing membrane",
        hindlimb="relatively small hindlimbs, plantigrade foot",
        wing_or_flipper="wing membrane stretched taut between elongated fourth finger and flank, membrane to ankles",
        stance="quadrupedal on ground — walked on knuckles of folded wings and hindlimbs",
        digit_count="three small clawed fingers free at wing wrist, elongated fourth finger supports membrane",
    ),

    integument=Integument(
        primary_covering="dense hair-like pycnofibers covering body — NOT feathers, hair-like filaments",
        texture_detail="fine fuzzy pycnofiber texture visible at skin surface, similar to bat fur but finer",
        membrane="translucent wing membrane stretched taut between elongated finger and flank, membranous and leathery",
    ),

    body=BodyProportions(
        body_length_m=1.8,
        body_mass_kg=25,
        build="extremely lightweight for wingspan, hollow pneumatic bones, bird-like respiratory system",
        neck="long stiff neck for aerial fish snatching",
        tail="vestigial short tail — very short compared to earlier pterosaurs",
        silhouette="huge wingspan with pointed beak and backward crest, tiny body, quadrupedal on ground",
        size_comparison="body only 1.8m but wingspan up to 7m, weight just 25kg — extraordinarily light",
    ),

    coloration=ColorationEvidence(
        likely_pattern="uncertain, crest likely brightly colored for sexual display",
        display_structures="cranial crest was primary display structure — sexually dimorphic, likely vivid colors",
    ),

    locomotion=LocomotionProfile(
        primary_mode="soaring flight, quadrupedal terrestrial locomotion",
        flight="dynamic soaring over ocean like albatross, minimal flapping, used wind and thermals",
        gait_detail="quadrupedal on ground — folded wings as forelimbs, plantigrade hindlimbs",
        special="launched quadrupedally using all four limbs in pole-vault style — did NOT run and flap to take off",
    ),

    flora=FloraAssociation(
        primary_flora=["coastal cliffs", "open ocean over Cretaceous Western Interior Seaway"],
        banned_flora=["dense forest (would impede flight and launch)"],
    ),

    unique_features=[
        "NOT a dinosaur — a pterosaur, completely separate evolutionary lineage from dinosaurs",
        "quadrupedal launch from all fours, not bipedal running takeoff",
        "strong sexual dimorphism — males with large crests and narrow hips, females smaller crests wider hips",
    ],

    mj_shorthand=[
        "long backward-sweeping bony cranial crest",
        "toothless pointed beak pelican-like",
        "taut wing membrane to ankles",
        "fuzzy pycnofiber body covering",
        "tiny body 7m wingspan 25kg",
        "quadrupedal on ground folded wings",
    ],

    recommended_stylize=(75, 125, 250),

    known_failures=[
        "teeth — Pteranodon is TOOTHLESS; name literally means 'toothless wing'",
        "bat wings — membrane attaches to single elongated fourth finger, not between multiple fingers",
        "bipedal running — quadrupedal launch from all fours; walked on folded wings",
        "dinosaur — NOT a dinosaur; a pterosaur, completely separate lineage",
    ],
)
