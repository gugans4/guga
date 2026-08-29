"""Send a Telegram alert when critical cohort anomalies are present."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from src.metrics.anomalies import critical_anomalies, detect_cohort_anomalies, format_critical_alert
from src.metrics.channel_cohorts import cohort_retention_by_channel


def main() -> None:
    input_path = Path(os.environ.get("EVENTS_PATH", "/tmp/events.csv"))
    events = pd.read_csv(input_path, parse_dates=["event_timestamp"])
    anomalies = cohort_retention_by_channel(events)
    critical = critical_anomalies(detect_cohort_anomalies(anomalies))
    text = format_critical_alert(critical)
    if not text:
        print("No critical cohort anomalies detected")
        return

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Critical anomalies detected, but Telegram secrets are not configured")
        print(text)
        return

    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(urllib.request.Request(url, data=payload), timeout=20) as response:
        result = json.loads(response.read())
    if not result.get("ok"):
        raise RuntimeError(result)
    print("Critical anomaly alert sent")


if __name__ == "__main__":
    main()
