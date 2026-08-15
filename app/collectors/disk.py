"""
Storage and Disk I/O metrics collector.
Monitors multi-partition drive capacity, usage percentage, and real-time Disk I/O transfer rates.
"""

import time
import psutil
from typing import List, Optional, Tuple
from app.models.telemetry import DiskPartitionMetrics, StorageMetrics


class DiskCollector:
    def __init__(self):
        self._last_time: Optional[float] = None
        self._last_read_bytes: Optional[int] = None
        self._last_write_bytes: Optional[int] = None

    def collect(self) -> StorageMetrics:
        """Collect storage capacity across partitions and calculate current I/O rates."""
        partitions_list: List[DiskPartitionMetrics] = []
        
        # 1. Collect partition capacity
        try:
            raw_partitions = psutil.disk_partitions(all=False)
            for part in raw_partitions:
                # Skip cdrom or empty mount points on Windows
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
                
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions_list.append(
                        DiskPartitionMetrics(
                            device=part.device,
                            mountpoint=part.mountpoint,
                            fstype=part.fstype,
                            total_bytes=int(usage.total),
                            used_bytes=int(usage.used),
                            free_bytes=int(usage.free),
                            usage_percent=float(usage.percent),
                        )
                    )
                except (PermissionError, OSError):
                    # Inaccessible partition (e.g. unmounted network drive or permission restricted)
                    continue
        except Exception:
            pass

        # 2. Calculate Disk I/O throughput
        read_rate = 0.0
        write_rate = 0.0
        now = time.time()
        
        try:
            io_counters = psutil.disk_io_counters()
            if io_counters:
                curr_read = int(io_counters.read_bytes)
                curr_write = int(io_counters.write_bytes)

                if (
                    self._last_time is not None
                    and self._last_read_bytes is not None
                    and self._last_write_bytes is not None
                ):
                    time_delta = now - self._last_time
                    if time_delta > 0:
                        read_diff = max(0, curr_read - self._last_read_bytes)
                        write_diff = max(0, curr_write - self._last_write_bytes)
                        read_rate = round(read_diff / time_delta, 2)
                        write_rate = round(write_diff / time_delta, 2)

                self._last_time = now
                self._last_read_bytes = curr_read
                self._last_write_bytes = curr_write
        except Exception:
            pass

        return StorageMetrics(
            partitions=partitions_list,
            read_bytes_sec=read_rate,
            write_bytes_sec=write_rate,
        )
