# Streamlit deployment notes

The official Streamlit documentation states that a local app can be started with `streamlit run your_script.py` or `python -m streamlit run your_script.py`. The Community Cloud workflow connects to GitHub, lets the user choose a repository, branch, and app entrypoint, and handles containerization. Python dependencies should be declared in one dependency file; this project uses the root `requirements.txt`. The deployed Python version should match the development version.

References:

- https://docs.streamlit.io/develop/concepts/architecture/run-your-app
- https://docs.streamlit.io/deploy/streamlit-community-cloud
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
