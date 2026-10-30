from __future__ import annotations

import csv
import argparse
import json
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/data":
            summary_path = OUT / "run_summary.json"
            if not summary_path.exists():
                self._json(200, {"ready": False})
                return
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            with (OUT / "timetable.csv").open(encoding="utf-8", newline="") as f:
                timetable = list(csv.DictReader(f))
            self._json(200, {"ready": True, "summary": summary, "timetable": timetable})
            return
        body = (ROOT / "dashboard.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/run":
            self._json(404, {"error": "Unknown endpoint"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            values = {k: v[-1] for k, v in parse_qs(self.rfile.read(size).decode()).items()}
            command = [sys.executable, str(ROOT / "main.py"), "--output", str(OUT)]
            for arg in ("students", "population", "generations", "seed"):
                if arg in values:
                    command += ["--" + arg, values[arg]]
            if values.get("start_date"):
                command += ["--start-date", values["start_date"]]
            if values.get("end_date"):
                command += ["--end-date", values["end_date"]]
            if values.get("branch_sizes"):
                command += ["--branch-sizes", values["branch_sizes"]]
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180)
            if run.returncode:
                message = run.stderr or run.stdout or "The timetable run failed."
                match = re.search(r"ValueError: (.+)", message)
                if match:
                    message = match.group(1).strip()
                self._json(400, {"error": message})
            else:
                self._json(200, {"ok": True, "message": "Comparison complete"})
        except subprocess.TimeoutExpired:
            self._json(408, {"error": "Run exceeded the 180 second limit. Reduce population or generations."})
        except Exception as exc:
            self._json(500, {"error": str(exc)})

    def log_message(self, fmt, *args):
        print("[dashboard] " + fmt % args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local exam timetable dashboard")
    parser.add_argument("--port", type=int, default=8766)
    port = parser.parse_args().port
    OUT.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Dashboard ready at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped")
