# tests/test_parser.py
import pytest
from app.parser import parse_line


def test_parse_valid_info_line():
    line = "[2024-01-15T10:30:00.123Z] [INFO] User login successful for user_id=42"
    result = parse_line(line)
    assert result is not None
    assert result["level"] == "INFO"
    assert result["message"] == "User login successful for user_id=42"
    assert result["timestamp"] == "2024-01-15T10:30:00.123Z"


def test_parse_valid_critical_line():
    line = "[2024-01-15T10:30:00.000Z] [CRITICAL] Disk usage at 99% — write operations failing"
    result = parse_line(line)
    assert result is not None
    assert result["level"] == "CRITICAL"


def test_parse_malformed_line_returns_none():
    assert parse_line("this is not a valid log line") is None


def test_parse_empty_line_returns_none():
    assert parse_line("") is None
    assert parse_line("   ") is None


def test_parse_invalid_level_returns_none():
    line = "[2024-01-15T10:30:00.000Z] [DEBUG] something"
    assert parse_line(line) is None


def test_parse_result_has_parsed_at_field():
    line = "[2024-01-15T10:30:00.000Z] [ERROR] Something broke"
    result = parse_line(line)
    assert "parsed_at" in result
