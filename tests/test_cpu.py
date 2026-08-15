"""
Unit tests for CPU Collector.
"""

from app.collectors.cpu import CPUCollector
from app.models.telemetry import CPUMetrics


def test_cpu_collector():
    collector = CPUCollector()
    metrics = collector.collect()

    assert isinstance(metrics, CPUMetrics)
    assert 0.0 <= metrics.usage_percent <= 100.0
    assert metrics.physical_cores >= 1
    assert metrics.logical_cores >= metrics.physical_cores
    assert isinstance(metrics.per_core_percent, list)
    assert len(metrics.per_core_percent) == metrics.logical_cores
