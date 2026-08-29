from pathlib import Path

import pandas as pd
import streamlit as st

from src.metrics.core import experiment_summary, funnel_summary

st.set_page_config(page_title="Growth Funnel Lab", layout="wide")
st.title("Growth Funnel Lab")
st.caption("Decision-oriented funnel, cohort, and experiment analytics")

DATA_PATH = Path("data/raw/events.csv")
if not DATA_PATH.exists():
    st.warning("No dataset found. Run: python -m src.data.simulate_events")
    st.stop()

events = pd.read_csv(DATA_PATH, parse_dates=["event_timestamp"])

st.subheader("Funnel summary")
funnel = funnel_summary(events).T.reset_index()
funnel.columns = ["metric", "value"]
funnel["value"] = funnel["value"].map(lambda value: f"{value:.1%}" if isinstance(value, float) and value <= 1 else f"{int(value):,}")
st.dataframe(funnel, use_container_width=True, hide_index=True)

st.subheader("Experiment readout")
experiment = experiment_summary(events)
st.dataframe(experiment, use_container_width=True, hide_index=True)

st.subheader("Event volume")
volume = events["event_name"].value_counts().rename_axis("event_name").reset_index(name="events")
st.bar_chart(volume.set_index("event_name"))

st.info("Interpret metrics using docs/metrics.md. This project uses synthetic data only.")
