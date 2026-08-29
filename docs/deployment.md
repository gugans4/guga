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

## Telegram CI reports

The CI workflow can send a compact report after a successful quality run through the Telegram Bot API `sendMessage` method. The workflow never stores credentials in the repository and skips the notification step when either secret is absent.

Create a Telegram bot with BotFather, add it to the destination chat, and obtain the destination `chat_id`. In GitHub, open **Settings → Secrets and variables → Actions → New repository secret** and create:

| Secret | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | The bot token from BotFather |
| `TELEGRAM_CHAT_ID` | The destination user, group, or channel chat ID |

The notification step sends only the synthetic-data CI summary and does not include credentials or raw event rows. It uses `continue-on-error: true`, so an unavailable Telegram endpoint does not turn a successful analytics test into a failed build. Repository secrets should be passed to workflows through `${{ secrets.NAME }}` rather than hard-coded [1] [2].

This repository currently notifies successful **GitHub Actions CI runs**. Streamlit Community Cloud deployment happens outside GitHub Actions, so a GitHub workflow cannot automatically observe its deployment status unless a separate deployment workflow or webhook integration is introduced. The same Telegram step can be reused in a future deploy workflow after the deploy command reports success.

### References

[1]: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions "GitHub Actions: Using secrets"
[2]: https://core.telegram.org/bots/api "Telegram Bot API"
