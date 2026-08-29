# Dashboard deployment

## Run locally

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.data.simulate_events --users 5000 --days 90 --seed 42 --output data/raw/events.csv
python -m streamlit run dashboard/app.py
```

Streamlit will start a local server and normally open the app in a browser. If it does not open automatically, visit `http://localhost:8501`.

To use another port:

```bash
python -m streamlit run dashboard/app.py --server.port 8502
```

The dashboard reads `data/raw/events.csv`. Regenerate it whenever you want a new deterministic dataset by changing `--seed` or the other simulator arguments.

## Deploy to Streamlit Community Cloud

1. Push the repository to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub.
3. Choose **Create app**.
4. Select repository `gugans4/guga`, branch `main`, and file path `dashboard/app.py`.
5. Select Python 3.11 if the deployment settings expose a Python-version selector.
6. Click **Deploy** and open the generated app URL.

The repository already includes a root `requirements.txt`, which declares the Python dependencies. Community Cloud should therefore install the environment before starting the app. If deployment fails, inspect the app logs first; dependency resolution and Python-version mismatches are common causes.

## Notes for this project

The app is public and uses synthetic data only. Do not add production exports, secrets, API keys, or personally identifiable information to the repository. If external credentials are ever needed, use Community Cloud secrets rather than committing them to Git.

## Official references

- [Run your Streamlit app](https://docs.streamlit.io/develop/concepts/architecture/run-your-app)
- [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [App dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
