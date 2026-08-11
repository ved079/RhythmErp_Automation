from typing import Optional, Dict

from common.erp_api_client import RhythmERPAPIClient
from pages.private_b2b.modules.sales_order.api.endpoints import (
    SCREEN_NAME,
    build_create_url,
    build_get_url,
    build_list_url,
    build_schema_url,
)


class SOAPIUtils:
    """CRUD helpers for the Sales Order screen (portal /sales/orders/ viewset)."""

    def __init__(self, client: RhythmERPAPIClient):
        self.client = client
        self._last_payload = None
        self._last_response = None
        self._last_status = None

    def create_so(self, payload: dict) -> Optional[Dict]:
        self._last_payload = payload
        url = build_create_url(self.client.BASE_URL)
        resp = self.client.session.post(
            url,
            headers=self.client.session.headers,
            params={"screen_name": "Sales Order", "viewType": "create"},
            json=payload,
            timeout=30,
        )
        self._last_response = resp
        self._last_status = resp.status_code
        if resp.status_code in (200, 201):
            return resp.json()
        return None

    def get_so(self, entry_id) -> Optional[Dict]:
        url = build_get_url(self.client.BASE_URL, entry_id)
        resp = self.client.session.get(url, headers=self.client.session.headers, timeout=30)
        self._last_response = resp
        self._last_status = resp.status_code
        if resp.status_code == 200:
            return resp.json()
        return None

    def list_sos(self, page: int = 1, page_size: int = 25) -> Optional[Dict]:
        url = build_list_url(self.client.BASE_URL)
        resp = self.client.session.get(
            url,
            headers=self.client.session.headers,
            params={"page_number": page, "page_size": page_size},
            timeout=30,
        )
        self._last_response = resp
        self._last_status = resp.status_code
        if resp.status_code == 200:
            return resp.json()
        return None

    def get_schema(self) -> Optional[Dict]:
        url = build_schema_url(self.client.BASE_URL)
        resp = self.client.session.get(url, headers=self.client.session.headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        return None
