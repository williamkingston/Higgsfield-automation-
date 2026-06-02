"""Empire Ops — automation foundation for the Velvyt ventures.

Phase 0 of the staged build plan (see docs/automation-plan.md). This package is
the shared spine every routine builds on:

- ``config``      env loading
- ``schema``      live Airtable base/table/field IDs
- ``guardrails``  the §4 tier policy, enforced
- ``airtable``    the single Airtable client (all base I/O goes through here)
"""

__version__ = "0.1.0"
