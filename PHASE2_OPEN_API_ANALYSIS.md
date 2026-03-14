# Phase 2+3: Open API Migration + Server-Driven Config Analysis

**Branch:** `phase2/open-api-server-driven-config`  
**Goal:** Evaluate switching to the Open API and adopting server-driven config  
**Key Question:** Does the Open API return everything we need?  
**Short Answer:** No — not even close, and we already do most of what "server-driven config" means.

---

## Part 1: What "Server-Driven Config" Actually Means (And What We Already Do)

The previous migration analysis overstated the difference. Let's be precise:

### What the Official Integration Calls "Server-Driven Config"

The Open API's `/api/device/list` response includes a `config` field per device that contains:
- `entitySupports` — which HA platforms to create (fan, climate, sensor, switch, number, light, select)
- `fan_entity_config` — speed_range, preset_modes
- `heater_entity_config` — hvac_modes, temperature_range, preset_modes, hvac_mode_relate_map
- `toggle_entity_config` — which toggle switches exist, their field names, operableWhenOff flags
- `sensor_entity_config` — which sensors, their directive names, device classes, icons
- `number_entity_config` — slide components with ranges, directive names
- `humidifier_entity_config` — humidity ranges, mode configs
- `light_entity_config` — brightness range, color temperature range
- `select_entity_config` — select options with directive names

### What We Already Do (Our "Server-Driven" Aspects)

| Capability | Our Approach | Official Approach | Gap? |
|-----------|-------------|-------------------|------|
| **Feature detection** (does device have mute? PTC? child lock?) | ✅ Auto-detected from API state — if `muteon` field exists, we show the switch | Config declares `toggle_entity_config.mute_switch` | **None — ours is actually MORE adaptive** |
| **State values** (current temp, speed, mode) | ✅ Fully from API + WebSocket push | ✅ From API polling | None |
| **Entity creation** (which platforms) | Derived from device type | Declared in `entitySupports` | Minor |
| **Speed ranges** | ❌ Hardcoded in models.py per model | ✅ From `fan_entity_config.speed_range` | **Gap — but small** |
| **Temperature ranges** | ❌ Hardcoded in models.py per model | ✅ From `heater_entity_config.temperature_range` | **Gap — but small** |
| **Humidity ranges** | ❌ Hardcoded in models.py per model | ✅ From `humidifier_entity_config.humidity_range` | **Gap — but small** |
| **Preset modes** | ❌ Hardcoded in models.py per model | ✅ From config | **Gap — but small** |
| **Oscillation angles** | ❌ Hardcoded in models.py per model | ✅ From config (fixed_angle, oscrange) | Gap |
| **HVAC mode mapping** | ❌ Hardcoded in dreoheater.py | ✅ From `hvac_mode_relate_map` | Gap |
| **Number entity ranges** | ✅ Partially from device + hardcoded fallback | ✅ From `slide_component` config | Minor |

### Bottom Line on "Server-Driven Config"

**Our feature detection is BETTER than theirs** — we detect features dynamically from API state (if a field exists in the response, we create the entity). They require the server to explicitly declare features in the config.

**Where we're worse:** Numeric ranges (speed 1-9, temp 41-85) and preset mode lists are hardcoded per model in our `models.py`. The official integration gets these from the server config.

**But this is a SMALL win**, because:
1. Ranges rarely change for a given model — it's a "set once" value
2. Adding a new model to our `models.py` is trivial (one dict entry)
3. The official integration still has hardcoded device type → processing logic (their coordinator.py has separate data classes and processors per device type, just like we do)

---

## Part 2: The Field Name Problem — Why We Can't Just Switch APIs

### Different API, Different Field Names

This is the critical issue. The two APIs use **completely different field names for the same data**.

#### Our API (Mobile App API) State Fields → Official API (Open API) Directive Names

