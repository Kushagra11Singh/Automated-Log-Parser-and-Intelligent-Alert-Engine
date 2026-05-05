# Automated Log Parser & Intelligent Alert Engine

A Python backend service that ingests application logs, classifies entries by severity, fires threshold-based alerts over rolling time windows, and exposes everything via a REST API.

## Stack
Python · Flask · Pandas · Docker · pytest · GitHub Actions

## Features
- Regex-based log parser — classifies INFO / WARNING / ERROR / CRITICAL
- Zero data loss — malformed lines written to a dedicated error log
- Configurable threshold alerting over rolling time windows
- REST API — query logs, trigger parsing, fetch alerts, get 24h summary
- Full CI/CD — flake8 lint + pytest + Docker build on every push

## Quick Start

### Run locally
```bash
python main.py
```

### Run with Docker
```bash
docker compose up --build
```

### Run tests
```bash
pytest tests/ -v
```

## API Routes

Main endpoints used in this project:

- GET /health → checks if the service is running
- POST /parse → parses incoming log files
- GET /logs → returns parsed logs (supports filters like level and limit)
- GET /alerts → returns all triggered alerts
- POST /alerts/check → manually runs the alert system
- GET /summary → shows a summary of logs from the last 24 hours

## Configuration

Create a `config.json` to override defaults:

```json
{
  "log_file": "logs/app.log",
  "thresholds": {
    "error_rate_percent": 15.0,
    "critical_count_per_window": 2,
    "window_minutes": 10
  }
}
```
