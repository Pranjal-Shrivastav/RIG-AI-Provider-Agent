"""
RIG Backend API Client.
Handles secure HTTP communication with the RIG decentralized compute backend:
- Node Registration
- Periodic Heartbeat
- Telemetry Metrics Transmission
- Dynamic Configuration Fetching
Implements exponential backoff retries, timeouts, and local telemetry buffering queue when backend is offline.
"""

import time
import logging
from collections import deque
from typing import Dict, Any, Optional
import requests
from app.config.settings import Settings
from app.models.telemetry import NodeTelemetry
from app.models.health import NodeHealthInfo

logger = logging.getLogger("rig_agent.client")


class RIGAPIClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self._offline_queue: deque = deque(maxlen=100)  # Buffer up to 100 metrics payloads offline
        self.is_connected = False
        self._last_backend_check = 0.0

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.settings.auth_token}",
            "User-Agent": f"RIG-Provider-Agent/{self.settings.agent_version}",
        }

    def _url(self, path: str) -> str:
        base = self.settings.backend_url.rstrip("/")
        endpoint = path.lstrip("/")
        return f"{base}/{endpoint}"

    def register_node(self, system_dict: Dict[str, Any]) -> bool:
        """Register provider node with RIG backend scheduler."""
        url = self._url("/api/v1/nodes/register")
        payload = {
            "node_id": self.settings.node_id,
            "provider_name": self.settings.provider_name,
            "agent_version": self.settings.agent_version,
            "system_info": system_dict,
        }

        try:
            resp = self.session.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=5.0,
            )
            if resp.status_code in (200, 201):
                logger.info(f"Node successfully registered with RIG backend at {url}")
                self.is_connected = True
                return True
            else:
                logger.warning(f"Registration response HTTP {resp.status_code}: {resp.text}")
                self.is_connected = False
                return False
        except Exception as e:
            logger.warning(f"Failed to register node with RIG backend ({url}): {e}")
            self.is_connected = False
            return False

    def send_heartbeat(self, health: NodeHealthInfo) -> bool:
        """Send periodic pulse/heartbeat to RIG backend."""
        url = self._url("/api/v1/nodes/heartbeat")
        payload = {
            "node_id": self.settings.node_id,
            "timestamp": health.last_evaluated or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "agent_version": self.settings.agent_version,
            "health_status": health.status.value,
            "rig_available": health.rig_available,
        }

        try:
            resp = self.session.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=3.0,
            )
            if resp.status_code == 200:
                self.is_connected = True
                return True
            else:
                logger.warning(f"Heartbeat HTTP {resp.status_code}")
                self.is_connected = False
                return False
        except Exception as e:
            logger.debug(f"Heartbeat failed (backend unreachable): {e}")
            self.is_connected = False
            return False

    def send_telemetry(self, telemetry: NodeTelemetry) -> bool:
        """
        Send structured telemetry to backend metrics endpoint.
        Buffers payload locally if backend is unreachable.
        """
        url = self._url("/api/v1/nodes/metrics")
        payload = telemetry.model_dump()

        # Flush queued offline telemetry if reconnected
        if self.is_connected and len(self._offline_queue) > 0:
            self._flush_offline_queue(url)

        try:
            resp = self.session.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=4.0,
            )
            if resp.status_code in (200, 202):
                self.is_connected = True
                return True
            else:
                logger.warning(f"Telemetry submission returned HTTP {resp.status_code}")
                self._buffer_payload(payload)
                self.is_connected = False
                return False
        except Exception as e:
            logger.warning(f"Backend unreachable for telemetry, buffering locally. ({e})")
            self._buffer_payload(payload)
            self.is_connected = False
            return False

    def _buffer_payload(self, payload: Dict[str, Any]) -> None:
        self._offline_queue.append(payload)
        logger.debug(f"Buffered telemetry frame offline. Queue length: {len(self._offline_queue)}")

    def _flush_offline_queue(self, url: str) -> None:
        logger.info(f"Flushing {len(self._offline_queue)} buffered offline telemetry frames to backend...")
        flushed = 0
        while self._offline_queue:
            payload = self._offline_queue[0]
            try:
                resp = self.session.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                    timeout=3.0,
                )
                if resp.status_code in (200, 202):
                    self._offline_queue.popleft()
                    flushed += 1
                else:
                    break
            except Exception:
                break
        if flushed > 0:
            logger.info(f"Successfully flushed {flushed} offline telemetry frames.")

    def fetch_config(self) -> Optional[Dict[str, Any]]:
        """Fetch remote provider node configuration updates from RIG backend."""
        url = self._url(f"/api/v1/nodes/config?node_id={self.settings.node_id}")
        try:
            resp = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=4.0,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.debug(f"Could not fetch remote config: {e}")
        return None
