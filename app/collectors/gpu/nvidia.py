"""
NVIDIA GPU telemetry collector using NVML (NVIDIA Management Library via pynvml).
Handles single/multi GPU setups, driver missing/unsupported states, and graceful hardware error recovery.
"""

import logging
from typing import List, Optional
from app.collectors.gpu.base import GPUProvider
from app.models.telemetry import GPUMetrics, GPUStatus, VRAMMetrics

logger = logging.getLogger("rig_agent.gpu.nvidia")

try:
    import pynvml
    PYNVML_INSTALLED = True
except ImportError:
    PYNVML_INSTALLED = False
    pynvml = None


class NvidiaGPUProvider(GPUProvider):
    """NVIDIA GPU provider implementation via NVML."""

    def __init__(self):
        self._initialized = False
        self._init_error_reason: Optional[str] = None
        self._init_nvml()

    def _init_nvml(self) -> None:
        if not PYNVML_INSTALLED:
            self._init_error_reason = "pynvml module not installed in Python environment"
            return
        
        try:
            pynvml.nvmlInit()
            self._initialized = True
            logger.info("Successfully initialized NVIDIA NVML GPU monitoring subsystem.")
        except Exception as e:
            self._initialized = False
            self._init_error_reason = f"NVML Initialization Failed: {str(e)}"
            logger.warning(f"NVIDIA GPU monitoring unavailable: {self._init_error_reason}")

    def is_available(self) -> bool:
        return self._initialized

    def get_gpus(self) -> List[GPUMetrics]:
        if not self._initialized:
            # Return single unavailable entry indicating GPU status
            return [
                GPUMetrics(
                    index=0,
                    name="NVIDIA GPU",
                    status=GPUStatus.UNAVAILABLE,
                    reason=self._init_error_reason or "NVIDIA management interface unavailable",
                )
            ]

        gpu_list: List[GPUMetrics] = []
        try:
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count == 0:
                return [
                    GPUMetrics(
                        index=0,
                        name="NVIDIA GPU",
                        status=GPUStatus.NOT_PRESENT,
                        reason="No NVIDIA GPU devices detected by NVML",
                    )
                ]

            for i in range(device_count):
                gpu_metric = self._collect_device_metrics(i)
                gpu_list.append(gpu_metric)

        except Exception as e:
            logger.error(f"Error querying NVML device count or details: {e}")
            return [
                GPUMetrics(
                    index=0,
                    name="NVIDIA GPU",
                    status=GPUStatus.UNAVAILABLE,
                    reason=f"NVML Runtime Error: {str(e)}",
                )
            ]

        return gpu_list

    def _collect_device_metrics(self, index: int) -> GPUMetrics:
        """Query and format metrics for a single NVML GPU device handle."""
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(index)
            
            # GPU Name
            raw_name = pynvml.nvmlDeviceGetName(handle)
            name = raw_name.decode("utf-8") if isinstance(raw_name, bytes) else str(raw_name)

            # Utilization
            gpu_util: Optional[float] = None
            mem_util: Optional[float] = None
            try:
                rates = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_util = float(rates.gpu)
                mem_util = float(rates.memory)
            except Exception:
                pass

            # VRAM Memory
            vram_metrics: Optional[VRAMMetrics] = None
            try:
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                total_b = int(mem_info.total)
                used_b = int(mem_info.used)
                free_b = int(mem_info.free)
                usage_pct = round((used_b / total_b) * 100.0, 2) if total_b > 0 else 0.0
                
                vram_metrics = VRAMMetrics(
                    total_bytes=total_b,
                    used_bytes=used_b,
                    free_bytes=free_b,
                    usage_percent=usage_pct,
                )
            except Exception:
                pass

            # Temperature
            temp_c: Optional[float] = None
            try:
                temp_c = float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
            except Exception:
                pass

            # Power usage (mW -> W)
            power_w: Optional[float] = None
            try:
                power_mw = pynvml.nvmlDeviceGetPowerUsage(handle)
                power_w = round(float(power_mw) / 1000.0, 2)
            except Exception:
                pass

            # Power limit (mW -> W)
            power_limit_w: Optional[float] = None
            try:
                limit_mw = pynvml.nvmlDeviceGetEnforcedPowerLimit(handle)
                power_limit_w = round(float(limit_mw) / 1000.0, 2)
            except Exception:
                try:
                    limit_mw = pynvml.nvmlDeviceGetPowerManagementLimit(handle)
                    power_limit_w = round(float(limit_mw) / 1000.0, 2)
                except Exception:
                    pass

            # Clocks (MHz)
            gfx_clock: Optional[float] = None
            mem_clock: Optional[float] = None
            try:
                gfx_clock = float(pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS))
            except Exception:
                pass

            try:
                mem_clock = float(pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM))
            except Exception:
                pass

            # Fan Speed (%)
            fan_speed: Optional[float] = None
            try:
                fan_speed = float(pynvml.nvmlDeviceGetFanSpeed(handle))
            except Exception:
                pass

            return GPUMetrics(
                index=index,
                name=name,
                status=GPUStatus.AVAILABLE,
                utilization_percent=gpu_util,
                memory_utilization_percent=mem_util,
                vram=vram_metrics,
                temperature_celsius=temp_c,
                power_watts=power_w,
                power_limit_watts=power_limit_w,
                graphics_clock_mhz=gfx_clock,
                memory_clock_mhz=mem_clock,
                fan_speed_percent=fan_speed,
            )

        except Exception as e:
            return GPUMetrics(
                index=index,
                name=f"NVIDIA GPU #{index}",
                status=GPUStatus.UNAVAILABLE,
                reason=f"Failed to query metrics: {str(e)}",
            )

    def shutdown(self) -> None:
        if self._initialized and PYNVML_INSTALLED:
            try:
                pynvml.nvmlShutdown()
                self._initialized = False
                logger.info("Shut down NVIDIA NVML subsystem.")
            except Exception as e:
                logger.warning(f"Error shutting down NVML: {e}")
