# app/scraper.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()  # ✅ make .env values available here too

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def scrape_google_results(keyword, num_results=10):
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        raise RuntimeError(
            "Missing GOOGLE_API_KEY or GOOGLE_CSE_ID. "
            "Set them in your environment or .env file."
        )

    url = "https://www.googleapis.com/customsearch/v1"
    params = {"q": keyword, "key": GOOGLE_API_KEY, "cx": GOOGLE_CSE_ID, "num": num_results}
    res = requests.get(url, params=params, timeout=15)

    # Helpful error if Google responds with 4xx/5xx
    try:
        res.raise_for_status()
    except requests.HTTPError:
        try:
            details = res.json()
        except Exception:
            details = res.text
        raise RuntimeError(f"Google CSE error {res.status_code}: {details}")

    data = res.json()
    results = [(item.get("title","No title"), item.get("link","")) for item in data.get("items",[])]
    return results
