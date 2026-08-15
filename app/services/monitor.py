"""
Real-time Monitoring Engine Orchestrator.
Coordinates hardware sampling loops with optimized sampling rates (fast for CPU/RAM/GPU, slower for Disk/System),
calculates RIG resource availability and node health, and outputs strongly-typed NodeTelemetry.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Optional
from app.config.settings import Settings
from app.collectors import (
    SystemCollector,
    CPUCollector,
    MemoryCollector,
    GPUCollectorManager,
    DiskCollector,
    NetworkCollector,
)
from app.services.availability import AvailabilityEngine
from app.services.health import HealthEngine
from app.models.telemetry import NodeTelemetry, StorageMetrics

logger = logging.getLogger("rig_agent.monitor")


class MonitoringEngine:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings.load()
        
        # Initialize collectors
        self.system_collector = SystemCollector(agent_version=self.settings.agent_version)
        self.cpu_collector = CPUCollector()
        self.memory_collector = MemoryCollector()
        self.gpu_manager = GPUCollectorManager()
        self.disk_collector = DiskCollector()
        self.network_collector = NetworkCollector()

        # Initialize evaluation engines
        self.availability_engine = AvailabilityEngine(self.settings)
        self.health_engine = HealthEngine(self.settings)

        # Storage caching (Storage capacity sampled less frequently, e.g. every 5 seconds)
        self._cached_storage: Optional[StorageMetrics] = None
        self._last_disk_sample_time: float = 0.0
        self._disk_sample_interval: float = 5.0

    def collect_telemetry(self) -> NodeTelemetry:
        """Collect current system telemetry snapshot across all hardware subsystems."""
        now = time.time()

        # 1. Fast path collectors (~1s interval)
        system_info = self.system_collector.collect()
        cpu_metrics = self.cpu_collector.collect()
        memory_metrics = self.memory_collector.collect()
        gpu_metrics = self.gpu_manager.collect()
        network_metrics = self.network_collector.collect()

        # 2. Medium path collector (Disk - sampled every ~5s)
        if self._cached_storage is None or (now - self._last_disk_sample_time) >= self._disk_sample_interval:
            self._cached_storage = self.disk_collector.collect()
            self._last_disk_sample_time = now
        storage_metrics = self._cached_storage

        # 3. Calculate Availability & Health
        availability = self.availability_engine.calculate(
            cpu=cpu_metrics,
            memory=memory_metrics,
            gpus=gpu_metrics,
        )

        health_info = self.health_engine.evaluate(
            cpu=cpu_metrics,
            memory=memory_metrics,
            gpus=gpu_metrics,
            storage=storage_metrics,
            network=network_metrics,
        )

        iso_timestamp = datetime.now(timezone.utc).isoformat()

        return NodeTelemetry(
            node_id=self.settings.node_id,
            timestamp=iso_timestamp,
            agent_version=self.settings.agent_version,
            system=system_info,
            cpu=cpu_metrics,
            memory=memory_metrics,
            gpu=gpu_metrics,
            storage=storage_metrics,
            network=network_metrics,
            availability=availability,
            health=health_info,
        )

    def shutdown(self) -> None:
        """Clean shutdown of underlying collectors (e.g. NVML)."""
        logger.info("Shutting down Monitoring Engine...")
        try:
            self.gpu_manager.shutdown()
        except Exception as e:
            logger.warning(f"Error during GPU manager shutdown: {e}")
