# Wellness Wädenswil – Auslastung

Vollautomatisches Dashboard für die Countee-Auslastungszahl.

## Architektur

| Komponente | Wo | Wofür |
|---|---|---|
| `scraper.py` | GitHub Actions | Holt alle 15 Min den aktuellen Countee-Wert (headless Chrome) |
| `.github/workflows/scrape.yml` | GitHub Actions | Cron `*/15 6-20 * * *` UTC, committet die CSV ins Repo |
| `wellness_belegung_daten.csv` | Repo-Root | Persistenter Speicher (Bot-committed) |
| `index.html` | Netlify (static) | Lädt CSV via `fetch` von `raw.githubusercontent.com`, rendert Plotly.js clientside |
| `netlify.toml` | Repo-Root | Skippt Netlify-Build bei CSV-Only-Commits (spart Free-Tier-Minuten) |

## Vorteile

- **Keine laufenden Prozesse** – Scraping nur 15× pro Stunde via Actions, Dashboard ist statisches HTML.
- **Daten frisch** – Browser fetcht CSV bei jedem Page-Load direkt von GitHub.
- **Keine manuelle Arbeit** – Bot scrapt, committet, Netlify hostet ewig dieselbe HTML.

## Lokal scraper-testen

```bash
pip install -r requirements-scraper.txt
python scraper.py
```

## Lokal Dashboard ansehen

```bash
python -m http.server 8000
# → http://localhost:8000
```
