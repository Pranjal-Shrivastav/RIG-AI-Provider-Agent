"""
Main entry point for RIG AI Provider Node Monitoring Agent.
Handles CLI arguments, daemon execution, heartbeat lifecycle, telemetry reporting, and dashboard rendering.
"""

import sys
import time
import json
import argparse
import signal
import logging
from app.config.settings import Settings
from app.utils.logging import setup_logger
from app.services.monitor import MonitoringEngine
from app.services.heartbeat import HeartbeatService
from app.client.api import RIGAPIClient
from app.dashboard import CLIDashboard


def parse_args():
    parser = argparse.ArgumentParser(description="RIG AI Provider Node Monitoring Agent")
    parser.add_argument("--dashboard", action="store_true", help="Run with live interactive CLI terminal dashboard")
    parser.add_argument("--headless", action="store_true", help="Run in headless background mode (default)")
    parser.add_argument("--once", action="store_true", help="Collect single telemetry snapshot, print JSON, and exit")
    parser.add_argument("--env-file", type=str, default=None, help="Path to custom .env configuration file")
    return parser.parse_args()


def main():
    args = parse_args()

    # Load settings
    settings = Settings.load()
    
    # Setup logging
    logger = setup_logger(
        name="rig_agent",
        log_file=settings.log_file,
        log_level=settings.log_level,
    )
    
    logger.info("=" * 60)
    logger.info(f"Starting RIG Provider Node Agent v{settings.agent_version}")
    logger.info(f"Node ID: {settings.node_id}")
    logger.info(f"Backend URL: {settings.backend_url}")
    logger.info("=" * 60)

    # Initialize monitoring engine & API client
    monitor = MonitoringEngine(settings)
    api_client = RIGAPIClient(settings)

    # If --once requested: collect single snapshot, print JSON, shutdown and exit
    if args.once:
        telemetry = monitor.collect_telemetry()
        print(json.dumps(telemetry.model_dump(), indent=2))
        monitor.shutdown()
        sys.exit(0)

    # Initialize heartbeat service
    heartbeat_service = HeartbeatService(
        settings=settings,
        api_client=api_client,
        health_engine=monitor.health_engine,
    )

    # Register node with backend
    initial_telemetry = monitor.collect_telemetry()
    api_client.register_node(initial_telemetry.system.model_dump())
    
    # Start background heartbeat
    heartbeat_service.start()

    dashboard = CLIDashboard(clear_screen=True) if args.dashboard else None

    running = True

    def signal_handler(sig, frame):
        nonlocal running
        logger.info("Shutdown signal received. Stopping agent...")
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info(f"Monitoring active. Interval: {settings.monitoring_interval}s. Press Ctrl+C to stop.")
        while running:
            start_loop = time.time()
            
            # 1. Collect real-time telemetry
            telemetry = monitor.collect_telemetry()

            # 2. Transmit to RIG backend
            api_client.send_telemetry(telemetry)

            # 3. Render dashboard if requested
            if dashboard:
                dashboard_str = dashboard.render(telemetry)
                print(dashboard_str, flush=True)

            # Sleep to match monitoring interval
            elapsed = time.time() - start_loop
            sleep_time = max(0.1, settings.monitoring_interval - elapsed)
            
            # Sub-step sleep to handle interrupt quickly
            sleep_step = 0.2
            slept = 0.0
            while running and slept < sleep_time:
                time.sleep(min(sleep_step, sleep_time - slept))
                slept += sleep_step

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        logger.info("Shutting down agent services...")
        heartbeat_service.stop()
        monitor.shutdown()
        logger.info("RIG Provider Agent stopped cleanly.")


if __name__ == "__main__":
    main()
