"""
CPU metrics collector.
Collects overall and per-core CPU utilization, core counts, operating frequencies, and load averages.
"""

import os
import psutil
from typing import List, Optional
from app.models.telemetry import CPUMetrics


class CPUCollector:
    def __init__(self):
        # Warmup psutil CPU percent calculation (first call can return 0.0)
        try:
            psutil.cpu_percent(interval=None)
            psutil.cpu_percent(interval=None, percpu=True)
        except Exception:
            pass

    def collect(self) -> CPUMetrics:
        """Collect current CPU metrics."""
        # Overall usage %
        try:
            usage_percent = float(psutil.cpu_percent(interval=None))
        except Exception:
            usage_percent = 0.0

        # Per-core usage %
        try:
            per_core_raw = psutil.cpu_percent(interval=None, percpu=True)
            per_core_percent = [float(val) for val in per_core_raw]
        except Exception:
            per_core_percent = []

        # Physical and logical core counts
        physical_cores = psutil.cpu_count(logical=False) or 1
        logical_cores = psutil.cpu_count(logical=True) or physical_cores

        # Frequency
        current_freq: Optional[float] = None
        max_freq: Optional[float] = None
        try:
            freq_info = psutil.cpu_freq()
            if freq_info:
                current_freq = round(float(freq_info.current), 2)
                max_freq = round(float(freq_info.max), 2) if freq_info.max > 0 else None
        except Exception:
            pass

        # Load average (available on Linux/macOS, or via psutil on newer OS)
        load_avg: Optional[List[float]] = None
        try:
            if hasattr(os, "getloadavg"):
                load_tuple = os.getloadavg()
                load_avg = [round(x, 2) for x in load_tuple]
            elif hasattr(psutil, "getloadavg"):
                load_tuple = psutil.getloadavg()
                load_avg = [round(x, 2) for x in load_tuple]
        except Exception:
            pass

        return CPUMetrics(
            usage_percent=usage_percent,
            per_core_percent=per_core_percent,
            physical_cores=physical_cores,
            logical_cores=logical_cores,
            current_frequency_mhz=current_freq,
            max_frequency_mhz=max_freq,
            load_average=load_avg,
        )
