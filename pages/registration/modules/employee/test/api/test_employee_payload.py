"""
test_employee_payload.py — Fast API payload structure tests.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import re
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.employee.data.employee_data import (
    generate_employee_api_payload,
    build_employee_api_payload,
    generate_valid_employee_data,
    generate_batch_payloads,
    DESIGNATION_IDS,
    DESIGNATION_NAMES,
    PARTY_REF_IDS,
)


@pytest.mark.api
class TestEmployeeAPIPayload:
    """Verify that generated API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, details, children."""
        payload = generate_employee_api_payload()
        assert "id" in payload
        assert payload["id"] == ""
        assert payload["attribute_name"] == "Employee"
        assert "details" in payload
        assert "children" in payload

    def test_payload_has_all_field_keys(self):
        """Payload must include all Employee field keys."""
        payload = generate_employee_api_payload()
        expected_keys = {
            "party_ref_id", "name", "email_id", "mobile_no",
            "designation", "department", "status",
        }
        for key in expected_keys:
            assert key in payload, f"Missing field key: {key}"

    def test_payload_is_flat_no_steppers(self):
        """Employee is a FLAT form — children and details must be empty arrays."""
        payload = generate_employee_api_payload()
        assert payload["children"] == []
        assert payload["details"] == []

    def test_payload_name_is_letters_and_spaces(self):
        """Employee name must match ^[A-Za-z ]+$ pattern."""
        payload = generate_employee_api_payload()
        name = payload["name"]
        assert re.match(r"^[A-Za-z ]+$", name), f"Name '{name}' doesn't match ^[A-Za-z ]+$"

    def test_payload_email_is_valid_format(self):
        """Email must contain @ and domain."""
        payload = generate_employee_api_payload()
        email = payload.get("email_id", "")
        if email:
            assert "@" in email
            assert "." in email.split("@")[-1]

    def test_payload_phone_is_valid_indian(self):
        """Phone must be a 10-digit Indian mobile starting with 6-9."""
        payload = generate_employee_api_payload()
        phone = payload.get("mobile_no")
        if phone is not None:
            phone_str = str(phone)
            assert len(phone_str) == 10, f"Phone {phone_str} is not 10 digits"
            assert phone_str[0] in "6789", f"Phone {phone_str} doesn't start with 6-9"

    def test_payload_designation_is_valid_fk(self):
        """Designation must be a valid FK ID from the verified pool."""
        payload = generate_employee_api_payload()
        designation = payload.get("designation")
        if designation is not None:
            assert designation in DESIGNATION_IDS, f"Designation {designation} not in valid pool"

    def test_payload_department_is_null(self):
        """Department should be null (0 options currently)."""
        payload = generate_employee_api_payload()
        assert payload["department"] is None

    def test_payload_status_is_boolean(self):
        """Status must be a boolean value."""
        payload = generate_employee_api_payload()
        assert isinstance(payload["status"], bool)

    def test_payload_party_ref_id_nullable(self):
        """party_ref_id can be null (it's optional)."""
        payload = generate_employee_api_payload()
        # Just verify it's either None or a valid ID
        party_ref = payload.get("party_ref_id")
        if party_ref is not None:
            assert isinstance(party_ref, int)

    def test_build_with_explicit_data(self):
        """build_employee_api_payload with explicit data should use it."""
        employee_data = generate_valid_employee_data()
        employee_data["employee_name"] = "Test Build Employee"
        payload = build_employee_api_payload(employee_data)
        assert payload["name"] == "Test Build Employee"

    def test_build_with_fk_overrides(self):
        """build_employee_api_payload with fk_ids should override defaults."""
        employee_data = generate_valid_employee_data()
        payload = build_employee_api_payload(
            employee_data,
            fk_ids={"designation": 5}
        )
        assert payload["designation"] == 5

    def test_generate_with_kwargs_overrides(self):
        """generate_employee_api_payload with kwargs should override fields."""
        payload = generate_employee_api_payload(name="Custom Name", designation=10)
        assert payload["name"] == "Custom Name"
        assert payload["designation"] == 10


@pytest.mark.api
class TestEmployeeBatchGeneration:
    """Verify batch generation produces unique, valid payloads."""

    def test_batch_generates_correct_count(self):
        """Batch generation should return the requested count."""
        payloads = generate_batch_payloads(5)
        assert len(payloads) == 5

    def test_batch_names_are_unique(self):
        """All names in a batch should be unique."""
        payloads = generate_batch_payloads(20)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names found in batch"

    def test_batch_emails_are_unique(self):
        """All emails in a batch should be unique."""
        payloads = generate_batch_payloads(20)
        emails = [p.get("email_id", "") for p in payloads if p.get("email_id")]
        assert len(emails) == len(set(emails)), "Duplicate emails found in batch"

    def test_batch_designations_vary(self):
        """Designations should vary across the batch (statistical check)."""
        payloads = generate_batch_payloads(20)
        designations = [p.get("designation") for p in payloads if p.get("designation") is not None]
        unique_count = len(set(designations))
        # With 56 options and 20 entries, we expect at least 5 unique values
        assert unique_count >= 5, f"Only {unique_count} unique designations in 20 payloads"
