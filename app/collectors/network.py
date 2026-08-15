"""
Network telemetry collector.
Monitors cumulative bytes, calculates upload/download speeds via consecutive sample deltas,
and lists active network interfaces.
"""

import time
import socket
import psutil
from typing import List, Optional
from app.models.telemetry import NetworkInterfaceInfo, NetworkMetrics
from app.utils.conversion import bps_to_mbps


class NetworkCollector:
    def __init__(self):
        self._last_time: Optional[float] = None
        self._last_bytes_sent: Optional[int] = None
        self._last_bytes_recv: Optional[int] = None

    def _collect_interfaces(self) -> List[NetworkInterfaceInfo]:
        """List active network interface names and assigned IP addresses."""
        interface_list: List[NetworkInterfaceInfo] = []
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            for name, addr_list in addrs.items():
                ips: List[str] = []
                for addr in addr_list:
                    # Collect IPv4 and IPv6 string representations
                    if addr.family in (socket.AF_INET, getattr(socket, "AF_INET6", -1)):
                        if addr.address:
                            ips.append(addr.address)

                is_up = stats[name].isup if name in stats else True
                interface_list.append(
                    NetworkInterfaceInfo(
                        name=name,
                        addresses=ips,
                        is_up=is_up,
                    )
                )
        except Exception:
            pass
        return interface_list

    def collect(self) -> NetworkMetrics:
        """Collect cumulative traffic, speeds, and interface metadata."""
        now = time.time()
        curr_sent = 0
        curr_recv = 0
        
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                curr_sent = int(net_io.bytes_sent)
                curr_recv = int(net_io.bytes_recv)
        except Exception:
            pass

        upload_bps = 0.0
        download_bps = 0.0

        if (
            self._last_time is not None
            and self._last_bytes_sent is not None
            and self._last_bytes_recv is not None
        ):
            time_delta = now - self._last_time
            if time_delta > 0:
                sent_diff = max(0, curr_sent - self._last_bytes_sent)
                recv_diff = max(0, curr_recv - self._last_bytes_recv)
                upload_bps = round(sent_diff / time_delta, 2)
                download_bps = round(recv_diff / time_delta, 2)

        self._last_time = now
        self._last_bytes_sent = curr_sent
        self._last_bytes_recv = curr_recv

        interfaces = self._collect_interfaces()
        is_connected = any(iface.is_up for iface in interfaces) if interfaces else True

        return NetworkMetrics(
            bytes_sent=curr_sent,
            bytes_recv=curr_recv,
            upload_speed_bps=upload_bps,
            download_speed_bps=download_bps,
            upload_speed_mbps=bps_to_mbps(upload_bps),
            download_speed_mbps=bps_to_mbps(download_bps),
            interfaces=interfaces,
            is_connected=is_connected,
        )
