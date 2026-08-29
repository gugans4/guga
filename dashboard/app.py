from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.metrics.core import cohort_retention, experiment_summary, funnel_summary, ltv_by_cohort

st.set_page_config(page_title="Growth Funnel Lab", layout="wide")
st.title("Growth Funnel Lab")
st.caption("Decision-oriented funnel, cohort, retention, and LTV analytics")

DATA_PATH = Path("data/raw/events.csv")
if not DATA_PATH.exists():
    st.warning("No dataset found. Run: python -m src.data.simulate_events")
    st.stop()

events = pd.read_csv(DATA_PATH, parse_dates=["event_timestamp"])
events["event_timestamp"] = pd.to_datetime(events["event_timestamp"], utc=True)

funnel_tab, retention_tab, ltv_tab, experiment_tab = st.tabs(["Funnel", "Retention", "LTV", "Experiment"])

with funnel_tab:
    st.subheader("Funnel summary")
    funnel = funnel_summary(events).T.reset_index()
    funnel.columns = ["metric", "value"]
    funnel["value"] = funnel["value"].map(lambda value: f"{value:.1%}" if isinstance(value, float) and value <= 1 else f"{int(value):,}")
    st.dataframe(funnel, use_container_width=True, hide_index=True)

    st.subheader("Event volume")
    volume = events["event_name"].value_counts().rename_axis("event_name").reset_index(name="events")
    st.bar_chart(volume.set_index("event_name"))

with retention_tab:
    st.subheader("Monthly cohort retention")
    retention = cohort_retention(events)
    if retention.empty:
        st.info("Not enough activity data to calculate retention.")
    else:
        max_period = int(retention["period_number"].max())
        period_limit = st.slider("Maximum cohort month", min_value=0, max_value=max_period, value=min(6, max_period))
        filtered = retention.loc[retention["period_number"].le(period_limit)].copy()
        heatmap = filtered.pivot(index="cohort_month", columns="period_number", values="retention_rate")
        heatmap.columns = [f"M{int(column)}" for column in heatmap.columns]
        fig = px.imshow(
            heatmap,
            text_auto=".0%",
            aspect="auto",
            color_continuous_scale="Oranges",
            labels={"x": "Months since signup", "y": "Signup cohort", "color": "Retention"},
        )
        fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

        curve = filtered.groupby("period_number", as_index=False).agg(
            retention_rate=("retention_rate", "mean"),
            cohorts=("cohort_month", "nunique"),
        )
        curve["period"] = curve["period_number"].map(lambda value: f"M{int(value)}")
        curve_fig = px.line(curve, x="period", y="retention_rate", markers=True, labels={"retention_rate": "Average retention"})
        curve_fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(curve_fig, use_container_width=True)
        st.caption("Retention counts unique users with a login or activation event in each calendar month after signup. Cohort sizes and definitions are documented in docs/metrics.md.")

with ltv_tab:
    st.subheader("Cumulative LTV by signup cohort")
    ltv = ltv_by_cohort(events)
    if ltv.empty:
        st.info("No subscription revenue is available for LTV analysis.")
    else:
        ltv["period"] = ltv["period_number"].map(lambda value: f"M{int(value)}")
        ltv_fig = px.line(
            ltv,
            x="period_number",
            y="ltv",
            color="cohort_month",
            markers=True,
            labels={"period_number": "Months since signup", "ltv": "Cumulative LTV", "cohort_month": "Signup cohort"},
        )
        ltv_fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(ltv_fig, use_container_width=True)

        latest = ltv.sort_values("period_number").groupby("cohort_month", as_index=False).tail(1)
        latest = latest[["cohort_month", "cohort_users", "cumulative_revenue", "ltv"]].sort_values("ltv", ascending=False)
        latest.columns = ["cohort", "users", "cumulative_revenue", "latest_ltv"]
        st.dataframe(latest.style.format({"cumulative_revenue": "${:,.2f}", "latest_ltv": "${:,.2f}"}), use_container_width=True, hide_index=True)
        st.caption("LTV is cumulative attributed subscription revenue divided by the number of users in the signup cohort. It is observed LTV, not a forecast.")

with experiment_tab:
    st.subheader("Experiment readout")
    experiment = experiment_summary(events)
    st.dataframe(experiment.style.format({"activation_rate": "{:.1%}"}), use_container_width=True, hide_index=True)
    st.info("Interpret metrics using docs/metrics.md. This project uses synthetic data only.")
