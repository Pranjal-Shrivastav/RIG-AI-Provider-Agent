"""
Health evaluation data models for RIG Provider Agent.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    OFFLINE = "OFFLINE"


class NodeHealthInfo(BaseModel):
    """Detailed health status report of the provider node."""
    status: HealthStatus = HealthStatus.HEALTHY
    rig_available: bool = True
    reasons: List[str] = Field(default_factory=list)
    cpu_healthy: bool = True
    ram_healthy: bool = True
    gpu_healthy: bool = True
    disk_healthy: bool = True
    network_healthy: bool = True
    last_evaluated: str = ""
