"""Hole den aktuellen Belegungs-Wert für das Wellness Wädenswil via Countee API.

Vorher: Selenium + Headless Chrome → fragil, weil Countee-CSS-Klassen gehashed sind.
Jetzt: direkter JSON-API-Call. Robust, schnell, ohne Browser.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

import pandas as pd

API_URL = "https://www.startupuniverse.ch/api/1.1/de/counters/get/c5f646119aec21"
DATA_FILE = "wellness_belegung_daten.csv"
MAX_PERSONEN_FALLBACK = 10
TIMEOUT = 20


def fetch_counter() -> dict:
    req = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": "waedi-wellness-scraper/2.0 (+https://github.com/pwdrrr/waedi-wellness)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.load(resp)


def append_row(freie_plaetze: int, max_p: int) -> None:
    freie_plaetze = max(0, min(freie_plaetze, max_p))
    belegte = max_p - freie_plaetze
    now = datetime.now()
    row = pd.DataFrame({
        "Datum": [now.strftime("%Y-%m-%d")],
        "Uhrzeit": [now.strftime("%H:%M:%S")],
        "Belegte Plätze": [belegte],
        "Freie Plätze": [freie_plaetze],
    })
    if not os.path.exists(DATA_FILE):
        row.to_csv(DATA_FILE, index=False)
    else:
        row.to_csv(DATA_FILE, mode="a", header=False, index=False)
    print(f"OK: {now.isoformat(timespec='seconds')} → {freie_plaetze} frei / {belegte} belegt (max {max_p})")


def main() -> int:
    try:
        data = fetch_counter()
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"WARN: API-Call fehlgeschlagen ({e}) – überspringe diesen Tick.", file=sys.stderr)
        return 0
    except json.JSONDecodeError as e:
        print(f"ERROR: API lieferte kein JSON: {e}", file=sys.stderr)
        return 1

    try:
        d = data["response"]["data"]
        closed = int(d.get("closed", 0))
        max_p = int(d.get("max", MAX_PERSONEN_FALLBACK))
        items = d.get("counteritems", [])
    except (KeyError, TypeError, ValueError) as e:
        print(f"ERROR: Unerwartete API-Struktur: {e}\nRaw: {data!r}", file=sys.stderr)
        return 1

    if closed:
        print("INFO: Wellness ist geschlossen – kein Eintrag.")
        return 0
    if not items:
        print("WARN: Offen, aber keine counteritems – überspringe.", file=sys.stderr)
        return 0

    try:
        val = int(items[0]["val"])
    except (KeyError, TypeError, ValueError) as e:
        print(f"ERROR: counteritems[0].val nicht parsbar: {e}", file=sys.stderr)
        return 1

    # mode_display = "available" → val ist die Zahl der freien Plätze.
    append_row(val, max_p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
