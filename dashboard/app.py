from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.metrics.ab_testing import activation_experiment_from_events
from src.metrics.anomalies import critical_anomalies, detect_cohort_anomalies
from src.metrics.channel_cohorts import cohort_retention_by_channel, ltv_by_channel
from src.metrics.core import cohort_retention, funnel_summary, ltv_by_cohort
from src.reporting.exports import build_excel_report, build_pdf_report

st.set_page_config(page_title="Growth Funnel Lab", layout="wide")
st.title("Growth Funnel Lab")
st.caption("Decision-oriented funnel, cohort, retention, LTV, anomaly, and experiment analytics")

DATA_PATH = Path("data/raw/events.csv")
if not DATA_PATH.exists():
    st.warning("No dataset found. Run: python -m src.data.simulate_events")
    st.stop()

events = pd.read_csv(DATA_PATH, parse_dates=["event_timestamp"])
events["event_timestamp"] = pd.to_datetime(events["event_timestamp"], utc=True)
channels = sorted(events["channel"].dropna().unique().tolist())
funnel_raw = funnel_summary(events)
retention = cohort_retention(events)
channel_retention = cohort_retention_by_channel(events)
ltv = ltv_by_cohort(events)
channel_ltv = ltv_by_channel(events)
anomalies = detect_cohort_anomalies(channel_retention) if not channel_retention.empty else pd.DataFrame()
critical = critical_anomalies(anomalies) if not anomalies.empty else pd.DataFrame()
ab_result = activation_experiment_from_events(events)

