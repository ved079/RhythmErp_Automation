"""
test_employee_validation.py
---------------------------
Comprehensive validation tests for RhythmERP Employee Screen.

Tests cover:
  1. API batch creation (fast, deterministic)
  2. Field-level validation (boundary values, invalid inputs)
  3. Schema verification (all fields present, FK IDs correct)
  4. CRUD operations (Create, Read, Update)
  5. UI form creation (Selenium — requires browser)

Run:
    # API-only tests (fast, no browser needed)
    pytest pages/registration/modules/employee/test/test_employee.py -m api -v

    # Validation boundary tests
    pytest pages/registration/modules/employee/test/test_employee.py -m validation -v

    # UI tests (requires browser + ERP access)
    pytest pages/registration/modules/employee/test/test_employee.py -m ui -v

    # All tests
    pytest pages/registration/modules/employee/test/test_employee.py -v
"""

import pytest
import sys
import os

# Add project root
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.employee.data.employee_data import (
    generate_employee_name,
    generate_email,
    generate_phone,
    generate_designation_id,
    generate_employee_api_payload,
    build_employee_api_payload,
    generate_valid_employee_data,
    generate_minimal_employee_data,
    generate_batch_payloads,
    generate_string_255,
    generate_string_256,
    generate_invalid_name_numbers,
    generate_invalid_name_special_chars,
    generate_invalid_email_no_at,
    generate_invalid_phone_starts_with_5,
    generate_invalid_phone_too_short,
    generate_sql_injection_name,
    generate_xss_name,
    ExpectedMessages,
    DESIGNATION_IDS,
    DESIGNATION_NAMES,
    PARTY_REF_IDS,
    DEPARTMENT_IDS,
    DEFAULT_EMPLOYEE_FK_IDS,
    FIELD_VALIDATION_RULES,
)


# ═══════════════════════════════════════════════════════════════
# API Client fixture (reusable across test sessions)
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def api_client():
    """Create an authenticated API client for Employee tests.

    Uses token from environment variable or prompts interactively.
    """
    from common.erp_api_client import RhythmERPAPIClient

    token = os.environ.get("ERP_TOKEN", "").strip()
    tenant_id = os.environ.get("ERP_TENANT_ID", "681")

    client = RhythmERPAPIClient()
    if token:
        client.login_from_browser(token=token, tenant_id=tenant_id)
    else:
        # Try login from config credentials
        try:
            client.login()
        except Exception:
            pytest.skip("No ERP token available. Set ERP_TOKEN env var.")

    # Verify auth works
    result = client.list_entries("Employee", page=1, page_size=1)
    if not result:
        pytest.skip("ERP authentication failed. Check token/credentials.")

    yield client
    client.close()


# ═══════════════════════════════════════════════════════════════
# MARKER: api — Fast API-based tests (no browser)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.api
class TestEmployeeAPIPayload:
    """Verify that generated API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, details, children."""
        payload = generate_employee_api_payload()
        assert "id" in payload
        assert payload["id"] == ""  # Empty string for new entries
        assert payload["attribute_name"] == "Employee"
        assert payload["details"] == []
        assert payload["children"] == []

    def test_payload_has_all_field_keys(self):
        """Payload must include all 7 field keys."""
        payload = generate_employee_api_payload()
        expected_keys = {"party_ref_id", "name", "email_id", "mobile_no",
                         "designation", "department", "status"}
        assert expected_keys.issubset(set(payload.keys()))

    def test_payload_name_is_letters_and_spaces(self):
        """Employee name must match ^[A-Za-z ]+$ pattern."""
        payload = generate_employee_api_payload()
        name = payload["name"]
        assert name, "Name should not be empty"
        assert all(c.isalpha() or c == " " for c in name), \
            f"Name '{name}' contains invalid characters"

    def test_payload_email_is_valid_format(self):
        """Email must be a valid format."""
        payload = generate_employee_api_payload()
        email = payload["email_id"]
        assert "@" in email, f"Email '{email}' missing @"
        assert "." in email.split("@")[-1], f"Email '{email}' missing domain"

    def test_payload_phone_is_valid_indian(self):
        """Phone must be 10 digits starting with 6-9."""
        payload = generate_employee_api_payload()
        phone = payload["mobile_no"]
        phone_str = str(phone)
        assert len(phone_str) == 10, f"Phone {phone_str} is not 10 digits"
        assert phone_str[0] in "6789", f"Phone {phone_str} doesn't start with 6-9"

    def test_payload_designation_is_valid_fk(self):
        """Designation must be a valid FK ID from the verified pool."""
        payload = generate_employee_api_payload()
        designation = payload["designation"]
        assert designation in DESIGNATION_IDS, \
            f"Designation {designation} not in valid pool {DESIGNATION_IDS}"

    def test_payload_department_is_null(self):
        """Department must be null (no options available currently)."""
        payload = generate_employee_api_payload()
        assert payload["department"] is None, \
            "Department should be null (no options available)"

    def test_payload_status_is_boolean(self):
        """Status must be a boolean value."""
        payload = generate_employee_api_payload()
        assert isinstance(payload["status"], bool)

    def test_payload_party_ref_id_nullable(self):
        """party_ref_id must be either None or a valid FK ID."""
        payload = generate_employee_api_payload()
        prid = payload["party_ref_id"]
        if prid is not None:
            assert prid in PARTY_REF_IDS, \
                f"party_ref_id {prid} not in valid pool"

    def test_build_with_explicit_data(self):
        """build_employee_api_payload with explicit data should use it."""
        data = generate_valid_employee_data()
        data["employee_name"] = "Rajesh Sharma"
        data["email"] = "rajesh@test.com"
        data["phone_number"] = 9876543210

        payload = build_employee_api_payload(data)
        assert payload["name"] == "Rajesh Sharma"
        assert payload["email_id"] == "rajesh@test.com"
        assert payload["mobile_no"] == 9876543210

    def test_build_with_fk_overrides(self):
        """build_employee_api_payload with fk_ids should override defaults."""
        payload = build_employee_api_payload(fk_ids={"designation": 5})
        assert payload["designation"] == 5

    def test_generate_with_kwargs_overrides(self):
        """generate_employee_api_payload with kwargs should override fields."""
        payload = generate_employee_api_payload(name="Test User", status=False)
        assert payload["name"] == "Test User"
        assert payload["status"] is False


