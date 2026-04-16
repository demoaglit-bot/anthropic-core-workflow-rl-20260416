import json
from copy import deepcopy
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED_PATH = ROOT / "data" / "seed_state.json"
TEMPLATE_PATH = ROOT / "templates" / "index.html"
STATIC_DIR = ROOT / "static"

STATE = json.loads(SEED_PATH.read_text())


def load_seed():
    return json.loads(SEED_PATH.read_text())


def iso_now():
    return datetime.now(timezone.utc).isoformat()


def json_bytes(payload):
    return json.dumps(payload, indent=2).encode("utf-8")


def build_episode():
    target_task_id = STATE["environment"]["target_task_id"]
    target_task = next(task for task in STATE["tasks"] if task["id"] == target_task_id)
    return {
        "environment": STATE["environment"],
        "observation": {
            "queue": [
                {
                    "id": task["id"],
                    "title": task["title"],
                    "priority": task["priority"],
                    "status": task["status"],
                }
                for task in STATE["tasks"]
            ],
            "target_task": target_task,
        },
    }


def log_transition(task_id, action, reward):
    STATE["environment"]["transition_log"].append(
        {"task_id": task_id, "action": action, "reward": reward, "at": iso_now()}
    )


def find_task(task_id):
    for task in STATE["tasks"]:
        if task["id"] == task_id:
            return task
    return None


def reset_state():
    global STATE
    reset_count = STATE["environment"]["reset_count"] + 1
    STATE = deepcopy(load_seed())
    STATE["environment"]["reset_count"] = reset_count
    return {"ok": True, "reset_count": STATE["environment"]["reset_count"]}


def _response(status, body, content_type):
    return status, {"Content-Type": content_type}, body


def handle_request(method, path, payload=None):
    if path == "/":
        return _response(HTTPStatus.OK, TEMPLATE_PATH.read_bytes(), "text/html; charset=utf-8")

    if path.startswith("/static/"):
        asset = STATIC_DIR / path.removeprefix("/static/")
        if not asset.exists():
            return _response(
                HTTPStatus.NOT_FOUND,
                json_bytes({"error": "asset_not_found"}),
                "application/json; charset=utf-8",
            )
        content_type = (
            "text/css; charset=utf-8" if asset.suffix == ".css" else "text/plain; charset=utf-8"
        )
        return _response(HTTPStatus.OK, asset.read_bytes(), content_type)

    if method == "GET":
        if path == "/api/state":
            return _response(
                HTTPStatus.OK, json_bytes(STATE), "application/json; charset=utf-8"
            )
        if path == "/api/episode":
            return _response(
                HTTPStatus.OK, json_bytes(build_episode()), "application/json; charset=utf-8"
            )
        if path == "/api/tasks":
            return _response(
                HTTPStatus.OK, json_bytes(STATE["tasks"]), "application/json; charset=utf-8"
            )
        if path.startswith("/api/tasks/"):
            task_id = path.split("/")[-1]
            task = find_task(task_id)
            if not task:
                return _response(
                    HTTPStatus.NOT_FOUND,
                    json_bytes({"error": "task_not_found"}),
                    "application/json; charset=utf-8",
                )
            return _response(
                HTTPStatus.OK, json_bytes(task), "application/json; charset=utf-8"
            )

    if method == "POST":
        payload = payload or {}
        if path == "/api/reset":
            return _response(
                HTTPStatus.OK,
                json_bytes(reset_state()),
                "application/json; charset=utf-8",
            )
        if path.startswith("/api/tasks/") and path.endswith("/draft"):
            task_id = path.split("/")[-2]
            task = find_task(task_id)
            if not task:
                return _response(
                    HTTPStatus.NOT_FOUND,
                    json_bytes({"error": "task_not_found"}),
                    "application/json; charset=utf-8",
                )
            draft = (payload.get("draft") or "").strip()
            if not draft:
                return _response(
                    HTTPStatus.BAD_REQUEST,
                    json_bytes({"error": "draft_required"}),
                    "application/json; charset=utf-8",
                )
            task["draft"] = draft
            task["status"] = "drafted"
            task["history"].append({"action": "draft_saved", "at": iso_now(), "draft": draft})
            reward = STATE["environment"]["reward_profile"]["draft_saved"]
            log_transition(task_id, "draft_saved", reward)
            return _response(
                HTTPStatus.OK, json_bytes(task), "application/json; charset=utf-8"
            )
        if path.startswith("/api/tasks/") and path.endswith("/submit"):
            task_id = path.split("/")[-2]
            task = find_task(task_id)
            if not task:
                return _response(
                    HTTPStatus.NOT_FOUND,
                    json_bytes({"error": "task_not_found"}),
                    "application/json; charset=utf-8",
                )
            draft = task.get("draft", "").strip()
            if not draft:
                reward = STATE["environment"]["reward_profile"]["submit_without_draft"]
                log_transition(task_id, "submit_rejected", reward)
                return _response(
                    HTTPStatus.BAD_REQUEST,
                    json_bytes({"error": "draft_required"}),
                    "application/json; charset=utf-8",
                )
            task["final_response"] = draft
            task["status"] = "submitted"
            task["history"].append(
                {"action": "submitted", "at": iso_now(), "final_response": draft}
            )
            reward = STATE["environment"]["reward_profile"]["successful_submit"]
            log_transition(task_id, "submitted", reward)
            return _response(
                HTTPStatus.OK, json_bytes(task), "application/json; charset=utf-8"
            )

    return _response(
        HTTPStatus.NOT_FOUND,
        json_bytes({"error": "not_found"}),
        "application/json; charset=utf-8",
    )