| Our Field Name | Official Directive Name | Same? | Notes |
|---------------|------------------------|-------|-------|
| `poweron` | `power_switch` | ❌ DIFFERENT | |
| `fanon` | `power_switch` | ❌ DIFFERENT | We distinguish fan-on vs power-on |
| `windlevel` | `speed` | ❌ DIFFERENT | |
| `windtype` | `mode` | ❌ DIFFERENT | We call it windtype, they call it mode |
| `windmode` | *(no equivalent)* | ❌ MISSING | |
| `temperature` | `temperature` | ✅ Same | |
| `oscon` | `oscillate` | ❌ DIFFERENT | |
| `hoscon` | *(no equivalent)* | ❌ MISSING | Horizontal oscillation |
| `voscon` | *(no equivalent)* | ❌ MISSING | Vertical oscillation |
| `hoscangle` | *(mapped differently)* | ❌ | They use hoscrange/voscrange |
| `voscangle` | *(mapped differently)* | ❌ | |
| `oscmode` | `oscmode` | ✅ Same | |
| `oscangle` | `oscangle` | ✅ Same | |
| `cruiseconf` | *(no equivalent)* | ❌ MISSING | Cruise configuration string |
| `fixedconf` | *(mapped differently)* | ❌ | They use hfixedangle/vfixedangle |
| `hangleadj` | *(no equivalent)* | ❌ MISSING | Horizontal angle adjustment |
| `ledalwayson` | *(no equivalent)* | ❌ MISSING | LED always on |
| `voiceon` | *(no equivalent)* | ❌ MISSING | Voice control on |
| `lightsensoron` | `lightsensor_switch` | ❌ DIFFERENT | |
| `muteon` | `mute_switch` | ❌ DIFFERENT | |
| `lighton` | `light_switch` | ❌ DIFFERENT | Or `lightmode` |
| `brightness` | `brightness` | ✅ Same | |
| `colortemp` | `colortemp` | ✅ Same | |
| `ecolevel` | `ecolevel` | ✅ Same | |
| `htalevel` | `htalevel` | ✅ Same | |
| `mode` | `mode` | ✅ Same | |
| `childlockon` | `childlock_switch` | ❌ DIFFERENT | |
| `ptcon` | *(no equivalent)* | ❌ MISSING | PTC heater element status |
| `devon` | *(no equivalent)* | ❌ MISSING | Dev mode on |
| `timeron` | *(no equivalent)* | ❌ MISSING | Timer on (complex sub-field) |
| `timeroff` | *(no equivalent)* | ❌ MISSING | Timer off |
| `cooldown` | *(no equivalent)* | ❌ MISSING | Cooldown timer |
| `ctlstatus` | *(no equivalent)* | ❌ MISSING | Control status |
| `tempoffset` | *(no equivalent)* | ❌ MISSING | Temperature offset |
| `pm25` | *(no equivalent)* | ❌ MISSING | PM2.5 sensor |
| `rh` | `humidity_sensor` | ❌ DIFFERENT | |
| `rhautolevel` | *(no equivalent)* | ❌ MISSING | Auto humidity target |
| `rhlevel` | *(no equivalent)* | ❌ MISSING | Target humidity level |
| `rhtarget` | `humidity` | ❌ DIFFERENT | |
| `rhmode` | `humidity_mode` | ❌ DIFFERENT | |
| `worktime` | *(no equivalent)* | ❌ MISSING | Work time counter |
| `reachtarget` | *(no equivalent)* | ❌ MISSING | Target reached status |
| `sleeptempoffset` | *(no equivalent)* | ❌ MISSING | Sleep temp offset |
| `atmon` | `ambient_switch` | ❌ DIFFERENT | |
| `atmcolor` | `atmcolor` | ✅ Same | |
| `atmbri` | `atmbri` | ✅ Same | |
| `atmmode` | `atmmode` | ✅ Same | |
| `rgblevel` | *(no equivalent)* | ❌ MISSING | RGB indicator level |
| `scheon` | *(no equivalent)* | ❌ MISSING | Schedule enable |
| `shakehorizon` | *(no equivalent)* | ❌ MISSING | Horizontal shake |
| `shakehorizonangle` | *(no equivalent)* | ❌ MISSING | Shake angle |
| `wrong` (water level) | *(no equivalent)* | ❌ MISSING | Water level status |
| `autoon` | *(no equivalent)* | ❌ MISSING | Auto mode on |
| `ledpotkepton` | *(no equivalent)* | ❌ MISSING | ChefMaker light |
| `templevel` | *(no equivalent)* | ❌ MISSING | AC target temp |
| `hvacmode` | `hvacmode` | ✅ Same | |

### Score Card

| Category | Count |
|----------|-------|
| **Same field name** | ~12 fields |
| **Different field name** | ~15 fields |
| **Missing from Open API entirely** | ~25+ fields |
| **Total fields we use** | ~61 fields |

