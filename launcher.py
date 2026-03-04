"""
Kea Service Launcher.

Starts all microservices in the correct dependency order:

  1. ML Inference (port 8007) — must be fully ready before RAG and MCP Host
     begin their startup sync, which requires the embedding endpoint.
  2. All other services — started concurrently once ML Inference is healthy.

Usage (Kaggle / Colab notebook cell):
    from launcher import start_all_services
    start_all_services()          # verbose
    start_all_services(silent=True)  # errors-only logging
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Callable

import httpx


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _configure_log_level(silent: bool) -> str:
    """Set the global log level and return the uvicorn log-level string."""
    level = "error" if silent else "info"

    if silent:
        os.environ["LOG_LEVEL"] = "ERROR"
        logging.basicConfig(level=logging.ERROR)
        for name in [
            "services.mcp_host",
            "services.orchestrator",
            "services.api_gateway",
            "services.rag_service",
            "services.vault",
            "services.swarm_manager",
            "services.chronos",
            "services.ml_inference",
            "shared",
            "uvicorn",
            "uvicorn.access",
            "uvicorn.error",
        ]:
            logging.getLogger(name).setLevel(logging.ERROR)

    return level


def _wait_for_ml_inference(health_url: str, poll_interval: float, timeout: float) -> bool:
    """
    Block until the ML Inference service reports ``status == "ok"`` on its
    ``/health`` endpoint, or until *timeout* seconds elapse.

    Returns True if the service became healthy, False on timeout.
    """
    deadline = time.monotonic() + timeout
    attempt = 0

    while time.monotonic() < deadline:
        attempt += 1
        try:
            resp = httpx.get(health_url, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ok":
                    print(
                        f"[launcher] ML Inference ready after ~{attempt} poll(s) "
                        f"({data.get('models_loaded', '?')} model(s) on {data.get('device', '?')})."
                    )
                    return True
                print(
                    f"[launcher] ML Inference initializing "
                    f"(models_loaded={data.get('models_loaded', 0)}, "
                    f"status={data.get('status')}) — waiting..."
                )
        except Exception:
            # Service not yet accepting connections — normal during model download.
            print(f"[launcher] Waiting for ML Inference to accept connections (attempt {attempt})...")

        time.sleep(poll_interval)

    return False


def _make_runner(service_name: str, import_path: str, host: str, port: int, log_level: str) -> Callable:
    """Return a zero-argument function that starts a uvicorn service."""

    def _run() -> None:
        import uvicorn

        # Import the app lazily inside the thread so that heavy service
        # imports don't happen on the main thread before ML Inference is ready.
        module_path, app_attr = import_path.rsplit(".", 1)
        import importlib
        module = importlib.import_module(module_path)
        app = getattr(module, app_attr)
        uvicorn.run(app, host=host, port=port, log_level=log_level)

    _run.__name__ = f"run_{service_name}"
    return _run


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def start_all_services(
    silent: bool = False,
    host: str = "127.0.0.1",
) -> None:
    """
    Launch all Kea microservices in dependency order.

    Args:
        silent: When True, suppress all logs except errors.
        host:   Bind address passed to every uvicorn instance.
    """
    from shared.config import get_settings
    from shared.service_registry import ServiceName, ServiceRegistry

    log_level = _configure_log_level(silent)
    settings = get_settings()

    # ------------------------------------------------------------------
    # Step 1 — Start ML Inference first (embedding/reranker model load)
    # ------------------------------------------------------------------
    ml_port = ServiceRegistry.get_port(ServiceName.ML_INFERENCE)
    ml_runner = _make_runner(
        service_name="ml_inference",
        import_path="services.ml_inference.main.app",
        host=host,
        port=ml_port,
        log_level=log_level,
    )
    threading.Thread(target=ml_runner, daemon=True, name="svc-ml_inference").start()
    print(f"[launcher] ML Inference thread started on {host}:{ml_port}.")

    # ------------------------------------------------------------------
    # Step 2 — Wait until ML Inference is healthy before starting others
    # ------------------------------------------------------------------
    ml_health_url = f"http://{host}:{ml_port}/health"
    poll_interval = settings.ml_inference.startup_poll_interval
    health_timeout = settings.ml_inference.startup_health_timeout

    print(
        f"[launcher] Waiting for ML Inference to become ready "
        f"(poll_interval={poll_interval}s, timeout={health_timeout}s)..."
    )

    ready = _wait_for_ml_inference(ml_health_url, poll_interval, health_timeout)
    if not ready:
        print(
            "[launcher] WARNING: ML Inference did not become healthy within "
            f"{health_timeout}s. Proceeding anyway — dependent services will "
            "retry embeddings via their own backoff logic."
        )
    else:
        print("[launcher] ML Inference is healthy. Starting remaining services...")

    # ------------------------------------------------------------------
    # Step 3 — Start all remaining services concurrently
    # ------------------------------------------------------------------
    dependent_services = [
        ("api_gateway",    "services.api_gateway.main.app",    ServiceName.GATEWAY),
        ("orchestrator",   "services.orchestrator.main.app",   ServiceName.ORCHESTRATOR),
        ("mcp_host",       "services.mcp_host.main.app",       ServiceName.MCP_HOST),
        ("rag_service",    "services.rag_service.main.app",    ServiceName.RAG_SERVICE),
        ("vault",          "services.vault.main.app",          ServiceName.VAULT),
        ("swarm_manager",  "services.swarm_manager.main.app",  ServiceName.SWARM_MANAGER),
        ("chronos",        "services.chronos.main.app",        ServiceName.CHRONOS),
    ]

    for svc_name, import_path, service_name_enum in dependent_services:
        port = ServiceRegistry.get_port(service_name_enum)
        runner = _make_runner(
            service_name=svc_name,
            import_path=import_path,
            host=host,
            port=port,
            log_level=log_level,
        )
        threading.Thread(target=runner, daemon=True, name=f"svc-{svc_name}").start()
        print(f"[launcher] {svc_name} thread started on {host}:{port}.")

    mode = "SILENT" if silent else "VERBOSE"
    print(f"\n✅ All services started in {mode} mode.")
