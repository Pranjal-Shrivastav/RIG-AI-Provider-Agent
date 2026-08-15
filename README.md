# RIG AI - Provider Node Monitoring Agent

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A production-quality, cross-platform **Provider Node Monitoring Agent** built for **RIG AI**, a decentralized AI compute marketplace.

The agent runs locally on a **Compute Provider's** computer to continuously collect real-time system and hardware telemetry, evaluate node health, calculate compute resources available for RIG workloads, and securely expose/stream that data to the RIG backend and resource scheduler.

---

## Architecture Overview

```
                      +---------------------------------+
                      |   RIG Provider Node Agent       |
                      +---------------------------------+
                                       |
       +-------------------------------+-------------------------------+
       |                               |                               |
       v                               v                               v
[Hardware Collectors]          [Logic Engines]              [Communication & UI]
 ├── CPU (psutil)               ├── Availability Engine      ├── API Client (requests)
 ├── Memory (RAM)               └── Health Engine            ├── Heartbeat Loop
 ├── GPU (NVIDIA NVML)                                       └── CLI Dashboard
 ├── Storage (Multi-Drive I/O)
 └── Network (Speeds & NICs)
```

---

## Features & Capabilities

- **Cross-Platform Telemetry Collectors**:
  - **CPU**: Overall %, per-core %, physical & logical core counts, current/max frequency (MHz), CPU model name, load average.
  - **RAM**: Total, used, available bytes, usage percentage, cached bytes.
  - **GPU Subsystem (NVIDIA NVML)**: Detects single/multi-GPUs, GPU name, GPU core & memory utilization %, VRAM total/used/free, temperature °C, power usage/limit (W), core/memory clock speeds, fan speed. Extensible abstract base class (`GPUProvider`) for future AMD ROCm and Intel OneAPI monitoring.
  - **Storage**: Multi-drive monitoring across all mounted disk partitions (total/used/free/%) and real-time Disk I/O read/write rates.
  - **Network**: Real-time upload/download speeds (Mbps & B/s calculated via delta sampling), NIC details, connection status.
  - **System Info**: OS, OS version, architecture, hostname, uptime seconds, agent version. Cached for low CPU overhead.

- **Dynamic RIG Resource Availability Engine**:
  - Distinguishes raw system utilization from compute available for RIG workloads.
  - Enforces provider reservation limits (`max_cpu_percent_rig`, `max_ram_percent_rig`, `max_gpu_percent_rig`, `max_vram_percent_rig`, `max_gpu_temp_celsius`, `allow_rig_workloads`).

- **Node Health Evaluation System**:
  - Categorizes node health: `HEALTHY`, `DEGRADED`, `UNAVAILABLE`, `OFFLINE`.
  - Configurable thresholds for CPU load, RAM pressure, GPU overheating, disk capacity, and network connectivity.

- **Backend Integration & Reliability**:
  - Authenticated requests using Bearer tokens.
  - Exponential backoff retries, configurable HTTP timeouts.
  - Local offline telemetry buffering queue (buffers up to 100 metrics payloads if backend is temporarily unreachable and flushes automatically on reconnect).

- **Local Live CLI Dashboard**:
  - Formatted terminal dashboard displaying real-time metrics, node identity, health status, and available compute.

---

## Installation

### Prerequisites

- Python **3.11+**
- (Optional for GPU monitoring) NVIDIA GPU with recent graphics driver installed.

### Setup Instructions

1. Clone or navigate to the project directory:
   ```bash
   cd provider-agent
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

Copy `.env.example` to `.env` and adjust provider settings:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `RIG_NODE_ID` | Auto-generated | Unique Node ID (persisted in `.rig_node_id`) |
| `RIG_PROVIDER_NAME` | `Provider-Node-01` | Human-readable node name |
| `RIG_BACKEND_URL` | `http://localhost:8000` | RIG Backend API base URL |
| `RIG_AUTH_TOKEN` | `your_secure_token` | Authentication secret token |
| `RIG_MONITORING_INTERVAL` | `1.0` | Telemetry sampling interval in seconds |
| `RIG_HEARTBEAT_INTERVAL` | `10.0` | Heartbeat pulse interval in seconds |
| `RIG_MAX_CPU_PERCENT` | `80.0` | Max CPU % allowed for RIG workloads |
| `RIG_MAX_RAM_PERCENT` | `80.0` | Max RAM % allowed for RIG workloads |
| `RIG_MAX_GPU_PERCENT` | `90.0` | Max GPU % allowed for RIG workloads |
| `RIG_MAX_VRAM_PERCENT` | `90.0` | Max VRAM % allowed for RIG workloads |
| `RIG_MAX_GPU_TEMP_CELSIUS` | `85.0` | Max GPU temp threshold before node is marked DEGRADED/UNAVAILABLE |
| `RIG_ALLOW_WORKLOADS` | `true` | Enable/disable RIG compute workloads |

