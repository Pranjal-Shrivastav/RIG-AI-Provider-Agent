"""
Unit tests for Memory Collector.
"""

from app.collectors.memory import MemoryCollector
from app.models.telemetry import MemoryMetrics


def test_memory_collector():
    collector = MemoryCollector()
    metrics = collector.collect()

    assert isinstance(metrics, MemoryMetrics)
    assert metrics.total_bytes > 0
    assert metrics.used_bytes >= 0
    assert metrics.available_bytes >= 0
    assert 0.0 <= metrics.usage_percent <= 100.0
    assert metrics.used_bytes + metrics.available_bytes <= metrics.total_bytes * 1.05  # Allow minor delta
