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
import random
import sqlite3
import sys
from pathlib import Path

from species import get_anatomy, build_anatomy_prompt, build_anatomy_negative

WIDE_SCALE_VARIANTS = ["wide shot"]

# Output modes that are inherently wide/landscape-dominant.
# These auto-activate wide_mode in assemble_prompt() so the subject reads
# small in frame and the environment dominates — critical for canvas prints.
WIDE_MODES = {"environmental", "valley_panorama", "ridgeline_silhouette", "river_crossing", "misty_dawn", "storm_front"}

# Group modes — multiple same-species animals. Subject lead gets explicit
# count, anatomy forced to "wide" level, "full body head to tail" suppressed.
GROUP_MODES = {"group_herd", "family_group", "waterhole_gather", "migration_march"}

# ---------------------------------------------------------------------------
# Camera perspective — angle override independent of output mode.
# ---------------------------------------------------------------------------
CAMERA_PERSPECTIVES = {
    "default": {
        "display": "Default (mode's built-in angle)",
        "lead":    "",
    },
    "drone_overhead": {
        "display": "Drone / bird's-eye — straight down",
        "lead":    "drone photograph looking straight down from 30m altitude, top-down bird's-eye view, no horizon, dorsal surface of animal visible",
    },
    "drone_angled": {
        "display": "Drone / elevated 45° — angled down",
        "lead":    "drone photograph from 20m altitude at 45-degree angle looking down, elevated perspective, ground visible around animal, slight horizon",
    },
    "epic_aerial": {
        "display": "Epic aerial — vast landscape, animal small in frame",
        "lead":    "epic aerial photograph from 200m altitude, vast sweeping landscape dominates the frame, ultra-wide establishing shot, animals tiny in the environment, enormous scale, cinematic landscape photography, shot on ultra-wide 14mm lens",
    },
    "ground_level": {
        "display": "Ground level — eye height with animal",
        "lead":    "camera at animal eye level on the ground, low angle, ground surface visible in foreground, horizon at eye height",
    },
    "low_upward": {
        "display": "Low angle — looking up at animal",
        "lead":    "camera on ground looking up at animal from below, extreme low angle, animal towering above, sky visible behind",
    },
    "hide_blind": {
        "display": "Hide / blind — concealed, peering through cover",
        "lead":    "photograph from wildlife hide, camera partially obscured by vegetation in foreground, candid unaware angle, telephoto compression",
    },
}

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
    # Arthropod — forest floor / swamp / underwater depending on species
    "arthropod_Cambrian":  "shallow Cambrian sea floor, sandy bottom, microbial mat, murky water",
    "arthropod_Ordovician":"shallow Ordovician sea, rocky bottom, scattered shells, dim filtered light",
    "arthropod_Silurian":  "warm Silurian coastal water, sandy substrate, early coral formations",
    "arthropod_Devonian":  "dark Devonian coastal shallows, rocky reef, murky green water",
    "arthropod_Carboniferous":"dense Carboniferous swamp forest floor, giant ferns, fallen logs, humid mist, rotting vegetation",
    "arthropod_Other":     "prehistoric forest floor, damp leaf litter, rotting logs, fern undergrowth",
    # Plant — forest / swamp environments
    "plant_Devonian":      "early Devonian floodplain, bare rocky soil, scattered pioneer vegetation, shallow pools",
    "plant_Carboniferous": "dense Carboniferous coal swamp, standing water between roots, thick humid air, fern undergrowth",
    "plant_Permian":       "dry Permian floodplain, sandy soil, scattered vegetation, seasonal drought",
    "plant_Jurassic":      "lush Jurassic forest, dense fern undergrowth, dappled light, rich soil",
    "plant_Cretaceous":    "Cretaceous river bank, sandy alluvial soil, early flowering ground cover, warm humid air",
    "plant_Other":         "prehistoric landscape, rich soil, scattered vegetation",
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
    "eye_contact":    ["closeup_portrait","jaw_level",         "murk_emerge",       "tight_head",         "detail_abstract"],
    "jaws_detail":    ["jaw_level",       "closeup_portrait",  "below_looking_up",  "murk_emerge",        "detail_abstract"],
    "confrontation":  ["jaw_level",       "murk_emerge",       "below_looking_up",  "chase_behind",       "closeup_portrait"],
    "valley_panorama":["distant_surface", "above_looking_down","underwater_wide",   "split_waterline",    "swim_alongside"],
    "misty_dawn":     ["distant_surface", "above_looking_down","swim_alongside",    "split_waterline",    "underwater_wide"],
    "storm_front":    ["distant_surface", "split_waterline",   "above_looking_down","surface_skim",       "breach_freeze"],
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
    "eye_contact":      ["closeup_portrait", "tight_head",        "telephoto_compress", "hidden_blind",      "detail_abstract"],
    "jaws_detail":      ["tight_head",       "closeup_portrait",  "dynamic_low",        "detail_abstract",   "ground_level_up"],
    "action_freeze":    ["dynamic_low",      "tracking_pan",      "walking_toward",     "ground_level_up",   "dust_level"],
    "tracking_side":    ["tracking_pan",     "telephoto_compress","full_body_profile",  "trail_camera",      "dust_level"],
    "ground_level":     ["ground_level_up",  "dynamic_low",       "dust_level",         "walking_toward",    "trail_camera"],
    "confrontation":    ["walking_toward",   "dynamic_low",       "ground_level_up",    "closeup_portrait",  "dust_level"],
    "valley_panorama":  ["epic_wide",        "aerial_above",      "telephoto_compress", "waterhole_edge",    "silhouette_ridge"],
    "ridgeline_silhouette":["silhouette_ridge","epic_wide",       "telephoto_compress", "trail_camera",      "waterhole_edge"],
    "river_crossing":   ["epic_wide",        "waterhole_edge",    "trail_camera",       "telephoto_compress","tracking_pan"],
    "misty_dawn":       ["epic_wide",        "telephoto_compress","trail_camera",       "hidden_blind",      "waterhole_edge"],
    "storm_front":      ["epic_wide",        "silhouette_ridge",  "trail_camera",       "telephoto_compress","aerial_above"],
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
    "eye_contact":     ["closeup_portrait","tight_head",      "cliff_perch",       "wing_detail",       "detail_abstract"],
    "soaring_thermal": ["below_up_wings",  "thermal_circle",  "flight_tracking",   "sunrise_silhouette","cloud_frame"],
    "dive_strike":     ["stoop_above",     "head_on_approach","banking_turn",      "flight_tracking",   "below_up_wings"],
    "action_freeze":   ["stoop_above",     "head_on_approach","banking_turn",      "below_up_wings",    "parallel_flight"],
    "extreme_closeup": ["wing_detail",     "detail_abstract", "tight_head",        "cliff_perch",       "closeup_portrait"],
    "valley_panorama": ["distant_speck",   "cloud_frame",     "thermal_circle",    "sunrise_silhouette","flight_tracking"],
    "ridgeline_silhouette":["sunrise_silhouette","distant_speck","cloud_frame",    "thermal_circle",    "below_up_wings"],
    "misty_dawn":      ["distant_speck",   "cloud_frame",     "sunrise_silhouette","thermal_circle",    "flight_tracking"],
    "storm_front":     ["distant_speck",   "cloud_frame",     "sunrise_silhouette","stoop_above",       "thermal_circle"],
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
# Arthropod context-reactive branching (Session 17)
# ---------------------------------------------------------------------------

# Arthropods split into two locomotion groups:
#   aquatic: Anomalocaris, Eurypterus, Megalograptus, Jaekelopterus, Megarachne (eurypterids)
#   terrestrial: Meganeura, Arthropleura, Pulmonoscorpius
AQUATIC_ARTHROPODS = {"Anomalocaris", "Eurypterus", "Megalograptus", "Jaekelopterus", "Megarachne"}
TERRESTRIAL_ARTHROPODS = {"Meganeura", "Arthropleura", "Pulmonoscorpius"}

ARTHROPOD_LIGHTING_BY_SPECIES = {
    # Terrestrial arthropods — forest floor / swamp
    "Meganeura":       ["dappled_canopy",  "golden_hour",      "dawn_first_light",  "backlit_haze",      "broken_cloud"],
    "Arthropleura":    ["forest_floor_shade","dappled_canopy", "overcast",           "dawn_first_light",  "fog_diffuse"],
    "Pulmonoscorpius": ["dramatic_rim",     "moonlit",         "dawn_first_light",   "forest_floor_shade","dust_glow"],
    # Aquatic arthropods — underwater
    "Anomalocaris":    ["underwater_caustics","reef_scatter",   "noon_column",        "murk_glow",         "surface_dapple"],
    "Eurypterus":      ["reef_scatter",     "underwater_caustics","murk_glow",        "surface_dapple",    "noon_column"],
    "Megalograptus":   ["murk_glow",        "underwater_caustics","deep_water_fade",  "reef_scatter",      "noon_column"],
    "Jaekelopterus":   ["murk_glow",        "deep_water_fade",  "underwater_caustics","noon_column",       "bioluminescent"],
    "Megarachne":      ["forest_floor_shade","dappled_canopy", "murk_glow",          "overcast",          "dawn_first_light"],
}

ARTHROPOD_MOOD_BY_LIGHTING = {
    "dappled_canopy":     ["quiet_power",     "feeding_focus",    "alert_scan",        "serene",            "scent_tracking"],
    "forest_floor_shade": ["quiet_power",     "scent_tracking",   "alert_scan",        "feeding_focus",     "serene"],
    "golden_hour":        ["heat_rest",       "serene",           "feeding_focus",      "quiet_power",       "alert_scan"],
    "dawn_first_light":   ["alert_scan",      "quiet_power",      "serene",            "feeding_focus",     "scent_tracking"],
    "overcast":           ["quiet_power",     "feeding_focus",    "alert_scan",         "serene",            "mid_stride"],
    "dramatic_rim":       ["menacing",        "quiet_power",      "alert_scan",         "feeding_focus",     "territorial_hold"],
    "moonlit":            ["scent_tracking",  "alert_scan",       "quiet_power",        "menacing",          "serene"],
    "fog_diffuse":        ["quiet_power",     "scent_tracking",   "alert_scan",         "serene",            "feeding_focus"],
    "backlit_haze":       ["quiet_power",     "serene",           "feeding_focus",      "alert_scan",        "eye_contact"],
    "broken_cloud":       ["feeding_focus",   "mid_stride",       "alert_scan",         "quiet_power",       "serene"],
    "dust_glow":          ["heat_rest",       "quiet_power",      "feeding_focus",      "territorial_hold",  "menacing"],
    # Aquatic arthropod lighting
    "underwater_caustics":["feeding_focus",   "quiet_power",      "alert_scan",         "serene",            "eye_contact"],
    "reef_scatter":       ["feeding_focus",   "quiet_power",      "serene",             "alert_scan",        "eye_contact"],
    "noon_column":        ["feeding_focus",   "quiet_power",      "alert_scan",         "mid_stride",        "menacing"],
    "murk_glow":          ["menacing",        "quiet_power",      "alert_scan",         "feeding_focus",     "scent_tracking"],
    "surface_dapple":     ["quiet_power",     "serene",           "feeding_focus",      "alert_scan",        "mid_stride"],
    "deep_water_fade":    ["menacing",        "quiet_power",      "scent_tracking",     "alert_scan",        "serene"],
    "bioluminescent":     ["quiet_power",     "serene",           "menacing",           "alert_scan",        "scent_tracking"],
}

ARTHROPOD_BEHAVIOR_BY_MOOD = {
    "feeding_focus":  ["feeding",           "scanning_territory","standing_still",    "mid_stride",        "emerging_from_cover"],
    "quiet_power":    ["standing_still",    "scanning_territory","mid_stride",        "resting_alert",     "emerging_from_cover"],
    "alert_scan":     ["scanning_territory","standing_still",    "emerging_from_cover","resting_alert",    "mid_stride"],
    "serene":         ["resting_alert",     "standing_still",    "basking_flat",      "post_rain_stillness","feeding"],
    "menacing":       ["scanning_territory","mid_stride",        "standing_still",    "emerging_from_cover","feeding"],
    "heat_rest":      ["basking_flat",      "resting_alert",     "standing_still",    "post_rain_stillness","shaking_off_water"],
    "scent_tracking": ["scanning_territory","emerging_from_cover","mid_stride",       "standing_still",    "resting_alert"],
    "mid_stride":     ["mid_stride",        "scanning_territory","standing_still",    "emerging_from_cover","feeding"],
    "territorial_hold":["scanning_territory","standing_still",   "mid_stride",        "emerging_from_cover","resting_alert"],
    "eye_contact":    ["standing_still",    "scanning_territory","resting_alert",     "emerging_from_cover","feeding"],
}

ARTHROPOD_CONDITION_BY_SPECIES = {
    "Meganeura":       ["pristine_juvenile","dominant_prime",    "torn_wing_edge",    "dust_on_wings",     "dew_droplets"],
    "Arthropleura":    ["dominant_prime",   "weathered_adult",   "mud_caked",         "moulting_skin",     "battle_scarred"],
    "Pulmonoscorpius": ["dominant_prime",   "battle_scarred",    "weathered_adult",   "mud_caked",         "pristine_juvenile"],
    "Anomalocaris":    ["dominant_prime",   "pristine_juvenile", "weathered_adult",   "battle_scarred",    "algae_growth"],
    "Eurypterus":      ["dominant_prime",   "pristine_juvenile", "weathered_adult",   "battle_scarred",    "algae_growth"],
    "Megalograptus":   ["dominant_prime",   "battle_scarred",    "weathered_adult",   "pristine_juvenile", "algae_growth"],
    "Jaekelopterus":   ["dominant_prime",   "battle_scarred",    "weathered_adult",   "mud_caked",         "algae_growth"],
    "Megarachne":      ["dominant_prime",   "weathered_adult",   "mud_caked",         "battle_scarred",    "pristine_juvenile"],
}

ARTHROPOD_CAMERA_BY_MODE = {
    "portrait":        ["closeup_portrait", "tight_head",       "detail_abstract",   "ground_level_up",   "medium_shot"],
    "canvas":          ["full_body_profile","ground_level_up",  "dynamic_low",       "rear_three_quarter","trail_camera"],
    "environmental":   ["epic_wide",        "ground_level_up",  "trail_camera",       "aerial_above",     "medium_shot"],
    "extreme_closeup": ["detail_abstract",  "tight_head",       "ground_level_up",   "closeup_portrait",  "medium_shot"],
    "eye_contact":     ["closeup_portrait", "tight_head",       "ground_level_up",   "detail_abstract",   "medium_shot"],
    "action_freeze":   ["dynamic_low",      "ground_level_up",  "medium_shot",       "trail_camera",      "detail_abstract"],
    "tracking_side":   ["ground_level_up",  "medium_shot",      "full_body_profile", "trail_camera",      "dynamic_low"],
    "ground_level":    ["ground_level_up",  "dynamic_low",      "detail_abstract",   "trail_camera",      "medium_shot"],
    "confrontation":   ["ground_level_up",  "dynamic_low",      "closeup_portrait",  "detail_abstract",   "medium_shot"],
}

ARTHROPOD_WEATHER_BY_MOOD = {
    "feeding_focus":    ["humid_haze",      "clear_pristine",   "overcast_flat",     "ground_mist",       "drizzle_steady"],
    "quiet_power":      ["clear_pristine",  "ground_mist",      "overcast_flat",     "humid_haze",        "heat_haze"],
    "alert_scan":       ["ground_mist",     "clear_pristine",   "cold_fog",          "overcast_flat",     "humid_haze"],
    "serene":           ["clear_pristine",  "ground_mist",      "humid_haze",        "overcast_flat",     "rain_clearing"],
    "menacing":         ["storm_approaching","ground_mist",     "cold_fog",           "overcast_flat",     "humid_haze"],
    "heat_rest":        ["heat_haze",       "hot_still_air",    "humid_haze",         "clear_pristine",   "overcast_flat"],
    "scent_tracking":   ["ground_mist",     "cold_fog",         "humid_haze",         "rain_clearing",    "clear_pristine"],
    "mid_stride":       ["clear_pristine",  "overcast_flat",    "ground_mist",        "humid_haze",       "wind_gusts_dry"],
    "territorial_hold": ["clear_pristine",  "heat_haze",        "ground_mist",        "overcast_flat",    "humid_haze"],
    "eye_contact":      ["clear_pristine",  "overcast_flat",    "ground_mist",        "humid_haze",       "cold_fog"],
}

ARTHROPOD_INVALID_COMBOS = [
    # Basking ↔ nocturnal/storm
    ("behavior", "basking_flat",     "lighting", "moonlit",           "basking needs sunlight — moonlit contradicts"),
    ("behavior", "basking_flat",     "weather",  "storm_approaching", "basking — approaching storm contradicts"),
    ("behavior", "basking_flat",     "mood",     "menacing",          "basking — too passive for menacing mood"),
    # Active behaviors ↔ passive moods
    ("behavior", "mid_stride",       "mood",     "heat_rest",         "active locomotion — contradicts heat rest"),
    ("behavior", "feeding",          "mood",     "heat_rest",         "actively feeding — contradicts passive heat rest"),
    ("behavior", "scanning_territory","mood",    "heat_rest",         "actively scanning — contradicts passive heat rest"),
]


