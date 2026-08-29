# Growth Funnel Lab: Anomaly & Reporting Layer

## Cover
Growth Funnel Lab: Anomaly Detection & Reporting
From cohort signals to operational alerts
Manus AI

## Slide 1
Cohort analytics needs an exception layer
- Retention and LTV curves describe the baseline.
- Outliers can indicate tracking breaks, campaign effects, seasonality, or product changes.
- The new layer prioritizes observations without claiming a root cause.

## Slide 2
Robust statistics make anomaly flags explainable
- Peer group: same first-touch channel and months-since-signup period.
- Baseline: peer median.
- Dispersion: median absolute deviation (MAD), with IQR fallback when MAD is zero.
- Flag: cohort size ≥ 30, at least 3 peers, robust score ≥ 3.5.

## Slide 3
The score measures deviation from comparable cohorts
- `score = 0.6745 × |value − peer_median| / MAD`
- `deviation` preserves direction even when the score uses absolute distance.
- `peer_count` and `cohort_users` expose confidence constraints.
- `reason` separates insufficient data from an unusual observation.

## Slide 4
The dashboard shows distribution and context
- Box plots compare score distributions across acquisition channels.
- Scatter points identify individual cohort-period observations.
- Point size reflects cohort users; hover details show baseline, deviation, and reason.
- Reference lines mark detection 3.5 and critical 5.0 thresholds.

## Slide 5
Critical alerts are deliberately harder to trigger
- Critical alert requires an existing anomaly flag.
- Score must be ≥ 5.0.
- Cohort must contain at least 100 users.
- Alert contains only channel, cohort, period, score, and cohort size.

## Slide 6
The metric layer remains the single source of truth
- `src/metrics/anomalies.py` computes scores and critical candidates.
- `dashboard/app.py` visualizes flags and distributions.
- `docs/metrics.md` documents formulas, thresholds, and caveats.
- Tests cover outlier detection and small-sample behavior.

## Slide 7
Reports reuse the same approved tables
- Excel workbook: Funnel, Retention, LTV, Anomalies, Event sample.
- PDF summary: funnel conversion, A/B p-value, lift, and anomaly count.
- Export buttons use the same data and definitions as the dashboard.
- Timezone-aware timestamps are normalized only for Excel compatibility.

## Slide 8
CI turns analysis into a repeatable control loop
- GitHub Actions generates a seeded smoke dataset.
- Tests validate data, metrics, anomaly logic, and export signatures.
- Job Summary receives a compact report for every run.
- Telegram receives a success report when repository secrets are configured.

## Slide 9
Telegram alerts connect detection to action
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` stay in GitHub Secrets.
- Critical anomaly alerts run after successful CI quality checks.
- Missing secrets skip delivery without exposing credentials or failing analytics.
- Delivery is non-blocking so notification outages do not hide code quality results.

## Slide 10
The operating model is signal → investigate → decide
- Signal: robust score and cohort context.
- Investigate: instrumentation, campaigns, seasonality, pricing, and releases.
- Decide: fix data, monitor behavior, or prioritize a growth experiment.
- Next step: add alert deduplication and a historical anomaly registry.
