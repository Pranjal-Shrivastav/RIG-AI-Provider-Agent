"""
Health evaluation service for RIG Provider Node.
Evaluates hardware telemetry against configurable thresholds to assign node health states:
HEALTHY, DEGRADED, UNAVAILABLE, or OFFLINE.
"""

from datetime import datetime, timezone
from typing import List
from app.config.settings import Settings
from app.models.health import HealthStatus, NodeHealthInfo
from app.models.telemetry import (
    CPUMetrics,
    MemoryMetrics,
    GPUMetrics,
    GPUStatus,
    StorageMetrics,
    NetworkMetrics,
)


class HealthEngine:
    def __init__(self, settings: Settings):
        self.settings = settings

    def evaluate(
        self,
        cpu: CPUMetrics,
        memory: MemoryMetrics,
        gpus: List[GPUMetrics],
        storage: StorageMetrics,
        network: NetworkMetrics,
    ) -> NodeHealthInfo:
        """Evaluate overall node health status and return detailed NodeHealthInfo report."""

        reasons: List[str] = []
        cpu_healthy = True
        ram_healthy = True
        gpu_healthy = True
        disk_healthy = True
        network_healthy = True
        
        status = HealthStatus.HEALTHY

        # 1. Provider Workload Allowance
        if not self.settings.allow_rig_workloads:
            status = HealthStatus.UNAVAILABLE
            reasons.append("Provider disabled RIG workloads.")

        # 2. CPU Evaluation
        if cpu.usage_percent >= 95.0:
            cpu_healthy = False
            reasons.append(f"CPU utilization extremely high ({cpu.usage_percent}%).")
            if status == HealthStatus.HEALTHY:
                status = HealthStatus.DEGRADED

        # 3. RAM Evaluation
        if memory.usage_percent >= 95.0:
            ram_healthy = False
            reasons.append(f"RAM utilization critical ({memory.usage_percent}%).")
            if status == HealthStatus.HEALTHY:
                status = HealthStatus.DEGRADED
        elif memory.available_bytes < (512 * 1024 * 1024):  # < 512 MB available
            ram_healthy = False
            reasons.append("Available RAM dangerously low (< 512 MB).")
            status = HealthStatus.UNAVAILABLE

        # 4. GPU Temperature & Utilization Evaluation
        max_temp_threshold = self.settings.max_gpu_temp_celsius
        for gpu in gpus:
            if gpu.status == GPUStatus.AVAILABLE:
                if gpu.temperature_celsius is not None:
                    temp = gpu.temperature_celsius
                    if temp > (max_temp_threshold + 5.0):
                        gpu_healthy = False
                        reasons.append(f"GPU {gpu.index} ({gpu.name}) temp critical ({temp}°C > {max_temp_threshold + 5}°C).")
                        status = HealthStatus.UNAVAILABLE
                    elif temp >= max_temp_threshold:
                        gpu_healthy = False
                        reasons.append(f"GPU {gpu.index} ({gpu.name}) temp elevated ({temp}°C >= {max_temp_threshold}°C).")
                        if status == HealthStatus.HEALTHY:
                            status = HealthStatus.DEGRADED

        # 5. Disk Capacity Evaluation
        for partition in storage.partitions:
            if partition.usage_percent >= 95.0:
                disk_healthy = False
                reasons.append(f"Disk partition '{partition.mountpoint}' nearly full ({partition.usage_percent}%).")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED

        # 6. Network Connectivity Evaluation
        if not network.is_connected:
            network_healthy = False
            reasons.append("No active network interfaces detected.")
            if status != HealthStatus.UNAVAILABLE:
                status = HealthStatus.DEGRADED

        if not reasons and status == HealthStatus.HEALTHY:
            reasons.append("All node subsystems operating within healthy parameters.")

        rig_available = (status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)) and self.settings.allow_rig_workloads

        return NodeHealthInfo(
            status=status,
            rig_available=rig_available,
            reasons=reasons,
            cpu_healthy=cpu_healthy,
            ram_healthy=ram_healthy,
            gpu_healthy=gpu_healthy,
            disk_healthy=disk_healthy,
            network_healthy=network_healthy,
            last_evaluated=datetime.now(timezone.utc).isoformat(),
        )
