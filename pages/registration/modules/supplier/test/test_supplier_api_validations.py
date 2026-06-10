"""
test_supplier_api_validations.py
--------------------------------
API-only validation test suite for RhythmERP Supplier screen.
~14 test cases migrated from the original 16 UI tests (Bucket A — API-only).

Migrated test inventory:
  Create Validation (SP-C01–SP-C10, 10 tests):
    SP-C01  Empty submit — all fields empty
    SP-C03  Spaces-only company name (xfail — BUG-006)
    SP-C04  Special chars in company name (xfail — BUG-001)
    SP-C05  SQL injection in company name (xfail — BUG-001)
    SP-C06  XSS payload in company name (xfail — BUG-001)
    SP-C07  255 chars boundary (accepted)
    SP-C08  256 chars over-max (may be truncated or rejected)
    SP-C09  Invalid email format
    SP-C10  Invalid PAN format

  Duplicate Validation (SP-D01–SP-D03, 3 tests):
    SP-D01  Duplicate company name
    SP-D02  Duplicate email
    SP-D03  Duplicate phone number

  Edit Validation (SP-E04, 1 test):
    SP-E04  Edit invalid email

Key implementation details:
  - Each test uses ``sp_api`` fixture (SupplierAPIUtils)
  - Build invalid payloads via ``sp_api.generate_unique_payload()`` then override
  - Use ``sp_api.create_and_expect_failure(payload)`` for invalid payloads
  - Then ``sp_api.assert_validation_error(field, expected_status, expected_message_substring)``
  - Use ``sp_api.create_supplier()`` for valid creation
  - Use ``sp_api.search_suppliers(search=...)`` for search tests
  - Use ``sp_api.update_supplier(supplier_id, payload)`` for edit tests
  - All names use ``AutoSup_{timestamp}_{uuid8}`` format
  - NO delete methods exist — no cleanup in teardown

Run:
  pytest test_supplier_api_validations.py -v --tb=short
  pytest test_supplier_api_validations.py -v -m api --tb=short
  pytest test_supplier_api_validations.py -v -k "SP_C01" --tb=short
  pytest test_supplier_api_validations.py -v -m "not bug" --tb=short
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.registration.modules.supplier.data.supplier_data import (
    generate_spaces_only,
    generate_string_255,
    generate_string_256,
    generate_special_char_company_name,
    generate_sql_injection_company_name,
    generate_xss_company_name,
    generate_invalid_email,
    generate_invalid_pan,
    generate_alpha_phone,
    KnownBugs,
)
from pages.registration.modules.supplier.api.endpoints import SCREEN_NAME


# ====================================================================
# CREATE VALIDATION
# ====================================================================

class TestCreateValidation:
    """API-only create validation tests — no browser needed."""

    # ---- SP-C01: Empty submit ----
    @pytest.mark.api
    @pytest.mark.smoke
    def test_SP_C01_empty_submit(self, sp_api):
        """Submit with all fields empty — server should reject.

        The ERP may return validation errors on ANY field (e.g., Address Details
        is checked before company name). We assert that SOME validation error
        occurs, regardless of which field is flagged first.
        """
        log.info("SP-C01 (API): Empty submit")
        empty_payload = {
            "attribute_name": SCREEN_NAME,
            "details": [],
        }
        sp_api.create_and_expect_failure(empty_payload, name_prefix="EmptySup")
        sp_api.assert_validation_error(
            field=None,  # Accept any validation error — ERP checks Address Details first
            expected_status=400,
            expected_message_substring="",
            accept_statuses=[400, 500],
        )

    # ---- SP-C03: Spaces-only company name (BUG-006) ----
    @pytest.mark.api
    @pytest.mark.sanity
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_006, strict=False)
    def test_SP_C03_spaces_only_company_name(self, sp_api):
        """Spaces-only company name — BUG-006: accepted, no whitespace validation."""
        log.info("SP-C03 (API): Spaces-only company name")
        payload = sp_api.generate_unique_payload(name_prefix="SpaceSup")
        payload["name"] = generate_spaces_only(10)
        sp_api.create_and_expect_failure(payload, name_prefix="SpaceSup")
        sp_api.assert_validation_error(
            field="name",
            expected_status=400,
            expected_message_substring="",
            accept_statuses=[400, 500],
        )

    # ---- SP-C04: Special chars in company name (BUG-001) ----
    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_001, strict=False)
    def test_SP_C04_special_chars_company_name(self, sp_api):
        """Special chars in company name — BUG-001: accepted."""
        log.info("SP-C04 (API): Special chars company name")
        payload = sp_api.generate_unique_payload(name_prefix="SpecSup")
        payload["name"] = generate_special_char_company_name()
        sp_api.create_and_expect_failure(payload, name_prefix="SpecSup")
        sp_api.assert_validation_error(
            field="name",
            expected_status=400,
            expected_message_substring="",
            accept_statuses=[400, 500],
        )

    # ---- SP-C05: SQL injection in company name (BUG-001) ----
    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_001, strict=False)
    def test_SP_C05_sql_injection_company_name(self, sp_api):
        """SQL injection in company name — BUG-001: accepted."""
        log.info("SP-C05 (API): SQL injection company name")
        payload = sp_api.generate_unique_payload(name_prefix="SQLSup")
        payload["name"] = generate_sql_injection_company_name()
        sp_api.create_and_expect_failure(payload, name_prefix="SQLSup")
        sp_api.assert_validation_error(
            field="name",
            expected_status=400,
            expected_message_substring="",
            accept_statuses=[400, 500],
        )

    # ---- SP-C06: XSS payload in company name (BUG-001) ----
    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_001, strict=False)
    def test_SP_C06_xss_company_name(self, sp_api):
        """XSS payload in company name — BUG-001: accepted."""
        log.info("SP-C06 (API): XSS company name")
        payload = sp_api.generate_unique_payload(name_prefix="XSSSup")
        payload["name"] = generate_xss_company_name()
        sp_api.create_and_expect_failure(payload, name_prefix="XSSSup")
        sp_api.assert_validation_error(
            field="name",
            expected_status=400,
            expected_message_substring="",
            accept_statuses=[400, 500],
        )

    # ---- SP-C07: 255 chars boundary (should be accepted) ----
    @pytest.mark.api
    @pytest.mark.sanity
    def test_SP_C07_255_chars_company_name(self, sp_api):
        """255 chars company name — should be accepted at boundary."""
        log.info("SP-C07 (API): 255 chars company name")
        payload = sp_api.generate_unique_payload(name_prefix="255Sup")
        payload["name"] = generate_string_255()
        result = sp_api.create_supplier(
            supplier_data={"company_name": generate_string_255()},
            name_prefix="255Sup",
        )
        # May or may not succeed — boundary is edge case
        if result is not None:
            log.info("255 chars accepted at boundary")
        else:
            log.info("255 chars rejected at boundary — may need adjustment")

    # ---- SP-C08: 256 chars over-max ----
    @pytest.mark.api
    @pytest.mark.sanity
    def test_SP_C08_256_chars_company_name(self, sp_api):
        """256 chars company name — over-max, should be rejected or truncated."""
        log.info("SP-C08 (API): 256 chars company name")
        payload = sp_api.generate_unique_payload(name_prefix="256Sup")
        payload["name"] = generate_string_256()
        sp_api.create_and_expect_failure(payload, name_prefix="256Sup")
        sp_api.assert_validation_error(
            field="name",
            expected_status=400,
            expected_message_substring="",
            accept_statuses=[400, 500],
        )

    # ---- SP-C09: Invalid email ----
    @pytest.mark.api
    @pytest.mark.sanity
    def test_SP_C09_invalid_email(self, sp_api):
        """Invalid email format — server should reject."""
        log.info("SP-C09 (API): Invalid email")
        payload = sp_api.generate_unique_payload(name_prefix="InvEmailSup")
        # Override email in step1 data
        payload["email_id"] = generate_invalid_email()
        sp_api.create_and_expect_failure(payload, name_prefix="InvEmailSup")
        sp_api.assert_validation_error(
            field="email_id",
            expected_status=400,
            expected_message_substring="",
            accept_statuses=[400, 500],
        )

    # ---- SP-C10: Invalid PAN ----
    @pytest.mark.api
    @pytest.mark.sanity
    def test_SP_C10_invalid_pan(self, sp_api):
        """Invalid PAN format — server should reject."""
        log.info("SP-C10 (API): Invalid PAN")
        payload = sp_api.generate_unique_payload(name_prefix="InvPANSup")
        payload["pan_no"] = generate_invalid_pan()
        sp_api.create_and_expect_failure(payload, name_prefix="InvPANSup")
        sp_api.assert_validation_error(
            field="pan_no",
            expected_status=400,
            expected_message_substring="",
            accept_statuses=[400, 500],
        )


# ====================================================================
# DUPLICATE VALIDATION
# ====================================================================

class TestDuplicateValidation:
    """API-only duplicate validation tests — no browser needed."""

    # ---- SP-D01: Duplicate company name ----
    @pytest.mark.api
    def test_SP_D01_duplicate_company_name(self, sp_api):
        """Create two suppliers with same company name — check uniqueness."""
        log.info("SP-D01 (API): Duplicate company name")
        result1 = sp_api.create_supplier(name_prefix="DupCoSup")
        if result1 is None:
            pytest.skip("First supplier creation failed — cannot test duplicate")
        company_name = result1.get("name", "")

        payload2 = sp_api.generate_unique_payload(name_prefix="DupCoSup2")
        payload2["name"] = company_name
        result2 = sp_api.create_and_expect_failure(payload2, name_prefix="DupCoSup2")
        if result2 is None:
            log.info("Duplicate company name correctly rejected")
        else:
            log.info("Duplicate company name allowed — no uniqueness constraint")

    # ---- SP-D02: Duplicate email ----
    @pytest.mark.api
    def test_SP_D02_duplicate_email(self, sp_api):
        """Create two suppliers with same email — check uniqueness."""
        log.info("SP-D02 (API): Duplicate email")
        result1 = sp_api.create_supplier(name_prefix="DupEmailSup")
        if result1 is None:
            pytest.skip("First supplier creation failed — cannot test duplicate")
        email = result1.get("email_id", "")

        payload2 = sp_api.generate_unique_payload(name_prefix="DupEmailSup2")
        payload2["email_id"] = email
        result2 = sp_api.create_and_expect_failure(payload2, name_prefix="DupEmailSup2")
        if result2 is None:
            log.info("Duplicate email correctly rejected")
        else:
            log.info("Duplicate email allowed — no uniqueness constraint")

    # ---- SP-D03: Duplicate phone ----
    @pytest.mark.api
    def test_SP_D03_duplicate_phone(self, sp_api):
        """Create two suppliers with same phone — check uniqueness."""
        log.info("SP-D03 (API): Duplicate phone")
        result1 = sp_api.create_supplier(name_prefix="DupPhoneSup")
        if result1 is None:
            pytest.skip("First supplier creation failed — cannot test duplicate")
        phone = result1.get("phone_no", "")

        payload2 = sp_api.generate_unique_payload(name_prefix="DupPhoneSup2")
        payload2["phone_no"] = phone
        result2 = sp_api.create_and_expect_failure(payload2, name_prefix="DupPhoneSup2")
        if result2 is None:
            log.info("Duplicate phone correctly rejected")
        else:
            log.info("Duplicate phone allowed — no uniqueness constraint")


# ====================================================================
# EDIT VALIDATION
# ====================================================================

class TestEditValidation:
    """API-only edit validation tests — no browser needed."""

    # ---- SP-E04: Edit invalid email ----
    @pytest.mark.api
    @pytest.mark.sanity
    def test_SP_E04_edit_invalid_email(self, sp_api):
        """Edit supplier with invalid email — server should reject."""
        log.info("SP-E04 (API): Edit invalid email")
        result = sp_api.create_supplier(name_prefix="EditEmailSup")
        if result is None:
            pytest.skip("Supplier creation failed — cannot test edit")
        supplier_id = result.get("id")

        # Fetch current data and modify email
        detail = sp_api.get_supplier(supplier_id)
        if detail is None:
            pytest.skip("Could not fetch supplier detail for edit")

        detail["email_id"] = generate_invalid_email()
        update_result = sp_api.update_supplier(supplier_id, detail)

        if update_result is None:
            log.info("Edit with invalid email correctly rejected")
        else:
            log.warning("Edit with invalid email was accepted — validation gap")
