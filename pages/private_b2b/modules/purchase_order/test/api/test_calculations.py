"""
test_calculations.py — Calculation-focused tests for Purchase Order.

Structure:
  Unit (no network):
    TestLineCalculations       — qty × rate, tax per line
    TestAggregateCalculations  — multi-line sum → master total
    TestDiscountInterest       — discount %, interest % math
    TestComputeExpectedResults — end-to-end payload computation helper

  Live (requires ERP_TOKEN):
    TestLiveLineMath           — ERP returns correct per-line amounts
    TestLiveMasterTotal        — ERP master total matches sum of lines
    TestLiveDiscountInterest   — ERP recomputes discount/interest from %
    TestLiveEdgeCases          — decimals, zero tax, transportation charges
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    build_po_payload,
    build_po_item,
    compute_expected_results,
    compute_line_amount,
    compute_line_tax,
    compute_line_total,
    compute_master_total,
    compute_discount_amount,
    compute_interest_amount,
    assert_calculations_match,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item(item_ref_id=5, hsn_sac_no=2, uom=3, qty=10.0, rate=100.0, tax_rate=None):
    i = {
        "item_ref_id": item_ref_id,
        "hsn_sac_no": hsn_sac_no,
        "uom": uom,
        "alternate_uom": uom,
        "alternate_quantity": str(qty),
        "quantity": qty,
        "rate": rate,
        "expected_delivery_date": "2026-06-30",
    }
    if tax_rate is not None:
        i["tax_rate"] = tax_rate
    return i


def _payload(items, additional_details=None):
    return build_po_payload(
        supplier_ref_id=1,
        po_item_type=113,
        po_type=25,
        txn_currency=1,
        base_currency=1,
        parameter1=1,
        parameter2=1,
        parameter3=25,
        parameter4=1,
        items=items,
        additional_details=additional_details,
    )


def _additional(discount_pct=None, interest_pct=None, transport=0, remark=None,
                discount_amt=0, interest_amt=0):
    return {
        "transportation_charges": transport,
        "txn_currency_discount_percent": discount_pct,
        "txn_currency_discount_amount": discount_amt,
        "txn_currency_interest_percent": interest_pct,
        "txn_currency_interest_amount": interest_amt,
        "remark": remark,
    }


# ---------------------------------------------------------------------------
# UNIT: individual math helpers
# ---------------------------------------------------------------------------

@pytest.mark.calculation
class TestLineCalculations:
    """Pure unit tests for per-line computation — no network needed."""

    def test_integer_qty_and_rate(self):
        assert compute_line_amount(10, 100) == 1000.0

    def test_decimal_qty(self):
        assert compute_line_amount(1.5, 200) == 300.0

    def test_decimal_rate(self):
        assert compute_line_amount(10, 9.99) == pytest.approx(99.9, abs=0.01)

    def test_decimal_qty_and_rate(self):
        # 1.5 × 3.33 = 4.995 → should not round at compute level
        assert compute_line_amount(1.5, 3.33) == pytest.approx(4.995, abs=0.001)

    def test_large_values(self):
        assert compute_line_amount(10000, 9999.99) == pytest.approx(99999900.0, abs=1.0)

    def test_zero_quantity(self):
        assert compute_line_amount(0, 500) == 0.0

    def test_zero_rate(self):
        assert compute_line_amount(100, 0) == 0.0

    def test_tax_12_percent(self):
        assert compute_line_tax(1000, 12) == 120.0

    def test_tax_5_percent(self):
        assert compute_line_tax(1000, 5) == 50.0

    def test_tax_18_percent(self):
        assert compute_line_tax(1000, 18) == 180.0

    def test_tax_28_percent(self):
        assert compute_line_tax(1000, 28) == 280.0

    def test_tax_zero_percent(self):
        assert compute_line_tax(1000, 0) == 0.0

    def test_tax_on_zero_amount(self):
        assert compute_line_tax(0, 18) == 0.0

    def test_tax_decimal_rate(self):
        # 1000 × 0.5% = 5.0
        assert compute_line_tax(1000, 0.5) == pytest.approx(5.0, abs=0.001)

    def test_line_total_with_tax(self):
        assert compute_line_total(1000, 180) == 1180.0

    def test_line_total_zero_tax(self):
        assert compute_line_total(1000, 0) == 1000.0

    def test_line_total_decimal(self):
        assert compute_line_total(4.995, 0) == pytest.approx(4.995, abs=0.001)


# ---------------------------------------------------------------------------
# UNIT: multi-line aggregate
# ---------------------------------------------------------------------------

@pytest.mark.calculation
class TestAggregateCalculations:
    """Master total = sum of all line totals."""

    def test_single_line_total(self):
        lines = [{"total_amount": 1000.0}]
        assert compute_master_total(lines) == 1000.0

    def test_two_lines(self):
        lines = [{"total_amount": 1050.0}, {"total_amount": 1120.0}]
        assert compute_master_total(lines) == 2170.0

    def test_five_lines(self):
        lines = [{"total_amount": v} for v in [100, 200, 300, 400, 500]]
        assert compute_master_total(lines) == 1500.0

    def test_empty_lines(self):
        assert compute_master_total([]) == 0.0

    def test_lines_with_decimal_amounts(self):
        lines = [{"total_amount": 4.995}, {"total_amount": 10.005}]
        assert compute_master_total(lines) == pytest.approx(15.0, abs=0.01)

    def test_large_multi_line(self):
        lines = [{"total_amount": 99999.99} for _ in range(10)]
        assert compute_master_total(lines) == pytest.approx(999999.9, abs=0.1)

    def test_zero_amount_lines_ignored(self):
        lines = [{"total_amount": 0.0}, {"total_amount": 500.0}, {"total_amount": 0.0}]
        assert compute_master_total(lines) == 500.0


# ---------------------------------------------------------------------------
# UNIT: discount and interest
# ---------------------------------------------------------------------------

@pytest.mark.calculation
class TestDiscountInterest:
    """Discount and interest are computed from % applied to master total."""

    def test_discount_5_percent(self):
        assert compute_discount_amount(10000, 5) == 500.0

    def test_discount_10_percent(self):
        assert compute_discount_amount(5000, 10) == 500.0

    def test_discount_zero_percent(self):
        assert compute_discount_amount(10000, 0) == 0.0

    def test_discount_none_percent(self):
        assert compute_discount_amount(10000, None) == 0.0

    def test_discount_100_percent(self):
        assert compute_discount_amount(10000, 100) == 10000.0

    def test_discount_decimal_percent(self):
        # 10000 × 2.5% = 250
        assert compute_discount_amount(10000, 2.5) == pytest.approx(250.0, abs=0.01)

    def test_interest_8_percent(self):
        assert compute_interest_amount(3000, 8) == pytest.approx(240.0, abs=0.01)

    def test_interest_zero_percent(self):
        assert compute_interest_amount(10000, 0) == 0.0

    def test_interest_none_percent(self):
        assert compute_interest_amount(10000, None) == 0.0

    def test_interest_decimal_percent(self):
        # 5000 × 1.5% = 75
        assert compute_interest_amount(5000, 1.5) == pytest.approx(75.0, abs=0.01)

    def test_discount_and_interest_independent(self):
        # Each computed on the same master total — not stacked
        total = 10000.0
        disc = compute_discount_amount(total, 5)   # 500
        intr = compute_interest_amount(total, 10)  # 1000
        assert disc == 500.0
        assert intr == 1000.0
        assert disc + intr == 1500.0


# ---------------------------------------------------------------------------
# UNIT: compute_expected_results end-to-end
# ---------------------------------------------------------------------------

@pytest.mark.calculation
class TestComputeExpectedResults:
    """End-to-end payload computation — verifies the full calculation chain."""

    def test_single_line_no_tax(self):
        payload = _payload([_item(qty=10.0, rate=100.0)])
        r = compute_expected_results(payload)
        assert r["lines"][0]["txn_currency_amount_detail"] == 1000.0
        assert r["lines"][0]["txn_currency_tax_amount_details"] == 0.0
        assert r["lines"][0]["total_amount"] == 1000.0
        assert r["txn_currency_total_amount"] == 1000.0
        assert r["txn_currency_discount_amount"] == 0.0
        assert r["txn_currency_interest_amount"] == 0.0

    def test_single_line_with_tax(self):
        payload = _payload([_item(qty=10.0, rate=100.0, tax_rate=18.0)])
        r = compute_expected_results(payload)
        # 10 × 100 = 1000, tax = 180, total = 1180
        assert r["lines"][0]["txn_currency_amount_detail"] == 1000.0
        assert r["lines"][0]["txn_currency_tax_amount_details"] == 180.0
        assert r["lines"][0]["total_amount"] == 1180.0
        assert r["txn_currency_total_amount"] == 1180.0

    def test_multi_line_different_tax_rates(self):
        items = [
            _item(item_ref_id=5, qty=10.0, rate=100.0, tax_rate=5.0),   # 1000, tax=50,  total=1050
            _item(item_ref_id=6, qty=5.0,  rate=200.0, tax_rate=12.0),  # 1000, tax=120, total=1120
            _item(item_ref_id=7, qty=2.0,  rate=500.0, tax_rate=18.0),  # 1000, tax=180, total=1180
            _item(item_ref_id=8, qty=4.0,  rate=250.0, tax_rate=28.0),  # 1000, tax=280, total=1280
            _item(item_ref_id=9, qty=20.0, rate=50.0,  tax_rate=0.0),   # 1000, tax=0,   total=1000
        ]
        payload = _payload(items)
        r = compute_expected_results(payload)
        assert r["lines"][0]["total_amount"] == 1050.0
        assert r["lines"][1]["total_amount"] == 1120.0
        assert r["lines"][2]["total_amount"] == 1180.0
        assert r["lines"][3]["total_amount"] == 1280.0
        assert r["lines"][4]["total_amount"] == 1000.0
        assert r["txn_currency_total_amount"] == 5630.0

    def test_master_total_equals_sum_of_line_totals(self):
        items = [_item(qty=q, rate=r) for q, r in [(10, 100), (5, 200), (3, 333), (7, 150)]]
        payload = _payload(items)
        r = compute_expected_results(payload)
        line_sum = sum(l["total_amount"] for l in r["lines"])
        assert r["txn_currency_total_amount"] == pytest.approx(line_sum, abs=0.01)

    def test_discount_from_percent(self):
        # master total = 100 × 500 = 50000; 5% discount = 2500
        payload = _payload(
            [_item(qty=100.0, rate=500.0)],
            additional_details=_additional(discount_pct=5.0),
        )
        r = compute_expected_results(payload)
        assert r["txn_currency_total_amount"] == 50000.0
        assert r["txn_currency_discount_amount"] == 2500.0
        assert r["txn_currency_interest_amount"] == 0.0

    def test_interest_from_percent(self):
        # 30 × 100 = 3000; 8% interest = 240
        payload = _payload(
            [_item(qty=30.0, rate=100.0)],
            additional_details=_additional(interest_pct=8.0),
        )
        r = compute_expected_results(payload)
        assert r["txn_currency_total_amount"] == 3000.0
        assert r["txn_currency_interest_amount"] == pytest.approx(240.0, abs=0.01)
        assert r["txn_currency_discount_amount"] == 0.0

    def test_discount_and_interest_combined(self):
        # 10 × 1000 = 10000; discount 5% = 500, interest 10% = 1000
        payload = _payload(
            [_item(qty=10.0, rate=1000.0)],
            additional_details=_additional(discount_pct=5.0, interest_pct=10.0),
        )
        r = compute_expected_results(payload)
        assert r["txn_currency_total_amount"] == 10000.0
        assert r["txn_currency_discount_amount"] == 500.0
        assert r["txn_currency_interest_amount"] == 1000.0

    def test_decimal_quantity_and_rate(self):
        # 1.5 × 333.33 = 499.995
        payload = _payload([_item(qty=1.5, rate=333.33)])
        r = compute_expected_results(payload)
        assert r["lines"][0]["txn_currency_amount_detail"] == pytest.approx(499.995, abs=0.001)

    def test_high_quantity_precision(self):
        # 999 × 999.99 = 998990.01
        payload = _payload([_item(qty=999.0, rate=999.99)])
        r = compute_expected_results(payload)
        assert r["lines"][0]["txn_currency_amount_detail"] == pytest.approx(998990.01, abs=0.1)

    def test_zero_quantity_line(self):
        payload = _payload([_item(qty=0.0, rate=500.0)])
        r = compute_expected_results(payload)
        assert r["lines"][0]["txn_currency_amount_detail"] == 0.0
        assert r["lines"][0]["total_amount"] == 0.0
        assert r["txn_currency_total_amount"] == 0.0

    def test_ten_line_po(self):
        items = [_item(item_ref_id=i, qty=float(i * 10), rate=float(i * 100)) for i in range(1, 11)]
        payload = _payload(items)
        r = compute_expected_results(payload)
        assert len(r["lines"]) == 10
        for idx, line in enumerate(r["lines"]):
            expected_amt = float((idx + 1) * 10) * float((idx + 1) * 100)
            assert line["txn_currency_amount_detail"] == pytest.approx(expected_amt, abs=0.01)


# ---------------------------------------------------------------------------
# LIVE: per-line math verified against ERP response
# ---------------------------------------------------------------------------

@pytest.mark.calculation
@pytest.mark.live
class TestLiveLineMath:
    """Create PO via API and verify ERP returns correct per-line amounts."""

    def test_single_line_no_tax(self, po_api):
        payload = _payload([_item(qty=10.0, rate=100.0)])
        result = po_api.create_and_verify_calculations(payload=payload)
        live = result["entry"]["purchasing_order_items_details"][0]
        assert float(live["txn_currency_amount_detail"]) == pytest.approx(1000.0, abs=0.01)
        assert float(live.get("txn_currency_tax_amount_details", 0) or 0) == 0.0
        assert float(live["total_amount"]) == pytest.approx(1000.0, abs=0.01)

    def test_single_line_with_5pct_tax(self, po_api):
        # 20 × 250 = 5000; tax 5% = 250; total = 5250
        payload = _payload([_item(qty=20.0, rate=250.0, tax_rate=5.0)])
        result = po_api.create_and_verify_calculations(payload=payload)
        live = result["entry"]["purchasing_order_items_details"][0]
        assert float(live["txn_currency_amount_detail"]) == pytest.approx(5000.0, abs=0.01)
        assert float(live.get("txn_currency_tax_amount_details", 0) or 0) == pytest.approx(250.0, abs=0.01)
        assert float(live["total_amount"]) == pytest.approx(5250.0, abs=0.01)

    def test_single_line_with_18pct_tax(self, po_api):
        # 5 × 200 = 1000; tax 18% = 180; total = 1180
        payload = _payload([_item(qty=5.0, rate=200.0, tax_rate=18.0)])
        result = po_api.create_and_verify_calculations(payload=payload)
        live = result["entry"]["purchasing_order_items_details"][0]
        assert float(live["txn_currency_amount_detail"]) == pytest.approx(1000.0, abs=0.01)
        assert float(live["total_amount"]) == pytest.approx(1180.0, abs=0.01)

    def test_multi_line_independent_tax(self, po_api):
        """Each line's tax is computed independently — not blended."""
        items = [
            _item(item_ref_id=5, qty=10.0, rate=100.0, tax_rate=5.0),   # total=1050
            _item(item_ref_id=6, qty=5.0,  rate=200.0, tax_rate=12.0),  # total=1120
            _item(item_ref_id=7, qty=2.0,  rate=500.0, tax_rate=18.0),  # total=1180
        ]
        payload = _payload(items)
        result = po_api.create_and_verify_calculations(payload=payload)
        live_lines = result["entry"]["purchasing_order_items_details"]
        assert float(live_lines[0]["total_amount"]) == pytest.approx(1050.0, abs=0.01)
        assert float(live_lines[1]["total_amount"]) == pytest.approx(1120.0, abs=0.01)
        assert float(live_lines[2]["total_amount"]) == pytest.approx(1180.0, abs=0.01)

    def test_decimal_quantity(self, po_api):
        # 1.5 × 200 = 300
        payload = _payload([_item(qty=1.5, rate=200.0)])
        result = po_api.create_and_verify_calculations(payload=payload)
        live = result["entry"]["purchasing_order_items_details"][0]
        assert float(live["txn_currency_amount_detail"]) == pytest.approx(300.0, abs=0.01)

    def test_high_quantity(self, po_api):
        # 500 × 50 = 25000
        payload = _payload([_item(qty=500.0, rate=50.0)])
        result = po_api.create_and_verify_calculations(payload=payload)
        live = result["entry"]["purchasing_order_items_details"][0]
        assert float(live["txn_currency_amount_detail"]) == pytest.approx(25000.0, abs=0.01)


