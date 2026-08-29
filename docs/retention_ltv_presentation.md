# Retention & LTV Architecture
## Advanced cohort analytics in Growth Funnel Lab

---

# 1. Why cohort analytics?

Aggregate metrics hide the truth. Growth Funnel Lab uses **signup-month cohorts** to answer:

- Are newer cohorts better than older ones?
- When exactly do users drop out?
- How much value does a user bring over time?

**Goal:** move from "how many users" to "how much value per cohort".

---

# 2. Retention definition

**Monthly Cohort Retention** measures the share of users who return after their signup month.

- **Cohort:** users who signed up in the same UTC calendar month.
- **Activity:** at least one `login` or `activation` event in a subsequent month.
- **Metric:** `retained_users / cohort_users`.

Definitions are formally documented in `docs/metrics.md`.

---

# 3. LTV definition

**Observed Cumulative LTV** is the total attributed revenue divided by the cohort size.

- **Attribution:** revenue from `subscription` events.
- **Cumulative:** revenue sums up as the cohort matures.
- **Observed:** it is a historical measure, not a predictive forecast.

Formula: `cumulative_revenue(cohort, period) / cohort_users`.

---

# 4. Data flow for cohorts

```text
Event Stream (CSV)
      ↓
Signup Time Extraction
      ↓
Monthly Cohort Assignment
      ↓
Activity/Revenue Join
      ↓
Period Calculation (M0, M1, M2...)
      ↓
Aggregation & Normalization
```

The logic is encapsulated in `src/metrics/core.py` for reproducibility.

---

# 5. Retention Heatmap architecture

The dashboard transforms long-format cohort data into a **pivot table**.

- **Rows:** Signup cohorts (YYYY-MM).
- **Columns:** Months since signup (M0, M1...).
- **Values:** Retention rate (%).

This visualization highlights "leakage" points in the user journey.

---

# 6. LTV Curve architecture

LTV curves compare the **compounding value** of different cohorts.

- **X-axis:** Months since signup.
- **Y-axis:** Cumulative LTV ($).
- **Lines:** One curve per signup cohort.

Steeper curves indicate faster monetization or higher price points.

---

# 7. Handling incomplete cohorts

Recent cohorts have less observation time.

- **M0** is always available for a new cohort.
- **M3** is only available for cohorts at least 3 months old.

The dashboard uses filtering and clear labeling to prevent misleading comparisons between mature and "young" cohorts.

---

# 8. Integration with Metric Layer

Retention and LTV are first-class citizens in the project's **Metric Layer**.

- **core.py:** implements `cohort_retention()` and `ltv_by_cohort()`.
- **test_simulate_events.py:** verifies that rates are between 0-1 and LTV is cumulative.
- **metrics.md:** serves as the single source of truth for definitions.

---

# 9. Business application

How to use these insights:

1. **Identify drop-offs:** if M1 retention is low, focus on onboarding.
2. **Channel quality:** compare LTV by acquisition source (planned update).
3. **Payback period:** compare LTV to acquisition cost (CAC).

**Decision:** Prioritize growth efforts where the LTV/Retention gap is largest.

---

# 10. Summary and roadmap

## Summary
Growth Funnel Lab provides a reproducible framework for measuring user value over time through formal cohort definitions.

## Roadmap
- Add LTV by acquisition channel.
- Add predictive LTV modeling.
- Add churn event handling.
- Integrate A/B significance into cohort views.
