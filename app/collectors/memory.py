"""
Memory (RAM) metrics collector.
Collects total, used, available memory bytes, percentage, and cached memory.
"""

import psutil
from typing import Optional
from app.models.telemetry import MemoryMetrics


class MemoryCollector:
    def collect(self) -> MemoryMetrics:
        """Collect current RAM metrics."""
        vmem = psutil.virtual_memory()
        
        cached_bytes: Optional[int] = None
        if hasattr(vmem, "cached") and vmem.cached is not None:
            cached_bytes = int(vmem.cached)
        elif hasattr(vmem, "buffers") and vmem.buffers is not None:
            cached_bytes = int(vmem.buffers)

        return MemoryMetrics(
            total_bytes=int(vmem.total),
            used_bytes=int(vmem.used),
            available_bytes=int(vmem.available),
            usage_percent=float(vmem.percent),
            cached_bytes=cached_bytes,
        )