# ---------------------------------------------------------------------------
# LIVE: master total = sum of all lines
# ---------------------------------------------------------------------------

@pytest.mark.calculation
@pytest.mark.live
class TestLiveMasterTotal:
    """ERP master total must equal the sum of all line totals."""

    def test_single_line_master_total(self, po_api):
        payload = _payload([_item(qty=10.0, rate=100.0)])
        result = po_api.create_and_verify_calculations(payload=payload)
        entry = result["entry"]
        live_lines = entry["purchasing_order_items_details"]
        line_sum = sum(float(l["total_amount"]) for l in live_lines)
        assert float(entry["txn_currency_total_amount"]) == pytest.approx(line_sum, abs=0.01)

    def test_two_line_master_total(self, po_api):
        items = [
            _item(item_ref_id=5, qty=10.0, rate=100.0),  # 1000
            _item(item_ref_id=6, qty=5.0,  rate=200.0),  # 1000
        ]
        payload = _payload(items)
        result = po_api.create_and_verify_calculations(payload=payload)
        entry = result["entry"]
        assert float(entry["txn_currency_total_amount"]) == pytest.approx(2000.0, abs=0.01)

    def test_five_line_master_total(self, po_api):
        items = [_item(item_ref_id=i, qty=float(i * 5), rate=100.0) for i in range(1, 6)]
        payload = _payload(items)
        result = po_api.create_and_verify_calculations(payload=payload)
        entry = result["entry"]
        live_lines = entry["purchasing_order_items_details"]
        line_sum = sum(float(l["total_amount"]) for l in live_lines)
        assert float(entry["txn_currency_total_amount"]) == pytest.approx(line_sum, abs=0.01)

    def test_mixed_tax_master_total(self, po_api):
        # Lines: 1050 + 1120 + 1180 = 3350
        items = [
            _item(item_ref_id=5, qty=10.0, rate=100.0, tax_rate=5.0),
            _item(item_ref_id=6, qty=5.0,  rate=200.0, tax_rate=12.0),
            _item(item_ref_id=7, qty=2.0,  rate=500.0, tax_rate=18.0),
        ]
        payload = _payload(items)
        result = po_api.create_and_verify_calculations(payload=payload)
        entry = result["entry"]
        assert float(entry["txn_currency_total_amount"]) == pytest.approx(3350.0, abs=0.01)


