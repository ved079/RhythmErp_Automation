"""
test_customer_schema.py — Verify Customer code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.customer.data.customer_data import (
    FIELD_VALIDATION_RULES,
    OWNERSHIP_STATUS_IDS,
    SUPPLY_TYPE_IDS,
    SALE_TYPE_IDS,
    PAYMENT_TERMS_IDS,
    DELIVERY_TERMS_IDS,
    MODE_OF_DELIVERY_IDS,
    BANK_DOC_IDS,
    ADDRESS_TYPE_IDS,
    ACCOUNT_TYPE_IDS,
    PREFERRED_PAYMENT_METHOD_IDS,
    COURIER_TERMS_IDS,
    GST_REGISTRATION_TYPE_IDS,
    DEFAULT_CUSTOMER_FK_IDS,
    OWNERSHIP_STATUS_NAMES,
    SUPPLY_TYPE_NAMES,
    SALE_TYPE_NAMES,
    BANK_DOC_NAMES,
    PAYMENT_TERMS_NAMES,
    PREFERRED_PAYMENT_METHOD_NAMES,
    COURIER_TERMS_NAMES,
    GST_REGISTRATION_TYPE_NAMES,
)


@pytest.mark.schema
class TestCustomerSchema:
    """Verify the Customer screen schema matches our code expectations."""

    def test_field_validation_rules_has_root_fields(self):
        """FIELD_VALIDATION_RULES should cover root-level fields."""
        root_fields = {"party_ref_id", "ownership_status_ref_id", "name",
                       "supply_type_ref_id", "sale_type_ref_id",
                       "default_currency_ref_id", "email_id", "mobile_no",
                       "pan_no", "status"}
        assert root_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_additional_details(self):
        """FIELD_VALIDATION_RULES should cover Additional Details fields."""
        additional_fields = {"display_name_as", "office_no",
                            "preferred_payment_method_ref_id",
                            "gst_registration_type",
                            "payment_terms_ref_id", "delivery_terms_ref_id",
                            "mode_of_delivery_ref_id", "courier_terms_ref_id",
                            "deposit", "quantity_tolerance", "rate_tolerance",
                            "is_tds_applicable", "is_gst_set_off",
                            "customer_status", "customer_type_ref_id",
                            "packing_material_ref_id"}
        assert additional_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_address_fields(self):
        """FIELD_VALIDATION_RULES should cover Address fields."""
        address_fields = {"address_type", "country_ref_id_id",
                          "state_ref_id_id", "district_ref_id_id",
                          "sub_district_ref_id_id", "village_ref_id_id",
                          "address", "pin_code", "gstin",
                          "registration_number"}
        assert address_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_bank_fields(self):
        """FIELD_VALIDATION_RULES should cover Bank fields."""
        bank_fields = {"bank_name", "bank_branch_code", "bank_ifsc_code",
                       "account_type", "bank_account_holder_name",
                       "bank_account_no", "bank_doc_id", "bank_attachment_path"}
        assert bank_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_pan_pattern_matches_schema(self):
        """PAN pattern should match [A-Z]{5}[0-9]{4}[A-Z]."""
        pan_rule = FIELD_VALIDATION_RULES["pan_no"]
        assert pan_rule["pattern"] == r"^[A-Z]{5}[0-9]{4}[A-Z]$"

    def test_ownership_status_has_8_options(self):
        """Ownership Status dropdown should have 8 options."""
        assert FIELD_VALIDATION_RULES["ownership_status_ref_id"]["fk_options_count"] == 8

    def test_supply_type_has_5_options(self):
        """Supply Type dropdown should have 5 options."""
        assert FIELD_VALIDATION_RULES["supply_type_ref_id"]["fk_options_count"] == 5

    def test_sale_type_has_4_options(self):
        """Sale Type dropdown should have 4 options."""
        assert FIELD_VALIDATION_RULES["sale_type_ref_id"]["fk_options_count"] == 4

    def test_payment_terms_has_5_options(self):
        """Payment Terms dropdown should have 5 options."""
        assert FIELD_VALIDATION_RULES["payment_terms_ref_id"]["fk_options_count"] == 5

    def test_preferred_payment_method_has_5_options(self):
        """Preferred Payment Method dropdown should have 5 options."""
        assert FIELD_VALIDATION_RULES["preferred_payment_method_ref_id"]["fk_options_count"] == 5

    def test_courier_terms_has_3_options(self):
        """Courier Terms dropdown should have 3 options."""
        assert FIELD_VALIDATION_RULES["courier_terms_ref_id"]["fk_options_count"] == 3

    def test_gst_registration_type_has_2_options(self):
        """GST Registration Type dropdown should have 2 options."""
        assert FIELD_VALIDATION_RULES["gst_registration_type"]["fk_options_count"] == 2

    def test_bank_doc_has_3_options(self):
        """Bank Proof dropdown should have 3 options."""
        assert FIELD_VALIDATION_RULES["bank_doc_id"]["fk_options_count"] == 3

    def test_pan_is_unique(self):
        """PAN should be marked as unique."""
        assert FIELD_VALIDATION_RULES["pan_no"]["unique"] is True

    def test_status_is_required(self):
        """Status should be required."""
        assert FIELD_VALIDATION_RULES["status"]["required"] is True

    def test_default_fk_ids_valid(self):
        """DEFAULT_CUSTOMER_FK_IDS values should be in valid pools."""
        assert DEFAULT_CUSTOMER_FK_IDS["ownership_status_ref_id"] in OWNERSHIP_STATUS_IDS
        assert DEFAULT_CUSTOMER_FK_IDS["supply_type_ref_id"] in SUPPLY_TYPE_IDS
        assert DEFAULT_CUSTOMER_FK_IDS["sale_type_ref_id"] in SALE_TYPE_IDS
        assert DEFAULT_CUSTOMER_FK_IDS["payment_terms_ref_id"] in PAYMENT_TERMS_IDS
        assert DEFAULT_CUSTOMER_FK_IDS["bank_doc_id"] in BANK_DOC_IDS
        assert DEFAULT_CUSTOMER_FK_IDS["preferred_payment_method_ref_id"] in PREFERRED_PAYMENT_METHOD_IDS
        assert DEFAULT_CUSTOMER_FK_IDS["courier_terms_ref_id"] in COURIER_TERMS_IDS
        assert DEFAULT_CUSTOMER_FK_IDS["gst_registration_type"] in GST_REGISTRATION_TYPE_IDS

    def test_ownership_status_names_complete(self):
        """OWNERSHIP_STATUS_NAMES should map every ID."""
        for oid in OWNERSHIP_STATUS_IDS:
            assert oid in OWNERSHIP_STATUS_NAMES, f"Missing name for ownership {oid}"

    def test_supply_type_names_complete(self):
        """SUPPLY_TYPE_NAMES should map every ID."""
        for sid in SUPPLY_TYPE_IDS:
            assert sid in SUPPLY_TYPE_NAMES, f"Missing name for supply type {sid}"

    def test_sale_type_names_complete(self):
        """SALE_TYPE_NAMES should map every ID."""
        for sid in SALE_TYPE_IDS:
            assert sid in SALE_TYPE_NAMES, f"Missing name for sale type {sid}"

    def test_bank_doc_names_complete(self):
        """BANK_DOC_NAMES should map every ID."""
        for bid in BANK_DOC_IDS:
            assert bid in BANK_DOC_NAMES, f"Missing name for bank doc {bid}"

    def test_payment_terms_names_complete(self):
        """PAYMENT_TERMS_NAMES should map every ID."""
        for pid in PAYMENT_TERMS_IDS:
            assert pid in PAYMENT_TERMS_NAMES, f"Missing name for payment term {pid}"

    def test_preferred_payment_method_names_complete(self):
        """PREFERRED_PAYMENT_METHOD_NAMES should map every ID."""
        for pid in PREFERRED_PAYMENT_METHOD_IDS:
            assert pid in PREFERRED_PAYMENT_METHOD_NAMES, f"Missing name for payment method {pid}"

    def test_courier_terms_names_complete(self):
        """COURIER_TERMS_NAMES should map every ID."""
        for cid in COURIER_TERMS_IDS:
            assert cid in COURIER_TERMS_NAMES, f"Missing name for courier term {cid}"

    def test_gst_registration_type_names_complete(self):
        """GST_REGISTRATION_TYPE_NAMES should map every ID."""
        for gid in GST_REGISTRATION_TYPE_IDS:
            assert gid in GST_REGISTRATION_TYPE_NAMES, f"Missing name for GST reg type {gid}"

    def test_fk_pool_lengths_match_rules(self):
        """FK pool lengths should match FIELD_VALIDATION_RULES counts."""
        assert len(OWNERSHIP_STATUS_IDS) == FIELD_VALIDATION_RULES["ownership_status_ref_id"]["fk_options_count"]
        assert len(SUPPLY_TYPE_IDS) == FIELD_VALIDATION_RULES["supply_type_ref_id"]["fk_options_count"]
        assert len(SALE_TYPE_IDS) == FIELD_VALIDATION_RULES["sale_type_ref_id"]["fk_options_count"]
        assert len(PAYMENT_TERMS_IDS) == FIELD_VALIDATION_RULES["payment_terms_ref_id"]["fk_options_count"]
        assert len(BANK_DOC_IDS) == FIELD_VALIDATION_RULES["bank_doc_id"]["fk_options_count"]
        assert len(PREFERRED_PAYMENT_METHOD_IDS) == FIELD_VALIDATION_RULES["preferred_payment_method_ref_id"]["fk_options_count"]
        assert len(COURIER_TERMS_IDS) == FIELD_VALIDATION_RULES["courier_terms_ref_id"]["fk_options_count"]
        assert len(GST_REGISTRATION_TYPE_IDS) == FIELD_VALIDATION_RULES["gst_registration_type"]["fk_options_count"]