def get_arthropod_suggestions(category: str, context: dict) -> list:
    """Context-reactive suggestions for arthropod habitat."""
    if context.get("habitat") != "arthropod":
        return []

    species_name = context.get("species_name", "")
    output_mode  = context.get("output_mode", "")
    lighting     = context.get("lighting")
    mood         = context.get("mood")
    behavior     = context.get("behavior")

    if category == "lighting":
        return ARTHROPOD_LIGHTING_BY_SPECIES.get(species_name, [])

    if category == "mood":
        base = list(ARTHROPOD_MOOD_BY_LIGHTING.get(lighting, []))
        # Predatory arthropods bias toward menacing/hunting moods
        if species_name in ("Jaekelopterus", "Megalograptus", "Anomalocaris", "Pulmonoscorpius"):
            priority = [m for m in ["menacing", "feeding_focus", "alert_scan", "territorial_hold", "quiet_power"] if m in base]
            rest = [m for m in base if m not in priority]
            base = priority + rest
        return base[:5]

    if category == "behavior":
        return ARTHROPOD_BEHAVIOR_BY_MOOD.get(mood, [])

    if category == "condition":
        return ARTHROPOD_CONDITION_BY_SPECIES.get(species_name, [])[:5]

    if category == "camera":
        return ARTHROPOD_CAMERA_BY_MODE.get(output_mode, [])[:5]

    if category == "weather":
        return ARTHROPOD_WEATHER_BY_MOOD.get(mood, [])[:5]

    return []


def get_arthropod_blocked(category: str, context: dict) -> dict:
    """Invalid combo blocking for arthropod habitat."""
    if context.get("habitat") != "arthropod":
        return {}

    blocked = {}
    for cat_a, name_a, cat_b, name_b, reason in ARTHROPOD_INVALID_COMBOS:
        if cat_b == category and context.get(cat_a) == name_a:
            blocked.setdefault(name_b, reason)
        if cat_a == category and context.get(cat_b) == name_b:
            blocked.setdefault(name_a, reason)

    return blocked


# ---------------------------------------------------------------------------
# Plant context-reactive branching (Session 17)
# Plants skip mood/behavior/condition in main() — only lighting, camera,
# and weather need suggestions.
# ---------------------------------------------------------------------------

# Plants split by environment:
#   swamp: Lepidodendron, Calamites, Sigillaria (Carboniferous coal swamp)
#   forest: Araucaria, Williamsonia, Glossopteris
#   aquatic: Archaefructus, Wattieza (near water)
SWAMP_PLANTS = {"Lepidodendron", "Calamites", "Sigillaria"}
FOREST_PLANTS = {"Araucaria", "Williamsonia", "Glossopteris"}
AQUATIC_PLANTS = {"Archaefructus", "Wattieza"}

PLANT_LIGHTING_BY_SPECIES = {
    # Swamp plants — humid, foggy, filtered light
    "Lepidodendron":  ["fog_diffuse",      "dappled_canopy",   "overcast",          "dawn_first_light",  "backlit_haze"],
    "Calamites":      ["dappled_canopy",   "fog_diffuse",      "golden_hour",       "overcast",          "dawn_first_light"],
    "Sigillaria":     ["fog_diffuse",      "overcast",         "dappled_canopy",    "dawn_first_light",  "backlit_haze"],
    # Forest plants — richer light
    "Araucaria":      ["golden_hour",      "backlit_haze",     "harsh_midday",      "overcast",          "dawn_first_light"],
    "Williamsonia":   ["golden_hour",      "dappled_canopy",   "backlit_haze",      "dawn_first_light",  "broken_cloud"],
    "Glossopteris":   ["golden_hour",      "overcast",         "backlit_haze",      "dawn_first_light",  "broken_cloud"],
    # Aquatic plants — water-surface light
    "Archaefructus":  ["dawn_first_light", "golden_hour",      "overcast",          "backlit_haze",      "surface_dapple"],
    "Wattieza":       ["dawn_first_light", "golden_hour",      "overcast",          "fog_diffuse",       "backlit_haze"],
}

PLANT_CAMERA_BY_MODE = {
    "portrait":        ["closeup_portrait", "detail_abstract",  "medium_shot",       "tight_head",        "ground_level_up"],
    "canvas":          ["full_body_profile","epic_wide",        "medium_shot",       "ground_level_up",   "aerial_above"],
    "environmental":   ["epic_wide",        "aerial_above",     "medium_shot",       "full_body_profile", "ground_level_up"],
    "extreme_closeup": ["detail_abstract",  "tight_head",       "closeup_portrait",  "ground_level_up",   "medium_shot"],
    "ground_level":    ["ground_level_up",  "dynamic_low",      "medium_shot",       "trail_camera",      "detail_abstract"],
}

PLANT_WEATHER_BY_ENVIRONMENT = {
    "swamp":   ["humid_haze",       "ground_mist",       "drizzle_steady",    "overcast_flat",     "rain_clearing"],
    "forest":  ["clear_pristine",   "ground_mist",       "overcast_flat",     "humid_haze",        "wind_gusts_dry"],
    "aquatic": ["ground_mist",      "clear_pristine",    "drizzle_steady",    "humid_haze",        "overcast_flat"],
}


def get_plant_suggestions(category: str, context: dict) -> list:
    """Context-reactive suggestions for plant habitat."""
    if context.get("habitat") != "plant":
        return []

    species_name = context.get("species_name", "")
    output_mode  = context.get("output_mode", "")

    if category == "lighting":
        return PLANT_LIGHTING_BY_SPECIES.get(species_name, [])

    if category == "camera":
        return PLANT_CAMERA_BY_MODE.get(output_mode, [])[:5]

    if category == "weather":
        if species_name in SWAMP_PLANTS:
            return PLANT_WEATHER_BY_ENVIRONMENT["swamp"]
        elif species_name in AQUATIC_PLANTS:
            return PLANT_WEATHER_BY_ENVIRONMENT["aquatic"]
        else:
            return PLANT_WEATHER_BY_ENVIRONMENT["forest"]

    return []


def get_plant_blocked(category: str, context: dict) -> dict:
    """Invalid combo blocking for plant habitat. Plants are simple — few combos to block."""
    # Plants don't pick mood/behavior/condition, so almost no combos to block.
    # Only block weather incompatible with plant environment.
    return {}


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
    if habitat == "arthropod":
        return get_arthropod_suggestions(category, context)
    if habitat == "plant":
        return get_plant_suggestions(category, context)
    return []


def get_blocked(category: str, context: dict) -> dict:
    habitat = context.get("habitat", "")
    if habitat == "marine":
        return get_marine_blocked(category, context)
    if habitat == "terrestrial":
        return get_terrestrial_blocked(category, context)
    if habitat == "aerial":
        return get_aerial_blocked(category, context)
    if habitat == "arthropod":
        return get_arthropod_blocked(category, context)
    if habitat == "plant":
        return get_plant_blocked(category, context)
    return {}


# Style is always hyperrealism — never ask the user.
# Per-clade style anchors so plant/arthropod prompts don't inherit
# vertebrate "living animal skin texture" language.
# Session 11: realism stack stripped from active output. The dict structure
# stays for save_prompt/parameter-id wiring; values are blank so nothing
# flows into the prose.
CLADE_STYLE = {
    "terrestrial": {"id": 24, "name": "hyperrealism", "value": ""},
    "marine":      {"id": 24, "name": "hyperrealism", "value": ""},
    "aerial":      {"id": 24, "name": "hyperrealism", "value": ""},
    "arthropod":   {"id": 24, "name": "hyperrealism", "value": ""},
    "plant":       {"id": 24, "name": "hyperrealism", "value": ""},
}

# Backward-compatible default for any code path that asks for the constant
# without a clade — defaults to vertebrate language.
HYPERREALISM_STYLE = CLADE_STYLE["terrestrial"]

# ---------------------------------------------------------------------------
# Mouth / teeth / saliva — diet-aware, injected as a dedicated prompt block
# ---------------------------------------------------------------------------

MOUTH_TEETH_CARNIVORE = "yellowed uneven teeth"
MOUTH_TEETH_HERBIVORE = "grinding teeth worn flat"

# ---------------------------------------------------------------------------
# Habitat-specific interaction blocks — replaces the old single GROUND_INTERACTION.
# Each habitat gets its own physics/contact language so MJ renders the right
# relationship between the animal and its medium.
# ---------------------------------------------------------------------------

# Marine default is UNDERWATER, not waterline. Most marine species in the DB
# are fully aquatic — defaulting to surface language created the contradiction
# "fully aquatic, body partially submerged" on canvas/portrait/environmental
# modes. Surface-state modes (`shoreline`, `surface_break`) override below.
HABITAT_INTERACTION = {
    "terrestrial": "feet fully weight-bearing",
    "marine":      "fully submerged",
    "aerial":      "body suspended in open sky",
    "arthropod":   "massive body weight pressing into ground",
    "plant":       "rooted in soil",
}

# ---------------------------------------------------------------------------
# Habitat-specific realism style anchors — appended to HYPERREALISM_STYLE
# to push MJ toward the right kind of wildlife photography per domain.
# ---------------------------------------------------------------------------

# Session 11: "wildlife photography" variants stripped from active output —
# they were biasing MJ toward staged specimen-style composition. Dict
# structure preserved for save_prompt/parameter wiring; values are blank
# so nothing flows into the prose.
HABITAT_REALISM = {
    "terrestrial": "",
    "marine":      "",
    "aerial":      "",
    "arthropod":   "",
    "plant":       "",
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
    "arthropod": (
        "mammal, dinosaur, vertebrate, furry, feathered, "
        "cartoon bug, cute insect, anime, chibi, "
        "small insect, tiny bug, macro photography of small creature, "
        "petri dish, lab specimen, pin mounted, entomology collection, "
        "normal sized, modern insect, house bug"
    ),
    "plant": (
        "animal, dinosaur, insect, mammal, "
        "cartoon plant, anime, potted plant, houseplant, modern garden"
    ),
}

# ---------------------------------------------------------------------------
# Canvas print mode constants
# ---------------------------------------------------------------------------

# CANVAS_PRINT removed in Session 10 — was 5 phrases of HDR/print-ready
# language that did almost nothing for MJ. The print-readiness happens at
# upscale time, not in the prompt. The canvas_print flag is kept on
# OUTPUT_MODES for tag/saved-record purposes only.
CANVAS_PRINT = ""

# ---------------------------------------------------------------------------
# Negative prompt — modular blocks assembled per-clade by build_negative_prompt().
# Each clade only gets the negatives that actually apply to its anatomy.
# This stops "fused digits, missing claws" from being injected into plant
# and arthropod prompts (where digits/claws don't exist) — wasted MJ tokens
# that dilute attention from the negatives that matter.
# ---------------------------------------------------------------------------

# Vertebrate extremity errors — only relevant to clades with toes/fingers/claws
# osteoderms live here (not in fossil block) because they are a vertebrate skin
# feature; arthropods/plants don't have them so should never see them in --no.
NEG_VERTEBRATE_ANATOMY = (
    "fused digits, merged toes, webbed feet, blob hands, extra fingers, "
    "missing claws, undefined claw tips, floating toes, amputated digits, "
    "incorrect toe count, melted feet, smooth footpad with no digit separation, "
    "smeared claws, indistinct talons, CGI smoothness on extremities, "
    "osteoderms, osteoderm"
)

# Arthropod-specific anatomy errors — segmented chitin, jointed legs, mandibles
NEG_ARTHROPOD_ANATOMY = (
    "fused leg segments, missing limb joints, smooth chitin with no segmentation, "
    "mammalian limbs, vertebrate hands, fingers, toes, claws, talons, footpads, "
    "rubbery skin, fleshy limbs, melted exoskeleton"
)

# Studio / controlled environment blockers — universal to all clades
NEG_STUDIO = (
    "studio background, seamless backdrop, portrait lighting, gradient background, "
    "grey background, controlled lighting, specimen photography, museum display, "
    "exhibit lighting, black background, white background, studio flash, "
    "specimen mount, display case, diorama, natural history exhibit"
)

# Fossil / skeletal blockers — for vertebrate clades (skeleton/bones apply)
NEG_FOSSIL_VERTEBRATE = (
    "fossil, fossilized, skeleton, skeletal, bones, bone structure, excavation, "
    "petrified, paleontology specimen, museum specimen, rock matrix, sediment, "
    "dinosaur fossil, fossil record, prehistoric bones, mineralized, stone cast"
)

# Fossil blockers for arthropods — drop "skeleton/bones" (no internal skeleton)
NEG_FOSSIL_ARTHROPOD = (
    "fossil, fossilized, petrified, paleontology specimen, museum specimen, "
    "rock matrix, sediment, mineralized, stone cast, amber inclusion"
)

# Fossil blockers for plants — drop "skeleton/bones/osteoderms" (not applicable),
# keep "petrified / fossil" since petrified plants are a real failure mode
NEG_FOSSIL_PLANT = (
    "fossil, fossilized, petrified, paleontology specimen, museum specimen, "
    "rock matrix, mineralized, stone cast, dried herbarium specimen, pressed leaf"
)

# Indoor / built environment blockers — universal
NEG_INDOOR = (
    "indoors, interior, building, warehouse, arena, concrete floor"
)

# CGI / digital environment blockers — universal
NEG_CGI = (
    "digital matte painting, rendered background, CGI environment, concept art, "
    "illustration, painted background, 3D render, Unreal Engine, volumetric god rays, "
    "hyper-saturated, fantasy landscape, perfect symmetry, smooth gradient sky"
)


def build_negative_prompt(habitat: str) -> str:
    """Assemble the --no clause from clade-appropriate blocks only.

    Plants get studio + plant-fossil + indoor + CGI + plant-specific —
    no vertebrate digits, no skeleton, no osteoderms.

    Arthropods get arthropod anatomy + studio + animal-fossil + indoor + CGI +
    arthropod-specific — no vertebrate digit/talon language.

    Vertebrate clades (terrestrial / marine / aerial) get the full set.
    """
    if habitat == "plant":
        blocks = [NEG_STUDIO, NEG_FOSSIL_PLANT, NEG_INDOOR, NEG_CGI]
    elif habitat == "arthropod":
        blocks = [NEG_ARTHROPOD_ANATOMY, NEG_STUDIO, NEG_FOSSIL_ARTHROPOD, NEG_INDOOR, NEG_CGI]
    else:
        blocks = [NEG_VERTEBRATE_ANATOMY, NEG_STUDIO, NEG_FOSSIL_VERTEBRATE, NEG_INDOOR, NEG_CGI]

    base = ", ".join(blocks)
    extra = HABITAT_NEGATIVE.get(habitat, "")
    return f"{base}, {extra}" if extra else base


