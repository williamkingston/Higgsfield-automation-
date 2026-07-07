#!/usr/bin/env python3
"""Live end-to-end smoke test against the real Higgsfield REST API.

Guarded so it never runs by accident: set HIGGSFIELD_LIVE_SMOKE=1 (plus real
credentials) to enable. It submits ONE short generation, polls to completion,
and prints the raw response shapes so you can verify the API surface
(endpoint, auth headers, and `/generations` field names) that src/client.py
assumes — these were ported from OpenMontage and are otherwise unverified.

NOTE: model ids here target the platform.higgsfield.ai/v1 REST surface as
assumed by OpenMontage. The Higgsfield MCP connector's catalog uses a different
scheme (e.g. `seedance_2_0`, `kling3_0`, `veo3_1`). Override with
HIGGSFIELD_SMOKE_MODEL to match whatever your REST account actually accepts.

Usage:
    HIGGSFIELD_LIVE_SMOKE=1 \\
    HIGGSFIELD_API_KEY=... HIGGSFIELD_API_SECRET=... \\
    python scripts/live_smoke.py "a calm ocean at sunrise"
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.client import HiggsfieldClient, HiggsfieldError


def main() -> int:
    if os.environ.get("HIGGSFIELD_LIVE_SMOKE", "").lower() not in ("1", "true", "yes"):
        print(
            "Refusing to run: set HIGGSFIELD_LIVE_SMOKE=1 to enable the live test.\n"
            "It makes a real (billable) API call. See the module docstring.",
            file=sys.stderr,
        )
        return 2

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    prompt = sys.argv[1] if len(sys.argv) > 1 else "a calm ocean at sunrise, cinematic"
    model = os.environ.get("HIGGSFIELD_SMOKE_MODEL", "seedance_2_0")
    out = os.environ.get("HIGGSFIELD_SMOKE_OUTPUT", "output/smoke.mp4")

    try:
        client = HiggsfieldClient.from_env()
        print(f"→ base_url: {client.base_url}")

        print(f"→ submitting (model={model}): {prompt!r}")
        gen_id = client.submit_generation(prompt, model=model, duration=5)
        print(f"✓ submit ok — generation id: {gen_id}")

        # Show the raw status payload so field names can be verified by eye.
        first = client.get_generation(gen_id)
        print("→ first status payload keys:", sorted(first.keys()))
        print(json.dumps(first, indent=2)[:1000])

        result = client.wait_for_generation(gen_id, poll_interval=5, timeout=360)
        print(f"✓ terminal status: {result.status}")
        print(f"✓ output_url: {result.output_url}")

        if result.output_url:
            path = client.download(result.output_url, out)
            size = path.stat().st_size
            print(f"✓ downloaded {size} bytes → {path}")
            if size == 0:
                print("✗ downloaded file is empty", file=sys.stderr)
                return 1
    except HiggsfieldError as exc:
        print(f"✗ Higgsfield error: {exc}", file=sys.stderr)
        return 1

    print("\n✅ Live smoke test passed — the API surface in src/client.py is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
