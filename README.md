# Wellness Wädenswil – Auslastung

Automatischer Scraper + Streamlit-Dashboard für die Countee-Auslastungszahl.

## Architektur

- `scraper.py` – Standalone-Selenium-Script, holt aktuellen Countee-Wert und appendet ihn an `wellness_belegung_daten.csv`.
- `.github/workflows/scrape.yml` – GitHub-Actions-Cron läuft alle 15 Min (06–20 UTC) und committet die CSV.
- `wellness.py` – Streamlit-Dashboard. Liest die CSV direkt aus dem Repo. Hosting via Streamlit Community Cloud.

## Deploy

1. Repo ist auf GitHub als private Repo gepusht.
2. Streamlit Cloud → https://share.streamlit.io → "New app" → Repo wählen → Main-File `wellness.py` → Deploy.
3. Erste Action manuell triggern unter Actions → "Scrape Wellness" → "Run workflow".

## Lokal laufen lassen

```bash
pip install -r requirements.txt
streamlit run wellness.py

# oder den Scraper einmalig:
pip install -r requirements-scraper.txt
python scraper.py
```
