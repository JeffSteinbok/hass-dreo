# hass-dreo vs Official hass-dreoverse: Comparative Analysis

**Date:** March 2026  
**Purpose:** Decision document for evaluating whether to migrate hass-dreo to the official Dreo API used by hass-dreoverse, or to collaborate/merge with the official integration.

---

## Executive Summary

The official Dreo team has released their own Home Assistant integration (`hass-dreoverse`) that uses a **fundamentally different API** from what `hass-dreo` uses. The official integration communicates via a **public/open API** (`open-api-{region}.dreo-tech.com`) while our integration uses the **internal mobile app API** (`app-api-{region}.dreo-tech.com`). The official API is more standardized, uses a simpler REST-based polling architecture, and is backed by a published PyPI library (`pydreo-cloud`). However, the official integration is currently **less mature in device support**, **uses polling instead of push**, and has **43 open issues** indicating growing pains. Our integration supports more device types and uses WebSocket push for real-time updates.

**Recommendation:** Consider a phased migration to the official Open API while preserving our WebSocket push architecture. The official API is more sustainable long-term since it's sanctioned by Dreo and less likely to break without notice.

---

## 1. API Architecture Comparison

### 1.1 API Endpoints

| Aspect | hass-dreo (Ours) | hass-dreoverse (Official) |
|--------|-----------------|--------------------------|
| **Base URL** | `https://app-api-{region}.dreo-tech.com` | `https://open-api-{region}.dreo-tech.com` |
| **API Type** | Internal mobile app API (reverse-engineered) | Official Open API (sanctioned by Dreo) |
| **Login** | `POST /api/oauth/login` | `POST /api/oauth/login` |
| **Device List** | `GET /api/v2/user-device/device/list` | `GET /api/device/list` |
| **Device State** | `GET /api/user-device/device/state` | `GET /api/device/state` |
| **Device Control** | Via WebSocket only | `POST /api/device/control` |
| **Settings** | `GET/PUT /api/user-device/setting` | N/A (via control endpoint) |
| **WebSocket** | `wss://wsb-{region}.dreo-tech.com/websocket` | `wss://wsb-{region}.dreo-tech.com/websocket` (in pydreo-cloud lib, but NOT used by integration) |

**Key Difference:** The official API has a **dedicated REST endpoint for device control** (`/api/device/control`), while our integration sends all commands through WebSocket. The official integration currently **doesn't use WebSocket at all** — it relies entirely on REST polling.

### 1.2 Authentication

| Aspect | hass-dreo (Ours) | hass-dreoverse (Official) |
|--------|-----------------|--------------------------|
| **Grant Type** | `email-password` | `openapi` |
| **Client ID** | `7de37c362ee54dcf9c4561812309347a` | `89ef537b2202481aaaf9077068bcb0c9` |
| **Client Secret** | `32dfa0764f25451d99f94e1693498791` | `41b20a1f60e9499e89c8646c31f93ea1` |
| **Password Handling** | MD5 hashed before sending | MD5 hashed before sending (done in config_flow) |
| **User Agent** | `dreo/2.8.2` / `okhttp/4.9.1` | `openapi/1.0.0` |
| **Region Detection** | Auth region in API response body | Token suffix format: `token:EU` or `token:NA` |
| **Extra Fields** | `himei`, `encrypt`, `acceptLanguage` | None (cleaner request) |

**Key Difference:** The official API uses `grant_type: "openapi"` with different client credentials, indicating it's a separate, officially-provisioned API surface. Our integration mimics the mobile app with `grant_type: "email-password"`.

### 1.3 Device Control

| Aspect | hass-dreo (Ours) | hass-dreoverse (Official) |
|--------|-----------------|--------------------------|
| **Command Mechanism** | WebSocket messages | REST POST to `/api/device/control` |
| **Command Format** | `{"devicesn": ..., "method": "control", "params": {...}, "timestamp": ...}` | `{"devicesn": ..., "desired": {...}}` |
| **Acknowledgment** | Waits for WebSocket ACK (2s timeout) | HTTP response (synchronous) |
| **Retry Logic** | 3 retries with 5s delay on WebSocket | None (HTTP error handling) |
| **Serialization** | Custom command serialization to prevent drops | None needed (HTTP is inherently serialized per-request) |

