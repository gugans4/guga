"""Statistical significance helpers for binary Growth experiments."""

from __future__ import annotations

from statistics import NormalDist

import pandas as pd
from statsmodels.stats.proportion import proportions_ztest


def activation_experiment_test(
    control_successes: int,
    control_users: int,
    treatment_successes: int,
    treatment_users: int,
    alpha: float = 0.05,
) -> dict[str, float | int | bool | str]:
    """Compare two independent activation rates using a two-sided z-test.

    The difference and confidence interval are treatment minus control.
    """
    if min(control_successes, control_users, treatment_successes, treatment_users) < 0:
        raise ValueError("Counts must be non-negative")
    if control_successes > control_users or treatment_successes > treatment_users:
        raise ValueError("Successes cannot exceed users")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if control_users == 0 or treatment_users == 0:
        raise ValueError("Both groups must contain at least one user")

    control_rate = control_successes / control_users
    treatment_rate = treatment_successes / treatment_users
    z_stat, p_value = proportions_ztest(
        [treatment_successes, control_successes],
        [treatment_users, control_users],
        alternative="two-sided",
    )

    difference = treatment_rate - control_rate
    standard_error = (
        treatment_rate * (1 - treatment_rate) / treatment_users
        + control_rate * (1 - control_rate) / control_users
    ) ** 0.5
    critical_value = NormalDist().inv_cdf(1 - alpha / 2)
    ci_low = difference - critical_value * standard_error
    ci_high = difference + critical_value * standard_error
    relative_lift = difference / control_rate if control_rate else float("nan")

    return {
        "control_users": control_users,
        "control_successes": control_successes,
        "control_rate": control_rate,
        "treatment_users": treatment_users,
        "treatment_successes": treatment_successes,
        "treatment_rate": treatment_rate,
        "absolute_lift": difference,
        "relative_lift": relative_lift,
        "z_statistic": float(z_stat),
        "p_value": float(p_value),
        "ci_low": ci_low,
        "ci_high": ci_high,
        "alpha": alpha,
        "significant": bool(p_value < alpha),
        "decision": "Ship candidate" if p_value < alpha and difference > 0 else "Do not ship yet",
    }


def activation_experiment_from_events(events: pd.DataFrame) -> dict[str, float | int | bool | str]:
    """Build the 24-hour activation test from event-level data."""
    typed = events.copy()
    typed["event_timestamp"] = pd.to_datetime(typed["event_timestamp"], utc=True)
    exposure = typed.loc[typed["event_name"].eq("experiment_exposure"), ["user_id", "experiment_variant"]]
    exposure = exposure.drop_duplicates("user_id")
    signup = typed.loc[typed["event_name"].eq("signup"), ["user_id", "event_timestamp"]]
    signup = signup.groupby("user_id", as_index=False)["event_timestamp"].min().rename(columns={"event_timestamp": "signup_time"})
    activation = typed.loc[typed["event_name"].eq("activation"), ["user_id", "event_timestamp"]]
    activation = activation.groupby("user_id", as_index=False)["event_timestamp"].min().rename(columns={"event_timestamp": "activation_time"})
    users = exposure.merge(signup, on="user_id", how="left").merge(activation, on="user_id", how="left")
    users["eligible"] = users["signup_time"].notna()
    users["success"] = (
        users["eligible"]
        & users["activation_time"].ge(users["signup_time"])
        & users["activation_time"].le(users["signup_time"] + pd.Timedelta(hours=24))
    )

    counts = users.groupby("experiment_variant").agg(
        users=("eligible", "sum"),
        successes=("success", "sum"),
    )
    if not {"control", "treatment"}.issubset(counts.index):
        raise ValueError("Both control and treatment variants are required")
    return activation_experiment_test(
        control_successes=int(counts.loc["control", "successes"]),
        control_users=int(counts.loc["control", "users"]),
        treatment_successes=int(counts.loc["treatment", "successes"]),
        treatment_users=int(counts.loc["treatment", "users"]),
    )
