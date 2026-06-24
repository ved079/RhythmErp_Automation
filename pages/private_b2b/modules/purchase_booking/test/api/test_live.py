"""
test_live.py — Live ERP tests for Purchase Booking.

Requires ERP_TOKEN and ERP_TENANT_ID env vars.
All tests skip if token is absent (run offline by default).

Test layers:
  TestLiveCreate       — basic create + GET roundtrip
  TestLiveCalculations — ERP confirms computed fields match our formulas
  TestLiveMasterAggs   — ERP confirms master amount/total_quantity aggregation
  TestLiveIntegrity    — read-after-write, update recalculation
"""

import os
import pytest
from pages.private_b2b.modules.purchase_booking.data.purchase_booking_data import (
    build_pb_item,
    build_pb_payload,
    SUPPLIER_TYPE_FARMER,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _item(rate=100.0, qty=10.0, ebw=0.0, labour=0.0,
          igst=0.0, cgst=0.0, sgst=0.0, bags=1.0):
    return build_pb_item(
        item_ref_id=1, hsn_sac_no=1, uom=1,
        rate=rate, quantity=qty, no_of_bags=bags,
        empty_bag_weight=ebw, labour_charges=labour,
        igst_rate=igst, cgst_rate=cgst, sgst_rate=sgst,
    )


def _payload(items, **kwargs):
    return build_pb_payload(
        supplier_ref_id=1, supplier_ref_type=SUPPLIER_TYPE_FARMER,
        parameter1=1, parameter2=1, parameter5=1, parameter6=1,
        base_currency=8, txn_currency=8,
        items=items, **kwargs,
    )


def _create(pb_api, payload):
    data = pb_api.create_pb(payload)
    assert data is not None, (
        f"PB create failed: {pb_api.last_response().text[:400] if pb_api.last_response() else 'no response'}"
    )
    return data


def _get(pb_api, entry_id):
    data = pb_api.get_pb(entry_id)
    assert data is not None, f"PB GET failed for id={entry_id}"
    return data


def _entry_id(data):
    return data.get("id") or data.get("entry_id")


# ── Create + GET roundtrip ────────────────────────────────────────────────────

class TestLiveCreate:
    @pytest.mark.live
    def test_create_single_item_returns_id(self, pb_api):
        data = _create(pb_api, _payload([_item()]))
        assert _entry_id(data) is not None

    @pytest.mark.live
    def test_create_has_transaction_ref_no(self, pb_api):
        data = _create(pb_api, _payload([_item()]))
        assert data.get("transaction_ref_no"), "transaction_ref_no empty or missing"

    @pytest.mark.live
    def test_get_returns_same_record(self, pb_api):
        created = _create(pb_api, _payload([_item()]))
        fetched = _get(pb_api, _entry_id(created))
        assert _entry_id(fetched) == _entry_id(created)

    @pytest.mark.live
    def test_create_multi_item(self, pb_api):
        items = [_item(rate=100.0), _item(rate=200.0)]
        data = _create(pb_api, _payload(items))
        assert _entry_id(data) is not None

    @pytest.mark.live
    def test_unique_ref_nos_across_creates(self, pb_api):
        refs = set()
        for _ in range(3):
            data = _create(pb_api, _payload([_item()]))
            refs.add(data.get("transaction_ref_no", ""))
        assert len(refs) == 3, f"Duplicate ref nos: {refs}"


# ── Live calculation verification ─────────────────────────────────────────────

class TestLiveCalculations:
    @pytest.mark.live
    def test_net_quantity_in_response(self, pb_api):
        item = _item(qty=10.0, ebw=0.5)
        data = _create(pb_api, _payload([item]))
        entry = _get(pb_api, _entry_id(data))
        details = entry.get("purchase_booking_details") or []
        assert details, "No purchase_booking_details in GET response"
        row = details[0]
        assert float(row.get("net_quantity", 0)) == pytest.approx(9.5, rel=1e-4)

    @pytest.mark.live
    def test_txn_currency_amount_in_response(self, pb_api):
        item = _item(rate=100.0, qty=10.0)
        data = _create(pb_api, _payload([item]))
        entry = _get(pb_api, _entry_id(data))
        details = entry.get("purchase_booking_details") or []
        row = details[0]
        assert float(row.get("txn_currency_amount", 0)) == pytest.approx(1000.0, rel=1e-4)

    @pytest.mark.live
    def test_line_total_with_labour_in_response(self, pb_api):
        item = _item(rate=100.0, qty=10.0, labour=50.0)
        data = _create(pb_api, _payload([item]))
        entry = _get(pb_api, _entry_id(data))
        details = entry.get("purchase_booking_details") or []
        row = details[0]
        assert float(row.get("txn_currency_amount", 0)) == pytest.approx(950.0, rel=1e-4)

    @pytest.mark.live
    def test_master_total_quantity(self, pb_api):
        items = [_item(qty=5.0), _item(qty=3.0)]
        data = _create(pb_api, _payload(items))
        entry = _get(pb_api, _entry_id(data))
        assert float(entry.get("total_quantity", 0)) == pytest.approx(8.0, rel=1e-4)

    @pytest.mark.live
    def test_master_amount_sum_of_lines(self, pb_api):
        items = [_item(rate=100.0, qty=10.0), _item(rate=200.0, qty=5.0)]
        data = _create(pb_api, _payload(items))
        entry = _get(pb_api, _entry_id(data))
        assert float(entry.get("amount", 0)) == pytest.approx(2000.0, rel=1e-4)


# ── Master aggregate live checks ──────────────────────────────────────────────

class TestLiveMasterAggregates:
    @pytest.mark.live
    def test_five_lines_total_qty(self, pb_api):
        items = [_item(qty=float(q)) for q in range(1, 6)]
        data = _create(pb_api, _payload(items))
        entry = _get(pb_api, _entry_id(data))
        assert float(entry.get("total_quantity", 0)) == pytest.approx(15.0, rel=1e-4)

    @pytest.mark.live
    def test_bag_weight_reduces_total_qty(self, pb_api):
        items = [_item(qty=10.0, ebw=1.0)]  # net = 9
        data = _create(pb_api, _payload(items))
        entry = _get(pb_api, _entry_id(data))
        assert float(entry.get("total_quantity", 0)) == pytest.approx(9.0, rel=1e-4)


# ── Integrity: read-after-write ───────────────────────────────────────────────

class TestLiveIntegrity:
    @pytest.mark.live
    @pytest.mark.integrity
    def test_get_twice_identical(self, pb_api):
        data = _create(pb_api, _payload([_item()]))
        eid = _entry_id(data)
        r1 = _get(pb_api, eid)
        r2 = _get(pb_api, eid)
        assert r1.get("amount") == r2.get("amount")
        assert r1.get("total_quantity") == r2.get("total_quantity")

    @pytest.mark.live
    @pytest.mark.integrity
    def test_all_detail_keys_present_in_get(self, pb_api):
        data = _create(pb_api, _payload([_item()]))
        entry = _get(pb_api, _entry_id(data))
        details = entry.get("purchase_booking_details") or []
        assert details, "No details in GET response"
        row = details[0]
        for k in ["item_ref_id", "net_quantity", "rate",
                  "txn_currency_amount", "txn_currency_total_txn_amount"]:
            assert k in row, f"Missing key in detail response: {k}"

    @pytest.mark.live
    @pytest.mark.integrity
    def test_list_includes_created_entry(self, pb_api):
        data = _create(pb_api, _payload([_item()]))
        eid = _entry_id(data)
        listing = pb_api.list_pbs(page=1, page_size=25)
        assert listing is not None
        ids = [r.get("id") for r in (listing.get("screenmatlistingdata_set") or [])]
        assert eid in ids, f"Created PB {eid} not found in listing"