### What This Means

**~25 fields we use don't exist in the Open API at all.** These are features that work in our integration today that would be lost:

- **Timer controls** (timeron, timeroff, cooldown)
- **PTC heater element status** (ptcon) — we infer power state from this
- **PM2.5 air quality** (pm25)
- **Voice control toggle** (voiceon)
- **LED always-on toggle** (ledalwayson)
- **Work time counter** (worktime)
- **Target reached indicator** (reachtarget)
- **Schedule enable** (scheon)
- **Shake/oscillation variants** (shakehorizon, shakehorizonangle)
- **Water level status** (wrong)
- **Dev mode** (devon)
- **Control status** (ctlstatus)
- **Temperature offset/calibration** (tempoffset, sleeptempoffset)
- **Auto humidity modes** (rhautolevel, rhlevel)
- **RGB indicator level** (rgblevel)
- **ChefMaker light** (ledpotkepton)
- **AC target temperature** (templevel)
- **Horizontal oscillation** (hoscon) as separate from general oscillation
- **Vertical oscillation** (voscon) as separate from general oscillation
- **Cruise configuration** (cruiseconf)
- **Horizontal angle adjustment** (hangleadj)

---

## Part 3: The Command Name Problem

It's not just state reading — **command sending uses different field names too**.

```python
# Our integration sends commands like:
{"method": "control", "params": {"poweron": true, "windlevel": 5}}

# Official API expects:
{"devicesn": "...", "desired": {"power_switch": true, "speed": 5}}
```

Every device class would need its commands translated. And some commands we send have **no equivalent** in the Open API.

---

## Part 4: Device Type Coverage Gaps

| Device Type | Our Integration | Open API |
|-------------|----------------|----------|
| Tower Fans | ✅ Full support | ✅ Supported |
| Air Circulators | ✅ Full support | ✅ Supported |
| Ceiling Fans | ✅ Full support | ✅ Basic support |
| Air Purifiers | ✅ Full support | ⚠️ Exists in code but untested |
| Heaters | ✅ Full support (12 models) | ✅ Added v2.1.3 (limited) |
| Air Conditioners | ✅ Full support | ✅ Basic support |
| Humidifiers | ✅ Full support (4 models) | ⚠️ Mapped to HEC category? |
| Dehumidifiers | ✅ Full support | ✅ Basic support |
| **ChefMaker** | ✅ Full support | ❌ Explicitly unsupported |
| Evaporative Coolers | ✅ Full support | ✅ Basic support |

The Open API has **43 open issues** on their integration, many related to missing features that our integration already handles.

---

## Part 5: What Would We Actually Gain?

### Gains from switching to Open API:
1. ✅ Official API — won't break without notice
2. ✅ Speed/temp/humidity ranges from server config (no more hardcoding in models.py)
3. ✅ Preset modes from server config
4. ✅ REST control endpoint as WebSocket backup
5. ✅ Path toward official HA integration

### Losses from switching to Open API:
1. ❌ **~25 features/fields lost** (timers, PTC status, PM2.5, voice control, etc.)
2. ❌ ChefMaker support completely lost
3. ❌ Many device-specific features lost (cruise config, angle adjustments, etc.)
4. ❌ Massive rework of all device classes (field name translation)
5. ❌ User-facing feature regression

---

## Part 6: Recommendation

### Don't switch APIs. Instead, improve what we have.

**The Open API is designed for basic device control.** It's a simplified abstraction over the full device capabilities. Our mobile app API gives us access to the FULL device feature set. That's why we support 54+ models with deep feature coverage, while the official integration has 43 open issues with 25 tested models.

### What we SHOULD do instead:

#### 1. Stay on the mobile app API (it's not going away — the mobile app uses it)

The mobile app API is the same API that millions of Dreo app users rely on. Dreo can't break it without breaking their own app. The risk of it "disappearing" is near zero.

#### 2. Reduce our hardcoded model config (from our own API, not theirs)

Our mobile app API's `controlsConf` field already contains useful metadata that we currently IGNORE:
- The heater `controlsConf.schedule.modes` already lists available modes with their commands, value ranges, and types
- `controlsConf.preference` lists available settings (mute, display, child lock) with their command names
- `controlsConf.control` has oscillation type info
- `controlsConf.category` has the device category string

