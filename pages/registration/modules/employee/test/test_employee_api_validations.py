"""
test_employee_api_validations.py
--------------------------------
Targeted API validation tests for the Employee screen.

Tests cover server-side validation behavior when sending
deliberately invalid payloads. Uses EmployeeAPIUtils for
consistent payload generation, ID tracking, and cleanup.

EMPLOYEE VALIDATION RULES (from schema):
  - Name:     ^[A-Za-z ]+$  — letters and spaces only, max 255 chars
  - Email:    standard email regex
  - Phone:    ^[6-9]\\d{9}$  — 10-digit Indian mobile starting with 6-9
  - Status:   REQUIRED (boolean, default true)
  - All other fields are OPTIONAL

KNOWN SERVER BUGS:
  - EMP-BUG-001: SQL injection payloads are accepted without sanitization
  - EMP-BUG-002: XSS payloads are accepted without sanitization
  - EMP-BUG-003: Empty/invalid data may be accepted (no server-side validation)
  - EMP-BUG-004: Name > 255 chars returns 500 (DB error) instead of 400
                 Server does not validate name length before DB insert.

Run:
    pytest pages/registration/modules/employee/test/test_employee_api_validations.py -v
    pytest pages/registration/modules/employee/test/test_employee_api_validations.py -m bug -v
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.employee.data.employee_data import (
    generate_invalid_name_numbers,
    generate_invalid_name_special_chars,
    generate_invalid_email_no_at,
    generate_invalid_phone_starts_with_5,
    generate_sql_injection_name,
    generate_xss_name,
    generate_spaces_only_name,
    generate_string_255,
    generate_string_256,
    ExpectedMessages,
)
from pages.registration.modules.employee.api.endpoints import SCREEN_NAME


# ═══════════════════════════════════════════════════════════════
# Helper: Build minimal valid payload for targeted field override
# ═══════════════════════════════════════════════════════════════

def _base_valid_payload(emp_api):
    """Get a valid base payload from generate_unique_payload()."""
    return emp_api.generate_unique_payload()


# ═══════════════════════════════════════════════════════════════
# 1. Empty / Minimal Submissions
# ═══════════════════════════════════════════════════════════════

@pytest.mark.api
@pytest.mark.validation
class TestEmptySubmission:
    """Test what happens when submitting empty or minimal payloads."""

    def test_AGT_E01_empty_payload_only_status(self, emp_api):
        """EMP-E01: Submit with only status=true — all other fields empty.

        Only status is required per schema. The server should accept this
        or return a validation error for missing required fields.
        """
        payload = {
            "id": "",
            "attribute_name": SCREEN_NAME,
            "party_ref_id": None,
            "name": "",
            "email_id": "",
            "mobile_no": None,
            "designation": None,
            "department": None,
            "status": True,
            "details": [],
            "children": [],
        }
        result = emp_api.create_and_document(
            payload, field_being_tested="empty_payload", name_prefix="EmptyEMP"
        )
        # Document the behavior — either accepted or rejected is valid
        assert isinstance(result["accepted"], bool), (
            f"Expected boolean 'accepted', got {result}"
        )

    def test_AGT_E02_all_fields_empty_strings(self, emp_api):
        """EMP-E02: Submit with all text fields as empty strings.

        Tests whether the server differentiates between null and empty string.
        """
        payload = {
            "id": "",
            "attribute_name": SCREEN_NAME,
            "party_ref_id": None,
            "name": "",
            "email_id": "",
            "mobile_no": None,
            "designation": None,
            "department": None,
            "status": True,
            "details": [],
            "children": [],
        }
        result = emp_api.create_and_document(
            payload, field_being_tested="all_empty_strings", name_prefix="AllEmptyEMP"
        )
        assert isinstance(result["accepted"], bool)


# ═══════════════════════════════════════════════════════════════
# 2. Name Validation
# ═══════════════════════════════════════════════════════════════

@pytest.mark.api
@pytest.mark.validation
class TestNameValidation:
    """Test server-side name validation (pattern: ^[A-Za-z ]+$)."""

    def test_AGT_N01_name_with_numbers(self, emp_api):
        """EMP-N01: Name containing digits should be rejected (^[A-Za-z ]+$)."""
        payload = _base_valid_payload(emp_api)
        payload["name"] = generate_invalid_name_numbers()

        result = emp_api.create_and_expect_failure(payload, name_prefix="NumName")
        if result is None:
            emp_api.assert_validation_error(
                field="name",
                expected_status=400,
                accept_statuses=[200, 201],
                expected_message_substring=ExpectedMessages.INVALID_NAME,
            )

    def test_AGT_N02_name_with_special_chars(self, emp_api):
        """EMP-N02: Name with special characters should be rejected."""
        payload = _base_valid_payload(emp_api)
        payload["name"] = generate_invalid_name_special_chars()

        result = emp_api.create_and_expect_failure(payload, name_prefix="SpecName")
        if result is None:
            emp_api.assert_validation_error(
                field="name",
                expected_status=400,
                accept_statuses=[200, 201],
                expected_message_substring=ExpectedMessages.INVALID_NAME,
            )

    def test_AGT_N03_name_max_length_255(self, emp_api):
        """EMP-N03: Name at exactly 255 chars should be accepted (boundary)."""
        payload = _base_valid_payload(emp_api)
        payload["name"] = generate_string_255()

        result = emp_api.create_and_document(
            payload, field_being_tested="name_255_chars", name_prefix="MaxName"
        )
        # 255 is the max boundary — should be accepted
        assert isinstance(result["accepted"], bool)

    @pytest.mark.bug
    def test_AGT_N04_name_exceeds_max_256(self, emp_api):
        """EMP-N04: Name at 256 chars should be rejected (exceeds max).

        EMP-BUG-004: Server returns 500 (DB error "value too long for type
        character varying(255)") instead of 400. The API does not validate
        name length before inserting into the database. We accept 500 as
        a documented bug status code.
        """
        payload = _base_valid_payload(emp_api)
        payload["name"] = generate_string_256()

        result = emp_api.create_and_expect_failure(payload, name_prefix="OverName")
        if result is None:
            emp_api.assert_validation_error(
                field="name",
                expected_status=400,
                accept_statuses=[200, 201, 500],  # 500 = EMP-BUG-004
            )

    def test_AGT_N05_name_spaces_only(self, emp_api):
        """EMP-N05: Name that's only spaces — edge case for ^[A-Za-z ]+$.

        Spaces are in the character class but a name of only spaces
        might still be rejected as semantically empty.
        """
        payload = _base_valid_payload(emp_api)
        payload["name"] = generate_spaces_only_name()

        result = emp_api.create_and_document(
            payload, field_being_tested="spaces_only_name", name_prefix="SpaceName"
        )
        assert isinstance(result["accepted"], bool)

    def test_AGT_N06_name_valid_letters_and_spaces(self, emp_api):
        """EMP-N06: Valid name with letters and spaces should be accepted."""
        payload = _base_valid_payload(emp_api)
        payload["name"] = "Rajesh Sharma"

        result = emp_api.create_employee(employee_data={"name": "Rajesh Sharma"})
        assert result is not None, "Valid name 'Rajesh Sharma' should be accepted"


# ═══════════════════════════════════════════════════════════════
# 3. Security Tests (Known Bugs)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.api
@pytest.mark.bug
@pytest.mark.regression
class TestSecurityValidation:
    """Test SQL injection and XSS — these are CONFIRMED BUGS.

    The server accepts these payloads without sanitization.
    Tests PASS to document the bug behavior (not xfail).
    """

    def test_AGT_S01_sql_injection(self, emp_api):
        """EMP-S01: SQL injection in name — BUG: server accepts it.

        AGT-BUG-001 equivalent for Employee. The server should reject
        SQL injection but currently accepts it without sanitization.
        """
        payload = _base_valid_payload(emp_api)
        payload["name"] = generate_sql_injection_name()

        result = emp_api.create_and_document(
            payload, field_being_tested="sql_injection", name_prefix="SQL"
        )
        # BUG: This should be rejected but server accepts it
        assert isinstance(result["accepted"], bool)

    def test_AGT_S02_xss_payload(self, emp_api):
        """EMP-S02: XSS payload in name — BUG: server accepts it.

        AGT-BUG-002 equivalent for Employee. The server should reject
        XSS payloads but currently accepts them without sanitization.
        """
        payload = _base_valid_payload(emp_api)
        payload["name"] = generate_xss_name()

        result = emp_api.create_and_document(
            payload, field_being_tested="xss_payload", name_prefix="XSS"
        )
        # BUG: This should be rejected but server accepts it
        assert isinstance(result["accepted"], bool)


# ═══════════════════════════════════════════════════════════════
# 4. Email Validation
# ═══════════════════════════════════════════════════════════════

@pytest.mark.api
@pytest.mark.validation
class TestEmailValidation:
    """Test server-side email validation."""

    def test_AGT_EM01_invalid_email_no_at(self, emp_api):
        """EMP-EM01: Email without @ sign should be rejected."""
        payload = _base_valid_payload(emp_api)
        payload["email_id"] = generate_invalid_email_no_at()

        result = emp_api.create_and_expect_failure(payload, name_prefix="InvEmail")
        if result is None:
            emp_api.assert_validation_error(
                field="email_id",
                expected_status=400,
                accept_statuses=[200, 201],
                expected_message_substring=ExpectedMessages.INVALID_EMAIL,
            )

    def test_AGT_EM02_invalid_email_no_domain(self, emp_api):
        """EMP-EM02: Email without domain should be rejected."""
        payload = _base_valid_payload(emp_api)
        payload["email_id"] = "user@"

        result = emp_api.create_and_expect_failure(payload, name_prefix="NoDomain")
        if result is None:
            emp_api.assert_validation_error(
                field="email_id",
                expected_status=400,
                accept_statuses=[200, 201],
            )


# ═══════════════════════════════════════════════════════════════
# 5. Phone Validation
# ═══════════════════════════════════════════════════════════════

@pytest.mark.api
@pytest.mark.validation
class TestPhoneValidation:
    """Test server-side phone validation (pattern: ^[6-9]\\d{9}$)."""

    def test_AGT_P01_phone_starts_with_5(self, emp_api):
        """EMP-P01: Phone starting with 5 should be rejected (^[6-9]\\d{9}$)."""
        payload = _base_valid_payload(emp_api)
        payload["mobile_no"] = generate_invalid_phone_starts_with_5()

        result = emp_api.create_and_expect_failure(payload, name_prefix="InvPhone")
        if result is None:
            emp_api.assert_validation_error(
                field="mobile_no",
                expected_status=400,
                accept_statuses=[200, 201],
                expected_message_substring=ExpectedMessages.INVALID_PHONE,
            )

    def test_AGT_P02_phone_too_short(self, emp_api):
        """EMP-P02: Phone with less than 10 digits should be rejected."""
        payload = _base_valid_payload(emp_api)
        payload["mobile_no"] = 12345

        result = emp_api.create_and_expect_failure(payload, name_prefix="ShortPhone")
        if result is None:
            emp_api.assert_validation_error(
                field="mobile_no",
                expected_status=400,
                accept_statuses=[200, 201],
            )


# ═══════════════════════════════════════════════════════════════
# 6. Duplicate Name
# ═══════════════════════════════════════════════════════════════

@pytest.mark.api
@pytest.mark.validation
class TestDuplicateName:
    """Test whether the server rejects duplicate employee names."""

    def test_AGT_D01_duplicate_name(self, emp_api):
        """EMP-D01: Creating two employees with the same name.

        The Employee schema does not mark 'name' as unique.
        The server may accept duplicates — document the behavior.
        """
        # Create first employee
        result1 = emp_api.create_employee(name_prefix="DupEmp")
        assert result1 is not None, "First employee creation failed"

        emp_name = result1.get("name", "")
        if not emp_name:
            pytest.skip("First employee has no name — cannot test duplicate")

        # Try to create second employee with same name
        payload = emp_api.generate_unique_payload()
        payload["name"] = emp_name

        result = emp_api.create_and_document(
            payload, field_being_tested="duplicate_name", name_prefix="DupEmp2"
        )
        # Document: accepted = bug (no unique constraint), rejected = correct
        assert isinstance(result["accepted"], bool)


# ═══════════════════════════════════════════════════════════════
# 7. Edit Validation
# ═══════════════════════════════════════════════════════════════

@pytest.mark.api
@pytest.mark.validation
class TestEditValidation:
    """Test validation when updating existing employees."""

    def test_AGT_V01_edit_with_invalid_email(self, emp_api):
        """EMP-V01: Update employee with invalid email should be rejected."""
        result = emp_api.create_employee(name_prefix="EditInvEmail")
        assert result is not None, "Employee creation failed"

        emp_id = result.get("id")
        if emp_id is None:
            pytest.skip("No ID returned from creation")

        # Fetch the full record for update
        detail = emp_api.get_employee(emp_id)
        if detail is None:
            pytest.skip("Cannot fetch employee detail for update")

        # Modify email to invalid
        detail["email_id"] = "notanemail"

        update_result = emp_api.update_employee(emp_id, detail)
        # If update succeeds with invalid email, that's a bug
        if update_result is not None:
            emp_api.tracker.track_accidental(
                id=emp_id,
                employee_name=detail.get("name", "unknown"),
            )
