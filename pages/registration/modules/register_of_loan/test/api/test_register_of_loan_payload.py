"""
test_register_of_loan_payload.py — Verify Register of Loan payload structure.
"""

import sys
import os
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.register_of_loan.data.register_of_loan_data import (
    build_api_payload,
    generate_api_payload,
    generate_batch_payloads,
    FACILITY_DETAILS_IDS,
    EMI_PERIOD_IDS,
)


class TestRegisterOfLoanPayloadStructure:
    """Verify the generated payload matches expected structure."""

    def test_payload_has_required_keys(self):
        payload = generate_api_payload()
        assert "id" in payload
        assert "attribute_name" in payload
        assert "sanction_date" in payload
        assert "bank_name" in payload
        assert "sanction_amount" in payload
        assert "facility_details_ref_id" in payload
        assert "disbursement_amount" in payload
        assert "emi_servicing_date" in payload
        assert "instalment_amount" in payload
        assert "reminder_period_in_days" in payload
        assert "emi_period" in payload
        assert "outstanding_amount" in payload
        assert "details" in payload
        assert "children" in payload

    def test_attribute_name_is_correct(self):
        payload = generate_api_payload()
        assert payload["attribute_name"] == "Register of Loan"

    def test_id_is_empty_string(self):
        payload = generate_api_payload()
        assert payload["id"] == ""

    def test_details_and_children_are_empty_lists(self):
        payload = generate_api_payload()
        assert payload["details"] == []
        assert payload["children"] == []

    def test_bank_name_letters_and_spaces_only(self):
        for _ in range(20):
            payload = generate_api_payload()
            name = payload["bank_name"]
            assert re.match(r'^[A-Za-z ]+$', name), f"Bank name '{name}' has invalid chars"

    def test_sanction_amount_positive(self):
        for _ in range(20):
            payload = generate_api_payload()
            assert payload["sanction_amount"] > 0

    def test_disbursement_amount_positive(self):
        for _ in range(20):
            payload = generate_api_payload()
            assert payload["disbursement_amount"] > 0

    def test_facility_details_ref_id_is_valid(self):
        for _ in range(20):
            payload = generate_api_payload()
            assert payload["facility_details_ref_id"] in FACILITY_DETAILS_IDS

    def test_emi_period_is_valid(self):
        for _ in range(20):
            payload = generate_api_payload()
            assert payload["emi_period"] in EMI_PERIOD_IDS

    def test_reminder_period_positive_integer(self):
        for _ in range(20):
            payload = generate_api_payload()
            rp = payload["reminder_period_in_days"]
            assert isinstance(rp, int) and rp > 0

    def test_instalment_amount_positive(self):
        for _ in range(20):
            payload = generate_api_payload()
            assert payload["instalment_amount"] > 0

    def test_outstanding_amount_positive(self):
        for _ in range(20):
            payload = generate_api_payload()
            assert payload["outstanding_amount"] > 0

    def test_is_notification_applicable_is_boolean(self):
        for _ in range(20):
            payload = generate_api_payload()
            assert isinstance(payload["is_notification_applicable"], bool)


class TestRegisterOfLoanBuildPayload:
    """Verify build_api_payload with explicit data and overrides."""

    def test_build_with_explicit_data(self):
        data = {
            "bank_name": "Test Bank",
            "sanction_amount": 1000000,
            "disbursement_amount": 900000,
            "instalment_amount": 15000,
            "reminder_period_in_days": 30,
            "outstanding_amount": 500000,
        }
        payload = build_api_payload(data=data)
        assert payload["bank_name"] == "Test Bank"
        assert payload["sanction_amount"] == 1000000

    def test_fk_overrides(self):
        payload = build_api_payload(fk_overrides={"facility_details_ref_id": 651, "emi_period": 1530})
        assert payload["facility_details_ref_id"] == 651
        assert payload["emi_period"] == 1530

    def test_kwargs_override(self):
        payload = generate_api_payload(bank_name="Custom Bank Name")
        assert payload["bank_name"] == "Custom Bank Name"

    def test_batch_with_override(self):
        payloads = generate_batch_payloads(5, facility_details_ref_id=1547)
        for p in payloads:
            assert p["facility_details_ref_id"] == 1547
