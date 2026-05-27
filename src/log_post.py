#!/usr/bin/env python3
"""Log a published post to the post-log.json file."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / "data" / "post-log.json"


def load_log():
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return {"posts": []}


def save_log(data):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Log a published post")
    parser.add_argument("--platform", required=True, help="Platform posted to")
    parser.add_argument("--text", required=True, help="Post text")
    parser.add_argument("--media-url", help="Visual/media URL")
    parser.add_argument("--post-id", help="Blotato post submission ID")
    parser.add_argument("--live-url", help="Live URL of the published post")
    parser.add_argument("--status", default="published", help="Post status")
    args = parser.parse_args()

    log = load_log()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": args.platform,
        "text": args.text,
        "media_url": args.media_url,
        "post_id": args.post_id,
        "live_url": args.live_url,
        "status": args.status,
    }
    log["posts"].append(entry)
    save_log(log)

    print(f"Logged post to {args.platform} (total: {len(log['posts'])} posts)")
    print(json.dumps(entry, indent=2))


if __name__ == "__main__":
    main()
