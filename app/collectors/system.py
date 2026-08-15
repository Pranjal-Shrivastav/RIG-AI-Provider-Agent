"""
System information collector.
Collects operating system, hardware architecture, CPU model, hostname, and system uptime.
Caches static fields for high performance.
"""

import platform
import time
import os
import psutil
from typing import Optional
from app.models.telemetry import SystemInfo


class SystemCollector:
    def __init__(self, agent_version: str = "0.1.0"):
        self.agent_version = agent_version
        self._cached_os = platform.system()
        self._cached_os_version = platform.version()
        self._cached_arch = platform.machine() or platform.architecture()[0]
        self._cached_hostname = platform.node()
        self._cached_cpu_model = self._detect_cpu_model()

    def _detect_cpu_model(self) -> str:
        """Detect CPU model string across Windows/Linux/macOS."""
        try:
            processor = platform.processor()
            if processor and processor.strip():
                return processor.strip()
        except Exception:
            pass

        # Windows WMI fallback or environment variable
        if os.name == 'nt':
            try:
                import subprocess
                cmd = "wmic cpu get name"
                output = subprocess.check_output(cmd, shell=True).decode().strip()
                lines = [line.strip() for line in output.splitlines() if line.strip()]
                if len(lines) > 1:
                    return lines[1]
            except Exception:
                pass
            env_cpu = os.getenv("PROCESSOR_IDENTIFIER")
            if env_cpu:
                return env_cpu

        # Linux /proc/cpuinfo fallback
        elif os.name == 'posix':
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if "model name" in line:
                            return line.split(":")[1].strip()
            except Exception:
                pass

        return platform.machine() or "Generic CPU"

    def get_uptime_seconds(self) -> float:
        """Calculate system uptime in seconds."""
        try:
            boot_time = psutil.boot_time()
            return max(0.0, time.time() - boot_time)
        except Exception:
            return 0.0

    def collect(self) -> SystemInfo:
        """Collect and return system info object."""
        return SystemInfo(
            os=self._cached_os,
            os_version=self._cached_os_version,
            architecture=self._cached_arch,
            hostname=self._cached_hostname,
            cpu_model=self._cached_cpu_model,
            uptime_seconds=round(self.get_uptime_seconds(), 2),
            agent_version=self.agent_version,
        )
