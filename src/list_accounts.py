#!/usr/bin/env python3
"""List connected social media accounts from Blotato."""
import argparse
import json
from client import list_accounts


def main():
    parser = argparse.ArgumentParser(description="List Blotato social accounts")
    parser.add_argument("--platform", help="Filter by platform (e.g. twitter, instagram)")
    args = parser.parse_args()

    accounts = list_accounts(platform=args.platform)

    if not accounts:
        print("No accounts found. Connect your socials at https://my.blotato.com/")
        return

    print(json.dumps(accounts, indent=2))


if __name__ == "__main__":
    main()
