"""
test_schema.py — Purchase Booking schema verification tests.

Verifies that the ERP screen schema matches our expectations so we catch
any backend schema drift before it breaks batch creates.
"""

import pytest
from pages.private_b2b.modules.purchase_booking.api.endpoints import SCREEN_NAME


class TestSchemaStructure:
    @pytest.mark.schema
    @pytest.mark.live
    def test_schema_reachable(self, pb_api):
        client = pb_api.client
        schema = client.get_screen_schema(SCREEN_NAME)
        assert schema is not None, f"Cannot reach schema for '{SCREEN_NAME}'"

    @pytest.mark.schema
    @pytest.mark.live
    def test_screen_name_matches(self, pb_api):
        schema = pb_api.client.get_screen_schema(SCREEN_NAME)
        assert schema["attribute_name"] == SCREEN_NAME

    @pytest.mark.schema
    @pytest.mark.live
    def test_master_table_name(self, pb_api):
        schema = pb_api.client.get_screen_schema(SCREEN_NAME)
        assert schema.get("master_table_name") == "tbl_purchase_booking_mst"

    @pytest.mark.schema
    @pytest.mark.live
    def test_detail_table_name(self, pb_api):
        schema = pb_api.client.get_screen_schema(SCREEN_NAME)
        assert schema.get("detail_table_name") == "tbl_purchase_booking_details"

    @pytest.mark.schema
    @pytest.mark.live
    def test_sub_detail_table_name(self, pb_api):
        schema = pb_api.client.get_screen_schema(SCREEN_NAME)
        assert schema.get("sub_detail_table_name") == "tbl_purchase_booking_sub_details"

    @pytest.mark.schema
    @pytest.mark.live
    def test_expected_master_fields_present(self, pb_api):
        schema = pb_api.client.get_screen_schema(SCREEN_NAME)
        all_fields = {f["field_key"] for f in schema.get("screendefinition_set", [])}
        expected = {
            "transaction_date", "supplier_ref_id", "supplier_ref_type",
            "qc_ref_id", "parameter1", "parameter2", "parameter5", "parameter6",
            "base_currency", "txn_currency", "amount", "total_quantity",
            "is_tds_applicable", "remark",
            "purchase_booking_details", "other_charges", "grn_details",
        }
        missing = expected - all_fields
        assert not missing, f"Missing master schema fields: {missing}"

    @pytest.mark.schema
    @pytest.mark.live
    def test_purchase_booking_details_is_stepper_grid(self, pb_api):
        schema = pb_api.client.get_screen_schema(SCREEN_NAME)
        for f in schema.get("screendefinition_set", []):
            if f["field_key"] == "purchase_booking_details":
                assert f["is_stepper_name"] is True
                assert f["is_grid"] is True
                return
        pytest.fail("purchase_booking_details stepper not found in schema")

    @pytest.mark.schema
    @pytest.mark.live
    def test_detail_has_quantity_details_sub_grid(self, pb_api):
        schema = pb_api.client.get_screen_schema(SCREEN_NAME)
        for f in schema.get("screendefinition_set", []):
            if f["field_key"] == "purchase_booking_details":
                child_keys = {c["field_key"] for c in f.get("children", [])}
                assert "quantity_details" in child_keys
                return
        pytest.fail("purchase_booking_details not found")

    @pytest.mark.schema
    @pytest.mark.live
    def test_supplier_ref_type_dropdown_includes_farmer_and_supplier(self, pb_api):
        opts = pb_api.client.get_dropdown_options(SCREEN_NAME, "supplier_ref_type")
        ids = {o["id"] for o in opts}
        assert 1769 in ids, "Farmer role type (1769) not in dropdown"
        assert 1771 in ids, "Supplier role type (1771) not in dropdown"

    @pytest.mark.schema
    @pytest.mark.live
    def test_location_dropdown_non_empty(self, pb_api):
        opts = pb_api.client.get_dropdown_options(SCREEN_NAME, "parameter5")
        assert len(opts) > 0, "No locations in PB parameter5 dropdown"

    @pytest.mark.schema
    @pytest.mark.live
    def test_supplier_dropdown_non_empty(self, pb_api):
        opts = pb_api.client.get_dropdown_options(SCREEN_NAME, "supplier_ref_id")
        assert len(opts) > 0, "No suppliers in PB supplier_ref_id dropdown"
