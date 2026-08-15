"""
Unit tests for Network Collector.
"""

from app.collectors.network import NetworkCollector
from app.models.telemetry import NetworkMetrics


def test_network_collector():
    collector = NetworkCollector()
    metrics = collector.collect()

    assert isinstance(metrics, NetworkMetrics)
    assert metrics.bytes_sent >= 0
    assert metrics.bytes_recv >= 0
    assert metrics.upload_speed_bps >= 0.0
    assert metrics.download_speed_bps >= 0.0
    assert isinstance(metrics.interfaces, list)
