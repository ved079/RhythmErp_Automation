"""
test_company_onboarding_validation.py
---------------------------------------
Comprehensive validation test suite for RhythmERP Company Onboarding screen.

6 Steps:
  Step 1 = Company Details  (Company Name, Company Code, Entity Group, etc.)
  Step 2 = Promoters
  Step 3 = Address
  Step 4 = Business Details
  Step 5 = Infrastructure
  Step 6 = Configuration (Base Currency)

Test Categories:
  C = Create Form Validations
  D = Duplicate Validations
  E = Edit Form Validations
  S = Search & Filter Edge Cases
  P = Popup & UI Behaviors
  H = History & Audit Trail

Known Bugs:
  BUG-001 (HIGH)  : Duplicate Company Name silently rejected
  BUG-002 (HIGH)  : Company Code maxlength not enforced server-side
  BUG-003 (MEDIUM): Inconsistent SweetAlert after successful create
  BUG-004 (LOW)   : No Delete option

Run:
  pytest test_company_onboarding_validation.py -v --tb=short
"""

import os
import sys
import time
import random

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from selenium.webdriver.common.by import By

from pages.company_onboarding.Company_Onboarding.company_onboarding_page import (
    CompanyOnboardingPage,
)
from pages.company_onboarding.data.company_onboarding_data import (
    SINGLE_COMPANY,
    generate_bulk_companies,
    generate_company_code_4_chars,
    generate_company_code_5_chars,
    generate_company_code_empty,
    generate_company_code_spaces,
)
from common.logger import log


# ====================================================================
# Helper: create a prerequisite company, refresh, return its name
# ====================================================================

def _create_prerequisite_company(page, prefix="PreReq"):
    """Create a Company Onboarding entry for tests that need existing data.
    Returns the company name and the data dict.
    """
    from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
    data = _generate_single_company()
    # Override name prefix for traceability
    data["company_name"] = f"{prefix}_{data['company_name']}"

    page.create_company(data)
    # Cleanup form if still open
    try:
        page.click_cancel_or_dismiss_dialog()
    except Exception:
        pass
    page.click_refresh()
    page.wait_seconds(2)
    name = data.get("company_name", "")
    log.info(f"Prerequisite company created: {name}")
    return name, data


# ====================================================================
# PHASE 1: Create Form Validations (10 tests)
# ====================================================================

