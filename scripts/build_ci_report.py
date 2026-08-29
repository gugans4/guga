"""Build a compact CI report from a generated event CSV."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.metrics.ab_testing import activation_experiment_from_events
from src.metrics.core import funnel_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    events = pd.read_csv(args.input, parse_dates=["event_timestamp"])
    funnel = funnel_summary(events).iloc[0]
    ab = activation_experiment_from_events(events)
    report = "\n".join(
        [
            "Growth Funnel Lab CI report",
            f"Events: {len(events):,} | Users: {events['user_id'].nunique():,}",
            f"Signup CVR: {funnel['landing_to_signup_cvr']:.1%}",
            f"Activation CVR: {funnel['signup_to_activation_cvr']:.1%}",
            f"Subscription CVR: {funnel['activation_to_subscription_cvr']:.1%}",
            f"A/B lift: {ab['absolute_lift']:.1%} | p-value: {ab['p_value']:.4f}",
            f"Decision: {ab['decision']}",
        ]
    )
    args.output.write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
