"""The single Airtable client for Empire Ops.

Per the repo conventions, all Airtable I/O goes through this module — never
scattered ``requests`` calls. Implements bearer auth, request-ID logging, and
exponential backoff on 429s.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Iterator

import requests

from . import config

log = logging.getLogger("empire_ops.airtable")

API_ROOT = "https://api.airtable.com/v0"
_MAX_RETRIES = 5


class AirtableError(RuntimeError):
    pass


class AirtableClient:
    """Thin, typed wrapper over the Airtable REST API for one base."""

    def __init__(self, api_key: str | None = None, base_id: str | None = None):
        self._api_key = api_key or config.airtable_api_key()
        self.base_id = base_id or config.airtable_base_id()
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
        )

    # -- low-level request with rate-limit backoff -------------------------

    def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        url = f"{API_ROOT}/{self.base_id}/{path}"
        for attempt in range(_MAX_RETRIES):
            resp = self._session.request(method, url, timeout=30, **kwargs)
            req_id = resp.headers.get("x-request-id", "-")
            if resp.status_code == 429:
                wait = 2 ** attempt
                log.warning("Airtable 429 (req %s); backing off %ss", req_id, wait)
                time.sleep(wait)
                continue
            if not resp.ok:
                # Never log full bodies — they may carry record PII.
                raise AirtableError(
                    f"Airtable {method} {path} failed "
                    f"({resp.status_code}, req {req_id})"
                )
            log.debug("Airtable %s %s ok (req %s)", method, path, req_id)
            return resp.json()
        raise AirtableError(f"Airtable {method} {path} rate-limited after retries")

    # -- record operations -------------------------------------------------

    def list_records(
        self,
        table_id: str,
        *,
        max_records: int | None = None,
        page_size: int = 100,
        filter_by_formula: str | None = None,
        sort: list[dict[str, str]] | None = None,
    ) -> Iterator[dict]:
        """Yield records from a table, transparently following pagination.

        Fields come back keyed by field ID (not name) so reads line up with how
        we write and with the constants in ``schema.py``.
        """
        params: dict[str, Any] = {
            "pageSize": page_size,
            "returnFieldsByFieldId": "true",
        }
        if filter_by_formula:
            params["filterByFormula"] = filter_by_formula
        if sort:
            for i, s in enumerate(sort):
                params[f"sort[{i}][field]"] = s["field"]
                params[f"sort[{i}][direction]"] = s.get("direction", "asc")

        yielded = 0
        offset: str | None = None
        while True:
            if offset:
                params["offset"] = offset
            data = self._request("GET", table_id, params=params)
            for record in data.get("records", []):
                yield record
                yielded += 1
                if max_records and yielded >= max_records:
                    return
            offset = data.get("offset")
            if not offset:
                return

    def get_first(self, table_id: str, **kwargs: Any) -> dict | None:
        """Return the first record from a table, or None if empty."""
        for record in self.list_records(table_id, max_records=1, **kwargs):
            return record
        return None

    def create_records(self, table_id: str, records: list[dict]) -> list[dict]:
        payload = {"records": [{"fields": r} for r in records], "typecast": True}
        return self._request("POST", table_id, json=payload).get("records", [])

    def update_record(self, table_id: str, record_id: str, fields: dict) -> dict:
        payload = {"records": [{"id": record_id, "fields": fields}]}
        result = self._request("PATCH", table_id, json=payload)
        return result["records"][0]