**We can parse our OWN API's controlsConf to reduce hardcoding.** This is a much simpler and lower-risk path than switching APIs entirely.

#### Specific improvements from parsing controlsConf:

From heater `controlsConf.schedule.modes`:
```json
{
  "cmd": "mode",
  "value": "eco",
  "controls": [{ "cmd": ["ecolevel"], "startValue": 41, "endValue": 95 }]
}
```
→ **We can extract ecolevel range (41-95) instead of hardcoding it!**

From heater `controlsConf.preference`:
```json
{ "type": "Panel Sound", "cmd": "muteon" },
{ "type": "Display Auto Off", "cmd": "lighton" },
{ "type": "Child Lock", "cmd": "childlockon" }
```
→ **We can auto-detect available switches instead of the hardcoded master list!**

#### 3. Monitor the Open API for feature parity

If the Open API ever achieves feature parity with the mobile app API (same fields, same coverage), THEN consider switching. Today it's not even close.

---

## Part 7: Concrete Action Items for This Phase

### Instead of "Switch to Open API", do this:

1. **Parse `controlsConf` from our OWN API to reduce hardcoding**
   - Extract speed ranges from schedule modes
   - Extract temperature ranges from schedule modes
   - Extract available preferences (switches)
   - Extract available modes and their value types
   - Use this as the "server-driven config" source — from OUR API, not theirs

2. **Add fallback logic for unknown models**
   - If a model isn't in `SUPPORTED_DEVICES`, attempt to auto-configure from `controlsConf`
   - This gives us "works without code changes for new devices" behavior
   - Still use hardcoded overrides for models where controlsConf is incomplete

3. **Add a REST control endpoint as backup**
   - The official API's `POST /api/device/control` could be useful as a WebSocket fallback
   - Investigate whether the mobile app API has a similar REST control endpoint we missed
   - This doesn't require switching APIs entirely

4. **Add a `Select` entity type**
   - The official integration has this (for oscillation direction, etc.)
   - We can add this using our existing API — no API switch needed

---

## Appendix A: Full `controlsConf` Field Map (From Our API)

### What our mobile app API already returns but we don't use:

| controlsConf Field | Contains | Currently Used? |
|-------------------|----------|----------------|
| `template` | Model reference | ✅ (for logging) |
| `schedule.modes` | Available modes with ranges | ❌ UNUSED — has speed/temp ranges! |
| `schedule.modes[].controls` | Value ranges per mode | ❌ UNUSED — has startValue/endValue! |
| `preference` | Available settings/switches | ❌ UNUSED — has switch list! |
| `control` | Oscillation type, features | ❌ UNUSED |
| `cards` | UI cards config | ❌ Not needed |
| `feature` | Schedule support, firmware | ❌ Not needed |
| `category` | Device category string | ❌ Could replace hardcoded type |
| `lottie` | Animation config | ❌ Not needed |
| `instructions` | Help URLs | ❌ Not needed |
| `version` | Min app version | ❌ Not needed |

### Example: Auto-detecting heater config from controlsConf

```python
# Parse modes from controlsConf
modes_config = controls_conf.get("schedule", {}).get("modes", [])
for mode in modes_config:
    mode_name = mode.get("value")  # "hotair", "eco", "coolair"
    for control in mode.get("controls", []):
        cmd = control.get("cmd", [])
        if "ecolevel" in cmd:
            eco_range = (control["startValue"], control["endValue"])  # (41, 95)
        elif "htalevel" in cmd:
            hta_range = (control["startValue"], control["endValue"])  # (0, 3)

# Parse switches from preferences  
prefs = controls_conf.get("preference", [])
available_switches = {p["cmd"]: p["type"] for p in prefs if "cmd" in p}
# → {"muteon": "Panel Sound", "lighton": "Display Auto Off", "childlockon": "Child Lock"}
```

This gives us the SAME benefits as the official "server-driven config" without losing ANY features.

---

## Appendix B: Field Names That Match Between APIs

These are the only fields where a simple API switch would "just work":

```
temperature, mode, ecolevel, htalevel, oscmode, oscangle,
brightness, colortemp, atmcolor, atmbri, atmmode, hvacmode,
foglevel, humidity_mode
```

**That's ~14 out of 61 fields.** The other 47 would need translation or would be lost entirely.
