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
        transaction_date: Optional[str] = None,
        fiscal_year: Optional[str] = None,
        period: Optional[str] = None,
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
        self.transaction_date = transaction_date or ""
        self.fiscal_year = fiscal_year or ""
        self.period = period or ""

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
            transaction_date=entry.get("transaction_date") or "",
            fiscal_year=entry.get("fiscal_year") or "",
            period=entry.get("period") or "",
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

    @staticmethod
    def _extract_purb_id(ref_no: str) -> Optional[int]:
        """Extract numeric ID from 'PURB/2026-2027/001229' → 1229, or None if not a PURB."""
        if not ref_no or not ref_no.startswith("PURB/"):
            return None
        try:
            return int(ref_no.rsplit("/", 1)[-1])
        except (ValueError, IndexError):
            return None

    def _find_jv_entry(
        self,
        pb_ref_no: str,
        user_id: int,
        division_id: int,
        department_id: int,
        type_of_sale_id: int,
        location_id: int,
    ) -> Optional[dict]:
        """Paginate through the JV report and return the matching entry dict.

        Early-exit heuristic for PURB refs: if we've seen ≥5 PURBs with IDs
        above AND ≥5 with IDs below the target without finding it, the entry
        is conclusively absent — no need to scan the full report.
        """
        # Discover all ledger groups from ERP; fall back to [1, 2] if unavailable
        try:
            lg_resp = self.client.session.get(
                f"{self.client.BASE_URL}/core/dynamic-screen-wrapper/Ledger%20Group/",
                params={"page_number": 1, "page_size": 100, "user_id": user_id},
                timeout=10,
            )
            lg_data = lg_resp.json().get("screenmatlistingdata_set") or []
            ledger_groups = [int(row["id"]) for row in lg_data if row.get("id")] or [1, 2]
        except Exception:
            ledger_groups = [1, 2]

        target_id = self._extract_purb_id(pb_ref_no)
        ABOVE_NEEDED = 1   # just 1 newer PURB in JV is enough to confirm newer ones exist
        BELOW_NEEDED = 5   # 5 older PURBs confirms we've passed the target's slot

        for ledger_group in ledger_groups:
            purb_above: set = set()
            purb_below: set = set()
            for page in range(1, self.MAX_PAGES + 1):
                body = {
                    "report_name": self.REPORT_NAME,
                    "parameter_1": "",
                    "parameter_2": "",
                    "parameter_3": "",
                    "parameter_4": "",
                    "parameter_5": "",
                    "tenant_id": int(self.client.tenant_id),
                    "ledger_group": ledger_group,
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
                    log.info(f"[JV] No entries at page {page} (lg={ledger_group}) — stopping")
                    break

                for entry in entries:
                    ref = entry.get("ref_transaction_no")
                    if ref == pb_ref_no:
                        log.info(f"[JV] Found {pb_ref_no} on page {page} (lg={ledger_group})")
                        return entry

                    # Track surrounding PURB IDs for early-exit heuristic
                    if target_id is not None:
                        eid = self._extract_purb_id(ref or "")
                        if eid is not None:
                            if eid > target_id:
                                purb_above.add(eid)
                            elif eid < target_id:
                                purb_below.add(eid)

                # Early exit: 1 newer PURB in JV + 5 older ones → target slot is conclusively absent
                if target_id is not None and len(purb_above) >= ABOVE_NEEDED and len(purb_below) >= BELOW_NEEDED:
                    log.info(
                        f"[JV] {pb_ref_no} not found in lg={ledger_group} — bracketed by "
                        f"{len(purb_above)} above and {len(purb_below)} below after page {page}"
                    )
                    break

                if len(entries) < self.PAGE_LIMIT:
                    break

        return None
