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
            return None
        # 201 body is {"status": "Record Created Successfully", "id": <int>}
        return resp.json()

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
