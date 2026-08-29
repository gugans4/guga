"""Core user-level funnel metrics for Growth Funnel Lab."""

from __future__ import annotations

import pandas as pd


def _first_event(events: pd.DataFrame, name: str) -> pd.DataFrame:
    subset = events.loc[events["event_name"].eq(name), ["user_id", "event_timestamp"]].copy()
    return subset.groupby("user_id", as_index=False)["event_timestamp"].min().rename(
        columns={"event_timestamp": f"{name}_time"}
    )


def funnel_summary(events: pd.DataFrame) -> pd.DataFrame:
    """Return user counts and conversion rates for the core funnel."""
    required = {"user_id", "event_name", "event_timestamp"}
    missing = required.difference(events.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    typed = events.copy()
    typed["event_timestamp"] = pd.to_datetime(typed["event_timestamp"], utc=True)
    users = pd.DataFrame({"user_id": typed["user_id"].drop_duplicates()})
    for event_name in ("landing_view", "signup", "activation", "subscription"):
        users = users.merge(_first_event(typed, event_name), on="user_id", how="left")

    signup_window = users["signup_time"].notna() & (users["signup_time"] >= users["landing_view_time"]) & (
        users["signup_time"] <= users["landing_view_time"] + pd.Timedelta(days=7)
    )
    activation_window = users["activation_time"].notna() & (users["activation_time"] >= users["signup_time"]) & (
        users["activation_time"] <= users["signup_time"] + pd.Timedelta(hours=24)
    )
    subscription_window = users["subscription_time"].notna() & users["subscription_time"].ge(users["activation_time"]) & (
        users["subscription_time"] <= users["activation_time"] + pd.Timedelta(days=30)
    )

    counts = {
        "landing_users": int(users["landing_view_time"].notna().sum()),
        "signup_users": int(signup_window.sum()),
        "activated_users": int(activation_window.sum()),
        "subscribed_users": int(subscription_window.sum()),
    }
    counts["landing_to_signup_cvr"] = counts["signup_users"] / counts["landing_users"] if counts["landing_users"] else 0.0
    counts["signup_to_activation_cvr"] = counts["activated_users"] / counts["signup_users"] if counts["signup_users"] else 0.0
    counts["activation_to_subscription_cvr"] = counts["subscribed_users"] / counts["activated_users"] if counts["activated_users"] else 0.0
    return pd.DataFrame([counts])


def experiment_summary(events: pd.DataFrame) -> pd.DataFrame:
    """Compare activation within 24 hours for control and treatment users."""
    typed = events.copy()
    typed["event_timestamp"] = pd.to_datetime(typed["event_timestamp"], utc=True)
    exposure = typed.loc[typed["event_name"].eq("experiment_exposure"), ["user_id", "experiment_variant", "event_timestamp"]]
    exposure = exposure.drop_duplicates("user_id").rename(columns={"event_timestamp": "exposure_time"})
    signup = _first_event(typed, "signup")
    activation = _first_event(typed, "activation")
    users = exposure.merge(signup, on="user_id", how="left").merge(activation, on="user_id", how="left")
    users["eligible"] = users["signup_time"].notna()
    users["activated_24h"] = (
        users["eligible"]
        & users["activation_time"].ge(users["signup_time"])
        & users["activation_time"].le(users["signup_time"] + pd.Timedelta(hours=24))
    )
    result = users.groupby("experiment_variant", dropna=False).agg(
        eligible_users=("eligible", "sum"),
        activated_users=("activated_24h", "sum"),
    ).reset_index()
    result["activation_rate"] = result["activated_users"] / result["eligible_users"].replace(0, pd.NA)
    return result


def cohort_retention(events: pd.DataFrame, activity_events: tuple[str, ...] = ("login", "activation")) -> pd.DataFrame:
    """Return monthly cohort retention by signup cohort and months since signup."""
    typed = events.copy()
    typed["event_timestamp"] = pd.to_datetime(typed["event_timestamp"], utc=True)
    signup = _first_event(typed, "signup")
    signup["signup_date"] = signup["signup_time"].dt.floor("D")
    signup["cohort_month"] = signup["signup_date"].dt.strftime("%Y-%m")

    activity = typed.loc[typed["event_name"].isin(activity_events), ["user_id", "event_timestamp"]].drop_duplicates()
    activity = activity.merge(signup[["user_id", "signup_date", "cohort_month"]], on="user_id", how="inner")
    activity["activity_date"] = activity["event_timestamp"].dt.floor("D")
    activity["period_number"] = (
        (activity["activity_date"].dt.year - activity["signup_date"].dt.year) * 12
        + activity["activity_date"].dt.month - activity["signup_date"].dt.month
    )
    activity = activity.loc[activity["period_number"].ge(0)]

    cohort_sizes = signup.groupby("cohort_month")["user_id"].nunique().rename("cohort_users")
    retained = (
        activity.groupby(["cohort_month", "period_number"])["user_id"]
        .nunique()
        .rename("retained_users")
    )
    result = retained.reset_index().merge(cohort_sizes.reset_index(), on="cohort_month", how="left")
    result["retention_rate"] = result["retained_users"] / result["cohort_users"]
    return result.sort_values(["cohort_month", "period_number"]).reset_index(drop=True)


def ltv_by_cohort(events: pd.DataFrame) -> pd.DataFrame:
    """Return cumulative revenue LTV by signup cohort and months since signup."""
    typed = events.copy()
    typed["event_timestamp"] = pd.to_datetime(typed["event_timestamp"], utc=True)
    typed["revenue"] = pd.to_numeric(typed["revenue"], errors="coerce").fillna(0.0)
    signup = _first_event(typed, "signup")
    signup["signup_date"] = signup["signup_time"].dt.floor("D")
    signup["cohort_month"] = signup["signup_date"].dt.strftime("%Y-%m")

    subscriptions = typed.loc[typed["event_name"].eq("subscription"), ["user_id", "event_timestamp", "revenue"]]
    subscriptions = subscriptions.merge(signup[["user_id", "signup_date", "cohort_month"]], on="user_id", how="inner")
    subscriptions["period_number"] = (
        (subscriptions["event_timestamp"].dt.year - subscriptions["signup_date"].dt.year) * 12
        + subscriptions["event_timestamp"].dt.month - subscriptions["signup_date"].dt.month
    )
    revenue = subscriptions.groupby(["cohort_month", "period_number"], as_index=False)["revenue"].sum()
    cohort_sizes = signup.groupby("cohort_month")["user_id"].nunique().rename("cohort_users").reset_index()
    result = revenue.merge(cohort_sizes, on="cohort_month", how="left").sort_values(["cohort_month", "period_number"])
    result["cumulative_revenue"] = result.groupby("cohort_month")["revenue"].cumsum()
    result["ltv"] = result["cumulative_revenue"] / result["cohort_users"]
    return result.reset_index(drop=True)
