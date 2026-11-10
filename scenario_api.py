import os
import random
import threading
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)
_lock = threading.Lock()
assigned = {}  # call_id -> scenario_id (same call, same scenario)

SCENARIOS = {
    "IN-01a": {"opening_line": "I want to register as a member, but I don't know how.",
               "hidden_cause": "none"},
    "IN-01b": {"opening_line": "I entered my shareholder number and postal code, but I can't proceed.",
               "hidden_cause": "postal code typed with a hyphen"},
    "IN-01c": {"opening_line": "I entered my shareholder number and postal code, but I can't proceed.",
               "hidden_cause": "moved; postal code differs from notice"},
    "IN-01d": {"opening_line": "I entered my email address, phone number and so on, but I can't go any further.",
               "hidden_cause": "phone number typed with hyphens"},
    "IN-01e": {"opening_line": "I want to register as a member, but I don't have my shareholder number with me.",
               "hidden_cause": "shareholder number on notice letter at home"},
}

@app.get("/")
@app.get("/health")
def health():
    return {"status": "ok", "scenarios": list(SCENARIOS)}

@app.route("/scenario/assign", methods=["GET", "POST"])
@app.route("/scenario/assign/", methods=["GET", "POST"])
def assign():
    body = request.get_json(silent=True) or {}
    call_id = str(body.get("call_id") or request.args.get("call_id") or "").strip()
    if not call_id:
        # No call ID from the platform: treat this request as a new call.
        call_id = "auto-" + uuid.uuid4().hex[:12]
    with _lock:
        if call_id not in assigned:
            assigned[call_id] = random.choice(list(SCENARIOS))
        sid = assigned[call_id]
    return jsonify({"call_id": call_id, "scenario_id": sid, **SCENARIOS[sid]})

@app.post("/scenario/reset")
def reset():
    with _lock:
        assigned.clear()
    return {"status": "cleared"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