**Key Difference:** Our WebSocket command pipeline is more complex but provides real-time push updates. The official REST approach is simpler but requires polling for state changes.

### 1.4 State Updates

| Aspect | hass-dreo (Ours) | hass-dreoverse (Official) |
|--------|-----------------|--------------------------|
| **IoT Class** | `cloud_push` | `cloud_polling` |
| **Update Method** | WebSocket push (real-time) | REST polling every 15 seconds |
| **State Freshness** | Near-instantaneous | Up to 15s delay |
| **Connection Overhead** | Persistent WebSocket connection | Periodic HTTP requests |
| **Auto-Reconnect** | Yes (configurable) | N/A (polling reconnects naturally) |

**Key Difference:** This is the most significant architectural difference. Our push-based approach gives much better responsiveness, but the official polling approach is simpler and more resilient.

---

## 2. Integration Architecture Comparison

### 2.1 Code Organization

| Aspect | hass-dreo (Ours) | hass-dreoverse (Official) |
|--------|-----------------|--------------------------|
| **API Library** | Embedded `pydreo/` package (14+ files) | External PyPI package `pydreo-cloud==1.0.0` |
| **Device Classes** | Per-device-type Python classes (e.g., `PyDreoTowerFan`, `PyDreoHeater`) | Single coordinator with data classes per type |
| **State Management** | Device objects with properties + callbacks | `DataUpdateCoordinator` pattern (HA standard) |
| **Entity Pattern** | Custom base entities, manual `schedule_update_ha_state()` | `CoordinatorEntity` (HA standard pattern) |
| **HA Patterns** | Partially follows HA patterns | Follows HA patterns closely (quality_scale: bronze) |
| **Config Entry** | `hass.data[DOMAIN]` storage | `runtime_data` (modern HA pattern) |
| **Platforms** | Fan, Climate, Humidifier, Light, Sensor, Switch, Number | Fan, Climate, Humidifier, Light, Sensor, Switch, Number, **Select** |
| **Quality Scale** | N/A | Bronze (working toward official inclusion) |

**Key Difference:** The official integration follows modern Home Assistant architecture patterns more closely, using `DataUpdateCoordinator`, `CoordinatorEntity`, `runtime_data`, and `has_entity_name`. It's structured for potential inclusion as an official HA integration.

### 2.2 Device Configuration Model

**hass-dreo (Ours):**
- Device capabilities are defined in Python code per model
- Hardcoded model-to-class mappings
- New device support requires code changes to the embedded pydreo library
- Device type classes: `PyDreoTowerFan`, `PyDreoAirCirculator`, `PyDreoCeilingFan`, `PyDreoHeater`, `PyDreoAC`, `PyDreoHumidifier`, `PyDreoDehumidifier`, `PyDreoChefMaker`, `PyDreoEvaporativeCooler`, `PyDreoAirPurifier`

**hass-dreoverse (Official):**
- Device capabilities come from **server-side configuration** (`config` field in device list response)
- The `config` field contains entity specifications: which entities to create, speed ranges, preset modes, temperature ranges, etc.
- Entity generation is **data-driven** from the API response
- Uses `DreoEntityConfigSpec` keys like `fan_entity_config`, `light_entity_config`, `toggle_entity_config`, etc.
- New devices can potentially work **without code changes** if the server provides correct config

**This is a critical difference.** The official API returns device capability metadata alongside the device list, making the integration more adaptable to new devices without code updates. Our approach requires manual mapping of every model's capabilities.

### 2.3 Entity Generation

**hass-dreo (Ours):**
```
Device JSON → Model prefix lookup → Hardcoded device class → Hardcoded entity mappings
```

**hass-dreoverse (Official):**
```
Device JSON (includes config) → Config-driven entity creation → Dynamic entity generation
```

The official integration reads entity configuration from the server response:
- `fan_entity_config`: Speed range, preset modes, oscillation support
- `light_entity_config`: Brightness range, color temperature range
- `toggle_entity_config`: Switch entities with fields, icons, operableWhenOff flags
- `number_entity_config`: Numeric controls with ranges and step sizes
- `sensor_entity_config`: Sensor types with units and device classes
- `select_entity_config`: Selection entities with options
- `humidifier_entity_config`: Humidity ranges and mode configs
- `heater_entity_config`: Heater-specific settings

---

## 3. Device Support Comparison

### 3.1 Supported Device Categories

