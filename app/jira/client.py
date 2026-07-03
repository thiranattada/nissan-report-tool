import time
from typing import Iterator

import requests

PAGE_SIZE = 100
MAX_RETRIES = 5


class JiraClient:
    """Thin wrapper around the Jira Cloud REST API: auth + pagination + retry.
    No business logic lives here — see queries.py / service.py for that."""

    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({"Accept": "application/json"})

    def search(self, jql: str, fields: list[str]) -> Iterator[dict]:
        """Yields every issue matching jql, handling pagination transparently."""
        start_at = 0
        total = None
        while total is None or start_at < total:
            payload = self._search_page(jql, fields, start_at)
            total = payload["total"]
            issues = payload["issues"]
            if not issues:
                break
            yield from issues
            start_at += len(issues)

    def _search_page(self, jql: str, fields: list[str], start_at: int) -> dict:
        url = f"{self.base_url}/rest/api/3/search"
        body = {
            "jql": jql,
            "fields": fields,
            "startAt": start_at,
            "maxResults": PAGE_SIZE,
        }
        for attempt in range(MAX_RETRIES):
            resp = self.session.post(url, json=body)
            if resp.status_code == 429 or resp.status_code >= 500:
                retry_after = float(resp.headers.get("Retry-After", 2 ** attempt))
                time.sleep(retry_after)
                continue
            resp.raise_for_status()
            return resp.json()
        resp.raise_for_status()
        return resp.json()
