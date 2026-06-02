"""Outbound notifications (digests, alerts).

Slack incoming webhook is the one stable, no-OAuth sink, so it's all Phase 3B
needs. Posting is best-effort: a failed notification never aborts a routine that
already did its real work (e.g. writing the digest row).
"""

from __future__ import annotations

import json
import logging

import requests

from . import config

log = logging.getLogger("empire_ops.notify")


def post_slack(text: str, *, webhook_url: str | None = None) -> bool:
    """Post a message to Slack. Returns True on success, False otherwise."""
    url = webhook_url or config.get("SLACK_WEBHOOK_URL")
    if not url:
        log.info("No SLACK_WEBHOOK_URL configured; skipping Slack post.")
        return False
    try:
        resp = requests.post(
            url,
            data=json.dumps({"text": text}),
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        if resp.ok:
            return True
        log.warning("Slack post failed (%s)", resp.status_code)
        return False
    except requests.RequestException as exc:
        log.warning("Slack post errored: %s", exc)
        return False
