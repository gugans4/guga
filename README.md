# Growth Funnel Lab

> An end-to-end portfolio project for turning product and marketing event data into growth decisions.

[![Status: MVP](https://img.shields.io/badge/status-MVP-orange)](#roadmap)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Why this project exists

Growth teams often have plenty of events but no consistent way to answer four basic questions:

1. Where do users drop out of the funnel?
2. Which acquisition channels bring users who actually activate and retain?
3. Which cohorts improve or deteriorate over time?
4. What should the team test next?

**Growth Funnel Lab** is a reproducible analytics workspace that connects those questions in one workflow: data quality checks, funnel analysis, cohort retention, experiment readouts, and a decision-oriented dashboard.

## What it demonstrates

- Defining and documenting a growth metric tree.
- Building a clean event-level data model.
- Measuring conversion between acquisition, activation, and retention stages.
- Comparing cohorts by channel, segment, and signup period.
- Estimating experiment lift with uncertainty instead of reporting only a point estimate.
- Translating analysis into a prioritized experiment backlog.
- Packaging analysis so that another person can reproduce it locally.

## Product questions answered

| Area | Example question |
|---|---|
| Acquisition | Which channels produce the most qualified signups? |
| Activation | What is the largest drop-off before the first value moment? |
| Retention | Which signup cohorts return after 7, 14, and 30 days? |
| Monetization | How do activated users compare with non-activated users on revenue? |
| Experimentation | Did the treatment improve the target metric, and how confident are we? |
| Prioritization | Which next experiment has the strongest expected impact and confidence? |

## Architecture

```text
Raw events → Validation → Analytical tables → Metrics layer → Dashboard
                                      ↘ Experiment readout → Experiment backlog
```

## Repository structure

```text
.
├── data/
│   ├── raw/                 # Input data or documented sample-data instructions
│   └── processed/           # Generated analytical tables; usually gitignored
├── notebooks/               # Exploratory analysis and findings
├── src/
│   ├── data/                # Loading and validation
│   ├── metrics/             # Funnel, cohort, retention, and experiment metrics
│   └── reporting/           # Tables and dashboard-ready outputs
├── dashboard/               # Streamlit application
├── tests/                   # Metric and data-quality tests
├── docs/                    # Metric definitions and decision log
├── requirements.txt
└── README.md
```

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/gugans4/guga.git
cd guga
```

### 2. Create an environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### 3. Prepare the data

Place an approved event export in `data/raw/` and follow the schema described in [`docs/data_dictionary.md`](docs/data_dictionary.md). Do not commit personal, confidential, or production customer data.

### 4. Run validation and analysis

```bash
python -m src.data.validate
python -m src.metrics.build
pytest
```

### 5. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

## Metric definitions

The project uses explicit metric definitions so that the analysis is reproducible. For example, **activation** is not simply “a user opened the product”; it is the documented first-value event selected for the product being analyzed. Full definitions, windows, exclusions, and caveats live in [`docs/metrics.md`](docs/metrics.md).

## Example decision output

The final output is not only a chart. Each analysis should end with a concise decision record:

| Field | Example |
|---|---|
| Observation | Mobile signup-to-activation conversion is lower than desktop |
| Hypothesis | The mobile onboarding flow delays the first value moment |
| Proposed test | Reduce the first-session steps and surface the core action earlier |
| Primary metric | Activation within 24 hours |
| Guardrail metrics | Error rate, day-7 retention, support contacts |
| Decision rule | Ship, iterate, or stop based on the pre-registered rule |

## Roadmap

- [ ] Define the event schema and metric dictionary.
- [ ] Add data validation checks.
- [ ] Implement funnel and cohort metrics.
- [ ] Add retention and experiment analysis.
- [ ] Build the first dashboard view.
- [ ] Add automated tests and GitHub Actions.
- [ ] Publish a short case study with findings and limitations.

## Dashboard deployment

See [`docs/deployment.md`](docs/deployment.md) for local launch instructions and Streamlit Community Cloud deployment settings. The app entrypoint is `dashboard/app.py`.

## Responsible data use

This repository is designed for public portfolio work. Use synthetic, anonymized, or explicitly shareable data only. Never commit API keys, credentials, personally identifiable information, or proprietary company data.

## License

This project is released under the MIT License. See [`LICENSE`](LICENSE).
