# tests/test_alert_engine.py
import json
import os
import pytest
from datetime import datetime, timezone, timedelta
from app.alert_engine import check_alerts


def _make_entries(level: str, count: int, minutes_ago: int = 1) -> list[dict]:
    ts = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f"
    )[:-3] + "Z"
    return [{"timestamp": ts, "level": level, "message": "test"} for _ in range(count)]


def _write_parsed(tmp_path, entries):
    p = tmp_path / "parsed.json"
    p.write_text(json.dumps(entries))
    return str(p)


THRESHOLDS = {
    "error_rate_percent": 20.0,
    "critical_count_per_window": 3,
    "window_minutes": 5
}


def test_no_alerts_when_all_info(tmp_path):
    entries = _make_entries("INFO", 50)
    path = _write_parsed(tmp_path, entries)
    alerts = check_alerts(path, THRESHOLDS)
    assert alerts == []


def test_high_error_rate_fires(tmp_path):
    entries = _make_entries("INFO", 70) + _make_entries("ERROR", 30)
    path = _write_parsed(tmp_path, entries)
    alerts = check_alerts(path, THRESHOLDS)
    types = [a["alert_type"] for a in alerts]
    assert "HIGH_ERROR_RATE" in types


def test_critical_threshold_fires(tmp_path):
    entries = _make_entries("INFO", 50) + _make_entries("CRITICAL", 5)
    path = _write_parsed(tmp_path, entries)
    alerts = check_alerts(path, THRESHOLDS)
    types = [a["alert_type"] for a in alerts]
    assert "CRITICAL_THRESHOLD_EXCEEDED" in types


def test_old_entries_outside_window_ignored(tmp_path):
    # entries 60 minutes ago — outside 5-min window
    entries = _make_entries("CRITICAL", 10, minutes_ago=60)
    path = _write_parsed(tmp_path, entries)
    alerts = check_alerts(path, THRESHOLDS)
    assert alerts == []


def test_alert_contains_required_fields(tmp_path):
    entries = _make_entries("ERROR", 50) + _make_entries("INFO", 10)
    path = _write_parsed(tmp_path, entries)
    alerts = check_alerts(path, THRESHOLDS)
    assert len(alerts) > 0
    for alert in alerts:
        assert "alert_type" in alert
        assert "fired_at" in alert
        assert "message" in alert
        assert "threshold" in alert
