"""
accounting_def_validator.py
---------------------------
Validates a Purchase Booking payload against the ERP's Accounting Definition
conditions BEFORE the record is submitted, so the automation script can confirm
the correct accounts will be hit.

Usage in batch_create.py:
    from .utils.accounting_def_validator import AccountingDefValidator
    validator = AccountingDefValidator(client)
    validator.load()                        # fetches AD once
    report = validator.validate(payload)    # returns ValidationReport
    validator.print_report(report)

AD condition parameter IDs → PB payload fields:
    5  (Type of Sale)   → payload["supplier_ref_type"]  (str: "Supplier"/"Farmer")
    6  (Location)       → payload["parameter6"]          (int: location FK id)

Operator codes:
    1704 = IN (value is in options list)
    1705 = NOT IN

Logical operator between conditions in a group:
    1710 = AND  (all conditions in group must be satisfied)
    null = last condition in the group (no further chaining)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ERP transaction_type code for Purchase Booking (global constant, not tenant-specific)
_PB_TRANSACTION_TYPE = "5"

# Operator code meanings
_OP_IN     = 1704
_OP_NOT_IN = 1705

# Map AD condition parameter IDs → the key in the PB payload dict
# and whether the value is an integer FK (True) or a plain string (False).
_PARAM_TO_PAYLOAD: dict[int, tuple[str, bool]] = {
    5: ("supplier_ref_type", False),   # Type of Sale: "Supplier" / "Farmer"
    6: ("parameter6",        True),    # Location: integer FK id
}


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ConditionResult:
    parameter_id: int
    param_label: str
    operator: int
    options: list
    passed: bool
    actual_value: Any


@dataclass
class ADDetailResult:
    detail_id: int
    account_ref_id: int
    dr_cr: str           # "Debit" | "Credit"
    value_name: str      # the AD value_name field (account code / group)
    fires: bool          # True if ALL conditions pass for this detail entry
    conditions: list[ConditionResult] = field(default_factory=list)
    skip_reason: str = ""  # set when fires=False due to a condition


@dataclass
class ValidationReport:
    pb_location_id: Optional[int]
    pb_supplier_type: Optional[str]
    entries_that_fire: list[ADDetailResult]
    entries_skipped: list[ADDetailResult]
    all_entries: list[ADDetailResult]


# ── Validator ─────────────────────────────────────────────────────────────────

class AccountingDefValidator:
    """
    Loads the Purchase Booking Accounting Definition once and evaluates
    its conditions against any number of PB payloads.
    """

    def __init__(self, client):
        self.client = client
        self._ad_details: list[dict] = []
        self._loaded = False

    def load(self) -> bool:
        """
        Discover and fetch the Purchase Booking Accounting Definition for this tenant.

        Queries the AD listing filtered by transaction_type=5 (Purchase Booking).
        Each tenant may have a different AD id — never hardcode it.
        """
        try:
            # List all ADs for this tenant and find the one for transaction_type 5
            resp = self.client.session.get(
                f"{self.client.BASE_URL}/core/accounting-definition/",
                params={"page_number": 1, "page_size": 100},
                timeout=15,
            )
            if resp.status_code != 200:
                logger.error("AD listing failed: HTTP %s", resp.status_code)
                return False

            listing = resp.json()
            if isinstance(listing, list):
                rows = listing
            else:
                rows = (
                    listing.get("results")
                    or listing.get("screenmatlistingdata_set")
                    or []
                )
            if not isinstance(rows, list):
                logger.error("Unexpected AD listing shape: %s", type(rows))
                return False

            pb_ad = next(
                (r for r in rows if str(r.get("transaction_type", "")) == _PB_TRANSACTION_TYPE),
                None,
            )
            if not pb_ad:
                logger.error(
                    "No Accounting Definition with transaction_type=%s found for this tenant",
                    _PB_TRANSACTION_TYPE,
                )
                return False

            ad_id = pb_ad.get("id")
            logger.info("Found PB AD: id=%s name=%s", ad_id, pb_ad.get("name"))

            # Fetch full detail
            resp2 = self.client.session.get(
                f"{self.client.BASE_URL}/core/accounting-definition/{ad_id}/",
                timeout=15,
            )
            if resp2.status_code != 200:
                logger.error("AD detail fetch failed: HTTP %s", resp2.status_code)
                return False

            data = resp2.json()
            self._ad_details = data.get("accounting_definition_detail") or []
            self._loaded = True
            logger.info(
                "AccountingDefValidator: loaded AD '%s' id=%s (%d entries)",
                data.get("name"),
                ad_id,
                len(self._ad_details),
            )
            return True
        except Exception as e:
            logger.error("AccountingDefValidator: load error: %s", e)
            return False

    # ── Condition evaluation ───────────────────────────────────────────────────

    def _get_payload_value(self, payload: dict, param_id: int) -> Any:
        """Extract the PB payload value that corresponds to an AD condition parameter."""
        if param_id not in _PARAM_TO_PAYLOAD:
            return None
        key, is_int = _PARAM_TO_PAYLOAD[param_id]
        raw = payload.get(key)
        if raw is None:
            return None
        if is_int:
            try:
                return int(raw)
            except (TypeError, ValueError):
                return raw
        return str(raw)

    def _eval_condition(self, cond: dict, payload: dict) -> ConditionResult:
        param_id = cond.get("parameter")
        operator = cond.get("operator")
        options  = cond.get("options") or []
        actual   = self._get_payload_value(payload, param_id)

        param_label = {5: "Type of Sale", 6: "Location"}.get(param_id, f"param{param_id}")

        if actual is None:
            # Can't evaluate — treat as not matching (conservative)
            passed = False
        elif operator == _OP_IN:
            # Cast options to same type as actual for fair comparison
            if isinstance(actual, int):
                passed = any(
                    _safe_int(o) == actual for o in options
                )
            else:
                passed = str(actual).strip() in [str(o).strip() for o in options]
        elif operator == _OP_NOT_IN:
            if isinstance(actual, int):
                passed = all(
                    _safe_int(o) != actual for o in options
                )
            else:
                passed = str(actual).strip() not in [str(o).strip() for o in options]
        else:
            # Unknown operator — skip (assume passes)
            passed = True

        return ConditionResult(
            parameter_id=param_id,
            param_label=param_label,
            operator=operator,
            options=options,
            passed=passed,
            actual_value=actual,
        )

    def _eval_detail(self, detail: dict, payload: dict) -> ADDetailResult:
        conditions_raw = detail.get("conditions") or []
        cond_results: list[ConditionResult] = []
        fires = True
        skip_reason = ""

        for cond in conditions_raw:
            result = self._eval_condition(cond, payload)
            cond_results.append(result)
            if not result.passed:
                fires = False
                op_label = "IN" if result.operator == _OP_IN else "NOT IN"
                skip_reason = (
                    f"{result.param_label} {op_label} {result.options} "
                    f"(actual: {result.actual_value!r})"
                )
                break  # AND semantics — short-circuit on first failure

        return ADDetailResult(
            detail_id=detail.get("id"),
            account_ref_id=detail.get("account_ref_id"),
            dr_cr=detail.get("dr_cr", ""),
            value_name=detail.get("value_name", ""),
            fires=fires,
            conditions=cond_results,
            skip_reason=skip_reason,
        )

    # ── AD-derived filter helpers ─────────────────────────────────────────────

    def valid_location_ids(self) -> set[int]:
        """
        Return the set of location IDs (parameter 6) that appear in at least
        one AD detail entry's conditions.

        Only these locations are guaranteed to trigger a debit entry.
        CBR data for any other location should be skipped.
        """
        if not self._loaded:
            raise RuntimeError("Call load() before valid_location_ids()")
        ids: set[int] = set()
        for detail in self._ad_details:
            for cond in (detail.get("conditions") or []):
                if cond.get("parameter") == 6 and cond.get("operator") == _OP_IN:
                    for o in (cond.get("options") or []):
                        v = _safe_int(o)
                        if v is not None:
                            ids.add(v)
        return ids

    def valid_supplier_types(self) -> set[str]:
        """
        Return the set of supplier_ref_type strings ("Supplier", "Farmer", …)
        that appear in at least one AD detail entry's conditions.

        Only these types are guaranteed to trigger a debit entry.
        """
        if not self._loaded:
            raise RuntimeError("Call load() before valid_supplier_types()")
        types: set[str] = set()
        for detail in self._ad_details:
            for cond in (detail.get("conditions") or []):
                if cond.get("parameter") == 5 and cond.get("operator") == _OP_IN:
                    for o in (cond.get("options") or []):
                        types.add(str(o).strip())
        return types

    def has_unconditional_debit(self) -> bool:
        """True if at least one Debit entry has no conditions (fires for any PB)."""
        if not self._loaded:
            raise RuntimeError("Call load() before has_unconditional_debit()")
        return any(
            d.get("dr_cr") == "Debit" and not d.get("conditions")
            for d in self._ad_details
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def validate(self, payload: dict) -> ValidationReport:
        """
        Evaluate all AD detail entries against `payload`.

        `payload` is the dict passed to api.create_pb() — it must have
        `parameter6` (int location ID) and `supplier_ref_type` (str).
        """
        if not self._loaded:
            raise RuntimeError("Call load() before validate()")

        all_results = [self._eval_detail(d, payload) for d in self._ad_details]
        fires   = [r for r in all_results if r.fires]
        skipped = [r for r in all_results if not r.fires]

        return ValidationReport(
            pb_location_id=_safe_int(payload.get("parameter6")),
            pb_supplier_type=payload.get("supplier_ref_type"),
            entries_that_fire=fires,
            entries_skipped=skipped,
            all_entries=all_results,
        )

    def print_report(self, report: ValidationReport, pb_ref: str = "") -> None:
        """Pretty-print the validation report to stdout."""
        sep = "-" * 60
        label = f" [{pb_ref}]" if pb_ref else ""
        print(f"\n{sep}")
        print(f"  AD Validation{label}")
        print(f"  Location ID: {report.pb_location_id}  |  Supplier type: {report.pb_supplier_type}")
        print(sep)

        print(f"  WILL FIRE ({len(report.entries_that_fire)} entries):")
        for r in report.entries_that_fire:
            cond_summary = ", ".join(
                f"{c.param_label} {'IN' if c.operator==_OP_IN else 'NOT IN'} {c.options}"
                for c in r.conditions
            ) or "always"
            print(f"    [{r.dr_cr[:2].upper()}] acct={r.account_ref_id}  value={r.value_name}  cond: {cond_summary}")

        if report.entries_skipped:
            print(f"\n  SKIPPED ({len(report.entries_skipped)} entries):")
            for r in report.entries_skipped:
                print(f"    [{r.dr_cr[:2].upper()}] acct={r.account_ref_id}  FAIL: {r.skip_reason}")

        print(sep)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_int(v) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
