"""Megalodon — scientifically accurate anatomy module."""

from species.base import (
    SpeciesAnatomy, SkullAnatomy, DentitionProfile, LimbStructure,
    Integument, BodyProportions, ColorationEvidence, LocomotionProfile,
    FloraAssociation,
)

ANATOMY = SpeciesAnatomy(
    species_name="Megalodon",
    common_name="Megalodon",
    period="Miocene–Pliocene (23–3.6 Ma)",
    habitat="marine",

    skull=SkullAnatomy(
        overall_shape="broad heavy skull similar to great white shark but massively scaled up",
        distinctive_features="thick conical snout, wide-set dark eyes, jaw gape over 3m wide",
        eye_description="small dark eyes set wide apart on broad head",
    ),

    dentition=DentitionProfile(
        tooth_shape="massive triangular serrated teeth, each the size of a human hand, thick and robust",
        tooth_count_note="276 teeth in five rows, continuous replacement throughout life",
        jaw_mechanics="enormous gape exceeding 3m, bite force estimated at 108,000–182,000 newtons",
        bite_force_note="most powerful bite of any animal ever — could crush whale bones",
        visible_teeth="serrated tooth tips visible along jaw line, triangular silhouette",
    ),

    limbs=LimbStructure(
        wing_or_flipper="large pectoral fins for lift and steering, typical lamniform shark fin plan",
        stance="fully aquatic, typical shark body plan",
    ),

    integument=Integument(
        primary_covering="dermal denticles covering entire body — tiny tooth-like scales",
        texture_detail="rough sandpaper-like skin from dermal denticles, hydrodynamic micro-texture",
        special_structures="tall dorsal fin, powerful crescent-shaped caudal fin with lunate upper and lower lobes",
    ),

    body=BodyProportions(
        body_length_m=15.0,
        body_mass_kg=50000,
        build="broad heavy-bodied shark, more robust and barrel-chested than great white",
        neck="no distinct neck — head flows into body",
        tail="powerful crescent-shaped heterocercal caudal fin, high aspect ratio for sustained cruising",
        silhouette="scaled-up great white shark body plan — broad snout, massive jaws, powerful tail",
        size_comparison="school bus-sized, 15m+ long, 50 tonnes — largest predatory shark ever",
    ),

    coloration=ColorationEvidence(
        likely_pattern="countershaded — grey above, white below, similar to great white shark",
        fossil_evidence="no direct pigment evidence but phylogenetic inference supports great white-like coloration",
    ),

    locomotion=LocomotionProfile(
        primary_mode="fully aquatic",
        swimming="ram ventilating obligate swimmer, thunniform propulsion via powerful caudal fin",
        speed_note="endothermic — maintained elevated body temperature for sustained cruising and burst speed",
        special="likely a whale predator — tooth marks found on fossil whale bones, attacked from below",
    ),

    flora=FloraAssociation(
        water_plants="warm temperate to tropical open ocean, coastal and pelagic",
        banned_flora=["cold polar waters", "freshwater"],
    ),

    unique_features=[
        "heavy scarring on snout from prey impacts — battle-worn appearance natural and expected",
        "went extinct approximately 3.6 Ma, possibly due to cooling oceans and whale migration to polar waters",
        "NOT alive today despite sensationalist media — definitively extinct",
    ],

    mj_shorthand=[
        "hand-sized triangular serrated teeth",
        "broad heavy great-white body plan scaled up",
        "rough dermal-denticle sandpaper skin",
        "scarred blunt snout battle-worn",
        "powerful crescent caudal fin",
        "school-bus-sized 15m apex shark",
    ],
)
