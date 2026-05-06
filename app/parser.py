import re
import json
import os
from datetime import datetime, timezone

LOG_PATTERN = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<level>INFO|WARNING|ERROR|CRITICAL)\]\s+(?P<message>.+)$"
)

VALID_LEVELS = {"INFO", "WARNING", "ERROR", "CRITICAL"}


def parse_line(line: str) -> dict | None:
    """Parse a single log line. Returns dict or None if malformed."""
    line = line.strip()
    if not line:
        return None
    match = LOG_PATTERN.match(line)
    if not match:
        return None
    return {
        "timestamp": match.group("timestamp"),
        "level": match.group("level"),
        "message": match.group("message"),
        "parsed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    }


def parse_log_file(
    log_path: str,
    output_path: str,
    error_log_path: str
) -> dict:
    """
    Parse entire log file.
    Returns summary: total, parsed, failed counts + breakdown by level.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(error_log_path), exist_ok=True)

    parsed_entries = []
    error_lines = []
    level_counts = {level: 0 for level in VALID_LEVELS}

    if not os.path.exists(log_path):
        return {"error": f"Log file not found: {log_path}"}

    with open(log_path, "r") as f:
        raw_lines = f.readlines()

    for raw_line in raw_lines:
        result = parse_line(raw_line)
        if result:
            parsed_entries.append(result)
            level_counts[result["level"]] += 1
        else:
            stripped = raw_line.strip()
            if stripped:
                error_lines.append(stripped)

    with open(output_path, "w") as f:
        json.dump(parsed_entries, f, indent=2)

    with open(error_log_path, "w") as f:
        for line in error_lines:
            f.write(line + "\n")

    total = len(raw_lines)
    parsed = len(parsed_entries)
    failed = len(error_lines)

    summary = {
        "total_lines": total,
        "parsed": parsed,
        "failed": failed,
        "level_breakdown": level_counts
    }

    print(
        f"[parser] {parsed}/{total} lines parsed | "
        f"{failed} malformed | breakdown: {level_counts}"
    )
    return summary


if __name__ == "__main__":
    from app.config import load_config
    cfg = load_config()
    parse_log_file(cfg["log_file"], cfg["parsed_output"], cfg["error_log"])
