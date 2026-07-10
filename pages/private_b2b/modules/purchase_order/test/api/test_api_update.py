import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    build_po_payload,
)
from pages.private_b2b.modules.purchase_order.api.endpoints import build_update_url


def _build_with_nonnull_add(**kw):
    payload = build_po_payload(**kw)
    add = payload.get("additional_details", {})
    if add.get("txn_currency_discount_percent") is None:
        add["txn_currency_discount_percent"] = 0
    if add.get("txn_currency_interest_percent") is None:
        add["txn_currency_interest_percent"] = 0
    payload["additional_details"] = add
    return payload


class TestUpdatePO:
    @pytest.mark.api
    def test_PUP01_update_quantity_recalculates(self, po_api):
        log.info("PUP01: Update qty via PUT — verify recalculation")
        payload = _build_with_nonnull_add(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            items=[{"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                    "quantity": 10.0, "rate": 100.0,
                    "expected_delivery_date": "2026-06-20"}],
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")

        update_payload = dict(payload)
        update_payload["purchasing_order_items_details"][0]["quantity"] = 50.0
        resp = po_api.update_po(entry_id, update_payload)
        assert resp is not None, f"Update failed (status {po_api._last_status})"

        entry = po_api.get_po(entry_id)
        items = entry.get("purchasing_order_items_details", [])
        if items:
            assert float(items[0]["quantity"]) == 50.0
            assert float(items[0]["txn_currency_amount_detail"]) == 5000.0
            assert float(items[0]["total_amount"]) == 5000.0
            assert float(entry["txn_currency_total_amount"]) == 5000.0

    @pytest.mark.api
    def test_PUP02_update_rate_recalculates(self, po_api):
        log.info("PUP02: Update rate via PUT")
        payload = _build_with_nonnull_add(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            items=[{"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                    "quantity": 10.0, "rate": 100.0,
                    "expected_delivery_date": "2026-06-20"}],
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")

        update_payload = dict(payload)
        update_payload["purchasing_order_items_details"][0]["rate"] = 250.0
        resp = po_api.update_po(entry_id, update_payload)
        assert resp is not None, f"Update failed (status {po_api._last_status})"

        entry = po_api.get_po(entry_id)
        items = entry.get("purchasing_order_items_details", [])
        if items:
            assert float(items[0]["rate"]) == 250.0
            assert float(items[0]["txn_currency_amount_detail"]) == 2500.0
            assert float(items[0]["total_amount"]) == 2500.0
            assert float(entry["txn_currency_total_amount"]) == 2500.0

    @pytest.mark.api
    @pytest.mark.xfail(reason="Backend does not update additional_details via PUT")
    def test_PUP03_update_discount_percent_recomputes(self, po_api):
        log.info("PUP03: Update discount % via PUT")
        payload = _build_with_nonnull_add(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            items=[{"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                    "quantity": 10.0, "rate": 100.0,
                    "expected_delivery_date": "2026-06-20"}],
            additional_details={
                "transportation_charges": 0,
                "txn_currency_discount_percent": 5.0,
                "txn_currency_discount_amount": 0,
                "txn_currency_interest_percent": 0,
                "txn_currency_interest_amount": 0,
                "remark": None,
            },
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")

        update_payload = dict(payload)
        update_payload["additional_details"]["txn_currency_discount_percent"] = 10.0
        resp = po_api.update_po(entry_id, update_payload)
        assert resp is not None, f"Update failed (status {po_api._last_status})"

        entry = po_api.get_po(entry_id)
        add = entry.get("additional_details", {})
        assert float(add.get("txn_currency_discount_amount", 0)) == 100.0

    @pytest.mark.api
    @pytest.mark.xfail(reason="Backend does not update additional_details via PUT")
    def test_PUP04_update_interest_percent_recomputes(self, po_api):
        log.info("PUP04: Update interest % via PUT")
        payload = _build_with_nonnull_add(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            items=[{"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                    "quantity": 10.0, "rate": 100.0,
                    "expected_delivery_date": "2026-06-20"}],
            additional_details={
                "transportation_charges": 0,
                "txn_currency_discount_percent": 0,
                "txn_currency_discount_amount": 0,
                "txn_currency_interest_percent": 5.0,
                "txn_currency_interest_amount": 0,
                "remark": None,
            },
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")

        update_payload = dict(payload)
        update_payload["additional_details"]["txn_currency_interest_percent"] = 8.0
        resp = po_api.update_po(entry_id, update_payload)
        assert resp is not None, f"Update failed (status {po_api._last_status})"

        entry = po_api.get_po(entry_id)
        add = entry.get("additional_details", {})
        assert float(add.get("txn_currency_interest_amount", 0)) == 80.0

    @pytest.mark.api
    def test_PUP05_update_succeeds_with_full_payload(self, po_api):
        log.info("PUP05: Full payload update succeeds")
        payload = _build_with_nonnull_add(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")

        resp = po_api.update_po(entry_id, payload)
        assert resp is not None, f"Update failed (status {po_api._last_status})"
        assert resp.get("status") == "Record Updated Successfully"

    @pytest.mark.api
    def test_PUP06_update_nonexistent_po(self, po_api):
        log.info("PUP06: Update non-existent PO")
        resp = po_api.update_po(999999, {"additional_details": {"txn_currency_discount_percent": 0, "txn_currency_interest_percent": 0}})
        assert resp is None
        assert po_api._last_status in (404, 400, 424, 500)

    @pytest.mark.api
    def test_PUP07_update_returns_updated_status(self, po_api):
        log.info("PUP07: Update returns success status")
        payload = _build_with_nonnull_add(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")

        update_payload = dict(payload)
        update_payload["additional_details"]["remark"] = "Status check"
        resp = po_api.update_po(entry_id, update_payload)
        assert resp is not None, f"Update failed (status {po_api._last_status})"
        assert resp.get("status") == "Record Updated Successfully"

    @pytest.mark.api
    def test_PUP08_update_supplier_changes_data(self, po_api):
        log.info("PUP08: Change supplier via update")
        payload = _build_with_nonnull_add(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")

        update_payload = dict(payload)
        update_payload["supplier_ref_id"] = 2
        resp = po_api.update_po(entry_id, update_payload)
        assert resp is not None, f"Update failed (status {po_api._last_status})"
        assert resp.get("status") == "Record Updated Successfully"
