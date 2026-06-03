"""
test_customer_payload.py — Fast API payload structure tests.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.customer.data.customer_data import (
    generate_customer_api_payload,
    build_customer_api_payload,
    generate_valid_customer_data,
    generate_valid_address_row,
    generate_valid_bank_row,
    generate_batch_payloads,
    generate_company_name,
    generate_email,
    generate_phone_number,
    generate_pan_number,
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
    FIELD_VALIDATION_RULES,
)


@pytest.mark.api
class TestCustomerAPIPayload:
    """Verify that generated API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, children (no root details — that's on steppers)."""
        payload = generate_customer_api_payload()
        assert "id" in payload
        assert payload["id"] == ""
        assert payload["attribute_name"] == "Customer"
        # Root payload does NOT have "details" — details[] lives inside each child stepper
        assert "details" not in payload
        assert "children" in payload

    def test_payload_has_3_children_steppers(self):
        """Payload must have 3 children: Additional Details, Customer Details, Bank."""
        payload = generate_customer_api_payload()
        children = payload["children"]
        assert len(children) == 3
        assert children[0]["stepper_name"] == "Additional Details"
        assert children[1]["stepper_name"] == "Customer Details"
        assert children[2]["stepper_name"] == "Customer Bank Details"

    def test_payload_additional_details_on_stepper(self):
        """Additional Details fields must be ON the stepper object, NOT in details[]."""
        payload = generate_customer_api_payload()
        additional = payload["children"][0]
        # details must be empty — fields are directly on stepper
        assert additional["details"] == []
        # Key FK fields should exist directly on the stepper
        assert "payment_terms_ref_id" in additional
        assert "delivery_terms_ref_id" in additional
        assert "mode_of_delivery_ref_id" in additional
        # Customer-specific FK fields
        assert "preferred_payment_method_ref_id" in additional
        assert "gst_registration_type" in additional
        assert "courier_terms_ref_id" in additional

    def test_payload_customer_specific_root_fields(self):
        """Customer root has supply_type_ref_id and sale_type_ref_id (not po_type)."""
        payload = generate_customer_api_payload()
        assert "supply_type_ref_id" in payload
        assert "sale_type_ref_id" in payload
        # Should NOT have po_type_ref_id (that's Supplier-only)
        assert "po_type_ref_id" not in payload

    def test_payload_address_in_details_array(self):
        """Address rows must be in children[1].details[] array."""
        payload = generate_customer_api_payload()
        address_stepper = payload["children"][1]
        assert len(address_stepper["details"]) >= 1
        addr = address_stepper["details"][0]
        assert "address_type" in addr
        assert "country_ref_id_id" in addr
        assert "state_ref_id_id" in addr
        assert "address" in addr

    def test_payload_bank_in_details_array(self):
        """Bank rows must be in children[2].details[] array."""
        payload = generate_customer_api_payload()
        bank_stepper = payload["children"][2]
        assert len(bank_stepper["details"]) >= 1
        bank = bank_stepper["details"][0]
        assert "bank_name" in bank
        assert "bank_account_holder_name" in bank
        assert "bank_doc_id" in bank

    def test_payload_company_name_is_string(self):
        """Company name should be a non-empty string."""
        payload = generate_customer_api_payload()
        assert isinstance(payload["name"], str)
        assert len(payload["name"]) > 0

    def test_payload_email_is_valid_format(self):
        """Email must contain @ and domain."""
        payload = generate_customer_api_payload()
        email = payload.get("email_id", "")
        if email:
            assert "@" in email
            assert "." in email.split("@")[-1]

    def test_payload_phone_is_10_digits(self):
        """Phone must be a 10-digit number."""
        payload = generate_customer_api_payload()
        phone = payload.get("mobile_no")
        if phone:
            phone_str = str(phone)
            assert len(phone_str) == 10

    def test_payload_pan_format(self):
        """PAN must match ABCDE1234F format."""
        payload = generate_customer_api_payload()
        pan = payload.get("pan_no", "")
        if pan:
            assert len(pan) == 10
            assert pan[:5].isalpha()
            assert pan[5:9].isdigit()
            assert pan[9].isalpha()

    def test_payload_gstin_valid_length(self):
        """GSTIN must be 15 characters."""
        payload = generate_customer_api_payload()
        addr_details = payload["children"][1]["details"]
        if addr_details:
            gstin = addr_details[0].get("gstin", "")
            if gstin:
                assert len(gstin) == 15

    def test_payload_fk_ids_in_valid_pools(self):
        """All dropdown FK IDs must be from valid pools."""
        payload = generate_customer_api_payload()
        # Root-level FKs
        if payload.get("ownership_status_ref_id"):
            assert payload["ownership_status_ref_id"] in OWNERSHIP_STATUS_IDS
        if payload.get("supply_type_ref_id"):
            assert payload["supply_type_ref_id"] in SUPPLY_TYPE_IDS
        if payload.get("sale_type_ref_id"):
            assert payload["sale_type_ref_id"] in SALE_TYPE_IDS
        # Additional Details FKs
        additional = payload["children"][0]
        if additional.get("preferred_payment_method_ref_id"):
            assert additional["preferred_payment_method_ref_id"] in PREFERRED_PAYMENT_METHOD_IDS
        if additional.get("gst_registration_type"):
            assert additional["gst_registration_type"] in GST_REGISTRATION_TYPE_IDS
        if additional.get("courier_terms_ref_id"):
            assert additional["courier_terms_ref_id"] in COURIER_TERMS_IDS

    def test_payload_status_is_boolean(self):
        """Status must be a boolean value."""
        payload = generate_customer_api_payload()
        assert isinstance(payload["status"], bool)

    def test_payload_deposit_is_numeric(self):
        """Deposit in Additional Details must be numeric."""
        payload = generate_customer_api_payload()
        additional = payload["children"][0]
        deposit = additional.get("deposit")
        assert deposit is not None
        assert isinstance(deposit, (int, float))

    def test_build_with_explicit_data(self):
        """build_customer_api_payload with explicit data should use it."""
        customer_data = generate_valid_customer_data()
        customer_data["company_name"] = "Test Build Customer Co"
        payload = build_customer_api_payload(customer_data)
        assert payload["name"] == "Test Build Customer Co"

    def test_build_with_fk_overrides(self):
        """build_customer_api_payload with dropdown_ids should override defaults."""
        customer_data = generate_valid_customer_data()
        payload = build_customer_api_payload(
            customer_data,
            dropdown_ids={"ownership_status_ref_id": 1262}
        )
        assert payload["ownership_status_ref_id"] == 1262


@pytest.mark.api
class TestCustomerBatchGeneration:
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
