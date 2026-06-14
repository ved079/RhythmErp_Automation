import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    generate_po_payload,
    build_po_payload,
)
from pages.private_b2b.modules.purchase_order.api.endpoints import SCREEN_NAME


class TestCreateValidation:
    @pytest.mark.api
    @pytest.mark.smoke
    def test_PO_C01_empty_payload(self, po_api):
        log.info("PO-C01 (API): Empty payload")
        empty_payload = {"id": "", "attribute_name": SCREEN_NAME, "details": []}
        po_api.create_and_expect_failure(empty_payload)
        po_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    def test_PO_C02_missing_supplier(self, po_api):
        log.info("PO-C02 (API): Missing supplier_ref_id")
        payload = generate_po_payload(fk_overrides={
            "parameter2": 1, "parameter3": 25, "parameter4": 1,
        })
        del payload["supplier_ref_id"]
        po_api.create_and_expect_failure(payload)
        po_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    def test_PO_C03_missing_parameter2(self, po_api):
        log.info("PO-C03 (API): Missing parameter2 (Department) — backend defaults it")
        payload = generate_po_payload(fk_overrides={
            "supplier_ref_id": 1, "parameter3": 25, "parameter4": 1,
        })
        del payload["parameter2"]
        result = po_api.create_po(payload)
        assert result is not None, f"PO creation should succeed (backend defaults parameter2). Status: {po_api._last_status}"

    @pytest.mark.api
    def test_PO_C04_missing_parameter4(self, po_api):
        log.info("PO-C04 (API): Missing parameter4 (Location) — backend defaults it")
        payload = generate_po_payload(fk_overrides={
            "supplier_ref_id": 1, "parameter2": 1, "parameter3": 25,
        })
        del payload["parameter4"]
        result = po_api.create_po(payload)
        assert result is not None, f"PO creation should succeed (backend defaults parameter4). Status: {po_api._last_status}"

    @pytest.mark.api
    def test_PO_C05_missing_po_item_type(self, po_api):
        log.info("PO-C05 (API): Missing po_item_type")
        payload = generate_po_payload(fk_overrides={
            "supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1,
        })
        del payload["po_item_type"]
        po_api.create_and_expect_failure(payload)
        po_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    def test_PO_C06_missing_grid_items(self, po_api):
        log.info("PO-C06 (API): Missing grid items — backend creates PO without items")
        payload = generate_po_payload(fk_overrides={
            "supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1,
        })
        del payload["purchasing_order_items_details"]
        result = po_api.create_po(payload)
        assert result is not None, f"PO creation should succeed (items are not required). Status: {po_api._last_status}"


class TestSupplierDropdown:
    @pytest.mark.api
    def test_PO_D01_supplier_has_valid_options(self, erp_api):
        log.info("PO-D01: Supplier dropdown has valid options")
        schema = erp_api.get_screen_schema(SCREEN_NAME)
        fields = schema.get("screendefinition_set", [])
        supplier_field = next(f for f in fields if f["field_key"] == "supplier_ref_id")
        options = supplier_field.get("filter_dropdown_raw_query") or []
        assert len(options) >= 1, "Supplier dropdown should have options"
        supplier_names = [o["key"] for o in options]
        assert "Maa Kalinga Commodities" in supplier_names

    @pytest.mark.api
    def test_PO_D02_location_has_valid_options(self, erp_api):
        log.info("PO-D02: Location dropdown has valid options")
        schema = erp_api.get_screen_schema(SCREEN_NAME)
        fields = schema.get("screendefinition_set", [])
        loc_field = next(f for f in fields if f["field_key"] == "parameter4")
        options = loc_field.get("filter_dropdown_raw_query") or []
        assert len(options) >= 1
        loc_names = [o["key"] for o in options]
        assert "Pune" in loc_names or "Mumbai" in loc_names


