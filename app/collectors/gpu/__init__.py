"""
GPU telemetry provider factory and manager.
Provides unified GPU metrics collection across NVIDIA (NVML) and stubs for AMD / Intel.
"""

import logging
from typing import List
from app.collectors.gpu.base import GPUProvider
from app.collectors.gpu.nvidia import NvidiaGPUProvider
from app.models.telemetry import GPUMetrics, GPUStatus

logger = logging.getLogger("rig_agent.gpu")


class AMDGPUProvider(GPUProvider):
    """Placeholder stub for future AMD ROCm/smi GPU monitoring implementation."""
    def is_available(self) -> bool:
        return False

    def get_gpus(self) -> List[GPUMetrics]:
        return []

    def shutdown(self) -> None:
        pass


class IntelGPUProvider(GPUProvider):
    """Placeholder stub for future Intel OneAPI/xpu GPU monitoring implementation."""
    def is_available(self) -> bool:
        return False

    def get_gpus(self) -> List[GPUMetrics]:
        return []

    def shutdown(self) -> None:
        pass


class GPUCollectorManager:
    """Manages all registered GPU telemetry providers."""

    def __init__(self):
        self.providers: List[GPUProvider] = [
            NvidiaGPUProvider(),
            AMDGPUProvider(),
            IntelGPUProvider(),
        ]

    def collect(self) -> List[GPUMetrics]:
        all_gpus: List[GPUMetrics] = []
        
        for provider in self.providers:
            if provider.is_available():
                gpus = provider.get_gpus()
                all_gpus.extend(gpus)

        # If no active GPU providers returned available GPUs, return standard unavailable indicator
        if not all_gpus:
            # Check if Nvidia provider returned an unavailable status entry
            for provider in self.providers:
                if isinstance(provider, NvidiaGPUProvider):
                    return provider.get_gpus()

            return [
                GPUMetrics(
                    index=0,
                    name="GPU",
                    status=GPUStatus.NOT_PRESENT,
                    reason="No supported GPU providers available",
                )
            ]

        return all_gpus

    def shutdown(self) -> None:
        for provider in self.providers:
            try:
                provider.shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down GPU provider {provider}: {e}")
