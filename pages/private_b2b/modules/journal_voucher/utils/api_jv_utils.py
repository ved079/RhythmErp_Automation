"""
api_jv_utils.py
---------------
Fetches the JV (Journal Voucher) report and verifies accounting entries
for a given Purchase Booking reference number.

Report endpoint:
    POST /reports/builder?user_id={user_id}
    body: { report_name:2, tenant_id, division_id, department_id,
            type_of_sale_id, location_id,
            task_identifier:"report_view_data",
            pageLimit:50, pageNumber:1 }

Response structure:
    list[0]["report_data"] → list of JV header entries
    Each header entry has "children" → { "data": [ { account row }, ... ] }

Field locations:
    - division / department / type_of_sale / location: on each child row
    - commodity: on Debit child rows only (null on Credit/Payable rows)
    - total_debit_amount / total_credit_amount: on the header entry
"""

from __future__ import annotations

import jwt
from typing import List, Optional

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log


class JVVerificationResult:
    def __init__(
        self,
        pb_ref_no: str,
        found: bool,
        debit: Optional[float] = None,
        credit: Optional[float] = None,
        balanced: Optional[bool] = None,
        # fields extracted from child rows
        division: Optional[str] = None,
        department: Optional[str] = None,
        type_of_sale: Optional[str] = None,
        location: Optional[str] = None,
        commodity: Optional[str] = None,   # from the Debit row
        child_rows: Optional[List[dict]] = None,
        error: Optional[str] = None,
    ):
        self.pb_ref_no = pb_ref_no
        self.found = found
        self.debit = debit
        self.credit = credit
        self.balanced = balanced
        self.division = division
        self.department = department
        self.type_of_sale = type_of_sale
        self.location = location
        self.commodity = commodity
        self.child_rows = child_rows or []
        self.error = error

    def ok(self) -> bool:
        return self.found and self.balanced is True

    def summary(self) -> str:
        if self.error:
            return f"JV check error: {self.error}"
        if not self.found:
            return f"JV entry not found for {self.pb_ref_no}"
        status = "BALANCED" if self.balanced else "UNBALANCED"
        parts = [f"JV {self.pb_ref_no} — {status}",
                 f"DR={self.debit:.2f} CR={abs(self.credit):.2f}"]
        if self.commodity:
            parts.append(f"commodity={self.commodity}")
        return " | ".join(parts)


