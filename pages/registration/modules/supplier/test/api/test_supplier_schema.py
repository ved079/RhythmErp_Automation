"""
test_supplier_schema.py — Verify Supplier code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.supplier.data.supplier_data import (
    FIELD_VALIDATION_RULES,
    OWNERSHIP_STATUS_IDS,
    PO_TYPE_IDS,
    PAYMENT_TERMS_IDS,
    DELIVERY_TERMS_IDS,
    MODE_OF_DELIVERY_IDS,
    BANK_DOC_IDS,
    ADDRESS_TYPE_IDS,
    ACCOUNT_TYPE_IDS,
    DEFAULT_SUPPLIER_FK_IDS,
    OWNERSHIP_STATUS_NAMES,
    BANK_DOC_NAMES,
    PAYMENT_TERMS_NAMES,
)


@pytest.mark.schema
class TestSupplierSchema:
    """Verify the Supplier screen schema matches our code expectations."""

    def test_field_validation_rules_has_root_fields(self):
        """FIELD_VALIDATION_RULES should cover root-level fields."""
        root_fields = {"party_ref_id", "ownership_status_ref_id", "name",
                       "po_type_ref_id", "email_id", "mobile_no",
                       "default_currency_ref_id", "pan_no",
                       "is_msme_registered", "status"}
        assert root_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_additional_details(self):
        """FIELD_VALIDATION_RULES should cover Additional Details fields."""
        additional_fields = {"display_name_as", "office_no",
                            "payment_terms_ref_id", "delivery_terms_ref_id",
                            "mode_of_delivery_ref_id", "is_gst_set_off",
                            "is_tds_applicable"}
        assert additional_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_address_fields(self):
        """FIELD_VALIDATION_RULES should cover Address fields."""
        address_fields = {"address_type", "country_ref_id_id",
                          "state_ref_id_id", "district_ref_id_id",
                          "sub_district_ref_id_id", "village_ref_id_id",
                          "address", "pin_code", "gstin"}
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

    def test_ownership_status_has_6_options(self):
        """Ownership Status dropdown should have 6 options."""
        assert FIELD_VALIDATION_RULES["ownership_status_ref_id"]["fk_options_count"] == 6

    def test_payment_terms_has_6_options(self):
        """Payment Terms dropdown should have 6 options."""
        assert FIELD_VALIDATION_RULES["payment_terms_ref_id"]["fk_options_count"] == 6

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
        """DEFAULT_SUPPLIER_FK_IDS values should be in valid pools."""
        assert DEFAULT_SUPPLIER_FK_IDS["ownership_status_ref_id"] in OWNERSHIP_STATUS_IDS
        assert DEFAULT_SUPPLIER_FK_IDS["po_type_ref_id"] in PO_TYPE_IDS
        assert DEFAULT_SUPPLIER_FK_IDS["payment_terms_ref_id"] in PAYMENT_TERMS_IDS
        assert DEFAULT_SUPPLIER_FK_IDS["bank_doc_id"] in BANK_DOC_IDS

    def test_ownership_status_names_complete(self):
        """OWNERSHIP_STATUS_NAMES should map every ID."""
        for oid in OWNERSHIP_STATUS_IDS:
            assert oid in OWNERSHIP_STATUS_NAMES, f"Missing name for ownership {oid}"

    def test_bank_doc_names_complete(self):
        """BANK_DOC_NAMES should map every ID."""
        for bid in BANK_DOC_IDS:
            assert bid in BANK_DOC_NAMES, f"Missing name for bank doc {bid}"

    def test_payment_terms_names_complete(self):
        """PAYMENT_TERMS_NAMES should map every ID."""
        for pid in PAYMENT_TERMS_IDS:
            assert pid in PAYMENT_TERMS_NAMES, f"Missing name for payment term {pid}"

    def test_fk_pool_lengths_match_rules(self):
        """FK pool lengths should match FIELD_VALIDATION_RULES counts."""
        assert len(OWNERSHIP_STATUS_IDS) == FIELD_VALIDATION_RULES["ownership_status_ref_id"]["fk_options_count"]
        assert len(PO_TYPE_IDS) == FIELD_VALIDATION_RULES["po_type_ref_id"]["fk_options_count"]
        assert len(PAYMENT_TERMS_IDS) == FIELD_VALIDATION_RULES["payment_terms_ref_id"]["fk_options_count"]
        assert len(BANK_DOC_IDS) == FIELD_VALIDATION_RULES["bank_doc_id"]["fk_options_count"]

    def test_address_type_has_dual_requirement_note(self):
        """FIELD_VALIDATION_RULES for address_type should note dual requirement."""
        rule = FIELD_VALIDATION_RULES["address_type"]
        assert rule["required"] is True
        note = rule.get("note", "")
        assert "Shipping" in note and "Billing" in note, (
            f"address_type rule should note both types required, got: {note}"
        )

    def test_default_fk_ids_has_both_address_types(self):
        """DEFAULT_SUPPLIER_FK_IDS must include both shipping and billing address types."""
        assert "shipping_address_type" in DEFAULT_SUPPLIER_FK_IDS
        assert "billing_address_type" in DEFAULT_SUPPLIER_FK_IDS
        assert DEFAULT_SUPPLIER_FK_IDS["shipping_address_type"] in ADDRESS_TYPE_IDS
        assert DEFAULT_SUPPLIER_FK_IDS["billing_address_type"] in ADDRESS_TYPE_IDS
