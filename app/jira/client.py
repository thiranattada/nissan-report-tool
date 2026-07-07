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
        """Yields every issue matching jql, handling pagination transparently.
        Uses the token-based /rest/api/3/search/jql endpoint — Atlassian
        removed the old startAt/total-based /rest/api/3/search on 1 May 2025
        (it now returns 410 Gone)."""
        next_page_token = None
        while True:
            payload = self._search_page(jql, fields, next_page_token)
            issues = payload.get("issues", [])
            if not issues:
                break
            yield from issues
            next_page_token = payload.get("nextPageToken")
            # Jira Cloud has a documented bug on some sites where
            # nextPageToken/isLast never signal completion; a short page is
            # a reliable stop condition regardless of that.
            if not next_page_token or len(issues) < PAGE_SIZE:
                break

    def _search_page(self, jql: str, fields: list[str], next_page_token: str | None) -> dict:
        url = f"{self.base_url}/rest/api/3/search/jql"
        body = {
            "jql": jql,
            "fields": fields,
            "maxResults": PAGE_SIZE,
        }
        if next_page_token:
            body["nextPageToken"] = next_page_token
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