| Device Type | hass-dreo (Ours) | hass-dreoverse (Official) |
|-------------|-----------------|--------------------------|
| Tower Fans (HTF) | ✅ 9 models | ✅ 8+ models |
| Air Circulators (HAF/HPF) | ✅ 9 models | ✅ 10+ models |
| Ceiling Fans (HCF) | ✅ 3 models | ✅ 1 tested model |
| Air Purifiers (HAP) | ✅ 4 models | ❌ Not listed (but device type exists in code) |
| Space Heaters (HSH/WH) | ✅ 12 models | ✅ Added in v2.1.3 |
| Air Conditioners (HAC) | ✅ 2 models | ✅ 1 model |
| Humidifiers (HHM) | ✅ 4 models | ❓ Listed as HEC category |
| Dehumidifiers (HDH) | ✅ 3 models | ✅ Added in v2.1.1 |
| ChefMaker (KCM) | ✅ 1 model | ❌ "Only KCM001/KCM002 unsupported" |
| Evaporative Coolers (HEC) | ✅ 1 model | ✅ 1 model |

**Total tested models: hass-dreo ~54, hass-dreoverse ~25+**

### 3.2 Entity Types

| Entity Type | hass-dreo (Ours) | hass-dreoverse (Official) |
|-------------|-----------------|--------------------------|
| Fan | ✅ | ✅ |
| Climate | ✅ | ✅ |
| Humidifier | ✅ | ✅ |
| Light | ✅ (display + RGB) | ✅ (display + RGB) |
| Sensor | ✅ | ✅ |
| Switch | ✅ | ✅ |
| Number | ✅ | ✅ |
| **Select** | ❌ | ✅ (oscillation direction, etc.) |

---

## 4. Dependency & Maintenance Comparison

### 4.1 Dependencies

| Aspect | hass-dreo (Ours) | hass-dreoverse (Official) |
|--------|-----------------|--------------------------|
| **Runtime Deps** | `websockets` | `pydreo-cloud==1.0.0` |
| **pydreo-cloud deps** | N/A | `requests`, `tzlocal`, `pycryptodome`, `websocket-client` |
| **API Library** | Embedded (we maintain it) | External PyPI (Dreo maintains it) |
| **HA Version Req** | Not specified | 2024.8.0+ (hacs.json), 2024.12.0+ (release notes) |

### 4.2 Maintenance & Activity

| Aspect | hass-dreo (Ours) | hass-dreoverse (Official) |
|--------|-----------------|--------------------------|
| **Current Version** | 1.6.3 | 2.2.1 |
| **First Release** | ~2023 (Homebridge origin) | May 2025 (v1.0.0) |
| **Latest Release** | Active | Feb 2026 (v2.2.1) |
| **Open Issues** | Active community | 43 open issues |
| **Maintainer** | @JeffSteinbok (community) | @dreo-team / @w-xtao (official) |
| **Test Suite** | pytest + pylint CI | Minimal (quality_scale bronze) |
| **HACS Status** | Default repository | Custom repository (applying for default) |
| **Official HA Goal** | N/A | Actively working toward official inclusion |

### 4.3 Key Issue from pydreo-client

Issue #11 on pydreo-client was filed by @JeffSteinbok noting that the password parameter needs to be MD5 hashed before passing to the client. This indicates some awareness/interaction between the projects.

---

## 5. Strengths & Weaknesses

### hass-dreo (Ours) - Strengths
1. **Real-time push updates** via WebSocket — much better UX than 15s polling
2. **Broader device support** — 54+ tested models vs 25+
3. **Mature codebase** — years of community testing and bug fixes
4. **Comprehensive test suite** — unit tests, integration tests, CI/CD
5. **ChefMaker support** — unique to our integration
6. **Air Purifier support** — not available in official
7. **Battle-tested** WebSocket reconnection and command serialization

### hass-dreo (Ours) - Weaknesses
1. **Reverse-engineered API** — could break without notice if Dreo changes their mobile app API
2. **Embedded library** — we maintain the full API library in-repo
3. **Hardcoded device models** — adding new devices requires code changes
4. **Older HA patterns** — doesn't use `DataUpdateCoordinator` or `CoordinatorEntity`
5. **No path to official** — can never become an official HA integration (unofficial API)