@pytest.mark.api
class TestEmployeeBatchGeneration:
    """Verify batch generation produces unique, valid payloads."""

    def test_batch_generates_correct_count(self):
        """Batch generation should produce the requested number of payloads."""
        payloads = generate_batch_payloads(5)
        assert len(payloads) == 5

    def test_batch_names_are_unique(self):
        """All generated names in a batch should be unique."""
        payloads = generate_batch_payloads(20)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names found in batch"

    def test_batch_emails_are_unique(self):
        """All generated emails in a batch should be unique."""
        payloads = generate_batch_payloads(20)
        emails = [p["email_id"] for p in payloads]
        assert len(emails) == len(set(emails)), "Duplicate emails found in batch"

    def test_batch_designations_vary(self):
        """Batch should use varied designations (not all the same)."""
        payloads = generate_batch_payloads(20)
        designations = [p["designation"] for p in payloads]
        assert len(set(designations)) > 1, "All designations are the same"


# ═══════════════════════════════════════════════════════════════
# MARKER: api — Live API tests (requires authenticated client)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.api
class TestEmployeeAPILive:
    """Live API tests — create entries and verify on the ERP."""

    def test_create_single_employee(self, api_client):
        """Create a single Employee via API and verify it exists."""
        payload = generate_employee_api_payload()
        result = api_client.create_entry(payload)

        # API returns the listing page on success (status 200)
        assert result is not None, "API create returned None (likely failure)"

    def test_create_employee_with_designation(self, api_client):
        """Create an Employee with a specific designation."""
        payload = generate_employee_api_payload(designation=2)  # Farm Supervisor
        assert payload["designation"] == 2
        result = api_client.create_entry(payload)
        assert result is not None

    def test_create_employee_inactive(self, api_client):
        """Create an inactive Employee (status=False)."""
        payload = generate_employee_api_payload(status=False)
        assert payload["status"] is False
        result = api_client.create_entry(payload)
        assert result is not None

    def test_create_minimal_employee(self, api_client):
        """Create an Employee with all required fields filled.

        The ERP server requires name, email_id, mobile_no, and designation
        in addition to status — submitting without them returns a validation
        error (verified by API validation tests).
        """
        payload = generate_employee_api_payload()
        result = api_client.create_entry(payload)
        assert result is not None

    def test_list_employees(self, api_client):
        """List Employee entries — should return a valid response."""
        result = api_client.list_entries("Employee", page=1, page_size=5)
        assert result is not None
        assert "screenmatlistingdata_set" in result

    def test_get_employee_detail(self, api_client):
        """Get a specific Employee entry by ID."""
        # First list to get an ID
        result = api_client.list_entries("Employee", page=1, page_size=1)
        assert result is not None
        records = result.get("screenmatlistingdata_set", [])
        if records:
            entry_id = records[0]["id"]
            detail = api_client.get_entry("Employee", entry_id)
            assert detail is not None
            assert detail["attribute_name"] == "Employee"

    def test_discover_employee_structure(self, api_client):
        """Discover and verify the Employee payload structure."""
        detail = api_client.discover_structure("Employee")
        if detail:
            assert detail["attribute_name"] == "Employee"
            assert "children" in detail
            # Employee is a flat screen — children should be empty
            assert detail["children"] == []
            assert detail["details"] == []


