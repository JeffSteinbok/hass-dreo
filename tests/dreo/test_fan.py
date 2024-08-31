from contextlib import suppress

import pytest
from homeassistant.components.fan import FanEntityFeature

from custom_components.dreo import fan

from .utils import create_devices_from_data

fan_zandra = create_devices_from_data("fan-ZandraFan.json")


process_functions_expected = (
    FanEntityFeature.PRESET_MODE
    | FanEntityFeature.SET_SPEED
    | FanEntityFeature.DIRECTION
)
# Added in 2024.8.0
with suppress(AttributeError):
    process_functions_expected |= FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF


@pytest.fixture
def empty_fan(mocked_coordinator):
    yield fan.DreoFanHA(mocked_coordinator, "test fan")


@pytest.fixture
def speed_fan(mocked_coordinator):
    test_fan = fan.DreoFanHA(mocked_coordinator, "test fan")
    test_fan._supported_features = process_functions_expected
    test_fan._fan_speeds = [
        "fan-speed-6-016",
        "fan-speed-6-033",
        "fan-speed-6-050",
        "fan-speed-6-066",
        "fan-speed-6-083",
        "fan-speed-6-100",
    ]
    yield test_fan


class Test_DreoTowerFan:

    @pytest.mark.parametrize(
        "functions, expected_attrs",
        [
            (
                fan_zandra[0].functions,
                {
                    "_instance_attrs": {
                        "fan-speed": "fan-speed",
                        "fan-reverse": "fan-reverse",
                        "power": "fan-power",
                    },
                    "_supported_features": process_functions_expected,
                    "_preset_modes": {"comfort-breeze"},
                    "_fan_speeds": [
                        "fan-speed-6-016",
                        "fan-speed-6-033",
                        "fan-speed-6-050",
                        "fan-speed-6-066",
                        "fan-speed-6-083",
                        "fan-speed-6-100",
                    ],
                },
            )
        ],
    )
    def test_process_functions(self, functions, expected_attrs, empty_fan):
        empty_fan.process_functions(functions)
        for key, val in expected_attrs.items():
            assert getattr(empty_fan, key) == val

    @pytest.mark.parametrize(
        "states, expected_attrs, extra_attrs",
        [
            (
                fan_zandra[0].states,
                {
                    "_preset_mode": "comfort-breeze",
                    "_fan_speed": "fan-speed-6-050",
                    "_current_direction": "reverse",
                    "_state": "on",
                    "_availability": True,
                },
                {
                    "model": None,
                    "deviceId": None,
                    "Child ID": None,
                    "wifi-ssid": "71e7209f-b932-44b9-ba2f-a8179f68c3ac",
                    "wifi-mac-address": "e1119e0a-688d-45df-9882-a76549db9bc3",
                    "ble-mac-address": "07346a23-350b-4606-8d86-67217ec7a688",
                },
            ),
        ],
    )
    
    def test_update_states(self, states, expected_attrs, extra_attrs, empty_fan):
        empty_fan.states = states
        empty_fan.coordinator.data[ENTITY_FAN][empty_fan._child_id] = empty_fan
        empty_fan.update_states()
        assert empty_fan.extra_state_attributes == extra_attrs
        for key, val in expected_attrs.items():
            assert getattr(empty_fan, key) == val

    def test_name(self, empty_fan):
        assert empty_fan.name == "test fan"

    def test_unique_id(self, empty_fan):
        empty_fan._child_id = "beans"
        assert empty_fan.unique_id == "beans"

    @pytest.mark.parametrize(
        "state, expected",
        [
            ("on", True),
            ("off", False),
        ],
    )
    def test_is_on(self, state, expected, empty_fan):
        empty_fan._state = state
        assert empty_fan.is_on == expected

    def test_extra_state_attributes(self, mocked_coordinator):
        model = "bean model"
        device_id = "bean-123"
        child_id = "bean-123-123"
        test_fan = fan.DreoFanHA(
            mocked_coordinator,
            "test fan",
            model=model,
            device_id=device_id,
            child_id=child_id,
        )
        assert test_fan.extra_state_attributes == {
            "model": model,
            "deviceId": device_id,
            "Child ID": child_id,
        }

    def test_current_direction(self, empty_fan):
        empty_fan._current_direction = "reverse"
        assert empty_fan.current_direction == "reverse"

    def test_oscillating(self, empty_fan):
        assert not empty_fan.oscillating

    @pytest.mark.parametrize(
        "set_speed, expected",
        [
            # Speed not set
            (None, 0),
            # Speed is set but 000
            ("fan-speed-6-000", 0),
            # Speed is set to a value
            ("fan-speed-6-016", 16),
        ],
    )
    def test_percentage(self, set_speed, expected, speed_fan):
        speed_fan._fan_speed = set_speed
        assert speed_fan.percentage == expected

    @pytest.mark.parametrize(
        "preset, expected",
        [
            # Breeze
            ("comfort-breeze", "breeze"),
            ("not supported", None),
        ],
    )
    def test_preset_mode(self, preset, expected, empty_fan):
        empty_fan._preset_mode = preset
        assert empty_fan.preset_mode == expected

    def test_preset_modes(self, empty_fan):
        preset_modes = ["comfort-breeze"]
        empty_fan._preset_modes = preset_modes
        assert empty_fan.preset_modes == preset_modes

    def test_speed_count(self, speed_fan):
        assert speed_fan.speed_count == 6

    def test_supported_features(self, empty_fan):
        features = [1, 2, 3]
        empty_fan._supported_features = features
        assert empty_fan.supported_features == features

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "percentage, preset_mode, expected_attrs",
        [
            (
                12,
                None,
                {
                    "_fan_speed": "fan-speed-6-016",
                    "_preset_mode": None,
                },
            ),
            (
                17,
                "comfort-breeze",
                {
                    "_fan_speed": "fan-speed-6-033",
                    "_preset_mode": "breeze",
                },
            ),
        ],
    )
    async def test_async_turn_on(
        self, percentage, preset_mode, expected_attrs, speed_fan
    ):
        speed_fan._supported_features = process_functions_expected
        await speed_fan.async_turn_on(percentage=percentage, preset_mode=preset_mode)
        for key, val in expected_attrs.items():
            assert getattr(speed_fan, key) == val

    @pytest.mark.asyncio
    async def test_async_turn_off(self, empty_fan):
        # Added in 2024.8.0
        with suppress(AttributeError):
            empty_fan._supported_features |= fan.FanEntityFeature.TURN_OFF
        await empty_fan.async_turn_off()
        assert empty_fan._state == "off"