import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log


class TestSchemaStructure:
    @pytest.mark.schema
    def test_schema_returns_valid(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        assert schema is not None, "Schema fetch returned None"
        assert schema.get("attribute_name") == "Purchase Order"
        assert "screendefinition_set" in schema

    @pytest.mark.schema
    def test_master_table_name(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        assert schema.get("master_table_name") == "tbl_purchase_order"

    @pytest.mark.schema
    def test_detail_table_name(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        assert schema.get("detail_table_name") == "tbl_purchase_order_details"

    @pytest.mark.schema
    def test_all_required_master_fields_present(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        fields = schema.get("screendefinition_set", [])
        field_keys = {f["field_key"] for f in fields}

        required = {
            "transaction_date", "supplier_ref_id", "transaction_ref_no",
            "po_item_type", "po_type", "txn_currency", "txn_currency_total_amount",
            "base_currency", "parameter1", "parameter2", "parameter3", "parameter4",
            "conversion_rate", "additional_details", "supplier_details",
            "purchasing_order_items_details",
        }
        missing = required - field_keys
        assert not missing, f"Missing master fields: {missing}"

    @pytest.mark.schema
    def test_required_fields_flagged(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        fields = schema.get("screendefinition_set", [])
        required_keys = {f["field_key"] for f in fields if f.get("is_required")}

        assert "supplier_ref_id" in required_keys
        assert "po_item_type" in required_keys
        assert "parameter2" in required_keys
        assert "parameter3" in required_keys
        assert "parameter4" in required_keys

    @pytest.mark.schema
    def test_supplier_ref_id_has_auto_patch(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        fields = schema.get("screendefinition_set", [])
        supplier_field = next(f for f in fields if f["field_key"] == "supplier_ref_id")
        assert supplier_field.get("is_onchange_event") is True
        apq = supplier_field.get("auto_patch_query", "")
        assert "party_address_details" in apq
        assert "address_type" in apq
        assert "base_currency" in apq
        assert "tbl_tenant_details" in apq

    @pytest.mark.schema
    def test_grid_field_has_correct_structure(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        fields = schema.get("screendefinition_set", [])
        grid = next(f for f in fields if f["field_key"] == "purchasing_order_items_details")
        assert grid.get("is_grid") is True
        assert grid.get("detail_table_name") == "tbl_purchase_order_details"
        children = grid.get("children", [])
        child_keys = {c["field_key"] for c in children}

        required_children = {
            "item_ref_id", "hsn_sac_no", "uom", "quantity", "rate",
            "txn_currency_amount_details", "tax_rate", "txn_currency_tax_amount",
            "total_amount", "expected_delivery_date",
        }
        missing = required_children - child_keys
        assert not missing, f"Missing grid children fields: {missing}"

    @pytest.mark.schema
    def test_grid_required_children(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        fields = schema.get("screendefinition_set", [])
        grid = next(f for f in fields if f["field_key"] == "purchasing_order_items_details")
        children = grid.get("children", [])
        required_keys = {c["field_key"] for c in children if c.get("is_required")}
        assert "item_ref_id" in required_keys
        assert "quantity" in required_keys
        assert "rate" in required_keys
        assert "expected_delivery_date" in required_keys

    @pytest.mark.schema
    def test_additional_details_stepper_children(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        fields = schema.get("screendefinition_set", [])
        stepper = next(f for f in fields if f["field_key"] == "additional_details")
        assert stepper.get("is_stepper_name") is True
        children = stepper.get("children", [])
        child_keys = {c["field_key"] for c in children}
        expected = {"transportation_charges", "txn_currency_discount_percent",
                     "txn_currency_discount_amount", "txn_currency_interest_percent",
                     "txn_currency_interest_amount", "remark"}
        assert child_keys == expected, f"additional_details children mismatch"

    @pytest.mark.schema
    def test_supplier_details_stepper_children(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        fields = schema.get("screendefinition_set", [])
        stepper = next(f for f in fields if f["field_key"] == "supplier_details")
        assert stepper.get("is_stepper_name") is True
        children = stepper.get("children", [])
        child_keys = {c["field_key"] for c in children}
        expected = {"supplier_payment_terms", "supplier_delivery_terms",
                     "packing_forwarding_ref_id", "supplier_ship_from", "supplier_bill_from"}
        assert child_keys == expected, f"supplier_details children mismatch"

    @pytest.mark.schema
    def test_grid_field_has_auto_patch_on_item(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        fields = schema.get("screendefinition_set", [])
        grid = next(f for f in fields if f["field_key"] == "purchasing_order_items_details")
        children = grid.get("children", [])
        item_field = next(c for c in children if c["field_key"] == "item_ref_id")
        assert item_field.get("is_onchange_event") is True
        apq = item_field.get("auto_patch_query", "")
        assert apq, "item_ref_id should have auto_patch_query"

    @pytest.mark.schema
    def test_all_dropdowns_have_valid_options(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        fields = schema.get("screendefinition_set", [])
        dropdown_fields = ["supplier_ref_id", "parameter2", "parameter4", "po_item_type", "po_type"]
        for f in fields:
            if f["field_key"] in dropdown_fields:
                raw = f.get("filter_dropdown_raw_query")
                assert raw, f"{f['field_key']} should have filter_dropdown_raw_query"
                assert len(raw) >= 1, f"{f['field_key']} dropdown should have options"

    @pytest.mark.schema
    def test_master_field_types(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        fields = schema.get("screendefinition_set", [])
        field_map = {f["field_key"]: f for f in fields}
        assert field_map["transaction_date"]["field_type_val"] == "date"
        assert field_map["supplier_ref_id"]["field_type_val"] == "dropdown"
        assert field_map["po_item_type"]["field_type_val"] == "dropdown"
        assert field_map["txn_currency_total_amount"]["field_type_val"] in ("integer", "varchar", "decimal")

    @pytest.mark.schema
    def test_grid_child_field_types(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        fields = schema.get("screendefinition_set", [])
        grid = next(f for f in fields if f["field_key"] == "purchasing_order_items_details")
        children = {c["field_key"]: c for c in grid.get("children", [])}
        assert children["item_ref_id"]["field_type_val"] == "dropdown"
        assert children["quantity"]["field_type_val"] in ("integer", "decimal", "varchar")
        assert children["rate"]["field_type_val"] in ("integer", "decimal", "varchar")
        assert children["expected_delivery_date"]["field_type_val"] == "date"

    @pytest.mark.schema
    def test_is_required_flags_match_assumptions(self, erp_api):
        schema = erp_api.get_screen_schema("Purchase Order")
        fields = schema.get("screendefinition_set", [])
        required_keys = {f["field_key"] for f in fields if f.get("is_required")}
        assert "supplier_ref_id" in required_keys
        assert "po_item_type" in required_keys
        assert "parameter2" in required_keys
        grid = next(f for f in fields if f["field_key"] == "purchasing_order_items_details")
        grid_required = {c["field_key"] for c in grid.get("children", []) if c.get("is_required")}
        assert "item_ref_id" in grid_required
        assert "quantity" in grid_required
        assert "expected_delivery_date" in grid_required
