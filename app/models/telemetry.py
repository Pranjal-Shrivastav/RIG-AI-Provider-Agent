"""
Strongly typed telemetry models for RIG Provider Node Monitoring Agent.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.health import NodeHealthInfo


class SystemInfo(BaseModel):
    """Static system and operating system info."""
    os: str
    os_version: str
    architecture: str
    hostname: str
    cpu_model: str
    uptime_seconds: float
    agent_version: str


class CPUMetrics(BaseModel):
    """Real-time CPU utilization and frequency metrics."""
    usage_percent: float
    per_core_percent: List[float] = Field(default_factory=list)
    physical_cores: int
    logical_cores: int
    current_frequency_mhz: Optional[float] = None
    max_frequency_mhz: Optional[float] = None
    load_average: Optional[List[float]] = None


class MemoryMetrics(BaseModel):
    """Real-time RAM metrics."""
    total_bytes: int
    used_bytes: int
    available_bytes: int
    usage_percent: float
    cached_bytes: Optional[int] = None


class VRAMMetrics(BaseModel):
    """VRAM metrics for GPU."""
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float


class GPUStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_PRESENT = "NOT_PRESENT"


class GPUMetrics(BaseModel):
    """Metrics for a single GPU device."""
    index: int
    name: str
    status: GPUStatus = GPUStatus.AVAILABLE
    reason: Optional[str] = None
    utilization_percent: Optional[float] = None
    memory_utilization_percent: Optional[float] = None
    vram: Optional[VRAMMetrics] = None
    temperature_celsius: Optional[float] = None
    power_watts: Optional[float] = None
    power_limit_watts: Optional[float] = None
    graphics_clock_mhz: Optional[float] = None
    memory_clock_mhz: Optional[float] = None
    fan_speed_percent: Optional[float] = None


class DiskPartitionMetrics(BaseModel):
    """Partition capacity and usage metrics."""
    device: str
    mountpoint: str
    fstype: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float


class StorageMetrics(BaseModel):
    """Storage overview across all partitions and I/O rates."""
    partitions: List[DiskPartitionMetrics] = Field(default_factory=list)
    read_bytes_sec: float = 0.0
    write_bytes_sec: float = 0.0


class NetworkInterfaceInfo(BaseModel):
    """Details of a single network interface."""
    name: str
    addresses: List[str] = Field(default_factory=list)
    is_up: bool = True


class NetworkMetrics(BaseModel):
    """Network throughput metrics and interface list."""
    bytes_sent: int
    bytes_recv: int
    upload_speed_bps: float = 0.0
    download_speed_bps: float = 0.0
    upload_speed_mbps: float = 0.0
    download_speed_mbps: float = 0.0
    interfaces: List[NetworkInterfaceInfo] = Field(default_factory=list)
    is_connected: bool = True


class RIGResourceAvailability(BaseModel):
    """Dynamic calculation of resources available strictly for RIG AI workloads."""
    available_cpus: float
    available_ram_bytes: int
    available_gpus: int
    available_vram_bytes: int
    rig_workload_allowed: bool
    explanation: str


class NodeTelemetry(BaseModel):
    """Consolidated telemetry payload sent to RIG backend."""
    node_id: str
    timestamp: str
    agent_version: str
    system: SystemInfo
    cpu: CPUMetrics
    memory: MemoryMetrics
    gpu: List[GPUMetrics] = Field(default_factory=list)
    storage: StorageMetrics
    network: NetworkMetrics
    availability: RIGResourceAvailability
    health: NodeHealthInfo
