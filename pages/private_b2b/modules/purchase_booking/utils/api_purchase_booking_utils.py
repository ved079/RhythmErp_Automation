"""
api_purchase_booking_utils.py
-----------------------------
Thin API wrapper for Purchase Booking CRUD operations.

PB creation uses the ERP's async SUBMIT pipeline:
  POST /procure_to_pay/purchase-booking/?screenName=Purchase%20Booking
       &submission_id=<UUID>&request_method=SUBMIT
  → 201 (pipeline queued); async processing takes ~3-5 s via SSE.
After 201, we wait then GET the listing to retrieve the new PB's id.
"""

import uuid
from typing import Optional, Dict

from common.erp_api_client import RhythmERPAPIClient
from pages.private_b2b.modules.purchase_booking.api.endpoints import (
    SCREEN_NAME,
    CREATE_PARAMS,
    build_create_url,
    build_get_url,
    build_list_url,
    build_update_url,
    build_schema_url,
)


class PBAPIUtils:
    """CRUD helpers for the Purchase Booking screen."""

    def __init__(self, client: RhythmERPAPIClient):
        self.client = client
        self._last_response = None
        self._last_status = None

    def create_pb(self, payload: dict) -> Optional[dict]:
        """Submit a PB via the ERP's async SUBMIT pipeline.

        POSTs with request_method=SUBMIT. The 201 response body contains
        {"status": "Record Created Successfully", "id": <int>} directly.
        Returns (data, submission_id) so the caller can stream events.
        """
        submission_id = str(uuid.uuid4())
        params = {**CREATE_PARAMS, "submission_id": submission_id}
        url = build_create_url(self.client.BASE_URL)
        resp = self.client.session.post(
            url, headers=self.client.session.headers, json=payload, params=params, timeout=30
        )
        self._last_response = resp
        self._last_status = resp.status_code
        if resp.status_code not in (200, 201):
            return None, submission_id
        # 201 body is {"status": "Record Created Successfully", "id": <int>}
        return resp.json(), submission_id

    def stream_pb_events(self, submission_id: str, timeout: int = 40):
        """Stream SSE events for a PB submission until terminal or timeout.

        Yields parsed event dicts: {submission_id, sequence, step, status,
        message, meta, is_terminal, timestamp}.

        The endpoint hangs indefinitely for unknown submission_ids, so `timeout`
        is enforced as a hard read timeout on the streaming connection.
        Auth is Bearer token (same session headers — no separate cookie needed).
        """
        import json as _json
        url = f"{self.client.BASE_URL}/notification/api/transactions/{submission_id}/events/"
        try:
            with self.client.session.get(
                url,
                headers={**self.client.session.headers, "Accept": "text/event-stream"},
                stream=True,
                timeout=timeout,
            ) as resp:
                if resp.status_code != 200:
                    return
                data_buf = ""
                for line in resp.iter_lines(decode_unicode=True):
                    if line.startswith("data:"):
                        data_buf = line[5:].strip()
                    elif line == "" and data_buf:
                        try:
                            event = _json.loads(data_buf)
                            yield event
                            if event.get("is_terminal"):
                                return
                        except _json.JSONDecodeError:
                            pass
                        data_buf = ""
        except Exception:
            return

    def get_pb(self, entry_id: int) -> Optional[dict]:
        url = build_get_url(self.client.BASE_URL, entry_id)
        resp = self.client.session.get(url, headers=self.client.session.headers, timeout=30)
        self._last_response = resp
        self._last_status = resp.status_code
        if resp.status_code == 200:
            return resp.json()
        return None

    def list_pbs(self, page: int = 1, page_size: int = 10) -> Optional[dict]:
        url = build_list_url(self.client.BASE_URL)
        resp = self.client.session.get(
            url,
            headers=self.client.session.headers,
            params={
                "page": page,
                "limit": page_size,
                "filters": "",
                "screen_name": SCREEN_NAME,
                "search": "",
            },
            timeout=30,
        )
        self._last_response = resp
        self._last_status = resp.status_code
        if resp.status_code == 200:
            return resp.json()
        return None

    def update_pb(self, entry_id: int, payload: dict) -> Optional[dict]:
        url = build_update_url(self.client.BASE_URL, entry_id)
        resp = self.client.session.put(url, headers=self.client.session.headers, json=payload, timeout=30)
        self._last_response = resp
        self._last_status = resp.status_code
        if resp.status_code in (200, 201):
            return resp.json()
        return None

    def get_schema(self) -> Optional[dict]:
        url = build_schema_url(self.client.BASE_URL)
        resp = self.client.session.get(url, headers=self.client.session.headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        return None

    def last_response(self):
        return self._last_response