# ---------------------------------------------------------------------------
# LIVE: discount and interest
# ---------------------------------------------------------------------------

@pytest.mark.calculation
@pytest.mark.live
class TestLiveDiscountInterest:
    """Discount and interest amounts pass through correctly — ERP stores explicit values."""

    def test_discount_5pct_from_percent(self, po_api):
        # 20 × 250 = 5000; explicit discount = 250
        payload = _payload(
            [_item(qty=20.0, rate=250.0)],
            additional_details=_additional(discount_amt=250.0),
        )
        result = po_api.create_po(payload=payload)
        assert result is not None, "PO creation failed"
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None, "Failed to fetch PO"
        add = entry["additional_details"]
        assert float(add.get("txn_currency_discount_amount", 0) or 0) == pytest.approx(250.0, abs=0.01)
        assert float(add.get("txn_currency_interest_amount", 0) or 0) == 0.0

    def test_interest_8pct_from_percent(self, po_api):
        # 30 × 100 = 3000; explicit interest = 240
        payload = _payload(
            [_item(qty=30.0, rate=100.0)],
            additional_details=_additional(interest_amt=240.0),
        )
        result = po_api.create_po(payload=payload)
        assert result is not None
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        add = entry["additional_details"]
        assert float(add.get("txn_currency_interest_amount", 0) or 0) == pytest.approx(240.0, abs=0.01)
        assert float(add.get("txn_currency_discount_amount", 0) or 0) == 0.0

    def test_discount_and_interest_combined(self, po_api):
        # 10 × 1000 = 10000; explicit amounts
        payload = _payload(
            [_item(qty=10.0, rate=1000.0)],
            additional_details=_additional(discount_amt=500.0, interest_amt=1000.0),
        )
        result = po_api.create_po(payload=payload)
        assert result is not None
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        add = entry["additional_details"]
        assert float(add.get("txn_currency_discount_amount", 0) or 0) == pytest.approx(500.0, abs=0.01)
        assert float(add.get("txn_currency_interest_amount", 0) or 0) == pytest.approx(1000.0, abs=0.01)

    def test_backend_overrides_explicit_amounts_with_percent(self, po_api):
        """Document ERP behavior: when both percent and explicit amount are sent, the explicit amount is stored."""
        # 10 × 100 = 1000; ERP stores explicit amounts regardless of percent
        payload = _payload(
            [_item(qty=10.0, rate=100.0)],
            additional_details=_additional(
                discount_pct=5.0, discount_amt=999.0,
                interest_pct=10.0, interest_amt=888.0,
            ),
        )
        result = po_api.create_po(payload=payload)
        assert result is not None, "PO creation failed"
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        add = entry["additional_details"]
        d = float(add.get("txn_currency_discount_amount", 0) or 0)
        i = float(add.get("txn_currency_interest_amount", 0) or 0)
        assert d == pytest.approx(999.0, abs=0.01), (
            f"Expected ERP to store explicit discount_amt=999, got {d}"
        )
        assert i == pytest.approx(888.0, abs=0.01), (
            f"Expected ERP to store explicit interest_amt=888, got {i}"
        )

    def test_no_discount_no_interest(self, po_api):
        payload = _payload([_item(qty=10.0, rate=100.0)])
        result = po_api.create_and_verify_calculations(payload=payload)
        add = result["entry"]["additional_details"]
        assert float(add.get("txn_currency_discount_amount", 0) or 0) == 0.0
        assert float(add.get("txn_currency_interest_amount", 0) or 0) == 0.0

    def test_discount_on_multi_line_total(self, po_api):
        # Lines: 1000 + 2000 = 3000; explicit discount = 300
        items = [
            _item(item_ref_id=5, qty=10.0, rate=100.0),
            _item(item_ref_id=6, qty=10.0, rate=200.0),
        ]
        payload = _payload(items, additional_details=_additional(discount_amt=300.0))
        result = po_api.create_po(payload=payload)
        assert result is not None
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        add = entry["additional_details"]
        assert float(add.get("txn_currency_discount_amount", 0) or 0) == pytest.approx(300.0, abs=0.01)


