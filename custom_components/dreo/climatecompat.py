"""Compatibility for the native_* climate temperature API across Home Assistant versions.

Home Assistant 2026.11 renamed the climate temperature members to native_* names (temperature_unit ->
native_temperature_unit, current_temperature -> native_current_temperature, and so on) and warns about
integrations that still provide the old names. Older versions, which this integration still supports
(see hacs.json), only read the old names. Climate entities here provide the native_* names, and
NativeClimateTemperatureCompat serves the old names from them when Home Assistant lacks the new API.
On 2026.11 and later the mixin is empty, so no deprecated member is provided.
"""

from homeassistant.components.climate import ClimateEntity

HAS_NATIVE_CLIMATE_TEMPERATURES = hasattr(ClimateEntity, "native_temperature_unit")


class NativeClimateTemperatureCompat:
    """Serve the pre-2026.11 climate temperature members from the native_* ones.

    List it before ClimateEntity in the bases so its members override ClimateEntity's.
    """

    if not HAS_NATIVE_CLIMATE_TEMPERATURES:
        _attr_native_current_temperature: float | None = None
        _attr_native_target_temperature: float | None = None
        _attr_native_target_temperature_high: float | None = None
        _attr_native_target_temperature_low: float | None = None

        @property
        def native_temperature_unit(self) -> str:
            """Return the unit the entity reports temperatures in."""
            return self._attr_native_temperature_unit

        @property
        def native_current_temperature(self) -> float | None:
            """Return the current temperature in the native unit."""
            return self._attr_native_current_temperature

        @property
        def native_target_temperature(self) -> float | None:
            """Return the target temperature in the native unit."""
            return self._attr_native_target_temperature

        @property
        def native_target_temperature_high(self) -> float | None:
            """Return the upper bound of the target temperature in the native unit."""
            return self._attr_native_target_temperature_high

        @property
        def native_target_temperature_low(self) -> float | None:
            """Return the lower bound of the target temperature in the native unit."""
            return self._attr_native_target_temperature_low

        @property
        def temperature_unit(self) -> str:
            """Return the unit the entity reports temperatures in."""
            return self.native_temperature_unit

        @property
        def current_temperature(self) -> float | None:
            """Return the current temperature."""
            return self.native_current_temperature

        @property
        def target_temperature(self) -> float | None:
            """Return the target temperature."""
            return self.native_target_temperature

        @property
        def target_temperature_high(self) -> float | None:
            """Return the upper bound of the target temperature."""
            return self.native_target_temperature_high

        @property
        def target_temperature_low(self) -> float | None:
            """Return the lower bound of the target temperature."""
            return self.native_target_temperature_low
