"""
CLI Dashboard renderer for RIG AI Provider Node.
Displays real-time node statistics, hardware metrics, RIG available capacity, and health status in a formatted terminal interface.
"""

import os
import sys
from app.models.telemetry import NodeTelemetry, GPUStatus
from app.utils.conversion import bytes_to_gb, bps_to_mbps, format_uptime


class CLIDashboard:
    def __init__(self, clear_screen: bool = True):
        self.clear_screen = clear_screen

    def render(self, telemetry: NodeTelemetry) -> str:
        """Format telemetry into a clean, human-readable terminal dashboard string."""

        output: list[str] = []
        sep = "=" * 65
        sub_sep = "-" * 65

        output.append(sep)
        output.append("                 RIG AI PROVIDER NODE MONITORING                ")
        output.append(sep)

        # 1. NODE SUMMARY
        output.append(f"NODE ID:              {telemetry.node_id}")
        output.append(f"PROVIDER NAME:        {telemetry.system.hostname}")
        output.append(f"HEALTH STATUS:        {telemetry.health.status.value}")
        avail_str = "YES" if telemetry.availability.rig_workload_allowed and telemetry.health.rig_available else "NO"
        output.append(f"RIG AVAILABLE:        {avail_str}")
        output.append(f"UPTIME:               {format_uptime(telemetry.system.uptime_seconds)}")
        output.append(sub_sep)

        # 2. CPU METRICS
        cpu = telemetry.cpu
        output.append("CPU")
        output.append(f"Model:                {telemetry.system.cpu_model}")
        output.append(f"Usage:                {cpu.usage_percent:.1f}%")
        output.append(f"Cores:                {cpu.physical_cores} Physical / {cpu.logical_cores} Logical")
        freq_str = f"{cpu.current_frequency_mhz:.0f} MHz" if cpu.current_frequency_mhz else "N/A"
        output.append(f"Frequency:            {freq_str}")
        output.append(sub_sep)

        # 3. RAM METRICS
        mem = telemetry.memory
        output.append("RAM")
        output.append(f"Total:                {bytes_to_gb(mem.total_bytes):.2f} GB")
        output.append(f"Used:                 {bytes_to_gb(mem.used_bytes):.2f} GB")
        output.append(f"Available:            {bytes_to_gb(mem.available_bytes):.2f} GB")
        output.append(f"Usage:                {mem.usage_percent:.1f}%")
        output.append(sub_sep)

        # 4. GPU METRICS
        output.append("GPU")
        if not telemetry.gpu:
            output.append("Status:               NO GPU DETECTED")
        else:
            for g in telemetry.gpu:
                if g.status != GPUStatus.AVAILABLE:
                    output.append(f"GPU {g.index}:               {g.name} [{g.status.value}] ({g.reason or 'Unavailable'})")
                else:
                    util = f"{g.utilization_percent:.1f}%" if g.utilization_percent is not None else "N/A"
                    temp = f"{g.temperature_celsius:.0f}°C" if g.temperature_celsius is not None else "N/A"
                    pwr = f"{g.power_watts:.1f} W" if g.power_watts is not None else "N/A"
                    vram_str = "N/A"
                    if g.vram:
                        used_g = bytes_to_gb(g.vram.used_bytes)
                        total_g = bytes_to_gb(g.vram.total_bytes)
                        vram_str = f"{used_g:.2f} / {total_g:.2f} GB ({g.vram.usage_percent:.1f}%)"

                    output.append(f"GPU {g.index} Name:          {g.name}")
                    output.append(f"  Utilization:        {util}")
                    output.append(f"  VRAM Usage:         {vram_str}")
                    output.append(f"  Temperature:        {temp}")
                    output.append(f"  Power Usage:        {pwr}")
        output.append(sub_sep)

        # 5. RIG RESOURCE AVAILABILITY FOR SCHEDULER
        avail = telemetry.availability
        output.append("RIG AVAILABLE COMPUTE CAPACITY")
        output.append(f"Available CPUs:       {avail.available_cpus:.1f} Cores")
        output.append(f"Available RAM:        {bytes_to_gb(avail.available_ram_bytes):.2f} GB")
        output.append(f"Available GPUs:       {avail.available_gpus} Device(s)")
        output.append(f"Available VRAM:       {bytes_to_gb(avail.available_vram_bytes):.2f} GB")
        output.append(sub_sep)

        # 6. NETWORK METRICS
        net = telemetry.network
        output.append("NETWORK")
        output.append(f"Download Speed:       {net.download_speed_mbps:.2f} Mbps")
        output.append(f"Upload Speed:         {net.upload_speed_mbps:.2f} Mbps")
        output.append(sep)

        rendered_text = "\n".join(output)

        if self.clear_screen:
            # Clear terminal screen ansi escape
            sys.stdout.write("\033[H\033[J")
            sys.stdout.flush()

        return rendered_text