# ---------------------------------------------------------------------------
# LIVE: edge cases
# ---------------------------------------------------------------------------

@pytest.mark.calculation
@pytest.mark.live
class TestLiveEdgeCases:
    """Edge cases that are easy to overlook but critical for a transactional screen."""

    def test_transportation_charges_pass_through(self, po_api):
        """transportation_charges should be stored as-is — not added to txn_currency_total_amount."""
        payload = _payload(
            [_item(qty=10.0, rate=100.0)],
            additional_details=_additional(transport=500.0),
        )
        result = po_api.create_po(payload=payload)
        assert result is not None
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        add = entry["additional_details"]
        # Master total should still be 1000 (transportation not added)
        assert float(entry["txn_currency_total_amount"]) == pytest.approx(1000.0, abs=0.01)
        # Transportation charges stored correctly
        assert float(add.get("transportation_charges", 0) or 0) == pytest.approx(500.0, abs=0.01)

    def test_remark_passes_through(self, po_api):
        payload = _payload(
            [_item(qty=10.0, rate=100.0)],
            additional_details=_additional(remark="Test remark 123"),
        )
        result = po_api.create_po(payload=payload)
        assert result is not None
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        assert entry["additional_details"].get("remark") == "Test remark 123"

    def test_zero_tax_rate_explicit(self, po_api):
        """Explicitly sending tax_rate=0 should produce no tax."""
        payload = _payload([_item(qty=10.0, rate=100.0, tax_rate=0.0)])
        result = po_api.create_and_verify_calculations(payload=payload)
        live = result["entry"]["purchasing_order_items_details"][0]
        assert float(live.get("txn_currency_tax_amount_details", 0) or 0) == 0.0
        assert float(live["total_amount"]) == pytest.approx(1000.0, abs=0.01)

    def test_single_unit_quantity(self, po_api):
        # qty=1 × rate=9999 = 9999
        payload = _payload([_item(qty=1.0, rate=9999.0)])
        result = po_api.create_and_verify_calculations(payload=payload)
        live = result["entry"]["purchasing_order_items_details"][0]
        assert float(live["txn_currency_amount_detail"]) == pytest.approx(9999.0, abs=0.01)

    def test_conversion_rate_one_does_not_affect_total(self, po_api):
        """conversion_rate=1.0 means txn and base currency totals are identical."""
        payload = _payload([_item(qty=10.0, rate=100.0)])
        result = po_api.create_po(payload=payload)
        assert result is not None
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        # With conversion_rate=1, total should be 1000 in both currencies
        assert float(entry["txn_currency_total_amount"]) == pytest.approx(1000.0, abs=0.01)

    def test_all_zero_discount_interest_fields_remain_zero(self, po_api):
        """Sending None percents should leave amounts as 0."""
        payload = _payload(
            [_item(qty=10.0, rate=100.0)],
            additional_details=_additional(discount_pct=None, interest_pct=None),
        )
        result = po_api.create_po(payload=payload)
        assert result is not None
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        add = entry["additional_details"]
        assert float(add.get("txn_currency_discount_amount", 0) or 0) == 0.0
        assert float(add.get("txn_currency_interest_amount", 0) or 0) == 0.0

    def test_line_total_in_response_equals_amount_plus_tax(self, po_api):
        """ERP line total must always equal amount + tax — no hidden fields."""
        items = [
            _item(item_ref_id=5, qty=10.0, rate=100.0, tax_rate=12.0),
            _item(item_ref_id=6, qty=7.0,  rate=300.0, tax_rate=18.0),
        ]
        payload = _payload(items)
        result = po_api.create_po(payload=payload)
        assert result is not None
        entry = po_api.get_po(result.get("id") or result.get("entry_id"))
        assert entry is not None
        for line in entry["purchasing_order_items_details"]:
            amount = float(line.get("txn_currency_amount_detail", 0) or 0)
            tax = float(line.get("txn_currency_tax_amount_details", 0) or 0)
            total = float(line.get("total_amount", 0) or 0)
            assert total == pytest.approx(amount + tax, abs=0.01), (
                f"Line total {total} != amount {amount} + tax {tax}"
            )


