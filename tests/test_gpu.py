"""
Unit tests for GPU Telemetry Collectors and NVML mocking.
"""

from unittest.mock import MagicMock, patch
from app.collectors.gpu.nvidia import NvidiaGPUProvider
from app.collectors.gpu import GPUCollectorManager
from app.models.telemetry import GPUStatus


def test_gpu_manager_fallback():
    """Verify GPU manager handles environment gracefully."""
    manager = GPUCollectorManager()
    gpus = manager.collect()

    assert isinstance(gpus, list)
    assert len(gpus) >= 1
    assert gpus[0].name != ""


def test_nvidia_gpu_provider_mocked():
    """Test NvidiaGPUProvider with mocked NVML handles."""
    with patch("app.collectors.gpu.nvidia.pynvml") as mock_nvml:
        mock_nvml.nvmlDeviceGetCount.return_value = 2
        
        # Mock handle
        mock_handle = MagicMock()
        mock_nvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_nvml.nvmlDeviceGetName.return_value = "NVIDIA RTX 4090"
        
        # Mock utilization
        rates = MagicMock()
        rates.gpu = 45
        rates.memory = 30
        mock_nvml.nvmlDeviceGetUtilizationRates.return_value = rates

        # Mock memory
        mem_info = MagicMock()
        mem_info.total = 24 * (1024**3)
        mem_info.used = 8 * (1024**3)
        mem_info.free = 16 * (1024**3)
        mock_nvml.nvmlDeviceGetMemoryInfo.return_value = mem_info

        # Mock temperature & power
        mock_nvml.nvmlDeviceGetTemperature.return_value = 62
        mock_nvml.nvmlDeviceGetPowerUsage.return_value = 180000  # 180 W in mW
        mock_nvml.nvmlDeviceGetEnforcedPowerLimit.return_value = 450000  # 450 W in mW
        mock_nvml.nvmlDeviceGetClockInfo.return_value = 2500
        mock_nvml.nvmlDeviceGetFanSpeed.return_value = 55

        provider = NvidiaGPUProvider()
        provider._initialized = True
        
        gpus = provider.get_gpus()

        assert len(gpus) == 2
        gpu0 = gpus[0]
        assert gpu0.name == "NVIDIA RTX 4090"
        assert gpu0.status == GPUStatus.AVAILABLE
        assert gpu0.utilization_percent == 45.0
        assert gpu0.vram is not None
        assert gpu0.vram.total_bytes == 24 * (1024**3)
        assert gpu0.vram.used_bytes == 8 * (1024**3)
        assert gpu0.temperature_celsius == 62.0
        assert gpu0.power_watts == 180.0
        assert gpu0.power_limit_watts == 450.0
        assert gpu0.fan_speed_percent == 55.0


def test_nvidia_gpu_provider_unavailable():
    """Test NvidiaGPUProvider when NVML initialization fails."""
    provider = NvidiaGPUProvider()
    provider._initialized = False
    provider._init_error_reason = "Mocked NVML failure"

    gpus = provider.get_gpus()
    assert len(gpus) == 1
    assert gpus[0].status == GPUStatus.UNAVAILABLE
    assert "Mocked NVML failure" in gpus[0].reason
