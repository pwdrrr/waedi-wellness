"""Hole den aktuellen Countee-Wert für das Wellness Wädenswil und appende ihn an die CSV.

Läuft als Standalone-Script (z.B. via GitHub Actions Cron). Keine Streamlit-Imports.
"""
import os
import sys
from datetime import datetime

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

URL = "https://www.countee.ch/app/de/counter/view/c5f646119aec21"
DATA_FILE = "wellness_belegung_daten.csv"
MAX_PERSONEN = 10
CSS_SELECTOR = "span.counter-val-themeable"
WAIT_SECONDS = 20


def fetch_free_slots() -> int:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(URL)
        WebDriverWait(driver, WAIT_SECONDS).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, CSS_SELECTOR))
        )
        # Countee rendert den Span sofort, befüllt den Text aber asynchron via JS.
        # Auf den nicht-leeren Text warten.
        WebDriverWait(driver, WAIT_SECONDS).until(
            lambda d: (d.find_element(By.CSS_SELECTOR, CSS_SELECTOR).text or "").strip().isdigit()
        )
        text = driver.find_element(By.CSS_SELECTOR, CSS_SELECTOR).text.strip()
        return int(text)
    finally:
        driver.quit()


def append_row(free_slots: int) -> None:
    free_slots = max(0, min(free_slots, MAX_PERSONEN))
    belegte = MAX_PERSONEN - free_slots
    now = datetime.now()
    row = pd.DataFrame({
        "Datum": [now.strftime("%Y-%m-%d")],
        "Uhrzeit": [now.strftime("%H:%M:%S")],
        "Belegte Plätze": [belegte],
        "Freie Plätze": [free_slots],
    })
    if not os.path.exists(DATA_FILE):
        row.to_csv(DATA_FILE, index=False)
    else:
        row.to_csv(DATA_FILE, mode="a", header=False, index=False)
    print(f"OK: {now.isoformat(timespec='seconds')} → {free_slots} frei / {belegte} belegt")


def main() -> int:
    try:
        free = fetch_free_slots()
    except TimeoutException:
        print("WARN: Timeout beim Laden des Countee-Werts – überspringe diesen Tick.", file=sys.stderr)
        return 0
    except ValueError as e:
        print(f"WARN: Wert nicht parsbar ({e}) – überspringe diesen Tick.", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"ERROR: Unerwarteter Fehler beim Scraping: {e}", file=sys.stderr)
        return 1
    append_row(free)
    return 0


if __name__ == "__main__":
    sys.exit(main())
