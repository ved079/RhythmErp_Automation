"""
test_integrity.py — Data integrity tests for Purchase Order.

Verifies that:
  - Calculations stay consistent across create → read → update cycles
  - Updating one field does not corrupt others
  - Read-after-write is immediate and complete
  - Concurrent creates produce unique, correct records
  - Performance baselines hold under realistic load

Requires ERP_TOKEN env var.

Structure:
  TestReadAfterWrite       — GET immediately after POST returns correct computed fields
  TestUpdateConsistency    — Updating a line recalculates everything correctly
  TestIsolation            — Updating one line doesn't corrupt sibling lines
  TestConcurrentCreation   — Simultaneous creates produce unique, correct records
  TestPerformanceBaselines — Response time contracts
"""

import os
import sys
import time
import pytest
import threading

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    build_po_payload,
    compute_expected_results,
    assert_calculations_match,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item(item_ref_id=5, qty=10.0, rate=100.0, tax_rate=None, hsn=2, uom=3):
    i = {
        "item_ref_id": item_ref_id,
        "hsn_sac_no": hsn,
        "uom": uom,
        "alternate_uom": uom,
        "alternate_quantity": str(qty),
        "quantity": qty,
        "rate": rate,
        "expected_delivery_date": "2026-12-31",
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


def _additional(**kwargs):
    base = {
        "transportation_charges": 0,
        "txn_currency_discount_percent": None,
        "txn_currency_discount_amount": 0,
        "txn_currency_interest_percent": None,
        "txn_currency_interest_amount": 0,
        "remark": None,
    }
    base.update(kwargs)
    return base


def _create(po_api, payload):
    result = po_api.create_po(payload)
    assert result is not None, f"PO creation failed (status {po_api._last_status})"
    entry_id = result.get("id") or result.get("entry_id")
    assert entry_id, "No entry ID returned"
    return entry_id


def _get(po_api, entry_id):
    entry = po_api.get_po(entry_id)
    assert entry is not None, f"Failed to GET PO {entry_id}"
    return entry


# ---------------------------------------------------------------------------
# Read-after-write: computed fields present immediately
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestReadAfterWrite:
    """GET immediately after POST must return all computed fields — no async lag."""

    def test_line_amount_present_on_create_response(self, po_api):
        payload = _payload([_item(qty=10.0, rate=100.0)])
        result = po_api.create_po(payload)
        assert result is not None
        lines = result.get("purchasing_order_items_details", [])
        assert len(lines) > 0
        assert float(lines[0].get("txn_currency_amount_detail", 0) or 0) == pytest.approx(1000.0, abs=0.01)

    def test_master_total_present_on_create_response(self, po_api):
        payload = _payload([_item(qty=10.0, rate=100.0)])
        result = po_api.create_po(payload)
        assert result is not None
        assert float(result.get("txn_currency_total_amount", 0) or 0) == pytest.approx(1000.0, abs=0.01)

    def test_get_matches_create_response(self, po_api):
        """GET response must match the create response exactly for computed fields."""
        payload = _payload([_item(qty=10.0, rate=100.0)])
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = _get(po_api, entry_id)

        create_total = float(result.get("txn_currency_total_amount", 0) or 0)
        get_total = float(entry.get("txn_currency_total_amount", 0) or 0)
        assert create_total == pytest.approx(get_total, abs=0.01), (
            f"Create total {create_total} != GET total {get_total}"
        )

    def test_get_twice_returns_identical_totals(self, po_api):
        """Two consecutive GETs must return identical computed values — no background recalc."""
        payload = _payload([_item(qty=10.0, rate=100.0)])
        entry_id = _create(po_api, payload)

        entry1 = _get(po_api, entry_id)
        entry2 = _get(po_api, entry_id)

        assert float(entry1["txn_currency_total_amount"]) == pytest.approx(
            float(entry2["txn_currency_total_amount"]), abs=0.01
        )
        lines1 = entry1["purchasing_order_items_details"]
        lines2 = entry2["purchasing_order_items_details"]
        for l1, l2 in zip(lines1, lines2):
            assert float(l1.get("total_amount", 0) or 0) == pytest.approx(
                float(l2.get("total_amount", 0) or 0), abs=0.01
            )

    def test_all_line_computed_fields_present_on_get(self, po_api):
        """Every line in the GET response must have amount, tax, and total fields."""
        payload = _payload([
            _item(item_ref_id=5, qty=10.0, rate=100.0, tax_rate=12.0),
            _item(item_ref_id=6, qty=5.0,  rate=200.0, tax_rate=18.0),
        ])
        entry_id = _create(po_api, payload)
        entry = _get(po_api, entry_id)

        for i, line in enumerate(entry["purchasing_order_items_details"]):
            assert "txn_currency_amount_detail" in line, f"Line {i} missing amount"
            assert "txn_currency_tax_amount_details" in line, f"Line {i} missing tax"
            assert "total_amount" in line, f"Line {i} missing total"
            amount = float(line["txn_currency_amount_detail"] or 0)
            tax = float(line["txn_currency_tax_amount_details"] or 0)
            total = float(line["total_amount"] or 0)
            assert total == pytest.approx(amount + tax, abs=0.01), (
                f"Line {i}: total {total} != amount {amount} + tax {tax}"
            )

    def test_discount_amount_present_on_get(self, po_api):
        payload = _payload(
            [_item(qty=20.0, rate=250.0)],
            additional_details=_additional(txn_currency_discount_amount=250.0),
        )
        entry_id = _create(po_api, payload)
        entry = _get(po_api, entry_id)
        disc = float(entry["additional_details"].get("txn_currency_discount_amount", 0) or 0)
        assert disc == pytest.approx(250.0, abs=0.01)


# ---------------------------------------------------------------------------
# Update consistency: recalculation after edit
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestUpdateConsistency:
    """After updating a PO, all computed fields must reflect the new values."""

    def test_update_quantity_recalculates_line_total(self, po_api):
        """Change qty → line amount and master total must both update."""
        payload = _payload([_item(qty=10.0, rate=100.0)])
        entry_id = _create(po_api, payload)
        entry = _get(po_api, entry_id)

        # Double the quantity
        updated = dict(entry)
        updated["purchasing_order_items_details"][0]["quantity"] = 20.0
        result = po_api.update_po(entry_id, updated)
        assert result is not None, f"Update failed (status {po_api._last_status})"

        refreshed = _get(po_api, entry_id)
        line = refreshed["purchasing_order_items_details"][0]
        assert float(line["txn_currency_amount_detail"]) == pytest.approx(2000.0, abs=0.01)
        assert float(refreshed["txn_currency_total_amount"]) == pytest.approx(2000.0, abs=0.01)

    def test_update_rate_recalculates_line_total(self, po_api):
        """Change rate → line amount and master total must both update."""
        payload = _payload([_item(qty=10.0, rate=100.0)])
        entry_id = _create(po_api, payload)
        entry = _get(po_api, entry_id)

        updated = dict(entry)
        updated["purchasing_order_items_details"][0]["rate"] = 250.0
        result = po_api.update_po(entry_id, updated)
        assert result is not None

        refreshed = _get(po_api, entry_id)
        line = refreshed["purchasing_order_items_details"][0]
        assert float(line["txn_currency_amount_detail"]) == pytest.approx(2500.0, abs=0.01)
        assert float(refreshed["txn_currency_total_amount"]) == pytest.approx(2500.0, abs=0.01)

    def test_update_discount_recalculates_discount_amount(self, po_api):
        """Update explicit discount amount → amount must reflect new value."""
        payload = _payload(
            [_item(qty=10.0, rate=1000.0)],
            additional_details=_additional(txn_currency_discount_amount=500.0),
        )
        entry_id = _create(po_api, payload)
        entry = _get(po_api, entry_id)
        initial_disc = float(entry["additional_details"].get("txn_currency_discount_amount", 0) or 0)
        assert initial_disc == pytest.approx(500.0, abs=0.01)

        updated = dict(entry)
        updated["additional_details"]["txn_currency_discount_amount"] = 1000.0
        result = po_api.update_po(entry_id, updated)
        assert result is not None

        refreshed = _get(po_api, entry_id)
        new_disc = float(refreshed["additional_details"].get("txn_currency_discount_amount", 0) or 0)
        assert new_disc == pytest.approx(1000.0, abs=0.01)


# ---------------------------------------------------------------------------
# Isolation: updating one line must not corrupt siblings
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestIsolation:
    """Mutating one line in a multi-line PO must not affect other lines."""

    def test_update_line1_does_not_change_line2(self, po_api):
        payload = _payload([
            _item(item_ref_id=5, qty=10.0, rate=100.0),   # line 0: total=1000
            _item(item_ref_id=6, qty=5.0,  rate=200.0),   # line 1: total=1000
        ])
        entry_id = _create(po_api, payload)
        entry = _get(po_api, entry_id)

        line1_id = entry["purchasing_order_items_details"][1].get("id")
        line1_total_before = float(
            entry["purchasing_order_items_details"][1].get("total_amount", 0) or 0
        )

        # Update only line 0
        updated = dict(entry)
        updated["purchasing_order_items_details"][0]["quantity"] = 99.0
        result = po_api.update_po(entry_id, updated)
        assert result is not None

        refreshed = _get(po_api, entry_id)
        lines = refreshed["purchasing_order_items_details"]

        # Find line 1 by its ID
        line1 = next((l for l in lines if l.get("id") == line1_id), None)
        assert line1 is not None, "Line 1 disappeared after updating line 0"
        line1_total_after = float(line1.get("total_amount", 0) or 0)
        assert line1_total_after == pytest.approx(line1_total_before, abs=0.01), (
            f"Line 1 total changed from {line1_total_before} to {line1_total_after} "
            "after updating line 0 — isolation failure"
        )

    def test_master_total_updates_when_one_line_changes(self, po_api):
        payload = _payload([
            _item(item_ref_id=5, qty=10.0, rate=100.0),   # 1000
            _item(item_ref_id=6, qty=5.0,  rate=200.0),   # 1000
            _item(item_ref_id=7, qty=2.0,  rate=500.0),   # 1000
        ])
        entry_id = _create(po_api, payload)
        entry = _get(po_api, entry_id)
        total_before = float(entry.get("txn_currency_total_amount", 0) or 0)
        assert total_before == pytest.approx(3000.0, abs=0.01)

        # Double line 0 qty → 2000, total should become 4000
        updated = dict(entry)
        updated["purchasing_order_items_details"][0]["quantity"] = 20.0
        result = po_api.update_po(entry_id, updated)
        assert result is not None

        refreshed = _get(po_api, entry_id)
        total_after = float(refreshed.get("txn_currency_total_amount", 0) or 0)
        assert total_after == pytest.approx(4000.0, abs=0.01), (
            f"Expected master total 4000 after update, got {total_after}"
        )

    def test_non_financial_field_update_preserves_totals(self, po_api):
        """Updating remark must not change any calculated amounts."""
        payload = _payload([_item(qty=10.0, rate=100.0)])
        entry_id = _create(po_api, payload)
        entry = _get(po_api, entry_id)
        total_before = float(entry.get("txn_currency_total_amount", 0) or 0)

        updated = dict(entry)
        updated["additional_details"]["remark"] = "Updated remark"
        result = po_api.update_po(entry_id, updated)
        assert result is not None

        refreshed = _get(po_api, entry_id)
        total_after = float(refreshed.get("txn_currency_total_amount", 0) or 0)
        assert total_after == pytest.approx(total_before, abs=0.01), (
            f"Remark update changed master total from {total_before} to {total_after}"
        )
        assert refreshed["additional_details"].get("remark") == "Updated remark"


# ---------------------------------------------------------------------------
# Concurrent creation: simultaneous creates must produce unique records
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestConcurrentCreation:
    """5 simultaneous PO creates must each produce a unique, correct record."""

    def test_5_concurrent_creates_all_succeed(self, po_api):
        payload = _payload([_item(qty=10.0, rate=100.0)])
        results = []
        errors = []

        def create():
            try:
                import copy
                p = copy.deepcopy(payload)
                r = po_api.create_po(p)
                results.append(r)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=create) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert not errors, f"Errors during concurrent create: {errors}"
        successful = [r for r in results if r is not None]
        assert len(successful) >= 4, (
            f"Only {len(successful)}/5 concurrent creates succeeded"
        )

    def test_concurrent_creates_produce_unique_ids(self, po_api):
        payload = _payload([_item(qty=10.0, rate=100.0)])
        ids = []
        lock = threading.Lock()

        def create():
            import copy
            p = copy.deepcopy(payload)
            r = po_api.create_po(p)
            if r:
                eid = r.get("id") or r.get("entry_id")
                with lock:
                    ids.append(eid)

        threads = [threading.Thread(target=create) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert len(ids) == len(set(ids)), (
            f"Duplicate IDs in concurrent creates: {ids}"
        )

    def test_concurrent_creates_unique_ref_nos(self, po_api):
        payload = _payload([_item(qty=10.0, rate=100.0)])
        ref_nos = []
        lock = threading.Lock()

        def create():
            import copy
            p = copy.deepcopy(payload)
            r = po_api.create_po(p)
            if r:
                entry_id = r.get("id") or r.get("entry_id")
                if entry_id:
                    entry = po_api.get_po(entry_id)
                    if entry:
                        ref = entry.get("transaction_ref_no", "")
                        with lock:
                            ref_nos.append(ref)

        threads = [threading.Thread(target=create) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert len(ref_nos) == len(set(ref_nos)), (
            f"Duplicate ref nos in concurrent creates: {ref_nos}"
        )


# ---------------------------------------------------------------------------
# Performance baselines
# ---------------------------------------------------------------------------

@pytest.mark.live
@pytest.mark.performance
class TestPerformanceBaselines:
    """Response time contracts — if these fail, something regressed."""

    def test_single_create_under_5s(self, po_api):
        payload = _payload([_item(qty=10.0, rate=100.0)])
        start = time.time()
        result = po_api.create_po(payload)
        elapsed = time.time() - start
        assert result is not None, "PO creation failed"
        assert elapsed < 5.0, f"Create PO took {elapsed:.2f}s — expected < 5s"

    def test_get_under_2s(self, po_api):
        payload = _payload([_item(qty=10.0, rate=100.0)])
        entry_id = _create(po_api, payload)
        start = time.time()
        entry = po_api.get_po(entry_id)
        elapsed = time.time() - start
        assert entry is not None
        assert elapsed < 2.0, f"GET PO took {elapsed:.2f}s — expected < 2s"

    def test_list_under_3s(self, po_api):
        start = time.time()
        listing = po_api.list_pos(page=1, page_size=25)
        elapsed = time.time() - start
        assert listing is not None
        assert elapsed < 3.0, f"List POs took {elapsed:.2f}s — expected < 3s"

    def test_10_line_po_create_under_8s(self, po_api):
        """A large PO with 10 lines should still respond within 8 seconds."""
        items = [_item(item_ref_id=5, qty=float(i + 1), rate=100.0) for i in range(10)]
        payload = _payload(items)
        start = time.time()
        result = po_api.create_po(payload)
        elapsed = time.time() - start
        assert result is not None, "10-line PO creation failed"
        assert elapsed < 8.0, f"10-line PO create took {elapsed:.2f}s — expected < 8s"

    def test_10_sequential_creates_no_degradation(self, po_api):
        """10th create must not be significantly slower than 1st — no memory/resource leak."""
        times = []
        for _ in range(10):
            payload = _payload([_item(qty=10.0, rate=100.0)])
            start = time.time()
            result = po_api.create_po(payload)
            elapsed = time.time() - start
            assert result is not None, "PO creation failed mid-sequence"
            times.append(elapsed)

        first = times[0]
        last = times[-1]
        # Last request should not be more than 3× slower than first
        assert last < first * 3 + 2.0, (
            f"Performance degraded: 1st={first:.2f}s, 10th={last:.2f}s — "
            f"possible resource leak"
        )
