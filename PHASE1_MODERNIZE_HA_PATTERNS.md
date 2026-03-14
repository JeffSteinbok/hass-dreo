# Phase 1: Modernize Home Assistant Patterns

**Branch:** `phase1/modernize-ha-patterns`  
**Goal:** Refactor the integration to use modern HA architecture patterns while keeping our existing API layer and WebSocket push intact.  
**Risk:** Low — purely internal refactoring, no API changes.  
**Estimated Scope:** ~15-20 files modified

---

## Why This Matters

Our integration works great, but it uses older HA patterns that make maintenance harder and block any future path to official HA inclusion. The official dreoverse integration already uses these modern patterns. Adopting them makes our codebase cleaner and sets us up for Phase 2+3 regardless of which direction we go.

### Current Pattern Problems

1. **`hass.data[DOMAIN]` storage** — Deprecated in favor of `runtime_data` on the config entry. Our approach pollutes the global `hass.data` namespace and doesn't properly scope data to the config entry lifecycle.

2. **Manual `schedule_update_ha_state()`** — Every entity control method must manually call this. Easy to forget (we've had bugs from this — see humidifier/dehumidifier fixes). The `CoordinatorEntity` pattern handles this automatically.

3. **Callback spaghetti** — Our data flow is: `WebSocket → pydreo device object (sets properties) → calls callback → HA entity callback calls schedule_update_ha_state()`. With `DataUpdateCoordinator`, entities automatically react to coordinator updates.

4. **No `has_entity_name = True`** — Modern HA entities use this so device names aren't duplicated in entity names.

5. **Platform loading is overly complex** — We manually determine which platforms to load based on device types found. The modern pattern loads all platforms and lets each platform's setup filter devices.

---

## Detailed Refactoring Plan

### Step 1: Create `DreoDataUpdateCoordinator`

**New file:** `custom_components/dreo/coordinator.py`

This coordinator wraps our existing PyDreo device objects. Unlike the official integration which uses REST polling, ours will be **push-based** — the coordinator's `_async_update_data` will be a no-op (or a periodic state refresh), and WebSocket pushes will call `coordinator.async_set_updated_data()`.

```
Current flow:
  WebSocket msg → pydreo device._handle_server_update() → device.callback() → HA entity.schedule_update_ha_state()

New flow:
  WebSocket msg → pydreo device._handle_server_update() → coordinator.async_set_updated_data(device) → all CoordinatorEntities auto-update
```

**Key design decisions:**
- One coordinator per device (same as official integration)
- Coordinator holds reference to the PyDreo device object
- WebSocket callback triggers `async_set_updated_data`
- Optional periodic refresh as fallback (e.g., every 60s via REST)
- Preserves our `cloud_push` IoT class

### Step 2: Create `DreoBaseEntity(CoordinatorEntity)`

**Modify:** `custom_components/dreo/dreobasedevice.py`

Replace the current `DreoBaseDeviceHA` with a `CoordinatorEntity`-based class:

```python
# Current pattern (dreobasedevice.py):
class DreoBaseDeviceHA(Entity):
    def __init__(self, pydreo_device):
        self.device = pydreo_device
        # Manual callback registration
        self.device.add_attr_callback(self.ha_callback)
    
    def ha_callback(self):
        self.schedule_update_ha_state()

# New pattern:
class DreoBaseEntity(CoordinatorEntity[DreoDataUpdateCoordinator]):
    _attr_has_entity_name = True
    
    def __init__(self, coordinator, pydreo_device, ...):
        super().__init__(coordinator)
        self._device = pydreo_device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, pydreo_device.serial_number)},
            manufacturer="Dreo",
            model=pydreo_device.model,
            name=pydreo_device.name,
        )
```

### Step 3: Switch to `runtime_data`

**Modify:** `custom_components/dreo/__init__.py`

```python
# Current:
hass.data[DOMAIN] = {}
hass.data[DOMAIN][PYDREO_MANAGER] = pydreo_manager

# New:
@dataclass
class DreoRuntimeData:
    manager: PyDreo
    coordinators: dict[str, DreoDataUpdateCoordinator]

type DreoConfigEntry = ConfigEntry[DreoRuntimeData]
config_entry.runtime_data = DreoRuntimeData(manager=pydreo_manager, coordinators=coordinators)
```

### Step 4: Simplify Platform Loading

**Modify:** `custom_components/dreo/__init__.py`

```python
# Current: Complex if/elif chain checking device types
# New: Load all platforms, let each platform filter
PLATFORMS = [Platform.FAN, Platform.CLIMATE, Platform.HUMIDIFIER, 
             Platform.LIGHT, Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]
await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
```

Each platform's `async_setup_entry` already filters by device type, so this is safe.

### Step 5: Update All Entity Classes

**Files to modify:**
- `dreofan.py` → Use `DreoBaseEntity`, remove manual `schedule_update_ha_state()` calls
- `dreoheater.py` → Same pattern
- `dreohumidifier.py` → Same pattern  
- `dreodehumidifier.py` → Same pattern
- `light.py` → Same pattern
- `sensor.py` → Same pattern
- `switch.py` → Same pattern
- `number.py` → Same pattern

For each entity class:
1. Inherit from `DreoBaseEntity` instead of `DreoBaseDeviceHA`
2. Accept `coordinator` in `__init__`
3. Remove all `schedule_update_ha_state()` calls from control methods
4. Properties still read from `self._device` (the pydreo object) — this is unchanged
5. The coordinator triggers UI updates automatically when WebSocket pushes arrive

### Step 6: Wire Up WebSocket → Coordinator Bridge

**Modify:** `custom_components/dreo/__init__.py` (in `async_setup_entry`)

After creating coordinators and starting transport, wire the pydreo device callbacks to coordinator updates:

```python
for device in pydreo_manager.devices:
    coordinator = coordinators[device.serial_number]
    
    def make_callback(coord, dev):
        def _callback():
            coord.async_set_updated_data(dev)
        return _callback
    
    device.add_attr_callback(make_callback(coordinator, device))
```

### Step 7: Update `async_unload_entry`

Clean up using config_entry.runtime_data instead of hass.data.

---

## Files Changed (Complete List)

| File | Change Type | Description |
|------|------------|-------------|
| `coordinator.py` | **NEW** | DreoDataUpdateCoordinator class |
| `__init__.py` | **MODIFY** | runtime_data, coordinator setup, simplified platform loading |
| `dreobasedevice.py` | **MODIFY** | DreoBaseEntity(CoordinatorEntity) |
| `dreofan.py` | **MODIFY** | Use new base, remove schedule_update_ha_state |
| `dreoheater.py` | **MODIFY** | Use new base, remove schedule_update_ha_state |
| `dreohumidifier.py` | **MODIFY** | Use new base, remove schedule_update_ha_state |
| `dreodehumidifier.py` | **MODIFY** | Use new base, remove schedule_update_ha_state |
| `light.py` | **MODIFY** | Use new base, remove schedule_update_ha_state |
| `sensor.py` | **MODIFY** | Use new base, remove schedule_update_ha_state |
| `switch.py` | **MODIFY** | Use new base, remove schedule_update_ha_state |
| `number.py` | **MODIFY** | Use new base, remove schedule_update_ha_state |
| `config_flow.py` | **MODIFY** | Minor — unique_id, options flow |
| `fan.py` | **MODIFY** | Pass coordinators to entities |
| `climate.py` | **MODIFY** | Pass coordinators to entities |
| `humidifier.py` | **MODIFY** | Pass coordinators to entities |
| `const.py` | **MODIFY** | Remove PYDREO_MANAGER constant |
| `manifest.json` | **MODIFY** | Bump version |
| `haimports.py` | **MODIFY** | Add CoordinatorEntity imports |

---

## What Does NOT Change

- **PyDreo library** (`pydreo/` directory) — Completely untouched
- **API endpoints** — Same mobile app API
- **WebSocket transport** — Same push architecture
- **Device models/capabilities** — Same hardcoded model definitions
- **All existing features** — Feature parity guaranteed
- **Test structure** — Tests updated to use new patterns but same coverage

---

## Testing Strategy

1. All existing pytest tests must pass (update mocks for coordinator pattern)
2. Integration tests with e2e_test_data JSON must pass
3. Manual testing: verify WebSocket push still triggers immediate UI updates
4. Verify that `schedule_update_ha_state()` removal doesn't break anything

---

## Migration Path for Users

- **No breaking changes** — Entity IDs unchanged
- **No reconfiguration** — Config entries unchanged
- **Transparent upgrade** — Users won't notice any difference except potentially snappier UI updates
