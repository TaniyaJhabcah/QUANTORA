# QUANTORA — Financial Intelligence

A Streamlit application for cleaning an uploaded UrbanKart sales CSV and presenting five business intelligence views.

## Files
- `app.py` — Streamlit user interface and visualizations
- `urbankart_engine.py` — CSV cleaning and business calculations
- `requirements.txt` — Python dependencies
- `prompts.txt` — AI assistance disclosure and ChatGPT share-link location

## Run locally

1. Open Terminal in this folder.
2. (Recommended) Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
4. Start the app:
   ```bash
   python3 -m streamlit run app.py
   ```
5. Upload the CSV using the sidebar uploader.

Before submission, replace the first line of `prompts.txt` with your actual ChatGPT share link.
