import os
import time
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_URL = "https://backend.blotato.com/v2"
VALID_PLATFORMS = [
    "twitter", "linkedin", "facebook", "instagram",
    "pinterest", "tiktok", "threads", "bluesky", "youtube",
]


def _api_key():
    key = os.environ.get("BLOTATO_API_KEY")
    if not key:
        raise RuntimeError(
            "BLOTATO_API_KEY not set. Add it to .env or export it. "
            "Get your key at https://my.blotato.com/ under Settings > API Keys."
        )
    return key


def _headers():
    return {
        "Content-Type": "application/json",
        "blotato-api-key": _api_key(),
    }


def _request(method, path, **kwargs):
    url = f"{BASE_URL}{path}"
    backoff = 2
    last_exc = None
    for attempt in range(5):
        try:
            resp = requests.request(method, url, headers=_headers(), **kwargs)
            if resp.status_code == 429:
                wait = backoff * (2 ** attempt)
                print(f"Rate limited. Retrying in {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            if attempt < 4:
                wait = backoff * (2 ** attempt)
                print(f"Request failed ({exc}). Retrying in {wait}s...")
                time.sleep(wait)
    raise RuntimeError(f"Request failed after 5 attempts: {last_exc}")


def list_accounts(platform=None):
    params = {}
    if platform:
        params["platform"] = platform
    data = _request("GET", "/users/me/accounts", params=params)
    return data.get("items", data if isinstance(data, list) else [])


def publish_post(account_id, platform, text, media_urls=None, scheduled_at=None):
    if platform not in VALID_PLATFORMS:
        raise ValueError(f"Invalid platform '{platform}'. Must be one of: {VALID_PLATFORMS}")

    body = {
        "post": {
            "accountId": account_id,
            "content": {
                "text": text,
                "platform": platform,
            },
            "target": {
                "targetType": platform,
            },
        }
    }

    if media_urls:
        body["post"]["content"]["mediaUrls"] = (
            media_urls if isinstance(media_urls, list) else [media_urls]
        )

    if scheduled_at:
        body["scheduledAt"] = scheduled_at

    return _request("POST", "/posts", json=body)


def get_post_status(post_submission_id):
    return _request("GET", f"/posts/{post_submission_id}/status")


def list_visual_templates():
    return _request("GET", "/videos/templates")


def create_visual(template_id, prompt, inputs=None, render=True):
    body = {
        "templateId": template_id,
        "inputs": inputs or {},
        "prompt": prompt,
        "render": render,
    }
    return _request("POST", "/videos/from-templates", json=body)


def get_visual_status(creation_id):
    return _request("GET", f"/videos/creations/{creation_id}")