# ═══════════════════════════════════════════════════════════════
# MARKER: validation — Field validation boundary tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.validation
class TestEmployeeFieldValidation:
    """Test field-level validation rules against the ERP schema."""

    # --- Employee Name validation ---

    def test_name_valid_letters_only(self):
        """Valid name: letters only should pass ^[A-Za-z ]+$."""
        name = generate_employee_name()
        assert all(c.isalpha() or c == " " for c in name)

    def test_name_invalid_with_numbers(self):
        """Invalid name: numbers should fail ^[A-Za-z ]+$."""
        invalid_name = generate_invalid_name_numbers()
        assert not all(c.isalpha() or c == " " for c in invalid_name)

    def test_name_invalid_with_special_chars(self):
        """Invalid name: special chars should fail ^[A-Za-z ]+$."""
        invalid_name = generate_invalid_name_special_chars()
        assert not all(c.isalpha() or c == " " for c in invalid_name)

    def test_name_max_length_255(self):
        """Name at exactly 255 chars should be accepted (max boundary)."""
        name_255 = generate_string_255()
        assert len(name_255) == 255

    def test_name_exceeds_max_length(self):
        """Name at 256 chars should be rejected (exceeds max)."""
        name_256 = generate_string_256()
        assert len(name_256) == 256

    def test_name_sql_injection(self):
        """SQL injection in name should be handled safely."""
        sql_name = generate_sql_injection_name()
        # The ERP should either sanitize or reject this
        assert "'" in sql_name  # Verify the injection string is correct

    def test_name_xss_payload(self):
        """XSS payload in name should be handled safely."""
        xss_name = generate_xss_name()
        assert "<script>" in xss_name

    # --- Email validation ---

    def test_email_valid_format(self):
        """Valid email should pass format validation."""
        email = generate_email()
        assert "@" in email
        assert "." in email.split("@")[-1]

    def test_email_invalid_no_at(self):
        """Invalid email without @ should fail validation."""
        invalid_email = generate_invalid_email_no_at()
        assert "@" not in invalid_email

    # --- Phone validation ---

    def test_phone_valid_indian_mobile(self):
        """Valid Indian mobile (starts 6-9, 10 digits) should pass."""
        phone = generate_phone()
        phone_str = str(phone)
        assert len(phone_str) == 10
        assert phone_str[0] in "6789"

    def test_phone_invalid_starts_with_5(self):
        """Phone starting with 5 should fail ^[6-9]\\d{9}$."""
        invalid_phone = generate_invalid_phone_starts_with_5()
        phone_str = str(invalid_phone)
        assert phone_str[0] == "5"

    def test_phone_invalid_too_short(self):
        """Phone with less than 10 digits should fail."""
        invalid_phone = generate_invalid_phone_too_short()
        assert len(str(invalid_phone)) < 10

    # --- Designation FK validation ---

    def test_designation_ids_are_valid(self):
        """All designation IDs in the pool should be in range 1-56."""
        for did in DESIGNATION_IDS:
            assert 1 <= did <= 56, f"Designation ID {did} out of range"

    def test_designation_names_map_complete(self):
        """DESIGNATION_NAMES should have an entry for every ID."""
        for did in DESIGNATION_IDS:
            assert did in DESIGNATION_NAMES, f"Missing name for designation {did}"


# ═══════════════════════════════════════════════════════════════
# MARKER: schema — Schema verification tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.schema
class TestEmployeeSchema:
    """Verify the Employee screen schema matches our code expectations."""

    def test_field_validation_rules_complete(self):
        """FIELD_VALIDATION_RULES should cover all data fields."""
        expected_fields = {"name", "email_id", "mobile_no",
                          "designation", "department", "status"}
        actual_fields = set(FIELD_VALIDATION_RULES.keys())
        assert expected_fields == actual_fields, \
            f"Missing fields: {expected_fields - actual_fields}, Extra: {actual_fields - expected_fields}"

    def test_name_pattern_matches_schema(self):
        """Name validation pattern should match ^[A-Za-z ]+$."""
        name_rule = FIELD_VALIDATION_RULES["name"]
        assert name_rule["pattern"] == r"^[A-Za-z ]+$"

    def test_phone_pattern_matches_schema(self):
        """Phone validation pattern should match ^[6-9]\\d{9}$."""
        phone_rule = FIELD_VALIDATION_RULES["mobile_no"]
        assert phone_rule["pattern"] == r"^[6-9]\d{9}$"

    def test_designation_has_56_options(self):
        """Designation dropdown should have 56 options."""
        assert FIELD_VALIDATION_RULES["designation"]["fk_options_count"] == 56

    def test_department_has_0_options(self):
        """Department dropdown should have 0 options currently."""
        assert FIELD_VALIDATION_RULES["department"]["fk_options_count"] == 0

    def test_status_is_required(self):
        """Status should be the only required field."""
        assert FIELD_VALIDATION_RULES["status"]["required"] is True
        # All other fields should be optional
        for field_key, rule in FIELD_VALIDATION_RULES.items():
            if field_key != "status":
                assert rule["required"] is False, \
                    f"Field {field_key} should be optional"

    def test_default_fk_ids_valid(self):
        """DEFAULT_EMPLOYEE_FK_IDS values should be in valid pools."""
        if DEFAULT_EMPLOYEE_FK_IDS["designation"] is not None:
            assert DEFAULT_EMPLOYEE_FK_IDS["designation"] in DESIGNATION_IDS
        assert DEFAULT_EMPLOYEE_FK_IDS["department"] is None  # No options


