"""
Configuration management for RIG AI Provider Agent.
Handles environment variables, node identity persistence, and configurable provider resource limits.
"""

import os
import uuid
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Load environment variables from .env file if available
load_dotenv()


def get_or_create_node_id(id_filepath: str = ".rig_node_id") -> str:
    """
    Get existing persistent Node ID or generate a new one and persist it.
    Ensures Node ID remains stable across agent restarts.
    """
    # 1. Environment variable override
    env_node_id = os.getenv("RIG_NODE_ID")
    if env_node_id and env_node_id.strip():
        return env_node_id.strip()

    path = Path(id_filepath)
    if path.exists():
        try:
            stored_id = path.read_text(encoding="utf-8").strip()
            if stored_id:
                return stored_id
        except Exception:
            pass

    # Generate new unique node ID
    new_node_id = f"RIG-NODE-{uuid.uuid4().hex[:12].upper()}"
    try:
        path.write_text(new_node_id, encoding="utf-8")
    except Exception:
        pass
    
    return new_node_id


class Settings(BaseModel):
    """Provider Node Agent Configuration Settings."""
    
    # Node Identity & Metadata
    node_id: str = Field(default_factory=get_or_create_node_id)
    provider_name: str = Field(default_factory=lambda: os.getenv("RIG_PROVIDER_NAME", "Provider-Node-01"))
    agent_version: str = "0.1.0"
    
    # RIG Backend Connection Settings
    backend_url: str = Field(default_factory=lambda: os.getenv("RIG_BACKEND_URL", "http://localhost:8000"))
    auth_token: str = Field(default_factory=lambda: os.getenv("RIG_AUTH_TOKEN", "default_secret_token"))
    
    # Timing & Frequency (Seconds)
    monitoring_interval: float = Field(default_factory=lambda: float(os.getenv("RIG_MONITORING_INTERVAL", "1.0")))
    heartbeat_interval: float = Field(default_factory=lambda: float(os.getenv("RIG_HEARTBEAT_INTERVAL", "10.0")))
    
    # Provider Resource Reservation & Limits
    max_cpu_percent_rig: float = Field(default_factory=lambda: float(os.getenv("RIG_MAX_CPU_PERCENT", "80.0")))
    max_ram_percent_rig: float = Field(default_factory=lambda: float(os.getenv("RIG_MAX_RAM_PERCENT", "80.0")))
    max_gpu_percent_rig: float = Field(default_factory=lambda: float(os.getenv("RIG_MAX_GPU_PERCENT", "90.0")))
    max_vram_percent_rig: float = Field(default_factory=lambda: float(os.getenv("RIG_MAX_VRAM_PERCENT", "90.0")))
    max_gpu_temp_celsius: float = Field(default_factory=lambda: float(os.getenv("RIG_MAX_GPU_TEMP_CELSIUS", "85.0")))
    allow_rig_workloads: bool = Field(
        default_factory=lambda: os.getenv("RIG_ALLOW_WORKLOADS", "true").lower() in ("true", "1", "yes")
    )
    
    # Logging
    log_level: str = Field(default_factory=lambda: os.getenv("RIG_LOG_LEVEL", "INFO"))
    log_file: str = Field(default_factory=lambda: os.getenv("RIG_LOG_FILE", "logs/provider_agent.log"))

    @classmethod
    def load(cls) -> "Settings":
        """Load settings instance."""
        return cls()


# Global settings singleton helper
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings.load()
    return _settings_instance
