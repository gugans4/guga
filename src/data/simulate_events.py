"""Generate a deterministic synthetic event dataset for Growth Funnel Lab.

Usage:
    python -m src.data.simulate_events --users 5000 --output data/raw/events.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

EVENT_NAMES = {
    "landing_view",
    "signup",
    "experiment_exposure",
    "activation",
    "login",
    "subscription",
}
CHANNELS = ("organic", "paid_search", "paid_social", "referral", "email")
DEVICES = ("desktop", "mobile", "tablet")
COUNTRIES = ("US", "GB", "DE", "CA", "AU", "OTHER")


def _clip_probability(value: float) -> float:
    return float(np.clip(value, 0.01, 0.98))


def _event(
    rows: list[dict],
    user_id: str,
    event_name: str,
    timestamp: pd.Timestamp,
    channel: str,
    device_type: str,
    country: str,
    variant: str | None = None,
    revenue: float | None = None,
) -> None:
    rows.append(
        {
            "user_id": user_id,
            "event_name": event_name,
            "event_timestamp": timestamp.isoformat(),
            "channel": channel,
            "device_type": device_type,
            "country": country,
            "experiment_variant": variant,
            "revenue": revenue,
        }
    )


def generate_events(
    users: int = 5000,
    start_date: str = "2025-01-01",
    days: int = 90,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate one anonymous event stream with reproducible user journeys."""
    if users < 1:
        raise ValueError("users must be positive")
    if days < 1:
        raise ValueError("days must be positive")

    rng = np.random.default_rng(seed)
    start = pd.Timestamp(start_date, tz="UTC")
    rows: list[dict] = []

    channel_probs = np.array([0.30, 0.22, 0.20, 0.13, 0.15])
    device_probs = np.array([0.48, 0.44, 0.08])
    country_probs = np.array([0.42, 0.14, 0.12, 0.10, 0.08, 0.14])

    for index in range(users):
        user_id = f"u_{index + 1:06d}"
        channel = str(rng.choice(CHANNELS, p=channel_probs))
        device = str(rng.choice(DEVICES, p=device_probs))
        country = str(rng.choice(COUNTRIES, p=country_probs))
        signup_offset = int(rng.integers(0, days))
        landing_time = start + pd.Timedelta(days=signup_offset, minutes=int(rng.integers(0, 1440)))

        _event(rows, user_id, "landing_view", landing_time, channel, device, country)

        signup_base = {
            "organic": 0.58,
            "paid_search": 0.46,
            "paid_social": 0.34,
            "referral": 0.64,
            "email": 0.52,
        }[channel]
        signup_probability = signup_base + (0.04 if device == "desktop" else -0.02 if device == "mobile" else 0.0)
        if rng.random() >= _clip_probability(signup_probability):
            continue

        signup_time = landing_time + pd.Timedelta(hours=int(rng.integers(1, 48)))
        if signup_time >= start + pd.Timedelta(days=days + 7):
            continue
        _event(rows, user_id, "signup", signup_time, channel, device, country)

        variant = str(rng.choice(("control", "treatment")))
        exposure_time = signup_time + pd.Timedelta(minutes=int(rng.integers(1, 30)))
        _event(rows, user_id, "experiment_exposure", exposure_time, channel, device, country, variant)

        activation_base = {
            "organic": 0.55,
            "paid_search": 0.48,
            "paid_social": 0.39,
            "referral": 0.62,
            "email": 0.51,
        }[channel]
        activation_probability = activation_base
        activation_probability += 0.06 if device == "desktop" else -0.04 if device == "mobile" else 0.0
        activation_probability += 0.07 if variant == "treatment" else 0.0
        if rng.random() >= _clip_probability(activation_probability):
            continue

        activation_time = signup_time + pd.Timedelta(hours=int(rng.integers(1, 25)))
        _event(rows, user_id, "activation", activation_time, channel, device, country, variant)

        login_count = int(rng.poisson(2.4 if variant == "treatment" else 2.0))
        for _ in range(login_count):
            login_time = activation_time + pd.Timedelta(days=int(rng.integers(1, 31)), hours=int(rng.integers(0, 24)))
            _event(rows, user_id, "login", login_time, channel, device, country, variant)

        subscription_probability = 0.24 + (0.05 if variant == "treatment" else 0.0)
        if rng.random() < subscription_probability:
            subscription_time = activation_time + pd.Timedelta(days=int(rng.integers(1, 31)))
            revenue = round(float(rng.choice([19.0, 29.0, 49.0], p=[0.50, 0.35, 0.15])), 2)
            _event(rows, user_id, "subscription", subscription_time, channel, device, country, variant, revenue)

    events = pd.DataFrame(rows)
    events["event_timestamp"] = pd.to_datetime(events["event_timestamp"], utc=True)
    events = events.sort_values(["user_id", "event_timestamp", "event_name"], kind="stable").reset_index(drop=True)
    return events


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--users", type=int, default=5000)
    parser.add_argument("--start-date", default="2025-01-01")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("data/raw/events.csv"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events = generate_events(args.users, args.start_date, args.days, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    events.to_csv(args.output, index=False)
    print(f"Wrote {len(events):,} events for {events['user_id'].nunique():,} users to {args.output}")
    print(events["event_name"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
