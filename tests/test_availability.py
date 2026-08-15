"""
Unit tests for RIG Resource Availability Engine.
"""

from app.config.settings import Settings
from app.services.availability import AvailabilityEngine
from app.models.telemetry import (
    CPUMetrics,
    MemoryMetrics,
    GPUMetrics,
    GPUStatus,
    VRAMMetrics,
)


def test_availability_calculation():
    settings = Settings()
    settings.max_cpu_percent_rig = 80.0
    settings.max_ram_percent_rig = 80.0
    settings.max_gpu_percent_rig = 90.0
    settings.max_vram_percent_rig = 90.0
    settings.allow_rig_workloads = True

    engine = AvailabilityEngine(settings)

    cpu = CPUMetrics(usage_percent=20.0, per_core_percent=[], physical_cores=8, logical_cores=16)
    mem = MemoryMetrics(total_bytes=10000, used_bytes=2000, available_bytes=8000, usage_percent=20.0)
    
    vram = VRAMMetrics(total_bytes=10000, used_bytes=2000, free_bytes=8000, usage_percent=20.0)
    gpus = [
        GPUMetrics(
            index=0,
            name="NVIDIA RTX 3080",
            status=GPUStatus.AVAILABLE,
            utilization_percent=20.0,
            temperature_celsius=65.0,
            vram=vram,
        )
    ]

    avail = engine.calculate(cpu, mem, gpus)

    assert avail.rig_workload_allowed is True
    assert avail.available_cpus > 0
    assert avail.available_ram_bytes > 0
    assert avail.available_gpus == 1
    assert avail.available_vram_bytes > 0


def test_availability_disabled():
    settings = Settings()
    settings.allow_rig_workloads = False
    engine = AvailabilityEngine(settings)

    cpu = CPUMetrics(usage_percent=20.0, per_core_percent=[], physical_cores=8, logical_cores=16)
    mem = MemoryMetrics(total_bytes=10000, used_bytes=2000, available_bytes=8000, usage_percent=20.0)
    gpus = []

    avail = engine.calculate(cpu, mem, gpus)

    assert avail.rig_workload_allowed is False
    assert avail.available_cpus == 0.0
    assert avail.available_ram_bytes == 0
    assert avail.available_gpus == 0