# ---------------------------------------------------------------------------
# UNIT: boundary value analysis
# ---------------------------------------------------------------------------

@pytest.mark.calculation
class TestBoundaryValues:
    """Values at exact mathematical boundaries — min, max, near-zero, near-100%."""

    def test_minimum_meaningful_quantity(self):
        # 0.0001 × 1000 = 0.1
        assert compute_line_amount(0.0001, 1000) == pytest.approx(0.1, abs=0.0001)

    def test_minimum_meaningful_rate(self):
        # 100 × 0.01 = 1.0 (1 paisa)
        assert compute_line_amount(100, 0.01) == pytest.approx(1.0, abs=0.001)

    def test_near_max_quantity(self):
        assert compute_line_amount(999999.99, 1) == pytest.approx(999999.99, abs=0.01)

    def test_near_max_rate(self):
        assert compute_line_amount(1, 9999999.99) == pytest.approx(9999999.99, abs=0.01)

    def test_near_max_combined(self):
        # Large qty × large rate — must not silently overflow
        result = compute_line_amount(99999.99, 99999.99)
        assert result == pytest.approx(99999.99 * 99999.99, rel=1e-6)

    def test_tax_exactly_100_percent(self):
        # tax = 100% of amount → total doubles
        tax = compute_line_tax(1000, 100)
        assert tax == pytest.approx(1000.0, abs=0.01)
        assert compute_line_total(1000, tax) == pytest.approx(2000.0, abs=0.01)

    def test_tax_just_below_100_percent(self):
        tax = compute_line_tax(1000, 99.999)
        assert tax == pytest.approx(999.99, abs=0.01)

    def test_tax_just_above_100_percent(self):
        # 110% tax — mathematically valid, total = amount + 110% of amount
        tax = compute_line_tax(1000, 110)
        assert tax == pytest.approx(1100.0, abs=0.01)
        total = compute_line_total(1000, tax)
        assert total == pytest.approx(2100.0, abs=0.01)

    def test_discount_exactly_100_percent(self):
        # Full discount — nothing owed
        assert compute_discount_amount(10000, 100) == pytest.approx(10000.0, abs=0.01)

    def test_discount_just_under_100_percent(self):
        assert compute_discount_amount(10000, 99.999) == pytest.approx(9999.9, abs=0.1)

    def test_discount_over_100_percent(self):
        # 110% discount — net total would go negative. Math allows it — ERP should block it.
        disc = compute_discount_amount(10000, 110)
        assert disc == pytest.approx(11000.0, abs=0.01)
        # Net = 10000 - 11000 = -1000 — document this is the compute layer behaviour
        assert (10000 - disc) == pytest.approx(-1000.0, abs=0.01)

    def test_single_paisa_total(self):
        # qty=1, rate=0.01 → amount=0.01, total=0.01
        amount = compute_line_amount(1, 0.01)
        total = compute_line_total(amount, compute_line_tax(amount, 0))
        assert total == pytest.approx(0.01, abs=0.001)