---

## Running the Agent

### 1. Run Live Interactive CLI Dashboard

```bash
python -m app.main --dashboard
```

### 2. Run in Headless Background Mode

```bash
python -m app.main --headless
```

### 3. Print Single Telemetry JSON Snapshot & Exit

```bash
python -m app.main --once
```

---

## Telemetry JSON Payload Format

Example telemetry frame generated by the agent:

```json
{
  "node_id": "RIG-NODE-9F81A2B3C4D5",
  "timestamp": "2026-08-15T15:10:00.000Z",
  "agent_version": "0.1.0",
  "system": {
    "os": "Windows",
    "os_version": "10.0.26100",
    "architecture": "AMD64",
    "hostname": "PROVIDER-DESKTOP",
    "cpu_model": "Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz",
    "uptime_seconds": 123456.78,
    "agent_version": "0.1.0"
  },
  "cpu": {
    "usage_percent": 35.2,
    "per_core_percent": [30.0, 40.0, 32.0, 38.0],
    "physical_cores": 8,
    "logical_cores": 16,
    "current_frequency_mhz": 4200.0,
    "max_frequency_mhz": 5000.0,
    "load_average": null
  },
  "memory": {
    "total_bytes": 34293841920,
    "used_bytes": 12884901888,
    "available_bytes": 21408939032,
    "usage_percent": 37.5,
    "cached_bytes": null
  },
  "gpu": [
    {
      "index": 0,
      "name": "NVIDIA GeForce GTX 1050 Ti",
      "status": "AVAILABLE",
      "reason": null,
      "utilization_percent": 25.0,
      "memory_utilization_percent": 15.0,
      "vram": {
        "total_bytes": 4294967296,
        "used_bytes": 1073741824,
        "free_bytes": 3221225472,
        "usage_percent": 25.0
      },
      "temperature_celsius": 52.0,
      "power_watts": 45.2,
      "power_limit_watts": 75.0,
      "graphics_clock_mhz": 1392.0,
      "memory_clock_mhz": 3504.0,
      "fan_speed_percent": 40.0
    }
  ],
  "storage": {
    "partitions": [
      {
        "device": "C:\\",
        "mountpoint": "C:\\",
        "fstype": "NTFS",
        "total_bytes": 1000204886016,
        "used_bytes": 450000000000,
        "free_bytes": 550204886016,
        "usage_percent": 45.0
      }
    ],
    "read_bytes_sec": 1024.0,
    "write_bytes_sec": 4096.0
  },
  "network": {
    "bytes_sent": 10485760,
    "bytes_recv": 52428800,
    "upload_speed_bps": 125000.0,
    "download_speed_bps": 1250000.0,
    "upload_speed_mbps": 1.0,
    "download_speed_mbps": 10.0,
    "interfaces": [
      {
        "name": "Ethernet",
        "addresses": ["192.168.1.100"],
        "is_up": true
      }
    ],
    "is_connected": true
  },
  "availability": {
    "available_cpus": 10.37,
    "available_ram_bytes": 21408939032,
    "available_gpus": 1,
    "available_vram_bytes": 3221225472,
    "rig_workload_allowed": true,
    "explanation": "CPUs Available: 10.37/16; RAM Available: 19.94 GB; GPUs Available: 1/1; VRAM Available: 3.00 GB"
  },
  "health": {
    "status": "HEALTHY",
    "rig_available": true,
    "reasons": ["All node subsystems operating within healthy parameters."],
    "cpu_healthy": true,
    "ram_healthy": true,
    "gpu_healthy": true,
    "disk_healthy": true,
    "network_healthy": true,
    "last_evaluated": "2026-08-15T15:10:00.000Z"
  }
}
```

---

## Testing

Run the full automated test suite using `pytest`:

```bash
pytest -v
```

All hardware calls (including NVML multi-GPU and failure modes) are fully mocked so unit tests pass consistently across all environments.

---

## Future Extensions

1. **AMD GPU Support**: Plug `AMDGPUProvider` into `app/collectors/gpu/` using ROCm `pyrsmi` or `rocm-smi`.
2. **Intel GPU Support**: Plug `IntelGPUProvider` using Intel OneAPI `level-zero` bindings.
3. **Containerized Workload Isolation**: Expose Docker/cgroup hardware isolation statistics to the scheduler.
