"""Dreo HomeAssistant Integration."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

from .haimports import *  # pylint: disable=W0401,W0614
from .const import DOMAIN, PYDREO_MANAGER, DREO_PLATFORMS, CONF_AUTO_RECONNECT, DEBUG_TEST_MODE

if TYPE_CHECKING:
    from .pydreo import PyDreo

_LOGGER = logging.getLogger(__name__)


def _install_ha_call_later_scheduler(
    hass: HomeAssistant,
    pydreo_manager: "PyDreo",
    config_entry: ConfigEntry,
) -> None:
    """Route PyDreo delayed work through HA ``async_call_later``.

    Lifecycle (maintainers)
    -----------------------
    - **Install**: called once from ``async_setup_entry`` after ``PyDreo`` is
      constructed. Failures are caught by setup and fall back to Timer.
    - **Schedule**: may be invoked from HA **executor** threads (entity setters).
      Posts onto the **event loop** via ``call_soon_threadsafe`` →
      ``async_call_later``; when due, ``work`` runs in an **executor job** so
      device I/O never blocks the loop.
    - **Cancel**: device ``dispose()`` / ``stop_transport`` and this function's
      returned cancel handles; ``config_entry.async_on_unload`` cancels any
      remaining handles and clears the host scheduler on integration unload.
    """
    from homeassistant.core import callback as ha_callback  # pylint: disable=C0415
    from homeassistant.helpers.event import async_call_later  # pylint: disable=C0415

    # List (not set): async_call_later unsub callables are hashable, but a list
    # avoids any set/hash edge cases and keeps cancellation order stable. All
    # mutations run under active_lock (may be touched from executor + loop).
    active_cancel_handles: list[Callable[[], None]] = []
    active_lock = threading.Lock()

    def schedule_call_later(delay: float, work: Callable[[], None]) -> Callable[[], None]:
        """Schedule ``work`` after delay; return a thread-safe cancel function.

        Parameter is named ``work`` (not ``callback``) so it does not shadow the
        Home Assistant ``@ha_callback`` / ``@callback`` decorator used below.
        """
        cancelled = threading.Event()
        # Filled on the event loop when async_call_later returns its unsub handle.
        cancel_handle_box: list[Callable[[], None] | None] = [None]

        @ha_callback
        def _on_timer(_now) -> None:
            with active_lock:
                cancel_handle = cancel_handle_box[0]
                if cancel_handle is not None:
                    try:
                        active_cancel_handles.remove(cancel_handle)
                    except ValueError:
                        pass
                    cancel_handle_box[0] = None
            if cancelled.is_set():
                return
            # Device I/O (_send_command / websockets) is synchronous — run off the
            # event loop so settle work never blocks HA.
            hass.async_add_executor_job(work)

        def _schedule_on_loop() -> None:
            if cancelled.is_set():
                return
            cancel_handle = async_call_later(hass, delay, _on_timer)
            cancel_handle_box[0] = cancel_handle
            with active_lock:
                active_cancel_handles.append(cancel_handle)

        hass.loop.call_soon_threadsafe(_schedule_on_loop)

        def cancel() -> None:
            cancelled.set()

            def _cancel_on_loop() -> None:
                cancel_handle = cancel_handle_box[0]
                if cancel_handle is None:
                    return
                try:
                    cancel_handle()
                except Exception as ex:  # pylint: disable=broad-except
                    # Teardown race: handle may already be invalid.
                    _LOGGER.debug("schedule_call_later.cancel: handle failed: %s", ex)
                finally:
                    with active_lock:
                        try:
                            active_cancel_handles.remove(cancel_handle)
                        except ValueError:
                            pass
                    cancel_handle_box[0] = None

            try:
                hass.loop.call_soon_threadsafe(_cancel_on_loop)
            except RuntimeError:
                # Event loop already closed during shutdown.
                pass

        return cancel

    pydreo_manager.set_schedule_call_later(schedule_call_later)

    def _cancel_all_pending() -> None:
        # Integration unload: cancel every outstanding settle timer, then drop
        # the host scheduler so any late schedule_call_later uses Timer (or no-ops
        # after devices are disposed).
        with active_lock:
            pending = list(active_cancel_handles)
            active_cancel_handles.clear()
        for cancel_handle in pending:
            try:
                cancel_handle()
            except Exception as ex:  # pylint: disable=broad-except
                # Unload must finish even if a handle is already dead; log and continue.
                _LOGGER.debug(
                    "_cancel_all_pending: cancel_handle failed (%s): %s",
                    type(ex).__name__,
                    ex,
                )
        pydreo_manager.set_schedule_call_later(None)

    config_entry.async_on_unload(_cancel_all_pending)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    "HomeAssistant EntryPoint"
    _LOGGER.debug("async_setup_entry: Starting setup")

    _LOGGER.debug("async_setup_entry: Username: %s", config_entry.data.get(CONF_USERNAME))
    username = config_entry.data.get(CONF_USERNAME)
    password = config_entry.data.get(CONF_PASSWORD)
    auto_reconnect = config_entry.options.get(CONF_AUTO_RECONNECT)
    if auto_reconnect is None:
        _LOGGER.debug("async_setup_entry: auto_reconnect is None.  Default to True")
        auto_reconnect = True

    region = config_entry.data.get(CONF_REGION)
    if region == "auto":
        region = None

    from .pydreo import PyDreo  # pylint: disable=C0415
    from .pydreo.constant import DreoDeviceType  # pylint: disable=C0415

    if DEBUG_TEST_MODE:
        _LOGGER.error("async_setup_entry: DEBUG_TEST_MODE is True!")
        from .debug_test_mode import get_debug_test_mode_payload  # pylint: disable=C0415

        debug__test_mode_payload: dict = get_debug_test_mode_payload("custom_components/dreo")
        if debug__test_mode_payload is None:
            _LOGGER.error("async_setup_entry: Unable to get debug test mode payload.  Exiting setup.")
            return False
        pydreo_manager = PyDreo("TEST_EMAIL", "TEST_PASSWORD", redact=True, debug_test_mode=True, debug_test_mode_payload=debug__test_mode_payload)
    else:
        pydreo_manager = PyDreo(username, password, region=region)
        pydreo_manager.auto_reconnect = auto_reconnect

    # Prefer HA event-loop timers over raw threading.Timer for delayed device work.
    try:
        _install_ha_call_later_scheduler(hass, pydreo_manager, config_entry)
        _LOGGER.debug(
            "async_setup_entry: installed HA async_call_later scheduler for PyDreo"
        )
    except Exception as ex:  # pylint: disable=broad-except
        # Integration continues with threading.Timer fallback; surface clearly.
        _LOGGER.warning(
            "async_setup_entry: failed to install HA call_later scheduler "
            "(%s: %s); delayed fixedconf settle will use threading.Timer fallback",
            type(ex).__name__,
            ex,
        )

    login = await hass.async_add_executor_job(pydreo_manager.login)

    if not login:
        _LOGGER.error("async_setup_entry: Unable to login to the dreo server")
        raise ConfigEntryNotReady("Unable to login to the Dreo server")

    load_devices = await hass.async_add_executor_job(pydreo_manager.load_devices)

    if not load_devices:
        _LOGGER.error("async_setup_entry: Unable to load devices from the dreo server")
        raise ConfigEntryNotReady("Unable to load devices from the Dreo server")

    _LOGGER.debug("async_setup_entry: Checking for supported installed device types")
    device_types = set()
    for device in pydreo_manager.devices:
        device_types.add(device.type)
    _LOGGER.debug("async_setup_entry: Device types found are: %s", device_types)
    _LOGGER.info("async_setup_entry: %d Dreo devices found", len(pydreo_manager.devices))

    platforms = set()
    if (
        DreoDeviceType.TOWER_FAN in device_types
        or DreoDeviceType.AIR_CIRCULATOR in device_types
        or DreoDeviceType.AIR_PURIFIER in device_types
        or DreoDeviceType.CEILING_FAN in device_types
    ):
        platforms.add(Platform.FAN)
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)

    if DreoDeviceType.CEILING_FAN in device_types or DreoDeviceType.AIR_CIRCULATOR in device_types:
        platforms.add(Platform.LIGHT)
    if DreoDeviceType.CEILING_FAN in device_types:
        # Diagnostic main-power sensor; see binary_sensor.py.
        platforms.add(Platform.BINARY_SENSOR)
    if DreoDeviceType.AIR_CIRCULATOR in device_types:
        platforms.add(Platform.SELECT)
        # Diagnostic settle-pending binary sensor for models with fixedconf settle.
        platforms.add(Platform.BINARY_SENSOR)

    if DreoDeviceType.HEATER in device_types or DreoDeviceType.AIR_CONDITIONER in device_types:
        platforms.add(Platform.CLIMATE)
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)

    if DreoDeviceType.HUMIDIFIER in device_types:
        platforms.add(Platform.HUMIDIFIER)
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)
        platforms.add(Platform.SELECT)
        platforms.add(Platform.BINARY_SENSOR)
        platforms.add(Platform.LIGHT)

    if DreoDeviceType.DEHUMIDIFIER in device_types:
        platforms.add(Platform.HUMIDIFIER)
        platforms.add(Platform.FAN)
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)

    if DreoDeviceType.CHEF_MAKER in device_types:
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)

    if DreoDeviceType.EVAPORATIVE_COOLER in device_types:
        platforms.add(Platform.FAN)
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)
        platforms.add(Platform.BINARY_SENSOR)
        platforms.add(Platform.LIGHT)
        platforms.add(Platform.SELECT)

    pydreo_manager.start_transport()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][PYDREO_MANAGER] = pydreo_manager
    hass.data[DOMAIN][DREO_PLATFORMS] = platforms

    _LOGGER.debug("async_setup_entry: Platforms are: %s", platforms)

    await hass.config_entries.async_forward_entry_setups(config_entry, platforms)

    async def _update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
        """Handle options update."""
        await hass.config_entries.async_reload(config_entry.entry_id)

    ## Create update listener
    config_entry.async_on_unload(config_entry.add_update_listener(_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    pydreo_manager = hass.data[DOMAIN][PYDREO_MANAGER]
    if unload_ok := await hass.config_entries.async_unload_platforms(
        config_entry,
        hass.data[DOMAIN][DREO_PLATFORMS],
    ):
        hass.data.pop(DOMAIN)

    pydreo_manager.stop_transport()
    return unload_ok


async def async_remove_config_entry_device(hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry) -> bool:
    """Remove a config entry from a device.

    This allows users to delete Dreo devices from the UI.
    Since Dreo devices are cloud-based and managed by the Dreo service,
    we can safely remove them from Home Assistant's device registry.
    """
    _LOGGER.debug(
        "async_remove_config_entry_device: Removing device %s (identifiers: %s) from config entry %s",
        device_entry.name,
        device_entry.identifiers,
        config_entry.entry_id,
    )

    # For cloud-based devices, we don't need to do any cleanup on the device itself.
    # The device will still exist in the Dreo cloud and can be re-added by reloading
    # the integration or if the device is discovered again.
    return True
