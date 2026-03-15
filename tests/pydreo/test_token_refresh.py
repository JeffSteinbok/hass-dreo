"""Tests for PyDreo token refresh and 401 retry logic."""
import logging
from unittest.mock import patch, MagicMock
from .imports import * # pylint: disable=W0401,W0614

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

PATCH_BASE = 'custom_components.dreo.pydreo'
PATCH_CALL_API = f'{PATCH_BASE}.helpers.Helpers.call_api'
PATCH_LOGIN = f'{PATCH_BASE}.PyDreo.login'


class TestTokenRefresh:
    """Test token refresh and 401 retry logic."""

    def _make_manager(self):
        """Create a PyDreo manager for testing."""
        manager = PyDreo('test@example.com', 'password', redact=True)
        manager.enabled = True
        manager.token = "old_token"
        manager.account_id = "test_account"
        return manager

    def test_call_dreo_api_retries_on_401(self):
        """Test that call_dreo_api retries once after a 401 response."""
        manager = self._make_manager()

        with patch(PATCH_CALL_API) as mock_call_api:
            mock_call_api.side_effect = [
                (None, 401),
                ({"code": 0, "data": {}}, 200),
            ]
            with patch(PATCH_LOGIN, return_value=True):
                response, status_code = manager.call_dreo_api(DREO_API_DEVICELIST)

        assert status_code == 200
        assert response is not None
        assert mock_call_api.call_count == 2

    def test_call_dreo_api_no_retry_on_login_api(self):
        """Test that call_dreo_api does NOT retry the login API itself on 401."""
        manager = self._make_manager()

        with patch(PATCH_CALL_API) as mock_call_api:
            mock_call_api.return_value = (None, 401)
            response, status_code = manager.call_dreo_api(DREO_API_LOGIN)

        assert mock_call_api.call_count == 1
        assert status_code == 401

    def test_call_dreo_api_no_retry_on_relogin_failure(self):
        """Test that call_dreo_api doesn't retry if re-login fails."""
        manager = self._make_manager()

        with patch(PATCH_CALL_API) as mock_call_api:
            mock_call_api.return_value = (None, 401)
            with patch(PATCH_LOGIN, return_value=False):
                response, status_code = manager.call_dreo_api(DREO_API_DEVICELIST)

        assert mock_call_api.call_count == 1
        assert status_code == 401

    def test_call_dreo_api_no_retry_on_200(self):
        """Test that call_dreo_api doesn't retry on success."""
        manager = self._make_manager()

        with patch(PATCH_CALL_API) as mock_call_api:
            mock_call_api.return_value = ({"code": 0}, 200)
            response, status_code = manager.call_dreo_api(DREO_API_DEVICELIST)

        assert mock_call_api.call_count == 1
        assert status_code == 200

    def test_re_login_updates_transport_token(self):
        """Test that _re_login updates the transport token on success."""
        manager = self._make_manager()
        manager.debug_test_mode = False

        with patch(PATCH_LOGIN) as mock_login:
            def login_side_effect():
                manager.token = "new_token"
                return True
            mock_login.side_effect = login_side_effect

            with patch.object(manager._transport, 'update_token') as mock_update:
                result = manager._re_login()

        assert result is True
        mock_update.assert_called_once_with("new_token")

    def test_re_login_failure_returns_false(self):
        """Test that _re_login returns False when login fails."""
        manager = self._make_manager()

        with patch(PATCH_LOGIN, return_value=False):
            result = manager._re_login()

        assert result is False

    def test_re_login_skips_transport_update_in_debug_mode(self):
        """Test that _re_login skips transport update in debug test mode."""
        manager = self._make_manager()
        manager.debug_test_mode = True

        with patch(PATCH_LOGIN) as mock_login:
            def login_side_effect():
                manager.token = "new_token"
                return True
            mock_login.side_effect = login_side_effect

            with patch.object(manager._transport, 'update_token') as mock_update:
                result = manager._re_login()

        assert result is True
        mock_update.assert_not_called()
