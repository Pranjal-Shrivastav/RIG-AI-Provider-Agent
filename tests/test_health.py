"""
Unit tests for Health Evaluation Engine.
"""

from app.config.settings import Settings
from app.services.health import HealthEngine
from app.models.health import HealthStatus
from app.models.telemetry import (
    CPUMetrics,
    MemoryMetrics,
    GPUMetrics,
    GPUStatus,
    StorageMetrics,
    DiskPartitionMetrics,
    NetworkMetrics,
)


def test_health_evaluation_healthy():
    settings = Settings()
    engine = HealthEngine(settings)

    cpu = CPUMetrics(usage_percent=30.0, per_core_percent=[30.0], physical_cores=4, logical_cores=8)
    mem = MemoryMetrics(total_bytes=16 * (1024**3), used_bytes=4 * (1024**3), available_bytes=12 * (1024**3), usage_percent=25.0)
    gpu = [
        GPUMetrics(index=0, name="NVIDIA RTX 3060", status=GPUStatus.AVAILABLE, temperature_celsius=65.0)
    ]
    storage = StorageMetrics(
        partitions=[DiskPartitionMetrics(device="C:", mountpoint="C:\\", fstype="NTFS", total_bytes=500*(1024**3), used_bytes=200*(1024**3), free_bytes=300*(1024**3), usage_percent=40.0)]
    )
    net = NetworkMetrics(bytes_sent=100, bytes_recv=100, is_connected=True)

    health = engine.evaluate(cpu, mem, gpu, storage, net)

    assert health.status == HealthStatus.HEALTHY
    assert health.rig_available is True
    assert health.cpu_healthy is True
    assert health.ram_healthy is True


def test_health_evaluation_degraded_and_unavailable():
    settings = Settings()
    settings.max_gpu_temp_celsius = 80.0
    engine = HealthEngine(settings)

    cpu = CPUMetrics(usage_percent=98.0, per_core_percent=[98.0], physical_cores=4, logical_cores=8)
    mem = MemoryMetrics(total_bytes=16 * (1024**3), used_bytes=4 * (1024**3), available_bytes=12 * (1024**3), usage_percent=25.0)
    gpu = [
        GPUMetrics(index=0, name="NVIDIA RTX 3060", status=GPUStatus.AVAILABLE, temperature_celsius=89.0)  # > 85°C critical
    ]
    storage = StorageMetrics()
    net = NetworkMetrics(bytes_sent=100, bytes_recv=100, is_connected=True)

    health = engine.evaluate(cpu, mem, gpu, storage, net)

    assert health.status == HealthStatus.UNAVAILABLE
    assert health.gpu_healthy is False
