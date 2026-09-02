"""
api_payment_utils.py
--------------------
Thin API wrapper for Payment CRUD + bank account resolution.

Payment creation uses a direct POST (no SUBMIT pipeline):
  POST /procure_to_pay/payments/
  → 200/201 with {"id": <int>, "transaction_ref_no": "<str>", ...}

Passing posting_status="Post" in the payload creates AND posts in one step.
"""

from typing import Optional, List

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.private_b2b.modules.payment.api.endpoints import (
    PAYMENT_METHOD_CASH,
    build_create_url,
    build_get_url,
    build_list_url,
    build_bank_list_url,
    build_bank_get_url,
)


class PaymentAPIUtils:
    """CRUD helpers for the Payment screen."""

    def __init__(self, client: RhythmERPAPIClient):
        self.client = client
        self._last_response = None
        self._last_status = None
        # Cache: payment_method_ref_id -> list of {id, name, bal}
        self._bank_cache: dict = {}

    def create_payment(self, payload: dict) -> Optional[dict]:
        """POST a payment. Returns the response JSON or None on failure."""
        url = build_create_url(self.client.BASE_URL)
        resp = self.client.session.post(
            url, headers=self.client.session.headers, json=payload, timeout=30
        )
        self._last_response = resp
        self._last_status = resp.status_code
        if resp.status_code not in (200, 201):
            return None
        return resp.json()

    def get_payment(self, entry_id: int) -> Optional[dict]:
        url = build_get_url(self.client.BASE_URL, entry_id)
        resp = self.client.session.get(url, headers=self.client.session.headers, timeout=30)
        self._last_response = resp
        self._last_status = resp.status_code
        return resp.json() if resp.status_code == 200 else None

    def resolve_bank_account(self, payment_method_ref_id: int) -> Optional[int]:
        """Return a bank account id for the given payment method.

        Cash (53) → look for a bank whose name contains "Cash" (Petty Cash sub-group).
        Other methods → prefer the default bank (is_default_bank=True), else the
        first available bank.

        Banks are fetched from /core/dynamic-screen-wrapper/Bank/ and cached.
        """
        if payment_method_ref_id in self._bank_cache:
            banks = self._bank_cache[payment_method_ref_id]
        else:
            banks = self._fetch_all_banks()
            self._bank_cache[payment_method_ref_id] = banks

        if not banks:
            return None

        if payment_method_ref_id == PAYMENT_METHOD_CASH:
            # Petty Cash bank — name contains "Cash"
            cash_banks = [b for b in banks if "cash" in b["name"].lower()]
            if cash_banks:
                log.info(f"  Payment: selected cash bank #{cash_banks[0]['id']} ({cash_banks[0]['name']})")
                return cash_banks[0]["id"]
            log.warning("  Payment: no cash bank found; falling back to first bank")

        # Prefer the default bank; fall back to first
        defaults = [b for b in banks if b.get("is_default")]
        chosen = defaults[0] if defaults else banks[0]
        log.info(f"  Payment: selected bank #{chosen['id']} ({chosen['name']})")
        return chosen["id"]

    def _fetch_all_banks(self) -> List[dict]:
        """Fetch all bank records from the dynamic-screen-wrapper."""
        url = build_bank_list_url(self.client.BASE_URL)
        resp = self.client.session.get(
            url,
            headers=self.client.session.headers,
            params={"page_number": 1, "page_size": 100, "is_excel_download": "false"},
            timeout=30,
        )
        if resp.status_code != 200:
            log.warning(f"  Payment: bank list returned {resp.status_code}")
            return []

        data = resp.json()
        listing_rows = data.get("screenmatlistingdata_set", [])
        banks = []
        for row in listing_rows:
            bank_id = row.get("id")
            if bank_id is None:
                continue
            # Fetch each bank to get name + is_default_bank
            detail_url = build_bank_get_url(self.client.BASE_URL, bank_id)
            det_resp = self.client.session.get(
                detail_url, headers=self.client.session.headers, timeout=15
            )
            if det_resp.status_code != 200:
                continue
            det = det_resp.json()
            banks.append({
                "id": int(det.get("id", bank_id)),
                "name": det.get("bank_name", ""),
                "is_default": bool(det.get("is_default_bank", False)),
                "bal": det.get("bal_cash_credit_limit"),
            })
        log.info(f"  Payment: fetched {len(banks)} bank(s)")
        return banks
