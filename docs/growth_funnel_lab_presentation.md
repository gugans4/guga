# Growth Funnel Lab
## Structure and architecture of a Growth analytics portfolio project

---

# 1. The project in one sentence

**Growth Funnel Lab** is a reproducible analytics product for a fictional subscription service.

It connects event data to growth decisions across:

- acquisition quality
- signup-to-activation conversion
- cohort retention
- monetization
- experiment impact

**Portfolio signal:** business framing + data engineering + analytics + decision-making.

---

# 2. The business problem

Growth teams often have many events but no consistent answer to four questions:

1. Where do users drop out of the journey?
2. Which channels bring users who activate and retain?
3. Which cohorts improve or deteriorate over time?
4. What should the team test next?

The project is designed to make the path from **observation → hypothesis → experiment → decision** explicit.

---

# 3. Product journey and event model

```text
Landing view
     ↓
Signup
     ↓
Experiment exposure
     ↓
Activation: first-value action within 24h
     ↓
Login / return activity
     ↓
Subscription
```

Each event carries an anonymous user ID, UTC timestamp, acquisition channel, device, country, optional experiment variant, and optional revenue.

---

# 4. Metric tree

## North-star outcome

Retained activated users.

## Supporting metrics

| Funnel | Retention | Monetization | Experiment |
|---|---|---|---|
| Landing → signup | Day-1 / 7 / 14 / 30 | Revenue per signup | Activation rate |
| Signup → activation | Cohort retention | Revenue per activated user | Absolute lift |
| Activation → subscription | Return activity | First subscription revenue | Relative lift |
| Visitor → paid | Segment retention | Channel revenue | Guardrails |

Metrics are defined before implementation in `docs/metrics.md`.

---

# 5. Repository structure

```text
Growth Funnel Lab/
├── data/raw/              # approved input or generated shareable data
├── data/processed/        # reproducible analytical outputs
├── notebooks/             # exploration and findings
├── src/data/              # loading, simulation, validation
├── src/metrics/           # funnel, cohorts, retention, experiments
├── src/reporting/         # dashboard-ready outputs
├── dashboard/             # Streamlit application
├── tests/                 # metric and data-quality tests
├── docs/                  # metric dictionary and case study
└── .github/workflows/     # automated quality checks
```

The structure separates exploration from reusable production-style logic.

---

# 6. Data-to-decision architecture

```text
Synthetic / approved events
            ↓
   Schema + quality checks
            ↓
  Analytical tables and cohorts
            ↓
       Metrics layer
       ↙            ↘
Dashboard       Experiment readout
       ↘            ↙
       Prioritized experiment backlog
```

The simulator is deterministic and seeded, so another reader can reproduce the same dataset and outputs.

---

# 7. Metric layer and definitions

Every metric documents:

- numerator and denominator
- user-level grain
- attribution window
- cohort rule
- segmentation dimensions
- exclusions and caveats

Example:

```text
signup_to_activation_cvr
= users activated within 24h of signup
  / unique eligible signed-up users
```

Activation is treated as a product-specific first-value event, not an assumed generic action.

---

# 8. Experiment readout

The default experiment tests an onboarding change.

| Component | Definition |
|---|---|
| Primary metric | Activation within 24 hours of signup |
| Unit | User |
| Treatment effect | Absolute and relative lift versus control |
| Guardrails | Early retention, subscription conversion, errors, cancellations |
| Output | Estimate, uncertainty, sample-size caveat, decision |

The final artifact is a decision record: **ship, iterate, or stop**.

---

# 9. Responsible and reproducible data use

This is a public portfolio project. It uses synthetic, anonymized, or explicitly shareable data only.

Quality controls include:

- required-column and type checks
- valid event taxonomy
- chronological journey checks
- duplicate detection
- non-negative revenue validation
- experiment assignment conflict reporting

The repository must never contain customer data, credentials, API keys, or proprietary information.

---

# 10. Roadmap and definition of done

## Roadmap

1. Finalize event and metric dictionaries.
2. Add simulator, validation, and tests.
3. Build funnel and cohort transformations.
4. Add experiment analysis and dashboard.
5. Add CI and a concise case study.

## Definition of done

A new reader can clone the repository, generate approved data, understand the metric definitions, reproduce the main tables, launch the dashboard, and read a recommendation that explains the observation, hypothesis, test, success metric, and limitations.

**Growth Funnel Lab:** from raw events to a defensible growth decision.
