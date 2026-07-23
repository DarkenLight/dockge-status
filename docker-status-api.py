#!/usr/bin/env python3
"""
Dockge Status API
-----------------
Lightweight HTTP service exposing Docker container and stack status
for Dockge or GetHomepage dashboards.

Features:
  - /info         → Full JSON array of all containers
  - /summary      → Aggregated stack summary
  - /container/<name> → Details for a single container by name
  - /health       → Simple health check (returns {"status": "ok"})
  - In-memory caching with configurable TTL
  - CORS headers for browser-based dashboards
  - Threaded HTTP server for concurrent requests
  - Proper logging to stdout (works with journalctl)

Environment Variables:
  DOCKGE_STATUS_API_PORT         Port number (default: 9000)
  DOCKGE_STATUS_SCRIPT_PATH      Path to the Bash data collector
                                 (default: /usr/share/dockge-status/docker-status.sh)
  DOCKGE_STATUS_CACHE_TTL        Cache TTL in seconds (default: 5, 0 to disable)
"""

import os
import sys
import json
import signal
import logging
import threading
import subprocess
import time
from functools import wraps
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("dockge-status")

# === Defaults ===
DEFAULT_SCRIPT = "/usr/share/dockge-status/docker-status.sh"
PORT = int(os.getenv("DOCKGE_STATUS_API_PORT", "9000"))
SCRIPT_PATH = os.getenv("DOCKGE_STATUS_SCRIPT_PATH", DEFAULT_SCRIPT)
CACHE_TTL = float(os.getenv("DOCKGE_STATUS_CACHE_TTL", "5"))
WORKING_DIR = os.path.dirname(SCRIPT_PATH)

# === Simple In-Memory Cache ===
_cache = {}
_cache_lock = threading.Lock()


def cached(ttl: float = None):
    """Decorator that caches the return value of a function for `ttl` seconds.
    The cache key is derived from the function name and arguments.
    If ttl is 0, caching is disabled entirely.
    """
    if ttl is None:
        ttl = CACHE_TTL

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if ttl <= 0:
                # Caching disabled
                return func(*args, **kwargs)

            key = (func.__name__, args, tuple(sorted(kwargs.items())))

            with _cache_lock:
                if key in _cache:
                    entry = _cache[key]
                    if time.monotonic() - entry["time"] < ttl:
                        return entry["data"]

            result = func(*args, **kwargs)

            with _cache_lock:
                _cache[key] = {"data": result, "time": time.monotonic()}

            return result

        return wrapper

    return decorator


def clear_cache():
    """Clear all cached entries."""
    with _cache_lock:
        _cache.clear()


# === Script Runner ===
@cached(ttl=CACHE_TTL)
def run_script(mode: str) -> tuple[str, int]:
    """Run the bash script with the given mode and return (output, returncode)."""
    try:
        result = subprocess.run(
            [SCRIPT_PATH, mode],
            cwd=WORKING_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip(), result.returncode, result.stderr.strip()
    except FileNotFoundError:
        return "", -1, f"Script not found: {SCRIPT_PATH}"
    except Exception as e:
        return "", -1, str(e)


def get_single_container(container_name: str) -> tuple[str, int]:
    """Get details for a single container by name.
    Returns (json_output, status_code).
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", '{{json .}}', "--filter", f"name={container_name}"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return json.dumps({"error": result.stderr.strip()}), 500

        lines = [line for line in result.stdout.strip().split("\n") if line.strip()]
        if not lines:
            return json.dumps({"error": f"Container '{container_name}' not found"}), 404

        # Parse the JSON line
        try:
            data = json.loads(lines[0])
            return json.dumps(data, indent=2), 200
        except json.JSONDecodeError:
            return json.dumps({"error": "Failed to parse container data"}), 500

    except FileNotFoundError:
        return json.dumps({"error": "docker command not found"}), 500
    except Exception as e:
        return json.dumps({"error": str(e)}), 500


# === HTTP Handler ===
class DockgeStatusHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Dockge Status API."""

    # Silence default log messages (we use our own logging)
    def log_message(self, format, *args):
        logger.info("↔ %s - %s", self.client_address[0], format % args)

    def _send_json(self, data: str, status: int = 200):
        """Send a JSON response with CORS headers."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(data.encode("utf-8"))

    def _error(self, message: str, status: int = 400):
        """Send a JSON error response."""
        self._send_json(json.dumps({"error": message}) + "\n", status)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        path = self.path.strip("/")
        start_time = time.monotonic()

        # --- /health ---
        if path == "health":
            self._send_json(json.dumps({"status": "ok"}) + "\n")
            elapsed = time.monotonic() - start_time
            logger.debug("Handled /health in %.2fms", elapsed * 1000)
            return

        # --- /container/<name> ---
        if path.startswith("container/"):
            container_name = path[len("container/"):].strip("/")
            if not container_name:
                self._error("Missing container name", 400)
                return
            logger.info("Looking up container: %s", container_name)
            output, status = get_single_container(container_name)
            self._send_json(output + "\n", status)
            elapsed = time.monotonic() - start_time
            logger.debug("Handled /container/%s in %.2fms", container_name, elapsed * 1000)
            return

        # --- /info or /summary ---
        if path in ("info", "summary"):
            output, returncode, stderr_text = run_script(path)
            if returncode != 0:
                self._error(stderr_text or "Script failed", 500)
                elapsed = time.monotonic() - start_time
                logger.warning("Script failed for /%s after %.2fms: %s", path, elapsed * 1000, stderr_text)
                return
            if not output:
                self._error("Empty output from script", 500)
                return

            self._send_json(output + "\n")
            elapsed = time.monotonic() - start_time
            logger.debug("Handled /%s in %.2fms", path, elapsed * 1000)

            # If caching is enabled, note it
            if CACHE_TTL > 0:
                logger.debug("Response cached for %.1fs", CACHE_TTL)

        else:
            self._error("Invalid endpoint. Use /info, /summary, /health, or /container/<name>", 404)


# === Threaded HTTP Server ===
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in separate threads for concurrent processing."""
    allow_reuse_address = True
    daemon_threads = True


# === Graceful Shutdown ===
_server = None


def signal_handler(sig, frame):
    """Handle SIGTERM/SIGINT to shut down gracefully."""
    sig_name = signal.Signals(sig).name
    logger.info("Received %s, shutting down gracefully...", sig_name)
    if _server:
        # Shut down in a thread so we don't block the signal handler
        shutdown_thread = threading.Thread(target=_server.shutdown, daemon=True)
        shutdown_thread.start()


def run():
    """Start the HTTP server."""
    global _server

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    server_address = ("", PORT)

    try:
        _server = ThreadedHTTPServer(server_address, DockgeStatusHandler)
    except OSError as e:
        logger.error("Failed to bind to port %d: %s", PORT, e)
        sys.exit(1)

    logger.info("✅ Dockge Status API running on port %d", PORT)
    logger.info("📜 Using script: %s", SCRIPT_PATH)
    logger.info("📂 Working directory: %s", WORKING_DIR)
    logger.info("⏱️  Cache TTL: %.1fs (set DOCKGE_STATUS_CACHE_TTL=0 to disable)", CACHE_TTL)
    logger.info("📋 Endpoints: /info  /summary  /health  /container/<name>")

    _server.serve_forever()


if __name__ == "__main__":
    run()