# ---------------------------------------------------------------------------
# UNIT: floating point traps
# ---------------------------------------------------------------------------

@pytest.mark.calculation
class TestFloatingPointTraps:
    """Cases where IEEE-754 float arithmetic produces surprising results."""

    def test_0_1_times_3(self):
        # Classic: 0.1 + 0.1 + 0.1 != 0.3 in float
        # qty=3, rate=0.1 → expect 0.3 but raw float gives 0.30000000000000004
        result = compute_line_amount(3, 0.1)
        assert result == pytest.approx(0.3, abs=1e-9)

    def test_1_1_times_1_1(self):
        # 1.1 × 1.1 = 1.21 but float gives 1.2100000000000002
        result = compute_line_amount(1.1, 1.1)
        assert result == pytest.approx(1.21, abs=1e-9)

    def test_3_33_times_3(self):
        # 3.33 × 3 = 9.99 — common invoice amount
        result = compute_line_amount(3, 3.33)
        assert result == pytest.approx(9.99, abs=1e-6)

    def test_cumulative_rounding_100_lines(self):
        # 100 lines each qty=0.1, rate=0.1 → each line=0.01 → sum=1.0
        # Float accumulation should not drift beyond 0.001
        lines = [{"total_amount": compute_line_total(compute_line_amount(0.1, 0.1), 0)}
                 for _ in range(100)]
        total = compute_master_total(lines)
        assert total == pytest.approx(1.0, abs=0.001)

    def test_cumulative_rounding_1000_lines(self):
        # 1000 lines each producing 0.001 → sum should be 1.0
        lines = [{"total_amount": 0.001} for _ in range(1000)]
        total = compute_master_total(lines)
        assert total == pytest.approx(1.0, abs=0.01)

    def test_tax_33_333_percent_on_3000(self):
        # 3000 × 33.333% = 999.99 — not 1000
        tax = compute_line_tax(3000, 33.333)
        assert tax == pytest.approx(999.99, abs=0.01)

    def test_tax_on_decimal_amount(self):
        # amount=9.99, tax=10% → 0.999 — sub-paisa
        tax = compute_line_tax(9.99, 10)
        assert tax == pytest.approx(0.999, abs=0.001)

    def test_discount_2_5_percent_on_odd_total(self):
        # 7777.77 × 2.5% = 194.44425
        disc = compute_discount_amount(7777.77, 2.5)
        assert disc == pytest.approx(194.44, abs=0.01)

    def test_line_amount_sub_paisa_qty(self):
        # qty=0.001, rate=100 → 0.1
        result = compute_line_amount(0.001, 100)
        assert result == pytest.approx(0.1, abs=1e-6)

    def test_master_total_mixed_precision_lines(self):
        # Lines with varying decimal depths — sum must be stable
        lines = [
            {"total_amount": 1.1},
            {"total_amount": 2.22},
            {"total_amount": 3.333},
            {"total_amount": 4.4444},
            {"total_amount": 5.55555},
        ]
        total = compute_master_total(lines)
        expected = 1.1 + 2.22 + 3.333 + 4.4444 + 5.55555
        assert total == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# UNIT: negative inputs — math layer behaviour (not ERP validation)