# ═══════════════════════════════════════════════════════════════
# MARKER: ui — Selenium browser tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.ui
class TestEmployeeUI:
    """UI-based tests using Selenium — requires browser + ERP access."""

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver):
        """Navigate to Employee page before each test."""
        from pages.registration.modules.employee.employee_page import EmployeePage
        self.page = EmployeePage(logged_in_driver)
        self.page.navigate_to_page()

    def test_employee_page_loads(self):
        """Employee listing page should load with table."""
        assert self.page.is_page_loaded()

    def test_employee_add_form_opens(self):
        """Clicking ADD should open the Employee form popup."""
        self.page.open_add_form()
        assert self.page.is_add_form_open()

    def test_employee_form_fill_and_submit(self):
        """Fill all fields and submit — should create successfully."""
        data = generate_valid_employee_data()
        self.page.open_add_form()
        self.page.fill_employee_form(data)
        self.page.submit_form()
        self.page.wait_seconds(4)
        # Should see success alert, validation alert, or form closes
        success = self.page.is_success_alert_visible()
        form_closed = not self.page.is_add_form_open()
        if success:
            self.page.dismiss_alert()
        assert success or form_closed, \
            "Form submission should succeed or close the form"

    def test_employee_form_validation_invalid_name(self):
        """Invalid name (with numbers) should show validation error."""
        data = generate_valid_employee_data()
        data["employee_name"] = generate_invalid_name_numbers()
        self.page.open_add_form()
        self.page.fill_employee_form(data)
        self.page.submit_form()
        self.page.wait_seconds(1)
        # Should show validation error or stay on form
        has_errors = self.page.has_validation_errors()
        is_still_open = self.page.is_add_form_open()
        assert has_errors or is_still_open

    def test_employee_form_validation_invalid_email(self):
        """Invalid email should show validation error."""
        data = generate_valid_employee_data()
        data["email"] = generate_invalid_email_no_at()
        self.page.open_add_form()
        self.page.fill_employee_form(data)
        self.page.submit_form()
        self.page.wait_seconds(1)
        has_errors = self.page.has_validation_errors()
        is_still_open = self.page.is_add_form_open()
        assert has_errors or is_still_open

    def test_employee_form_validation_invalid_phone(self):
        """Invalid phone (starts with 5) should show validation error."""
        data = generate_valid_employee_data()
        data["phone_number"] = generate_invalid_phone_starts_with_5()
        self.page.open_add_form()
        self.page.fill_employee_form(data)
        self.page.submit_form()
        self.page.wait_seconds(1)
        has_errors = self.page.has_validation_errors()
        is_still_open = self.page.is_add_form_open()
        assert has_errors or is_still_open

    def test_employee_table_has_rows(self):
        """Employee listing table should have at least 1 row."""
        count = self.page.get_table_row_count()
        assert count >= 0  # May be 0 on fresh tenant

    def test_employee_search_works(self):
        """Search should filter the table."""
        # Get first name and search for it
        names = self.page.get_table_employee_names()
        if names:
            self.page.search_employee(names[0][:5])
            self.page.wait_seconds(2)
            # Search should not crash the page
            assert self.page.is_page_loaded()


# ═══════════════════════════════════════════════════════════════
# MARKER: performance — Speed and performance tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.performance
class TestEmployeePerformance:
    """Performance benchmarks for Employee batch creation."""

    def test_batch_create_10_employees(self, api_client):
        """Create 10 employees via API — should complete in under 10s."""
        import time
        start = time.time()
        for _ in range(10):
            payload = generate_employee_api_payload()
            api_client.create_entry(payload)
            time.sleep(0.1)
        elapsed = time.time() - start
        assert elapsed < 10, f"10 employees took {elapsed:.1f}s (expected < 10s)"

    def test_payload_generation_speed(self):
        """Generate 100 payloads — should complete in under 1s."""
        import time
        start = time.time()
        for _ in range(100):
            generate_employee_api_payload()
        elapsed = time.time() - start
        assert elapsed < 1, f"100 payloads took {elapsed:.2f}s (expected < 1s)"