# Back-compat shim for any external reference: vertebrate-flavoured default.
NEGATIVE_PROMPT = build_negative_prompt("terrestrial")

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
    # ─── CLOSE-UP / DETAIL (5) ──────────────────────────────────────────────
    "portrait": {
        "display":       "Portrait close-up",
        "desc":          "telephoto head/shoulders, mood-focused, shallow depth of field",
        "fixed_camera":  None,
        "composition":   "",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial", "arthropod", "plant"],
    },
    "extreme_closeup": {
        "display":       "Extreme detail macro",
        "desc":          "macro, single surface dominant, texture abstracted",
        "fixed_camera":  "Canon EOS R5 100mm macro f/8, razor-thin depth of field",
        "composition":   "single surface fills frame, texture dominant",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial", "arthropod", "plant"],
    },
    "eye_contact": {
        "display":       "Eye contact intimate",
        "desc":          "locked gaze, eye fills centre frame, iris detail",
        "fixed_camera":  None,
        "composition":   "direct eye contact with camera, eye and face dominant, intimate gaze",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial", "arthropod"],
    },
    "jaws_detail": {
        "display":       "Teeth & jaws detail",
        "desc":          "open mouth, teeth dominant, threat display",
        "fixed_camera":  None,
        "composition":   "mouth open, teeth and jaw dominate frame, threat or feeding display",
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
    # ─── MID-RANGE / FULL BODY (5) ──────────────────────────────────────────
    "canvas": {
        "display":       "Full body canvas print",
        "desc":          "mid-range, 60/40 negative space, gallery print-ready",
        "fixed_camera":  "Canon EOS R5 24-70mm f/4",
        "composition":   "PLACEMENT",
        "canvas_print":  True,
        "full_body":     True,
        "needs_placement": True,
        "habitats":      ["terrestrial", "marine", "aerial", "arthropod", "plant"],
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
        "desc":          "camera at dirt, animal towers above lens, dramatic scale",
        "fixed_camera":  "Canon EOS R5 24mm f/2.8, camera at ground, extreme upward angle",
        "composition":   "ground-level upward, animal towers overhead, sky behind",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "arthropod"],
    },
    "camera_trap": {
        "display":       "Camera trap / trail cam",
        "desc":          "off-centre, candid, motion-triggered framing",
        "fixed_camera":  "trail camera, fixed wide angle, off-centre framing, subject unaware of lens",
        "composition":   "candid camera trap angle, subject off-centre, motion-triggered moment, natural unposed framing",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "arthropod", "plant"],
    },
    "confrontation": {
        "display":       "Confrontation — walking toward camera",
        "desc":          "head-on approach, animal filling lower frame, intimidating",
        "fixed_camera":  None,
        "composition":   "animal walking directly toward camera, head-on angle, slightly low camera, imposing presence filling frame",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "arthropod"],
    },
    # ─── EPIC WIDE / LANDSCAPE (6) ──────────────────────────────────────────
    "environmental": {
        "display":       "Environmental wide — classic landscape",
        "desc":          "animal small in vast flat landscape, habitat dominant",
        "fixed_camera":  "Canon EOS R5 16-35mm f/2.8, ultra-wide",
        "composition":   "subject small in vast prehistoric landscape, habitat dominant",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial", "arthropod", "plant"],
    },
    "valley_panorama": {
        "display":       "Valley overlook panorama",
        "desc":          "camera high on ridge looking down into valley, animal below in distance",
        "fixed_camera":  "Canon EOS R5 24mm f/8, elevated vantage point",
        "composition":   "camera on elevated ridge looking down into wide valley, animal small below in middle distance, layers of terrain receding to horizon",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "aerial", "plant"],
    },
    "ridgeline_silhouette": {
        "display":       "Ridgeline silhouette — epic backlit",
        "desc":          "animal on ridge/hilltop, backlit by sun or sky, silhouette with rim light",
        "fixed_camera":  "Canon EOS R5 70-200mm, exposed for bright sky",
        "composition":   "animal standing on ridgeline or hilltop, strong backlight, silhouette with bright rim light, dramatic sky behind, landscape falling away below",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "aerial"],
    },
    "river_crossing": {
        "display":       "River crossing epic",
        "desc":          "animal at water crossing, wide river, landscape stretching beyond",
        "fixed_camera":  "Canon EOS R5 24-70mm f/4, low water-level angle",
        "composition":   "animal mid-stride crossing wide shallow river, water splashing at legs, vast open landscape stretching to horizon on both banks",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial"],
    },
    "misty_dawn": {
        "display":       "Misty dawn landscape",
        "desc":          "animal emerging from fog layers, layered atmospheric depth, cool light",
        "fixed_camera":  "Canon EOS R5 70-200mm f/2.8, dawn light through fog, layered depth",
        "composition":   "animal emerging from layered morning mist, vast foggy landscape, atmospheric depth, cool blue dawn light",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial", "arthropod", "plant"],
    },
    "storm_front": {
        "display":       "Storm front approach",
        "desc":          "massive storm clouds dominate sky, animal small below, dramatic light",
        "fixed_camera":  "Canon EOS R5 16-35mm f/2.8, ultra-wide",
        "composition":   "enormous storm clouds filling upper two-thirds of frame, dramatic light breaking through, animal small below against vast threatening sky",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial"],
    },
    # ─── SPECIALTY / ATMOSPHERIC (4) ────────────────────────────────────────
    "aerial_overhead": {
        "display":       "Aerial overhead — drone view",
        "desc":          "direct overhead, dorsal surface visible, habitat pattern below",
        "fixed_camera":  "DJI Mavic 3 Pro 24mm, drone directly overhead at 30m altitude, looking straight down",
        "composition":   "bird's-eye view looking straight down, camera directly above animal, top of head and back visible, ground/water surface fills entire frame, no horizon line, shot from drone altitude",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine"],
    },
    "dusk_long_exp": {
        "display":       "Dusk long exposure",
        "desc":          "motion blur, ambient light only, atmospheric and painterly",
        "fixed_camera":  "Canon EOS R5 50mm f/5.6, tripod, long exposure at dusk",
        "composition":   "long exposure, moving elements blurred, static elements sharp",
        "canvas_print":  False,
        "full_body":     False,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine"],
    },
    "shoreline": {
        "display":       "Shoreline / water edge",
        "desc":          "subject at water transition, half-wet half-dry, horizon line",
        "fixed_camera":  "Canon EOS R5 200mm f/4, low water-level angle, telephoto bokeh",
        "composition":   "subject at edge of water, transition zone between dry and wet, horizon visible",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "plant"],
    },
    "group_herd": {
        "display":       "Group / herd scene",
        "desc":          "three animals, social grouping, natural spacing across landscape",
        "fixed_camera":  "Canon EOS R5 70-200mm f/2.8, mid-range telephoto, group framing",
        "composition":   "each animal fully distinct, no overlap, imperfect natural detail",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial", "arthropod", "plant"],
    },
    "family_group": {
        "display":       "Family group — adult with juveniles",
        "desc":          "one large adult with two smaller juveniles, size variation, nurturing",
        "fixed_camera":  "Canon EOS R5 70-200mm f/2.8, mid-range telephoto, group framing",
        "composition":   "clear size difference between adult and juveniles, imperfect natural detail",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial", "arthropod"],
    },
    "waterhole_gather": {
        "display":       "Waterhole gathering",
        "desc":          "animals gathered at water source, drinking, reflections, golden light",
        "fixed_camera":  "Canon EOS R5 200mm f/4, low water-level angle, telephoto bokeh",
        "composition":   "muddy trampled ground, murky disturbed water, imperfect natural detail",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial"],
    },
    "migration_march": {
        "display":       "Migration march — column in motion",
        "desc":          "animals walking in loose column, receding into distance, epic depth",
        "fixed_camera":  "Canon EOS R5 70-200mm f/2.8, telephoto compression, depth layering",
        "composition":   "nearest animal largest, depth perspective, imperfect natural detail",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine", "aerial"],
    },
    # ─── MARINE-SPECIFIC ────────────────────────────────────────────────────
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
        "fixed_camera":  "Canon EOS R5 in underwater housing, 16-35mm f/2.8",
        "composition":   "fully submerged",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["marine"],
    },
    # ─── AERIAL-SPECIFIC ────────────────────────────────────────────────────
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
    # ─── MULTI-SUBJECT (Session 17) ─────────────────────────────────────────
    "predator_prey": {
        "display":       "Predator–prey encounter",
        "desc":          "two species in frame, predator and prey, tension-filled moment",
        "fixed_camera":  "Canon EOS R5 70-200mm f/2.8, telephoto, natural encounter distance",
        "composition":   "candid wildlife encounter, two different animals in frame, decisive moment",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine"],
    },
    "ecosystem_diorama": {
        "display":       "Ecosystem diorama — multiple species",
        "desc":          "wide scene, 2-3 species coexisting, natural ecosystem snapshot",
        "fixed_camera":  "Canon EOS R5 16-35mm f/2.8, ultra-wide, ecosystem framing",
        "composition":   "wide ecosystem view, multiple species coexisting naturally, different animals at different distances, natural prehistoric habitat",
        "canvas_print":  False,
        "full_body":     True,
        "needs_placement": False,
        "habitats":      ["terrestrial", "marine"],
    },
}

# ---------------------------------------------------------------------------
# Multi-subject scene system (Session 17, Priority #8)
# Period-compatible species pairings and interaction phrases.
# ---------------------------------------------------------------------------

MULTI_SUBJECT_MODES = {"predator_prey", "ecosystem_diorama"}

# Predator → [prey species] pairings. All must share a geological period.
PREDATOR_PREY_PAIRINGS = {
    # Late Cretaceous
    "Tyrannosaurus rex": ["Triceratops", "Parasaurolophus", "Ankylosaurus"],
    "Velociraptor":      ["Parasaurolophus"],
    # Early–Mid Cretaceous
    "Spinosaurus":       ["Cretoxyrhina", "Xiphactinus"],
    # Late Cretaceous marine
    "Mosasaurus":        ["Ammonite", "Archelon", "Xiphactinus"],
    "Kronosaurus":       ["Ammonite", "Ichthyosaurus"],
    "Cretoxyrhina":      ["Xiphactinus", "Archelon"],
    # Jurassic
    "Dilophosaurus":     ["Stegosaurus"],
    # Jurassic marine
    "Liopleurodon":      ["Ichthyosaurus", "Ammonite"],
    # Devonian
    "Dunkleosteus":      ["Eurypterus"],
    # Ordovician
    "Megalograptus":     ["Eurypterus"],
    # Miocene
    "Megalodon":         ["Leedsichthys"],
}

# Ecosystem pairings: species that coexisted (not necessarily predator-prey).
# Format: primary → [secondary species that share its period/habitat].
ECOSYSTEM_PAIRINGS = {
    "Tyrannosaurus rex": ["Triceratops", "Parasaurolophus", "Ankylosaurus", "Pteranodon"],
    "Triceratops":       ["Tyrannosaurus rex", "Parasaurolophus", "Ankylosaurus", "Pteranodon"],
    "Parasaurolophus":   ["Tyrannosaurus rex", "Triceratops", "Pteranodon"],
    "Ankylosaurus":      ["Tyrannosaurus rex", "Triceratops", "Pteranodon"],
    "Stegosaurus":       ["Brachiosaurus", "Dilophosaurus"],
    "Brachiosaurus":     ["Stegosaurus", "Dilophosaurus"],
    "Dilophosaurus":     ["Stegosaurus", "Brachiosaurus"],
    "Mosasaurus":        ["Ammonite", "Archelon", "Xiphactinus", "Pteranodon"],
    "Ichthyosaurus":     ["Ammonite", "Liopleurodon"],
    "Liopleurodon":      ["Ichthyosaurus", "Ammonite"],
    "Dunkleosteus":      ["Eurypterus"],
    "Lepidodendron":     ["Calamites", "Sigillaria", "Arthropleura", "Meganeura", "Pulmonoscorpius"],
    "Calamites":         ["Lepidodendron", "Sigillaria", "Arthropleura", "Meganeura"],
    "Meganeura":         ["Arthropleura", "Pulmonoscorpius", "Lepidodendron", "Calamites"],
    "Arthropleura":      ["Meganeura", "Pulmonoscorpius", "Lepidodendron", "Calamites"],
}

# ── Species-pair hunt moments ─────────────────────────────────────────────
# Keyed by (predator, prey) → dict of interaction_type → vivid frozen-moment
# description based on real paleontological behavior.  These replace generic
# interaction phrases so MJ gets a SPECIFIC action to render.
HUNT_MOMENTS = {
    ("Mosasaurus", "Ammonite"): {
        "stalking":      "mosasaurus gliding behind drifting ammonite, jaw slightly open, ambush approach",
        "confrontation": "mosasaurus jaw closing around ammonite shell, crushing bite, shell cracking",
        "chase":         "mosasaurus pursuing jet-propelling ammonite, tentacles trailing behind fleeing prey",
        "ambush":        "mosasaurus lunging from dark water below, jaws snapping shut on ammonite",
    },
    ("Mosasaurus", "Archelon"): {
        "stalking":      "mosasaurus shadowing archelon from below, massive silhouette beneath turtle",
        "confrontation": "mosasaurus biting archelon flipper, turtle thrashing to break free",
        "chase":         "mosasaurus chasing fleeing archelon, flippers beating water",
        "ambush":        "mosasaurus erupting from depth to seize archelon shell edge",
    },
    ("Mosasaurus", "Xiphactinus"): {
        "stalking":      "mosasaurus trailing wounded xiphactinus, blood trail in water",
        "confrontation": "mosasaurus and xiphactinus face to face, both jaws open",
        "chase":         "mosasaurus chasing xiphactinus at full speed through open water",
        "ambush":        "mosasaurus striking xiphactinus from below, impact moment",
    },
    ("Tyrannosaurus rex", "Triceratops"): {
        "stalking":      "tyrannosaur stalking through ferns behind unaware triceratops, crouched low",
        "confrontation": "tyrannosaur and triceratops locked face to face, horns versus jaws",
        "chase":         "tyrannosaur in full sprint after galloping triceratops, dust cloud",
        "ambush":        "tyrannosaur clamping jaws on triceratops frill, triceratops driving horns upward",
    },
    ("Tyrannosaurus rex", "Parasaurolophus"): {
        "stalking":      "tyrannosaur emerging from treeline toward grazing parasaurolophus",
        "confrontation": "tyrannosaur towering over crouching parasaurolophus, jaws open",
        "chase":         "tyrannosaur sprinting after fleeing parasaurolophus, ground shaking",
        "ambush":        "tyrannosaur seizing parasaurolophus by the neck, prey buckling",
    },
    ("Tyrannosaurus rex", "Ankylosaurus"): {
        "stalking":      "tyrannosaur circling wary ankylosaurus, tail club raised",
        "confrontation": "tyrannosaur snapping at ankylosaurus flank, tail club swinging defensively",
        "chase":         "tyrannosaur pursuing retreating ankylosaurus, armored back facing predator",
        "ambush":        "tyrannosaur biting ankylosaurus side, tail club striking tyrannosaur leg",
    },
    ("Velociraptor", "Parasaurolophus"): {
        "stalking":      "velociraptor crouched low in undergrowth watching parasaurolophus",
        "confrontation": "velociraptor leaping at parasaurolophus flank, sickle claw extended",
        "chase":         "velociraptor sprinting after young parasaurolophus, feathers flattened",
        "ambush":        "velociraptor airborne mid-leap onto parasaurolophus back, claws digging in",
    },
    ("Dilophosaurus", "Stegosaurus"): {
        "stalking":      "dilophosaurus stalking cautiously behind stegosaurus, eyeing vulnerable flank",
        "confrontation": "dilophosaurus and stegosaurus facing off, thagomizer tail spikes swinging",
        "chase":         "dilophosaurus circling stegosaurus, testing for opening, tail plates flushed",
        "ambush":        "dilophosaurus lunging at stegosaurus hindquarters, avoiding tail spikes",
    },
    ("Spinosaurus", "Cretoxyrhina"): {
        "stalking":      "spinosaurus wading chest deep watching circling cretoxyrhina fin",
        "confrontation": "spinosaurus swiping clawed hand at cretoxyrhina, jaws open, water splashing",
        "chase":         "spinosaurus pursuing cretoxyrhina through shallows, sail cutting water",
        "ambush":        "spinosaurus plunging snout underwater to snatch cretoxyrhina",
    },
    ("Spinosaurus", "Xiphactinus"): {
        "stalking":      "spinosaurus standing in river watching xiphactinus shadow below surface",
        "confrontation": "spinosaurus snout breaking water with xiphactinus in jaws",
        "chase":         "spinosaurus wading after thrashing xiphactinus in shallows",
        "ambush":        "spinosaurus striking into water, claws hooking xiphactinus",
    },
    ("Kronosaurus", "Ammonite"): {
        "stalking":      "kronosaurus gliding silently toward cluster of drifting ammonites",
        "confrontation": "kronosaurus massive jaw engulfing ammonite, shell splintering",
        "chase":         "kronosaurus pursuing jet-propelling ammonite through murky water",
        "ambush":        "kronosaurus surging upward from depth to crush ammonite",
    },
    ("Kronosaurus", "Ichthyosaurus"): {
        "stalking":      "kronosaurus shadowing ichthyosaurus from deep water below",
        "confrontation": "kronosaurus and ichthyosaurus face to face, massive size mismatch",
        "chase":         "kronosaurus chasing ichthyosaurus through open ocean",
        "ambush":        "kronosaurus lunging at ichthyosaurus from below, jaws wide",
    },
    ("Liopleurodon", "Ichthyosaurus"): {
        "stalking":      "liopleurodon trailing ichthyosaurus through dim deep water",
        "confrontation": "liopleurodon massive jaws opening around ichthyosaurus",
        "chase":         "liopleurodon pursuing ichthyosaurus at speed, flippers driving forward",
        "ambush":        "liopleurodon erupting from darkness to seize ichthyosaurus",
    },
    ("Liopleurodon", "Ammonite"): {
        "stalking":      "liopleurodon drifting toward cluster of ammonites, mouth opening",
        "confrontation": "liopleurodon jaw crushing ammonite shell with ease",
        "chase":         "liopleurodon sweeping through ammonite group, tentacles scattering",
        "ambush":        "liopleurodon gulping ammonite whole from below",
    },
    ("Cretoxyrhina", "Xiphactinus"): {
        "stalking":      "cretoxyrhina circling below wounded xiphactinus",
        "confrontation": "cretoxyrhina ramming xiphactinus broadside, teeth tearing",
        "chase":         "cretoxyrhina in pursuit of fleeing xiphactinus, shark speed",
        "ambush":        "cretoxyrhina striking xiphactinus from below, explosive bite",
    },
    ("Cretoxyrhina", "Archelon"): {
        "stalking":      "cretoxyrhina circling below archelon shadow on surface",
        "confrontation": "cretoxyrhina biting archelon flipper from below",
        "chase":         "cretoxyrhina pursuing archelon, turtle paddling desperately",
        "ambush":        "cretoxyrhina lunging upward at archelon belly, turtle recoiling",
    },
    ("Dunkleosteus", "Eurypterus"): {
        "stalking":      "dunkleosteus armored head emerging from gloom toward eurypterus",
        "confrontation": "dunkleosteus bony jaw plates snapping shut on eurypterus",
        "chase":         "dunkleosteus chasing eurypterus through murky water",
        "ambush":        "dunkleosteus engulfing eurypterus in single crushing bite",
    },
    ("Megalograptus", "Eurypterus"): {
        "stalking":      "megalograptus spiked arms reaching toward smaller eurypterus",
        "confrontation": "megalograptus grappling eurypterus with spined appendages",
        "chase":         "megalograptus pursuing eurypterus across seafloor",
        "ambush":        "megalograptus seizing eurypterus from behind with barbed claws",
    },
    ("Megalodon", "Leedsichthys"): {
        "stalking":      "megalodon massive shadow approaching leedsichthys from behind",
        "confrontation": "megalodon jaws gaping around leedsichthys tail section",
        "chase":         "megalodon in pursuit of leedsichthys, enormous shark dwarfing frame",
        "ambush":        "megalodon ramming leedsichthys from below, explosive impact",
    },
}

