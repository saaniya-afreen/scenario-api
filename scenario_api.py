import copy
import json
import os
import random
import threading
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)
_lock = threading.Lock()
assigned = {}  # call_id -> scenario_id (same call, same scenario)
PLACEHOLDER_MARKS = ("<", ">", "{{", "}}", "${")

# Scenario data lives in scenarios.json. Edit that file to add or change
# scenarios; the agent prompt reads everything it needs from the response.
_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenarios.json")


def _load_scenarios():
    with open(_DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    defaults = data.get("defaults", {})
    out = {}
    for sid, sc in data["scenarios"].items():
        merged = copy.deepcopy(defaults)
        for key, value in sc.items():
            if key == "caller" and isinstance(value, dict):
                merged.setdefault("caller", {}).update(value)
            elif key == "answers":
                # Scenario answers come first so they win over the defaults.
                merged["answers"] = value + merged.get("answers", [])
            else:
                merged[key] = value
        out[sid] = merged
    return out


SCENARIOS = _load_scenarios()
with open(_DATA_FILE, encoding="utf-8") as _f:
    ROTATION = [s for s in json.load(_f).get("rotation", []) if s in SCENARIOS]
_next = 0  # position in ROTATION for the next new call


@app.get("/")
@app.get("/health")
def health():
    return {"status": "ok", "scenarios": list(SCENARIOS), "rotation": ROTATION,
            "next": ROTATION[_next % len(ROTATION)] if ROTATION else None}


@app.route("/scenario/assign", methods=["GET", "POST"])
@app.route("/scenario/assign/", methods=["GET", "POST"])
def assign():
    body = request.get_json(silent=True) or {}
    call_id = str(body.get("call_id") or request.args.get("call_id") or "").strip()
    if any(m in call_id for m in PLACEHOLDER_MARKS):
        # Unfilled template text (e.g. "<call id>" or "{{call_id}}") is the same
        # on every call, so it would lock every call to one scenario. Ignore it.
        call_id = ""
    if not call_id:
        # No call ID from the platform: treat this request as a new call.
        call_id = "auto-" + uuid.uuid4().hex[:12]

    # Optional: force a scenario for targeted testing, e.g. ?scenario=IN-01c
    forced = str(body.get("scenario") or request.args.get("scenario") or "").strip()
    if forced and forced not in SCENARIOS:
        return jsonify({"error": f"unknown scenario '{forced}'", "scenarios": list(SCENARIOS)}), 400

    with _lock:
        if forced:
            assigned[call_id] = forced
        elif call_id not in assigned:
            mode = str(body.get("mode") or request.args.get("mode") or "")
            if ROTATION and mode != "random":
                # Each new call gets the next scenario in the rotation, so
                # consecutive calls always start with a different subcase.
                global _next
                assigned[call_id] = ROTATION[_next % len(ROTATION)]
                _next += 1
            else:
                ids = list(SCENARIOS)
                assigned[call_id] = random.choices(
                    ids, weights=[SCENARIOS[i].get("weight", 1) for i in ids])[0]
        sid = assigned[call_id]
    sc = SCENARIOS[sid]
    if str(body.get("full") or request.args.get("full") or "") in ("1", "true"):
        return jsonify({"call_id": call_id, "scenario_id": sid, **sc})
    # Default: a short response that small voice models follow reliably.
    c = sc.get("caller", {})
    details = (
        f"Name: {c.get('name', '')}. Shareholder number: {c.get('shareholder_number', '').rstrip('.')}. "
        f"Registered postal code: {c.get('registered_postal_code', '')}. "
        f"Email: {c.get('email', '')}. Phone: {c.get('phone', '')}. "
        f"Device: {c.get('device', '')}"
    )
    return jsonify({
        "call_id": call_id,
        "scenario_id": sid,
        "use_case": sc.get("use_case", ""),
        "subcase": sc.get("subcase", ""),
        "opening_line": sc["opening_line"],
        "brief": sc.get("brief", ""),
        "my_details": details,
    })


@app.post("/scenario/reset")
def reset():
    global _next
    with _lock:
        assigned.clear()
        _next = 0
    return {"status": "cleared", "next": ROTATION[0] if ROTATION else None}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