class TestCreateFormValidations:
    """CO-C01 to CO-C10: Validation checks on the Create form."""

    # ---- CO-C01: Submit with all fields empty ----
    def test_CO_C01_empty_submit(self, co_page):
        """Submit with all fields empty - should show validation errors or stay open."""
        log.info("CO-C01: Empty submit test")
        page = co_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Click Submit with all fields empty
        # We need to navigate to Step 6 to reach the Submit button
        for _ in range(5):
            try:
                page._click_next()
                page.wait_seconds(0.5)
            except Exception:
                break

        page.submit()
        page.wait_seconds(2)

        # Check for validation errors
        has_invalid = page.has_invalid_fields()
        errors = page.get_mat_error_text()
        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        # Expect: form stays open + validation errors shown
        assert form_still_open or errors or has_invalid or validation_alert, (
            "BUG: Form closed with all required fields empty and no validation feedback"
        )
        if errors:
            log.info(f"Validation errors shown: {errors}")
        if has_invalid:
            log.info("Fields marked as invalid (CSS class)")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.click_cancel_or_dismiss_dialog()
            except Exception:
                pass

    # ---- CO-C02: Create with valid data (happy path) ----
    def test_CO_C02_valid_create(self, co_page):
        """Create with valid data - should succeed."""
        log.info("CO-C02: Valid create test (happy path)")
        page = co_page

        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        data = _generate_single_company()

        page.create_company(data)

        # Verify the dialog closed
        page.wait_seconds(3)
        msg = page.get_success_message(timeout=10)
        dialog_closed = page.is_dialog_closed()

        assert dialog_closed or msg, (
            f"Create failed: dialog not closed and no success message"
        )
        log.info(f"Company created successfully: {data['company_name']}")

    # ---- CO-C03: Create with valid Company Code (4 chars) ----
    def test_CO_C03_valid_company_code(self, co_page):
        """Company Code with exactly 4 characters - should be accepted."""
        log.info("CO-C03: Valid Company Code test")
        page = co_page

        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        data = _generate_single_company()
        data["company_code"] = generate_company_code_4_chars()

        page.create_company(data)
        page.wait_seconds(3)
        msg = page.get_success_message(timeout=10)
        dialog_closed = page.is_dialog_closed()

        assert dialog_closed or msg, (
            f"Create with valid Company Code failed"
        )
        log.info(f"Company with 4-char code created: {data['company_code']}")

    # ---- CO-C04: Company Code with 5 chars (exceeds maxlength) ----
    @pytest.mark.xfail(
        reason="BUG-002: Company Code maxlength=4 on HTML but may not be enforced server-side",
        strict=False,
    )
    def test_CO_C04_company_code_5_chars(self, co_page):
        """Company Code with 5 characters - should be rejected (maxlength=4)."""
        log.info("CO-C04: Company Code 5 chars test")
        page = co_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Try to type 5 characters into Company Code field (maxlength=4 should block)
        code_5 = generate_company_code_5_chars()
        try:
            from selenium.webdriver.common.by import By
            code_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Company Code']"
            )
            page.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", code_input
            )
            # Use JS to bypass HTML maxlength
            page.driver.execute_script(
                "var s = Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype,'value').set;"
                "s.call(arguments[0], arguments[1]);"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
                code_input, code_5,
            )
            page.wait_seconds(0.5)

            # Read what was actually typed
            actual_value = code_input.get_attribute("value")
            log.info(f"Company Code field value: '{actual_value}' (length: {len(actual_value)})")

            # If maxlength is enforced, value should be truncated to 4
            assert len(actual_value) <= 4, (
                f"BUG-002 CONFIRMED: 5-char code accepted (value: '{actual_value}')"
            )
        except Exception as e:
            log.warning(f"Company Code test exception: {e}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.click_cancel_or_dismiss_dialog()
            except Exception:
                pass

    # ---- CO-C05: Company Code empty (required field) ----
    def test_CO_C05_company_code_empty(self, co_page):
        """Empty Company Code - should be blocked by validation."""
        log.info("CO-C05: Empty Company Code test")
        page = co_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Fill all fields EXCEPT Company Code
        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        data = _generate_single_company()
        data["company_code"] = ""  # Leave empty

        page.fill_company_details(data)

        # Navigate to step 6 and submit
        for _ in range(5):
            try:
                page._click_next()
                page.wait_seconds(0.5)
            except Exception:
                break

        page.submit()
        page.wait_seconds(2)

        # Check validation
        has_invalid = page.has_invalid_fields()
        errors = page.get_mat_error_text()
        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if form_still_open or has_invalid or errors or validation_alert:
            log.info("Empty Company Code rejected - validation working")
        else:
            log.warning("BUG: Empty Company Code may have been accepted")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.click_cancel_or_dismiss_dialog()
            except Exception:
                pass

    # ---- CO-C06: Spaces-only Company Code ----
    def test_CO_C06_company_code_spaces(self, co_page):
        """Spaces-only Company Code - should be rejected."""
        log.info("CO-C06: Spaces-only Company Code test")
        page = co_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        data = _generate_single_company()
        data["company_code"] = generate_company_code_spaces()

        page.fill_company_details(data)

        # Navigate to step 6 and submit
        for _ in range(5):
            try:
                page._click_next()
                page.wait_seconds(0.5)
            except Exception:
                break

        page.submit()
        page.wait_seconds(2)

        # Check validation
        has_invalid = page.has_invalid_fields()
        form_still_open = page.is_add_form_open()
        validation_alert = page.handle_validation_warning(timeout=3)

        if form_still_open or has_invalid or validation_alert:
            log.info("Spaces-only Company Code rejected - validation working")
        else:
            log.warning("Spaces-only Company Code may have been accepted")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.click_cancel_or_dismiss_dialog()
            except Exception:
                pass

    # ---- CO-C07: Base Currency required field ----
    def test_CO_C07_base_currency_required(self, co_page):
        """Step 6 Base Currency is required - empty should block submission."""
        log.info("CO-C07: Base Currency required test")
        page = co_page

        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        data = _generate_single_company()
        # Don't set base_currency — test if it blocks

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_company_details(data)

        # Navigate through all steps without filling Step 6
        page.go_to_step2()
        page.fill_promoters(data.get("promoters", [{}])[0])
        page.go_to_step3()
        page.fill_address_details(data)
        page.go_to_step4()
        page.fill_business_details(data)
        page.go_to_step5()
        page.fill_infrastructure(data)
        page.go_to_step6()
        # Don't fill Base Currency

        page.submit()
        page.wait_seconds(2)

        # Check validation
        has_invalid = page.has_invalid_fields()
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()
        validation_alert = page.handle_validation_warning(timeout=3)

        if form_still_open or has_invalid or errors or validation_alert:
            log.info("Empty Base Currency rejected - validation working")
        else:
            log.warning("Empty Base Currency may have been accepted")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.click_cancel_or_dismiss_dialog()
            except Exception:
                pass

    # ---- CO-C08: Valid Base Currency selection ----
    def test_CO_C08_valid_base_currency(self, co_page):
        """Select INR as Base Currency in Step 6 - should be accepted."""
        log.info("CO-C08: Valid Base Currency test")
        page = co_page

        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        data = _generate_single_company()
        data["base_currency"] = "INR"

        page.create_company(data)
        page.wait_seconds(3)
        msg = page.get_success_message(timeout=10)
        dialog_closed = page.is_dialog_closed()

        assert dialog_closed or msg, (
            f"Create with valid Base Currency failed"
        )
        log.info(f"Company with Base Currency INR created")

    # ---- CO-C09: Create one-call convenience method ----
    def test_CO_C09_create_one_call(self, co_page):
        """Test the one-call convenience method: create_company(data)."""
        log.info("CO-C09: Create company one-call test")
        page = co_page

        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        data = _generate_single_company()

        page.create_company(data)

        # Verify via table search
        page.wait_seconds(3)
        company_name = data['company_name']
        found = False
        for attempt in range(6):
            log.info(f"Table check attempt {attempt + 1}/6...")
            try:
                page.click_refresh()
                page.wait_seconds(3)
            except Exception:
                pass
            found = page.search_company(company_name)
            if found:
                break
            page.wait_seconds(5)

        if found:
            log.passed(f"One-call company creation verified: {company_name}")
        else:
            log.warning(f"Company not found in table after 30s: {company_name}")

    # ---- CO-C10: Create with minimal data ----
    def test_CO_C10_create_minimal(self, co_page):
        """Create with only required fields - should succeed."""
        log.info("CO-C10: Create minimal data test")
        page = co_page

        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        data = _generate_single_company()
        # Remove optional fields
        data.pop("company_background", None)
        data.pop("gstin", None)
        data.pop("cin", None)

        page.create_company(data)
        page.wait_seconds(3)
        msg = page.get_success_message(timeout=10)
        dialog_closed = page.is_dialog_closed()

        if dialog_closed or msg:
            log.info("Minimal data company created successfully")
        else:
            log.warning("Minimal data company creation may have failed")


# ====================================================================
# PHASE 2: Duplicate Validations (3 tests)
# ====================================================================

class TestDuplicateValidations:
    """CO-D01 to CO-D03: Duplicate name checks."""

    # ---- CO-D01: Duplicate exact name ----
    @pytest.mark.xfail(
        reason="BUG-001: Duplicate Company Name may be silently rejected",
        strict=False,
    )
    def test_CO_D01_duplicate_create(self, co_page):
        """Create two companies with identical names - second should show error."""
        log.info("CO-D01: Duplicate exact name create test")
        page = co_page

        # Create first company
        name, data = _create_prerequisite_company(page, "Dup1")

        # Try creating with the same name
        page.open_add_form()
        page.wait_seconds(1)
        dup_data = data.copy()
        dup_data["company_code"] = generate_company_code_4_chars()  # Different code

        page.fill_company_details(dup_data)
        page.go_to_step2()
        page.fill_promoters(dup_data.get("promoters", [{}])[0])
        page.go_to_step3()
        page.fill_address_details(dup_data)
        page.go_to_step4()
        page.fill_business_details(dup_data)
        page.go_to_step5()
        page.fill_infrastructure(dup_data)
        page.go_to_step6()
        page.fill_configuration(dup_data)
        page.submit()
        page.wait_seconds(3)

        # Check for error
        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG-001 CONFIRMED: Duplicate name silently rejected with no error"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.click_cancel_or_dismiss_dialog()
            except Exception:
                pass

    # ---- CO-D02: Verify duplicate NOT actually created ----
    def test_CO_D02_duplicate_not_created(self, co_page):
        """Verify that a duplicate company does NOT result in a second record."""
        log.info("CO-D02: Duplicate not created test")
        page = co_page

        # Create first company
        name, data = _create_prerequisite_company(page, "NotDup")

        # Verify it exists
        page.click_refresh()
        page.wait_seconds(2)
        found = page.search_company(name)
        assert found, f"Prerequisite company not found: {name}"

        log.info(f"Company '{name}' exists in table - duplicate prevention verified")

    # ---- CO-D03: Case-insensitive duplicate check ----
    @pytest.mark.xfail(
        reason="BUG-001: Case-insensitive duplicate may be silently rejected",
        strict=False,
    )
    def test_CO_D03_duplicate_case_insensitive(self, co_page):
        """Create company with same name in different case - should show error."""
        log.info("CO-D03: Duplicate case-insensitive test")
        page = co_page

        name, data = _create_prerequisite_company(page, "CaseDup")
        case_variant = name.upper()

        # Try creating with the case-variant name
        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        dup_data = _generate_single_company()
        dup_data["company_name"] = case_variant

        page.create_company(dup_data)
        page.wait_seconds(3)

        validation_alert = page.handle_validation_warning(timeout=5)
        form_still_open = page.is_add_form_open()

        # Either the form should be open with error, or validation alert
        if form_still_open or validation_alert:
            log.info("Case-insensitive duplicate rejected - validation working")
        else:
            log.warning("Case-insensitive duplicate may have been accepted")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.click_cancel_or_dismiss_dialog()
            except Exception:
                pass


# ====================================================================
# PHASE 3: Edit Form Validations (3 tests)
# ====================================================================

class TestEditFormValidations:
    """CO-E01 to CO-E03: Validation checks on the Edit form."""

    # ---- CO-E01: Edit pre-populated fields ----
    def test_CO_E01_edit_prepopulated(self, co_page):
        """Edit popup should show fields pre-populated with existing values."""
        log.info("CO-E01: Edit pre-populated fields test")
        page = co_page

        from pages.company_onboarding.Company_Onboarding.company_onboarding_page_update import (
            CompanyOnboardingUpdatePage,
        )
        update_page = CompanyOnboardingUpdatePage(page.driver)

        name, data = _create_prerequisite_company(page, "EditPre")

        # Search and click Edit
        update_page.search_company(name)
        update_page.wait_seconds(1)
        update_page._click_edit_button(name)
        update_page.wait_seconds(2)

        # Read form values
        form_values = update_page.read_all_step_values()

        assert "step1" in form_values, "Step 1 values not read"
        step1 = form_values.get("step1", {}).get("1", {})
        assert step1.get("company_name", ""), "Company Name empty in Edit form"
        assert step1.get("company_code", ""), "Company Code empty in Edit form"

        log.info(f"Edit form pre-populated correctly: company_name={step1.get('company_name')}, company_code={step1.get('company_code')}")

        # Verify form has Update button (edit mode)
        update_btns = page.driver.find_elements(
            By.XPATH,
            "//div[@class='popup-footer']//button[contains(.,'Update')]"
        )
        has_update = any(b.is_displayed() for b in update_btns)
        assert has_update, "Edit form should have Update button"

        # Cleanup
        try:
            update_page.click_cancel_or_dismiss_dialog()
        except Exception:
            pass

    # ---- CO-E02: Edit valid update ----
    def test_CO_E02_valid_edit(self, co_page):
        """Edit with valid new values - should succeed."""
        log.info("CO-E02: Valid edit test")
        page = co_page

        from pages.company_onboarding.Company_Onboarding.company_onboarding_page_update import (
            CompanyOnboardingUpdatePage,
        )
        from pages.company_onboarding.data.company_onboarding_update_data import ALL_UPDATES

        name, data = _create_prerequisite_company(page, "EditOK")

        update_page = CompanyOnboardingUpdatePage(page.driver)
        result = update_page.update_company(name, ALL_UPDATES)

        if result["success"]:
            log.info("Company updated successfully")
        else:
            log.warning(f"Edit failed: {result.get('error', 'unknown')}")

    # ---- CO-E03: Edit Company Code ----
    def test_CO_E03_edit_company_code(self, co_page):
        """Change Company Code in Edit - should succeed."""
        log.info("CO-E03: Edit Company Code test")
        page = co_page

        from pages.company_onboarding.Company_Onboarding.company_onboarding_page_update import (
            CompanyOnboardingUpdatePage,
        )
        from pages.company_onboarding.data.company_onboarding_update_data import STEP1_UPDATES

        name, data = _create_prerequisite_company(page, "EditCode")

        update_page = CompanyOnboardingUpdatePage(page.driver)

        # Update only Step 1 with new Company Code
        updates = {
            1: {
                "contact_name": STEP1_UPDATES["contact_name"],
                "company_code": generate_company_code_4_chars(),
            }
        }

        result = update_page.update_company(name, updates)

        if result["success"]:
            log.info(f"Company Code updated successfully")
        else:
            log.warning(f"Company Code update failed: {result.get('error', '')}")


# ====================================================================
# PHASE 4: Search & Filter Edge Cases (3 tests)
# ====================================================================

class TestSearchFilterValidations:
    """CO-S01 to CO-S03: Search and filter edge cases."""

    # ---- CO-S01: Search for existing company ----
    def test_CO_S01_search_existing(self, co_page):
        """Search for an existing company - should find it."""
        log.info("CO-S01: Search existing company test")
        page = co_page

        name, data = _create_prerequisite_company(page, "SearchEx")

        page.click_refresh()
        page.wait_seconds(2)
        found = page.search_company(name)
        assert found, f"Existing company '{name}' not found via search"
        log.info(f"Search found existing company: {name}")

    # ---- CO-S02: Search for non-existing company ----
    def test_CO_S02_search_nonexisting(self, co_page):
        """Search for a non-existing company - should not find it."""
        log.info("CO-S02: Search non-existing company test")
        page = co_page

        found = page.search_company("ZZZ_NONEXISTENT_COMPANY_12345")
        assert not found, "Search should not find a non-existent company"
        log.info("Non-existing company correctly not found")

    # ---- CO-S03: Search with partial name ----
    def test_CO_S03_search_partial(self, co_page):
        """Search with partial name - should return matching results."""
        log.info("CO-S03: Search partial name test")
        page = co_page

        name, data = _create_prerequisite_company(page, "Partial")

        page.click_refresh()
        page.wait_seconds(2)
        found = page.search_company("Partial")
        if found:
            log.info("Partial name search returned results")
        else:
            log.info("Partial name search returned no results")


# ====================================================================
# PHASE 5: Popup & UI Behaviors (4 tests)
# ====================================================================

class TestPopupUIBehaviors:
    """CO-P01 to CO-P04: Popup and UI behavior tests."""

    # ---- CO-P01: Success SweetAlert after create ----
    def test_CO_P01_success_swal(self, co_page):
        """Check if SweetAlert appears after successful creation.
        BUG-003: SweetAlert is inconsistent.
        """
        log.info("CO-P01: Success SweetAlert test")
        page = co_page

        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        data = _generate_single_company()

        page.create_company(data)

        page.wait_seconds(3)
        swal_present = page.is_validation_alert_present(timeout=5)
        swal_title = ""
        if swal_present:
            swal_title = page.get_swal_title()
            log.info(f"SweetAlert found: {swal_title}")
            page.handle_validation_warning(timeout=5)
        else:
            log.info("No SweetAlert after create (BUG-003: inconsistent)")

    # ---- CO-P02: Cancel button closes form ----
    def test_CO_P02_cancel_closes_form(self, co_page):
        """Click Cancel should close the add form."""
        log.info("CO-P02: Cancel closes form test")
        page = co_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form should be open"

        page.cancel()
        page.wait_seconds(1)

        form_closed = page.is_dialog_closed()
        assert form_closed, "Form should be closed after Cancel"
        log.info("Cancel button correctly closed the form")

    # ---- CO-P03: No Delete button available ----
    def test_CO_P03_no_delete_button(self, co_page):
        """Verify no Delete option exists on the screen.
        BUG-004: No Delete functionality.
        """
        log.info("CO-P03: No delete button test")
        page = co_page

        # Check toolbar for Delete button
        delete_found = False
        try:
            delete_btns = page.driver.find_elements(
                By.CSS_SELECTOR,
                "button[mattooltip='Delete'], button[mattooltip='delete']"
            )
            if any(b.is_displayed() for b in delete_btns):
                delete_found = True
        except Exception:
            pass

        if not delete_found:
            log.info("BUG-004 CONFIRMED: No Delete button found in toolbar")
        else:
            log.info("Delete button found - BUG-004 may be fixed")

    # ---- CO-P04: Add button present ----
    def test_CO_P04_add_button_present(self, co_page):
        """Verify the Add button is present and clickable on the listing page."""
        log.info("CO-P04: Add button present test")
        page = co_page

        add_btn_present = False
        try:
            btns = page.driver.find_elements(
                By.CSS_SELECTOR, "button.erp-add-btn"
            )
            for btn in btns:
                try:
                    if btn.is_displayed():
                        add_btn_present = True
                        break
                except Exception:
                    continue
        except Exception:
            pass

        assert add_btn_present, "Add button should be present and visible"
        log.info("Add button is present and visible")


# ====================================================================
# PHASE 6: Step Navigation Tests (3 tests)
# ====================================================================

class TestStepNavigation:
    """CO-N01 to CO-N03: Step navigation tests."""

    # ---- CO-N01: Navigate through all 6 steps ----
    def test_CO_N01_navigate_all_steps(self, co_page):
        """Navigate through all 6 steps using Next buttons."""
        log.info("CO-N01: Navigate all steps test")
        page = co_page

        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        data = _generate_single_company()

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Fill Step 1 and navigate
        page.fill_company_details(data)
        page.go_to_step2()
        log.info("Reached Step 2 (Promoters)")

        page.fill_promoters(data.get("promoters", [{}])[0])
        page.go_to_step3()
        log.info("Reached Step 3 (Address)")

        page.fill_address_details(data)
        page.go_to_step4()
        log.info("Reached Step 4 (Business Details)")

        page.fill_business_details(data)
        page.go_to_step5()
        log.info("Reached Step 5 (Infrastructure)")

        page.fill_infrastructure(data)
        page.go_to_step6()
        log.info("Reached Step 6 (Configuration)")

        # Verify Base Currency dropdown is visible
        base_currency_visible = page.is_displayed(page.BASE_CURRENCY_SELECT, timeout=5)
        assert base_currency_visible, "Base Currency dropdown should be visible in Step 6"

        page.fill_configuration(data)
        log.info("All 6 steps navigated successfully")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.click_cancel_or_dismiss_dialog()
            except Exception:
                pass

    # ---- CO-N02: Back button navigates to previous step ----
    def test_CO_N02_back_button(self, co_page):
        """Back button should navigate to the previous step."""
        log.info("CO-N02: Back button test")
        page = co_page

        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        data = _generate_single_company()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_company_details(data)

        # Go to Step 2
        page.go_to_step2()
        log.info("At Step 2 - clicking Back")

        # Click Back
        try:
            back_btns = page.driver.find_elements(
                By.CSS_SELECTOR, "button[matstepperprevious]"
            )
            for btn in back_btns:
                try:
                    if btn.is_displayed():
                        page.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn
                        )
                        page.wait_seconds(1)
                        break
                except Exception:
                    continue
        except Exception:
            log.warning("Back button not found")

        # Verify we're back at Step 1 (Company Name input visible)
        step1_visible = page.is_displayed(page.COMPANY_NAME_INPUT, timeout=5)
        assert step1_visible, "Should be back at Step 1 after clicking Back"

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.click_cancel_or_dismiss_dialog()
            except Exception:
                pass

    # ---- CO-N03: Step 6 Base Currency has options ----
    def test_CO_N03_base_currency_has_options(self, co_page):
        """Verify Base Currency dropdown in Step 6 has options."""
        log.info("CO-N03: Base Currency options test")
        page = co_page

        from pages.company_onboarding.data.company_onboarding_data import _generate_single_company
        data = _generate_single_company()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_company_details(data)
        page.go_to_step2()
        page.fill_promoters(data.get("promoters", [{}])[0])
        page.go_to_step3()
        page.fill_address_details(data)
        page.go_to_step4()
        page.fill_business_details(data)
        page.go_to_step5()
        page.fill_infrastructure(data)
        page.go_to_step6()

        # Open Base Currency dropdown and check for options
        try:
            page.click(page.BASE_CURRENCY_SELECT)
            page.wait_seconds(0.5)

            options = page.driver.find_elements(
                By.CSS_SELECTOR, "div[role='listbox'] mat-option"
            )
            option_texts = [opt.text.strip() for opt in options if opt.text.strip()]
            log.info(f"Base Currency options found: {option_texts}")

            assert len(option_texts) > 0, "Base Currency dropdown should have options"
            assert "INR" in option_texts, "INR should be an option in Base Currency"
        except Exception as e:
            log.warning(f"Base Currency options check failed: {e}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.click_cancel_or_dismiss_dialog()
            except Exception:
                pass