excel_bytes = build_excel_report(events, funnel_raw, channel_retention, channel_ltv, anomalies)
pdf_bytes = build_pdf_report(funnel_raw, ab_result, anomalies)
export_col1, export_col2 = st.columns(2)
with export_col1:
    st.download_button("Download Excel report", data=excel_bytes, file_name="growth_funnel_lab_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
with export_col2:
    st.download_button("Download PDF summary", data=pdf_bytes, file_name="growth_funnel_lab_report.pdf", mime="application/pdf", use_container_width=True)

funnel_tab, retention_tab, ltv_tab, experiment_tab = st.tabs(["Funnel", "Retention", "LTV", "Experiment"])

with funnel_tab:
    st.subheader("Funnel summary")
    funnel = funnel_raw.T.reset_index()
    funnel.columns = ["metric", "value"]
    funnel["value"] = funnel["value"].map(lambda value: f"{value:.1%}" if isinstance(value, float) and value <= 1 else f"{int(value):,}")
    st.dataframe(funnel, use_container_width=True, hide_index=True)

    st.subheader("Event volume")
    volume = events["event_name"].value_counts().rename_axis("event_name").reset_index(name="events")
    st.bar_chart(volume.set_index("event_name"))

with retention_tab:
    st.subheader("Monthly cohort retention")
    if retention.empty:
        st.info("Not enough activity data to calculate retention.")
    else:
        max_period = int(retention["period_number"].max())
        period_limit = st.slider("Maximum cohort month", min_value=0, max_value=max_period, value=min(6, max_period))
        filtered = retention.loc[retention["period_number"].le(period_limit)].copy()
        heatmap = filtered.pivot(index="cohort_month", columns="period_number", values="retention_rate")
        heatmap.columns = [f"M{int(column)}" for column in heatmap.columns]
        fig = px.imshow(heatmap, text_auto=".0%", aspect="auto", color_continuous_scale="Oranges", labels={"x": "Months since signup", "y": "Signup cohort", "color": "Retention"})
        fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

        curve = filtered.groupby("period_number", as_index=False).agg(retention_rate=("retention_rate", "mean"), cohorts=("cohort_month", "nunique"))
        curve["period"] = curve["period_number"].map(lambda value: f"M{int(value)}")
        curve_fig = px.line(curve, x="period", y="retention_rate", markers=True, labels={"retention_rate": "Average retention"})
        curve_fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(curve_fig, use_container_width=True)
        st.caption("Retention counts unique users with a login or activation event in each calendar month after signup.")

    st.subheader("Retention by acquisition channel")
    if channel_retention.empty:
        st.info("Not enough data for channel cohorts.")
    else:
        selected_channel = st.selectbox("First-touch channel", ["All channels"] + channels, key="retention_channel")
        channel_view = channel_retention if selected_channel == "All channels" else channel_retention[channel_retention["signup_channel"].eq(selected_channel)]
        channel_period_limit = int(channel_view["period_number"].max())
        channel_period = st.slider("Channel cohort month", 0, channel_period_limit, min(3, channel_period_limit), key="channel_retention_period")
        channel_view = channel_view[channel_view["period_number"].le(channel_period)].copy()
        channel_fig = px.line(channel_view, x="period_number", y="retention_rate", color="signup_channel", line_dash="cohort_month", markers=True, labels={"period_number": "Months since signup", "retention_rate": "Retention", "signup_channel": "Channel", "cohort_month": "Cohort"})
        channel_fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(channel_fig, use_container_width=True)
        st.dataframe(channel_view[["signup_channel", "cohort_month", "period_number", "retained_users", "cohort_users", "retention_rate"]].style.format({"retention_rate": "{:.1%}"}), use_container_width=True, hide_index=True)
        st.caption("Channel is first-touch at signup. Small cohorts should be treated as directional.")

    st.subheader("Cohort anomaly flags")
    anomaly_view = anomalies.loc[anomalies["is_anomaly"]].copy() if not anomalies.empty else pd.DataFrame()
    if anomaly_view.empty:
        st.success("No robust-statistical cohort anomalies detected with the current thresholds.")
    else:
        st.warning(f"{len(anomaly_view)} cohort-period anomalies detected. Investigate data quality and product changes before assigning a cause.")
        st.dataframe(anomaly_view, use_container_width=True, hide_index=True)

    st.subheader("Anomaly score distribution by cohort")
    if anomalies.empty:
        st.info("No anomaly score distribution is available.")
    else:
        score_view = anomalies.copy()
        score_view["cohort_label"] = score_view["signup_channel"] + " · " + score_view["cohort_month"] + " · M" + score_view["period_number"].astype(int).astype(str)
        score_view["status"] = score_view["is_anomaly"].map({True: "Flagged", False: "Within range"})
        distribution = px.box(score_view, x="signup_channel", y="anomaly_score", color="status", points="all", hover_data=["cohort_month", "period_number", "cohort_users", "peer_median", "deviation", "reason"], labels={"signup_channel": "Acquisition channel", "anomaly_score": "Robust anomaly score", "status": "Status"})
        distribution.add_hline(y=3.5, line_dash="dash", line_color="#EA580C", annotation_text="Flag threshold 3.5")
        distribution.add_hline(y=5.0, line_dash="dot", line_color="#991B1B", annotation_text="Critical threshold 5.0")
        distribution.update_layout(margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(distribution, use_container_width=True)
        scatter = px.scatter(score_view, x="cohort_month", y="anomaly_score", color="signup_channel", symbol="status", size="cohort_users", hover_data=["period_number", "retention_rate", "peer_median", "deviation", "reason"], labels={"cohort_month": "Signup cohort", "anomaly_score": "Robust anomaly score"})
        scatter.add_hline(y=3.5, line_dash="dash", line_color="#EA580C")
        scatter.add_hline(y=5.0, line_dash="dot", line_color="#991B1B")
        st.plotly_chart(scatter, use_container_width=True)
        st.caption(f"{len(critical)} critical alert-eligible anomalies currently meet score ≥ 5.0 and cohort size ≥ 100.")

with ltv_tab:
    st.subheader("Cumulative LTV by signup cohort")
    if ltv.empty:
        st.info("No subscription revenue is available for LTV analysis.")
    else:
        ltv_fig = px.line(ltv, x="period_number", y="ltv", color="cohort_month", markers=True, labels={"period_number": "Months since signup", "ltv": "Cumulative LTV", "cohort_month": "Signup cohort"})
        ltv_fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(ltv_fig, use_container_width=True)
        latest = ltv.sort_values("period_number").groupby("cohort_month", as_index=False).tail(1)
        latest = latest[["cohort_month", "cohort_users", "cumulative_revenue", "ltv"]].sort_values("ltv", ascending=False)
        latest.columns = ["cohort", "users", "cumulative_revenue", "latest_ltv"]
        st.dataframe(latest.style.format({"cumulative_revenue": "${:,.2f}", "latest_ltv": "${:,.2f}"}), use_container_width=True, hide_index=True)

    st.subheader("Observed LTV by acquisition channel")
    if channel_ltv.empty:
        st.info("No subscription revenue is available for channel LTV analysis.")
    else:
        ltv_channel = st.selectbox("LTV channel view", ["All channels"] + channels, key="ltv_channel")
        ltv_channel_view = channel_ltv if ltv_channel == "All channels" else channel_ltv[channel_ltv["signup_channel"].eq(ltv_channel)]
        ltv_channel_fig = px.line(ltv_channel_view, x="period_number", y="ltv", color="signup_channel", line_dash="cohort_month", markers=True, labels={"period_number": "Months since signup", "ltv": "Observed cumulative LTV", "signup_channel": "Channel"})
        ltv_channel_fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(ltv_channel_fig, use_container_width=True)
        st.caption("Observed cumulative revenue per signup-cohort user, segmented by first-touch channel. This is not a forecast.")

with experiment_tab:
    st.subheader("Experiment readout")
    summary = pd.DataFrame([ab_result])
    st.metric("p-value", f"{ab_result['p_value']:.4f}", help="Two-sided test of equal activation rates.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Absolute lift", f"{ab_result['absolute_lift']:.1%}")
    col2.metric("Relative lift", f"{ab_result['relative_lift']:.1%}")
    col3.metric("Decision", ab_result["decision"])
    st.dataframe(summary[["control_users", "control_successes", "control_rate", "treatment_users", "treatment_successes", "treatment_rate", "z_statistic", "p_value", "ci_low", "ci_high", "significant"]].style.format({"control_rate": "{:.1%}", "treatment_rate": "{:.1%}", "p_value": "{:.4f}", "ci_low": "{:.1%}", "ci_high": "{:.1%}", "z_statistic": "{:.2f}"}), use_container_width=True, hide_index=True)
    st.caption("The test compares 24-hour activation for independent control and treatment users. Interpret p-value together with effect size, confidence interval, sample size, and guardrails.")
