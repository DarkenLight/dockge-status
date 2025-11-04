#!/usr/bin/env python3
"""
Dockge Status API
-----------------
Lightweight HTTP service exposing Docker container and stack status
for Dockge or GetHomepage dashboards.

Environment Variables:
  DOCKGE_STATUS_API_PORT       → Port number (default: 9000)
  DOCKGE_STATUS_SCRIPT_PATH    → Path to the Bash data collector
                                (default: /usr/share/dockge-status/docker-status.sh)
"""

import os
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

# === Defaults ===
DEFAULT_SCRIPT = "/usr/share/dockge-status/docker-status.sh"
PORT = int(os.getenv("DOCKGE_STATUS_API_PORT", "9000"))
SCRIPT_PATH = os.getenv("DOCKGE_STATUS_SCRIPT_PATH", DEFAULT_SCRIPT)
WORKING_DIR = os.path.dirname(SCRIPT_PATH)

class DockgeStatusHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()

    def _bad_request(self, message="Invalid request"):
        self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(f'{{"error": "{message}"}}'.encode("utf-8"))

    def do_GET(self):
        path = self.path.strip("/")
        if path in ["info", "summary"]:
            try:
                result = subprocess.run(
                    [SCRIPT_PATH, path],
                    cwd=WORKING_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                if result.returncode != 0:
                    self._bad_request(result.stderr.strip() or "Script failed")
                    return

                output = result.stdout.strip()
                if not output:
                    self._bad_request("Empty output from script")
                    return

                self._set_headers()
                self.wfile.write(output.encode("utf-8"))

            except FileNotFoundError:
                self._bad_request(f"Script not found: {SCRIPT_PATH}")
            except Exception as e:
                self._bad_request(str(e))
        else:
            self._bad_request("Invalid endpoint. Use /info or /summary")

def run():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, DockgeStatusHandler)
    print(f"✅ Dockge Status API running on port {PORT}")
    print(f"📜 Using script: {SCRIPT_PATH}")
    print(f"📂 Working directory: {WORKING_DIR}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
  
