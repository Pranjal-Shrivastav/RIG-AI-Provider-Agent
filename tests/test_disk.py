"""
Unit tests for Disk / Storage Collector.
"""

from app.collectors.disk import DiskCollector
from app.models.telemetry import StorageMetrics


def test_disk_collector():
    collector = DiskCollector()
    metrics = collector.collect()

    assert isinstance(metrics, StorageMetrics)
    assert len(metrics.partitions) >= 1
    
    first_part = metrics.partitions[0]
    assert first_part.total_bytes > 0
    assert 0.0 <= first_part.usage_percent <= 100.0
    assert metrics.read_bytes_sec >= 0.0
    assert metrics.write_bytes_sec >= 0.0
