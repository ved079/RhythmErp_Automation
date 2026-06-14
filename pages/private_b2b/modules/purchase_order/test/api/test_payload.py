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
    generate_po_payloads,
    generate_random_fk_ids,
    compute_expected_results,
    assert_calculations_match,
    SUPPLIER_IDS,
    ITEM_IDS,
    LOCATION_IDS,
    DEPARTMENT_IDS,
    DIVISION_IDS,
    PO_TYPE_IDS,
    PO_ITEM_TYPE_IDS,
    CURRENCY_IDS,
    PAYMENT_TERMS_IDS,
    DELIVERY_TERMS_IDS,
    PACKING_FORWARDING_IDS,
    SUPPLIER_SHIP_FROM_IDS,
    SUPPLIER_BILL_FROM_IDS,
    HSN_SAC_IDS,
    UOM_IDS,
    DEFAULT_FK_IDS,
)


class TestPayloadStructure:
    @pytest.mark.api
    def test_build_po_payload_returns_dict(self):
        payload = build_po_payload()
        assert isinstance(payload, dict)
        assert payload.get("supplier_ref_id") == 1

    @pytest.mark.api
    def test_payload_has_all_root_keys(self):
        payload = build_po_payload()
        required_keys = {
            "transaction_date", "supplier_ref_id", "supplier_ref_type",
            "po_item_type", "po_type", "base_currency", "txn_currency",
            "conversion_rate", "parameter1", "parameter2", "parameter3",
            "parameter4", "parameter5", "parameter6",
            "additional_details", "supplier_details", "purchasing_order_items_details",
        }
        assert required_keys.issubset(payload.keys()), f"Missing keys: {required_keys - payload.keys()}"

    @pytest.mark.api
    def test_payload_has_inline_steppers(self):
        payload = build_po_payload()
        assert isinstance(payload.get("additional_details"), dict)
        assert isinstance(payload.get("supplier_details"), dict)
        assert isinstance(payload.get("purchasing_order_items_details"), list)

    @pytest.mark.api
    def test_additional_details_has_all_fields(self):
        payload = build_po_payload()
        add = payload["additional_details"]
        expected = {"transportation_charges", "txn_currency_discount_percent",
                     "txn_currency_discount_amount", "txn_currency_interest_percent",
                     "txn_currency_interest_amount", "remark"}
        assert set(add.keys()) == expected

    @pytest.mark.api
    def test_supplier_details_has_all_fields(self):
        payload = build_po_payload()
        sd = payload["supplier_details"]
        expected = {"supplier_payment_terms", "supplier_delivery_terms",
                     "packing_forwarding_ref_id", "supplier_ship_from", "supplier_bill_from"}
        assert set(sd.keys()) == expected

    @pytest.mark.api
    def test_grid_items_have_required_fields(self):
        payload = build_po_payload()
        item = payload["purchasing_order_items_details"][0]
        required = {"item_ref_id", "hsn_sac_no", "uom", "quantity", "rate", "expected_delivery_date"}
        assert required.issubset(item.keys()), f"Missing: {required - item.keys()}"

    @pytest.mark.api
    def test_default_conversion_rate_is_one(self):
        payload = build_po_payload()
        assert payload["conversion_rate"] == 1.0

    @pytest.mark.api
    def test_supplier_ref_type_is_supplier(self):
        payload = build_po_payload()
        assert payload["supplier_ref_type"] == "Supplier"

    @pytest.mark.api
    def test_custom_items_list(self):
        items = [{"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                  "quantity": 50.0, "rate": 200.0, "expected_delivery_date": "2026-07-01"}]
        payload = build_po_payload(items=items)
        assert len(payload["purchasing_order_items_details"]) == 1
        assert payload["purchasing_order_items_details"][0]["quantity"] == 50.0


class TestGeneratePayload:
    @pytest.mark.api
    def test_generate_po_payload_has_all_fields(self):
        payload = generate_po_payload()
        required_keys = {
            "transaction_date", "supplier_ref_id", "supplier_ref_type",
            "po_item_type", "po_type", "base_currency", "txn_currency",
            "conversion_rate", "parameter1", "parameter2", "parameter3",
            "parameter4", "parameter5", "parameter6",
            "additional_details", "supplier_details", "purchasing_order_items_details",
        }
        assert required_keys.issubset(payload.keys())

    @pytest.mark.api
    def test_generate_picks_valid_fk_ids(self):
        payload = generate_po_payload()
        assert payload["supplier_ref_id"] in SUPPLIER_IDS
        assert payload["parameter4"] in LOCATION_IDS
        assert payload["parameter2"] in DEPARTMENT_IDS
        assert payload["parameter1"] in DIVISION_IDS
        assert payload["po_type"] in PO_TYPE_IDS
        assert payload["po_item_type"] in PO_ITEM_TYPE_IDS

    @pytest.mark.api
    def test_generate_has_valid_supplier_details(self):
        payload = generate_po_payload()
        sd = payload["supplier_details"]
        assert sd["supplier_payment_terms"] in PAYMENT_TERMS_IDS
        assert sd["supplier_delivery_terms"] in DELIVERY_TERMS_IDS
        assert sd["packing_forwarding_ref_id"] in PACKING_FORWARDING_IDS
        assert sd["supplier_ship_from"] in SUPPLIER_SHIP_FROM_IDS
        assert sd["supplier_bill_from"] in SUPPLIER_BILL_FROM_IDS

    @pytest.mark.api
    def test_generate_has_valid_grid_item(self):
        payload = generate_po_payload()
        item = payload["purchasing_order_items_details"][0]
        assert item["item_ref_id"] in ITEM_IDS
        assert item["hsn_sac_no"] in HSN_SAC_IDS
        assert item["uom"] in UOM_IDS
        assert item["quantity"] > 0
        assert item["rate"] > 0

    @pytest.mark.api
    def test_generate_po_payloads_returns_correct_count(self):
        payloads = generate_po_payloads(5)
        assert len(payloads) == 5
        for p in payloads:
            assert isinstance(p, dict)

    @pytest.mark.api
    def test_generate_with_fk_overrides(self):
        payload = generate_po_payload(fk_overrides={"supplier_ref_id": 5, "parameter4": 3})
        assert payload["supplier_ref_id"] == 5
        assert payload["parameter4"] == 3

    @pytest.mark.api
    def test_generate_with_item_overrides(self):
        overrides = [{"quantity": 99.0, "rate": 250.0}]
        payload = generate_po_payload(fk_overrides={"supplier_ref_id": 1}, item_overrides=overrides)
        assert payload["purchasing_order_items_details"][0]["quantity"] == 99.0
        assert payload["purchasing_order_items_details"][0]["rate"] == 250.0


class TestRandomFKIds:
    @pytest.mark.api
    def test_generate_random_fk_ids_has_all_keys(self):
        fks = generate_random_fk_ids()
        expected_keys = {
            "supplier_ref_id", "po_item_type", "po_type", "txn_currency",
            "base_currency", "parameter1", "parameter2", "parameter3",
            "parameter4", "parameter5", "parameter6",
            "supplier_payment_terms", "supplier_delivery_terms",
            "packing_forwarding_ref_id", "supplier_ship_from", "supplier_bill_from",
            "item_ref_id", "hsn_sac_no", "uom",
        }
        assert set(fks.keys()) == expected_keys

    @pytest.mark.api
    def test_random_fk_ids_are_valid(self):
        fks = generate_random_fk_ids()
        assert fks["supplier_ref_id"] in SUPPLIER_IDS
        assert fks["parameter4"] in LOCATION_IDS
        assert fks["item_ref_id"] in ITEM_IDS