### hass-dreoverse (Official) - Strengths
1. **Official/sanctioned API** — less likely to break unexpectedly
2. **Server-driven device config** — new devices can work without code changes
3. **Modern HA patterns** — `DataUpdateCoordinator`, `CoordinatorEntity`, `runtime_data`
4. **Path to official** — actively working toward official HA integration inclusion
5. **Dedicated REST control endpoint** — simpler command model
6. **Dreo team maintains API library** — we don't need to maintain the protocol layer
7. **Select entity support** — additional entity type

### hass-dreoverse (Official) - Weaknesses
1. **Polling-only (15s)** — no WebSocket push for real-time updates
2. **Fewer tested devices** — ~25 tested vs our 54+
3. **43 open issues** — many device-specific bugs and missing features
4. **Less mature** — first release May 2025 vs our years of development
5. **No ChefMaker** — explicitly unsupported
6. **No Air Purifier** — not listed in supported devices
7. **External dependency risk** — `pydreo-cloud` is maintained by Dreo team with infrequent updates

---

## 6. Migration Options

### Option A: Full Migration to Official Open API
**Replace our embedded pydreo library with the official Open API (`open-api-{region}`)**

- **Effort:** Very High
- **Pros:** Official API, sustainable long-term, server-driven config
- **Cons:** Lose WebSocket push, need to rewrite all device classes, temporarily lose device coverage
- **Risk:** Medium — the official API may not support all our device types yet

### Option B: Hybrid — Switch API Layer, Keep WebSocket
**Use the Open API endpoints for auth/device-list/control but maintain our WebSocket connection for push updates**

- **Effort:** High
- **Pros:** Best of both worlds — official API + real-time push
- **Cons:** More complex architecture, WebSocket might use different auth with Open API
- **Risk:** Medium — WebSocket compatibility with Open API tokens is unverified
- **Note:** The `pydreo-cloud` library already has a `DreoWebSocketClient` class, suggesting the Open API supports WebSocket too, just unused by the integration

### Option C: Adopt Server-Driven Config Model
**Keep our API layer but adopt the official integration's config-driven entity generation pattern**

- **Effort:** Medium-High
- **Pros:** Easier device onboarding, more maintainable
- **Cons:** Still using unofficial API, need to understand the config schema
- **Risk:** Low — incremental improvement, doesn't change API layer

### Option D: Modernize HA Patterns Only
**Keep everything but refactor to use `DataUpdateCoordinator`, `CoordinatorEntity`, and `runtime_data`**

- **Effort:** Medium
- **Pros:** Better HA alignment, easier maintenance, potential for official inclusion path
- **Cons:** Doesn't address API sustainability concerns
- **Risk:** Low — purely internal refactoring

### Option E: Collaborate/Merge with Official
**Work with Dreo team to contribute our device support and WebSocket architecture to the official integration**

- **Effort:** Medium (contribution work)
- **Pros:** Single, comprehensive integration; Dreo team support; path to official
- **Cons:** Loss of control, dependent on Dreo team's review/merge timeline
- **Risk:** Medium — requires Dreo team cooperation; they may have different priorities

### Option F: Do Nothing
**Continue as-is, maintaining our independent integration**

- **Effort:** Ongoing maintenance
- **Pros:** No disruption, maintained feature set
- **Cons:** Risk of mobile app API breaking, growing divergence from official
- **Risk:** High long-term — Dreo could deprecate the app API or change authentication

---

## 7. Recommended Approach

**Phase 1 (Short-term): Option D — Modernize HA Patterns**
- Refactor to use `DataUpdateCoordinator` and `CoordinatorEntity`
- Switch to `runtime_data` pattern
- Add `has_entity_name = True`
- This improves maintainability and aligns with HA standards

**Phase 2 (Medium-term): Option B — Hybrid API Migration**
- Switch authentication to Open API (`grant_type: "openapi"`)
- Switch device list and state queries to Open API endpoints
- Test whether Open API tokens work with WebSocket endpoint
- Add REST control endpoint as fallback for WebSocket commands
- Maintain WebSocket push for real-time state updates

**Phase 3 (Long-term): Option C + E — Config-Driven + Collaboration**
- Adopt server-driven config model from device list responses
- Begin contributing device support upstream to official integration
- Evaluate whether full merge makes sense once official integration matures

---

## 8. Technical Details for Migration

### 8.1 API Endpoint Changes Required

