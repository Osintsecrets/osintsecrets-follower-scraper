import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

USERNAME = "osintsecrets"
OUT = Path("data/followers.json")
SOURCE_URL = f"https://instastatistics.com/{USERNAME}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HomeIntelDisplay/1.0; +https://github.com/Osintsecrets/osintsecrets-follower-scraper)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

def extract_count(html: str) -> int:
    patterns = [
        rf"@{USERNAME}\) is an Instagram account with\s*([\d,]+)\s*followers",
        rf"@{USERNAME}\) currently has\s*([\d,]+)\s*Instagram followers",
        r'"followerCount"\s*:\s*(\d+)',
        r'"followers"\s*:\s*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            count = int(match.group(1).replace(",", ""))
            if count > 0:
                return count
    raise RuntimeError("Instastatistics returned no valid follower count")

def get_count(session: requests.Session) -> int:
    response = session.get(SOURCE_URL, headers=HEADERS, timeout=25)
    response.raise_for_status()
    return extract_count(response.text)

def main() -> None:
    followers = get_count(requests.Session())
    payload = {
        "username": USERNAME,
        "followers": followers,
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "instastatistics-public-counter",
        "sourceUrl": SOURCE_URL,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(payload))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Counter refresh failed: {exc}", file=sys.stderr)
        raise
