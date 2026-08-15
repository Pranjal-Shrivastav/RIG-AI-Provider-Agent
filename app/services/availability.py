"""
RIG Resource Availability Calculation Engine.
Calculates dynamic resources available for RIG AI workloads based on total system capacity,
current provider background consumption, and provider resource reservation settings.
"""

from typing import List
from app.config.settings import Settings
from app.models.telemetry import (
    CPUMetrics,
    MemoryMetrics,
    GPUMetrics,
    GPUStatus,
    RIGResourceAvailability,
)


class AvailabilityEngine:
    def __init__(self, settings: Settings):
        self.settings = settings

    def calculate(
        self,
        cpu: CPUMetrics,
        memory: MemoryMetrics,
        gpus: List[GPUMetrics],
    ) -> RIGResourceAvailability:
        """
        Dynamically calculate RIG-available resources.
        
        Formula Principles:
        1. Respect provider allowance toggle (`allow_rig_workloads`).
        2. Cap allocation by provider reservation percentages (`max_*_percent_rig`).
        3. Do not allocate more than remaining free/unreserved system resources.
        """

        # 1. Allowance toggle
        if not self.settings.allow_rig_workloads:
            return RIGResourceAvailability(
                available_cpus=0.0,
                available_ram_bytes=0,
                available_gpus=0,
                available_vram_bytes=0,
                rig_workload_allowed=False,
                explanation="Provider currently disabled RIG workloads in settings.",
            )

        # 2. CPU Availability Calculation
        # Max CPUs provider allows RIG to use
        max_cpus_allowed = cpu.logical_cores * (self.settings.max_cpu_percent_rig / 100.0)
        # Unused CPU cores currently free on system
        current_free_percent = max(0.0, 100.0 - cpu.usage_percent)
        free_cpus = cpu.logical_cores * (current_free_percent / 100.0)
        
        # RIG available CPUs = min of (provider cap, unreserved free CPUs)
        available_cpus = round(max(0.0, min(max_cpus_allowed, free_cpus)), 2)

        # 3. RAM Availability Calculation (bytes)
        max_ram_allowed_bytes = int(memory.total_bytes * (self.settings.max_ram_percent_rig / 100.0))
        available_ram_bytes = max(0, min(max_ram_allowed_bytes, memory.available_bytes))

        # 4. GPU & VRAM Availability Calculation
        available_gpus = 0
        available_vram_bytes = 0

        for gpu in gpus:
            if gpu.status == GPUStatus.AVAILABLE and gpu.vram is not None:
                # Check temperature threshold
                if (
                    gpu.temperature_celsius is not None
                    and gpu.temperature_celsius > (self.settings.max_gpu_temp_celsius + 5.0)
                ):
                    continue  # Overheated GPU excluded from RIG available compute

                # Utilization cap check
                gpu_util = gpu.utilization_percent or 0.0
                if gpu_util <= self.settings.max_gpu_percent_rig:
                    available_gpus += 1

                # VRAM calculation
                max_vram_allowed = int(gpu.vram.total_bytes * (self.settings.max_vram_percent_rig / 100.0))
                free_vram_allowed = max(0, min(max_vram_allowed, gpu.vram.free_bytes))
                available_vram_bytes += free_vram_allowed

        explanation_parts = [
            f"CPUs Available: {available_cpus}/{cpu.logical_cores}",
            f"RAM Available: {round(available_ram_bytes / (1024**3), 2)} GB",
            f"GPUs Available: {available_gpus}/{len(gpus)}",
            f"VRAM Available: {round(available_vram_bytes / (1024**3), 2)} GB",
        ]

        return RIGResourceAvailability(
            available_cpus=available_cpus,
            available_ram_bytes=available_ram_bytes,
            available_gpus=available_gpus,
            available_vram_bytes=available_vram_bytes,
            rig_workload_allowed=True,
            explanation="; ".join(explanation_parts),
        )
