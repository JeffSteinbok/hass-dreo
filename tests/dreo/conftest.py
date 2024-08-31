import logging
from collections import defaultdict
import pytest

from custom_components.dreo.pydreo import PyDreo


@pytest.fixture
def mocked_pydreo(mocker, mocked_dreo):
    #mocker.patch("homeassistant.helpers.entity.Entity.async_write_ha_state")
    pydreo_mock = mocker.patch.object(
        PyDreo, "HubSpaceDataUpdateCoordinator", autospec=True
    )
    pydreo_mock.conn = mocked_dreo
    pydreo_mock.data = defaultdict(dict)
    yield pydreo_mock


@pytest.fixture
def mocked_pydreo(mocker):
    """Mock all HubSpace functionality but ensure the class is correct"""
    hs_mock = mocker.patch.object(pydreo_async, "HubSpaceConnection", autospec=True)
    yield hs_mock


@pytest.fixture(autouse=True)
def set_debug_mode(caplog):
    # Force capture of all debug logging. This is useful if you want to verify
    # log messages with `<message> in caplog.text`. If you run
    # pytest -rP it will display all log messages, including passing tests.
    caplog.set_level(logging.DEBUG)