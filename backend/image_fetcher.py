import os
import requests
import random
from chatgpt_api import get_chatgpt_response as generate_content

UNSPLASH_KEY = os.getenv("UNSPLASH_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY")

def fetch_image_url(query):
    # 1. Try Unsplash
    if UNSPLASH_KEY:
        try:
            headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
            r = requests.get("https://api.unsplash.com/search/photos", params={"query": query, "per_page": 5}, headers=headers, timeout=10)
            if r.status_code == 200 and r.json().get("results"):
                return random.choice(r.json()["results"])["urls"]["regular"]
        except Exception as e:
            print("Unsplash error:", e)

    # 2. Try Pexels
    if PEXELS_KEY:
        try:
            headers = {"Authorization": PEXELS_KEY}
            r = requests.get("https://api.pexels.com/v1/search", params={"query": query, "per_page": 5}, headers=headers, timeout=10)
            if r.status_code == 200 and r.json().get("photos"):
                return random.choice(r.json()["photos"])["src"]["medium"]
        except Exception as e:
            print("Pexels error:", e)

    return None

def fetch_image_for_paragraph(paragraph):
    """
    Generate an SEO-friendly image search query for the paragraph and fetch a matching image.
    """
    try:
        query_prompt = f"Summarize this paragraph into an image search query: {paragraph}"
        image_query = generate_content(query_prompt).strip()
        return fetch_image_url(image_query)
    except Exception as e:
        print("Error generating image for paragraph:", e)
        return None
