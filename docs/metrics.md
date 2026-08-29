# Growth Funnel Lab — metric dictionary

This document defines the metrics used in the project. Definitions must be reviewed before changing the event schema or analytical SQL/Python code.

## 1. Analytical grain and identity

The raw table has **one row per user event**. `user_id` is an anonymous identifier. A user can generate multiple events, but a metric counts a user at most once within its stated window unless explicitly described as a count metric.

All timestamps are stored in UTC. Dates used for cohorting are derived from the first qualifying `signup` event, not from an arbitrary event.

## 2. Event taxonomy

| Event | Meaning | Required fields | Funnel stage |
|---|---|---|---|
| `landing_view` | A user views the acquisition landing page | `user_id`, `event_timestamp`, `channel` | Acquisition |
| `signup` | A user completes account creation | `user_id`, `event_timestamp`, `channel`, `device_type` | Acquisition |
| `activation` | A user completes the product's first-value action | `user_id`, `event_timestamp` | Activation |
| `subscription` | A user starts a paid subscription | `user_id`, `event_timestamp`, `revenue` | Monetization |
| `login` | A user returns and authenticates | `user_id`, `event_timestamp` | Retention |
| `experiment_exposure` | A user is assigned and exposed to a variant | `user_id`, `event_timestamp`, `experiment_variant` | Experimentation |

**Activation rule:** for this fictional subscription product, activation means completing the first-value action within 24 hours after signup. The action itself should be named in the product case study before the project is presented publicly.

## 3. Core dimensions

| Dimension | Definition | Allowed/default values |
|---|---|---|
| `channel` | First-touch acquisition channel attached to the user's signup | `organic`, `paid_search`, `paid_social`, `referral`, `email` |
| `device_type` | Device category at signup | `desktop`, `mobile`, `tablet` |
| `country` | Coarse country segment, not precise location | `US`, `GB`, `DE`, `CA`, `AU`, `OTHER` |
| `experiment_variant` | Variant assigned for a named experiment | `control`, `treatment`, or null |
| `signup_date` | Calendar date of the first signup event | UTC date |
| `signup_cohort` | Month of `signup_date` | `YYYY-MM` |

## 4. Funnel metrics

### 4.1 Landing-to-signup conversion

**Definition:** the share of unique users with at least one `landing_view` who later complete a `signup` within the attribution window.

```text
landing_to_signup_cvr = users_with_signup_after_landing / unique_users_with_landing_view
```

**Default attribution window:** 7 calendar days from the first landing view. Count each user once. Exclude signups that precede the first landing view.

### 4.2 Signup-to-activation conversion

**Definition:** the share of unique signed-up users who complete `activation` within 24 hours of their first signup.

```text
signup_to_activation_cvr = activated_signed_up_users / unique_signed_up_users
```

The denominator is all eligible signups in the reporting period. Users without an activation event remain in the denominator.

### 4.3 Activation-to-subscription conversion

**Definition:** the share of activated users who complete their first `subscription` within 30 days of activation.

```text
activation_to_subscription_cvr = subscribed_activated_users / unique_activated_users
```

### 4.4 End-to-end visitor-to-paid conversion

**Definition:** the share of unique users with a first `landing_view` who complete a first subscription within 37 days of that view. The 37-day window combines the 7-day acquisition window and 30-day post-activation window for this project’s simplified model.

## 5. Retention metrics

### 5.1 Cohort assignment

A user belongs to the cohort corresponding to the UTC calendar month of their first `signup` event. Users without signup are excluded from signup-cohort retention.

### 5.2 Return retention

For a signup cohort, **day-N retention** is the share of users with at least one qualifying `login` or `activation` event on calendar day N after signup.

```text
day_n_retention = cohort_users_active_on_day_n / cohort_users
```

Use a consistent calendar-day convention. A user is counted once on a day. Report cohort size beside every retention percentage.

### 5.3 Paid retention

Paid retention is the share of users with a first subscription who still have an active subscription at the end of the stated observation period. The MVP may defer this metric if cancellation events are not in the schema; it must not infer active status from revenue alone.

## 6. Revenue metrics

### 6.1 Revenue per signup

```text
revenue_per_signup = total_attributed_revenue / unique_signed_up_users
```

Revenue must be attributed once to the first subscription event unless the project explicitly adds recurring billing events.

### 6.2 Revenue per activated user

```text
revenue_per_activated_user = total_attributed_revenue / unique_activated_users
```

Report the denominator and the attribution window with the metric.

## 7. Experiment metrics

### 7.1 Primary metric

The default primary metric is **activation within 24 hours of signup**. The unit of analysis is the user, and each user contributes one binary outcome.

```text
activation_rate_variant = activated_users_variant / eligible_exposed_users_variant
lift = activation_rate_treatment - activation_rate_control
relative_lift = lift / activation_rate_control
```

### 7.2 Guardrails

Track early retention, error rate, subscription conversion, cancellation/refund rate, and support contacts when available. A treatment should not be recommended solely because the primary metric improved if a guardrail materially worsened.

### 7.3 Experiment exclusions

Exclude users who were not exposed to a variant, users with conflicting variant assignments, duplicate assignment records, and events occurring before exposure when the experiment requires post-exposure measurement. Document any sample-ratio mismatch or missingness.

### 7.4 Decision record

Every experiment readout must state:

| Field | Required content |
|---|---|
| Observation | What changed in the measured data |
| Hypothesis | Why the change may have happened |
| Primary metric | Predefined success metric |
| Guardrails | Metrics that prevent harmful optimization |
| Estimate | Absolute lift and relative lift |
| Uncertainty | Interval or explicit sample-size limitation |
| Decision | Ship, iterate, or stop |
| Caveats | Data quality, attribution, or design limitations |

