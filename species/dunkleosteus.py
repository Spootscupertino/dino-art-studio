"""Dunkleosteus — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Dunkleosteus",
    common_name="Dunkleosteus",
    period="Late Devonian (382–358 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="massive broad flat head encased in interlocking bony plates, armored skull shield",
        distinctive_features="heavy bony head shield with interlocking dermal plates, small eyes set forward on flat head",
        eye_description="small forward-set eyes in armored skull, surrounded by bony plates",
        nostril_position="nares on top of flat armored snout",
    ),

    dentition=DentitionProfile(
        tooth_shape="no true teeth — self-sharpening bony jaw blades that worked like guillotine shears",
        jaw_mechanics="fastest jaw opening of any fish — could open and close jaw in 1/50th of a second, creating suction to pull in prey",
        bite_force_note="bite force estimated at 6,000 newtons at jaw tip — one of the most powerful bites of any fish",
        visible_teeth="bony jaw blade edges visible when mouth closed, sharp overlapping shear surfaces",
    ),

    limbs=LimbStructure(
        wing_or_flipper="paired pectoral and pelvic fins, typical placoderm fin plan",
        stance="fully aquatic, armored predatory fish",
    ),

    integument=Integument(
        primary_covering="heavy interlocking bony armor plates covering head and front half of body",
        texture_detail="thick bony dermal plates on anterior half, unarmored muscular rear half with possible scaleless skin",
        armor="massive bony head shield with distinct interlocking plate pattern, thoracic armor over shoulders",
        special_structures="sharp division between armored front half and unarmored muscular rear — the rear portion is mostly unknown and reconstructed by inference",
    ),

    body=BodyProportions(
        body_length_m=6.0,
        body_mass_kg=1000,
        build="massively armored front half, muscular unarmored rear half",
        neck="head shield articulates against thoracic shield — neck joint allows head to tilt upward for wide gape",
        tail="powerful tail of unknown exact shape — reconstructed as shark-like or tuna-like based on placoderm relatives",
        silhouette="armored tank-like front half with guillotine jaws, muscular fish rear half",
        size_comparison="car-sized armored predatory fish at 6m, apex predator of Devonian seas",
    ),

    coloration=ColorationEvidence(
        likely_pattern="dark armored plates, possibly dark grey or brown, rear half uncertain",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic",
        swimming="powerful but likely not fast — built for ambush and suction feeding, not sustained pursuit",
        speed_note="jaw opened so fast it created suction to pull prey into mouth",
    ),

    flora=FloraAssociation(
        water_plants="Devonian coastal and reef waters, no land plants visible underwater",
        banned_flora=["kelp", "seagrass", "modern corals"],
    ),

    unique_features=[
        "only the armored front half is well preserved — rear body is reconstructed by analogy with other placoderms",
        "jaw opening speed created suction feeding effect — prey was pulled into mouth by water pressure",
        "one of the first vertebrate apex predators in Earth's history",
    ],

    mj_shorthand=[
        "heavy interlocking bony head armor plates",
        "self-sharpening guillotine jaw blades no teeth",
        "armored front half unarmored muscular rear",
        "flat broad head small forward eyes",
        "bony thoracic shoulder shield",
        "car-sized 6m armored predatory fish",
    ],
)
