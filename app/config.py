import json
import os

DEFAULT_CONFIG = {
    "log_file": "logs/app.log",
    "parsed_output": "logs/parsed.json",
    "error_log": "logs/parse_errors.log",
    "alert_log": "logs/alerts.json",
    "thresholds": {
        "error_rate_percent": 20.0,
        "critical_count_per_window": 3,
        "window_minutes": 5
    }
}


def load_config(path: str = "config.json") -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            user_cfg = json.load(f)
        config = {**DEFAULT_CONFIG, **user_cfg}
        config["thresholds"] = {
            **DEFAULT_CONFIG["thresholds"],
            **user_cfg.get("thresholds", {})
        }
        return config
    return DEFAULT_CONFIG.copy()
