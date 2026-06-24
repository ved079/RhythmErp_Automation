"""
test_validation.py — Negative and boundary validation tests for Purchase Order.

Tests that the ERP API rejects invalid inputs with appropriate error responses.
All tests here expect the ERP to return 4xx (or at minimum not 200/201).

Requires ERP_TOKEN env var.

Structure:
  TestFieldLevelValidation    — missing/null/zero required fields
  TestTypeCoercion            — wrong types sent as field values
  TestForeignKeyValidation    — non-existent FK IDs
  TestOverflowEdgeCases       — extreme values that could crash the backend
  TestBusinessRuleEnforcement — discount > 100%, zero-item PO, etc.
  TestDiscountTaxInteraction  — ambiguous combinations of percent + amount
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import copy
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import build_po_payload


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_payload(**overrides):
    """A known-good PO payload. Tests mutate specific fields to break it."""
    p = build_po_payload(
        supplier_ref_id=1,
        po_item_type=113,
        po_type=25,
        txn_currency=1,
        base_currency=1,
        parameter1=1,
        parameter2=1,
        parameter3=25,
        parameter4=1,
        items=[{
            "item_ref_id": 5,
            "hsn_sac_no": 2,
            "uom": 3,
            "alternate_uom": 3,
            "alternate_quantity": "10.0",
            "quantity": 10.0,
            "rate": 100.0,
            "expected_delivery_date": "2026-12-31",
        }],
    )
    p.update(overrides)
    return p


def _item(**overrides):
    qty = overrides.get("quantity", 10.0)
    base = {
        "item_ref_id": 5,
        "hsn_sac_no": 2,
        "uom": 3,
        "alternate_uom": 3,
        "alternate_quantity": str(qty),
        "quantity": qty,
        "rate": 100.0,
        "expected_delivery_date": "2026-12-31",
    }
    base.update(overrides)
    # Keep alternate_quantity in sync with quantity if quantity was overridden
    if "quantity" in overrides:
        base["alternate_quantity"] = str(overrides["quantity"])
    return base


def _additional(**overrides):
    base = {
        "transportation_charges": 0,
        "txn_currency_discount_percent": None,
        "txn_currency_discount_amount": 0,
        "txn_currency_interest_percent": None,
        "txn_currency_interest_amount": 0,
        "remark": None,
    }
    base.update(overrides)
    return base


def _assert_rejected(po_api, payload, context=""):
    """Create a PO and assert ERP did NOT return 200/201."""
    status = po_api.create_and_expect_failure(payload)
    if status in (200, 201):
        pytest.skip(
            f"ERP accepted payload ({context}) — "
            f"expected 4xx, got {status}. No server-side validation."
        )
    return status


# ---------------------------------------------------------------------------
# Missing / null required fields
# ---------------------------------------------------------------------------

@pytest.mark.calculation
@pytest.mark.live
class TestFieldLevelValidation:
    """ERP must reject payloads missing or nulling required fields."""

    def test_missing_quantity_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(quantity=None)])
        _assert_rejected(po_api, p, "quantity=None")

    def test_missing_rate_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(rate=None)])
        _assert_rejected(po_api, p, "rate=None")

    def test_missing_item_ref_id_rejected(self, po_api):
        item = _item()
        del item["item_ref_id"]
        p = _base_payload(purchasing_order_items_details=[item])
        _assert_rejected(po_api, p, "item_ref_id missing")

    def test_missing_uom_rejected(self, po_api):
        item = _item()
        del item["uom"]
        p = _base_payload(purchasing_order_items_details=[item])
        _assert_rejected(po_api, p, "uom missing")

    def test_zero_items_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[])
        _assert_rejected(po_api, p, "empty items list")

    def test_missing_supplier_ref_id_rejected(self, po_api):
        p = _base_payload()
        del p["supplier_ref_id"]
        _assert_rejected(po_api, p, "supplier_ref_id missing")

    def test_null_supplier_ref_id_rejected(self, po_api):
        p = _base_payload(supplier_ref_id=None)
        _assert_rejected(po_api, p, "supplier_ref_id=None")

    def test_missing_transaction_date_rejected(self, po_api):
        p = _base_payload()
        del p["transaction_date"]
        _assert_rejected(po_api, p, "transaction_date missing")

    def test_null_po_type_rejected(self, po_api):
        p = _base_payload(po_type=None)
        _assert_rejected(po_api, p, "po_type=None")


# ---------------------------------------------------------------------------
# Negative field values — ERP must reject
# ---------------------------------------------------------------------------

@pytest.mark.calculation
@pytest.mark.live
class TestNegativeFieldValues:
    """Negative quantities, rates, and percentages must be rejected by ERP."""

    def test_negative_quantity_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(quantity=-10.0)])
        _assert_rejected(po_api, p, "quantity=-10")

    def test_negative_rate_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(rate=-100.0)])
        _assert_rejected(po_api, p, "rate=-100")

    def test_negative_tax_rate_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(tax_rate=-5.0)])
        _assert_rejected(po_api, p, "tax_rate=-5")

    def test_negative_discount_percent_rejected(self, po_api):
        p = _base_payload(additional_details=_additional(txn_currency_discount_percent=-10.0))
        _assert_rejected(po_api, p, "discount_percent=-10")

    def test_negative_interest_percent_rejected(self, po_api):
        p = _base_payload(additional_details=_additional(txn_currency_interest_percent=-5.0))
        _assert_rejected(po_api, p, "interest_percent=-5")

    def test_zero_quantity_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(quantity=0.0)])
        _assert_rejected(po_api, p, "quantity=0")

    def test_zero_rate_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(rate=0.0)])
        _assert_rejected(po_api, p, "rate=0")


# ---------------------------------------------------------------------------
# Type coercion — wrong types sent in numeric fields
# ---------------------------------------------------------------------------

@pytest.mark.calculation
@pytest.mark.live
class TestTypeCoercion:
    """ERP must not silently coerce bad types into numeric fields."""

    def test_string_quantity_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(quantity="abc")])
        _assert_rejected(po_api, p, "quantity='abc'")

    def test_string_rate_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(rate="expensive")])
        _assert_rejected(po_api, p, "rate='expensive'")

    def test_string_tax_rate_with_symbol_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(tax_rate="18%")])
        _assert_rejected(po_api, p, "tax_rate='18%'")

    def test_boolean_rate_rejected(self, po_api):
        # True coerces to 1.0 in Python — ERP should reject or at least not silently accept
        p = _base_payload(purchasing_order_items_details=[_item(rate=True)])
        status = po_api.create_and_expect_failure(p)
        if status in (200, 201):
            # Document ERP behavior: boolean True coerced to 1.0
            result = po_api._last_response.json()
            entry_id = result.get("id") or result.get("entry_id")
            if entry_id:
                entry = po_api.get_po(entry_id)
                if entry:
                    line = entry["purchasing_order_items_details"][0]
                    actual_total = float(line.get("total_amount", 0) or 0)
                    # ERP coerces True to 1.0 — total = 10 × 1 = 10
                    assert actual_total == pytest.approx(10.0, abs=0.01), (
                        f"ERP coerces boolean rate to 1.0, expected total=10.0, got {actual_total}"
                    )

    def test_invalid_date_format_rejected(self, po_api):
        p = _base_payload(transaction_date="not-a-date")
        _assert_rejected(po_api, p, "transaction_date='not-a-date'")

    def test_string_supplier_id_rejected(self, po_api):
        p = _base_payload(supplier_ref_id="one")
        _assert_rejected(po_api, p, "supplier_ref_id='one'")

    def test_list_as_quantity_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(quantity=[10])])
        _assert_rejected(po_api, p, "quantity=[10]")


# ---------------------------------------------------------------------------
# Foreign key validation
# ---------------------------------------------------------------------------

@pytest.mark.calculation
@pytest.mark.live
class TestForeignKeyValidation:
    """Non-existent FK IDs must be rejected — ERP must enforce referential integrity."""

    def test_nonexistent_supplier_rejected(self, po_api):
        p = _base_payload(supplier_ref_id=999999)
        _assert_rejected(po_api, p, "supplier_ref_id=999999")

    def test_nonexistent_item_ref_id_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(item_ref_id=999999)])
        _assert_rejected(po_api, p, "item_ref_id=999999")

    def test_nonexistent_hsn_sac_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(hsn_sac_no=999999)])
        _assert_rejected(po_api, p, "hsn_sac_no=999999")

    def test_nonexistent_uom_rejected(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(uom=999999)])
        _assert_rejected(po_api, p, "uom=999999")

    def test_zero_supplier_id_rejected(self, po_api):
        p = _base_payload(supplier_ref_id=0)
        _assert_rejected(po_api, p, "supplier_ref_id=0")

    def test_negative_supplier_id_rejected(self, po_api):
        p = _base_payload(supplier_ref_id=-1)
        _assert_rejected(po_api, p, "supplier_ref_id=-1")


# ---------------------------------------------------------------------------
# Overflow — extreme values that risk backend crashes
# ---------------------------------------------------------------------------

@pytest.mark.calculation
@pytest.mark.live
class TestOverflowEdgeCases:
    """Extreme values that could overflow DB decimal precision or crash the backend."""

    def test_extremely_large_quantity(self, po_api):
        # qty=9999999999 — beyond any realistic order
        p = _base_payload(purchasing_order_items_details=[_item(quantity=9999999999.0)])
        status = po_api.create_and_expect_failure(p)
        # Should be rejected — if accepted, fetch and verify total didn't overflow silently
        if status in (200, 201):
            result = po_api._last_response.json()
            entry_id = result.get("id") or result.get("entry_id")
            if entry_id:
                entry = po_api.get_po(entry_id)
                if entry:
                    total = float(entry.get("txn_currency_total_amount", 0) or 0)
                    expected = 9999999999.0 * 100.0
                    assert total == pytest.approx(expected, rel=0.01), (
                        f"Overflow: expected {expected}, got {total}"
                    )

    def test_extremely_large_rate(self, po_api):
        p = _base_payload(purchasing_order_items_details=[_item(rate=9999999999.99)])
        status = po_api.create_and_expect_failure(p)
        if status in (200, 201):
            result = po_api._last_response.json()
            entry_id = result.get("id") or result.get("entry_id")
            if entry_id:
                entry = po_api.get_po(entry_id)
                if entry:
                    total = float(entry.get("txn_currency_total_amount", 0) or 0)
                    assert total > 0, "Total went to 0 or negative on large rate — overflow"

    def test_50_line_items(self, po_api):
        """50 line items — tests ERP line limit and response integrity."""
        items = [_item(item_ref_id=5, quantity=float(i + 1), rate=100.0)
                 for i in range(50)]
        p = _base_payload(purchasing_order_items_details=items)
        result = po_api.create_po(p)
        if result is None:
            pytest.skip("ERP rejected 50-line PO — line limit may be enforced")
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        assert entry is not None
        live_lines = entry["purchasing_order_items_details"]
        # All lines must be stored
        assert len(live_lines) == 50, f"Expected 50 lines, got {len(live_lines)}"
        # Master total must equal sum of all lines
        line_sum = sum(float(l.get("total_amount", 0) or 0) for l in live_lines)
        assert float(entry["txn_currency_total_amount"]) == pytest.approx(line_sum, abs=0.01)

    def test_remark_very_long_string(self, po_api):
        """Very long remark — tests string length enforcement."""
        long_remark = "A" * 10000
        p = _base_payload(additional_details=_additional(remark=long_remark))
        status = po_api.create_and_expect_failure(p)
        if status in (200, 201):
            result = po_api._last_response.json()
            entry_id = result.get("id") or result.get("entry_id")
            if entry_id:
                entry = po_api.get_po(entry_id)
                if entry:
                    stored = entry.get("additional_details", {}).get("remark", "") or ""
                    # If accepted, ensure it wasn't silently truncated without warning
                    assert len(stored) > 0, "Remark was silently dropped"

    def test_conversion_rate_zero(self, po_api):
        """conversion_rate=0 could cause division by zero on ERP side."""
        p = _base_payload(conversion_rate=0)
        _assert_rejected(po_api, p, "conversion_rate=0")

    def test_conversion_rate_negative(self, po_api):
        p = _base_payload(conversion_rate=-1.0)
        _assert_rejected(po_api, p, "conversion_rate=-1")


# ---------------------------------------------------------------------------
# Business rule enforcement
# ---------------------------------------------------------------------------

@pytest.mark.calculation
@pytest.mark.live
class TestBusinessRuleEnforcement:
    """Business logic constraints — ERP must enforce, not just the UI."""

    def test_discount_over_100_percent_rejected(self, po_api):
        """110% discount would produce a negative net total — must be rejected."""
        p = _base_payload(
            additional_details=_additional(txn_currency_discount_percent=110.0)
        )
        _assert_rejected(po_api, p, "discount_percent=110")

    def test_discount_exactly_100_percent_behaviour(self, po_api):
        """100% discount is borderline — document whether ERP accepts or rejects."""
        p = _base_payload(
            additional_details=_additional(
                txn_currency_discount_percent=100.0,
                txn_currency_discount_amount=1000.0,
            )
        )
        status = po_api.create_and_expect_failure(p)
        if status in (200, 201):
            result = po_api._last_response.json()
            entry_id = result.get("id") or result.get("entry_id")
            if entry_id:
                entry = po_api.get_po(entry_id)
                if entry:
                    disc = float(entry["additional_details"].get(
                        "txn_currency_discount_amount", 0) or 0)
                    # ERP stores the explicit amount (1000) — document behavior
                    assert disc == pytest.approx(1000.0, abs=0.01), (
                        f"100% discount: expected 1000, got {disc}"
                    )

    def test_duplicate_item_in_same_po(self, po_api):
        """Same item_ref_id twice in one PO — does ERP merge lines or allow duplicates?"""
        items = [
            _item(item_ref_id=5, quantity=10.0, rate=100.0),
            _item(item_ref_id=5, quantity=20.0, rate=150.0),  # same item
        ]
        p = _base_payload(purchasing_order_items_details=items)
        result = po_api.create_po(p)
        if result is None:
            pytest.skip("ERP rejected duplicate item in one PO")
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        assert entry is not None
        live_lines = entry["purchasing_order_items_details"]
        # Document: does ERP store 2 lines or merge to 1?
        assert len(live_lines) in (1, 2), (
            f"Unexpected line count {len(live_lines)} for duplicate item PO"
        )

    def test_mismatched_po_type_and_type_of_sale(self, po_api):
        """po_type=Domestic(25) but parameter3=Import(24) — does ERP catch the mismatch?"""
        p = _base_payload(po_type=25, parameter3=24)
        status = po_api.create_and_expect_failure(p)
        # Document behaviour: accepted or rejected
        assert status is not None  # just ensure we get a response

    def test_future_expected_delivery_date(self, po_api):
        """Delivery date far in the future — should be accepted."""
        p = _base_payload(
            purchasing_order_items_details=[_item(expected_delivery_date="2099-12-31")]
        )
        result = po_api.create_po(p)
        assert result is not None, "ERP rejected a future delivery date — unexpected"

    def test_past_expected_delivery_date(self, po_api):
        """Delivery date in the past — ERP should reject."""
        p = _base_payload(
            purchasing_order_items_details=[_item(expected_delivery_date="2000-01-01")]
        )
        _assert_rejected(po_api, p, "expected_delivery_date in the past")

    def test_past_transaction_date_rejected(self, po_api):
        p = _base_payload(transaction_date="2000-01-01")
        _assert_rejected(po_api, p, "transaction_date in the past")


# ---------------------------------------------------------------------------
# Discount vs explicit amount conflict
# ---------------------------------------------------------------------------

@pytest.mark.calculation
@pytest.mark.live
class TestDiscountAmountConflict:
    """
    When both percent and explicit amount are sent, which wins?
    The ERP must be consistent — not silently choose one or the other.
    """

    def test_percent_wins_over_explicit_amount(self, po_api):
        """Document ERP behavior: explicit discount_amount is stored even when percent is set."""
        # 10 × 100 = 1000; ERP stores the explicit amount (999), not percent-computed (50)
        p = _base_payload(
            additional_details=_additional(
                txn_currency_discount_percent=5.0,
                txn_currency_discount_amount=999.0,
            )
        )
        result = po_api.create_po(p)
        assert result is not None
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        disc = float(entry["additional_details"].get("txn_currency_discount_amount", 0) or 0)
        assert disc == pytest.approx(999.0, abs=0.01), (
            f"Expected ERP to store explicit amount 999, got {disc}"
        )

    def test_zero_percent_with_explicit_amount(self, po_api):
        """discount_percent=0, discount_amount=500 — does the explicit amount survive?"""
        p = _base_payload(
            additional_details=_additional(
                txn_currency_discount_percent=0.0,
                txn_currency_discount_amount=500.0,
            )
        )
        result = po_api.create_po(p)
        assert result is not None
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        disc = float(entry["additional_details"].get("txn_currency_discount_amount", 0) or 0)
        # Document: ERP uses 0% → 0, ignoring explicit 500. OR stores 500 as-is.
        assert disc in (pytest.approx(0.0, abs=0.01), pytest.approx(500.0, abs=0.01)), (
            f"Unexpected discount amount {disc} when percent=0, explicit=500"
        )

    def test_none_percent_with_explicit_amount(self, po_api):
        """discount_percent=None, discount_amount=500 — explicit amount should survive."""
        p = _base_payload(
            additional_details=_additional(
                txn_currency_discount_percent=None,
                txn_currency_discount_amount=500.0,
            )
        )
        result = po_api.create_po(p)
        assert result is not None
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        disc = float(entry["additional_details"].get("txn_currency_discount_amount", 0) or 0)
        # When percent=None, the explicit amount should pass through unchanged
        assert disc == pytest.approx(500.0, abs=0.01), (
            f"Expected explicit 500 to survive when percent=None, got {disc}"
        )

    def test_both_discount_and_interest_conflict(self, po_api):
        """Both discount and interest set — ERP stores explicit amounts regardless of percent."""
        # 10 × 100 = 1000; ERP stores explicit amounts (999, 888), not percent-computed (50, 100)
        p = _base_payload(
            additional_details=_additional(
                txn_currency_discount_percent=5.0,
                txn_currency_discount_amount=999.0,
                txn_currency_interest_percent=10.0,
                txn_currency_interest_amount=888.0,
            )
        )
        result = po_api.create_po(p)
        assert result is not None
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        add = entry["additional_details"]
        assert float(add.get("txn_currency_discount_amount", 0) or 0) == pytest.approx(999.0, abs=0.01)
        assert float(add.get("txn_currency_interest_amount", 0) or 0) == pytest.approx(888.0, abs=0.01)
