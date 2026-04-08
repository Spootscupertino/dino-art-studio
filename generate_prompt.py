#!/usr/bin/env python3
"""
generate_prompt.py — interactive Midjourney prompt builder for dinosaur art.

Usage:
    python generate_prompt.py
    python generate_prompt.py --ar 16:9 --stylize 500 --chaos 10
    python generate_prompt.py --db /path/to/other.db
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Terminal color constants (ANSI escape codes)
# ---------------------------------------------------------------------------

class C:
    """ANSI color/style codes. All reset automatically via RESET."""
    RESET        = "\033[0m"
    BOLD         = "\033[1m"
    DIM          = "\033[2m"
    CYAN         = "\033[36m"
    BOLD_CYAN    = "\033[1;36m"
    WHITE        = "\033[37m"
    BRIGHT_WHITE = "\033[97m"
    GREEN        = "\033[32m"
    BOLD_GREEN   = "\033[1;32m"
    YELLOW       = "\033[33m"
    RED          = "\033[31m"
    BOLD_RED     = "\033[1;31m"
    MAGENTA      = "\033[35m"


def hdr(text: str) -> str:
    """Bold cyan section header."""
    return f"{C.BOLD_CYAN}{text}{C.RESET}"


def opt(text: str) -> str:
    """Bright white numbered option."""
    return f"{C.BRIGHT_WHITE}{text}{C.RESET}"


def ok(text: str) -> str:
    """Green confirmation / auto-applied."""
    return f"{C.BOLD_GREEN}{text}{C.RESET}"


def warn(text: str) -> str:
    """Yellow advisory / outdated flag."""
    return f"{C.YELLOW}{text}{C.RESET}"


def err(text: str) -> str:
    """Red error / hard block."""
    return f"{C.BOLD_RED}{text}{C.RESET}"


def dim(text: str) -> str:
    """Dim secondary info."""
    return f"{C.DIM}{text}{C.RESET}"

DB_DEFAULT = Path(__file__).parent / "dino_art.db"
SPECIES_REF_DIR = Path(__file__).parent / "species_reference"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".raw", ".cr2", ".cr3", ".arw", ".nef"}
OUTDATED_THRESHOLD = 2020  # flag species whose last_scientific_update is before this year

# Period → evocative environment phrase (one tight setting, no stacked sub-clauses)
ENVIRONMENTS = {
    # Terrestrial — real-location language, no fantasy adjectives
    "Triassic":            "dry floodplain, cracked mud, scattered ferns, low scrubby conifers",
    "Jurassic":            "dense conifer forest, fallen logs, fern undergrowth, muddy ground, mist between trees",
    "Cretaceous":          "river delta, sandy bank, low flowering shrubs, still water in background",
    "Other":               "open scrubland, rocky ground, scattered vegetation",
    # Marine — real ocean photography language
    "marine_Devonian":     "warm shallow Devonian sea, murky green water, reef rubble on sandy bottom, algae-covered rocks",
    "marine_Permian":      "dark Permian ocean, cold deep water, dim light from far above, empty open water",
    "marine_Triassic":     "shallow coastal water, sandy bottom visible, light ripple patterns on seafloor",
    "marine_Jurassic":     "shallow tropical sea, murky green water, particulate suspended in water column",
    "marine_Cretaceous":   "open ocean, grey-green water, light filtering from surface above, sediment haze",
    "marine_Miocene":      "warm coastal ocean, blue-green water, sunlight penetrating from above, kelp strands drifting",
    "marine_Other":        "open ocean, deep water, dim ambient light from above",
    # Aerial — real sky photography language
    "aerial_Jurassic":     "overcast sky, distant tree line below, hazy horizon",
    "aerial_Cretaceous":   "open sky, flat land far below, clouds at altitude, distant river visible",
    "aerial_Triassic":     "pale sky, barren land below, heat distortion at low altitude",
    "aerial_Other":        "open sky, distant ground, atmospheric haze at horizon",
}

CATEGORIES = ["lighting", "camera", "mood", "condition"]

# ---------------------------------------------------------------------------
# Lighting → Weather compatibility
# Each lighting has a sky state; each weather lists which sky states it fits.
# "any" means always shown regardless of lighting.
# ---------------------------------------------------------------------------

LIGHTING_SKY = {
    # clear sky — direct sun visible
    "golden_hour":         "clear",
    "harsh_midday":        "clear",
    "blue_hour":           "clear",
    "backlit_haze":        "clear",
    "dawn_first_light":    "clear",
    "sunset_warm":         "clear",
    "high_noon_flat":      "clear",
    "moonlit":             "clear",
    # overcast — no direct sun
    "overcast":            "overcast",
    "broken_cloud":        "mixed",
    "pre_storm":           "overcast",
    "dappled_canopy":      "mixed",
    "fog_diffuse":         "overcast",
    "twilight_fade":       "overcast",
    "dust_glow":           "mixed",
    "forest_floor_shade":  "overcast",
    # storm
    "stormy":              "storm",
    "dramatic_rim":        "mixed",
    # marine
    "underwater_caustics": "clear",
    "deep_water_fade":     "overcast",
    "surface_dapple":      "clear",
    "bioluminescent":      "overcast",
    "noon_column":         "clear",
    "reef_scatter":        "clear",
    "murk_glow":           "overcast",
    "dawn_surface":        "clear",
    "moonlit_surface":     "clear",
    # aerial
    "open_sky_flat":       "overcast",
    "cloud_shadow":        "mixed",
    "reflected_ground":    "clear",
    "halo_backlit":        "clear",
    "storm_flash":         "storm",
    "thermal_shimmer":     "clear",
    "fog_top_layer":       "overcast",
    "rain_scatter":        "storm",
}

WEATHER_SKY_COMPAT = {
    # terrestrial
    "clear_pristine":       ("clear", "mixed"),
    "heat_haze":            ("clear",),
    "ground_mist":          ("clear", "overcast", "mixed"),
    "storm_approaching":    ("overcast", "storm", "mixed"),
    "monsoon_heavy":        ("storm", "overcast"),
    "post_storm_clearing":  ("overcast", "mixed", "storm"),
    "light_snowfall":       ("overcast", "mixed"),
    "arctic_freeze":        ("clear", "overcast", "mixed"),
    "volcanic_ash_fall":    ("any",),
    "wildfire_smoke":       ("any",),
    "dust_storm":           ("clear", "mixed"),
    "humid_haze":           ("clear", "overcast", "mixed"),
    "cold_fog":             ("overcast", "mixed"),
    "drizzle_steady":       ("overcast", "mixed"),
    "wind_gusts_dry":       ("clear", "mixed"),
    "frost_dawn":           ("clear",),
    "rain_clearing":        ("overcast", "mixed"),
    "hot_still_air":        ("clear",),
    "late_afternoon_cool":  ("clear", "mixed"),
    "overcast_flat":        ("overcast",),
    # marine
    "calm_surface":         ("clear", "mixed"),
    "choppy_swell":         ("overcast", "storm", "mixed"),
    "ocean_storm":          ("storm",),
    "murky_green":          ("overcast", "mixed"),
    "clear_tropical":       ("clear",),
    "deep_current_cold":    ("any",),
    "surface_chop":         ("mixed", "overcast"),
    "tidal_surge":          ("storm", "mixed"),
    "plankton_bloom":       ("any",),
    "thermocline_shift":    ("any",),
    "underwater_haze":      ("overcast", "mixed"),
    "kelp_drift":           ("clear", "mixed"),
    "warm_shallows":        ("clear",),
    "storm_surge_murk":     ("storm",),
    "dawn_glass":           ("clear",),
    "twilight_surface":     ("overcast", "mixed"),
    "moonlit_calm":         ("clear",),
    "rain_on_surface":      ("storm", "overcast"),
    "volcanic_vent_warm":   ("any",),
    "reef_current":         ("clear", "mixed"),
    # aerial
    "high_altitude_clear":  ("clear",),
    "cloud_layer_below":    ("clear", "mixed"),
    "thermal_column":       ("clear", "mixed"),
    "coastal_wind":         ("clear", "overcast", "mixed"),
    "headwind_strong":      ("mixed", "overcast"),
    "tailwind_fast":        ("clear", "mixed"),
    "rain_curtain":         ("storm", "overcast"),
    "ice_crystal_air":      ("clear",),
    "updraft_turbulence":   ("mixed", "overcast"),
    "haze_layer":           ("overcast", "mixed"),
    "storm_anvil_top":      ("storm",),
    "sunset_altitude":      ("clear",),
    "dawn_horizon":         ("clear",),
    "crosswind_shear":      ("mixed", "overcast"),
    "sea_spray_altitude":   ("mixed", "overcast"),
    "dust_plume_below":     ("clear", "mixed"),
    "calm_dead_air":        ("clear", "overcast"),
    "mountain_wave":        ("mixed",),
    "fog_bank_below":       ("overcast", "mixed"),
    "clear_cold_high":      ("clear",),
}

# ---------------------------------------------------------------------------
# Marine context-reactive branching — suggestions + invalid combo blocking
# Applies only when habitat == "marine". Terrestrial/aerial flows unchanged.
# ---------------------------------------------------------------------------

MARINE_LIGHTING_BY_SPECIES = {
    "Mosasaurus":    ["surface_dapple",     "underwater_caustics", "murk_glow",          "storm_dark_above",  "noon_column"],
    "Elasmosaurus":  ["underwater_caustics", "surface_dapple",     "reef_scatter",        "noon_column",       "dawn_surface"],
    "Ichthyosaurus": ["reef_scatter",        "noon_column",        "underwater_caustics", "surface_dapple",    "dawn_surface"],
    "Liopleurodon":  ["murk_glow",           "deep_water_fade",    "underwater_caustics", "bioluminescent",    "sun_shaft_angle"],
    "Kronosaurus":   ["underwater_caustics", "murk_glow",          "surface_dapple",      "storm_dark_above",  "noon_column"],
    "Spinosaurus":   ["surface_dapple",      "dawn_surface",       "overcast",            "broken_cloud",      "golden_hour"],
    # Sharks
    "Megalodon":     ["noon_column",         "surface_dapple",     "sun_shaft_angle",    "underwater_caustics","storm_dark_above"],
    "Cretoxyrhina":  ["underwater_caustics", "noon_column",        "surface_dapple",      "sun_shaft_angle",   "reef_scatter"],
    "Helicoprion":   ["deep_water_fade",     "murk_glow",          "bioluminescent",      "twilight_depth",    "sun_shaft_angle"],
    # Fish
    "Dunkleosteus":  ["murk_glow",           "deep_water_fade",    "underwater_caustics", "reef_scatter",      "storm_dark_above"],
    "Xiphactinus":   ["noon_column",         "underwater_caustics", "surface_dapple",     "sun_shaft_angle",   "reef_scatter"],
    "Leedsichthys":  ["noon_column",         "sun_shaft_angle",    "surface_dapple",      "underwater_caustics","dawn_surface"],
    # Other
    "Archelon":      ["surface_dapple",      "noon_column",        "dawn_surface",        "underwater_caustics","reef_scatter"],
    "Ammonite":      ["reef_scatter",        "underwater_caustics", "bioluminescent",     "murk_glow",         "noon_column"],
}

MARINE_LIGHTING_BY_MODE = {
    "underwater":    ["deep_water_fade",  "bioluminescent",   "murk_glow",       "sun_shaft_angle",  "underwater_caustics"],
    "surface_break": ["surface_dapple",   "dawn_surface",     "noon_column",     "storm_dark_above", "backlit_haze"],
}

MARINE_MOOD_BY_LIGHTING = {
    "murk_glow":           ["ambush_still",     "deep_patrol",        "quiet_power",       "hunting_focus",      "resting_on_bottom"],
    "deep_water_fade":     ["ambush_still",     "deep_patrol",        "resting_on_bottom", "quiet_power",        "dusk_descent"],
    "bioluminescent":      ["resting_on_bottom","deep_patrol",        "ambush_still",      "quiet_power",        "dawn_ascent"],
    "twilight_depth":      ["dusk_descent",     "deep_patrol",        "ambush_still",      "quiet_power",        "resting_on_bottom"],
    "sun_shaft_angle":     ["ambush_still",     "hunting_focus",      "quiet_power",       "deep_patrol",        "eye_contact"],
    "underwater_caustics": ["playful_roll",     "curiosity_approach", "hunting_focus",     "kelp_weaving",       "cruising_calm"],
    "reef_scatter":        ["playful_roll",     "curiosity_approach", "kelp_weaving",      "hunting_focus",      "cruising_calm"],
    "surface_dapple":      ["cruising_calm",    "surfacing_breath",   "surface_rest",      "hunting_focus",      "eye_contact"],
    "dawn_surface":        ["dawn_ascent",      "surfacing_breath",   "serene",            "cruising_calm",      "eye_contact"],
    "noon_column":         ["hunting_focus",    "cruising_calm",      "eye_contact",       "burst_acceleration", "playful_roll"],
    "storm_dark_above":    ["menacing",         "burst_acceleration", "territorial_patrol","quiet_power",        "ambush_still"],
    "stormy":              ["menacing",         "burst_acceleration", "territorial_patrol","quiet_power",        "ambush_still"],
    "pre_storm":           ["menacing",         "territorial_patrol", "ambush_still",      "quiet_power",        "hunting_focus"],
    "moonlit_surface":     ["serene",           "surface_rest",       "closed_mouth_resting","quiet_power",      "dusk_descent"],
    "dawn_first_light":    ["dawn_ascent",      "serene",             "surfacing_breath",  "quiet_power",        "cruising_calm"],
    "golden_hour":         ["serene",           "eye_contact",        "cruising_calm",     "surface_rest",       "post_feed_drift"],
    "overcast":            ["quiet_power",      "cruising_calm",      "deep_patrol",       "hunting_focus",      "ambush_still"],
    "broken_cloud":        ["cruising_calm",    "quiet_power",        "eye_contact",       "hunting_focus",      "surfacing_breath"],
    "backlit_haze":        ["quiet_power",      "serene",             "eye_contact",       "surfacing_breath",   "cruising_calm"],
    "blue_hour":           ["dusk_descent",     "quiet_power",        "serene",            "ambush_still",       "resting_on_bottom"],
}

MARINE_BEHAVIOR_BY_MOOD = {
    "hunting_focus":      ["hunting_dive",      "jaw_snap_strike",    "chase_pursuit",     "feeding_underwater", "breaching_surface"],
    "ambush_still":       ["hovering_still",    "bottom_glide",       "resting_on_seafloor","slow_patrol",       "bubble_trail"],
    "cruising_calm":      ["cruising_open_water","tail_propulsion",   "current_riding",    "flipper_steering",   "surface_breathing"],
    "deep_patrol":        ["deep_sinking",      "bottom_glide",       "slow_patrol",       "hunting_dive",       "tail_propulsion"],
    "surfacing_breath":   ["surface_breathing", "spy_hopping",        "surface_roll",      "breaching_surface",  "bubble_trail"],
    "quiet_power":        ["slow_patrol",       "tail_propulsion",    "cruising_open_water","hovering_still",    "flipper_steering"],
    "burst_acceleration": ["chase_pursuit",     "jaw_snap_strike",    "breaching_surface", "tail_propulsion",    "hunting_dive"],
    "menacing":           ["jaw_snap_strike",   "chase_pursuit",      "hunting_dive",      "slow_patrol",        "spy_hopping"],
    "surface_rest":       ["surface_breathing", "hovering_still",     "debris_rubbing",    "surface_roll",       "flipper_steering"],
    "resting_on_bottom":  ["resting_on_seafloor","hovering_still",    "bottom_glide",      "bubble_trail",       "deep_sinking"],
    "post_feed_drift":    ["surface_breathing", "hovering_still",     "slow_patrol",       "debris_rubbing",     "current_riding"],
    "territorial_patrol": ["slow_patrol",       "tail_propulsion",    "chase_pursuit",     "jaw_snap_strike",    "spy_hopping"],
    "eye_contact":        ["spy_hopping",       "hovering_still",     "slow_patrol",       "surface_breathing",  "surface_roll"],
    "playful_roll":       ["surface_roll",      "debris_rubbing",     "kelp_threading",    "flipper_steering",   "bubble_trail"],
    "kelp_weaving":       ["kelp_threading",    "slow_patrol",        "hovering_still",    "flipper_steering",   "current_riding"],
    "curiosity_approach": ["slow_patrol",       "spy_hopping",        "hovering_still",    "surface_breathing",  "flipper_steering"],
    "dawn_ascent":        ["surface_breathing", "slow_patrol",        "tail_propulsion",   "spy_hopping",        "bubble_trail"],
    "dusk_descent":       ["deep_sinking",      "bottom_glide",       "slow_patrol",       "tail_propulsion",    "bubble_trail"],
    "serene":             ["hovering_still",    "slow_patrol",        "current_riding",    "flipper_steering",   "surface_breathing"],
    "closed_mouth_resting":["hovering_still",  "resting_on_seafloor","surface_breathing", "slow_patrol",        "debris_rubbing"],
}

MARINE_CONDITION_BY_SPECIES = {
    "Mosasaurus":    ["battle_scarred",   "dominant_prime",    "shark_bite_scar",   "weathered_adult",    "barnacle_growth"],
    "Elasmosaurus":  ["algae_on_hide",    "barnacle_growth",   "weathered_adult",   "fishing_line_scar",  "coral_scrape"],
    "Ichthyosaurus": ["pristine_juvenile","dominant_prime",    "algae_on_hide",     "remora_attached",    "salt_crust"],
    "Liopleurodon":  ["battle_scarred",   "dominant_prime",    "shark_bite_scar",   "belly_scars",        "tooth_missing_jaw"],
    "Kronosaurus":   ["battle_scarred",   "shark_bite_scar",   "dominant_prime",    "barnacle_growth",    "belly_scars"],
    "Spinosaurus":   ["blood_on_muzzle",  "algae_on_hide",     "moulting_skin",     "battle_scarred",     "barnacle_growth"],
    # Sharks
    "Megalodon":     ["battle_scarred",   "dominant_prime",    "shark_bite_scar",   "belly_scars",        "weathered_adult"],
    "Cretoxyrhina":  ["dominant_prime",   "battle_scarred",    "shark_bite_scar",   "pristine_juvenile",  "salt_crust"],
    "Helicoprion":   ["weathered_adult",  "algae_on_hide",     "dominant_prime",    "salt_crust",         "coral_scrape"],
    # Fish
    "Dunkleosteus":  ["battle_scarred",   "dominant_prime",    "algae_on_hide",     "coral_scrape",       "weathered_adult"],
    "Xiphactinus":   ["dominant_prime",   "battle_scarred",    "pristine_juvenile", "shark_bite_scar",    "salt_crust"],
    "Leedsichthys":  ["barnacle_growth",  "algae_on_hide",     "remora_attached",   "weathered_adult",    "coral_scrape"],
    # Other
    "Archelon":      ["barnacle_growth",  "algae_on_hide",     "weathered_adult",   "coral_scrape",       "shark_bite_scar"],
    "Ammonite":      ["algae_on_hide",    "coral_scrape",      "pristine_juvenile", "barnacle_growth",    "weathered_adult"],
}

MARINE_CAMERA_BY_MODE = {
    "portrait":       ["closeup_portrait","tight_head",        "jaw_level",         "murk_emerge",        "detail_abstract"],
    "canvas":         ["full_body_profile","swim_alongside",   "distant_surface",   "rear_three_quarter", "below_looking_up"],
    "environmental":  ["distant_surface", "above_looking_down","swim_alongside",    "underwater_wide",    "split_waterline"],
    "surface_break":  ["split_waterline", "breach_freeze",     "surface_skim",      "jaw_level",          "below_looking_up"],
    "underwater":     ["underwater_wide", "below_looking_up",  "swim_alongside",    "deep_telephoto",     "belly_underneath"],
    "action_freeze":  ["breach_freeze",   "jaw_level",         "chase_behind",      "deep_telephoto",     "murk_emerge"],
    "tracking_side":  ["swim_alongside",  "deep_telephoto",    "chase_behind",      "full_body_profile",  "murk_emerge"],
    "extreme_closeup":["detail_abstract", "jaw_level",         "belly_underneath",  "reef_foreground",    "closeup_portrait"],
    "aerial_overhead":["above_looking_down","distant_surface", "swim_alongside",    "split_waterline",    "full_body_profile"],
    "dusk_long_exp":  ["distant_surface", "split_waterline",   "surface_skim",      "swim_alongside",     "above_looking_down"],
}

MARINE_WEATHER_BY_MOOD = {
    "menacing":           ["ocean_storm",      "tidal_surge",       "choppy_swell",      "storm_surge_murk",   "rain_on_surface"],
    "burst_acceleration": ["ocean_storm",      "choppy_swell",      "tidal_surge",       "surface_chop",       "rain_on_surface"],
    "territorial_patrol": ["choppy_swell",     "surface_chop",      "ocean_storm",       "murky_green",        "tidal_surge"],
    "serene":             ["calm_surface",     "dawn_glass",        "moonlit_calm",      "clear_tropical",     "warm_shallows"],
    "surface_rest":       ["calm_surface",     "moonlit_calm",      "dawn_glass",        "clear_tropical",     "warm_shallows"],
    "closed_mouth_resting":["calm_surface",   "moonlit_calm",      "dawn_glass",        "warm_shallows",      "twilight_surface"],
    "deep_patrol":        ["deep_current_cold","thermocline_shift", "underwater_haze",   "plankton_bloom",     "murky_green"],
    "resting_on_bottom":  ["deep_current_cold","thermocline_shift", "volcanic_vent_warm","underwater_haze",    "plankton_bloom"],
    "ambush_still":       ["murky_green",      "underwater_haze",   "deep_current_cold", "thermocline_shift",  "plankton_bloom"],
    "hunting_focus":      ["clear_tropical",   "reef_current",      "calm_surface",      "murky_green",        "choppy_swell"],
    "playful_roll":       ["warm_shallows",    "kelp_drift",        "reef_current",      "clear_tropical",     "calm_surface"],
    "kelp_weaving":       ["kelp_drift",       "reef_current",      "warm_shallows",     "clear_tropical",     "calm_surface"],
}

# (cat_a, name_a, cat_b, name_b, reason) — symmetric: blocking works in both directions
MARINE_INVALID_COMBOS = [
    # Surface behaviors ↔ deep moods
    ("behavior", "breaching_surface",    "mood",     "resting_on_bottom", "breaching to surface — not resting on bottom"),
    ("behavior", "breaching_surface",    "mood",     "deep_patrol",       "breaching to surface — not a deep patrol"),
    ("behavior", "spy_hopping",          "mood",     "resting_on_bottom", "spy hop is surface — not resting on bottom"),
    ("behavior", "spy_hopping",          "mood",     "deep_patrol",       "spy hop is surface — not a deep patrol"),
    # Deep behaviors ↔ surface moods
    ("behavior", "deep_sinking",         "mood",     "surfacing_breath",  "sinking deep — contradicts surfacing for breath"),
    ("behavior", "resting_on_seafloor",  "mood",     "surfacing_breath",  "on seafloor — contradicts surfacing for breath"),
    ("behavior", "resting_on_seafloor",  "mood",     "burst_acceleration","resting on seafloor — not burst acceleration"),
    # Still behaviors ↔ active moods
    ("behavior", "hovering_still",       "mood",     "burst_acceleration","hovering still — contradicts burst acceleration"),
    ("behavior", "jaw_snap_strike",      "mood",     "post_feed_drift",   "jaw strike — contradicts post-feed passive drift"),
    # Surface behaviors ↔ deep lighting
    ("behavior", "breaching_surface",    "lighting", "deep_water_fade",   "breaching surface — deep fade light contradicts"),
    ("behavior", "breaching_surface",    "lighting", "bioluminescent",    "breaching surface — bioluminescent is deep"),
    ("behavior", "spy_hopping",          "lighting", "deep_water_fade",   "spy hop at surface — deep fade light contradicts"),
    ("behavior", "spy_hopping",          "lighting", "bioluminescent",    "spy hop at surface — bioluminescent is deep"),
    # Seafloor behaviors ↔ surface lighting
    ("behavior", "resting_on_seafloor",  "lighting", "surface_dapple",   "on seafloor — surface dapple light contradicts"),
    ("behavior", "deep_sinking",         "lighting", "surface_dapple",   "sinking deep — surface dapple light contradicts"),
]

# Mode-specific blocks — output_mode → category → {name: reason}
MARINE_MODE_COMBO_BLOCKS = {
    "underwater": {
        "behavior": {
            "breaching_surface": "fully submerged mode — can't breach surface",
            "spy_hopping":       "fully submerged mode — can't spy hop",
            "surface_breathing": "fully submerged mode — can't breathe at surface",
            "surface_roll":      "fully submerged mode — can't roll at surface",
        },
        "mood": {
            "surfacing_breath":  "fully submerged mode — can't surface for breath",
        },
    },
    "surface_break": {
        "behavior": {
            "resting_on_seafloor": "surface break mode — can't rest on seafloor",
            "deep_sinking":        "surface break mode — can't be deep sinking",
            "bottom_glide":        "surface break mode — can't be gliding at bottom",
        },
        "mood": {
            "resting_on_bottom": "surface break mode — can't be resting on bottom",
            "deep_patrol":       "surface break mode — can't be on deep patrol",
        },
    },
}


def get_marine_suggestions(category: str, context: dict) -> list:
    """Return up to 5 suggested parameter names for the given category and context.
    Only applies when habitat == 'marine'. Returns [] otherwise.
    """
    if context.get("habitat") != "marine":
        return []

    species_name = context.get("species_name", "")
    diet         = context.get("diet", "")
    output_mode  = context.get("output_mode", "")
    lighting     = context.get("lighting")
    mood         = context.get("mood")
    behavior     = context.get("behavior")

    if category == "lighting":
        if output_mode in MARINE_LIGHTING_BY_MODE:
            return MARINE_LIGHTING_BY_MODE[output_mode]
        return MARINE_LIGHTING_BY_SPECIES.get(species_name, [])

    if category == "mood":
        base = list(MARINE_MOOD_BY_LIGHTING.get(lighting, []))
        if diet == "Carnivore" and base:
            priority = [m for m in ["hunting_focus", "menacing", "ambush_still", "territorial_patrol", "burst_acceleration"] if m in base]
            rest = [m for m in base if m not in priority]
            base = priority + rest
        return base[:5]

    if category == "behavior":
        return MARINE_BEHAVIOR_BY_MOOD.get(mood, [])

    if category == "condition":
        base = list(MARINE_CONDITION_BY_SPECIES.get(species_name, []))
        if mood in ("hunting_focus", "menacing") or behavior in ("jaw_snap_strike", "chase_pursuit"):
            priority = ["blood_on_muzzle", "battle_scarred", "tooth_missing_jaw"]
            base = priority + [c for c in base if c not in priority]
        elif mood == "post_feed_drift":
            priority = ["blood_on_muzzle", "belly_scars", "weathered_adult"]
            base = priority + [c for c in base if c not in priority]
        return base[:5]

    if category == "camera":
        base = list(MARINE_CAMERA_BY_MODE.get(output_mode, []))
        if behavior in ("breaching_surface", "spy_hopping"):
            base = ["breach_freeze", "split_waterline", "below_looking_up", "surface_skim", "jaw_level"]
        elif behavior in ("jaw_snap_strike", "chase_pursuit"):
            base = ["jaw_level", "murk_emerge", "chase_behind", "deep_telephoto", "closeup_portrait"]
        elif behavior in ("deep_sinking", "resting_on_seafloor", "bottom_glide"):
            base = ["below_looking_up", "underwater_wide", "deep_telephoto", "belly_underneath", "swim_alongside"]
        return base[:5]

    if category == "weather":
        return MARINE_WEATHER_BY_MOOD.get(mood, [])[:5]

    return []


def get_marine_blocked(category: str, context: dict) -> dict:
    """Return {name: reason} for marine parameters that are invalid given current context.
    Returns {} for non-marine habitats.
    """
    if context.get("habitat") != "marine":
        return {}

    blocked = {}
    output_mode = context.get("output_mode", "")

    for cat_blk, entries in MARINE_MODE_COMBO_BLOCKS.get(output_mode, {}).items():
        if cat_blk == category:
            blocked.update(entries)

    for cat_a, name_a, cat_b, name_b, reason in MARINE_INVALID_COMBOS:
        if cat_b == category and context.get(cat_a) == name_a:
            blocked.setdefault(name_b, reason)
        if cat_a == category and context.get(cat_b) == name_b:
            blocked.setdefault(name_a, reason)

    return blocked


# ---------------------------------------------------------------------------
# Terrestrial context-reactive branching
# ---------------------------------------------------------------------------

TERRESTRIAL_LIGHTING_BY_SPECIES = {
    "Tyrannosaurus rex": ["golden_hour",      "harsh_midday",      "pre_storm",          "dramatic_rim",      "dust_glow"],
    "Velociraptor":      ["dappled_canopy",   "forest_floor_shade","shaft_light",        "dawn_first_light",  "broken_cloud"],
    "Triceratops":       ["golden_hour",      "overcast",          "broken_cloud",       "backlit_haze",      "harsh_midday"],
    "Stegosaurus":       ["golden_hour",      "overcast",          "broken_cloud",       "dappled_canopy",    "dawn_first_light"],
    "Brachiosaurus":     ["golden_hour",      "backlit_haze",      "overcast",           "harsh_midday",      "dust_glow"],
    "Ankylosaurus":      ["harsh_midday",     "golden_hour",       "overcast",           "broken_cloud",      "dust_glow"],
    "Parasaurolophus":   ["golden_hour",      "overcast",          "dawn_first_light",   "broken_cloud",      "backlit_haze"],
    "Dilophosaurus":     ["dappled_canopy",   "dawn_first_light",  "shaft_light",        "golden_hour",       "backlit_haze"],
}

TERRESTRIAL_LIGHTING_BY_MODE = {
    "ground_level":      ["dramatic_rim",     "harsh_midday",      "dust_glow",          "golden_hour",       "dawn_first_light"],
    "action_freeze":     ["harsh_midday",     "dramatic_rim",      "golden_hour",        "dust_glow",         "broken_cloud"],
    "dusk_long_exp":     ["twilight_fade",    "blue_hour",         "sunset_warm",        "golden_hour",       "moonlit"],
}

TERRESTRIAL_MOOD_BY_LIGHTING = {
    "golden_hour":       ["heat_rest",        "serene",            "grooming",           "herd_grazing",      "dusk_settling"],
    "harsh_midday":      ["heat_rest",        "feeding_focus",     "alert_scan",         "quiet_power",       "territorial_hold"],
    "dappled_canopy":    ["quiet_power",      "scent_tracking",    "feeding_focus",      "alert_scan",        "serene"],
    "dawn_first_light":  ["dawn_waking",      "alert_scan",        "serene",             "quiet_power",       "herd_grazing"],
    "overcast":          ["quiet_power",      "alert_scan",        "feeding_focus",      "herd_grazing",      "mid_stride"],
    "pre_storm":         ["menacing",         "territorial_hold",  "alert_scan",         "quiet_power",       "startled_freeze"],
    "stormy":            ["menacing",         "territorial_hold",  "alert_scan",         "startled_freeze",   "quiet_power"],
    "dramatic_rim":      ["menacing",         "territorial_hold",  "quiet_power",        "post_kill_pause",   "alert_scan"],
    "sunset_warm":       ["dusk_settling",    "heat_rest",         "serene",             "grooming",          "herd_grazing"],
    "dust_glow":         ["heat_rest",        "feeding_focus",     "quiet_power",        "territorial_hold",  "menacing"],
    "forest_floor_shade":["quiet_power",      "scent_tracking",    "feeding_focus",      "serene",            "alert_scan"],
    "shaft_light":       ["quiet_power",      "alert_scan",        "scent_tracking",     "menacing",          "serene"],
    "moonlit":           ["scent_tracking",   "alert_scan",        "quiet_power",        "menacing",          "startled_freeze"],
    "fog_diffuse":       ["quiet_power",      "scent_tracking",    "alert_scan",         "serene",            "menacing"],
    "backlit_haze":      ["quiet_power",      "serene",            "eye_contact",        "feeding_focus",     "alert_scan"],
    "blue_hour":         ["dusk_settling",    "quiet_power",       "serene",             "scent_tracking",    "grooming"],
    "broken_cloud":      ["feeding_focus",    "mid_stride",        "alert_scan",         "herd_grazing",      "quiet_power"],
    "twilight_fade":     ["dusk_settling",    "serene",            "quiet_power",        "heat_rest",         "grooming"],
    "reflected_water":   ["drinking",         "wading_shallow",    "serene",             "heat_rest",         "quiet_power"],
    "high_noon_flat":    ["heat_rest",        "feeding_focus",     "quiet_power",        "alert_scan",        "drinking"],
}

TERRESTRIAL_BEHAVIOR_BY_MOOD = {
    "heat_rest":             ["basking_flat",      "resting_alert",     "post_rain_stillness","jaw_clean_on_ground","standing_still"],
    "serene":                ["resting_alert",     "standing_still",    "post_rain_stillness","basking_flat",      "feeding"],
    "closed_mouth_resting":  ["basking_flat",      "resting_alert",     "standing_still",    "post_rain_stillness","jaw_clean_on_ground"],
    "eye_contact":           ["standing_still",    "scanning_territory","emerging_from_cover","threat_display",    "resting_alert"],
    "menacing":              ["charging_full",     "threat_display",    "tail_swipe",        "head_butt_spar",    "scanning_territory"],
    "alert_scan":            ["scanning_territory","freeze_detect",     "standing_still",    "resting_alert",     "emerging_from_cover"],
    "mid_stride":            ["mid_stride",        "charging_full",     "tail_swipe",        "scanning_territory","emerging_from_cover"],
    "drinking":              ["drinking_at_water", "shaking_off_water", "standing_still",    "mud_wallow",        "post_rain_stillness"],
    "feeding_focus":         ["feeding",           "jaw_clean_on_ground","carcass_standing", "standing_still",    "scanning_territory"],
    "territorial_hold":      ["threat_display",    "scanning_territory","tail_swipe",        "head_butt_spar",    "standing_still"],
    "post_kill_pause":       ["carcass_standing",  "standing_still",    "jaw_clean_on_ground","scanning_territory","resting_alert"],
    "scent_tracking":        ["scanning_territory","emerging_from_cover","freeze_detect",    "standing_still",    "mid_stride"],
    "dust_bath":             ["dust_rolling",      "shaking_off_water", "mud_wallow",        "basking_flat",      "resting_alert"],
    "wading_shallow":        ["drinking_at_water", "mud_wallow",        "shaking_off_water", "standing_still",    "post_rain_stillness"],
    "startled_freeze":       ["freeze_detect",     "standing_still",    "scanning_territory","resting_alert",     "emerging_from_cover"],
    "grooming":              ["jaw_clean_on_ground","shaking_off_water","dust_rolling",      "resting_alert",     "mud_wallow"],
    "herd_grazing":          ["feeding",           "mid_stride",        "standing_still",    "resting_alert",     "drinking_at_water"],
    "dawn_waking":           ["emerging_from_cover","standing_still",   "post_rain_stillness","shaking_off_water","scanning_territory"],
    "quiet_power":           ["standing_still",    "scanning_territory","mid_stride",        "resting_alert",     "emerging_from_cover"],
    "dusk_settling":         ["resting_alert",     "standing_still",    "basking_flat",      "post_rain_stillness","jaw_clean_on_ground"],
}

TERRESTRIAL_CONDITION_BY_SPECIES = {
    "Tyrannosaurus rex": ["dominant_prime",   "battle_scarred",    "blood_on_muzzle",    "jaw_asymmetry",     "fly_attention"],
    "Velociraptor":      ["pristine_juvenile","dominant_prime",    "battle_scarred",     "moulting_skin",     "parasite_ticks"],
    "Triceratops":       ["battle_scarred",   "dominant_prime",    "broken_horn_tip",    "weathered_adult",   "mud_caked"],
    "Stegosaurus":       ["weathered_adult",  "dominant_prime",    "mud_caked",          "parasite_ticks",    "moulting_skin"],
    "Brachiosaurus":     ["dominant_prime",   "weathered_adult",   "elder_specimen",     "parasite_ticks",    "mud_caked"],
    "Ankylosaurus":      ["dominant_prime",   "battle_scarred",    "mud_caked",          "weathered_adult",   "parasite_ticks"],
    "Parasaurolophus":   ["pristine_juvenile","dominant_prime",    "moulting_skin",      "parasite_ticks",    "wet_after_rain"],
    "Dilophosaurus":     ["dominant_prime",   "battle_scarred",    "blood_on_muzzle",    "moulting_skin",     "pristine_juvenile"],
}

TERRESTRIAL_CAMERA_BY_MODE = {
    "portrait":         ["closeup_portrait", "tight_head",        "telephoto_compress", "hidden_blind",      "detail_abstract"],
    "canvas":           ["full_body_profile","rear_three_quarter","epic_wide",          "trail_camera",      "waterhole_edge"],
    "environmental":    ["epic_wide",        "aerial_above",      "trail_camera",       "telephoto_compress","waterhole_edge"],
    "extreme_closeup":  ["detail_abstract",  "tight_head",        "dust_level",         "closeup_portrait",  "telephoto_compress"],
    "action_freeze":    ["dynamic_low",      "tracking_pan",      "walking_toward",     "ground_level_up",   "dust_level"],
    "tracking_side":    ["tracking_pan",     "telephoto_compress","full_body_profile",  "trail_camera",      "dust_level"],
    "ground_level":     ["ground_level_up",  "dynamic_low",       "dust_level",         "walking_toward",    "trail_camera"],
    "aerial_overhead":  ["aerial_above",     "canopy_gap_down",   "epic_wide",          "telephoto_compress","silhouette_ridge"],
    "dusk_long_exp":    ["silhouette_ridge", "waterhole_edge",    "telephoto_compress", "epic_wide",         "trail_camera"],
}

TERRESTRIAL_WEATHER_BY_MOOD = {
    "heat_rest":         ["heat_haze",        "hot_still_air",     "humid_haze",         "clear_pristine",    "late_afternoon_cool"],
    "serene":            ["clear_pristine",   "late_afternoon_cool","ground_mist",        "overcast_flat",     "post_storm_clearing"],
    "menacing":          ["storm_approaching","wind_gusts_dry",    "volcanic_ash_fall",  "wildfire_smoke",    "dust_storm"],
    "territorial_hold":  ["wind_gusts_dry",   "storm_approaching", "dust_storm",         "clear_pristine",    "heat_haze"],
    "post_kill_pause":   ["hot_still_air",    "humid_haze",        "clear_pristine",     "heat_haze",         "wind_gusts_dry"],
    "scent_tracking":    ["ground_mist",      "cold_fog",          "humid_haze",         "rain_clearing",     "post_storm_clearing"],
    "alert_scan":        ["wind_gusts_dry",   "ground_mist",       "clear_pristine",     "storm_approaching", "cold_fog"],
    "feeding_focus":     ["clear_pristine",   "hot_still_air",     "humid_haze",         "overcast_flat",     "rain_clearing"],
    "herd_grazing":      ["clear_pristine",   "overcast_flat",     "ground_mist",        "humid_haze",        "rain_clearing"],
    "drinking":          ["ground_mist",      "clear_pristine",    "rain_clearing",      "post_storm_clearing","humid_haze"],
    "dawn_waking":       ["ground_mist",      "frost_dawn",        "cold_fog",           "clear_pristine",    "humid_haze"],
    "dusk_settling":     ["late_afternoon_cool","clear_pristine",  "ground_mist",        "humid_haze",        "overcast_flat"],
    "dust_bath":         ["heat_haze",        "hot_still_air",     "dust_storm",         "wind_gusts_dry",    "clear_pristine"],
    "wading_shallow":    ["ground_mist",      "post_storm_clearing","rain_clearing",     "humid_haze",        "drizzle_steady"],
    "quiet_power":       ["clear_pristine",   "ground_mist",       "overcast_flat",      "wind_gusts_dry",    "humid_haze"],
    "grooming":          ["clear_pristine",   "late_afternoon_cool","hot_still_air",     "overcast_flat",     "post_storm_clearing"],
    "startled_freeze":   ["wind_gusts_dry",   "storm_approaching", "ground_mist",        "cold_fog",          "clear_pristine"],
    "mid_stride":        ["clear_pristine",   "overcast_flat",     "ground_mist",        "wind_gusts_dry",    "post_storm_clearing"],
    "eye_contact":       ["clear_pristine",   "overcast_flat",     "ground_mist",        "backlit_haze",      "cold_fog"],
    "closed_mouth_resting":["hot_still_air",  "clear_pristine",   "late_afternoon_cool","overcast_flat",     "humid_haze"],
}

TERRESTRIAL_INVALID_COMBOS = [
    # Active combat/charge ↔ passive rest moods
    ("behavior", "charging_full",    "mood", "heat_rest",            "charging — contradicts passive heat rest"),
    ("behavior", "charging_full",    "mood", "serene",               "charging — contradicts serene resting mood"),
    ("behavior", "charging_full",    "mood", "closed_mouth_resting", "charging — contradicts closed-mouth resting"),
    ("behavior", "charging_full",    "mood", "dusk_settling",        "charging — contradicts dusk settling"),
    ("behavior", "charging_full",    "mood", "grooming",             "charging — contradicts grooming"),
    ("behavior", "head_butt_spar",   "mood", "heat_rest",            "active sparring — contradicts heat rest"),
    ("behavior", "head_butt_spar",   "mood", "serene",               "active sparring — contradicts serene mood"),
    ("behavior", "tail_swipe",       "mood", "heat_rest",            "active tail swipe — contradicts heat rest"),
    ("behavior", "tail_swipe",       "mood", "serene",               "active tail swipe — contradicts serene mood"),
    # Basking ↔ incompatible states (ectotherm solar thermoregulation)
    ("behavior", "basking_flat",     "mood",    "menacing",          "basking flat — contradicts menacing mood"),
    ("behavior", "basking_flat",     "mood",    "mid_stride",        "basking flat — contradicts mid-stride"),
    ("behavior", "basking_flat",     "mood",    "territorial_hold",  "basking flat — too passive for territorial hold"),
    ("behavior", "basking_flat",     "lighting","moonlit",           "basking is solar thermoregulation — moonlit (night) contradicts"),
    ("behavior", "basking_flat",     "lighting","twilight_fade",     "basking is solar thermoregulation — twilight too dim"),
    ("behavior", "basking_flat",     "lighting","forest_floor_shade","basking needs direct light — deep shade contradicts"),
    ("behavior", "basking_flat",     "weather", "monsoon_heavy",     "basking flat — heavy rain contradicts"),
    ("behavior", "basking_flat",     "weather", "storm_approaching", "basking flat — approaching storm contradicts"),
    # Carcass context ↔ incompatible moods
    ("behavior", "carcass_standing", "mood",    "heat_rest",         "standing over carcass — not passive heat resting"),
    ("behavior", "carcass_standing", "mood",    "serene",            "standing over carcass — not serene"),
    ("behavior", "carcass_standing", "mood",    "herd_grazing",      "standing over carcass — not herd grazing"),
    ("behavior", "carcass_standing", "mood",    "dust_bath",         "standing over carcass — not dust bathing"),
    ("behavior", "carcass_standing", "mood",    "grooming",          "standing over carcass — not grooming"),
    # Dust rolling ↔ incompatible context
    ("behavior", "dust_rolling",     "mood",    "menacing",          "dust rolling is self-care — not menacing"),
    ("behavior", "dust_rolling",     "mood",    "scent_tracking",    "rolling in dust — destroys scent trail"),
    ("behavior", "dust_rolling",     "weather", "monsoon_heavy",     "dust rolling — heavy rain contradicts"),
    ("behavior", "dust_rolling",     "weather", "drizzle_steady",    "dust rolling — wet ground contradicts"),
    # Water drinking ↔ dry extreme weather
    ("behavior", "drinking_at_water","weather", "dust_storm",        "drinking at water — dust storm contradicts"),
    ("behavior", "drinking_at_water","weather", "wildfire_smoke",    "drinking at water — wildfire smoke is compatible, but water not open in fire"),
]

TERRESTRIAL_MODE_COMBO_BLOCKS = {
    "action_freeze": {
        "behavior": {
            "basking_flat":        "action freeze mode — basking is static, no motion to freeze",
            "resting_alert":       "action freeze mode — resting too passive for action freeze",
            "post_rain_stillness": "action freeze mode — post-rain stillness is static",
            "jaw_clean_on_ground": "action freeze mode — jaw cleaning is static",
        },
    },
}


def get_terrestrial_suggestions(category: str, context: dict) -> list:
    if context.get("habitat") != "terrestrial":
        return []

    species_name = context.get("species_name", "")
    diet         = context.get("diet", "")
    output_mode  = context.get("output_mode", "")
    lighting     = context.get("lighting")
    mood         = context.get("mood")
    behavior     = context.get("behavior")

    if category == "lighting":
        if output_mode in TERRESTRIAL_LIGHTING_BY_MODE:
            return TERRESTRIAL_LIGHTING_BY_MODE[output_mode]
        return TERRESTRIAL_LIGHTING_BY_SPECIES.get(species_name, [])

    if category == "mood":
        base = list(TERRESTRIAL_MOOD_BY_LIGHTING.get(lighting, []))
        if diet == "Carnivore" and base:
            priority = [m for m in ["menacing", "post_kill_pause", "feeding_focus", "territorial_hold", "quiet_power"] if m in base]
            rest = [m for m in base if m not in priority]
            base = priority + rest
        return base[:5]

    if category == "behavior":
        return TERRESTRIAL_BEHAVIOR_BY_MOOD.get(mood, [])

    if category == "condition":
        base = list(TERRESTRIAL_CONDITION_BY_SPECIES.get(species_name, []))
        if mood in ("post_kill_pause", "feeding_focus") or behavior in ("carcass_standing", "jaw_clean_on_ground"):
            priority = ["blood_on_muzzle", "fly_attention", "jaw_asymmetry"]
            base = priority + [c for c in base if c not in priority]
        elif mood in ("menacing", "territorial_hold") or behavior in ("charging_full", "threat_display"):
            priority = ["battle_scarred", "embedded_tooth", "neck_scar_collar"]
            base = priority + [c for c in base if c not in priority]
        elif mood == "heat_rest" or behavior == "basking_flat":
            priority = ["parasite_ticks", "fly_attention", "moulting_skin"]
            base = priority + [c for c in base if c not in priority]
        return base[:5]

    if category == "camera":
        base = list(TERRESTRIAL_CAMERA_BY_MODE.get(output_mode, []))
        if behavior in ("charging_full", "mid_stride", "tail_swipe"):
            base = ["dynamic_low", "tracking_pan", "walking_toward", "ground_level_up", "dust_level"]
        elif behavior in ("drinking_at_water", "mud_wallow"):
            base = ["waterhole_edge", "hidden_blind", "telephoto_compress", "trail_camera", "closeup_portrait"]
        elif behavior in ("basking_flat", "resting_alert", "post_rain_stillness"):
            base = ["hidden_blind", "trail_camera", "telephoto_compress", "canopy_gap_down", "full_body_profile"]
        elif behavior in ("threat_display", "head_butt_spar"):
            base = ["walking_toward", "dynamic_low", "ground_level_up", "telephoto_compress", "detail_abstract"]
        return base[:5]

    if category == "weather":
        return TERRESTRIAL_WEATHER_BY_MOOD.get(mood, [])[:5]

    return []


def get_terrestrial_blocked(category: str, context: dict) -> dict:
    if context.get("habitat") != "terrestrial":
        return {}

    blocked = {}
    output_mode = context.get("output_mode", "")

    for cat_blk, entries in TERRESTRIAL_MODE_COMBO_BLOCKS.get(output_mode, {}).items():
        if cat_blk == category:
            blocked.update(entries)

    for cat_a, name_a, cat_b, name_b, reason in TERRESTRIAL_INVALID_COMBOS:
        if cat_b == category and context.get(cat_a) == name_a:
            blocked.setdefault(name_b, reason)
        if cat_a == category and context.get(cat_b) == name_b:
            blocked.setdefault(name_a, reason)

    return blocked


# ---------------------------------------------------------------------------
# Aerial context-reactive branching
# ---------------------------------------------------------------------------

AERIAL_LIGHTING_BY_SPECIES = {
    "Pteranodon":     ["golden_hour",     "backlit_haze",     "thermal_shimmer",   "halo_backlit",      "open_sky_flat"],
    "Quetzalcoatlus": ["golden_hour",     "backlit_haze",     "thermal_shimmer",   "dramatic_rim",      "storm_flash"],
    "Rhamphorhynchus":["golden_hour",     "dawn_first_light", "backlit_haze",      "halo_backlit",      "open_sky_flat"],
    "Dimorphodon":    ["dawn_first_light","golden_hour",      "open_sky_flat",     "backlit_haze",      "cloud_shadow"],
}

AERIAL_LIGHTING_BY_MODE = {
    "soaring_thermal":["thermal_shimmer", "backlit_haze",     "halo_backlit",      "open_sky_flat",     "golden_hour"],
    "dive_strike":    ["storm_flash",     "dramatic_rim",     "backlit_haze",      "halo_backlit",      "golden_hour"],
    "perched":        ["golden_hour",     "dawn_first_light", "overcast",          "dramatic_rim",      "dappled_canopy"],
}

AERIAL_MOOD_BY_LIGHTING = {
    "golden_hour":    ["thermal_drift",   "effortless_cruise","serene",            "quiet_power",       "feeding_return"],
    "backlit_haze":   ["quiet_power",     "thermal_drift",    "effortless_cruise", "serene",            "eye_contact"],
    "thermal_shimmer":["thermal_drift",   "effortless_cruise","quiet_power",       "serene",            "wind_buffet"],
    "halo_backlit":   ["quiet_power",     "serene",           "eye_contact",       "thermal_drift",     "effortless_cruise"],
    "storm_flash":    ["menacing",        "rain_endurance",   "wind_buffet",       "exhausted_glide",   "startled_flare"],
    "stormy":         ["rain_endurance",  "wind_buffet",      "menacing",          "exhausted_glide",   "startled_flare"],
    "pre_storm":      ["wind_buffet",     "rain_endurance",   "menacing",          "thermal_drift",     "startled_flare"],
    "dramatic_rim":   ["menacing",        "quiet_power",      "eye_contact",       "territorial_display","hunting_scan"],
    "open_sky_flat":  ["effortless_cruise","thermal_drift",   "serene",            "quiet_power",       "glide_descent"],
    "cloud_shadow":   ["hunting_scan",    "quiet_power",      "glide_descent",     "effortless_cruise", "thermal_drift"],
    "dawn_first_light":["dawn_launch",   "serene",            "thermal_drift",     "quiet_power",       "effortless_cruise"],
    "sunset_warm":    ["dusk_roost_approach","effortless_cruise","serene",          "feeding_return",    "thermal_drift"],
    "blue_hour":      ["dusk_roost_approach","exhausted_glide","serene",           "quiet_power",       "glide_descent"],
    "overcast":       ["effortless_cruise","quiet_power",     "hunting_scan",      "glide_descent",     "serene"],
    "broken_cloud":   ["effortless_cruise","thermal_drift",   "hunting_scan",      "wind_buffet",       "glide_descent"],
    "fog_top_layer":  ["effortless_cruise","serene",          "quiet_power",       "glide_descent",     "exhausted_glide"],
    "rain_scatter":   ["rain_endurance",  "wind_buffet",      "exhausted_glide",   "headwind_struggle" ,"startled_flare"],
    "altitude_clear": ["effortless_cruise","thermal_drift",   "quiet_power",       "hunting_scan",      "serene"],
    "horizon_glow":   ["dusk_roost_approach","dawn_launch",   "effortless_cruise", "serene",            "thermal_drift"],
    "reflected_ground":["hunting_scan",  "glide_descent",    "quiet_power",       "effortless_cruise", "thermal_drift"],
}

AERIAL_BEHAVIOR_BY_MOOD = {
    "thermal_drift":      ["thermal_soaring",  "glide_coast",      "banking_turn",      "updraft_hover",     "level_cruise"],
    "wind_buffet":        ["wind_correction",  "headwind_struggle","banking_turn",      "flapping_climb",    "wake_turbulence"],
    "perched_alert":      ["cliff_perching",   "preening_perched", "morning_stretch",   "cliff_launch",      "aerial_display"],
    "glide_descent":      ["glide_coast",      "landing_approach", "banking_turn",      "diving_strike",     "fish_snatch"],
    "hunting_scan":       ["diving_strike",    "fish_snatch",      "banking_turn",      "glide_coast",       "thermal_soaring"],
    "territorial_display":["aerial_display",   "rival_chase",      "banking_turn",      "flapping_climb",    "diving_strike"],
    "effortless_cruise":  ["level_cruise",     "glide_coast",      "thermal_soaring",   "banking_turn",      "updraft_hover"],
    "startled_flare":     ["banking_turn",     "flapping_climb",   "wind_correction",   "cliff_launch",      "headwind_struggle"],
    "feeding_return":     ["landing_approach", "prey_carry",       "glide_coast",       "banking_turn",      "level_cruise"],
    "dawn_launch":        ["cliff_launch",     "flapping_climb",   "morning_stretch",   "level_cruise",      "banking_turn"],
    "dusk_roost_approach":["landing_approach", "glide_coast",      "banking_turn",      "cliff_perching",    "preening_perched"],
    "playful_tumble":     ["banking_turn",     "aerial_display",   "wake_turbulence",   "tandem_flight",     "updraft_hover"],
    "exhausted_glide":    ["glide_coast",      "level_cruise",     "landing_approach",  "headwind_struggle", "wind_correction"],
    "rain_endurance":     ["headwind_struggle","wind_correction",  "glide_coast",       "flapping_climb",    "level_cruise"],
    "juvenile_clumsy":    ["cliff_launch",     "banking_turn",     "flapping_climb",    "wind_correction",   "landing_approach"],
    "quiet_power":        ["thermal_soaring",  "level_cruise",     "glide_coast",       "banking_turn",      "updraft_hover"],
    "serene":             ["glide_coast",      "thermal_soaring",  "level_cruise",      "updraft_hover",     "banking_turn"],
    "menacing":           ["diving_strike",    "rival_chase",      "aerial_display",    "banking_turn",      "fish_snatch"],
    "eye_contact":        ["cliff_perching",   "updraft_hover",    "thermal_soaring",   "glide_coast",       "morning_stretch"],
    "closed_mouth_resting":["cliff_perching",  "preening_perched", "morning_stretch",   "glide_coast",       "updraft_hover"],
}

AERIAL_CONDITION_BY_SPECIES = {
    "Pteranodon":     ["dominant_prime",  "weathered_adult",  "torn_membrane",     "fish_oil_stain",    "salt_spray_residue"],
    "Quetzalcoatlus": ["dominant_prime",  "weathered_adult",  "torn_membrane",     "wind_worn_crest",   "battle_scarred"],
    "Rhamphorhynchus":["pristine_juvenile","dominant_prime",  "fish_oil_stain",    "torn_membrane",     "beak_chip"],
    "Dimorphodon":    ["pristine_juvenile","dominant_prime",  "fish_oil_stain",    "beak_chip",         "insect_bitten"],
}

AERIAL_CAMERA_BY_MODE = {
    "portrait":        ["closeup_portrait","tight_head",      "wing_detail",       "cliff_perch",       "detail_abstract"],
    "canvas":          ["full_body_profile","flight_tracking","below_up_wings",    "parallel_flight",   "distant_speck"],
    "environmental":   ["distant_speck",   "cloud_frame",     "thermal_circle",    "flight_tracking",   "sunrise_silhouette"],
    "soaring_thermal": ["below_up_wings",  "thermal_circle",  "flight_tracking",   "sunrise_silhouette","cloud_frame"],
    "dive_strike":     ["stoop_above",     "head_on_approach","banking_turn",      "flight_tracking",   "below_up_wings"],
    "action_freeze":   ["stoop_above",     "head_on_approach","banking_turn",      "below_up_wings",    "parallel_flight"],
    "extreme_closeup": ["wing_detail",     "detail_abstract", "tight_head",        "cliff_perch",       "closeup_portrait"],
    "aerial_overhead": ["above_down_dorsal","distant_speck",  "thermal_circle",    "cloud_frame",       "flight_tracking"],
    "tracking_side":   ["parallel_flight", "flight_tracking", "banking_turn",      "distant_speck",     "full_body_profile"],
    "dusk_long_exp":   ["sunrise_silhouette","distant_speck", "cloud_frame",       "thermal_circle",    "flight_tracking"],
    "perched":         ["cliff_perch",     "closeup_portrait","wing_detail",       "tight_head",        "medium_shot"],
}

AERIAL_WEATHER_BY_MOOD = {
    "thermal_drift":      ["thermal_column",  "high_altitude_clear","calm_dead_air",   "tailwind_fast",     "clear_cold_high"],
    "wind_buffet":        ["headwind_strong", "crosswind_shear",  "updraft_turbulence","coastal_wind",     "storm_anvil_top"],
    "effortless_cruise":  ["tailwind_fast",   "thermal_column",   "high_altitude_clear","calm_dead_air",   "clear_cold_high"],
    "hunting_scan":       ["high_altitude_clear","thermal_column","calm_dead_air",     "tailwind_fast",    "cloud_layer_below"],
    "menacing":           ["storm_anvil_top", "updraft_turbulence","headwind_strong",  "crosswind_shear",  "rain_curtain"],
    "rain_endurance":     ["rain_curtain",    "updraft_turbulence","headwind_strong",  "sea_spray_altitude","storm_anvil_top"],
    "exhausted_glide":    ["headwind_strong", "updraft_turbulence","rain_curtain",     "crosswind_shear",  "haze_layer"],
    "dusk_roost_approach":["sunset_altitude", "calm_dead_air",    "coastal_wind",      "haze_layer",       "tailwind_fast"],
    "dawn_launch":        ["dawn_horizon",    "thermal_column",   "calm_dead_air",     "coastal_wind",     "high_altitude_clear"],
    "serene":             ["calm_dead_air",   "high_altitude_clear","tailwind_fast",   "thermal_column",   "cloud_layer_below"],
    "playful_tumble":     ["updraft_turbulence","mountain_wave",  "thermal_column",    "coastal_wind",     "tailwind_fast"],
    "territorial_display":["coastal_wind",   "headwind_strong",  "updraft_turbulence","thermal_column",   "crosswind_shear"],
    "quiet_power":        ["high_altitude_clear","thermal_column","calm_dead_air",     "tailwind_fast",    "cloud_layer_below"],
    "glide_descent":      ["tailwind_fast",   "calm_dead_air",    "coastal_wind",      "haze_layer",       "cloud_layer_below"],
    "startled_flare":     ["updraft_turbulence","crosswind_shear","headwind_strong",   "coastal_wind",     "storm_anvil_top"],
}

AERIAL_INVALID_COMBOS = [
    # Perched behaviors ↔ active in-flight moods
    ("behavior", "cliff_perching",    "mood", "thermal_drift",    "perched on cliff — not thermaling"),
    ("behavior", "cliff_perching",    "mood", "effortless_cruise","perched on cliff — not cruising"),
    ("behavior", "cliff_perching",    "mood", "wind_buffet",      "perched on cliff — not in active wind buffet"),
    ("behavior", "preening_perched",  "mood", "thermal_drift",    "preening on perch — not thermaling"),
    ("behavior", "preening_perched",  "mood", "effortless_cruise","preening on perch — not cruising"),
    ("behavior", "preening_perched",  "mood", "hunting_scan",     "preening on perch — not on active hunting scan"),
    ("behavior", "morning_stretch",   "mood", "thermal_drift",    "morning stretch is grounded — not thermaling"),
    ("behavior", "morning_stretch",   "mood", "effortless_cruise","morning stretch is grounded — not cruising"),
    ("behavior", "morning_stretch",   "mood", "wind_buffet",      "morning stretch on ground — not in wind buffet"),
    # In-flight active behaviors ↔ perched mood
    ("behavior", "thermal_soaring",   "mood", "perched_alert",    "thermal soaring — contradicts perched alert mood"),
    ("behavior", "diving_strike",     "mood", "perched_alert",    "diving strike — contradicts perched mood"),
    ("behavior", "level_cruise",      "mood", "perched_alert",    "level cruise — contradicts perched mood"),
    ("behavior", "fish_snatch",       "mood", "perched_alert",    "fish snatch in flight — contradicts perched mood"),
    # Struggling behaviors ↔ effortless moods (scientifically: wind physics)
    ("behavior", "headwind_struggle", "mood", "thermal_drift",    "headwind struggle — contradicts leisurely thermal drift"),
    ("behavior", "headwind_struggle", "mood", "effortless_cruise","headwind struggle — contradicts effortless cruise"),
    ("behavior", "headwind_struggle", "mood", "serene",           "headwind struggle — contradicts serene mood"),
    # Steep dive ↔ drifting mood (contradicts flight mechanics)
    ("behavior", "diving_strike",     "mood", "thermal_drift",    "steep dive — contradicts slow thermal drifting"),
    # Landing ↔ active altitude moods
    ("behavior", "landing_approach",  "mood", "thermal_drift",    "landing approach — not still thermaling"),
    ("behavior", "landing_approach",  "mood", "hunting_scan",     "landing approach — not in hunting scan"),
]

AERIAL_MODE_COMBO_BLOCKS = {
    "soaring_thermal": {
        "behavior": {
            "cliff_perching":  "soaring thermal mode — can't be perched",
            "preening_perched":"soaring thermal mode — can't be preening on perch",
            "morning_stretch": "soaring thermal mode — can't be doing morning stretch",
            "landing_approach":"soaring thermal mode — already airborne, not landing",
            "cliff_launch":    "soaring thermal mode — already airborne, not launching",
        },
        "mood": {
            "perched_alert":       "soaring thermal mode — can't be in perched mood",
            "dusk_roost_approach": "soaring thermal mode — not approaching roost",
        },
    },
    "dive_strike": {
        "behavior": {
            "cliff_perching":  "dive strike mode — can't be perched",
            "preening_perched":"dive strike mode — can't be preening",
            "thermal_soaring": "dive strike mode — diving, not soaring",
            "updraft_hover":   "dive strike mode — diving, not hovering",
            "landing_approach":"dive strike mode — striking, not landing",
            "morning_stretch": "dive strike mode — can't be doing morning stretch",
        },
        "mood": {
            "perched_alert":       "dive strike mode — can't be in perched mood",
            "thermal_drift":       "dive strike mode — diving steeply, not drifting",
            "dusk_roost_approach": "dive strike mode — striking, not roosting",
        },
    },
    "perched": {
        "behavior": {
            "thermal_soaring":    "perched mode — not in flight",
            "diving_strike":      "perched mode — not in flight",
            "level_cruise":       "perched mode — not in flight",
            "fish_snatch":        "perched mode — not in flight",
            "flapping_climb":     "perched mode — not in flight",
            "banking_turn":       "perched mode — not in flight",
            "headwind_struggle":  "perched mode — not in flight",
            "wind_correction":    "perched mode — not in flight",
        },
        "mood": {
            "thermal_drift":      "perched mode — not thermaling",
            "effortless_cruise":  "perched mode — not cruising",
            "wind_buffet":        "perched mode — not in wind buffet",
            "hunting_scan":       "perched mode — not in active aerial hunt",
        },
    },
}


def get_aerial_suggestions(category: str, context: dict) -> list:
    if context.get("habitat") != "aerial":
        return []

    species_name = context.get("species_name", "")
    diet         = context.get("diet", "")
    output_mode  = context.get("output_mode", "")
    lighting     = context.get("lighting")
    mood         = context.get("mood")
    behavior     = context.get("behavior")

    if category == "lighting":
        if output_mode in AERIAL_LIGHTING_BY_MODE:
            return AERIAL_LIGHTING_BY_MODE[output_mode]
        return AERIAL_LIGHTING_BY_SPECIES.get(species_name, [])

    if category == "mood":
        base = list(AERIAL_MOOD_BY_LIGHTING.get(lighting, []))
        if diet == "Carnivore" and base:
            priority = [m for m in ["menacing", "hunting_scan", "territorial_display", "quiet_power", "glide_descent"] if m in base]
            rest = [m for m in base if m not in priority]
            base = priority + rest
        return base[:5]

    if category == "behavior":
        return AERIAL_BEHAVIOR_BY_MOOD.get(mood, [])

    if category == "condition":
        base = list(AERIAL_CONDITION_BY_SPECIES.get(species_name, []))
        if mood in ("hunting_scan", "menacing") or behavior in ("diving_strike", "fish_snatch"):
            priority = ["fish_oil_stain", "torn_membrane", "battle_scarred"]
            base = priority + [c for c in base if c not in priority]
        elif mood == "exhausted_glide" or behavior == "headwind_struggle":
            priority = ["torn_membrane", "wing_joint_swollen", "lean_season", "missing_pycnofibres"]
            base = priority + [c for c in base if c not in priority]
        elif behavior in ("cliff_perching", "preening_perched", "morning_stretch"):
            priority = ["wind_worn_crest", "talon_worn", "sun_bleached"]
            base = priority + [c for c in base if c not in priority]
        return base[:5]

    if category == "camera":
        base = list(AERIAL_CAMERA_BY_MODE.get(output_mode, []))
        if behavior in ("cliff_perching", "preening_perched", "morning_stretch"):
            base = ["cliff_perch", "closeup_portrait", "tight_head", "wing_detail", "medium_shot"]
        elif behavior in ("diving_strike", "fish_snatch", "stoop_above"):
            base = ["stoop_above", "banking_turn", "head_on_approach", "below_up_wings", "parallel_flight"]
        elif behavior in ("thermal_soaring", "glide_coast", "updraft_hover"):
            base = ["below_up_wings", "thermal_circle", "flight_tracking", "distant_speck", "parallel_flight"]
        elif behavior in ("landing_approach", "cliff_launch"):
            base = ["landing_sequence", "flight_tracking", "parallel_flight", "cliff_perch", "below_up_wings"]
        return base[:5]

    if category == "weather":
        return AERIAL_WEATHER_BY_MOOD.get(mood, [])[:5]

    return []


def get_aerial_blocked(category: str, context: dict) -> dict:
    if context.get("habitat") != "aerial":
        return {}

    blocked = {}
    output_mode = context.get("output_mode", "")

    for cat_blk, entries in AERIAL_MODE_COMBO_BLOCKS.get(output_mode, {}).items():
        if cat_blk == category:
            blocked.update(entries)

    for cat_a, name_a, cat_b, name_b, reason in AERIAL_INVALID_COMBOS:
        if cat_b == category and context.get(cat_a) == name_a:
            blocked.setdefault(name_b, reason)
        if cat_a == category and context.get(cat_b) == name_b:
            blocked.setdefault(name_a, reason)

    return blocked


# ---------------------------------------------------------------------------
# Habitat-agnostic dispatchers — used in main() for all three habitats
# ---------------------------------------------------------------------------

def get_suggestions(category: str, context: dict) -> list:
    habitat = context.get("habitat", "")
    if habitat == "marine":
        return get_marine_suggestions(category, context)
    if habitat == "terrestrial":
        return get_terrestrial_suggestions(category, context)
    if habitat == "aerial":
        return get_aerial_suggestions(category, context)
    return []


def get_blocked(category: str, context: dict) -> dict:
    habitat = context.get("habitat", "")
    if habitat == "marine":
        return get_marine_blocked(category, context)
    if habitat == "terrestrial":
        return get_terrestrial_blocked(category, context)
    if habitat == "aerial":
        return get_aerial_blocked(category, context)
    return {}


# Style is always hyperrealism — never ask the user
HYPERREALISM_STYLE = {
    "id":    24,
    "name":  "hyperrealism",
    "value": "hyperrealistic, anatomically accurate, living animal skin texture, natural imperfections, photographed in the wild",
}

# ---------------------------------------------------------------------------
# Mouth / teeth / saliva — diet-aware, injected as a dedicated prompt block
# ---------------------------------------------------------------------------

MOUTH_TEETH_CARNIVORE = (
    "yellowed uneven teeth, wet interior mouth, heavy saliva stranding between teeth"
)

MOUTH_TEETH_HERBIVORE = (
    "wet lips parted, grinding teeth worn flat, saliva catching light along jaw"
)

# ---------------------------------------------------------------------------
# Habitat-specific interaction blocks — replaces the old single GROUND_INTERACTION.
# Each habitat gets its own physics/contact language so MJ renders the right
# relationship between the animal and its medium.
# ---------------------------------------------------------------------------

HABITAT_INTERACTION = {
    "terrestrial": (
        "feet fully weight-bearing, each toe contacting ground at a different angle, "
        "visible pressure on toe pads, natural keratin wear on claw tips, "
        "packed dirt between digits, knuckle joints slightly bent under load"
    ),
    "marine": (
        "body partially submerged, waterline crossing torso, "
        "body above waterline sharp and dry with water beading on skin, "
        "body below waterline colour-shifted blue-green and slightly distorted by refraction, "
        "water surface tension visible against skin, "
        "ripples radiating from body movement, wet skin above waterline glistening"
    ),
    "aerial": (
        "wing membrane taut and translucent against light, individual finger bones "
        "visible as structural ridges, air current shaping membrane surface, "
        "body suspended in open sky, no ground contact"
    ),
}

# ---------------------------------------------------------------------------
# Habitat-specific realism style anchors — appended to HYPERREALISM_STYLE
# to push MJ toward the right kind of wildlife photography per domain.
# ---------------------------------------------------------------------------

HABITAT_REALISM = {
    "terrestrial": (
        "National Geographic wildlife photography, telephoto bokeh, "
        "muted natural colour, film grain, dust particles in air"
    ),
    "marine": (
        "National Geographic ocean wildlife photography, underwater caustics, "
        "water surface refraction, natural ocean colour, water droplets on lens, "
        "wet skin detail, marine biology documentary"
    ),
    "aerial": (
        "National Geographic bird-in-flight photography, atmospheric haze, "
        "thermal shimmer, open sky negative space, motion-sharp wings, "
        "raptor flight documentary"
    ),
}

# ---------------------------------------------------------------------------
# Habitat-specific negative prompt additions — appended to base NEGATIVE_PROMPT
# ---------------------------------------------------------------------------

HABITAT_NEGATIVE = {
    "terrestrial": "",
    "marine": (
        "dry land, standing on ground, desert, forest floor, "
        "no water, dry skin, dusty"
    ),
    "aerial": (
        "standing on ground, walking, sitting, grounded, "
        "feet on dirt, terrestrial pose, folded wings"
    ),
}

# ---------------------------------------------------------------------------
# Canvas print mode constants
# ---------------------------------------------------------------------------

CANVAS_PRINT = (
    "high dynamic range, shadow detail retained, highlight detail retained, "
    "print-ready detail, no blown highlights"
)

# ---------------------------------------------------------------------------
# Negative prompt — appended as --no flag to fight Midjourney's extremity slop
# ---------------------------------------------------------------------------

NEGATIVE_PROMPT = (
    # Anatomy / extremity errors
    "fused digits, merged toes, webbed feet, blob hands, extra fingers, "
    "missing claws, undefined claw tips, floating toes, amputated digits, "
    "incorrect toe count, melted feet, smooth footpad with no digit separation, "
    "smeared claws, indistinct talons, CGI smoothness on extremities, "
    # Studio / controlled environment blockers
    "studio background, seamless backdrop, portrait lighting, gradient background, "
    "grey background, controlled lighting, specimen photography, museum display, "
    "exhibit lighting, black background, white background, studio flash, "
    "specimen mount, display case, diorama, natural history exhibit, "
    # Fossil / skeletal blockers
    "fossil, fossilized, skeleton, skeletal, bones, bone structure, excavation, "
    "petrified, paleontology specimen, museum specimen, rock matrix, sediment, "
    "dinosaur fossil, fossil record, prehistoric bones, mineralized, stone cast, "
    "osteoderms, osteoderm, "
    # Indoor / built environment blockers
    "indoors, interior, building, warehouse, arena, concrete floor, "
    # CGI / digital environment blockers
    "digital matte painting, rendered background, CGI environment, concept art, "
    "illustration, painted background, 3D render, Unreal Engine, volumetric god rays, "
    "hyper-saturated, fantasy landscape, perfect symmetry, smooth gradient sky"
)

# Species-specific additions that only apply in canvas / full-body modes
CANVAS_SPECIES_EXTRAS = {
    "Velociraptor": "sickle claw raised, palms inward, tail extended for balance",
}

# ---------------------------------------------------------------------------
# Output modes
# Each entry drives fixed-camera text, composition instructions, and flags.
# fixed_camera=None means the user picks a camera from the DB.
# composition="PLACEMENT" is a sentinel that triggers the placement sub-menu.
# ---------------------------------------------------------------------------

OUTPUT_MODES: dict[str, dict] = {
    "portrait": {
        "display":       "Portrait close-up",
        "desc":          "telephoto, tight framing, mood-focused",
        "fixed_camera":  None,
        "composition":   "",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial"],
    },
    "canvas": {
        "display":       "Full body canvas print",
        "desc":          "mid-range lens, 60/40 negative space, print-ready",
        "fixed_camera":  "Canon EOS R5 24-70mm f/4, mid-range, habitat in frame",
        "composition":   "PLACEMENT",
        "canvas_print":  True,
        "full_body":     True,
        "needs_placement": True,
        "habitats":      ["terrestrial", "marine", "aerial"],
    },
    "environmental": {
        "display":       "Environmental wide shot",
        "desc":          "animal small in vast landscape, habitat dominant",
        "fixed_camera":  "Canon EOS R5 16-35mm f/2.8, ultra-wide, animal under 20% of frame",
        "composition":   "animal small in vast prehistoric landscape, habitat dominant",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial"],
    },
    "extreme_closeup": {
        "display":       "Extreme detail close-up",
        "desc":          "macro, single surface dominant, texture abstracted",
        "fixed_camera":  "Canon EOS R5 100mm macro f/8, razor-thin depth of field",
        "composition":   "single anatomical surface fills frame, texture dominant",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial"],
    },
    "action_freeze": {
        "display":       "Action freeze frame",
        "desc":          "motion stopped at peak energy, every detail sharp",
        "fixed_camera":  "Canon EOS R5 400mm f/2.8, 1/2000s freeze, sharp throughout",
        "composition":   "frozen mid-action at peak moment, kinetic force implied",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial"],
    },
    "silhouette": {
        "display":       "Silhouette against sky",
        "desc":          "backlit, form only, no surface detail",
        "fixed_camera":  "Canon EOS R5, exposed for bright background, strong rim light",
        "composition":   "pure silhouette against sky, stark contrast, form only",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "aerial"],
    },
    "tracking_side": {
        "display":       "Tracking side profile",
        "desc":          "panning shot, sharp subject, motion-blurred background",
        "fixed_camera":  "Canon EOS R5 400mm f/2.8, panning, subject sharp on blurred background",
        "composition":   "lateral tracking shot, sharp side profile, background streaked",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine"],
    },
    "ground_level": {
        "display":       "Ground-level upward",
        "desc":          "camera at ground, animal towers above lens",
        "fixed_camera":  "Canon EOS R5 24mm f/2.8, camera at ground, extreme upward angle",
        "composition":   "ground-level upward, animal towers overhead, sky behind",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial"],
    },
    "aerial_overhead": {
        "display":       "Aerial overhead",
        "desc":          "direct overhead, dorsal surface visible, habitat below",
        "fixed_camera":  "Canon EOS R5 35mm, directly overhead, dorsal surface",
        "composition":   "overhead view, dorsal surface centred, habitat visible around animal",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine"],
    },
    "dusk_long_exp": {
        "display":       "Dusk long exposure",
        "desc":          "motion blur, ambient light only, atmospheric",
        "fixed_camera":  "Canon EOS R5 50mm f/5.6, tripod, long exposure at dusk",
        "composition":   "long exposure, moving elements blurred, static elements sharp",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine"],
    },
    # --- Marine-specific modes ---
    "surface_break": {
        "display":       "Surface break",
        "desc":          "animal breaking water surface, half submerged",
        "fixed_camera":  "Canon EOS R5 400mm f/2.8, water-level camera, split waterline",
        "composition":   "animal breaching water surface, waterline bisecting frame, sky above water below",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
        "habitats":      ["marine"],
    },
    "underwater": {
        "display":       "Underwater",
        "desc":          "fully submerged, caustics, murky depth",
        "fixed_camera":  "Canon EOS R5 in underwater housing, 16-35mm f/2.8, natural light from above",
        "composition":   "fully submerged, light filtering from surface above, murky water depth",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["marine"],
    },
    # --- Aerial-specific modes ---
    "soaring_thermal": {
        "display":       "Soaring on thermal",
        "desc":          "wings spread, thermal soaring, shot from below",
        "fixed_camera":  "Canon EOS R5 600mm f/4, upward angle, bird-in-flight tracking",
        "composition":   "wings fully extended, thermal soaring, shot from below against sky",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["aerial"],
    },
    "dive_strike": {
        "display":       "Dive / strike",
        "desc":          "steep dive, wings tucked, speed lines implied",
        "fixed_camera":  "Canon EOS R5 400mm f/2.8, 1/4000s freeze, tracking downward",
        "composition":   "steep diving angle, wings partially folded, speed and gravity implied",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["aerial"],
    },
    "perched": {
        "display":       "Perched on cliff / roost",
        "desc":          "perched on rock or cliff edge, wings folded, grounded detail",
        "fixed_camera":  "Canon EOS R5 600mm f/4, telephoto, cliff-level angle",
        "composition":   "perched on rocky outcrop or cliff edge, wings folded at sides, talons gripping rock",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["aerial"],
    },
}


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        sys.exit(f"Database not found: {db_path}\nRun setup_db.py first.")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def fetch_species(conn: sqlite3.Connection, habitat: str = "terrestrial") -> list:
    return conn.execute(
        "SELECT id, name, common_name, period, diet, size_class, description, notes, habitat "
        "FROM species WHERE habitat = ? ORDER BY name",
        (habitat,),
    ).fetchall()


def fetch_parameters_by_category(conn: sqlite3.Connection, category: str, habitat: str = None) -> list:
    if habitat:
        return conn.execute(
            "SELECT id, name, value, weight FROM parameters "
            "WHERE category = ? AND habitats LIKE ? ORDER BY id",
            (category, f"%{habitat}%"),
        ).fetchall()
    return conn.execute(
        "SELECT id, name, value, weight FROM parameters WHERE category = ? ORDER BY id",
        (category,),
    ).fetchall()


def fetch_species_required_params(conn: sqlite3.Connection, species_id: int) -> list:
    return conn.execute(
        """SELECT p.id, p.category, p.name, p.value
           FROM species_parameters sp
           JOIN parameters p ON p.id = sp.parameter_id
           WHERE sp.species_id = ? AND sp.required = 1
           ORDER BY p.category, p.name""",
        (species_id,),
    ).fetchall()


def fetch_global_rules(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT rule FROM global_rules WHERE active = 1 ORDER BY id"
    ).fetchall()
    return [r["rule"] for r in rows]


def fetch_species_science(conn: sqlite3.Connection, species_id: int):
    return conn.execute(
        """SELECT body_length_m, body_mass_kg, locomotion_type, feathering_coverage,
                  skin_texture_type, tail_posture, wrist_position,
                  known_coloration_evidence, last_scientific_update, habitat
           FROM species WHERE id = ?""",
        (species_id,),
    ).fetchone()


def fetch_research_notes(conn: sqlite3.Connection, species_id: int) -> list:
    return conn.execute(
        """SELECT finding, author, year, source, affects_prompt
           FROM research_notes
           WHERE species_id = ? ORDER BY affects_prompt DESC, year DESC""",
        (species_id,),
    ).fetchall()


def scan_reference_images() -> dict[str, int]:
    """Return {species_name: image_count} by scanning species_reference subfolders."""
    counts = {}
    if not SPECIES_REF_DIR.exists():
        return counts
    for folder in sorted(SPECIES_REF_DIR.iterdir()):
        if folder.is_dir():
            images = [f for f in folder.iterdir()
                      if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
            counts[folder.name] = len(images)
    return counts


def save_prompt(
    conn: sqlite3.Connection,
    species_id: int,
    title: str,
    positive_prompt: str,
    tags: str,
    parameter_ids: list[int],
) -> int:
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO prompts (species_id, title, positive_prompt, tags, status)
           VALUES (?, ?, ?, ?, 'pending')""",
        (species_id, title, positive_prompt, tags),
    )
    prompt_id = cur.lastrowid
    cur.executemany(
        "INSERT INTO prompt_parameters (prompt_id, parameter_id) VALUES (?, ?)",
        [(prompt_id, pid) for pid in parameter_ids],
    )
    conn.commit()
    return prompt_id


