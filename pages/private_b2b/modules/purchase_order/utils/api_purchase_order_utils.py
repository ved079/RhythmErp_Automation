from typing import Dict, List, Optional

from common.erp_api_client import RhythmERPAPIClient
from pages.private_b2b.modules.purchase_order.api.endpoints import (
    SCREEN_NAME,
    build_create_url,
    build_get_url,
    build_list_url,
    build_update_url,
    build_schema_url,
)
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    generate_po_payload,
    build_po_payload,
    generate_random_fk_ids,
    compute_expected_results,
    assert_calculations_match,
)


class POAPIUtils:
    def __init__(self, api_client: RhythmERPAPIClient = None):
        self.client = api_client or RhythmERPAPIClient()
        self._last_payload = None
        self._last_response = None
        self._last_status = None

    def create_po(self, payload: dict = None, **overrides) -> Optional[Dict]:
        if payload is None:
            payload = generate_po_payload(fk_overrides=overrides)
        self._last_payload = payload
        url = build_create_url(self.client.BASE_URL)
        resp = self.client.session.post(url, headers=self.client.session.headers, json=payload, timeout=30)
        self._last_response = resp
        self._last_status = resp.status_code
        if resp.status_code in (200, 201):
            data = resp.json()
            entry_id = data.get("id") or data.get("entry_id")
            if entry_id:
                payload["id"] = entry_id
            return data
        return None

    def get_po(self, entry_id) -> Optional[Dict]:
        url = build_get_url(self.client.BASE_URL, entry_id)
        resp = self.client.session.get(url, headers=self.client.session.headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        self._last_response = resp
        self._last_status = resp.status_code
        return None

    def list_pos(self, page: int = 1, page_size: int = 20) -> Optional[Dict]:
        url = build_list_url(self.client.BASE_URL)
        resp = self.client.session.get(
            url,
            headers=self.client.session.headers,
            params={"page_number": page, "page_size": page_size},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()
        self._last_response = resp
        self._last_status = resp.status_code
        return None

    def update_po(self, entry_id: int, payload: dict) -> Optional[Dict]:
        url = build_update_url(self.client.BASE_URL, entry_id)
        resp = self.client.session.put(url, headers=self.client.session.headers, json=payload, timeout=30)
        self._last_response = resp
        self._last_status = resp.status_code
        if resp.status_code in (200, 201):
            return resp.json()
        return None

    def get_schema(self) -> Optional[Dict]:
        url = build_schema_url(self.client.BASE_URL)
        resp = self.client.session.get(url, headers=self.client.session.headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        return None

    def create_and_verify_calculations(self, payload: dict = None, **overrides) -> Dict:
        if payload is None:
            payload = generate_po_payload(fk_overrides=overrides)

        expected = compute_expected_results(payload)
        result = self.create_po(payload=payload)
        assert result is not None, f"PO creation failed (status {self._last_status})"

        entry_id = result.get("id") or result.get("entry_id")
        assert entry_id is not None, "No entry ID in create response"

        entry = self.get_po(entry_id)
        assert entry is not None, f"Failed to fetch PO {entry_id}"

        assert_calculations_match(entry, expected)

        return {"entry": entry, "expected": expected, "id": entry_id}

    def create_and_expect_failure(self, payload: dict) -> int:
        url = build_create_url(self.client.BASE_URL)
        resp = self.client.session.post(url, headers=self.client.session.headers, json=payload, timeout=30)
        self._last_response = resp
        self._last_status = resp.status_code
        return resp.status_code

    def assert_validation_error(
        self,
        field: Optional[str] = None,
        expected_status: int = 400,
        expected_message_substring: str = "",
        accept_statuses: List[int] = None,
    ):
        if accept_statuses is None:
            accept_statuses = [400, 500]
        assert self._last_status in accept_statuses, (
            f"Expected status in {accept_statuses}, got {self._last_status}"
        )
        if self._last_response is not None and self._last_response.text:
            text = self._last_response.text.lower()
            if expected_message_substring:
                assert expected_message_substring.lower() in text, (
                    f"Expected message containing '{expected_message_substring}', "
                    f"got: {self._last_response.text[:500]}"
                )
