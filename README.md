# Clipsal C-Bus Home Assistant Integration

A custom Home Assistant integration for the **Clipsal 5500SHAC** (Wiser C-Bus Network Automation Controller), communicating directly via its WebSocket API — no MQTT broker, no C-Gate, no middleware required.

## Features

- 💡 **Lights** — dimmable, real-time bidirectional sync
- 🌀 **Fans** — on/off control
- 🪟 **Blinds & Curtains** — open/close/position control
- ❄️ **Air Conditioning** — power, mode (Cool/Heat/Fan/Dry/Auto), fan speed, current & set temperature
- 🎬 **Scenes** — trigger C-Bus scenes from HA
- 👁️ **Motion Sensors** — real-time occupancy detection
- 🚨 **Alarms** — smoke and gas alarm monitoring
- 🌡️ **Temperature Sensors** — per-zone current temperature

## Requirements

- Home Assistant 2024.1 or later
- Clipsal 5500SHAC on your local network
- Network access between HA and the SHAC (default port 8087)

## Installation

### Manual

1. Copy the `homeassistant_clipsal_cbus` folder to your `config/custom_components/` directory
2. **Edit `const.py`** to match your device layout (see [Device Configuration](#device-configuration) below)
3. Restart Home Assistant
4. Go to **Settings → Integrations → Add Integration**
5. Search for **Clipsal C-Bus**
6. Enter your SHAC IP address and port (default: 8087)

### HACS

Add this repository as a custom repository in HACS.

## Device Configuration

> ⚠️ **Important:** The `const.py` file shipped with this integration contains the device layout for a specific installation (Apartment 1002). **You must edit this file to match your own C-Bus installation before use.**

Open `custom_components/homeassistant_clipsal_cbus/const.py` and update the following dictionaries to match your installation:

### Lights
```python
LIGHTS = {
    1: "Living Room Downlights",   # group number: friendly name
    2: "Dining Room Downlights",
    # add or remove entries to match your installation
}
```

### Fans
```python
FANS = {
    12: "Powder Room Fan",   # group number: friendly name
}
```

### Blinds & Curtains
```python
BLINDS = {
    40: "Dining Curtain",   # group number: friendly name
}
```

### Scenes
```python
SCENES = {
    0: "Goodbye",   # group number: scene name
    1: "Welcome Home",
}
```

### Motion Sensors
```python
MOTION_SENSORS = {
    18: "Occupancy",   # group number: friendly name
}
```

### Alarms
```python
ALARMS = {
    9:  ("Fire Alarm", "smoke"),   # group number: (name, type)
    10: ("Gas Alarm",  "gas"),
}
```

### Air Conditioning Zones

AC zones require the most configuration as each zone has multiple C-Bus group addresses. You will need to identify the correct group numbers for your installation by monitoring the WebSocket traffic in your browser's Developer Tools (Network → WS) while operating the AC from the SHAC web UI at `http://<SHAC-IP>:8087`.

```python
AC_ZONES = {
    "Master Bedroom": {
        "power":          0,   # group that turns AC on/off (0=off, 255=on)
        "mode":           3,   # group that sets mode (Cool/Heat/Fan/Dry/Auto)
        "fan":            2,   # group that sets fan speed
        "temp_up":        6,   # group to pulse for temperature increase
        "temp_down":      17,  # group to pulse for temperature decrease
        "cur_temp_group": 2,   # App 250 group for current room temperature
        "set_temp_group": 13,  # App 250 group for set point temperature
        "mode_map":       AC_MODE_MAP,      # use AC_MODE_MAP unless your zone differs
        "fan_map":        AC_FAN_MAP,       # use AC_FAN_MAP unless your zone differs
        "hvac_to_cbus":   AC_HVAC_TO_CBUS, # use AC_HVAC_TO_CBUS unless your zone differs
    },
}
```

### AC Mode and Fan Values

The default mode and fan value maps were determined by reverse engineering the WebSocket traffic on a specific installation:

```python
# Mode values — may differ on your installation, verify via WebSocket traffic
AC_MODE_MAP = {0: "off", 10: "heat", 20: "cool", 30: "fan_only", 40: "dry", 50: "auto"}

# Fan speed values — may differ on your installation
AC_FAN_MAP = {20: "low", 30: "medium", 40: "high", 50: "auto"}
```

> **Note:** These values are not standardised across all 5500SHAC installations. If your modes or fan speeds are incorrect, monitor the WebSocket messages while changing modes on the physical wall controller or SHAC web UI, and update the maps to match the values you observe.

## Finding Your Group Numbers

The easiest way to find the correct group numbers for your installation is:

1. Open your SHAC web UI at `http://<SHAC-IP>:8087`
2. Open your browser's Developer Tools (F12)
3. Go to **Network → WS** and click on the WebSocket connection
4. Go to the **Messages** tab
5. Operate a device (turn on a light, change AC mode, etc.)
6. Look for the `groupwrite` message — the `dst` field shows the address in `network/app/group` format

For example, `"dst":"0\/56\/1"` means App 56 (Lighting), Group 1.

## How It Works

The 5500SHAC exposes a WebSocket endpoint at `ws://<ip>:8087/scada-vis/objects/ws`. This integration maintains a persistent connection, receiving real-time `groupwrite` events and translating them to HA entity state updates. Commands from HA are sent as JSON write commands over the same connection.

State updates may have a slight delay as the SHAC only broadcasts changes when something happens on the C-Bus network.

## Troubleshooting

**Integration not appearing in the list:**
- Verify the `homeassistant_clipsal_cbus` folder is in `config/custom_components/`
- Check that `manifest.json` is valid JSON
- Restart Home Assistant and check logs for errors

**Cannot connect:**
- Verify the SHAC IP address and port (default 8087)
- Confirm the SHAC web UI is accessible at `http://<ip>:8087`
- Check that HA can reach the SHAC on your network

**Wrong modes or fan speeds:**
- Monitor WebSocket traffic in the SHAC web UI while changing settings
- Update `AC_MODE_MAP`, `AC_FAN_MAP` and `AC_HVAC_TO_CBUS` in `const.py` to match observed values

**Devices not updating:**
- The SHAC only sends updates when something changes — state will populate as you use devices
- Check HA logs for WebSocket connection errors

## Author

[@UNsync3D](https://github.com/UNsync3D)

## License

MIT
