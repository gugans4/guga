"""Explainable anomaly detection for cohort metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def detect_cohort_anomalies(
    cohort_metrics: pd.DataFrame,
    metric: str = "retention_rate",
    peer_columns: tuple[str, ...] = ("signup_channel", "period_number"),
    minimum_cohort_users: int = 30,
    minimum_peers: int = 3,
    robust_z_threshold: float = 3.5,
) -> pd.DataFrame:
    """Flag unusual cohort values using median/MAD or IQR fallback."""
    required = set(peer_columns) | {metric, "cohort_users"}
    missing = required.difference(cohort_metrics.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if minimum_cohort_users < 1 or minimum_peers < 3:
        raise ValueError("minimum_cohort_users must be positive and minimum_peers must be at least 3")

    result = cohort_metrics.copy()
    result[metric] = pd.to_numeric(result[metric], errors="coerce")
    result["cohort_users"] = pd.to_numeric(result["cohort_users"], errors="coerce")
    eligible = result["cohort_users"].ge(minimum_cohort_users) & result[metric].notna()
    result["peer_count"] = result.groupby(list(peer_columns))[metric].transform("count")
    result["peer_median"] = result.groupby(list(peer_columns))[metric].transform("median")
    result["peer_mad"] = result.groupby(list(peer_columns))[metric].transform(lambda values: np.median(np.abs(values - np.median(values))))
    result["deviation"] = result[metric] - result["peer_median"]
    result["anomaly_score"] = np.where(result["peer_mad"].gt(0), 0.6745 * result["deviation"].abs() / result["peer_mad"], np.nan)

    def iqr_fence(values: pd.Series) -> pd.Series:
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        return pd.Series({"lower": q1 - 1.5 * iqr, "upper": q3 + 1.5 * iqr})

    fences = result.groupby(list(peer_columns))[metric].apply(iqr_fence).reset_index()
    fences = fences.rename(columns={"level_2": "fence"}).pivot(index=list(peer_columns), columns="fence", values=metric).reset_index()
    result = result.merge(fences, on=list(peer_columns), how="left")
    fallback = result["peer_mad"].eq(0) & result["lower"].notna()
    result.loc[fallback, "anomaly_score"] = np.where(result.loc[fallback, metric].lt(result.loc[fallback, "lower"]), robust_z_threshold + 1, np.where(result.loc[fallback, metric].gt(result.loc[fallback, "upper"]), robust_z_threshold + 1, 0.0))
    result["is_anomaly"] = eligible & result["peer_count"].ge(minimum_peers) & result["anomaly_score"].ge(robust_z_threshold)
    result["reason"] = np.select([~eligible, result["peer_count"].lt(minimum_peers), result["is_anomaly"]], ["Insufficient cohort size", "Insufficient comparable peers", "Unusual versus comparable cohort-period peers"], default="Within expected range")
    return result.sort_values([*peer_columns, "cohort_month"] if "cohort_month" in result.columns else list(peer_columns)).reset_index(drop=True)


def critical_anomalies(
    anomalies: pd.DataFrame,
    score_threshold: float = 5.0,
    minimum_cohort_users: int = 100,
) -> pd.DataFrame:
    """Return high-confidence anomalies eligible for external alerting."""
    required = {"is_anomaly", "anomaly_score", "cohort_users"}
    missing = required.difference(anomalies.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return anomalies.loc[
        anomalies["is_anomaly"]
        & anomalies["anomaly_score"].ge(score_threshold)
        & anomalies["cohort_users"].ge(minimum_cohort_users)
    ].copy()


def format_critical_alert(anomalies: pd.DataFrame) -> str:
    """Format critical anomalies without exposing raw event-level data."""
    critical = critical_anomalies(anomalies)
    if critical.empty:
        return ""
    lines = [f"Growth Funnel Lab: {len(critical)} critical cohort anomaly(s)"]
    for _, row in critical.head(10).iterrows():
        channel = row.get("signup_channel", "all")
        cohort = row.get("cohort_month", "unknown")
        period = row.get("period_number", "unknown")
        lines.append(f"- {channel} | {cohort} | M{int(period)} | score {row['anomaly_score']:.2f} | users {int(row['cohort_users'])}")
    lines.append("Investigate tracking, campaigns, seasonality, and product changes before assigning a cause.")
    return "\n".join(lines)