## 8. Segmentation and attribution rules

Metrics may be segmented by first-touch channel, device type, country, signup cohort, and experiment variant. Segments with fewer than 30 eligible users should be flagged as low sample size rather than presented as stable conclusions.

Channel is first-touch for the MVP. Do not compare first-touch and last-touch results in the same chart without clearly labeling the attribution model.

## 9. Data-quality rules

The validation layer should check that:

1. Required columns are present and have expected types.
2. `user_id` and `event_name` are not null.
3. Event names belong to the documented taxonomy.
4. Timestamps parse as UTC and are not in the future relative to the simulation run date.
5. A user does not have activation before signup, or subscription before activation, unless an explicit exception is documented.
6. Experiment variants are valid and assignment conflicts are reported.
7. Revenue is non-negative and null for non-revenue events.
8. Duplicate event rows are detected and either removed or reported.

## 10. Interpretation caveats

These metrics describe associations in an observational funnel unless the experiment design supports a causal interpretation. Channel conversion differences may reflect audience mix, targeting, seasonality, or selection bias. Retention is sensitive to the activity definition and observation window. Small segment results are directional and should inform further investigation, not be treated as final business truth.

## 11. Advanced cohort retention

The dashboard uses signup-month cohorts. Each user is assigned to the month of their first signup. For each subsequent calendar month, a user is retained if they generate at least one `login` or `activation` event. The result includes cohort size, retained users, period number (`M0`, `M1`, `M2`, ...), and retention rate.

```text
monthly_retention(cohort, period)
= unique active users from cohort in period
  / all unique users in the cohort
```

`M0` is the signup month. Partial recent cohorts must be labeled as incomplete because they have had less time to mature. The dashboard presents cohort sizes alongside percentages where possible.

## 12. Observed LTV

For the MVP, LTV is **observed cumulative revenue per signup-cohort user**. It is not a predictive or discounted cash-flow forecast.

```text
observed_ltv(cohort, period)
= cumulative attributed subscription revenue through period
  / unique users in the signup cohort
```

Revenue is attributed to subscription events. The dashboard plots cumulative LTV by signup cohort and months since signup. Cohorts with incomplete observation windows should not be compared to mature cohorts without an explicit caveat.

## 13. Statistical significance for A/B activation tests

The dashboard compares binary 24-hour activation outcomes between independent control and treatment users with a two-sided two-sample z-test for proportions. The null hypothesis is that the activation rates are equal.

The readout reports:

| Output | Definition |
|---|---|
| `p_value` | Probability of observing a result at least this extreme under the equality null hypothesis |
| `z_statistic` | Standardized difference between treatment and control rates |
| `absolute_lift` | Treatment activation rate minus control activation rate |
| `relative_lift` | Absolute lift divided by control activation rate |
| `ci_low`, `ci_high` | Approximate 95% confidence interval for treatment minus control |
| `significant` | Whether `p_value < alpha`, with default `alpha = 0.05` |

A low p-value does not prove that the treatment is practically valuable, and it is not the probability that the hypothesis is true. Interpret it with effect size, confidence interval, sample size, experiment design, and guardrails. The normal approximation may be weak for very small groups or sparse outcomes; such cases should be flagged for a more exact or Bayesian analysis.

## 14. Channel-segmented cohorts

The dashboard segments cohorts by `signup_channel`, which is the user's first-touch acquisition channel attached to the first signup. A channel cohort is the intersection of `signup_channel` and `cohort_month`.

Channel retention uses:

```text
channel_cohort_retention
= active unique users for channel + cohort + period
  / all signed-up users for channel + cohort
```

Channel LTV uses:

```text
channel_cohort_ltv
= cumulative subscription revenue for channel + cohort + period
  / all signed-up users for channel + cohort
```

The dashboard exposes a channel selector and shows cohort size in the detail table. Channel cohorts with fewer than 30 eligible users are directional and should not be used as stable performance rankings.

## 15. Cohort anomaly detection

The dashboard uses an explainable robust-statistics check rather than an opaque ML model. For each comparable peer group—by `signup_channel` and `period_number`—it calculates the peer median and median absolute deviation (MAD). An anomaly is flagged when the cohort has at least 30 users, at least 3 comparable peers, and a robust score of at least 3.5. If MAD is zero, the detector falls back to the 1.5 × IQR fence.

An anomaly flag is a prioritization signal, not a diagnosis. Investigate tracking changes, sample-size effects, campaigns, seasonality, pricing, and product releases before assigning a business cause. Recent or small cohorts should remain directional.

## 16. Report exports

The dashboard exports the same approved analytical tables used on screen. Excel contains `Funnel`, `Retention`, `LTV`, `Anomalies`, and `Event sample` sheets. PDF contains a compact funnel and experiment summary plus the number of anomaly flags. Timestamps are converted to timezone-naive UTC values only for Excel compatibility; source event timestamps remain UTC in the CSV schema.

## 17. Anomaly score distribution and critical alerts

The dashboard visualizes robust anomaly scores by acquisition channel and cohort-period. Box plots show the distribution by channel, while a cohort scatter plot exposes individual outliers. Horizontal reference lines mark the detection threshold (3.5) and critical alert threshold (5.0).

A Telegram alert is eligible only when an observation is already flagged as anomalous, has a robust score of at least 5.0, and represents at least 100 cohort users. Alerts contain only channel, cohort, period, score, and cohort size; they do not include raw event rows. Delivery is skipped when Telegram secrets are absent and is non-blocking for the analytics CI job.
