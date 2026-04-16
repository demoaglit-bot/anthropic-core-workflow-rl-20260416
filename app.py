import copy
import json
import os
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import TCPServer
from urllib.parse import urlparse


ROOT = Path(__file__).parent
SEED_PATH = ROOT / "data" / "seed_state.json"
STATIC_DIR = ROOT / "static"


def load_seed_state():
    return json.loads(SEED_PATH.read_text())


STATE = load_seed_state()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _json(self, payload, status=HTTPStatus.OK):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw or b"{}")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            self._json(STATE)
            return
        if parsed.path == "/health":
            self._json({"ok": True})
            return
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        global STATE
        parsed = urlparse(self.path)
        if parsed.path == "/api/reset":
            STATE = load_seed_state()
            self._json({"ok": True, "state": STATE})
            return
        if parsed.path.startswith("/api/tasks/") and parsed.path.endswith("/transition"):
            task_id = parsed.path.split("/")[3]
            body = self._read_json()
            for task in STATE["tasks"]:
              if task["id"] == task_id:
                    task["status"] = body.get("status", task["status"])
                    task["assignee"] = body.get("assignee", task["assignee"])
                    note = body.get("note", "").strip()
                    if note:
                        task["notes"].append(note)
                    STATE["transitionLog"].append(
                        {
                            "taskId": task_id,
                            "status": task["status"],
                            "assignee": task["assignee"],
                            "note": note,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    self._json({"ok": True, "task": copy.deepcopy(task), "state": STATE})
                    return
            self._json({"ok": False, "error": "task not found"}, status=HTTPStatus.NOT_FOUND)
            return
        self._json({"ok": False, "error": "unknown endpoint"}, status=HTTPStatus.NOT_FOUND)


if __name__ == "__main__":
    preferred_port = int(os.environ.get("PORT", "8016"))
    candidate_ports = [preferred_port] + list(range(preferred_port + 1, preferred_port + 25))

    server = None
    bound_port = None
    for port in candidate_ports:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            bound_port = port
            break
        except OSError:
            continue

    if server is None:
        raise OSError("No open port available in the configured local range")

    print(f"Serving Anthropic Core Workflow RL Environment at http://127.0.0.1:{bound_port}")
    server.serve_forever()