# ---------------------------------------------------------------------------
# Interactive menus
# ---------------------------------------------------------------------------

def pick(label: str, rows: list, display_fn, suggestions=None, blocked=None, suggest_label: str = "") -> object:
    """Print a numbered menu and return the chosen row.

    suggestions:    list of parameter names to highlight with ★
    blocked:        dict of {name: reason} — shown greyed/red, selection refused
    suggest_label:  context string shown in the suggestion header
    """
    suggestions  = suggestions or []
    blocked      = blocked or {}
    suggested_set = set(suggestions)

    print(f"\n  {hdr(label)}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)

    if suggestions:
        sug_display = "  ".join(s.replace("_", " ") for s in suggestions)
        hdr_text = f"★ SUGGESTED{f' {suggest_label}' if suggest_label else ''}:"
        print(f"  {C.YELLOW}{hdr_text}{C.RESET}")
        print(f"  {C.YELLOW}  {sug_display}{C.RESET}")
        print(f"  {C.DIM}" + "─" * 60 + C.RESET)

    for i, row in enumerate(rows, 1):
        display = display_fn(row)
        try:
            row_name = row["name"]
        except (TypeError, KeyError):
            row_name = None

        if row_name and row_name in blocked:
            suffix = f"  {C.BOLD_RED}✗{C.RESET} {C.DIM}{blocked[row_name]}{C.RESET}"
            print(f"  {C.DIM}{i:>2}.{C.RESET}  {C.DIM}{display}{C.RESET}{suffix}")
        elif row_name and row_name in suggested_set:
            suffix = f"  {C.YELLOW}★{C.RESET}"
            print(f"  {C.DIM}{i:>2}.{C.RESET}  {opt(display)}{suffix}")
        else:
            print(f"  {C.DIM}{i:>2}.{C.RESET}  {opt(display)}")

    print()
    while True:
        raw = input(f"  {C.BOLD_CYAN}Choose 1–{len(rows)}:{C.RESET} ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(rows):
            chosen = rows[int(raw) - 1]
            try:
                chosen_name = chosen["name"]
            except (TypeError, KeyError):
                chosen_name = None
            if chosen_name and chosen_name in blocked:
                print(f"  {err(f'✗ Invalid combo: {blocked[chosen_name]}')}")
                continue
            print(f"  {ok('✓')} {ok(display_fn(chosen))}\n")
            return chosen
        print(f"  {err(f'Please enter a number between 1 and {len(rows)}.')}")


def select_habitat() -> str:
    """Present the 3 habitat types and return the chosen key."""
    HABITATS = [
        ("terrestrial", "Terrestrial", "land-based dinosaurs — ground, forest, plains"),
        ("marine",      "Marine",      "ocean and water-dwelling species — submerged, surface"),
        ("aerial",      "Aerial",      "flying species — pterosaurs, in-flight, soaring"),
    ]
    print(f"\n  {hdr('Select habitat type')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for i, (_, label, desc) in enumerate(HABITATS, 1):
        print(f"  {C.DIM}{i:>2}.{C.RESET}  {C.BRIGHT_WHITE}{label:<16}{C.RESET}  {dim(desc)}")
    print()
    while True:
        raw = input(f"  {C.BOLD_CYAN}Choose 1–{len(HABITATS)}:{C.RESET} ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(HABITATS):
            key, label, _ = HABITATS[int(raw) - 1]
            print(f"  {ok('✓')} {ok(label)}\n")
            return key
        print(f"  {err(f'Please enter a number between 1 and {len(HABITATS)}.')}")


def select_mode(habitat: str) -> str:
    """Present output modes filtered by habitat and return the chosen mode key."""
    keys = [k for k, v in OUTPUT_MODES.items() if habitat in v.get("habitats", ["terrestrial"])]
    print(f"\n  {hdr('Select output mode')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for i, key in enumerate(keys, 1):
        cfg = OUTPUT_MODES[key]
        print(f"  {C.DIM}{i:>2}.{C.RESET}  {C.BRIGHT_WHITE}{cfg['display']:<26}{C.RESET}  {dim(cfg['desc'])}")
    print()
    while True:
        raw = input(f"  {C.BOLD_CYAN}Choose 1–{len(keys)}:{C.RESET} ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            chosen_key = keys[int(raw) - 1]
            print(f"  {ok('✓')} {ok(OUTPUT_MODES[chosen_key]['display'])}\n")
            return chosen_key
        print(f"  {err(f'Please enter a number between 1 and {len(keys)}.')}")


def select_canvas_placement() -> tuple[str, str]:
    """Ask how the animal is positioned in frame.
    Returns (composition_phrase, space_side).
    'dead_center' is a sentinel that triggers symmetric composition text."""
    OPTIONS = [
        # (composition_phrase injected into prompt,  space_side label for display)
        ("animal positioned left of centre, rule of thirds",                "right"),
        ("animal positioned right of centre, rule of thirds",               "left"),
        ("dead_center",                                                      ""),
        ("animal filling lower foreground, environment stretching above",   "above"),
        ("animal in far distance, tiny against vast landscape",             "all"),
        ("animal emerging from dense vegetation, partially obscured",       "right"),
        ("animal seen from behind, retreating from camera",                 "ahead"),
        ("animal at water's edge, full reflection below",                   "below"),
        ("camera below looking up, animal against sky",                     "above"),
        ("animal high on ridge or elevated terrain, horizon behind",        "below"),
    ]
    LABELS = [
        "Rule of thirds — left",
        "Rule of thirds — right",
        "Dead centre — symmetrical, camera trap",
        "Foreground dominant — animal fills lower frame",
        "Distant figure — tiny in vast landscape",
        "Emerging from cover — partially obscured",
        "Retreating away — animal from behind",
        "Water's edge — animal with reflection",
        "Low angle — camera below, sky behind",
        "High ground — animal on ridge, horizon below",
    ]
    print(f"\n  {hdr('Animal placement')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for i, label in enumerate(LABELS, 1):
        print(f"  {C.DIM}{i:>2}.{C.RESET}  {opt(label)}")
    print()
    while True:
        raw = input(f"  {C.BOLD_CYAN}Choose 1–{len(OPTIONS)}:{C.RESET} ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(OPTIONS):
            chosen = OPTIONS[int(raw) - 1]
            print(f"  {ok('✓')} {ok(LABELS[int(raw) - 1])}\n")
            return chosen
        print(f"  {err(f'Please enter a number between 1 and {len(OPTIONS)}.')}")


def pick_species(conn: sqlite3.Connection, habitat: str = "terrestrial"):
    rows = fetch_species(conn, habitat)
    if not rows:
        sys.exit(f"No {habitat} species found. Run setup_db.py to seed the database.")

    def fmt(r):
        size = f"[{r['size_class']}]" if r["size_class"] else ""
        period = f"({r['period']})" if r["period"] else ""
        common = f" / {r['common_name']}" if r["common_name"] else ""
        return f"{r['name']}{common}  {size} {period}"

    if len(rows) == 1:
        chosen = rows[0]
        print(f"\n  {hdr('Select a dinosaur species')}")
        print(f"  {ok('✓')} {ok(fmt(chosen))}  {dim('(only species for this habitat)')}\n")
        return chosen

    return pick("Select a dinosaur species", rows, fmt)


def pick_parameter(conn: sqlite3.Connection, category: str, name_only: bool = False, habitat: str = None,
                   suggestions=None, blocked=None, suggest_label: str = ""):
    rows = fetch_parameters_by_category(conn, category, habitat=habitat)
    if not rows:
        sys.exit(f"No {habitat or ''} parameters found for category '{category}'. Run setup_db.py.")

    label = f"Select {category.upper()}"

    if name_only:
        def fmt(r):
            return r["name"].replace("_", " ")
    else:
        def fmt(r):
            weight_tag = f" [weight {r['weight']}]" if r["weight"] != 1.0 else ""
            return f"{r['name']:<22} — {r['value']}{weight_tag}"

    return pick(label, rows, fmt, suggestions=suggestions, blocked=blocked, suggest_label=suggest_label)


def pick_weather(conn: sqlite3.Connection, lighting_param, habitat: str = None,
                 suggestions=None, blocked=None, suggest_label: str = ""):
    """Pick weather, filtered by lighting compatibility."""
    all_weather = fetch_parameters_by_category(conn, "weather", habitat=habitat)
    sky = LIGHTING_SKY.get(lighting_param["name"], "mixed")

    compatible = []
    for w in all_weather:
        compat = WEATHER_SKY_COMPAT.get(w["name"], ("any",))
        if "any" in compat or sky in compat:
            compatible.append(w)

    if not compatible:
        compatible = all_weather  # fallback: show everything

    def fmt(r):
        return r["name"].replace("_", " ")

    return pick(f"Select WEATHER (for {lighting_param['name'].replace('_', ' ')} lighting)", compatible, fmt,
                suggestions=suggestions, blocked=blocked, suggest_label=suggest_label)


# ---------------------------------------------------------------------------
# Vary Region fix prompts — modular inpainting prompts for step 2 / 3 / 4
# ---------------------------------------------------------------------------

def validate_prompt(prompt: str, allow_mj_params: bool, label: str) -> None:
    """Raise ValueError if prompt violates its schema.

    Main prompts  (allow_mj_params=True)  — must contain at least one -- flag.
    Fix prompts   (allow_mj_params=False) — must contain no -- flags.
    """
    has_params = ' --' in prompt
    if allow_mj_params and not has_params:
        raise ValueError(f"[{label}] main prompt is missing MJ parameters (--style, --stylize, etc.)")
    if not allow_mj_params and has_params:
        import re
        found = re.findall(r'--\S+', prompt)
        raise ValueError(f"[{label}] fix prompt must not contain MJ parameters, found: {found}")


def strip_mj_params(prompt: str) -> str:
    """Remove all Midjourney parameters (--flag ...) from a prompt string.
    MJ flags are always appended at the end, so everything from the first -- onward is dropped."""
    idx = prompt.find(' --')
    return prompt[:idx].strip() if idx != -1 else prompt.strip()


def make_feet_fix_prompt(species, mj_style: str, stylize: int = 20) -> str:
    """Vary Region prompt for feet/claws/flippers/wings. Paint over extremity, paste this prompt."""
    diet    = species["diet"] or ""
    habitat = species["habitat"] or "terrestrial"
    name    = species["name"]

    if habitat == "marine":
        core = (
            f"extreme close-up of {name} flipper, paddle limb, "
            "individual digit bones visible under skin tension, wet glistening skin, "
            "natural wear on flipper tip, real wildlife photograph"
        )
    elif habitat == "aerial":
        core = (
            f"extreme close-up of {name} wing membrane, "
            "finger bones visible as structural ridges stretching taut membrane, "
            "translucent membrane with visible blood vessels backlit by sky, "
            "natural wear and small tears at trailing edge, "
            "pycnofibre texture on forearm, real wildlife photograph of bat wing reference"
        )
    elif diet in ("Carnivore", "Piscivore"):
        core = (
            f"extreme close-up of {name} foot, each toe individually separated gripping ground, "
            "recurved talons each a different length and curvature, "
            "visible knuckle joints bending under weight, "
            "dark worn keratin with cracks and chips, caked mud between digits, "
            "wrinkled leathery toe pads, komodo dragon foot reference, "
            "real wildlife photograph of reptile foot"
        )
    else:
        core = (
            f"extreme close-up of {name} foot, column-like toes weight-bearing, "
            "blunt rounded toenails with natural wear, "
            "wrinkled leathery skin at toe joints, caked mud between digits, "
            "elephant foot reference, real wildlife photograph"
        )

    flags = f"--no {NEGATIVE_PROMPT} --style {mj_style} --stylize {stylize}"
    return f"{core}, telephoto macro, shallow depth of field, muted colour, film grain {flags}"


def make_environment_fix_prompt(species, environment: str, weather_param, lighting_param,
                                 mj_style: str, stylize: int = 30) -> str:
    """Vary Region prompt for background/habitat. Paint over background, paste this prompt."""
    habitat = species["habitat"] or "terrestrial"

    if habitat == "marine":
        ground = "water surface texture, underwater light refraction, natural ocean colour"
    elif habitat == "aerial":
        ground = "real photographed sky, atmospheric haze, natural cloud formation"
    else:
        ground = "ground texture, soil and rock detail, sparse prehistoric vegetation in background"

    core = (
        f"{environment}, {ground}, "
        f"{lighting_param['value']}, {weather_param['value']}, "
        "real photographed sky with atmospheric haze at horizon, "
        "telephoto background bokeh, muted natural colour, film grain, "
        "no animal in frame, habitat only"
    )

    neg = ("painted sky, gradient sky, CGI sky, illustration, studio background, digital art, "
           "animal, dinosaur, 3D render, concept art, matte painting, hyper-saturated, volumetric god rays")
    flags = f"--no {neg} --style {mj_style} --stylize {stylize}"
    return f"{core} {flags}"


def make_mouth_fix_prompt(species, mj_style: str, stylize: int = 20) -> str:
    """Vary Region prompt for mouth/teeth. Paint over the mouth area, paste this prompt."""
    diet    = species["diet"] or ""
    habitat = species["habitat"] or "terrestrial"
    name    = species["name"]

    if habitat == "marine" and name in ("Megalodon", "Cretoxyrhina"):
        # Sharks — rows of triangular teeth, no gums like reptiles
        core = (
            f"extreme close-up of {name} open mouth, "
            "multiple rows of triangular teeth, serrated edges visible, "
            "teeth white at tip darkening toward root, replacement teeth behind front row, "
            "pink gum tissue receding at tooth base, water streaming through open jaw, "
            "real wildlife photograph, great white shark jaw reference"
        )
    elif habitat == "marine" and name == "Helicoprion":
        # Spiral tooth whorl — totally unique
        core = (
            f"extreme close-up of {name} lower jaw, "
            "spiral whorl of teeth curling under jaw like a circular saw, "
            "smallest oldest teeth at centre, largest newest at outer edge, "
            "individual teeth conical and sharp, whorl wet and glistening, "
            "no upper teeth visible, cartilaginous jaw smooth, "
            "real wildlife photograph"
        )
    elif habitat == "marine" and name == "Dunkleosteus":
        # Bony jaw blades — no true teeth
        core = (
            f"extreme close-up of {name} jaw, "
            "self-sharpening bony jaw blades instead of teeth, "
            "blades interlocking like shears, worn and chipped edges, "
            "algae growing in crevices of bony plates, "
            "armored head plates visible around jaw, water dripping from jaw edge, "
            "real wildlife photograph"
        )
    elif habitat == "marine" and name in ("Archelon", "Ammonite"):
        # Beaked species — no teeth
        core = (
            f"extreme close-up of {name} mouth, "
            "hooked beak with worn keratin edges, "
            "algae and mineral staining on beak surface, "
            "wet skin around mouth, water dripping, "
            "real wildlife photograph, sea turtle mouth reference"
        )
    elif habitat == "marine":
        # Default marine reptiles — jaw split by waterline
        core = (
            f"extreme close-up of {name} jaw at water surface, "
            "waterline crossing lower jaw, "
            "upper jaw above water sharp and dry with water droplets beading on scales, "
            "lower jaw below waterline visibly distorted by refraction, colour shifted blue-green, "
            "slightly blurred and warped through water surface, "
            "teeth individually different lengths and curvature, "
            "green algae staining on jaw skin, debris and grit caught between teeth, "
            "wet pink gum tissue visible at tooth bases, gum line receded and raw, "
            "real wildlife photograph, saltwater crocodile jaw reference"
        )
    elif diet in ("Carnivore", "Piscivore", "Filter-feeder"):
        core = (
            f"extreme close-up of {name} open jaw, "
            "each tooth a different length and curvature, "
            "yellowed and stained at base fading to off-white tip, "
            "brown decay discolouration at gum line on several teeth, "
            "fragment of bone or twig wedged between two teeth, "
            "wet pink gum tissue, gum pockets raw and slightly receded, "
            "heavy saliva stranding between upper and lower jaw, "
            "single strand of saliva catching light, "
            "flies on lip fold and nostril, animal unbothered, "
            "water or moisture glistening on chin and lower jaw skin, "
            "real wildlife photograph, saltwater crocodile jaw reference"
        )
    else:
        core = (
            f"extreme close-up of {name} mouth, "
            "grinding teeth worn flat with brown staining, "
            "uneven wear across tooth row, some teeth shorter than neighbours, "
            "wet pink gum tissue, saliva pooling at jaw hinge, "
            "plant fibre caught between molars, "
            "moisture on lips and chin, flies on nostril edge, "
            "real wildlife photograph"
        )

    flags = f"--no {NEGATIVE_PROMPT} --style {mj_style} --stylize {stylize}"
    return f"{core}, telephoto macro, shallow depth of field, muted colour, film grain {flags}"


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

def assemble_prompt(
    species,
    science,            # Row from fetch_species_science — injected into subject block
    style_param,
    lighting_param,
    camera_param,       # ignored when mode has a fixed_camera
    mood_param,
    condition_param,
    behavior_param,
    weather_param,
    required_params: list,
    global_rules: list[str],
    mj_style: str,
    stylize: int,
    chaos: int,
    quality: float,
    output_mode: str = "portrait",
    placement: tuple[str, str] = ("", ""),  # (subject_side, space_side) from select_placement()
    has_sref: bool = False,
    habitat: str = "terrestrial",
) -> str:
    mode_cfg     = OUTPUT_MODES.get(output_mode, OUTPUT_MODES["portrait"])
    full_body    = mode_cfg["full_body"]
    canvas_print = mode_cfg["canvas_print"]

    # ── SECTION 1: SUBJECT ───────────────────────────────────────────────────
    # Anatomy, pose, skin, mouth, behavior, condition, mood.
    # Richest section — MJ weights early tokens most heavily.
    # Rule: no environment, no lighting, no camera language here.

    size = species["size_class"].lower() if species["size_class"] else ""
    subject_parts = [f"{size} {species['name']}", species["description"] or ""]

    if species["notes"]:
        subject_parts.append(species["notes"])

    # Anatomy from science table
    if science and science["feathering_coverage"] and science["feathering_coverage"].lower() != "none":
        subject_parts.append(science["feathering_coverage"])
    if science and science["tail_posture"] and science["tail_posture"].lower() not in ("not applicable — pterosaur", ""):
        subject_parts.append(science["tail_posture"])  # no "tail posture:" label — reads as descriptor
    if science and science["known_coloration_evidence"]:
        ce = science["known_coloration_evidence"]
        if not any(ce.lower().startswith(p) for p in ("no direct", "no known", "unknown")):
            subject_parts.append(ce)

    # Required species params (e.g. raptor sickle claw accuracy)
    for rp in required_params:
        subject_parts.append(rp["value"])

    # Canvas species extras (pose specifics for full-body modes)
    if full_body or has_sref:
        if output_mode == "canvas":
            extra = CANVAS_SPECIES_EXTRAS.get(species["name"])
            if extra:
                subject_parts.append(extra)
        subject_parts.append("full body visible head to tail")

    # Skin texture (body surface — belongs in subject)
    if science and science["skin_texture_type"]:
        subject_parts.append(science["skin_texture_type"])

    # Mouth / teeth (body surface — diet-aware)
    diet = species["diet"] or ""
    subject_parts.append(MOUTH_TEETH_CARNIVORE if diet in ("Carnivore", "Piscivore") else MOUTH_TEETH_HERBIVORE)

    # Behavior (what the animal is doing — pose/action)
    subject_parts.append(behavior_param["value"])

    # Condition and mood (body state and demeanor)
    subject_parts.append(condition_param["value"])
    subject_parts.append(mood_param["value"])

    # Hyperrealism style anchor — appended last so it applies to the whole subject block
    subject_parts.append(style_param["value"])

    # Habitat-specific realism anchor
    habitat_realism = HABITAT_REALISM.get(habitat, HABITAT_REALISM["terrestrial"])
    subject_parts.append(habitat_realism)

    subject = ", ".join(p for p in subject_parts if p)

    # ── SECTION 2: INTERACTION ────────────────────────────────────────────────
    # Habitat-specific contact/physics block.
    # Terrestrial: feet/ground. Marine: water surface. Aerial: wing/air.
    # Mode overrides prevent repetitive compositions.
    if output_mode == "perched":
        interaction = (
            "talons gripping rocky edge, each digit wrapped around stone, "
            "wings folded tight against body, visible wing joint angles, "
            "weight settled on feet, perched posture"
        )
    elif output_mode == "underwater":
        interaction = (
            "fully submerged, water pressing against body from all sides, "
            "light filtering from surface above, suspended in open water, "
            "particulate and sediment drifting past"
        )
    elif output_mode == "surface_break":
        interaction = (
            "body erupting through water surface, spray and foam around torso, "
            "water sheeting off skin, split between air and water, "
            "surface tension breaking around body"
        )
    else:
        interaction = HABITAT_INTERACTION.get(habitat, HABITAT_INTERACTION["terrestrial"])

    # ── SECTION 3: ENVIRONMENT ────────────────────────────────────────────────
    # Habitat and period setting. Composition framing appended here.
    # No subject descriptors, no lighting language.
    period = species["period"] or "Other"
    if habitat in ("marine", "aerial"):
        env_key = f"{habitat}_{period}"
        environment = ENVIRONMENTS.get(env_key, ENVIRONMENTS.get(f"{habitat}_Other", ENVIRONMENTS["Other"]))
    else:
        environment = ENVIRONMENTS.get(period, ENVIRONMENTS["Other"])

    # Anti-CGI anchor — force real-location photography feel on every background
    environment = f"{environment}, real outdoor location, imperfect natural detail, uneven terrain"

    comp_template = mode_cfg["composition"]
    if comp_template == "PLACEMENT":
        subject_phrase, space_side = placement
        if subject_phrase == "dead_center":
            comp = "animal centred, symmetrical, horizon visible"
        elif space_side in ("right", "left"):
            comp = f"{subject_phrase}, negative space {space_side}, horizon visible"
        else:
            comp = f"{subject_phrase}, horizon visible"
        environment = f"{environment}, {comp}"
    elif comp_template:
        environment = f"{environment}, {comp_template}"

    # ── SECTION 4: LIGHTING ───────────────────────────────────────────────────
    # One lighting condition + one weather phrase. Short and supportive.
    lighting = f"{lighting_param['value']}, {weather_param['value']}"

    # ── SECTION 5: CAMERA ─────────────────────────────────────────────────────
    # Minimal — lens spec only. Everything else is in sections 1–4.
    camera_text = mode_cfg["fixed_camera"] or camera_param["value"]
    camera = f"shot on {camera_text}"

    # ── ASSEMBLE ──────────────────────────────────────────────────────────────
    sections = [subject, interaction, environment, lighting, camera]
    if canvas_print:
        sections.append(CANVAS_PRINT)

    # Deduplication — strip exact repeated clauses that can arise from overlapping params
    seen, deduped_clauses = set(), []
    for clause in ", ".join(s for s in sections if s).split(", "):
        key = clause.strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped_clauses.append(clause.strip())

    prose = ", ".join(deduped_clauses)

    # ── MJ FLAGS ──────────────────────────────────────────────────────────────
    neg = NEGATIVE_PROMPT
    if output_mode == "perched":
        # Perched mode: don't block folded wings or grounded poses
        habitat_neg = ""
    else:
        habitat_neg = HABITAT_NEGATIVE.get(habitat, "")
    if habitat_neg:
        neg = f"{neg}, {habitat_neg}"
    flags = f"--no {neg} --style {mj_style} --stylize {stylize} --q {quality:g}"
    if chaos > 0:
        flags += f" --chaos {chaos}"

    return f"{prose} {flags}"


def make_title(species, mood_param, output_mode: str = "portrait") -> str:
    name = species["common_name"] or species["name"]
    mode_display = OUTPUT_MODES.get(output_mode, {}).get("display", output_mode).lower()
    suffix = mode_display if output_mode != "portrait" else mood_param["name"].replace("_", " ")
    return f"{name} — {suffix}"


def make_tags(species, style_param, lighting_param, camera_param, mood_param,
              condition_param, behavior_param, weather_param, output_mode: str = "portrait") -> str:
    parts = []
    if species["period"]:
        parts.append(species["period"].lower())
    for p in (style_param, lighting_param, mood_param):
        parts.append(p["name"])
    parts.append(camera_param["name"] if camera_param else output_mode)
    parts.append(condition_param["name"])
    parts.append(behavior_param["name"])
    parts.append(weather_param["name"])
    parts.append(output_mode)
    return ",".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def display_reference_scan() -> None:
    """Print a startup report of reference images loaded per species."""
    counts = scan_reference_images()
    if not counts:
        print(f"  {dim('[reference] species_reference/ folder not found — skipping image scan')}")
        return
    total = sum(counts.values())
    loaded = sum(1 for c in counts.values() if c > 0)
    print(f"\n  {hdr(f'REFERENCE IMAGES  ({loaded}/{len(counts)} species loaded, {total} total)')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for folder, count in counts.items():
        display_name = folder.replace("_", " ").title()
        bar = f"{C.CYAN}" + "█" * min(count, 20) + C.RESET
        if count:
            status = ok(f"{count:>3} image{'s' if count != 1 else ' '}")
        else:
            status = dim("  — no images yet")
        print(f"  {C.WHITE}{display_name:<22}{C.RESET} {status}  {bar}")
    print()


def display_science_brief(species, science, notes: list) -> None:
    """Print a field-guide summary and research notes for the selected species."""
    name = species["name"]
    print(f"\n  {hdr(f'SPECIES BRIEF — {name}')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)

    if science and any(science):
        length  = f"{science['body_length_m']}m" if science["body_length_m"] else "unknown"
        mass    = f"{science['body_mass_kg']:,.0f} kg" if science["body_mass_kg"] else "unknown"
        loco    = science["locomotion_type"] or "unknown"
        feather = science["feathering_coverage"] or "unknown"
        print(f"  {C.WHITE}Length:{C.RESET} {length:<10} {C.WHITE}Mass:{C.RESET} {mass:<14} {C.WHITE}Locomotion:{C.RESET} {loco}")
        if science["skin_texture_type"]:
            print(f"  {C.WHITE}Skin:{C.RESET}   {science['skin_texture_type']}")
        if science["feathering_coverage"]:
            print(f"  {C.WHITE}Feathering:{C.RESET} {feather}")
        if science["tail_posture"]:
            print(f"  {C.WHITE}Tail posture:{C.RESET} {science['tail_posture']}")
        if science["wrist_position"]:
            print(f"  {C.WHITE}Wrist:{C.RESET} {science['wrist_position']}")

        update_year = science["last_scientific_update"]
        if update_year:
            if update_year < OUTDATED_THRESHOLD:
                print(f"  {warn(f'⚠  Last updated {update_year} — check for more recent observations')}")
            else:
                print(f"  {dim(f'Last updated: {update_year}')}")

    prompt_notes = [n for n in notes if n["affects_prompt"]]
    all_notes    = [n for n in notes if not n["affects_prompt"]]

    if prompt_notes:
        print(f"\n  {hdr(f'PROMPT-RELEVANT FINDINGS ({len(prompt_notes)})')}")
        for n in prompt_notes:
            year_tag = f"[{n['year']}] " if n["year"] else ""
            author   = f"{n['author']} — " if n["author"] else ""
            snippet  = n['finding'][:100] + ('…' if len(n['finding']) > 100 else '')
            print(f"  {C.YELLOW}!{C.RESET}  {dim(year_tag + author)}{C.WHITE}{snippet}{C.RESET}")

    if all_notes:
        print(f"  {dim(f'Background notes: {len(all_notes)} (not prompt-affecting)')}")

    print()


def print_prompt_box(prompt_text: str) -> None:
    """Word-wrap and box the final prompt in bright white with a bold border."""
    border_top    = f"  {C.BOLD_CYAN}┌{'─' * 62}┐{C.RESET}"
    border_bottom = f"  {C.BOLD_CYAN}└{'─' * 62}┘{C.RESET}"
    print(border_top)
    words, line = prompt_text.split(), ""
    lines = []
    for word in words:
        if len(line) + len(word) + 1 > 60:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    for l in lines:
        print(f"  {C.BOLD_CYAN}│{C.RESET}  {C.BRIGHT_WHITE}{l:<60}{C.RESET}{C.BOLD_CYAN}│{C.RESET}")
    print(border_bottom)


SREF_FILE = Path(__file__).parent / "sref_urls.json"


def load_sref_urls() -> dict:
    """Load species → [url, ...] mapping from sref_urls.json."""
    if not SREF_FILE.exists():
        return {}
    with open(SREF_FILE) as f:
        return json.load(f)


def prompt_sref_suggestion(species_name: str):
    """After species select, offer known --sref URLs if any exist. Returns URL or None."""
    urls = load_sref_urls()
    species_urls = urls.get(species_name, [])
    if not species_urls:
        return None

    print(f"\n  {hdr(f'STYLE REFERENCES — {species_name}')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for i, entry in enumerate(species_urls, 1):
        if isinstance(entry, dict):
            label = entry.get("label", f"Reference {i}")
            url = entry["url"]
        else:
            label = f"Reference {i}"
            url = entry
        short_url = url[:50] + "…" if len(url) > 50 else url
        print(f"  {C.DIM}{i:>2}.{C.RESET}  {C.BRIGHT_WHITE}{label}{C.RESET}")
        print(f"      {dim(short_url)}")
    print(f"  {C.DIM} 0.{C.RESET}  {C.WHITE}Skip — no style reference{C.RESET}")

    while True:
        try:
            raw = input(f"\n  {hdr('Choose 0–' + str(len(species_urls)) + ':')}  ").strip()
            choice = int(raw)
            if choice == 0:
                return None
            if 1 <= choice <= len(species_urls):
                entry = species_urls[choice - 1]
                url = entry["url"] if isinstance(entry, dict) else entry
                label = entry.get("label", f"Reference {choice}") if isinstance(entry, dict) else f"Reference {choice}"
                print(f"  {ok('✓')} {ok(label)}")
                return url
        except (ValueError, EOFError):
            pass
        print(f"  {warn('Invalid choice — try again')}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactively build a Midjourney dinosaur art prompt."
    )
    parser.add_argument("--db",       type=Path,  default=DB_DEFAULT, metavar="PATH")
    # --version intentionally removed: set MJ model version in Midjourney settings
    parser.add_argument("--style",    default="raw",  choices=["raw", "default"], help="--style flag (default: raw)")
    # --ar intentionally removed: set aspect ratio globally in Midjourney settings
    parser.add_argument("--stylize",  type=int,   default=100,  metavar="N",   help="--stylize 0-1000 (default: 100)")
    parser.add_argument("--chaos",    type=int,   default=0,    metavar="N",   help="--chaos 0-100 (default: 0)")
    parser.add_argument("--quality",  type=float, default=1.0,  choices=[0.25, 0.5, 1.0], help="--q (default: 1.0)")
    parser.add_argument("--sref",     type=str,   default=None, metavar="URL", help="Style reference image URL appended as --sref")
    parser.add_argument("--cref",     type=str,   default=None, metavar="URL", help="Character reference image URL appended as --cref")
    args = parser.parse_args()

    conn = connect(args.db)
    global_rules = fetch_global_rules(conn)

    # --- Startup banner ---
    print(f"\n{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}DINOSAUR ART PROMPT GENERATOR{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")

    # --- Startup: reference image scan ---
    display_reference_scan()

    # --- Habitat selection (first thing the user sees) ---
    habitat = select_habitat()

    # --- Mode selection (filtered by habitat) ---
    output_mode = select_mode(habitat)
    mode_cfg    = OUTPUT_MODES[output_mode]

    placement: tuple[str, str] = ("", "")
    if mode_cfg["needs_placement"]:
        placement = select_canvas_placement()

    # --- Species (filtered by habitat) ---
    species = pick_species(conn, habitat)
    science = fetch_species_science(conn, species["id"])
    notes   = fetch_research_notes(conn, species["id"])
    display_science_brief(species, science, notes)

    # --- Style reference suggestion (only if --sref not already passed) ---
    if not args.sref:
        suggested_sref = prompt_sref_suggestion(species["name"])
        if suggested_sref:
            args.sref = suggested_sref

    required_params = fetch_species_required_params(conn, species["id"])
    if required_params:
        sname = species["name"]
        nrp   = len(required_params)
        print(f"\n  {ok(f'AUTO-APPLIED — {nrp} required parameter(s) for {sname}')}:")
        for rp in required_params:
            cat, pname = rp["category"], rp["name"]
            print(f"    {ok('+')} {dim(f'[{cat}]')} {C.WHITE}{pname}{C.RESET}")
    if mode_cfg["full_body"] and species["name"] in CANVAS_SPECIES_EXTRAS:
        sname = species["name"]
        extra_preview = CANVAS_SPECIES_EXTRAS[sname][:80]
        print(f"  {ok('AUTO-APPLIED')} {dim(f'(full-body extras for {sname})')}:")
        print(f"    {ok('+')} {dim('[anatomy]')} {C.WHITE}{extra_preview}{C.RESET}")

    # Style is always hyperrealism — hardcoded, not user-selectable
    style_param = HYPERREALISM_STYLE

    # Context — tracks selections for branching suggestions + invalid combo blocking (all habitats)
    ctx = {
        "habitat":      habitat,
        "species_name": species["name"],
        "diet":         species["diet"] or "",
        "size_class":   species["size_class"] or "",
        "output_mode":  output_mode,
        "lighting": None, "mood": None, "behavior": None,
        "condition": None, "weather": None,
    }

    def _cpick(category, slabel=""):
        """Inject context-reactive suggestions + invalid combo blocking into pick_parameter."""
        sug = get_suggestions(category, ctx)
        blk = get_blocked(category, ctx)
        return pick_parameter(conn, category, name_only=True, habitat=habitat,
                              suggestions=sug, blocked=blk, suggest_label=slabel)

    lighting_param = _cpick("lighting", f"for {species['name']}")
    ctx["lighting"] = lighting_param["name"]

    # Camera: only ask if the mode doesn't fix its own camera
    if mode_cfg["fixed_camera"] is None:
        camera_param = _cpick("camera", f"for {mode_cfg['display'].lower()} mode")
    else:
        camera_param = None
        mode_display = mode_cfg["display"]
        cam_preview  = mode_cfg["fixed_camera"][:80]
        print(f"  {hdr('CAMERA')} {dim(f'(fixed for {mode_display})')}")
        print(f"  {dim(cam_preview)}\n")

    mood_param = _cpick("mood", f"for {lighting_param['name'].replace('_', ' ')} lighting")
    ctx["mood"] = mood_param["name"]

    condition_param = _cpick("condition", f"for {species['name']} · {mood_param['name'].replace('_', ' ')}")
    ctx["condition"] = condition_param["name"]

    behavior_param = _cpick("behavior", f"for {mood_param['name'].replace('_', ' ')} mood")
    ctx["behavior"] = behavior_param["name"]

    # Weather: filtered by lighting sky-state + context-reactive suggestions + blocking
    weather_sug = get_suggestions("weather", ctx)
    weather_blk = get_blocked("weather", ctx)
    weather_param = pick_weather(conn, lighting_param, habitat=habitat,
                                 suggestions=weather_sug, blocked=weather_blk,
                                 suggest_label=f"for {mood_param['name'].replace('_', ' ')} mood")
    ctx["weather"] = weather_param["name"]

    # --- Build prompt ---
    prompt_text = assemble_prompt(
        species, science, style_param, lighting_param, camera_param, mood_param,
        condition_param=condition_param,
        behavior_param=behavior_param,
        weather_param=weather_param,
        required_params=required_params,
        global_rules=global_rules,
        mj_style=args.style,
        stylize=args.stylize,
        chaos=args.chaos,
        quality=args.quality,
        output_mode=output_mode,
        placement=placement,
        has_sref=bool(args.sref),
        habitat=habitat,
    )

    title = make_title(species, mood_param, output_mode=output_mode)
    tags  = make_tags(species, style_param, lighting_param, camera_param, mood_param,
                      condition_param=condition_param, behavior_param=behavior_param,
                      weather_param=weather_param, output_mode=output_mode)

    # --- Append reference URLs to prompt ---
    if args.sref:
        prompt_text += f" --sref {args.sref}"
    if args.cref:
        prompt_text += f" --cref {args.cref}"

    # --- Build fix prompts ---
    period = species["period"] or "Other"
    if habitat in ("marine", "aerial"):
        env_key     = f"{habitat}_{period}"
        environment = ENVIRONMENTS.get(env_key, ENVIRONMENTS.get(f"{habitat}_Other", ENVIRONMENTS["Other"]))
    else:
        environment = ENVIRONMENTS.get(period, ENVIRONMENTS["Other"])

    feet_fix_prompt = make_feet_fix_prompt(species, mj_style=args.style)
    env_fix_prompt  = make_environment_fix_prompt(
        species, environment, weather_param, lighting_param, mj_style=args.style
    )

    # --- Display ---
    mode_label = mode_cfg["display"].upper()

    # STEP 1 — Main prompt
    habitat_label = habitat.upper()
    print(f"\n{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}STEP 1 — MAIN PROMPT{C.RESET}  {C.DIM}[{habitat_label} / {mode_label}]{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"\n  {C.WHITE}Title :{C.RESET} {C.BRIGHT_WHITE}{title}{C.RESET}")
    print(f"  {C.WHITE}Tags  :{C.RESET} {dim(tags)}")
    if args.sref:
        print(f"  {C.WHITE}sref  :{C.RESET} {dim(args.sref)}")
    if args.cref:
        print(f"  {C.WHITE}cref  :{C.RESET} {dim(args.cref)}")
    print()
    validate_prompt(prompt_text, allow_mj_params=True,  label="STEP 1 main")
    print_prompt_box(prompt_text)
    print(f"\n  {hdr('/imagine prompt:')}")
    print(f"  {C.BRIGHT_WHITE}{prompt_text}{C.RESET}\n")

    # STEP 2 — Extremity fix (feet / flipper / wing)
    step2_labels = {"terrestrial": ("FEET FIX", "feet"), "marine": ("FLIPPER FIX", "flippers"), "aerial": ("WING FIX", "wings")}
    step2_title, step2_region = step2_labels.get(habitat, step2_labels["terrestrial"])
    feet_fix_clean = strip_mj_params(feet_fix_prompt)
    validate_prompt(feet_fix_clean, allow_mj_params=False, label=f"STEP 2 {step2_region} fix")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}STEP 2 — {step2_title}{C.RESET}  {C.DIM}[Vary Region → paint over {step2_region}]{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print_prompt_box(feet_fix_clean)
    print(f"\n  {hdr('/imagine prompt:')}")
    print(f"  {C.BRIGHT_WHITE}{feet_fix_clean}{C.RESET}\n")

    # STEP 3 — Environment fix
    env_fix_clean = strip_mj_params(env_fix_prompt)
    validate_prompt(env_fix_clean, allow_mj_params=False, label="STEP 3 environment fix")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}STEP 3 — ENVIRONMENT FIX{C.RESET}  {C.DIM}[Vary Region → paint over background]{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print_prompt_box(env_fix_clean)
    print(f"\n  {hdr('/imagine prompt:')}")
    print(f"  {C.BRIGHT_WHITE}{env_fix_clean}{C.RESET}\n")

    # STEP 4 — Mouth fix
    mouth_fix_prompt = make_mouth_fix_prompt(species, mj_style=args.style)
    mouth_fix_clean  = strip_mj_params(mouth_fix_prompt)
    validate_prompt(mouth_fix_clean, allow_mj_params=False, label="STEP 4 mouth fix")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}STEP 4 — MOUTH FIX{C.RESET}  {C.DIM}[Vary Region → paint over mouth/jaw]{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print_prompt_box(mouth_fix_clean)
    print(f"\n  {hdr('/imagine prompt:')}")
    print(f"  {C.BRIGHT_WHITE}{mouth_fix_clean}{C.RESET}\n")

    # --- Save ---
    saved_param_ids = (
        [rp["id"] for rp in required_params]
        + [HYPERREALISM_STYLE["id"], lighting_param["id"], mood_param["id"],
           condition_param["id"], behavior_param["id"], weather_param["id"]]
        + ([camera_param["id"]] if camera_param else [])
    )
    prompt_id = save_prompt(
        conn,
        species_id=species["id"],
        title=title,
        positive_prompt=prompt_text,
        tags=tags,
        parameter_ids=saved_param_ids,
    )
    print(f"  {ok(f'✓ Saved — prompt id={prompt_id}, status=pending')}")
    print()


if __name__ == "__main__":
    main()
