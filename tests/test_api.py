# tests/test_api.py
import json
import pytest
from unittest.mock import patch, MagicMock
from app.api import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_get_logs_empty(client):
    with patch("app.api.load_parsed_entries", return_value=[]):
        resp = client.get("/logs")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 0
    assert data["entries"] == []


def test_get_logs_level_filter(client):
    fake = [
        {"timestamp": "2024-01-15T10:00:00.000Z", "level": "ERROR", "message": "bad"},
        {"timestamp": "2024-01-15T10:00:00.000Z", "level": "INFO",  "message": "ok"},
    ]
    with patch("app.api.load_parsed_entries", return_value=fake):
        resp = client.get("/logs?level=ERROR")
    data = resp.get_json()
    assert data["count"] == 1
    assert data["entries"][0]["level"] == "ERROR"


def test_get_alerts_empty(client):
    with patch("os.path.exists", return_value=False):
        resp = client.get("/alerts")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 0


def test_summary_endpoint(client):
    fake = [
        {"timestamp": "2024-01-15T10:00:00.000Z", "level": "INFO",     "message": "a"},
        {"timestamp": "2024-01-15T10:00:00.000Z", "level": "ERROR",    "message": "b"},
        {"timestamp": "2024-01-15T10:00:00.000Z", "level": "CRITICAL", "message": "c"},
    ]
    with patch("app.api.load_parsed_entries", return_value=fake):
        with patch("os.path.exists", return_value=False):
            resp = client.get("/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "error_rate_percent" in data
    assert "level_breakdown" in data


def test_trigger_parse_endpoint(client):
    mock_summary = {"total_lines": 10, "parsed": 10, "failed": 0, "level_breakdown": {}}
    with patch("app.api.parse_log_file", return_value=mock_summary):
        resp = client.post("/parse")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "parsed"
