"""Render a detailed anomaly-score distribution chart."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.metrics.anomalies import detect_cohort_anomalies
from src.metrics.channel_cohorts import cohort_retention_by_channel


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    events = pd.read_csv(args.input, parse_dates=["event_timestamp"])
    anomalies = detect_cohort_anomalies(cohort_retention_by_channel(events))
    anomalies = anomalies.dropna(subset=["anomaly_score"]).copy()
    anomalies["label"] = anomalies["signup_channel"] + " | " + anomalies["cohort_month"] + " | M" + anomalies["period_number"].astype(int).astype(str)

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), gridspec_kw={"width_ratios": [1, 1.6]})
    channels = sorted(anomalies["signup_channel"].unique())
    box_data = [anomalies.loc[anomalies["signup_channel"].eq(channel), "anomaly_score"] for channel in channels]
    axes[0].boxplot(box_data, tick_labels=channels, patch_artist=True, boxprops={"facecolor": "#FED7AA"}, medianprops={"color": "#9A3412"})
    axes[0].axhline(3.5, color="#EA580C", linestyle="--", label="Flag threshold 3.5")
    axes[0].axhline(5.0, color="#991B1B", linestyle=":", label="Critical threshold 5.0")
    axes[0].set_title("Score distribution by channel")
    axes[0].set_ylabel("Robust anomaly score")
    axes[0].legend(fontsize=8)

    colors = anomalies["is_anomaly"].map({True: "#C2410C", False: "#64748B"})
    axes[1].scatter(anomalies["cohort_month"], anomalies["anomaly_score"], c=colors, s=anomalies["cohort_users"].clip(lower=20) / 2, alpha=0.8, edgecolors="white", linewidths=0.5)
    for _, row in anomalies.loc[anomalies["is_anomaly"]].iterrows():
        axes[1].annotate(f"{row['signup_channel']} · M{int(row['period_number'])}", (row["cohort_month"], row["anomaly_score"]), xytext=(4, 4), textcoords="offset points", fontsize=7)
    axes[1].axhline(3.5, color="#EA580C", linestyle="--")
    axes[1].axhline(5.0, color="#991B1B", linestyle=":")
    axes[1].set_title("Cohort-period anomaly scores")
    axes[1].set_xlabel("Signup cohort")
    axes[1].set_ylabel("Robust anomaly score")
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].grid(axis="y", alpha=0.2)

    fig.suptitle("Growth Funnel Lab — Cohort anomaly score distribution", fontsize=15, fontweight="bold")
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180, bbox_inches="tight")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
