DOMAIN = "homeassistant_clipsal_cbus"
DEFAULT_PORT = 8087

APP_LIGHTING = 56
APP_COOLMASTER = 48
APP_SCENES = 202
APP_USER_PARAM = 250
APP_SECURITY = 208

LIGHTS = {
    1:  "Living Room Downlights",
    2:  "Dining Room Downlights",
    3:  "Kitchen Downlights",
    4:  "Hallway Downlights",
    5:  "Bedroom 2 Downlights",
    6:  "Master Bedroom Downlights",
    7:  "Ensuite Downlights",
    8:  "Rooftop Lights",
    9:  "Balcony Downlights",
    10: "Kitchen LED Strip",
    11: "Powder Room Downlights",
    13: "Staircase Lights",
    14: "Bathroom Downlights",
    17: "Ensuite LED Strip",
}

FANS = {
    12: "Powder Room Fan",
    20: "Ensuite Fan",
}

BLINDS = {
    40: "Dining Curtain",
    41: "Living Curtain",
    42: "Master Curtain",
    43: "Bedroom Blind",
    44: "Bedroom Curtain",
    45: "Master Blind",
    46: "Dining Blind",
    47: "Living Blind",
}

SCENES = {
    0: "Goodbye",
    1: "Welcome Home",
    2: "Goodnight",
    3: "Relax",
    4: "Entertain",
    5: "Movie",
}

MOTION_SENSORS = {
    18: "Occupancy",
    19: "Ensuite PIR",
}

ALARMS = {
    9:  ("Fire Alarm",  "smoke"),
    10: ("Gas Alarm",   "gas"),
}

# All zones share the same mode values
AC_MODE_MAP     = {0: "off", 10: "heat", 20: "cool", 30: "fan_only", 40: "dry", 50: "auto"}
AC_MODE_MAP_INV = {v: k for k, v in AC_MODE_MAP.items()}
AC_HVAC_TO_CBUS = {"heat": 10, "cool": 20, "fan_only": 30, "dry": 40, "auto": 50}

# Master Bedroom and Living Room fan values
AC_FAN_MAP      = {20: "low", 30: "medium", 40: "high", 50: "auto"}
AC_FAN_MAP_INV  = {v: k for k, v in AC_FAN_MAP.items()}

# Bedroom 2 has different fan values (auto=60 instead of 50)
B2_FAN_MAP      = {20: "low", 30: "medium", 40: "high", 60: "auto"}
B2_FAN_MAP_INV  = {v: k for k, v in B2_FAN_MAP.items()}

AC_ZONES = {
    "Master Bedroom": {
        "power": 0,  "mode": 3,  "fan": 2,
        "temp_up": 6, "temp_down": 17,
        "cur_temp_group": 2,
        "set_temp_group": 13,
        "mode_map":     AC_MODE_MAP,
        "fan_map":      AC_FAN_MAP,
        "hvac_to_cbus": AC_HVAC_TO_CBUS,
    },
    "Bedroom 2": {
        "power": 4,  "mode": 7,  "fan": 6,
        "temp_up": 18, "temp_down": 9,
        "cur_temp_group": 3,
        "set_temp_group": 23,
        "mode_map":     AC_MODE_MAP,
        "fan_map":      B2_FAN_MAP,
        "hvac_to_cbus": AC_HVAC_TO_CBUS,
    },
    "Living Room": {
        "power": 8,  "mode": 11, "fan": 10,
        "temp_up": 12, "temp_down": 13,
        "cur_temp_group": 4,
        "set_temp_group": 33,
        "mode_map":     AC_MODE_MAP,
        "fan_map":      AC_FAN_MAP,
        "hvac_to_cbus": AC_HVAC_TO_CBUS,
    },
}
