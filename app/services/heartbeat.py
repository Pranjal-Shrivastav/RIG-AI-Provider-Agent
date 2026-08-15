"""
Heartbeat Service for RIG AI Provider Node.
Runs periodic background pulses to report node presence and health status to the backend.
"""

import time
import threading
import logging
from typing import Optional
from app.config.settings import Settings
from app.client.api import RIGAPIClient
from app.services.health import HealthEngine

logger = logging.getLogger("rig_agent.heartbeat")


class HeartbeatService:
    def __init__(self, settings: Settings, api_client: RIGAPIClient, health_engine: HealthEngine):
        self.settings = settings
        self.api_client = api_client
        self.health_engine = health_engine
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the background heartbeat service thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="HeartbeatThread")
        self._thread.start()
        logger.info(f"Heartbeat service started (Interval: {self.settings.heartbeat_interval}s)")

    def _run_loop(self) -> None:
        while self._running:
            try:
                # We can construct a minimal health status for heartbeat or use health engine
                # Here we ping heartbeat
                self.api_client.send_heartbeat(
                    # Generate lightweight status check
                    health=self.health_engine.evaluate(
                        cpu=self._empty_cpu(),
                        memory=self._empty_mem(),
                        gpus=[],
                        storage=self._empty_storage(),
                        network=self._empty_net(),
                    )
                )
            except Exception as e:
                logger.debug(f"Error sending background heartbeat: {e}")

            # Sleep in 0.5s increments to support rapid cancellation on stop
            sleep_needed = self.settings.heartbeat_interval
            step = 0.5
            elapsed = 0.0
            while self._running and elapsed < sleep_needed:
                time.sleep(step)
                elapsed += step

    def stop(self) -> None:
        """Stop background heartbeat service thread."""
        if not self._running:
            return
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Heartbeat service stopped.")

    # Helper fallbacks for lightweight pulse
    def _empty_cpu(self):
        from app.models.telemetry import CPUMetrics
        return CPUMetrics(usage_percent=0.0, per_core_percent=[], physical_cores=1, logical_cores=1)

    def _empty_mem(self):
        from app.models.telemetry import MemoryMetrics
        return MemoryMetrics(total_bytes=1, used_bytes=0, available_bytes=1, usage_percent=0.0)

    def _empty_storage(self):
        from app.models.telemetry import StorageMetrics
        return StorageMetrics()

    def _empty_net(self):
        from app.models.telemetry import NetworkMetrics
        return NetworkMetrics(bytes_sent=0, bytes_recv=0)
