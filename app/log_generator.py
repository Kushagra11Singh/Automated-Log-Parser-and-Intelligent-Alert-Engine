import random
import time
import os
from datetime import datetime, timezone

LEVELS = ["INFO", "WARNING", "ERROR", "CRITICAL"]
LEVEL_WEIGHTS = [60, 20, 15, 5]

MESSAGES = {
    "INFO": [
        "User login successful for user_id={}",
        "Request completed in {}ms",
        "Cache hit for key={}",
        "Health check passed",
        "Scheduled job started: {}",
    ],
    "WARNING": [
        "Response time degraded: {}ms",
        "Retry attempt {} for service={}",
        "Memory usage at {}%",
        "Deprecated API endpoint called: /api/v1/{}",
        "Queue depth growing: {} messages pending",
    ],
    "ERROR": [
        "Database connection failed: timeout after {}s",
        "Failed to process request for user_id={}",
        "Service {} returned 500",
        "Unhandled exception in module={}",
        "File not found: /var/data/{}.json",
    ],
    "CRITICAL": [
        "Disk usage at {}% — write operations failing",
        "Out of memory — killing process {}",
        "Database cluster unreachable after {} retries",
        "SSL certificate expired for domain={}",
    ],
}

FILLERS = [
    42, 123, 99, "auth", "payments", "orders",
    "cache_v2", 7, 512, "user_service", 88, 3
]


def _random_message(level: str) -> str:
    template = random.choice(MESSAGES[level])
    try:
        return template.format(*[random.choice(FILLERS)
                                  for _ in range(template.count("{}"))])
    except (IndexError, KeyError):
        return template


def generate_log_line(level: str | None = None) -> str:
    if level is None:
        level = random.choices(LEVELS, weights=LEVEL_WEIGHTS, k=1)[0]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    msg = _random_message(level)
    return f"[{ts}] [{level}] {msg}"


def write_logs(path: str, count: int = 200, burst_errors: bool = False) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for _ in range(count):
            if burst_errors and random.random() < 0.3:
                level = random.choice(["ERROR", "CRITICAL"])
            else:
                level = None
            f.write(generate_log_line(level) + "\n")
    print(f"[log_generator] Wrote {count} log lines to {path}")


if __name__ == "__main__":
    write_logs("logs/app.log", count=200, burst_errors=True)
