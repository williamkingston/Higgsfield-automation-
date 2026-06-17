#!/usr/bin/env python3
"""Publish a post to a social media platform via Blotato."""
import argparse
import json
from client import publish_post


def main():
    parser = argparse.ArgumentParser(description="Publish a social media post")
    parser.add_argument("--platform", required=True, help="Target platform")
    parser.add_argument("--text", required=True, help="Post text content")
    parser.add_argument("--account-id", required=True, help="Blotato account ID")
    parser.add_argument("--media-url", action="append", help="Media URL(s) to attach")
    parser.add_argument("--scheduled-at", help="ISO 8601 timestamp for scheduling")
    args = parser.parse_args()

    result = publish_post(
        account_id=args.account_id,
        platform=args.platform,
        text=args.text,
        media_urls=args.media_url,
        scheduled_at=args.scheduled_at,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
