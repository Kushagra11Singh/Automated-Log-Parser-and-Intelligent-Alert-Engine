
import json
import os
from datetime import datetime, timezone, timedelta


def load_parsed_entries(parsed_path: str) -> list[dict]:
    if not os.path.exists(parsed_path):
        return []
    with open(parsed_path, "r") as f:
        return json.load(f)


def _entries_in_window(entries: list[dict], window_minutes: int) -> list[dict]:
    """Return only entries within the last window_minutes."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    result = []
    for e in entries:
        try:
            ts_str = e["timestamp"].replace("Z", "+00:00")
            ts = datetime.fromisoformat(ts_str)
            if ts >= cutoff:
                result.append(e)
        except (ValueError, KeyError):
            continue
    return result


def check_alerts(parsed_path: str, thresholds: dict) -> list[dict]:
    """
    Evaluate two alert rules:
      1. Error rate (ERROR + CRITICAL as % of total) exceeds threshold
      2. CRITICAL event count exceeds threshold
    Both evaluated over a rolling time window.
    Returns list of fired alert dicts.
    """
    all_entries = load_parsed_entries(parsed_path)
    window_minutes = thresholds.get("window_minutes", 5)
    windowed = _entries_in_window(all_entries, window_minutes)

    alerts = []
    fired_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    # Rule 1: error rate
    if windowed:
        error_count = sum(1 for e in windowed if e["level"] in ("ERROR", "CRITICAL"))
        error_rate = (error_count / len(windowed)) * 100
        threshold_rate = thresholds.get("error_rate_percent", 20.0)
        if error_rate >= threshold_rate:
            alerts.append({
                "alert_type": "HIGH_ERROR_RATE",
                "fired_at": fired_at,
                "value": round(error_rate, 2),
                "threshold": threshold_rate,
                "window_minutes": window_minutes,
                "message": (
                    f"Error rate {error_rate:.1f}% exceeds threshold "
                    f"{threshold_rate}% over last {window_minutes} min "
                    f"({error_count}/{len(windowed)} events)"
                )
            })

    # Rule 2: critical count
    critical_count = sum(1 for e in windowed if e["level"] == "CRITICAL")
    threshold_crit = thresholds.get("critical_count_per_window", 3)
    if critical_count >= threshold_crit:
        alerts.append({
            "alert_type": "CRITICAL_THRESHOLD_EXCEEDED",
            "fired_at": fired_at,
            "value": critical_count,
            "threshold": threshold_crit,
            "window_minutes": window_minutes,
            "message": (
                f"{critical_count} CRITICAL events in last {window_minutes} min, "
                f"threshold is {threshold_crit}"
            )
        })

    return alerts


def run_alert_engine(parsed_path: str, alert_log_path: str, thresholds: dict) -> list[dict]:
    """Run checks, persist alerts to file, return alert list."""
    os.makedirs(os.path.dirname(alert_log_path), exist_ok=True)
    alerts = check_alerts(parsed_path, thresholds)

    existing = []
    if os.path.exists(alert_log_path):
        with open(alert_log_path, "r") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []

    combined = existing + alerts
    with open(alert_log_path, "w") as f:
        json.dump(combined, f, indent=2)

    if alerts:
        print(f"[alert_engine] {len(alerts)} alert(s) fired: "
              f"{[a['alert_type'] for a in alerts]}")
    else:
        print("[alert_engine] No alerts fired.")

    return alerts


if __name__ == "__main__":
    from app.config import load_config
    cfg = load_config()
    run_alert_engine(cfg["parsed_output"], cfg["alert_log"], cfg["thresholds"])