# Fallback generic interactions — used when no species-pair entry exists.
PREDATOR_PREY_INTERACTIONS = {
    "stalking":      "predator creeping toward unaware prey, tension before strike",
    "confrontation": "predator and prey locked in standoff, frozen moment of tension",
    "chase":         "predator in full pursuit, prey fleeing at speed, chase in motion",
    "ambush":        "predator mid-strike, explosive attack, prey reacting",
}


def get_compatible_species(primary_name: str, mode: str) -> list[str]:
    """Return list of species names compatible with the primary for multi-subject scenes."""
    if mode == "predator_prey":
        return PREDATOR_PREY_PAIRINGS.get(primary_name, [])
    elif mode == "ecosystem_diorama":
        return ECOSYSTEM_PAIRINGS.get(primary_name, [])
    return []


def pick_secondary_species(conn: sqlite3.Connection, primary: dict, output_mode: str):
    """Pick a second species for multi-subject scenes. Returns species row or None."""
    compatible = get_compatible_species(primary["name"], output_mode)
    if not compatible:
        pname = primary["name"]
        print(f"  {warn(f'No compatible species pairings for {pname} in {output_mode} mode')}")
        return None

    all_species = conn.execute(
        "SELECT id, name, common_name, period, diet, size_class, description, notes, habitat "
        "FROM species WHERE name IN ({}) ORDER BY name".format(",".join("?" * len(compatible))),
        compatible,
    ).fetchall()

    if not all_species:
        return None

    if output_mode == "predator_prey":
        label = f"Select PREY species (predator: {primary['name']})"
    else:
        label = f"Select COMPANION species (primary: {primary['name']})"

    print(f"\n  {hdr(label)}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for i, sp in enumerate(all_species, 1):
        period = f"({sp['period']})" if sp["period"] else ""
        common = f" / {sp['common_name']}" if sp["common_name"] else ""
        sp_name = sp["name"]
        print(f"  {C.DIM}{i:>2}.{C.RESET}  {opt(f'{sp_name}{common}  {period}')}")
    print()
    while True:
        try:
            raw = input(f"  {C.BOLD_CYAN}Choose 1–{len(all_species)}:{C.RESET} ").strip()
            choice = int(raw)
            if 1 <= choice <= len(all_species):
                chosen = all_species[choice - 1]
                print(f"  {ok('✓')} {ok(chosen['name'])}\n")
                return dict(chosen)
        except (ValueError, EOFError):
            pass
        print(f"  {warn('Invalid choice — try again')}")


def pick_interaction_type() -> str:
    """Pick the predator-prey interaction type."""
    options = list(PREDATOR_PREY_INTERACTIONS.keys())
    print(f"\n  {hdr('Select INTERACTION type')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for i, key in enumerate(options, 1):
        key_display = key.replace("_", " ")
        desc = PREDATOR_PREY_INTERACTIONS[key]
        print(f"  {C.DIM}{i:>2}.{C.RESET}  {opt(f'{key_display} — {desc}')}")
    print()
    while True:
        try:
            raw = input(f"  {C.BOLD_CYAN}Choose 1–{len(options)}:{C.RESET} ").strip()
            choice = int(raw)
            if 1 <= choice <= len(options):
                chosen = options[choice - 1]
                print(f"  {ok('✓')} {ok(chosen.replace('_', ' '))}\n")
                return chosen
        except (ValueError, EOFError):
            pass
        print(f"  {warn('Invalid choice — try again')}")


def build_multi_subject_block(primary: dict, secondary: dict, interaction_type: str, output_mode: str) -> str:
    """Build the subject section for multi-subject scenes.

    CRITICAL: MJ's CLIP encoder only reliably processes ~77 tokens.
    Two-species prompts MUST front-load:
      1. Explicit count ("one X with one Y") so MJ renders TWO creatures
      2. Both species names in the first 20 tokens
      3. Anatomy trimmed to 'wide' level (silhouette only) for both
    Without this, MJ collapses the two species into variants of the primary.
    """
    primary_anatomy = get_anatomy(primary["name"])
    secondary_anatomy = get_anatomy(secondary["name"])

    # Size descriptors
    p_size = primary["size_class"].lower() if primary["size_class"] else ""
    s_size = secondary["size_class"].lower() if secondary["size_class"] else ""

    # Both species get WIDE-level anatomy only (silhouette + 1 key feature)
    # to keep total subject block under ~40 tokens
    p_anat = ""
    if primary_anatomy:
        p_anat = build_anatomy_prompt(primary_anatomy, "wide")
    s_anat = ""
    if secondary_anatomy:
        s_anat = build_anatomy_prompt(secondary_anatomy, "wide")

    if output_mode == "predator_prey":
        interaction = PREDATOR_PREY_INTERACTIONS.get(interaction_type, "two species in natural encounter")

        # ── Relative-size anchoring ──────────────────────────────────
        # MJ defaults to rendering both subjects at similar scale.
        # Inject explicit scale language: "tiny prey" vs "massive predator"
        # using real body-length data from anatomy modules.
        p_len = primary_anatomy.body.body_length_m if primary_anatomy and primary_anatomy.body else 0
        s_len = secondary_anatomy.body.body_length_m if secondary_anatomy and secondary_anatomy.body else 0
        if p_len and s_len and p_len > s_len * 3:
            scale_phrase = "tiny %s dwarfed by massive %s" % (secondary["name"], primary["name"])
        elif p_len and s_len and s_len > p_len * 3:
            scale_phrase = "tiny %s dwarfed by massive %s" % (primary["name"], secondary["name"])
        else:
            scale_phrase = "clear size difference between them"

        # Front-load: "one [predator] with one [prey]" then scale then interaction
        # This ensures CLIP registers both species names + size relationship early
        parts = [
            "one %s %s with one %s %s" % (p_size, primary["name"], s_size, secondary["name"]),
            scale_phrase,
            interaction,
        ]
        if p_anat:
            parts.append(p_anat)
        if s_anat:
            parts.append(s_anat)
        parts.append("two different species in frame")
        return ", ".join(p for p in parts if p)
    else:
        parts = [
            "one %s %s with one %s %s" % (p_size, primary["name"], s_size, secondary["name"]),
            "coexisting naturally in shared habitat",
        ]
        if p_anat:
            parts.append(p_anat)
        if s_anat:
            parts.append(s_anat)
        parts.append("two different species in frame")
        return ", ".join(p for p in parts if p)


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
    """Present the habitat types and return the chosen key."""
    HABITATS = [
        ("terrestrial", "Terrestrial", "land-based dinosaurs — ground, forest, plains"),
        ("marine",      "Marine",      "ocean and water-dwelling species — sharks, reptiles, fish"),
        ("aerial",      "Aerial",      "flying species — pterosaurs, in-flight, soaring"),
        ("arthropod",   "Arthropods",  "prehistoric insects, arachnids, and giant invertebrates"),
        ("plant",       "Plants",      "prehistoric flora — ferns, cycads, conifers, early flowers"),
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

    # Group labels injected before certain mode keys for readability
    GROUP_HEADERS = {
        "portrait":              "CLOSE-UP / DETAIL",
        "canvas":                "MID-RANGE / FULL BODY",
        "environmental":         "EPIC WIDE / LANDSCAPE  🏔️",
        "aerial_overhead":       "SPECIALTY / ATMOSPHERIC",
        "group_herd":            "GROUP / MULTI-ANIMAL",
        "surface_break":         "MARINE",
        "soaring_thermal":       "AERIAL",
    }
    for i, key in enumerate(keys, 1):
        cfg = OUTPUT_MODES[key]
        header = GROUP_HEADERS.get(key)
        if header:
            print(f"    {C.CYAN}{header}{C.RESET}")
        landscape_tag = f"  {C.GREEN}🏔️{C.RESET}" if key in WIDE_MODES else ""
        print(f"  {C.DIM}{i:>2}.{C.RESET}  {C.BRIGHT_WHITE}{cfg['display']}{C.RESET}{landscape_tag}")
        print(f"      {C.DIM}{cfg['desc']}{C.RESET}")
    print()
    while True:
        raw = input(f"  {C.BOLD_CYAN}Choose 1–{len(keys)}:{C.RESET} ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            chosen_key = keys[int(raw) - 1]
            print(f"  {ok('✓')} {ok(OUTPUT_MODES[chosen_key]['display'])}\n")
            return chosen_key
        print(f"  {err(f'Please enter a number between 1 and {len(keys)}.')}")


def select_perspective() -> str:
    """Ask the user for camera angle/perspective. Returns a key from CAMERA_PERSPECTIVES."""
    keys = list(CAMERA_PERSPECTIVES.keys())
    print(f"\n  {hdr('Camera perspective')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for i, key in enumerate(keys, 1):
        cfg = CAMERA_PERSPECTIVES[key]
        print(f"  {C.DIM}{i:>2}.{C.RESET}  {opt(cfg['display'])}")
    print()
    while True:
        raw = input(f"  {C.BOLD_CYAN}Choose 1–{len(keys)} (Enter for default):{C.RESET} ").strip()
        if raw == "":
            print(f"  {ok('✓')} {ok('Default (mode built-in angle)')}\n")
            return "default"
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            chosen_key = keys[int(raw) - 1]
            print(f"  {ok('✓')} {ok(CAMERA_PERSPECTIVES[chosen_key]['display'])}\n")
            return chosen_key
        print(f"  {err(f'Please enter a number between 1 and {len(keys)}, or press Enter.')}")


def select_canvas_placement() -> tuple[str, str]:
    """Ask how the animal is positioned in frame.
    Returns (composition_phrase, space_side).
    'dead_center' is a sentinel that triggers symmetric composition text.
    'wide' is a sentinel that triggers environmental-scale framing —
    suppresses full-body language, no camera language added."""
    OPTIONS = [
        # (composition_phrase injected into prompt,  space_side label for display)
        ("animal positioned left of centre, rule of thirds",                "right"),
        ("animal positioned right of centre, rule of thirds",               "left"),
        ("dead_center",                                                      ""),
        ("wide",                                                             "all"),
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
        "Wide scale — environment dominant, distant subject",
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
        # Show feathered tag for species with feathering in anatomy module
        anat = get_anatomy(r["name"])
        feather_tag = ""
        if anat and anat.integument and anat.integument.primary_covering:
            covering = anat.integument.primary_covering.lower()
            if "pycnofiber" in covering:
                feather_tag = f"  {C.YELLOW}[pycnofibers]{C.RESET}"
            elif any(kw in covering for kw in ("feather", "plumage")):
                feather_tag = f"  {C.YELLOW}[feathered]{C.RESET}"
            elif "filament" in covering:
                feather_tag = f"  {C.YELLOW}[filaments]{C.RESET}"
        return f"{r['name']}{common}  {size} {period}{feather_tag}"

    if len(rows) == 1:
        chosen = rows[0]
        label = _species_label(habitat)
        print(f"\n  {hdr(label)}")
        print(f"  {ok('✓')} {ok(fmt(chosen))}  {dim('(only species for this habitat)')}\n")
        return chosen

    # Group by diet for terrestrial and marine, show section headers
    if habitat == "terrestrial":
        groups = [("Carnivore", "CARNIVORES"), ("Herbivore", "HERBIVORES")]
    elif habitat == "marine":
        groups = [("Carnivore", "PREDATORS"), ("Piscivore", "FISH-EATERS"),
                  ("Filter-feeder", "FILTER FEEDERS"), ("Omnivore", "OMNIVORES")]
    else:
        groups = []

    label = _species_label(habitat)
    if groups:
        return _pick_grouped(label, rows, fmt, groups)
    return pick(label, rows, fmt)


def _species_label(habitat):
    labels = {
        "terrestrial": "Select a dinosaur species",
        "marine":      "Select a marine species",
        "aerial":      "Select an aerial species",
        "plant":       "Select a plant species",
        "arthropod":   "Select an arthropod species",
    }
    return labels.get(habitat, "Select a species")


def _pick_grouped(label, rows, display_fn, groups):
    """Numbered menu with diet group headers. Numbers are continuous across groups."""
    print(f"\n  {hdr(label)}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)

    ordered = []
    for diet_val, group_label in groups:
        members = [r for r in rows if (r["diet"] or "") == diet_val]
        if members:
            print(f"  {C.BOLD_CYAN}  {group_label}{C.RESET}")
            for r in members:
                idx = len(ordered) + 1
                ordered.append(r)
                print(f"  {C.DIM}{idx:>2}.{C.RESET}  {opt(display_fn(r))}")
    # Any remaining species not in a group
    grouped_names = {r["name"] for dv, _ in groups for r in rows if (r["diet"] or "") == dv}
    remaining = [r for r in rows if r["name"] not in {o["name"] for o in ordered}]
    if remaining:
        print(f"  {C.BOLD_CYAN}  OTHER{C.RESET}")
        for r in remaining:
            idx = len(ordered) + 1
            ordered.append(r)
            print(f"  {C.DIM}{idx:>2}.{C.RESET}  {opt(display_fn(r))}")

    print()
    while True:
        try:
            raw = input(f"  {C.BOLD_CYAN}Choose 1–{len(ordered)}:{C.RESET} ").strip()
            choice = int(raw)
            if 1 <= choice <= len(ordered):
                chosen = ordered[choice - 1]
                print(f"  {ok('✓')} {ok(display_fn(chosen))}\n")
                return chosen
        except (ValueError, EOFError):
            pass
        print(f"  {warn('Invalid choice — try again')}")


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


def auto_pick_parameter(conn: sqlite3.Connection, category: str, habitat: str,
                        ctx: dict) -> dict:
    """Auto-select the best parameter for a category using the suggestion system.
    Picks the top suggestion that isn't blocked. Falls back to the first
    unblocked DB row if no suggestions exist for the habitat/species."""
    suggestions = get_suggestions(category, ctx)
    blocked = get_blocked(category, ctx)
    rows = fetch_parameters_by_category(conn, category, habitat=habitat)
    if not rows:
        sys.exit(f"No {habitat or ''} parameters for '{category}'. Run setup_db.py.")

    # Try suggestion order first
    if suggestions:
        for sug_name in suggestions:
            for r in rows:
                if r["name"] == sug_name and r["name"] not in blocked:
                    return dict(r)

    # Fallback: first unblocked row
    for r in rows:
        if r["name"] not in blocked:
            return dict(r)
    return dict(rows[0])


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

    if habitat == "arthropod":
        core = (
            f"extreme close-up of {name} legs, jointed exoskeleton limbs, "
            "chitinous segments with natural scratches and wear, "
            "fine sensory hairs along leg segments, "
            "tarsal claws gripping surface, real macro insect photography",
        )
    elif habitat == "marine":
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

    flags = f"--no {build_negative_prompt(habitat)} --style {mj_style} --stylize {stylize}"
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
    elif habitat == "arthropod":
        # Arthropod mouthparts — mandibles, chelicerae, pincers depending on species
        if name in ("Pulmonoscorpius", "Jaekelopterus", "Eurypterus", "Megalograptus"):
            core = (
                f"extreme close-up of {name} chelicerae and pedipalps, "
                "pincer tips worn and scratched from use, "
                "chitinous exoskeleton detail on mouthparts, "
                "small sensory hairs along pincer edges, "
                "prey remains caught between pincer plates, "
                "real wildlife photograph, scorpion mouthparts reference"
            )
        elif name == "Anomalocaris":
            core = (
                f"extreme close-up of {name} circular mouth and grasping appendages, "
                "ring of overlapping tooth-like plates forming circular jaw, "
                "flexible grasping appendages with spiny inner edges, "
                "translucent body visible near mouth, "
                "real wildlife photograph, mantis shrimp appendage reference"
            )
        else:
            core = (
                f"extreme close-up of {name} mandibles, "
                "paired jaw-like mandibles with worn cutting edges, "
                "maxillae and labium visible behind mandibles, "
                "chitinous mouthpart detail, natural scratches and wear, "
                "real wildlife photograph, beetle mandible reference"
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

    flags = f"--no {build_negative_prompt(habitat)} --style {mj_style} --stylize {stylize}"
    return f"{core}, telephoto macro, shallow depth of field, muted colour, film grain {flags}"


# ---------------------------------------------------------------------------
# CLIP tokenizer helpers (Session 17)
# MJ uses CLIP ViT-L/14 which tokenizes text into ~77 tokens max.
# These helpers optimize prompt text for CLIP's actual behavior:
#   - Comma-separated short phrases get roughly equal weight
#   - Early tokens get slight priority
#   - Prose connector words ("the", "and", "with") waste token slots
#   - Each comma-phrase is a separate attention unit
# ---------------------------------------------------------------------------

# Words that CLIP tokenizes but carry zero visual information.
# Removing them frees token budget for actual visual descriptors.
_CLIP_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "has", "have", "had", "do", "does", "did", "its", "it",
    "that", "this", "these", "those", "very", "quite", "rather", "somewhat",
}


def _clip_clean(phrase: str) -> str:
    """Strip prose connector words that waste CLIP tokens.
    Keeps visual adjectives, nouns, and action verbs.
    'head raised and eyes on middle distance' → 'head raised, eyes middle distance'
    """
    words = phrase.split()
    cleaned = [w for w in words if w.lower() not in _CLIP_STOPWORDS]
    return " ".join(cleaned)


def _estimate_clip_tokens(text: str) -> int:
    """Rough estimate of CLIP token count.
    CLIP's BPE tokenizer averages ~1.3 tokens per word for English.
    Comma-separated phrases each count as separate attention units.
    Returns approximate token count (CLIP max is 77)."""
    words = text.split()
    return int(len(words) * 1.3)


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
    secondary_species: dict = None,         # Session 17: multi-subject scene support
    interaction_type: str = None,           # Session 17: predator_prey interaction type
    perspective: str = "default",           # Session 21: camera angle override
) -> str:
    mode_cfg     = OUTPUT_MODES.get(output_mode, OUTPUT_MODES["portrait"])
    full_body    = mode_cfg["full_body"]
    canvas_print = mode_cfg["canvas_print"]
    # Session 12+13: framing override system. Two flag families.
    #   wide_mode — distant-subject framings, suppress full-body language
    #   multi_species_mode — interspecies scene, keeps body detail visible
    # Both work regardless of the mode's composition template.
    # Session 13: wide_mode now also triggers for inherently wide output modes
    # (environmental, silhouette, aerial_overhead, etc.) so the subject always
    # reads small in frame with environment-dominant composition — essential
    # for premium canvas prints.
    placement_wide = bool(placement) and placement[0] in WIDE_SCALE_VARIANTS
    wide_mode = placement_wide or output_mode in WIDE_MODES
    multi_species_mode = bool(placement) and placement[0] == "multi_species"

    # ── SECTION 1: SUBJECT ───────────────────────────────────────────────────
    # Anatomy, pose, skin, mouth, behavior, condition, mood.
    # Richest section — MJ weights early tokens most heavily.
    # Rule: no environment, no lighting, no camera language here.

    size = species["size_class"].lower() if species["size_class"] else ""

    # ── Species anatomy module system (Sessions 15-17) ─────────────────
    # Per-species anatomy modules provide CLIP-optimized shorthand phrases
    # (mj_shorthand) that MJ actually responds to, budget-capped per mode:
    #   "close" — up to 350 chars (all shorthand + size + coloration)
    #   "mid"   — up to 250 chars (silhouette + top shorthand phrases)
    #   "wide"  — up to 120 chars (silhouette + one key feature)
    # build_anatomy_prompt() returns detail scaled to mode_type:
    #   "close" — full detail (skull, teeth, integument, limbs, coloration)
    #   "mid"   — moderate (integument, silhouette, key features)
    #   "wide"  — minimal (silhouette + 2 critical features only)
    #
    # Session 17 CLIP audit: when an anatomy module exists, species["description"]
    # is redundant prose that wastes CLIP tokens. The mj_shorthand already
    # covers the same ground but in CLIP-optimized comma-separated phrases.
    # Drop it to avoid duplicate attention fragmentation.
    anatomy = get_anatomy(species["name"])

    # ── Group modes: lead with explicit count + group framing ──────────
    # MJ ignores late-arriving "multiple individuals" — the count MUST be
    # in the very first tokens to override its single-subject default.
    is_group = output_mode in GROUP_MODES

    GROUP_LEADS = {
        "group_herd":       "three {size} {name}, spaced apart, each animal distinct, candid wildlife photograph",
        "family_group":     "one large adult {name} with two smaller juvenile {name}, size variation visible, candid wildlife photograph",
        "waterhole_gather": "three {size} {name} at muddy water edge, drinking and wading, trampled mud bank",
        "migration_march":  "column of five {size} {name} walking in loose line receding into distance, candid wildlife photograph",
    }

    if is_group:
        lead_template = GROUP_LEADS.get(output_mode, GROUP_LEADS["group_herd"])
        group_lead = lead_template.format(size=size, name=species["name"])
        subject_parts = [group_lead]
    elif anatomy:
        # Anatomy module exists — lead with species name only, shorthand follows
        subject_parts = [f"{size} {species['name']}"]
    else:
        # No anatomy module — keep DB description as fallback
        subject_parts = [f"{size} {species['name']}", species["description"] or ""]

    # Map output mode to anatomy detail level
    # Group herd forces "wide" — can't resolve detail on 3 animals, and
    # extra anatomy tokens fight the group composition instruction.
    CLOSE_MODES = {"portrait", "extreme_closeup", "eye_contact", "jaws_detail", "action_freeze"}
    if wide_mode or is_group:
        anatomy_mode = "wide"
    elif output_mode in CLOSE_MODES:
        anatomy_mode = "close"
    else:
        anatomy_mode = "mid"

    if anatomy:
        # Inject rich anatomy data — replaces old science fields
        anatomy_text = build_anatomy_prompt(anatomy, anatomy_mode)
        if anatomy_text:
            subject_parts.append(anatomy_text)

        if not wide_mode:
            # Required species params (e.g. raptor sickle claw accuracy)
            for rp in required_params:
                subject_parts.append(rp["value"])
    else:
        # Fallback: no anatomy module — use old science table fields
        if not wide_mode:
            if species["notes"]:
                subject_parts.append(species["notes"])
            if science and science["feathering_coverage"] and science["feathering_coverage"].lower() != "none":
                subject_parts.append(science["feathering_coverage"])
            if science and science["tail_posture"] and science["tail_posture"].lower() not in ("not applicable — pterosaur", ""):
                subject_parts.append(science["tail_posture"])
            if science and science["known_coloration_evidence"]:
                ce = science["known_coloration_evidence"]
                if not any(ce.lower().startswith(p) for p in ("no direct", "no known", "unknown")):
                    subject_parts.append(ce)
            for rp in required_params:
                subject_parts.append(rp["value"])

    # Canvas species extras (pose specifics for full-body modes).
    # Wide-scale variant suppresses "full body visible head to tail" because
    # the subject is meant to read small/distant, not anatomically resolved.
    if (full_body or has_sref) and not wide_mode and not is_group:
        if output_mode == "canvas":
            extra = CANVAS_SPECIES_EXTRAS.get(species["name"])
            if extra:
                subject_parts.append(extra)
        subject_parts.append("full body visible head to tail")

    # Session 13: in wide modes the subject is small/distant in frame.
    # Fine anatomical detail (skin texture, teeth, condition scars) can't be
    # resolved at that scale and their presence in early tokens pulls MJ
    # toward close-up composition. Skip them entirely for wide_mode.
    if not wide_mode and not anatomy:
        # Skin texture — only when no anatomy module (anatomy module already covers integument)
        if science and science["skin_texture_type"]:
            subject_parts.append(science["skin_texture_type"])

        # Mouth / teeth — only when no anatomy module (anatomy module already covers dentition)
        diet = species["diet"] or ""
        desc_blob = ((species["description"] or "") + " " + (species["notes"] or "")).lower()
        is_toothless = "toothless" in desc_blob or ("beak" in desc_blob and "tooth" not in desc_blob)
        if habitat == "arthropod":
            subject_parts.append("mandibles or chelicerae visible, no vertebrate mouth")
        elif habitat != "plant" and not is_toothless:
            subject_parts.append(MOUTH_TEETH_CARNIVORE if diet in ("Carnivore", "Piscivore") else MOUTH_TEETH_HERBIVORE)
    elif wide_mode:
        pass  # anatomy module handles wide mode detail level
    diet = species["diet"] or ""

    # Behavior — FIRST PHRASE ONLY (Session 10). Action verbs were the main
    # source of "narrative clutter" the user flagged: "jaw working on prey,
    # fragments drifting" reads like an event, not a static portrait.
    # Session 17 CLIP audit: strip prose connectors ("and", "with", "the")
    # that CLIP fragments into noise tokens.
    beh_phrase = behavior_param["value"].split(", ")[0]
    beh_phrase = _clip_clean(beh_phrase)
    subject_parts.append(beh_phrase)

    # Condition — skip entirely in wide modes (unresolvable at distance).
    # Otherwise first 2 phrases only (Session 10).
    # Session 17 CLIP audit: clean prose connectors from condition phrases.
    if not wide_mode:
        cond_phrases = condition_param["value"].split(", ")[:2]
        condition_short = ", ".join(_clip_clean(p) for p in cond_phrases)
        subject_parts.append(condition_short)

    # Mood is intentionally NOT injected into prose. It overlaps with behavior
    # and was the single biggest source of redundant action language. Mood is
    # still selected (drives context-reactive suggestions) and saved as a tag.

    # Session 19: Living-animal naturalism phrase — extracted from user's reptile
    # reference photos. Describes the visual QUALITIES of real wildlife photography
    # (specular scale highlights, warm directional light, organic imperfection)
    # rather than naming cameras/magazines which cause staged specimen bias.
    # Only injected for close/mid modes where surface detail is resolvable.
    if not wide_mode and not is_group and habitat not in ("plant",):
        if habitat == "arthropod":
            naturalism = "individual chitin plates catching light, organic imperfection, living animal"
        elif habitat == "marine":
            naturalism = "wet skin catching light, water particles, living animal"
        else:
            naturalism = "individual scales catching sunlight, warm natural light, living animal"
        subject_parts.append(naturalism)

    # Session 11: style_param["value"] and HABITAT_REALISM are NOT injected
    # into the prose. The DB-stored style rows contain the full realism stack
    # ("anatomically accurate, living animal skin texture, shot on Canon EOS,
    # National Geographic wildlife photography, ...") which was biasing MJ
    # toward staged specimen-style composition. The params are still passed
    # through the function signature so save_prompt / tag wiring is intact.

    subject = ", ".join(p for p in subject_parts if p)

    # Session 17: Multi-subject scene override — replaces single-species subject
    # with a combined block containing both species and their interaction.
    if secondary_species and output_mode in MULTI_SUBJECT_MODES:
        subject = build_multi_subject_block(
            species, secondary_species, interaction_type or "coexisting", output_mode
        )

    # ── SECTION 2: INTERACTION ────────────────────────────────────────────────
    # Habitat-specific contact/physics block.
    # Terrestrial: feet/ground. Marine: water surface. Aerial: wing/air.
    # Mode overrides prevent repetitive compositions.
    if output_mode == "predator_prey":
        # Naturalism anchor — the subject block already contains the specific
        # hunt action.  This slot reinforces wildlife-photo realism and
        # physical grounding (water/ground contact, environmental debris).
        if habitat == "marine":
            interaction = "murky water, sediment particles, bubbles trailing, bodies moving through water"
        else:
            interaction = "dirt kicked up, dust and debris, muscles tensed, raw animal energy"
    elif output_mode == "perched":
        interaction = "talons gripping rocky edge, wings folded"
    elif output_mode == "underwater":
        interaction = "fully submerged"
    elif output_mode == "surface_break":
        interaction = "body erupting through water surface"
    elif output_mode == "shoreline" and habitat == "marine":
        interaction = "body partially submerged, waterline crossing torso"
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

    # Cap environment phrases. Wide modes get the full environment (up to 5
    # phrases) so the landscape dominates the prompt for epic canvas prints.
    # Non-wide modes keep 3 to avoid filler phrases duplicating lighting.
    env_cap = 5 if wide_mode else 3
    environment = ", ".join(environment.split(", ")[:env_cap])

    # (Anti-CGI anchor removed — was 3 phrases of bloat per prompt.
    # The negative prompt + style anchor already cover the same ground.)

    comp_template = mode_cfg["composition"]
    # "horizon visible" is a contradiction underwater — drop it for marine
    # modes EXCEPT the two surface-state modes (shoreline + surface_break).
    marine_underwater = habitat == "marine" and output_mode not in ("shoreline", "surface_break")
    horizon_phrase = "" if marine_underwater else ", horizon visible"
    if wide_mode:
        # Session 13: Wide-scale framing block — forceful landscape-dominant
        # language for premium canvas prints. Subject must read as a small
        # element within a vast prehistoric world.
        wide_comp = ("ultra-wide angle, vast sweeping landscape, "
                     "single animal small but clearly visible in frame, "
                     "large negative space, deep layered depth, "
                     "epic sense of scale, landscape dominant")
        environment = f"{environment}, {wide_comp}{horizon_phrase}"
    elif comp_template == "PLACEMENT":
        subject_phrase, space_side = placement
        # Session 11: "animal centred, symmetrical" stripped — was biasing
        # MJ toward staged specimen-style framing. Dead-center sentinel
        # now contributes only the horizon hint (when applicable).
        if subject_phrase == "dead_center":
            comp = horizon_phrase.lstrip(", ")
        elif space_side in ("right", "left"):
            comp = f"{subject_phrase}, negative space {space_side}{horizon_phrase}"
        else:
            comp = f"{subject_phrase}{horizon_phrase}"
        if comp:
            environment = f"{environment}, {comp}"
    elif comp_template:
        environment = f"{environment}, {comp_template}"

    # ── SECTION 4: LIGHTING ───────────────────────────────────────────────────
    # ONE lead phrase of lighting only. DB values often pile on 4+ descriptors
    # ("light fading with depth, animal lit from above, dark water below,
    # natural light gradient") which dilute MJ attention. Weather is NOT
    # injected — almost always duplicates lighting. Both stay in tags / branching.
    lighting = lighting_param["value"].split(", ")[0]

    # ── SECTION 5: CAMERA ─────────────────────────────────────────────────────
    # Session 11: camera brands and lens specs stripped from active output —
    # they were pushing MJ toward staged product-shot/specimen framing.
    # Session 13: EXCEPTION for wide modes — ultra-wide lens language is
    # essential to force MJ into landscape-dominant composition for canvas
    # prints. Without it, MJ defaults to mid-range framing every time.
    if wide_mode:
        camera = "shot on ultra-wide 16mm lens, deep depth of field, everything in focus"
    else:
        camera = ""

    # ── ASSEMBLE ──────────────────────────────────────────────────────────────
    # Session 21: Camera perspective override. When a non-default perspective
    # is chosen, its lead phrase is injected FIRST — before subject — so MJ
    # treats the angle as the dominant composition directive.
    perspective_lead = CAMERA_PERSPECTIVES.get(perspective, {}).get("lead", "")

    # aerial_overhead mode implies drone_overhead perspective if user kept default
    if output_mode == "aerial_overhead" and not perspective_lead:
        perspective_lead = CAMERA_PERSPECTIVES["drone_overhead"]["lead"]

    if perspective_lead:
        # Perspective-first assembly: angle → subject → environment → details → lighting
        sections = [perspective_lead, subject, camera, environment, interaction, lighting]
    elif wide_mode:
        sections = [subject, camera, environment, lighting, interaction]
    else:
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
    # Clade-aware negative prompt — plants don't get vertebrate digit blockers,
    # arthropods don't get talon/footpad blockers, etc.
    if output_mode == "perched":
        # Perched mode: skip the aerial habitat extras (which block "folded wings"
        # and grounded poses — both wanted in a perched shot). Build base + clade
        # anatomy/studio/fossil/indoor/CGI without the habitat-specific overlay.
        if habitat == "plant":
            base_blocks = [NEG_STUDIO, NEG_FOSSIL_PLANT, NEG_INDOOR, NEG_CGI]
        elif habitat == "arthropod":
            base_blocks = [NEG_ARTHROPOD_ANATOMY, NEG_STUDIO, NEG_FOSSIL_ARTHROPOD, NEG_INDOOR, NEG_CGI]
        else:
            base_blocks = [NEG_VERTEBRATE_ANATOMY, NEG_STUDIO, NEG_FOSSIL_VERTEBRATE, NEG_INDOOR, NEG_CGI]
        neg = ", ".join(base_blocks)
    else:
        neg = build_negative_prompt(habitat)
    # Session 13: wide modes get additional negative prompt blockers to
    # prevent MJ from drifting back toward portrait/close-up composition.
    if wide_mode:
        wide_neg = (", close-up, portrait, headshot, tight crop, macro, "
                    "face filling frame, telephoto compression, "
                    "shallow depth of field, bokeh background, "
                    "detail shot, extreme close-up")
        neg = neg + wide_neg
    # Session 19: predator_prey mode — prevent MJ from merging bodies
    # and from rendering both species at equal size.
    if output_mode == "predator_prey":
        merge_neg = (", merged bodies, conjoined animals, fused creatures, "
                     "overlapping bodies, chimera, hybrid animal, "
                     "two-headed, morphing, blended anatomy, "
                     "same size animals, equal sized, "
                     "Siamese, body fusion, grafted limbs")
        neg = neg + merge_neg
    # Session 15: species anatomy module — banned flora (e.g. "grass" for
    # Jurassic species) injected into negative prompt to prevent MJ from
    # adding anachronistic vegetation.
    if anatomy:
        anatomy_neg = build_anatomy_negative(anatomy)
        if anatomy_neg:
            neg = neg + ", " + anatomy_neg
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
PALEOART_FILE = Path(__file__).parent / "paleoart_refs.json"

# ---------------------------------------------------------------------------
# Reference system: 3-layer approach (Session 23)
# ---------------------------------------------------------------------------
#   Layer 1 — --sref (wildlife photos): photographic style, lighting, texture
#   Layer 2 — --cref (paleoart renditions): what the animal LOOKS LIKE alive
#   Layer 3 — --cref fallback (skeletal diagrams): body proportions if no paleoart
#
# The key insight: --sref copies VISUAL STYLE, --cref copies LIKENESS.
# Wildlife --sref → "real National Geographic photography" feel
# Paleoart --cref → correct morphology (NOT a crocodile, NOT a shark)
# Skeletal --cref → body proportions fallback when paleoart unavailable
MAX_SREF_URLS = 2   # wildlife photo refs for --sref (style guide)
MAX_CREF_URLS = 1   # paleoart or skeletal ref for --cref (likeness/morphology)
DEFAULT_CW = 10     # unused in MJ v7 but kept for reference
DEFAULT_SW = 20     # --sw (style weight): subtle photographic feel

# ---------------------------------------------------------------------------
# Habitat → allowed ref categories (strict filtering)
# ---------------------------------------------------------------------------
# Prevents cross-contamination: land animal refs can't appear in underwater
# scenes, marine refs can't appear in terrestrial scenes, etc.
HABITAT_ALLOWED_CATEGORIES = {
    "marine":      {"marine", "sea_scorpion"},
    "terrestrial": {"waterhole", "crocodile", "komodo",
                    "tall_predator", "tortoise_group", "family", "migration"},
    "aerial":      {"komodo", "crocodile"},
    "arthropod":   {"arthropod_group", "sea_scorpion"},
    "plant":       {"paleo_plant"},
}

# Categories EXCLUDED from --sref selection — skeletal and paleoart should NOT
# be used as style refs (makes output look like a fossil or a painting).
SREF_EXCLUDED_CATEGORIES = {"skeletal", "paleoart"}

# Categories used for --cref (likeness): paleoart preferred, skeletal fallback
CREF_PALEOART_CATEGORY = "paleoart"
CREF_SKELETAL_CATEGORY = "skeletal"

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Bird photo categories — EXCLUDED from --sref for ALL species (Session 22)
# ---------------------------------------------------------------------------
# Lesson learned: bird --sref refs make feathered theropods look like literal
# birds (bustards/turkeys), and make pterosaurs grow feathered wings.
# Text prompts already describe feathering accurately — visual bird refs
# cause MJ to adopt bird body plans, not just feather texture.
# Only reptile/mammal refs used as style guides now.
BIRD_CATEGORIES = {"feathered_biped", "raptor_flight"}

# ---------------------------------------------------------------------------
# Categories with mouth/claw/toe detail — prioritized in --sref ordering
# ---------------------------------------------------------------------------
# These are the hardest features for MJ; refs showing them get top style slots.
MOUTH_CLAW_PRIORITY_CATEGORIES = ["komodo", "crocodile", "tall_predator"]

# ---------------------------------------------------------------------------
# Context → sref-category priority mapping  (Session 22 — wildlife --sref only)
# ---------------------------------------------------------------------------
# Mode-based priorities determine which wildlife photo categories fill --sref
# slots.  Skeletal excluded entirely — anatomy comes from text prompts.
SREF_MODE_PRIORITY = {
    # Close-up / detail modes → mouth, claw, skin texture refs dominate
    "portrait":         ["komodo", "crocodile", "tall_predator"],
    "extreme_closeup":  ["komodo", "crocodile", "tall_predator"],
    "eye_contact":      ["komodo", "crocodile", "tall_predator"],
    "jaws_detail":      ["komodo", "crocodile", "tall_predator"],
    "action_freeze":    ["komodo", "crocodile", "tall_predator"],
    # Mid-range full body
    "canvas":           ["waterhole", "tall_predator", "komodo", "crocodile"],
    "tracking_side":    ["tall_predator", "komodo", "crocodile"],
    "ground_level":     ["tall_predator", "komodo", "crocodile"],
    "camera_trap":      ["waterhole", "komodo", "crocodile", "tall_predator"],
    "confrontation":    ["komodo", "crocodile", "tall_predator"],
    # Epic wide / landscape
    "environmental":    ["waterhole", "migration", "family", "tall_predator", "komodo"],
    "valley_panorama":  ["waterhole", "migration", "family", "tall_predator"],
    "ridgeline_silhouette": ["waterhole", "migration", "tall_predator"],
    "river_crossing":   ["waterhole", "migration", "crocodile", "tall_predator"],
    "misty_dawn":       ["waterhole", "migration", "family", "tall_predator"],
    "storm_front":      ["waterhole", "migration", "tall_predator"],
    # Specialty
    "aerial_overhead":  ["waterhole", "migration", "tall_predator"],
    "dusk_long_exp":    ["waterhole", "migration", "tall_predator"],
    "shoreline":        ["waterhole", "crocodile", "marine", "tall_predator"],
    # Group / multi-animal
    "group_herd":       ["family", "migration", "waterhole", "tall_predator", "komodo"],
    "family_group":     ["family", "migration", "waterhole", "tall_predator"],
    "waterhole_gather": ["waterhole", "family", "migration", "crocodile", "tall_predator"],
    "migration_march":  ["migration", "family", "waterhole", "tall_predator"],
    # Marine
    "surface_break":    ["marine", "sea_scorpion"],
    "underwater":       ["marine", "sea_scorpion"],
    # Aerial — reptile skin refs only (bird refs removed Session 22)
    "soaring_thermal":  ["komodo", "crocodile"],
    "dive_strike":      ["komodo", "crocodile"],
    "perched":          ["komodo", "crocodile"],
    # Multi-subject
    "predator_prey":    ["komodo", "crocodile", "tall_predator", "waterhole"],
    "ecosystem_diorama":["waterhole", "family", "migration", "tall_predator"],
}

# ── Habitat-based sref injection (applied before mode priorities) ──────────
SREF_HABITAT_INJECT = {
    "marine":    ["marine"],
    "aerial":    ["komodo", "crocodile"],
    "arthropod": ["arthropod_group", "sea_scorpion"],
    "plant":     ["paleo_plant"],
}

# ── Lighting-based bonus categories (appended if sref slots remain) ────────
SREF_LIGHTING_BONUS = {
    "golden_hour":      ["waterhole", "migration"],
    "sunset_warm":      ["waterhole", "migration"],
    "dawn_first_light": ["waterhole", "migration"],
    "harsh_midday":     ["waterhole"],
    "moonlit":          ["waterhole"],
    "underwater_caustics": ["marine"],
    "deep_water_fade":  ["marine"],
    "surface_dapple":   ["marine"],
    "bioluminescent":   ["marine"],
    "noon_column":      ["marine"],
    "reef_scatter":     ["marine"],
    "murk_glow":        ["marine"],
    "dawn_surface":     ["marine"],
    "moonlit_surface":  ["marine"],
}


def load_sref_urls():
    """Load species → [{label, url}, ...] mapping from sref_urls.json."""
    if not SREF_FILE.exists():
        return {}
    with open(SREF_FILE) as f:
        return json.load(f)


def load_paleoart_refs():
    """Load species → [{label, url}, ...] paleoart mapping."""
    if not PALEOART_FILE.exists():
        return {}
    with open(PALEOART_FILE) as f:
        return json.load(f)


def _extract_category(label):
    """Extract category prefix from a label like 'komodo/komodo_tongue.jpg'."""
    if "/" in label:
        return label.split("/", 1)[0]
    return ""


def select_refs(species_name, output_mode, habitat, lighting_name):
    """Context-aware wildlife --sref selection (Session 22 overhaul).

    Session 22 lesson:
      --sref copies VISUAL STYLE → skeletal photos made outputs look fossilized
      --cref copies LIKENESS     → shark photos made Mosasaurus look like a shark

    New approach:  wildlife photos → --sref ONLY (photographic style guide).
    Skeletal refs excluded entirely — anatomy encoded in text prompts.
    --cref removed — too literal for cross-species reference.

    Returns (sref_urls, cref_urls, cw_weight) where:
      sref_urls: list of URL strings for --sref (wildlife style refs)
      cref_urls: always [] (--cref disabled)
      cw_weight: int (kept for backward compat, unused)
    """
    all_urls = load_sref_urls()
    species_entries = all_urls.get(species_name, [])
    if not species_entries:
        return [], [], DEFAULT_CW

    # Strict habitat filtering: only allowed categories pass through
    allowed = HABITAT_ALLOWED_CATEGORIES.get(habitat, HABITAT_ALLOWED_CATEGORIES["terrestrial"])

    # Build category → [url_entries] index, filtered by habitat + exclusions
    cat_index = {}         # wildlife refs (for --sref)
    paleoart_entries = []  # paleoart refs (for --cref, preferred)
    skeletal_entries = []  # skeletal refs (for --cref, fallback)
    for entry in species_entries:
        if isinstance(entry, dict):
            cat = _extract_category(entry.get("label", ""))
        else:
            cat = ""
        if cat == CREF_PALEOART_CATEGORY:
            paleoart_entries.append(entry)  # collect for --cref (preferred)
            continue
        if cat == CREF_SKELETAL_CATEGORY:
            skeletal_entries.append(entry)  # collect for --cref (fallback)
            continue
        if cat in SREF_EXCLUDED_CATEGORIES:
            continue
        if cat in BIRD_CATEGORIES:
            continue  # bird refs excluded — make dinosaurs look like birds
        if cat and cat not in allowed:
            continue  # habitat filter: reject this ref entirely
        cat_index.setdefault(cat, []).append(entry)

    # --- Helper: extract filename for dedup ---
    def _extract_filename(entry):
        if isinstance(entry, dict):
            label = entry.get("label", "")
            if "/" in label:
                return label.split("/", 1)[1].lower()
            return label.lower()
        return ""

    used_urls = set()
    used_filenames = set()

    def _pick_from_cats(cat_list, max_count):
        """Round-robin pick URLs from ordered category list up to max_count."""
        if max_count <= 0:
            return []
        available = [c for c in cat_list if c in cat_index]
        cursors = {c: 0 for c in available}
        picked = []
        rounds = 0
        while len(picked) < max_count and rounds < max_count:
            added = False
            for cat in available:
                if len(picked) >= max_count:
                    break
                entries = cat_index[cat]
                cursor = cursors[cat]
                while cursor < len(entries):
                    entry = entries[cursor]
                    url = entry["url"] if isinstance(entry, dict) else entry
                    fname = _extract_filename(entry)
                    cursor += 1
                    if url not in used_urls and fname not in used_filenames:
                        picked.append(url)
                        used_urls.add(url)
                        if fname:
                            used_filenames.add(fname)
                        cursors[cat] = cursor
                        added = True
                        break
                cursors[cat] = cursor
            if not added:
                break
            rounds += 1
        return picked

    # ── --sref: wildlife photos only (style guide) ────────────────────────
    # Build priority order: mouth/claw detail first, then context-aware
    sref_priority = []

    # 1. Mouth/claw emphasis: detail categories first (hardest MJ features)
    for cat in MOUTH_CLAW_PRIORITY_CATEGORIES:
        if cat in allowed and cat not in SREF_EXCLUDED_CATEGORIES and cat not in sref_priority:
            sref_priority.append(cat)

    # 2. Habitat injection
    for cat in SREF_HABITAT_INJECT.get(habitat, []):
        if cat not in SREF_EXCLUDED_CATEGORIES and cat not in sref_priority:
            sref_priority.append(cat)

    # 3. Mode-based priorities
    for cat in SREF_MODE_PRIORITY.get(output_mode, []):
        if cat not in SREF_EXCLUDED_CATEGORIES and cat not in sref_priority:
            sref_priority.append(cat)

    # 4. Lighting bonus
    for cat in SREF_LIGHTING_BONUS.get(lighting_name, []):
        if cat not in SREF_EXCLUDED_CATEGORIES and cat not in sref_priority:
            sref_priority.append(cat)

    # 5. Any remaining non-excluded categories
    for cat in cat_index:
        if cat and cat not in SREF_EXCLUDED_CATEGORIES and cat not in sref_priority:
            sref_priority.append(cat)

    # Filter to only habitat-allowed categories
    sref_priority = [c for c in sref_priority if c in allowed]

    sref_urls = _pick_from_cats(sref_priority, MAX_SREF_URLS)

    # --cref: paleoart (preferred) or skeletal (fallback) for likeness/morphology
    # Paleoart shows the animal ALIVE with correct morphology.
    # All refs must be Discord CDN URLs (MJ rejects Wikimedia direct URLs).
    cref_urls = []
    cref_source = ""
    if MAX_CREF_URLS > 0:
        if paleoart_entries:
            # Paleoart from sref_urls.json (already on Discord CDN)
            picked = random.sample(paleoart_entries, min(MAX_CREF_URLS, len(paleoart_entries)))
            cref_urls = [e["url"] if isinstance(e, dict) else e for e in picked]
            cref_source = "paleoart"
        elif skeletal_entries:
            # Skeletal fallback from sref_urls.json (already on Discord CDN)
            picked = random.sample(skeletal_entries, min(MAX_CREF_URLS, len(skeletal_entries)))
            cref_urls = [e["url"] if isinstance(e, dict) else e for e in picked]
            cref_source = "skeletal"

    return sref_urls, cref_urls, cref_source


# Back-compat wrapper for any callers still using the old API
def select_sref_urls(species_name, output_mode, habitat, lighting_name):
    """Legacy wrapper — returns combined URL list for backward compat."""
    sref, cref, _ = select_refs(species_name, output_mode, habitat, lighting_name)
    return sref + cref


def display_ref_selection(species_name, sref_urls, cref_urls, cref_source, species_entries):
    """Print the auto-selected --sref and --cref URLs with labels."""
    if not sref_urls and not cref_urls:
        return

    # Build url → label lookup
    url_to_label = {}
    for entry in species_entries:
        if isinstance(entry, dict):
            url_to_label[entry["url"]] = entry.get("label", "reference")

    total_refs = len(species_entries)
    total_selected = len(sref_urls)

    print(f"\n  {hdr(f'REFERENCES — {species_name} (auto-selected)')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)

    if sref_urls:
        print(f"  {C.WHITE}--sref (wildlife style guide, --sw {DEFAULT_SW}):{C.RESET}")
        for url in sref_urls:
            label = url_to_label.get(url, "reference")
            short_url = url[:50] + "..." if len(url) > 50 else url
            print(f"    {ok('+')} {C.BRIGHT_WHITE}{label}{C.RESET}")
            print(f"      {dim(short_url)}")

    if cref_urls:
        source_label = "paleoart rendition" if cref_source == "paleoart" else "skeletal anatomy"
        print(f"  {C.WHITE}--cref ({source_label}):{C.RESET}")
        for url in cref_urls:
            label = url_to_label.get(url, "skeletal reference")
            short_url = url[:50] + "..." if len(url) > 50 else url
            print(f"    {ok('+')} {C.BRIGHT_WHITE}{label}{C.RESET}")
            print(f"      {dim(short_url)}")

    skel_count = len(cref_urls)
    src = cref_source or "none"
    print(f"  {dim(f'{total_selected} wildlife --sref (--sw {DEFAULT_SW}) + {skel_count} {src} --cref')}")


def display_sref_selection(species_name, selected_urls, species_entries):
    """Legacy wrapper for display — used by A/B test path."""
    display_ref_selection(species_name, selected_urls, [], DEFAULT_CW, species_entries)


# ---------------------------------------------------------------------------
# A/B Testing Framework (Session 17 — Priority #10)
# ---------------------------------------------------------------------------
# Generate two prompt variants differing on a single axis (lighting, mood,
# condition, behavior, stylize, or output_mode).  Designed for systematic
# testing: run both through MJ, score, and track which parameter combos
# produce the best results for each species.
#
# Usage:  python generate_prompt.py --ab-test
# ---------------------------------------------------------------------------

AB_AXES = ["lighting", "mood", "condition", "behavior", "stylize", "output_mode"]


def _ensure_ab_tables(conn: sqlite3.Connection) -> None:
    """Create A/B testing tables if they don't exist (idempotent)."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS ab_tests (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            species_id      INTEGER NOT NULL REFERENCES species(id) ON DELETE CASCADE,
            variable_axis   TEXT NOT NULL,
            control_value   TEXT NOT NULL,
            variant_value   TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'pending',
            winner          TEXT,
            notes           TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            scored_at       TEXT
        );
        CREATE TABLE IF NOT EXISTS ab_variants (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id         INTEGER NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
            label           TEXT NOT NULL,
            prompt_id       INTEGER REFERENCES prompts(id) ON DELETE SET NULL,
            positive_prompt TEXT NOT NULL,
            variable_value  TEXT NOT NULL,
            rating          INTEGER,
            notes           TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_ab_variants_test ON ab_variants(test_id);
        CREATE INDEX IF NOT EXISTS idx_ab_tests_species ON ab_tests(species_id);
    """)


def select_ab_axis() -> str:
    """Let user pick which parameter axis to vary."""
    print(f"\n  {hdr('SELECT VARIABLE AXIS')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for i, axis in enumerate(AB_AXES, 1):
        print(f"    {C.WHITE}[{i}]{C.RESET}  {axis}")
    print()
    while True:
        try:
            raw = input(f"  {C.CYAN}Vary which axis? [1-{len(AB_AXES)}]: {C.RESET}").strip()
            idx = int(raw) - 1
            if 0 <= idx < len(AB_AXES):
                axis = AB_AXES[idx]
                print(f"  {ok('✓')} Testing axis: {C.WHITE}{axis}{C.RESET}")
                return axis
        except (ValueError, EOFError):
            pass
        print(f"  {warn('Invalid choice — try again')}")


def pick_ab_values(conn: sqlite3.Connection, axis: str, habitat: str,
                   current_value: str) -> tuple:
    """Pick A (control) and B (variant) values for the chosen axis.

    Returns (control_value, variant_value, control_param, variant_param).
    For 'stylize', returns (str(int), str(int), int, int).
    """
    if axis == "stylize":
        print(f"\n  {hdr('STYLIZE A/B VALUES')}")
        print(f"  {C.DIM}" + "─" * 60 + C.RESET)
        print(f"  Current default: {C.WHITE}{current_value}{C.RESET}")
        options = [50, 100, 150, 200, 300, 500, 750]
        for i, val in enumerate(options, 1):
            marker = " ← current" if str(val) == str(current_value) else ""
            print(f"    {C.WHITE}[{i}]{C.RESET}  --stylize {val}{C.DIM}{marker}{C.RESET}")
        print()

        def _pick_stylize(label):
            while True:
                try:
                    raw = input(f"  {C.CYAN}{label} value [1-{len(options)}]: {C.RESET}").strip()
                    idx = int(raw) - 1
                    if 0 <= idx < len(options):
                        return options[idx]
                except (ValueError, EOFError):
                    pass
                print(f"  {warn('Invalid choice — try again')}")

        a_val = _pick_stylize("A (control)")
        b_val = _pick_stylize("B (variant)")
        while b_val == a_val:
            print(f"  {warn('B must differ from A — pick again')}")
            b_val = _pick_stylize("B (variant)")
        return (str(a_val), str(b_val), a_val, b_val)

    if axis == "output_mode":
        modes = [m for m in OUTPUT_MODES if OUTPUT_MODES[m]["habitat"] == habitat]
        print(f"\n  {hdr('OUTPUT MODE A/B VALUES')}")
        print(f"  {C.DIM}" + "─" * 60 + C.RESET)
        for i, m in enumerate(modes, 1):
            marker = " ← current" if m == current_value else ""
            print(f"    {C.WHITE}[{i}]{C.RESET}  {m}{C.DIM}{marker}{C.RESET}")
        print()

        def _pick_mode(label):
            while True:
                try:
                    raw = input(f"  {C.CYAN}{label} [1-{len(modes)}]: {C.RESET}").strip()
                    idx = int(raw) - 1
                    if 0 <= idx < len(modes):
                        return modes[idx]
                except (ValueError, EOFError):
                    pass
                print(f"  {warn('Invalid choice — try again')}")

        a_val = _pick_mode("A (control)")
        b_val = _pick_mode("B (variant)")
        while b_val == a_val:
            print(f"  {warn('B must differ from A — pick again')}")
            b_val = _pick_mode("B (variant)")
        a_cfg = OUTPUT_MODES[a_val]
        b_cfg = OUTPUT_MODES[b_val]
        return (a_val, b_val, a_cfg, b_cfg)

    # Standard parameter categories: lighting, mood, condition, behavior
    params = fetch_parameters_by_category(conn, axis, habitat=habitat)
    print(f"\n  {hdr(f'{axis.upper()} A/B VALUES')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for i, p in enumerate(params, 1):
        marker = " ← current" if p["name"] == current_value else ""
        print(f"    {C.WHITE}[{i}]{C.RESET}  {p['name'].replace('_', ' ')}{C.DIM}{marker}{C.RESET}")
    print()

    def _pick_param(label):
        while True:
            try:
                raw = input(f"  {C.CYAN}{label} [1-{len(params)}]: {C.RESET}").strip()
                idx = int(raw) - 1
                if 0 <= idx < len(params):
                    return dict(params[idx])
            except (ValueError, EOFError):
                pass
            print(f"  {warn('Invalid choice — try again')}")

    a_param = _pick_param("A (control)")
    b_param = _pick_param("B (variant)")
    while b_param["name"] == a_param["name"]:
        print(f"  {warn('B must differ from A — pick again')}")
        b_param = _pick_param("B (variant)")
    return (a_param["name"], b_param["name"], a_param, b_param)


def save_ab_test(conn: sqlite3.Connection, species_id: int, axis: str,
                 control_value: str, variant_value: str) -> int:
    """Insert a new A/B test row and return its id."""
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO ab_tests (species_id, variable_axis, control_value, variant_value, status)
           VALUES (?, ?, ?, ?, 'pending')""",
        (species_id, axis, control_value, variant_value),
    )
    conn.commit()
    return cur.lastrowid


def save_ab_variant(conn: sqlite3.Connection, test_id: int, label: str,
                    prompt_id: int, positive_prompt: str, variable_value: str) -> int:
    """Insert an A/B variant row."""
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO ab_variants (test_id, label, prompt_id, positive_prompt, variable_value)
           VALUES (?, ?, ?, ?, ?)""",
        (test_id, label, prompt_id, positive_prompt, variable_value),
    )
    conn.commit()
    return cur.lastrowid


def score_ab_test(conn: sqlite3.Connection, test_id: int) -> None:
    """Interactive scoring of an A/B test after MJ results are in."""
    variants = conn.execute(
        "SELECT id, label, variable_value FROM ab_variants WHERE test_id = ? ORDER BY label",
        (test_id,),
    ).fetchall()
    if len(variants) < 2:
        print(f"  {warn('Test has fewer than 2 variants — cannot score')}")
        return

    print(f"\n  {hdr('SCORE A/B TEST')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for v in variants:
        print(f"  {C.WHITE}[{v['label']}]{C.RESET}  {v['variable_value']}")

    for v in variants:
        while True:
            try:
                raw = input(f"  {C.CYAN}Rate {v['label']} ({v['variable_value']}) [1-5]: {C.RESET}").strip()
                rating = int(raw)
                if 1 <= rating <= 5:
                    conn.execute(
                        "UPDATE ab_variants SET rating = ? WHERE id = ?",
                        (rating, v["id"]),
                    )
                    break
            except (ValueError, EOFError):
                pass
            print(f"  {warn('Enter 1-5')}")

    # Pick winner
    print(f"\n  {C.CYAN}Winner? [A/B/tie]: {C.RESET}", end="")
    while True:
        try:
            raw = input().strip().upper()
            if raw in ("A", "B", "TIE"):
                winner = raw.lower() if raw == "TIE" else raw
                break
        except EOFError:
            pass
        print(f"  {warn('Enter A, B, or tie')}")

    # Optional notes
    notes = input(f"  {C.CYAN}Notes (optional): {C.RESET}").strip() or None

    conn.execute(
        """UPDATE ab_tests SET status = 'scored', winner = ?, notes = ?,
           scored_at = datetime('now') WHERE id = ?""",
        (winner, notes, test_id),
    )
    conn.commit()
    print(f"  {ok(f'✓ Scored — winner: {winner}')}")


def show_ab_history(conn: sqlite3.Connection) -> None:
    """Display past A/B test results."""
    rows = conn.execute(
        """SELECT t.id, s.name AS species, t.variable_axis, t.control_value,
                  t.variant_value, t.winner, t.status, t.created_at
           FROM ab_tests t JOIN species s ON s.id = t.species_id
           ORDER BY t.created_at DESC LIMIT 20""",
    ).fetchall()
    if not rows:
        print(f"\n  {dim('No A/B tests recorded yet.')}")
        return

    print(f"\n  {hdr('A/B TEST HISTORY (last 20)')}")
    print(f"  {C.DIM}" + "─" * 80 + C.RESET)
    hdr_fmt = f"  {C.WHITE}{'ID':>4}  {'Species':<20} {'Axis':<12} {'A':<15} {'B':<15} {'Win':>4}  {'Status':<8}{C.RESET}"
    print(hdr_fmt)
    print(f"  {C.DIM}" + "─" * 80 + C.RESET)
    for r in rows:
        win_display = r["winner"] or "–"
        if win_display == "A":
            win_color = C.GREEN
        elif win_display == "B":
            win_color = C.YELLOW
        else:
            win_color = C.DIM
        ctrl = r["control_value"][:14]
        var_ = r["variant_value"][:14]
        print(f"  {C.DIM}{r['id']:>4}{C.RESET}  {C.WHITE}{r['species']:<20}{C.RESET} "
              f"{dim(r['variable_axis'][:11]):<12} {ctrl:<15} {var_:<15} "
              f"{win_color}{win_display:>4}{C.RESET}  {dim(r['status'])}")
    print()


def show_species_ab_summary(conn: sqlite3.Connection, species_id: int, species_name: str) -> None:
    """Show winning parameter values for a species from scored A/B tests."""
    rows = conn.execute(
        """SELECT variable_axis,
                  CASE WHEN winner = 'A' THEN control_value
                       WHEN winner = 'B' THEN variant_value
                       ELSE NULL END AS winning_value,
                  winner, notes
           FROM ab_tests
           WHERE species_id = ? AND status = 'scored' AND winner IN ('A', 'B')
           ORDER BY variable_axis, scored_at DESC""",
        (species_id,),
    ).fetchall()
    if not rows:
        return
    print(f"\n  {hdr(f'A/B TEST WINS — {species_name}')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    for r in rows:
        axis_label = r["variable_axis"].replace("_", " ")
        r_notes = r["notes"]
        if r_notes:
            print(f"  {ok('★')} {dim(f'[{axis_label}]')} {C.WHITE}{r['winning_value']}{C.RESET}"
                  f"  {dim(f'({r_notes})')}")
        else:
            print(f"  {ok('★')} {dim(f'[{axis_label}]')} {C.WHITE}{r['winning_value']}{C.RESET}")
    print()


def ab_test_main(args) -> None:
    """A/B testing mode — generates two prompt variants for comparison."""
    conn = connect(args.db)
    _ensure_ab_tables(conn)
    global_rules = fetch_global_rules(conn)

    print(f"\n{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}A/B TESTING MODE{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")

    # Check for --ab-score: score an existing test instead of creating one
    if args.ab_score:
        test_id = args.ab_score
        test_row = conn.execute("SELECT id FROM ab_tests WHERE id = ?", (test_id,)).fetchone()
        if not test_row:
            print(f"  {warn(f'No A/B test found with id={test_id}')}")
            return
        score_ab_test(conn, test_id)
        return

    # Check for --ab-history: show past results
    if args.ab_history:
        show_ab_history(conn)
        return

    # --- Normal A/B test creation ---
    habitat = select_habitat()
    output_mode = select_mode(habitat)
    mode_cfg = OUTPUT_MODES[output_mode]

    perspective = select_perspective()

    placement = ("", "")
    if mode_cfg["needs_placement"]:
        placement = select_canvas_placement()

    species = pick_species(conn, habitat)
    science = fetch_species_science(conn, species["id"])
    notes = fetch_research_notes(conn, species["id"])
    display_science_brief(species, science, notes)

    # Show prior A/B wins for this species
    show_species_ab_summary(conn, species["id"], species["name"])

    # Per-species stylize
    anatomy = get_anatomy(species["name"])
    if anatomy and anatomy.recommended_stylize:
        s_low, s_default, s_high = anatomy.recommended_stylize
        if args.stylize is None:
            args.stylize = s_default
    elif args.stylize is None:
        args.stylize = 100

    # Select axis to vary
    axis = select_ab_axis()

    # Build base context using auto-picks
    style_param = CLADE_STYLE.get(habitat, CLADE_STYLE["terrestrial"])
    ctx = {
        "habitat": habitat, "species_name": species["name"],
        "diet": species["diet"] or "", "size_class": species["size_class"] or "",
        "output_mode": output_mode,
        "lighting": None, "mood": None, "behavior": None,
        "condition": None, "weather": None,
    }

    lighting_param = auto_pick_parameter(conn, "lighting", habitat, ctx)
    ctx["lighting"] = lighting_param["name"]
    camera_param = auto_pick_parameter(conn, "camera", habitat, ctx)

    if habitat == "plant":
        mood_param = {"id": 0, "name": "still", "value": "motionless, no wind, static"}
        condition_param = {"id": 0, "name": "healthy", "value": "healthy growth, no damage"}
        behavior_param = {"id": 0, "name": "growing", "value": "natural growth posture"}
    else:
        mood_sug = get_suggestions("mood", ctx)
        mood_blk = get_blocked("mood", ctx)
        mood_param = auto_pick_parameter(conn, "mood", habitat, ctx)
        ctx["mood"] = mood_param["name"]

        cond_sug = get_suggestions("condition", ctx)
        cond_blk = get_blocked("condition", ctx)
        condition_param = auto_pick_parameter(conn, "condition", habitat, ctx)
        ctx["condition"] = condition_param["name"]

        beh_sug = get_suggestions("behavior", ctx)
        beh_blk = get_blocked("behavior", ctx)
        behavior_param = auto_pick_parameter(conn, "behavior", habitat, ctx)
        ctx["behavior"] = behavior_param["name"]

    # Weather auto-pick
    all_weather = fetch_parameters_by_category(conn, "weather", habitat=habitat)
    sky = LIGHTING_SKY.get(lighting_param["name"], "mixed")
    compatible_weather = [w for w in all_weather
                         if "any" in WEATHER_SKY_COMPAT.get(w["name"], ("any",))
                         or sky in WEATHER_SKY_COMPAT.get(w["name"], ())]
    if not compatible_weather:
        compatible_weather = all_weather
    weather_param = dict(compatible_weather[0]) if compatible_weather else {"id": 0, "name": "clear", "value": "clear skies"}
    ctx["weather"] = weather_param["name"]

    # Current values for axis
    current_values = {
        "lighting": lighting_param["name"],
        "mood": mood_param["name"],
        "condition": condition_param["name"],
        "behavior": behavior_param["name"],
        "stylize": str(args.stylize),
        "output_mode": output_mode,
    }

    # Pick A/B values
    ctrl_val, var_val, ctrl_obj, var_obj = pick_ab_values(
        conn, axis, habitat, current_values[axis]
    )

    print(f"\n  {hdr('GENERATING A/B VARIANTS')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    print(f"  Axis:    {C.WHITE}{axis}{C.RESET}")
    print(f"  A:       {C.WHITE}{ctrl_val}{C.RESET}")
    print(f"  B:       {C.WHITE}{var_val}{C.RESET}")
    print()

    # Save the test
    test_id = save_ab_test(conn, species["id"], axis, ctrl_val, var_val)

    # --- Context-aware dual-ref selection for A/B tests (Session 21) ---
    ab_sref_urls = []
    ab_cref_urls = []
    ab_cref_source = ""
    if not args.sref:
        ab_sref_urls, ab_cref_urls, ab_cref_source = select_refs(
            species["name"], output_mode, habitat, lighting_param["name"]
        )
    else:
        ab_sref_urls = [args.sref]

    # Build both prompts
    required_params = fetch_species_required_params(conn, species["id"])
    variant_labels = [("A", ctrl_val, ctrl_obj), ("B", var_val, var_obj)]
    variant_prompts = []

    for label, val, obj in variant_labels:
        # Override the axis parameter
        v_lighting = lighting_param
        v_mood = mood_param
        v_condition = condition_param
        v_behavior = behavior_param
        v_stylize = args.stylize
        v_output_mode = output_mode
        v_mode_cfg = mode_cfg
        v_placement = placement

        if axis == "lighting":
            v_lighting = obj
        elif axis == "mood":
            v_mood = obj
        elif axis == "condition":
            v_condition = obj
        elif axis == "behavior":
            v_behavior = obj
        elif axis == "stylize":
            v_stylize = obj
        elif axis == "output_mode":
            v_output_mode = val
            v_mode_cfg = OUTPUT_MODES[val]
            if v_mode_cfg["needs_placement"] and placement == ("", ""):
                v_placement = ("center", "center frame")

        prompt_text = assemble_prompt(
            species, science, style_param, v_lighting, camera_param, v_mood,
            condition_param=v_condition,
            behavior_param=v_behavior,
            weather_param=weather_param,
            required_params=required_params,
            global_rules=global_rules,
            mj_style=args.style,
            stylize=v_stylize,
            chaos=args.chaos,
            quality=args.quality,
            output_mode=v_output_mode,
            placement=v_placement,
            has_sref=bool(ab_sref_urls or ab_cref_urls),
            habitat=habitat,
            perspective=perspective,
        )

        if ab_sref_urls:
            ab_sref_joined = " ".join(ab_sref_urls)
            prompt_text += f" --sref {ab_sref_joined} --sw {DEFAULT_SW}"
        # --cref disabled (Session 22) — manual CLI override still honored
        if args.cref:
            prompt_text += f" --cref {args.cref}"

        title = make_title(species, v_mood, output_mode=v_output_mode)
        tags = make_tags(species, style_param, v_lighting, camera_param, v_mood,
                         condition_param=v_condition, behavior_param=v_behavior,
                         weather_param=weather_param, output_mode=v_output_mode)

        prompt_id = save_prompt(
            conn,
            species_id=species["id"],
            title=f"[AB-{test_id}{label}] {title}",
            positive_prompt=prompt_text,
            tags=f"ab_test,test_{test_id},{tags}",
            parameter_ids=[],
        )

        save_ab_variant(conn, test_id, label, prompt_id, prompt_text, val)
        variant_prompts.append((label, val, prompt_text, prompt_id))

    # Display both variants
    for label, val, prompt_text, prompt_id in variant_prompts:
        variant_marker = "CONTROL" if label == "A" else "VARIANT"
        print(f"\n{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
        print(f"  {C.BOLD_CYAN}[{label}] {variant_marker}{C.RESET}  "
              f"{C.DIM}[{axis} = {val}]{C.RESET}")
        print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
        print_prompt_box(prompt_text)

        prose_only = strip_mj_params(prompt_text)
        clip_est = _estimate_clip_tokens(prose_only)
        if clip_est > 77:
            print(f"  {warn(f'⚠  CLIP tokens ≈ {clip_est}/77 — over budget')}")
        else:
            print(f"  {dim(f'CLIP tokens ≈ {clip_est}/77')}")

        print(f"\n  {hdr('/imagine prompt:')}")
        print(f"  {C.BRIGHT_WHITE}{prompt_text}{C.RESET}\n")

    # Summary
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}A/B TEST #{test_id} — READY{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  Species: {C.WHITE}{species['name']}{C.RESET}")
    print(f"  Axis:    {C.WHITE}{axis}{C.RESET}")
    print(f"  A:       {C.WHITE}{ctrl_val}{C.RESET}  (prompt id={variant_prompts[0][3]})")
    print(f"  B:       {C.WHITE}{var_val}{C.RESET}  (prompt id={variant_prompts[1][3]})")
    print()
    print(f"  {dim('Run both prompts in Midjourney, then score:')}")
    print(f"  {C.WHITE}python generate_prompt.py --ab-score {test_id}{C.RESET}")
    print(f"  {dim('View all results:')}")
    print(f"  {C.WHITE}python generate_prompt.py --ab-history{C.RESET}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactively build a Midjourney dinosaur art prompt."
    )
    parser.add_argument("--db",       type=Path,  default=DB_DEFAULT, metavar="PATH")
    # --version intentionally removed: set MJ model version in Midjourney settings
    parser.add_argument("--style",    default="raw",  choices=["raw", "default"], help="--style flag (default: raw)")
    # --ar intentionally removed: set aspect ratio globally in Midjourney settings
    parser.add_argument("--stylize",  type=int,   default=None,  metavar="N",   help="--stylize 0-1000 (default: species-specific)")
    parser.add_argument("--chaos",    type=int,   default=0,    metavar="N",   help="--chaos 0-100 (default: 0)")
    parser.add_argument("--quality",  type=float, default=1.0,  choices=[0.25, 0.5, 1.0], help="--q (default: 1.0)")
    parser.add_argument("--sref",     type=str,   default=None, metavar="URL", help="Style reference image URL appended as --sref")
    parser.add_argument("--cref",     type=str,   default=None, metavar="URL", help="Character reference image URL appended as --cref")
    # A/B testing (Session 17)
    parser.add_argument("--ab-test",    action="store_true", help="Enter A/B testing mode")
    parser.add_argument("--ab-score",   type=int,  default=None, metavar="ID", help="Score an existing A/B test by ID")
    parser.add_argument("--ab-history", action="store_true", help="Show A/B test history")
    args = parser.parse_args()

    # Route to A/B testing mode if any A/B flag is set
    if args.ab_test or args.ab_score or args.ab_history:
        ab_test_main(args)
        return

    conn = connect(args.db)
    global_rules = fetch_global_rules(conn)

    # --- Startup banner ---
    print(f"\n{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}DINOSAUR ART PROMPT GENERATOR{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")

    # --- Habitat selection (first thing the user sees) ---
    habitat = select_habitat()

    # --- Mode selection (filtered by habitat) ---
    output_mode = select_mode(habitat)
    mode_cfg    = OUTPUT_MODES[output_mode]

    # --- Camera perspective (angle override — any mode) ---
    perspective = select_perspective()

    placement: tuple[str, str] = ("", "")
    if mode_cfg["needs_placement"]:
        placement = select_canvas_placement()

    # --- Species (filtered by habitat) ---
    species = pick_species(conn, habitat)
    science = fetch_species_science(conn, species["id"])
    notes   = fetch_research_notes(conn, species["id"])
    display_science_brief(species, science, notes)

    # --- Per-species stylize recommendation (Session 17) ---
    anatomy = get_anatomy(species["name"])
    if anatomy and anatomy.recommended_stylize:
        s_low, s_default, s_high = anatomy.recommended_stylize
        if args.stylize is None:
            # No user override — use species-recommended default
            args.stylize = s_default
            print(f"  {ok('AUTO-APPLIED')} {dim('[stylize]')} {C.WHITE}--stylize {s_default}{C.RESET}")
            print(f"    {dim(f'Species range: {s_low} (low) / {s_default} (default) / {s_high} (high)')}")
        else:
            print(f"  {dim(f'User override: --stylize {args.stylize}  (species default: {s_default}, range {s_low}–{s_high})')}")
    elif args.stylize is None:
        args.stylize = 100  # global fallback

    # --- Display known failure modes (Session 17) ---
    if anatomy and anatomy.known_failures:
        sp_name = species["name"]
        print(f"\n  {hdr(f'⚠  KNOWN MJ FAILURE MODES — {sp_name}')}")
        print(f"  {C.DIM}" + "─" * 60 + C.RESET)
        for fail in anatomy.known_failures:
            print(f"  {C.YELLOW}⚠{C.RESET}  {C.WHITE}{fail}{C.RESET}")
        print()

    # --- Show A/B test wins for this species (Session 17) ---
    _ensure_ab_tables(conn)
    show_species_ab_summary(conn, species["id"], species["name"])

    # --- Multi-subject scene: pick secondary species (Session 17) ---
    secondary_species = None
    interaction_type = None
    if output_mode in MULTI_SUBJECT_MODES:
        secondary_species = pick_secondary_species(conn, species, output_mode)
        if secondary_species:
            if output_mode == "predator_prey":
                interaction_type = pick_interaction_type()
            else:
                interaction_type = "coexisting"

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

    # Style is always hyperrealism — hardcoded, not user-selectable.
    # Clade-specific so plants get "living plant tissue" and arthropods get
    # "living chitinous exoskeleton" instead of "living animal skin texture".
    style_param = CLADE_STYLE.get(habitat, CLADE_STYLE["terrestrial"])

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

    # --- Lighting: auto-selected from suggestion system (Session 14) ---
    lighting_param = auto_pick_parameter(conn, "lighting", habitat, ctx)
    ctx["lighting"] = lighting_param["name"]

    # --- Camera: auto-selected from suggestion system (Session 14) ---
    camera_param = auto_pick_parameter(conn, "camera", habitat, ctx)

    # Plants skip mood/behavior/condition — they don't have animal states
    if habitat == "plant":
        mood_param      = {"id": 0, "name": "still", "value": "motionless, no wind, static"}
        condition_param = {"id": 0, "name": "healthy", "value": "healthy growth, no damage"}
        behavior_param  = {"id": 0, "name": "growing", "value": "natural growth posture"}
        print(f"  {dim('(mood/behavior/condition skipped for plants)')}\n")
    else:
        mood_param = _cpick("mood", f"for {lighting_param['name'].replace('_', ' ')} lighting")
        ctx["mood"] = mood_param["name"]

        condition_param = _cpick("condition", f"for {species['name']} · {mood_param['name'].replace('_', ' ')}")
        ctx["condition"] = condition_param["name"]

        behavior_param = _cpick("behavior", f"for {mood_param['name'].replace('_', ' ')} mood")
        ctx["behavior"] = behavior_param["name"]

    # --- Weather: auto-selected with sky-compat filtering (Session 14) ---
    all_weather = fetch_parameters_by_category(conn, "weather", habitat=habitat)
    sky = LIGHTING_SKY.get(lighting_param["name"], "mixed")
    compatible_weather = [w for w in all_weather
                         if "any" in WEATHER_SKY_COMPAT.get(w["name"], ("any",))
                         or sky in WEATHER_SKY_COMPAT.get(w["name"], ())]
    if not compatible_weather:
        compatible_weather = all_weather
    weather_sug = get_suggestions("weather", ctx)
    weather_blk = get_blocked("weather", ctx)
    weather_param = None
    if weather_sug:
        for sug_name in weather_sug:
            for w in compatible_weather:
                if w["name"] == sug_name and w["name"] not in weather_blk:
                    weather_param = dict(w)
                    break
            if weather_param:
                break
    if not weather_param:
        for w in compatible_weather:
            if w["name"] not in weather_blk:
                weather_param = dict(w)
                break
    if not weather_param:
        weather_param = dict(compatible_weather[0])
    ctx["weather"] = weather_param["name"]

    # --- Display all auto-applied scene settings together ---
    print(f"\n  {hdr('SCENE SETTINGS (auto-applied)')}")
    print(f"  {C.DIM}" + "─" * 60 + C.RESET)
    print(f"    {ok('+')} {dim('[lighting]')} {C.WHITE}{lighting_param['name'].replace('_', ' ')}{C.RESET}")
    print(f"    {ok('+')} {dim('[camera]')}   {C.WHITE}{camera_param['name'].replace('_', ' ')}{C.RESET}")
    print(f"    {ok('+')} {dim('[weather]')}  {C.WHITE}{weather_param['name'].replace('_', ' ')}{C.RESET}")
    print()

    # --- Context-aware refs (Session 23: 3-layer system) ---
    # --sref: wildlife photos → photographic style guide
    # --cref: paleoart renditions → correct morphology (or skeletal fallback)
    sref_urls_list = []
    cref_urls_list = []
    cref_source = ""
    if not args.sref:
        sref_urls_list, cref_urls_list, cref_source = select_refs(
            species["name"], output_mode, habitat, lighting_param["name"]
        )
        all_sref_data = load_sref_urls()
        display_ref_selection(
            species["name"], sref_urls_list, cref_urls_list, cref_source,
            all_sref_data.get(species["name"], [])
        )
    else:
        # CLI --sref passed: use it as-is (single URL from command line)
        sref_urls_list = [args.sref]

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
        has_sref=bool(sref_urls_list or cref_urls_list),
        habitat=habitat,
        secondary_species=secondary_species,
        interaction_type=interaction_type,
        perspective=perspective,
    )

    title = make_title(species, mood_param, output_mode=output_mode)
    tags  = make_tags(species, style_param, lighting_param, camera_param, mood_param,
                      condition_param=condition_param, behavior_param=behavior_param,
                      weather_param=weather_param, output_mode=output_mode)

    # --- Append reference URLs to prompt ---
    # Session 22: wildlife --sref only, --cref disabled (too literal)
    if sref_urls_list:
        sref_joined = " ".join(sref_urls_list)
        prompt_text += f" --sref {sref_joined} --sw {DEFAULT_SW}"
    # --cref: skeletal refs for anatomical proportions (low --cw)
    if cref_urls_list:
        cref_joined = " ".join(cref_urls_list)
        prompt_text += f" --cref {cref_joined}"
    elif args.cref:
        prompt_text += f" --cref {args.cref}"

    # --- Build fix prompts ---
    period = species["period"] or "Other"
    if habitat in ("marine", "aerial", "arthropod", "plant"):
        env_key     = f"{habitat}_{period}"
        environment = ENVIRONMENTS.get(env_key, ENVIRONMENTS.get(f"{habitat}_Other", ENVIRONMENTS["Other"]))
    else:
        environment = ENVIRONMENTS.get(period, ENVIRONMENTS["Other"])

    feet_fix_prompt = None if habitat == "plant" else make_feet_fix_prompt(species, mj_style=args.style)
    env_fix_prompt  = make_environment_fix_prompt(
        species, environment, weather_param, lighting_param, mj_style=args.style
    )

    # --- Display ---
    mode_label = mode_cfg["display"].upper()
    persp_label = CAMERA_PERSPECTIVES.get(perspective, {}).get("display", "")

    # STEP 1 — Main prompt
    habitat_label = habitat.upper()
    persp_tag = f" / {persp_label}" if perspective != "default" else ""
    print(f"\n{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"  {C.BOLD_CYAN}STEP 1 — MAIN PROMPT{C.RESET}  {C.DIM}[{habitat_label} / {mode_label}{persp_tag}]{C.RESET}")
    print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
    print(f"\n  {C.WHITE}Title :{C.RESET} {C.BRIGHT_WHITE}{title}{C.RESET}")
    print(f"  {C.WHITE}Tags  :{C.RESET} {dim(tags)}")
    if sref_urls_list:
        sref_display = f"{len(sref_urls_list)} wildlife refs (--sw {DEFAULT_SW})"
        print(f"  {C.WHITE}sref  :{C.RESET} {dim(sref_display)}")
    if cref_urls_list:
        cref_display = f"{len(cref_urls_list)} {cref_source} refs"
        print(f"  {C.WHITE}cref  :{C.RESET} {dim(cref_display)}")
    elif args.cref:
        print(f"  {C.WHITE}cref  :{C.RESET} {dim(args.cref)}")
    print()
    validate_prompt(prompt_text, allow_mj_params=True,  label="STEP 1 main")
    print_prompt_box(prompt_text)

    # Session 17: CLIP token budget indicator
    prose_only = strip_mj_params(prompt_text)
    clip_est = _estimate_clip_tokens(prose_only)
    if clip_est > 77:
        print(f"  {warn(f'⚠  CLIP tokens ≈ {clip_est}/77 — over budget, MJ will truncate tail phrases')}")
    elif clip_est > 60:
        print(f"  {dim(f'CLIP tokens ≈ {clip_est}/77 — approaching limit')}")
    else:
        print(f"  {dim(f'CLIP tokens ≈ {clip_est}/77')}")

    print(f"\n  {hdr('/imagine prompt:')}")
    print(f"  {C.BRIGHT_WHITE}{prompt_text}{C.RESET}\n")

    # STEP 2 — Extremity fix (feet / flipper / wing / legs) — skipped for plants
    if feet_fix_prompt:
        step2_labels = {
            "terrestrial": ("FEET FIX", "feet"), "marine": ("FLIPPER FIX", "flippers"),
            "aerial": ("WING FIX", "wings"), "arthropod": ("LEGS/APPENDAGE FIX", "legs"),
        }
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

    # STEP 4 — Mouth fix — skipped for plants
    if habitat != "plant":
        mouth_fix_prompt = make_mouth_fix_prompt(species, mj_style=args.style)
        mouth_fix_clean  = strip_mj_params(mouth_fix_prompt)
        validate_prompt(mouth_fix_clean, allow_mj_params=False, label="STEP 4 mouth fix")
        step4_label = "MOUTHPART FIX" if habitat == "arthropod" else "MOUTH FIX"
        step4_region = "mandibles/chelicerae" if habitat == "arthropod" else "mouth/jaw"
        print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
        print(f"  {C.BOLD_CYAN}STEP 4 — {step4_label}{C.RESET}  {C.DIM}[Vary Region → paint over {step4_region}]{C.RESET}")
        print(f"{C.BOLD_CYAN}{'═' * 64}{C.RESET}")
        print_prompt_box(mouth_fix_clean)
        print(f"\n  {hdr('/imagine prompt:')}")
        print(f"  {C.BRIGHT_WHITE}{mouth_fix_clean}{C.RESET}\n")

    # --- Save ---
    saved_param_ids = (
        [rp["id"] for rp in required_params]
        + [style_param["id"], lighting_param["id"], mood_param["id"],
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
