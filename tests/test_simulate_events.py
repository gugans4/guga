import pandas as pd

from src.data.simulate_events import EVENT_NAMES, generate_events


def test_generation_is_reproducible():
    first = generate_events(users=100, days=30, seed=7)
    second = generate_events(users=100, days=30, seed=7)
    pd.testing.assert_frame_equal(first, second)


def test_schema_and_event_names():
    events = generate_events(users=100, days=30, seed=7)
    expected = {
        "user_id",
        "event_name",
        "event_timestamp",
        "channel",
        "device_type",
        "country",
        "experiment_variant",
        "revenue",
    }
    assert set(events.columns) == expected
    assert set(events["event_name"]).issubset(EVENT_NAMES)


def test_events_are_ordered_per_user():
    events = generate_events(users=100, days=30, seed=7)
    ordered = events.groupby("user_id")["event_timestamp"].apply(
        lambda values: values.is_monotonic_increasing
    )
    assert ordered.all()


def test_journey_order_for_key_events():
    events = generate_events(users=500, days=30, seed=7)
    first_times = events.pivot_table(
        index="user_id", columns="event_name", values="event_timestamp", aggfunc="min"
    )
    for earlier, later in [("signup", "activation"), ("activation", "subscription")]:
        if earlier in first_times and later in first_times:
            comparable = first_times[[earlier, later]].dropna()
            assert (comparable[later] >= comparable[earlier]).all()


def test_cohort_retention_has_valid_rates():
    from src.metrics.core import cohort_retention

    events = generate_events(users=500, days=60, seed=42)
    retention = cohort_retention(events)
    assert not retention.empty
    assert retention["retention_rate"].between(0, 1).all()
    assert (retention["retained_users"] <= retention["cohort_users"]).all()


def test_ltv_is_non_negative_and_cumulative():
    from src.metrics.core import ltv_by_cohort

    events = generate_events(users=500, days=60, seed=42)
    ltv = ltv_by_cohort(events)
    assert not ltv.empty
    assert (ltv["ltv"] >= 0).all()
    for _, cohort in ltv.groupby("cohort_month"):
        assert cohort["cumulative_revenue"].is_monotonic_increasing
