import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    build_po_payload,
    generate_po_payload,
    SUPPLIER_IDS,
)


class TestLiveCRUD:
    @pytest.mark.api
    @pytest.mark.smoke
    def test_create_po_success(self, po_api):
        payload = generate_po_payload(fk_overrides={
            "supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1,
        })
        result = po_api.create_po(payload)
        assert result is not None, f"PO creation failed"
        entry_id = result.get("id") or result.get("entry_id")
        assert entry_id is not None, "No entry ID returned"

    @pytest.mark.api
    @pytest.mark.smoke
    def test_get_po_by_id(self, po_api):
        payload = generate_po_payload(fk_overrides={
            "supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1,
        })
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        assert entry is not None, f"Failed to fetch PO {entry_id}"
        assert entry.get("id") == entry_id or entry.get("id") == int(entry_id)

    @pytest.mark.api
    def test_list_pos(self, po_api):
        listing = po_api.list_pos(page=1, page_size=5)
        assert listing is not None, "List returned None"
        items = listing.get("screenmatlistingdata_set", [])
        assert len(items) >= 0

    @pytest.mark.api
    def test_create_po_with_all_fields(self, po_api):
        payload = build_po_payload(
            supplier_ref_id=1,
            po_item_type=113,
            po_type=25,
            txn_currency=8,
            base_currency=8,
            conversion_rate=1.0,
            parameter1=1,
            parameter2=1,
            parameter3=25,
            parameter4=1,
            parameter5=2,
            parameter6=1,
            supplier_details={
                "supplier_payment_terms": 550,
                "supplier_delivery_terms": 130,
                "packing_forwarding_ref_id": 89,
                "supplier_ship_from": 1,
                "supplier_bill_from": 2,
            },
            items=[
                {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                 "alternate_uom": 3, "alternate_quantity": "25.0",
                 "quantity": 25.0, "rate": 150.0,
                 "expected_delivery_date": "2026-07-01"},
                {"item_ref_id": 6, "hsn_sac_no": 2, "uom": 3,
                 "alternate_uom": 3, "alternate_quantity": "10.0",
                 "quantity": 10.0, "rate": 300.0,
                 "expected_delivery_date": "2026-07-15"},
            ],
        )
        result = po_api.create_po(payload)
        assert result is not None, "Full PO creation failed"

    @pytest.mark.api
    def test_create_po_returns_id(self, po_api):
        payload = generate_po_payload(fk_overrides={
            "supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1,
        })
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        assert entry_id is not None
        assert isinstance(entry_id, (int, str))

    @pytest.mark.api
    def test_get_po_has_calculated_fields(self, po_api):
        payload = generate_po_payload(fk_overrides={
            "supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1,
        })
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        assert entry is not None
        items = entry.get("purchasing_order_items_details", [])
        assert len(items) >= 1
        item = items[0]
        assert "txn_currency_amount_detail" in item
        assert "txn_currency_tax_amount_details" in item
        assert "total_amount" in item
        assert "txn_currency_total_amount" in entry

    @pytest.mark.api
    def test_create_with_validation_failure(self, po_api):
        payload = {"id": "", "attribute_name": "Purchase Order", "details": []}
        status = po_api.create_and_expect_failure(payload)
        po_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    def test_generated_transaction_ref_no(self, po_api):
        payload = generate_po_payload(fk_overrides={
            "supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1,
        })
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        assert entry is not None
        ref_no = entry.get("transaction_ref_no", "")
        assert ref_no.startswith("PUR/"), f"Unexpected ref no format: {ref_no}"
