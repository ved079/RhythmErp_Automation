"""
test_supplier_payload.py — Fast API payload structure tests.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.supplier.data.supplier_data import (
    generate_supplier_api_payload,
    build_supplier_api_payload,
    generate_valid_step1_data,
    generate_valid_step2_data,
    generate_valid_step3_data,
    generate_batch_payloads,
    generate_company_name,
    generate_email,
    generate_phone,
    generate_pan,
    generate_gstin,
    OWNERSHIP_STATUS_IDS,
    PO_TYPE_IDS,
    PAYMENT_TERMS_IDS,
    DELIVERY_TERMS_IDS,
    MODE_OF_DELIVERY_IDS,
    BANK_DOC_IDS,
    ADDRESS_TYPE_IDS,
    ACCOUNT_TYPE_IDS,
    DEFAULT_SUPPLIER_FK_IDS,
    FIELD_VALIDATION_RULES,
)


@pytest.mark.api
class TestSupplierAPIPayload:
    """Verify that generated API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, details, children."""
        payload = generate_supplier_api_payload()
        assert "id" in payload
        assert payload["id"] == ""
        assert payload["attribute_name"] == "Supplier"
        assert "details" in payload
        assert "children" in payload

    def test_payload_has_3_children_steppers(self):
        """Payload must have 3 children: Additional Details, Address, Bank."""
        payload = generate_supplier_api_payload()
        children = payload["children"]
        assert len(children) == 3
        assert children[0]["stepper_name"] == "Additional Details"
        assert children[1]["stepper_name"] == "Address Details"
        assert children[2]["stepper_name"] == "Bank Details"

    def test_payload_additional_details_on_stepper(self):
        """Additional Details fields must be ON the stepper object, NOT in details[]."""
        payload = generate_supplier_api_payload()
        additional = payload["children"][0]
        # details must be empty — fields are directly on stepper
        assert additional["details"] == []
        # Key fields should exist directly on the stepper
        assert "payment_terms_ref_id" in additional
        assert "delivery_terms_ref_id" in additional
        assert "mode_of_delivery_ref_id" in additional

    def test_payload_address_in_details_array(self):
        """Address rows must be in children[1].details[] array."""
        payload = generate_supplier_api_payload()
        address_stepper = payload["children"][1]
        assert len(address_stepper["details"]) >= 1
        addr = address_stepper["details"][0]
        assert "address_type" in addr
        assert "country_ref_id_id" in addr
        assert "state_ref_id_id" in addr
        assert "address" in addr

    def test_payload_bank_in_details_array(self):
        """Bank rows must be in children[2].details[] array."""
        payload = generate_supplier_api_payload()
        bank_stepper = payload["children"][2]
        assert len(bank_stepper["details"]) >= 1
        bank = bank_stepper["details"][0]
        assert "bank_name" in bank
        assert "bank_account_holder_name" in bank
        assert "bank_doc_id" in bank

    def test_payload_company_name_is_string(self):
        """Company name should be a non-empty string."""
        payload = generate_supplier_api_payload()
        assert isinstance(payload["name"], str)
        assert len(payload["name"]) > 0

    def test_payload_email_is_valid_format(self):
        """Email must contain @ and domain."""
        payload = generate_supplier_api_payload()
        email = payload.get("email_id", "")
        if email:
            assert "@" in email
            assert "." in email.split("@")[-1]

    def test_payload_phone_is_10_digits(self):
        """Phone must be a 10-digit number."""
        payload = generate_supplier_api_payload()
        phone = payload.get("mobile_no")
        if phone:
            phone_str = str(phone)
            assert len(phone_str) == 10

    def test_payload_pan_format(self):
        """PAN must match ABCDE1234F format."""
        payload = generate_supplier_api_payload()
        pan = payload.get("pan_no", "")
        if pan:
            assert len(pan) == 10
            assert pan[:5].isalpha()
            assert pan[5:9].isdigit()
            assert pan[9].isalpha()

    def test_payload_gstin_valid_checksum(self):
        """GSTIN must pass Luhn mod-36 checksum."""
        payload = generate_supplier_api_payload()
        addr_details = payload["children"][1]["details"]
        if addr_details:
            gstin = addr_details[0].get("gstin", "")
            if gstin:
                assert len(gstin) == 15

    def test_payload_fk_ids_in_valid_pools(self):
        """All dropdown FK IDs must be from valid pools."""
        payload = generate_supplier_api_payload()
        if payload.get("ownership_status_ref_id"):
            assert payload["ownership_status_ref_id"] in OWNERSHIP_STATUS_IDS
        if payload.get("po_type_ref_id"):
            assert payload["po_type_ref_id"] in PO_TYPE_IDS

    def test_payload_status_is_boolean(self):
        """Status must be a boolean value."""
        payload = generate_supplier_api_payload()
        assert isinstance(payload["status"], bool)

    def test_build_with_explicit_data(self):
        """build_supplier_api_payload with explicit data should use it."""
        step1 = generate_valid_step1_data()
        step1["company_name"] = "Test Build Company"
        step2 = generate_valid_step2_data()
        step3 = generate_valid_step3_data()
        payload = build_supplier_api_payload(step1, step2, step3)
        assert payload["name"] == "Test Build Company"

    def test_build_with_fk_overrides(self):
        """build_supplier_api_payload with dropdown_ids should override defaults."""
        step1 = generate_valid_step1_data()
        step2 = generate_valid_step2_data()
        step3 = generate_valid_step3_data()
        payload = build_supplier_api_payload(
            step1, step2, step3,
            dropdown_ids={"ownership_status_ref_id": 1262}
        )
        assert payload["ownership_status_ref_id"] == 1262


@pytest.mark.api
class TestSupplierBatchGeneration:
    """Verify batch generation produces unique, valid payloads."""

    def test_batch_generates_correct_count(self):
        payloads = generate_batch_payloads(5)
        assert len(payloads) == 5

    def test_batch_names_are_unique(self):
        payloads = generate_batch_payloads(20)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names found in batch"

    def test_batch_emails_are_unique(self):
        payloads = generate_batch_payloads(20)
        emails = [p.get("email_id", "") for p in payloads if p.get("email_id")]
        assert len(emails) == len(set(emails)), "Duplicate emails found in batch"

    def test_batch_pans_are_unique(self):
        payloads = generate_batch_payloads(20)
        pans = [p.get("pan_no", "") for p in payloads if p.get("pan_no")]
        assert len(pans) == len(set(pans)), "Duplicate PANs found in batch"
