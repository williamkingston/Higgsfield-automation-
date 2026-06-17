#!/usr/bin/env python3
"""View the post log with optional filters."""
import argparse
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / "data" / "post-log.json"


def main():
    parser = argparse.ArgumentParser(description="View post log")
    parser.add_argument("--platform", help="Filter by platform")
    parser.add_argument("--last", type=int, help="Show only the last N posts")
    parser.add_argument("--since", help="Show posts since date (YYYY-MM-DD)")
    parser.add_argument("--status", help="Filter by status")
    args = parser.parse_args()

    if not LOG_FILE.exists():
        print("No posts logged yet.")
        return

    with open(LOG_FILE) as f:
        log = json.load(f)

    posts = log.get("posts", [])

    if args.platform:
        posts = [p for p in posts if p["platform"] == args.platform]

    if args.status:
        posts = [p for p in posts if p.get("status") == args.status]

    if args.since:
        cutoff = datetime.fromisoformat(args.since)
        posts = [
            p for p in posts
            if datetime.fromisoformat(p["timestamp"].replace("Z", "+00:00")) >= cutoff
        ]

    if args.last:
        posts = posts[-args.last:]

    if not posts:
        print("No posts match the filters.")
        return

    print(f"Showing {len(posts)} post(s):\n")
    for i, post in enumerate(posts, 1):
        print(f"#{i}")
        print(f"  Platform:  {post['platform']}")
        print(f"  Date:      {post['timestamp']}")
        print(f"  Status:    {post.get('status', 'unknown')}")
        print(f"  Text:      {post['text'][:100]}{'...' if len(post['text']) > 100 else ''}")
        if post.get("live_url"):
            print(f"  Live URL:  {post['live_url']}")
        if post.get("media_url"):
            print(f"  Media:     {post['media_url']}")
        if post.get("post_id"):
            print(f"  Post ID:   {post['post_id']}")
        print()


if __name__ == "__main__":
    main()
