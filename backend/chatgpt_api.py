# backend/chatgpt_api.py
from openai import OpenAI
import os
from dotenv import load_dotenv
from pathlib import Path

_client = None

def _get_client():
    global _client
    if _client is None:
        # Load .env explicitly from project root (adjust if needed)
        root_env = Path(__file__).resolve().parents[1] / ".env"
        load_dotenv(dotenv_path=root_env)  # still OK if file not found

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY. Put it in your .env or OS env.")
        _client = OpenAI(api_key=api_key)
    return _client

def get_chatgpt_response(prompt: str) -> str:
    client = _get_client()
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content
