import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

USERNAME = "osintsecrets"
OUT = Path("data/followers.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.instagram.com",
    "Referer": f"https://www.instagram.com/{USERNAME}/",
    "X-IG-App-ID": "936619743392459",
}

def get_count(session: requests.Session) -> int:
    endpoints = [
        f"https://i.instagram.com/api/v1/users/web_profile_info/?username={USERNAME}",
        f"https://www.instagram.com/api/v1/users/web_profile_info/?username={USERNAME}",
    ]
    for url in endpoints:
        response = session.get(url, headers=HEADERS, timeout=20)
        if not response.ok:
            continue
        try:
            user = response.json()["data"]["user"]
            count = user.get("follower_count")
            if isinstance(count, int) and count >= 0:
                return count
        except (ValueError, KeyError, TypeError):
            pass

    response = session.get(
        f"https://www.instagram.com/{USERNAME}/",
        headers={**HEADERS, "Accept": "text/html,application/xhtml+xml"},
        timeout=20,
    )
    response.raise_for_status()
    patterns = [
        r'"follower_count":(\d+)',
        r'"edge_followed_by":\{"count":(\d+)\}',
        r'"followed_by_viewer":false.*?"follower_count":(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, response.text)
        if match:
            return int(match.group(1))
    raise RuntimeError("Instagram returned no follower count")

def main() -> None:
    session = requests.Session()
    followers = get_count(session)
    payload = {
        "username": USERNAME,
        "followers": followers,
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "instagram-public-profile",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(payload))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Scrape failed: {exc}", file=sys.stderr)
        raise
