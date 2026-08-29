"""Channel-segmented cohort retention and observed LTV metrics."""

from __future__ import annotations

import pandas as pd


def _signup_users(events: pd.DataFrame) -> pd.DataFrame:
    typed = events.copy()
    typed["event_timestamp"] = pd.to_datetime(typed["event_timestamp"], utc=True)
    signup = typed.loc[typed["event_name"].eq("signup"), ["user_id", "event_timestamp", "channel"]]
    signup = signup.sort_values("event_timestamp").drop_duplicates("user_id")
    signup = signup.rename(columns={"event_timestamp": "signup_time", "channel": "signup_channel"})
    signup["signup_date"] = signup["signup_time"].dt.floor("D")
    signup["cohort_month"] = signup["signup_date"].dt.strftime("%Y-%m")
    return signup


def cohort_retention_by_channel(events: pd.DataFrame, activity_events: tuple[str, ...] = ("login", "activation")) -> pd.DataFrame:
    """Return monthly retention by signup cohort and first-touch channel."""
    signup = _signup_users(events)
    typed = events.copy()
    typed["event_timestamp"] = pd.to_datetime(typed["event_timestamp"], utc=True)
    activity = typed.loc[typed["event_name"].isin(activity_events), ["user_id", "event_timestamp"]].drop_duplicates()
    activity = activity.merge(signup[["user_id", "signup_date", "cohort_month", "signup_channel"]], on="user_id", how="inner")
    activity["activity_date"] = activity["event_timestamp"].dt.floor("D")
    activity["period_number"] = (
        (activity["activity_date"].dt.year - activity["signup_date"].dt.year) * 12
        + activity["activity_date"].dt.month - activity["signup_date"].dt.month
    )
    activity = activity.loc[activity["period_number"].ge(0)]
    cohort_sizes = signup.groupby(["signup_channel", "cohort_month"])["user_id"].nunique().rename("cohort_users")
    retained = activity.groupby(["signup_channel", "cohort_month", "period_number"])["user_id"].nunique().rename("retained_users")
    result = retained.reset_index().merge(cohort_sizes.reset_index(), on=["signup_channel", "cohort_month"], how="left")
    result["retention_rate"] = result["retained_users"] / result["cohort_users"]
    return result.sort_values(["signup_channel", "cohort_month", "period_number"]).reset_index(drop=True)


def ltv_by_channel(events: pd.DataFrame) -> pd.DataFrame:
    """Return cumulative observed LTV by signup cohort, channel, and month."""
    typed = events.copy()
    typed["event_timestamp"] = pd.to_datetime(typed["event_timestamp"], utc=True)
    typed["revenue"] = pd.to_numeric(typed["revenue"], errors="coerce").fillna(0.0)
    signup = _signup_users(typed)
    subscriptions = typed.loc[typed["event_name"].eq("subscription"), ["user_id", "event_timestamp", "revenue"]]
    subscriptions = subscriptions.merge(signup[["user_id", "signup_date", "cohort_month", "signup_channel"]], on="user_id", how="inner")
    subscriptions["period_number"] = (
        (subscriptions["event_timestamp"].dt.year - subscriptions["signup_date"].dt.year) * 12
        + subscriptions["event_timestamp"].dt.month - subscriptions["signup_date"].dt.month
    )
    revenue = subscriptions.groupby(["signup_channel", "cohort_month", "period_number"], as_index=False)["revenue"].sum()
    cohort_sizes = signup.groupby(["signup_channel", "cohort_month"])["user_id"].nunique().rename("cohort_users").reset_index()
    result = revenue.merge(cohort_sizes, on=["signup_channel", "cohort_month"], how="left")
    result = result.sort_values(["signup_channel", "cohort_month", "period_number"])
    result["cumulative_revenue"] = result.groupby(["signup_channel", "cohort_month"])["revenue"].cumsum()
    result["ltv"] = result["cumulative_revenue"] / result["cohort_users"]
    return result.reset_index(drop=True)
