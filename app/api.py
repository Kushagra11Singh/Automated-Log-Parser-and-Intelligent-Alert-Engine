
import json
import os
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request
from app.config import load_config
from app.parser import parse_log_file
from app.alert_engine import run_alert_engine, load_parsed_entries

app = Flask(__name__)


def _get_cfg():
    return load_config()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})


@app.route("/parse", methods=["POST"])
def trigger_parse():
    """Trigger log parsing on demand."""
    cfg = _get_cfg()
    summary = parse_log_file(cfg["log_file"], cfg["parsed_output"], cfg["error_log"])
    return jsonify({"status": "parsed", "summary": summary})


@app.route("/alerts", methods=["GET"])
def get_alerts():
    """Return all alerts from the alert log."""
    cfg = _get_cfg()
    if not os.path.exists(cfg["alert_log"]):
        return jsonify({"alerts": [], "count": 0})
    with open(cfg["alert_log"], "r") as f:
        try:
            alerts = json.load(f)
        except json.JSONDecodeError:
            alerts = []
    return jsonify({"alerts": alerts, "count": len(alerts)})


@app.route("/alerts/check", methods=["POST"])
def trigger_alert_check():
    """Run alert engine on current parsed data."""
    cfg = _get_cfg()
    alerts = run_alert_engine(cfg["parsed_output"], cfg["alert_log"], cfg["thresholds"])
    return jsonify({"fired": len(alerts), "alerts": alerts})


@app.route("/logs", methods=["GET"])
def get_logs():
    """
    Return parsed log entries.
    Query params:
      level = INFO | WARNING | ERROR | CRITICAL
      limit = int (default 100)
    """
    cfg = _get_cfg()
    entries = load_parsed_entries(cfg["parsed_output"])

    level_filter = request.args.get("level", "").upper()
    if level_filter:
        entries = [e for e in entries if e.get("level") == level_filter]

    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        limit = 100

    entries = entries[-limit:]
    return jsonify({"entries": entries, "count": len(entries)})


@app.route("/summary", methods=["GET"])
def get_summary():
    """
    24-hour summary: level breakdown, error rate, alert count.
    """
    cfg = _get_cfg()
    all_entries = load_parsed_entries(cfg["parsed_output"])

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    windowed = []
    for e in all_entries:
        try:
            ts = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
            if ts >= cutoff:
                windowed.append(e)
        except (ValueError, KeyError):
            continue

    level_counts = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
    for e in windowed:
        level = e.get("level", "")
        if level in level_counts:
            level_counts[level] += 1

    total = len(windowed)
    error_count = level_counts["ERROR"] + level_counts["CRITICAL"]
    error_rate = round((error_count / total) * 100, 2) if total > 0 else 0.0

    alert_count = 0
    if os.path.exists(cfg["alert_log"]):
        with open(cfg["alert_log"], "r") as f:
            try:
                alert_count = len(json.load(f))
            except json.JSONDecodeError:
                alert_count = 0

    return jsonify({
        "window": "24h",
        "total_events": total,
        "level_breakdown": level_counts,
        "error_rate_percent": error_rate,
        "active_alerts": alert_count
    })
