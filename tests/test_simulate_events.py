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
