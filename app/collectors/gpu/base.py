"""
Abstract base class for GPU telemetry providers.
Supports multi-vendor modularity (NVIDIA, AMD, Intel).
"""

from abc import ABC, abstractmethod
from typing import List
from app.models.telemetry import GPUMetrics


class GPUProvider(ABC):
    """Abstract base provider interface for GPU telemetry collection."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this GPU provider interface is initialized and hardware is present."""
        pass

    @abstractmethod
    def get_gpus(self) -> List[GPUMetrics]:
        """Collect and return telemetry for all GPUs managed by this provider."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up resources or driver handles on shutdown."""
        pass
