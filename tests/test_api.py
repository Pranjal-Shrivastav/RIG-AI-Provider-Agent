"""
Unit tests for Backend API Client and Offline Buffering Queue.
"""

from unittest.mock import MagicMock, patch
from app.config.settings import Settings
from app.client.api import RIGAPIClient
from app.services.monitor import MonitoringEngine


def test_api_client_send_telemetry_success():
    settings = Settings()
    client = RIGAPIClient(settings)

    monitor = MonitoringEngine(settings)
    telemetry = monitor.collect_telemetry()
    monitor.shutdown()

    with patch.object(client.session, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        success = client.send_telemetry(telemetry)
        assert success is True
        assert client.is_connected is True
        assert len(client._offline_queue) == 0


def test_api_client_offline_buffering():
    settings = Settings()
    client = RIGAPIClient(settings)

    monitor = MonitoringEngine(settings)
    telemetry = monitor.collect_telemetry()
    monitor.shutdown()

    with patch.object(client.session, "post", side_effect=Exception("Connection refused")):
        success = client.send_telemetry(telemetry)
        assert success is False
        assert client.is_connected is False
        assert len(client._offline_queue) == 1
