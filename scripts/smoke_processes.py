"""Start real API and worker processes, verify them, and clean up both processes."""

import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from uuid import uuid4

from ingestion_worker.app import create_worker

processes: list[subprocess.Popen] = []
controller = create_worker()
with tempfile.TemporaryFile() as logs:
    try:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        api = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-access-log",
            ],
            stdout=logs,
            stderr=logs,
        )
        processes.append(api)
        deadline = time.monotonic() + 30
        while True:
            if api.poll() is not None:
                raise RuntimeError("API process exited before readiness")
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/ready", timeout=10
                ) as response:
                    ready = json.load(response)
                assert ready["status"] == "ready"
                break
            except (urllib.error.URLError, TimeoutError):
                if time.monotonic() >= deadline:
                    raise RuntimeError("API readiness timed out") from None
                time.sleep(0.2)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as response:
            assert json.load(response) == {"status": "ok"}

        node = f"rag-smoke-{uuid4().hex}@localhost"
        worker = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "celery",
                "-q",
                "-A",
                "ingestion_worker.app:app",
                "worker",
                "--pool=solo",
                "--concurrency=1",
                f"--hostname={node}",
                "--loglevel=ERROR",
                "--without-gossip",
                "--without-mingle",
            ],
            stdout=logs,
            stderr=logs,
        )
        processes.append(worker)
        deadline = time.monotonic() + 30
        while True:
            if worker.poll() is not None:
                raise RuntimeError("Worker process exited before responding")
            replies = controller.control.ping(destination=[node], timeout=1)
            if any(reply.get(node, {}).get("ok") == "pong" for reply in replies):
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("Worker ping timed out")
        print(json.dumps({"api_health": "ok", "api_readiness": ready, "worker_ping": "pong"}))
    finally:
        for process in reversed(processes):
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        controller.close()
