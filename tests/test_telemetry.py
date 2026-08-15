"""
Unit tests for Telemetry Model Serialization and Monitoring Engine.
"""

from app.config.settings import Settings
from app.services.monitor import MonitoringEngine
from app.models.telemetry import NodeTelemetry


def test_monitoring_engine_collect():
    settings = Settings()
    engine = MonitoringEngine(settings)
    
    telemetry = engine.collect_telemetry()
    assert isinstance(telemetry, NodeTelemetry)
    assert telemetry.node_id == settings.node_id
    assert telemetry.system.os != ""
    assert telemetry.cpu.physical_cores >= 1
    assert telemetry.memory.total_bytes > 0
    assert isinstance(telemetry.gpu, list)

    # Test serialization to JSON
    json_str = telemetry.model_dump_json()
    assert '"node_id":' in json_str
    assert '"system":' in json_str

    engine.shutdown()
