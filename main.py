from app.config import load_config
from app.log_generator import write_logs
from app.parser import parse_log_file
from app.alert_engine import run_alert_engine
from app.api import app


def main():
    cfg = load_config()

    print("=== Log Alert Engine Starting ===")
    write_logs(cfg["log_file"], count=200, burst_errors=True)
    parse_log_file(cfg["log_file"], cfg["parsed_output"], cfg["error_log"])
    run_alert_engine(cfg["parsed_output"], cfg["alert_log"], cfg["thresholds"])
    print("=== Pipeline complete. Starting API on :5001 ===")

    app.run(host="0.0.0.0", port=5001, debug=False)


if __name__ == "__main__":
    main()