class TestCalculationBoundaries:
    @pytest.mark.api
    def test_PO_CALC01_zero_quantity(self, po_api):
        log.info("PO-CALC01: Zero quantity should be rejected (cannot be < 0)")
        payload = generate_po_payload(
            fk_overrides={"supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1},
            item_overrides=[{"quantity": 0.0, "rate": 100.0}],
        )
        status = po_api.create_and_expect_failure(payload)
        assert status == 400, f"Zero quantity should return 400, got {status}"

    @pytest.mark.api
    def test_PO_CALC02_zero_rate(self, po_api):
        log.info("PO-CALC02: Zero rate should produce zero amount")
        payload = generate_po_payload(
            fk_overrides={"supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1},
            item_overrides=[{"quantity": 50.0, "rate": 0.0}],
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        item = entry["purchasing_order_items_details"][0]
        assert float(item.get("txn_currency_amount_detail", 0)) == 0.0

    @pytest.mark.api
    def test_PO_CALC03_large_values(self, po_api):
        log.info("PO-CALC03: Large qty and rate")
        payload = generate_po_payload(
            fk_overrides={"supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1},
            item_overrides=[{"quantity": 10000.0, "rate": 9999.0}],
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        item = entry["purchasing_order_items_details"][0]
        expected = 10000.0 * 9999.0
        assert abs(float(item.get("txn_currency_amount_detail", 0)) - expected) < 1.0

    @pytest.mark.api
    def test_PO_CALC04_null_discount_percent(self, po_api):
        log.info("PO-CALC04: Null discount percent should give zero discount")
        payload = generate_po_payload(
            fk_overrides={"supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1},
        )
        payload["additional_details"]["txn_currency_discount_percent"] = None
        payload["additional_details"]["txn_currency_discount_amount"] = 0
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        add = entry.get("additional_details", {})
        assert float(add.get("txn_currency_discount_amount", 0)) == 0.0


    @pytest.mark.api
    def test_PO_CALC05_non_zero_tax_rate(self, po_api):
        log.info("PO-CALC05: Non-zero tax rate — verify tax calculated")
        payload = build_po_payload(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            items=[{"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                    "quantity": 100.0, "rate": 200.0, "tax_rate": 5.0,
                    "expected_delivery_date": "2026-06-20"}],
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        item = entry["purchasing_order_items_details"][0]
        assert float(item["txn_currency_amount_detail"]) == 20000.0
        assert float(item["txn_currency_tax_amount_details"]) == 1000.0
        assert float(item["total_amount"]) == 21000.0

    @pytest.mark.api
    def test_PO_CALC06_transport_charges_stored(self, po_api):
        log.info("PO-CALC06: Transport charges stored as-is (not computed)")
        payload = build_po_payload(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            additional_details={
                "transportation_charges": 500.0,
                "txn_currency_discount_percent": None,
                "txn_currency_discount_amount": 0,
                "txn_currency_interest_percent": None,
                "txn_currency_interest_amount": 0,
                "remark": None,
            },
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        add = entry.get("additional_details", {})
        assert float(add.get("transportation_charges", 0)) == 500.0

    @pytest.mark.api
    def test_PO_CALC07_conversion_rate_not_one(self, po_api):
        log.info("PO-CALC07: Conversion rate != 1 — verify stored")
        payload = build_po_payload(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            txn_currency=108, base_currency=8, conversion_rate=83.0,
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        assert float(entry.get("conversion_rate", 0)) == 83.0
        assert entry.get("txn_currency") == 108
        assert entry.get("base_currency") == 8

    @pytest.mark.api
    def test_PO_CALC08_multi_line_mixed_tax(self, po_api):
        log.info("PO-CALC08: Multiple grid items with mixed tax — line-by-line verify")
        items = [
            {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
             "quantity": 10.0, "rate": 100.0, "tax_rate": 5.0,
             "expected_delivery_date": "2026-06-20"},
            {"item_ref_id": 6, "hsn_sac_no": 3, "uom": 5,
             "quantity": 5.0, "rate": 200.0, "tax_rate": 12.0,
             "expected_delivery_date": "2026-06-25"},
        ]
        payload = build_po_payload(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            items=items,
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        lines = entry["purchasing_order_items_details"]
        assert len(lines) == 2
        assert float(lines[0]["txn_currency_amount_detail"]) == 1000.0
        assert float(lines[0]["txn_currency_tax_amount_details"]) == 50.0
        assert float(lines[0]["total_amount"]) == 1050.0
        assert float(lines[1]["txn_currency_amount_detail"]) == 1000.0
        assert float(lines[1]["txn_currency_tax_amount_details"]) == 120.0
        assert float(lines[1]["total_amount"]) == 1120.0
        assert float(entry["txn_currency_total_amount"]) == 2170.0

    @pytest.mark.api
    def test_PO_CALC09_negative_quantity_rejected(self, po_api):
        log.info("PO-CALC09: Negative quantity — should be rejected")
        payload = generate_po_payload(
            fk_overrides={"supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1},
            item_overrides=[{"quantity": -10.0, "rate": 100.0}],
        )
        status = po_api.create_and_expect_failure(payload)
        assert status in (400, 500), f"Negative qty should fail, got {status}"

    @pytest.mark.api
    def test_PO_CALC10_discount_and_interest_simultaneously(self, po_api):
        log.info("PO-CALC10: Both discount% + interest% simultaneously")
        payload = build_po_payload(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            items=[{"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                    "quantity": 10.0, "rate": 100.0,
                    "expected_delivery_date": "2026-06-20"}],
            additional_details={
                "transportation_charges": 0,
                "txn_currency_discount_percent": 5.0,
                "txn_currency_discount_amount": 0,
                "txn_currency_interest_percent": 10.0,
                "txn_currency_interest_amount": 0,
                "remark": None,
            },
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        add = entry.get("additional_details", {})
        assert float(add.get("txn_currency_discount_amount", 0)) == 50.0
        assert float(add.get("txn_currency_interest_amount", 0)) == 100.0
        assert float(entry["txn_currency_total_amount"]) == 1000.0


class TestTransactionRef:
    @pytest.mark.api
    @pytest.mark.smoke
    def test_PO_T01_transaction_ref_format(self, po_api):
        log.info("PO-T01: Transaction Ref No follows format")
        payload = generate_po_payload(fk_overrides={
            "supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1,
        })
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        ref_no = entry.get("transaction_ref_no", "")
        assert ref_no.startswith("PUR/"), f"Unexpected ref format: {ref_no}"
        parts = ref_no.split("/")
        assert len(parts) == 3, f"Unexpected ref parts: {parts}"

    @pytest.mark.api
    def test_PO_T02_transaction_ref_increments(self, po_api):
        log.info("PO-T02: Transaction Ref increments sequentially")
        payload1 = generate_po_payload(fk_overrides={
            "supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1,
        })
        payload2 = generate_po_payload(fk_overrides={
            "supplier_ref_id": 1, "parameter2": 1, "parameter3": 25, "parameter4": 1,
        })
        r1 = po_api.create_po(payload1)
        r2 = po_api.create_po(payload2)
        assert r1 is not None and r2 is not None
        e1 = po_api.get_po(r1.get("id"))
        e2 = po_api.get_po(r2.get("id"))
        ref1 = e1.get("transaction_ref_no", "")
        ref2 = e2.get("transaction_ref_no", "")
        assert ref1 != ref2, "Refs should be different"
        num1 = int(ref1.split("/")[-1])
        num2 = int(ref2.split("/")[-1])
        assert num2 > num1, f"Ref should increment: {ref1} -> {ref2}"