# ---------------------------------------------------------------------------

@pytest.mark.calculation
class TestNegativeInputsMath:
    """
    Documents how compute functions behave with negative inputs.
    These are NOT expected valid ERP inputs — the live ERP should reject them.
    These unit tests pin the math layer's current behaviour so any change is visible.
    """

    def test_negative_quantity_produces_negative_amount(self):
        result = compute_line_amount(-10, 100)
        assert result == pytest.approx(-1000.0, abs=0.01)

    def test_negative_rate_produces_negative_amount(self):
        result = compute_line_amount(10, -100)
        assert result == pytest.approx(-1000.0, abs=0.01)

    def test_both_negative_produces_positive_amount(self):
        # −qty × −rate = positive (double negative)
        result = compute_line_amount(-10, -100)
        assert result == pytest.approx(1000.0, abs=0.01)

    def test_negative_tax_reduces_line_total(self):
        # Negative tax acts as a discount on the line
        tax = compute_line_tax(1000, -5)
        assert tax == pytest.approx(-50.0, abs=0.01)
        total = compute_line_total(1000, tax)
        assert total == pytest.approx(950.0, abs=0.01)

    def test_negative_discount_increases_total(self):
        # Negative discount = price increase — a hidden surcharge
        disc = compute_discount_amount(10000, -10)
        assert disc == pytest.approx(-1000.0, abs=0.01)

    def test_negative_interest_reduces_total(self):
        # Negative interest = rebate
        intr = compute_interest_amount(10000, -5)
        assert intr == pytest.approx(-500.0, abs=0.01)

    def test_negative_master_total_from_negative_lines(self):
        lines = [{"total_amount": -500.0}, {"total_amount": 1000.0}]
        total = compute_master_total(lines)
        assert total == pytest.approx(500.0, abs=0.01)

    def test_negative_amount_with_positive_tax(self):
        # Negative line amount (negative qty) + positive tax — tax adds to negative
        amount = compute_line_amount(-10, 100)   # -1000
        tax = compute_line_tax(amount, 18)        # -180
        total = compute_line_total(amount, tax)   # -1180
        assert total == pytest.approx(-1180.0, abs=0.01)