class JVAPIUtils:
    """Fetch and verify JV report entries for a Purchase Booking."""

    REPORT_NAME = 2
    PAGE_LIMIT = 50
    MAX_PAGES = 20  # safety cap

    def __init__(self, client: RhythmERPAPIClient):
        self.client = client

    # ── Public ────────────────────────────────────────────────────────────

    def verify_pb(
        self,
        pb_ref_no: str,
        division_id: int,
        department_id: int,
        type_of_sale_id: int,
        location_id: int,
    ) -> JVVerificationResult:
        """
        Find the JV entry for *pb_ref_no*, assert DR == |CR|, and extract
        the dimension fields (division, department, type_of_sale, location,
        commodity) from the child rows.

        Args:
            pb_ref_no:        "PURB/2026-2027/001129"
            division_id:      chain context parameter1
            department_id:    chain context parameter2
            type_of_sale_id:  chain context parameter5
            location_id:      chain context parameter6

        Returns:
            JVVerificationResult — call .ok() for pass/fail, .summary() for message.
        """
        log.info(f"[JV] Verifying journal voucher for {pb_ref_no}")
        user_id = self._user_id_from_token()

        try:
            entry = self._find_jv_entry(
                pb_ref_no=pb_ref_no,
                user_id=user_id,
                division_id=division_id,
                department_id=department_id,
                type_of_sale_id=type_of_sale_id,
                location_id=location_id,
            )
        except Exception as e:
            log.warning(f"[JV] Fetch error: {e}")
            return JVVerificationResult(pb_ref_no=pb_ref_no, found=False, error=str(e))

        if entry is None:
            log.warning(f"[JV] Entry not found for {pb_ref_no}")
            return JVVerificationResult(pb_ref_no=pb_ref_no, found=False)

        debit = float(entry.get("total_debit_amount") or 0)
        credit = float(entry.get("total_credit_amount") or 0)
        balanced = round(debit, 2) == round(abs(credit), 2)

        # Fields live on child rows, not the header
        child_rows = (entry.get("children") or {}).get("data") or []
        division, department, type_of_sale, location, commodity = self._extract_child_fields(child_rows)

        result = JVVerificationResult(
            pb_ref_no=pb_ref_no,
            found=True,
            debit=debit,
            credit=credit,
            balanced=balanced,
            division=division,
            department=department,
            type_of_sale=type_of_sale,
            location=location,
            commodity=commodity,
            child_rows=child_rows,
        )
        log.info(f"[JV] {result.summary()}")
        return result

    # ── Private ───────────────────────────────────────────────────────────

    @staticmethod
    def _extract_child_fields(child_rows: List[dict]):
        """
        Extract dimension fields from the child account rows.

        division / department / type_of_sale / location — same on all rows,
        so we take the first non-null value from any row.

        commodity — only present on Debit rows (the Purchase/inventory side);
        the Credit/Payable row has null. We take it from the first Debit row.
        """
        division = department = type_of_sale = location = None
        commodities: list[str] = []

        for row in child_rows:
            if division is None:
                division = row.get("division") or None
            if department is None:
                department = row.get("department") or None
            if type_of_sale is None:
                type_of_sale = row.get("type_of_sale") or None
            if location is None:
                location = row.get("location") or None
            # collect all unique non-null commodities from Debit rows
            if row.get("debit_credit_type") == "Debit":
                c = row.get("commodity") or None
                if c and c not in commodities:
                    commodities.append(c)

        commodity = ", ".join(commodities) if commodities else None
        return division, department, type_of_sale, location, commodity

    def _user_id_from_token(self) -> int:
        """Decode user_id from the Bearer JWT without verifying signature."""
        try:
            token = self.client.token
            payload = jwt.decode(token, options={"verify_signature": False})
            return int(payload.get("user_id", 0))
        except Exception:
            log.warning("[JV] Could not decode user_id from token — using 0")
            return 0

    def _find_jv_entry(
        self,
        pb_ref_no: str,
        user_id: int,
        division_id: int,
        department_id: int,
        type_of_sale_id: int,
        location_id: int,
    ) -> Optional[dict]:
        """Paginate through the JV report and return the matching entry dict."""
        for page in range(1, self.MAX_PAGES + 1):
            body = {
                "report_name": self.REPORT_NAME,
                "parameter_1": "",
                "parameter_2": "",
                "parameter_3": "",
                "parameter_4": "",
                "parameter_5": "",
                "tenant_id": int(self.client.tenant_id),
                "ledger_group": 1,
                # null filters = fetch all; matching is done in code by ref_transaction_no
                # passing actual IDs would exclude PBs on different locations/divisions
                "division_id": None,
                "department_id": None,
                "type_of_sale_id": None,
                "location_id": None,
                "file_format": None,
                "task_identifier": "report_view_data",
                "pageLimit": self.PAGE_LIMIT,
                "pageNumber": page,
            }

            resp = self.client.session.post(
                f"{self.client.BASE_URL}/reports/builder",
                params={"user_id": user_id},
                json=body,
                timeout=30,
            )
            resp.raise_for_status()
            raw = resp.json()

            # Response: list[0]["report_data"] holds the JV entries
            if isinstance(raw, list) and raw:
                entries = raw[0].get("report_data") or []
            elif isinstance(raw, dict):
                entries = raw.get("report_data") or raw.get("data") or raw.get("results") or []
            else:
                entries = []

            if not entries:
                log.info(f"[JV] No entries at page {page} — stopping")
                break

            for entry in entries:
                if entry.get("ref_transaction_no") == pb_ref_no:
                    log.info(f"[JV] Found {pb_ref_no} on page {page}")
                    return entry

            if len(entries) < self.PAGE_LIMIT:
                break

        return None