```
# Authentication
OLD: POST https://app-api-{region}.dreo-tech.com/api/oauth/login
     grant_type: "email-password", client_id: "7de37...", client_secret: "32dfa..."
NEW: POST https://open-api-{region}.dreo-tech.com/api/oauth/login
     grant_type: "openapi", client_id: "89ef5...", client_secret: "41b20..."

# Device List
OLD: GET https://app-api-{region}.dreo-tech.com/api/v2/user-device/device/list
NEW: GET https://open-api-{region}.dreo-tech.com/api/device/list

# Device State
OLD: GET https://app-api-{region}.dreo-tech.com/api/user-device/device/state
NEW: GET https://open-api-{region}.dreo-tech.com/api/device/state

# Device Control (NEW — currently done via WebSocket only)
NEW: POST https://open-api-{region}.dreo-tech.com/api/device/control
     Body: {"devicesn": "...", "desired": {"power_switch": true, "speed": 5}}

# WebSocket (may work with both APIs — needs testing)
SAME: wss://wsb-{region}.dreo-tech.com/websocket?accessToken={token}&timestamp={ts}
```

### 8.2 Response Format Differences

**Device List Response — Official API includes `config` field:**
```json
{
  "deviceSn": "...",
  "model": "DR-HTF007S",
  "deviceName": "My Fan",
  "deviceType": "fan",
  "config": {
    "fan_entity_config": {
      "speed_range": [1, 6],
      "preset_modes": ["1", "2", "3", "4"]
    },
    "toggle_entity_config": {
      "child_lock": {"field": "childlock", "operableWhenOff": false},
      "oscillation": {"field": "oscillate", "operableWhenOff": false}
    },
    "sensor_entity_config": {...},
    "number_entity_config": {...}
  },
  "state": {
    "connected": true,
    "power_switch": true,
    "speed": 3,
    "mode": 1
  }
}
```

### 8.3 Command Format Changes

```python
# OLD (WebSocket)
{
    "devicesn": "ABC123",
    "method": "control",
    "params": {"speed": 5},
    "timestamp": 1710000000000
}

# NEW (REST)
POST /api/device/control
{
    "devicesn": "ABC123",
    "desired": {"speed": 5}
}
```

### 8.4 Files That Would Need Changes

For **Phase 2 (Hybrid API Migration)**:
1. `pydreo/constant.py` — Update API URLs, client credentials, endpoint paths
2. `pydreo/helpers.py` — Update request construction, headers (User-Agent to `openapi/1.0.0`)
3. `pydreo/__init__.py` — Update login flow (grant_type), region detection (token suffix)
4. `pydreo/commandtransport.py` — Add REST fallback for device control
5. `pydreo/pydreobasedevice.py` — Update command sending to support REST
6. All device files — Update `send_command()` calls if format changes

---

## 9. Open Questions

1. **Does the Open API token work with the WebSocket endpoint?** The `pydreo-cloud` library has a `DreoWebSocketClient` that uses the same `wss://wsb-{region}.dreo-tech.com` endpoint, suggesting it does.

2. **Does the Open API return device `config` metadata?** The official integration heavily relies on this. Need to verify the response format.

3. **Are all our device types supported by the Open API?** ChefMaker and Air Purifier may not be available via the Open API.

4. **Rate limiting:** The official library handles HTTP 429. Does the Open API have stricter rate limits than the app API?

5. **Will Dreo deprecate the mobile app API?** This is the key risk question. If they move all mobile app users to a new API, our integration would break.

6. **Can we contribute WebSocket support to the official integration?** This would benefit both projects.

7. **Does the pydreo-cloud WebSocket work for push state updates, or just control?** Need to test whether state changes are pushed via WebSocket with Open API tokens.

---

## 10. References

- **hass-dreoverse:** https://github.com/dreo-team/hass-dreoverse
- **pydreo-cloud (PyPI):** https://pypi.org/project/pydreo-cloud/
- **pydreo-client (GitHub):** https://github.com/dreo-team/pydreo-client
- **hass-dreo (this repo):** https://github.com/JeffSteinbok/hass-dreo
- **pydreo-client Issue #11 (password hashing):** https://github.com/dreo-team/pydreo-client/issues/11
- **pydreo-client Issue #14 (collaboration):** https://github.com/dreo-team/pydreo-client/issues/14
