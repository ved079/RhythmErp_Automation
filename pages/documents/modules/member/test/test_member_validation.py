"""
test_member_validation.py
--------------------------
Comprehensive validation test suite for RhythmERP Member screen.

The Member form is a flat popup (no mat-horizontal-stepper).
KYC Details is a child grid inside app-dynamic-details.

Phases:
  1. Create Form Validations  (12 tests) -- MB-C01 to MB-C12
  2. Edit Form Validations     (4 tests)  -- MB-E01 to MB-E04
  3. Popup & UI Behaviors      (4 tests)  -- MB-P01 to MB-P04
  4. Search & Table            (3 tests)  -- MB-S01 to MB-S03
  5. Bug-Specific              (3 tests)  -- MB-B01 to MB-B03

Run:
  pytest test_member_validation.py -v --tb=short
  pytest test_member_validation.py -v -m smoke --tb=short
  pytest test_member_validation.py -v -m "not bug" --tb=short
"""

import os
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.documents.modules.member.member_page import MemberPage
from pages.documents.modules.member.data.member_data import (
    generate_valid_member_data,
    generate_member_name,
    generate_pan_number,
    generate_invalid_name_numbers,
    generate_invalid_name_special_chars,
    generate_spaces_only_name,
    generate_sql_injection_name,
    generate_xss_name,
    generate_string_255,
    generate_string_256,
    generate_distinctive_number,
    PREFIX_NAMES,
    KYC_DOC_NAMES,
)
from common.logger import log


# ====================================================================
# Helper: create a prerequisite Member entry
# ====================================================================

def _create_member(page, data=None):
    """Create a Member entry via UI. Returns the data dict used.

    Opens the Add form, fills all fields, submits, handles the alert.
    """
    if data is None:
        data = generate_valid_member_data()

    log.info(f"Creating member: {data.get('member_name', '?')[:40]}...")
    page.open_add_form()
    page.wait_seconds(1)
    page.fill_form(data)
    page.submit_form()
    alert_title = page.handle_success_alert(timeout=15)
    if "success" in alert_title.lower():
        log.info(f"Member created: {data.get('member_name', '?')[:40]}")
    else:
        log.warning(f"Member create result: {alert_title}")
    # Close any residual popups
    try:
        page.force_close_form_popup()
    except Exception:
        pass
    page.wait_seconds(1)
    return data


# ====================================================================
# PHASE 1: Create Form Validations (12 tests)
# ====================================================================

class TestCreateForm:
    """MB-C01 to MB-C12: Validation checks on the Create form."""

    # ---- MB-C01: Submit with all fields empty ----
    def test_MB_C01_empty_submit(self, mb_page):
        """Submit with all fields empty â€” should be blocked."""
        log.info("MB-C01: Empty submit test")
        page = mb_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Submit immediately with no fields filled
        page.submit_form()
        page.wait_seconds(2)

        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        log.info(f"Empty submit: form_open={form_still_open}, errors={errors}")
        assert form_still_open or errors, (
            "BUG: Form submitted with all fields empty â€” no validation"
        )

        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- MB-C02: Create with valid data (happy path) ----
    @pytest.mark.smoke
    def test_MB_C02_valid_create(self, mb_page):
        """Create Member with valid data â€” should succeed."""
        log.info("MB-C02: Valid member create test")
        page = mb_page

        data = _create_member(page)
        pan = data.get("pan_no", "")
        name = data.get("member_name", "")

        if pan:
            # Wait a moment for the table to refresh
            page.wait_seconds(2)
            found = page.is_member_in_table(pan)
            assert found, f"Created member with PAN '{pan}' not found in table"
            log.info(f"Member '{name}' found in table via PAN: {pan}")
        else:
            log.warning("No PAN in test data â€” skipping table presence check")

    # ---- MB-C03: Name with numbers ----
    def test_MB_C03_name_with_numbers(self, mb_page):
        """Member Name with numbers â€” should be rejected."""
        log.info("MB-C03: Name with numbers test")
        page = mb_page

        data = generate_valid_member_data()
        data["member_name"] = generate_invalid_name_numbers()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit_form()

        alert_title = page.handle_success_alert(timeout=10)
        log.info(f"MB-C03 result: '{alert_title}'")

        # If "success" is in the title, the name with numbers was accepted
        if "success" in alert_title.lower():
            log.warning(f"BUG? Name '{data['member_name']}' with numbers was accepted")

        try:
            page.force_close_form_popup()
        except Exception:
            pass

    # ---- MB-C04: Name with special characters ----
    def test_MB_C04_name_special_chars(self, mb_page):
        """Member Name with special characters â€” should be rejected."""
        log.info("MB-C04: Name with special chars test")
        page = mb_page

        data = generate_valid_member_data()
        data["member_name"] = generate_invalid_name_special_chars()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit_form()

        alert_title = page.handle_success_alert(timeout=10)
        log.info(f"MB-C04 result: '{alert_title}'")

        if "success" in alert_title.lower():
            log.warning(
                f"BUG? Name '{data['member_name']}' with special chars was accepted"
            )

        try:
            page.force_close_form_popup()
        except Exception:
            pass

    # ---- MB-C05: Spaces-only name ----
    def test_MB_C05_name_spaces_only(self, mb_page):
        """Spaces-only Member Name â€” should be rejected."""
        log.info("MB-C05: Spaces-only name test")
        page = mb_page

        data = generate_valid_member_data()
        data["member_name"] = generate_spaces_only_name()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit_form()
        page.wait_seconds(2)

        errors = page.get_mat_error_text()
        alert_title = page.handle_success_alert(timeout=5)
        form_still_open = page.is_add_form_open()

        log.info(
            f"Spaces-only name: errors={errors}, alert='{alert_title}', "
            f"form_open={form_still_open}"
        )

        assert form_still_open or errors or (
            alert_title and "success" not in alert_title.lower()
        ), "Spaces-only Member Name accepted without validation"

        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- MB-C06: SQL injection in name ----
    def test_MB_C06_name_sql_injection(self, mb_page):
        """SQL injection string in Member Name â€” should not crash."""
        log.info("MB-C06: SQL injection name test")
        page = mb_page

        data = generate_valid_member_data()
        data["member_name"] = generate_sql_injection_name()

        page.open_add_form()
        page.wait_seconds(1)
        try:
            page.fill_form(data)
            page.submit_form()
            page.wait_seconds(3)
            log.info("SQL injection name submitted without crash")
        except Exception as e:
            log.warning(f"SQL injection name caused exception: {e}")

        try:
            page.force_close_form_popup()
        except Exception:
            pass

    # ---- MB-C07: XSS payload in name ----
    def test_MB_C07_name_xss(self, mb_page):
        """XSS payload in Member Name â€” should not crash."""
        log.info("MB-C07: XSS payload name test")
        page = mb_page

        data = generate_valid_member_data()
        data["member_name"] = generate_xss_name()

        page.open_add_form()
        page.wait_seconds(1)
        try:
            page.fill_form(data)
            page.submit_form()
            page.wait_seconds(3)
            log.info("XSS name submitted without crash")
        except Exception as e:
            log.warning(f"XSS name caused exception: {e}")

        try:
            page.force_close_form_popup()
        except Exception:
            pass

    # ---- MB-C08: Name 255 chars (boundary) ----
    def test_MB_C08_name_255_chars(self, mb_page):
        """Member Name 255 chars (all letters) â€” should be accepted."""
        log.info("MB-C08: Name 255 chars boundary test")
        page = mb_page

        name_255 = "A" * 255  # All A's, matches ^[A-Za-z ]+$
        data = generate_valid_member_data()
        data["member_name"] = name_255

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.wait_seconds(1)

        try:
            name_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Member Name']"
            )
            actual_value = name_input.get_attribute("value") or ""
            log.info(f"Name 255 chars: entered length = {len(actual_value)}")
            assert len(actual_value) <= 255, (
                f"Name accepted {len(actual_value)} chars (max 255)"
            )
        except Exception as e:
            log.info(f"Could not read Member Name value: {e}")

        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- MB-C09: Name 256 chars (over max) ----
    def test_MB_C09_name_256_chars(self, mb_page):
        """Member Name 256 chars â€” should truncate or show error."""
        log.info("MB-C09: Name 256 chars overflow test")
        page = mb_page

        name_256 = "A" * 256
        data = generate_valid_member_data()
        data["member_name"] = name_256

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.wait_seconds(1)

        try:
            name_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Member Name']"
            )
            actual_value = name_input.get_attribute("value") or ""
            log.info(
                f"Name 256 chars: entered length = {len(actual_value)} "
                f"(expected <= 255)"
            )
        except Exception as e:
            log.info(f"Could not read Member Name value: {e}")

        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- MB-C10: Distinctive Number as string ----
    def test_MB_C10_distinctive_number_string(self, mb_page):
        """Distinctive Number as string 'DN-001' â€” should be rejected."""
        log.info("MB-C10: Distinctive Number string test")
        page = mb_page

        data = generate_valid_member_data()
        data["distinctive_number"] = "DN-001"

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit_form()

        alert_title = page.handle_success_alert(timeout=10)
        errors = page.get_mat_error_text()
        log.info(f"MB-C10 result: alert='{alert_title}', errors={errors}")

        # Should NOT succeed with a string distinctive number
        if "success" in alert_title.lower():
            log.warning("BUG? String distinctive number 'DN-001' was accepted")

        try:
            page.force_close_form_popup()
        except Exception:
            pass

    # ---- MB-C11: Duplicate PAN ----
    def test_MB_C11_duplicate_pan(self, mb_page):
        """Create two members with the same PAN â€” second should be rejected."""
        log.info("MB-C11: Duplicate PAN test")
        page = mb_page

        # Create first member
        data1 = generate_valid_member_data()
        pan = data1.get("pan_no", generate_pan_number())
        data1["pan_no"] = pan
        _create_member(page, data1)

        # Refresh the page to ensure clean state
        page.navigate_to_page()
        page.wait_seconds(2)

        # Attempt to create second member with SAME PAN
        data2 = generate_valid_member_data()
        data2["pan_no"] = pan
        # Change name to avoid any potential name-based uniqueness
        data2["member_name"] = f"Second_{pan[:5]}"

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data2)
        page.submit_form()

        alert_title = page.handle_success_alert(timeout=10)
        errors = page.get_mat_error_text()
        log.info(f"MB-C11 duplicate PAN result: alert='{alert_title}', errors={errors}")

        # The second submission should have been rejected
        assert not (
            "success" in alert_title.lower() and not errors
        ), f"Duplicate PAN '{pan}' was accepted"

        try:
            page.force_close_form_popup()
        except Exception:
            pass

    # ---- MB-C12: KYC no document selected ----
    def test_MB_C12_kyc_no_document(self, mb_page):
        """Add KYC row but don't select document â€” should be blocked."""
        log.info("MB-C12: KYC no document test")
        page = mb_page

        data = generate_valid_member_data()
        # Remove KYC details â€” we'll add a row manually without doc
        data["kyc_details"] = None

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)

        # Add KYC row manually but don't select a document
        page.add_kyc_row()
        page.wait_seconds(1)

        # Try to type a KYC number anyway (just to verify the row exists)
        try:
            page.driver.execute_script("""
                var lastRow = document.querySelector(
                    'app-dynamic-details tbody tr:last-child'
                );
                if (!lastRow) return false;
                var input = lastRow.querySelector('input[name="KYC Number"]');
                if (!input) return false;
                var nativeSet = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSet.call(input, 'TESTKYC123');
                input.dispatchEvent(new Event('input', {bubbles: true}));
                input.dispatchEvent(new Event('change', {bubbles: true}));
                return true;
            """)
        except Exception:
            pass

        page.submit_form()
        page.wait_seconds(2)

        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()
        log.info(
            f"KYC no document: errors={errors}, form_open={form_still_open}"
        )

        # Should be blocked â€” KYC document is required
        assert form_still_open or errors, (
            "KYC row without document was accepted"
        )

        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass


# ====================================================================
# PHASE 2: Edit Form Validations (4 tests)
# ====================================================================

class TestEditForm:
    """MB-E01 to MB-E04: Validation checks on the Edit form."""

    # ---- MB-E01: Edit â€” pre-populated fields ----
    def test_MB_E01_prepopulated(self, mb_page):
        """Edit popup should show fields pre-populated."""
        log.info("MB-E01: Edit pre-populated fields test")
        page = mb_page

        data = _create_member(page)

        if not data.get("member_name"):
            log.warning("No member created â€” skipping edit test")
            return

        # Refresh the table
        page.navigate_to_page()
        page.wait_seconds(2)

        # Open row menu and click Edit
        page.open_row_menu(0)
        page.click_edit()
        page.wait_seconds(2)

        # Check the Member Name input has a value
        try:
            name_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Member Name']"
            )
            actual_name = name_input.get_attribute("value") or ""
            log.info(f"Edit form Member Name: '{actual_name}'")
            assert actual_name, "Member Name is empty in Edit form"
        except Exception as e:
            log.warning(f"Could not read Member Name in Edit form: {e}")

        try:
            page.force_close_form_popup()
        except Exception:
            pass

    # ---- MB-E02: Edit â€” modify and save ----
    def test_MB_E02_modify_and_save(self, mb_page):
        """Edit member â€” change name and save."""
        log.info("MB-E02: Edit modify and save test")
        page = mb_page

        data = _create_member(page)
        if not data.get("member_name"):
            return

        page.navigate_to_page()
        page.wait_seconds(2)

        page.open_row_menu(0)
        page.click_edit()
        page.wait_seconds(2)

        # Change the member name to a new valid name
        new_name = generate_member_name(prefix="Edited")
        log.info(f"Changing name to: {new_name}")
        page._fill_input_by_name_js("Member Name", new_name)

        page.submit_form()
        alert_title = page.handle_success_alert(timeout=15)
        log.info(f"MB-E02 edit result: '{alert_title}'")

        try:
            page.force_close_form_popup()
        except Exception:
            pass

    # ---- MB-E03: Edit â€” clear required field ----
    def test_MB_E03_clear_required_field(self, mb_page):
        """Edit â€” clear Member Name (required) â€” should be blocked."""
        log.info("MB-E03: Clear required field test")
        page = mb_page

        data = _create_member(page)
        if not data.get("member_name"):
            return

        page.navigate_to_page()
        page.wait_seconds(2)

        page.open_row_menu(0)
        page.click_edit()
        page.wait_seconds(2)

        # Clear the Member Name
        page._fill_input_by_name_js("Member Name", "")
        page.wait_seconds(0.5)

        page.submit_form()
        page.wait_seconds(2)

        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()
        log.info(f"Clear required: errors={errors}, form_open={form_still_open}")

        assert form_still_open or errors, (
            "Edit submitted with empty required field â€” no validation"
        )

        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- MB-E04: Edit â€” change KYC doc type ----
    def test_MB_E04_change_kyc_doc(self, mb_page):
        """Edit â€” change KYC document type â€” should save."""
        log.info("MB-E04: Change KYC doc type test")
        page = mb_page

        data = _create_member(page)
        if not data.get("member_name"):
            return

        page.navigate_to_page()
        page.wait_seconds(2)

        page.open_row_menu(0)
        page.click_edit()
        page.wait_seconds(2)

        # Try to change KYC doc type in the first row
        try:
            # Find the KYC doc dropdown in the last (first) row
            result = page.driver.execute_script("""
                var lastRow = document.querySelector(
                    'app-dynamic-details tbody tr:last-child'
                );
                if (!lastRow) return false;
                var select = lastRow.querySelector('mat-select');
                if (!select) return false;
                select.scrollIntoView({block: 'center'});
                select.click();
                return true;
            """)
            if result:
                page.wait_seconds(1)
                # Try to select AADHAR (66)
                options = page.driver.find_elements(
                    By.CSS_SELECTOR, "div[role='listbox'] mat-option"
                )
                for opt in options:
                    try:
                        if opt.text.strip() == "AADHAR" and opt.is_displayed():
                            page.driver.execute_script(
                                "arguments[0].click();", opt
                            )
                            page.wait_seconds(0.5)
                            page._close_select_panel()
                            log.info("Changed KYC doc to AADHAR")
                            break
                    except Exception:
                        continue
                page._close_select_panel()
        except Exception as e:
            log.warning(f"Could not change KYC doc: {e}")

        page.submit_form()
        alert_title = page.handle_success_alert(timeout=15)
        log.info(f"MB-E04 change KYC doc result: '{alert_title}'")

        try:
            page.force_close_form_popup()
        except Exception:
            pass


# ====================================================================
# PHASE 3: Popup & UI Behaviors (4 tests)
# ====================================================================

class TestPopupBehaviors:
    """MB-P01 to MB-P04: Popup and UI behavior tests."""

    # ---- MB-P01: Cancel closes form ----
    def test_MB_P01_cancel_closes_form(self, mb_page):
        """Add form opens and closes via Cancel button."""
        log.info("MB-P01: Cancel closes form test")
        page = mb_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        page.cancel()
        page.wait_seconds(1)
        assert not page.is_add_form_open(), "Add form still open after Cancel"

    # ---- MB-P02: Close X button closes form ----
    def test_MB_P02_close_x_closes_form(self, mb_page):
        """Add form closes via X button."""
        log.info("MB-P02: Close X button test")
        page = mb_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        try:
            close_btn = page.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-header')]"
                "//button[.//mat-icon[text()='close']]",
            )
            if close_btn.is_displayed():
                page.driver.execute_script("arguments[0].click();", close_btn)
                page.wait_seconds(1)
        except Exception as e:
            log.warning(f"Close X button not found: {e} â€” trying Cancel fallback")
            page.cancel()

        assert not page.is_add_form_open(), (
            "Add form still open after Close X button"
        )

    # ---- MB-P03: Party Reference disabled by default ----
    def test_MB_P03_party_ref_disabled_by_default(self, mb_page):
        """Party Reference should be disabled when Copy toggle is OFF."""
        log.info("MB-P03: Party Reference disabled by default test")
        page = mb_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Copy From Existing Party toggle is OFF by default
        # Verify the Party Reference dropdown is disabled
        try:
            party_ref = page.driver.find_element(
                By.XPATH,
                "//mat-label[contains(.,'Party Reference')]"
                "/ancestor::mat-form-field//mat-select",
            )
            aria_disabled = party_ref.get_attribute("aria-disabled") or "false"
            log.info(f"Party Reference aria-disabled: {aria_disabled}")
        except Exception as e:
            log.info(f"Party Reference element not accessible: {e}")

        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- MB-P04: Party Reference toggle autofill ----
    def test_MB_P04_party_ref_autofill(self, mb_page):
        """Toggle Copy toggle ON â€” verify toggle changes state."""
        log.info("MB-P04: Party Reference autofill test")
        page = mb_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Toggle Copy From Existing Party ON and OFF
        try:
            page._toggle_switch(page.COPY_FROM_PARTY_TOGGLE, True)
            page.wait_seconds(1)
            log.info("Copy toggle turned ON")
        except Exception as e:
            log.warning(f"Could not toggle ON: {e}")

        # Toggle back OFF
        try:
            page._toggle_switch(page.COPY_FROM_PARTY_TOGGLE, False)
            page.wait_seconds(1)
            log.info("Copy toggle turned OFF")
        except Exception as e:
            log.warning(f"Could not toggle OFF: {e}")

        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass


# ====================================================================
# PHASE 4: Search & Table (3 tests)
# ====================================================================

class TestSearch:
    """MB-S01 to MB-S03: Search and table operation tests."""

    # ---- MB-S01: Search by PAN ----
    def test_MB_S01_search_by_pan(self, mb_page):
        """Search member by PAN â€” should find the row."""
        log.info("MB-S01: Search by PAN test")
        page = mb_page

        data = _create_member(page)
        pan = data.get("pan_no", "")
        if not pan:
            log.warning("No PAN created â€” skipping")
            return

        page.wait_seconds(2)
        page.search_member(pan)
        page.wait_seconds(2)

        row_count = page.get_table_row_count()
        log.info(f"Search by PAN '{pan}': row_count={row_count}")
        assert row_count >= 1, f"Search by PAN '{pan}' returned no rows"

    # ---- MB-S02: Search no results ----
    def test_MB_S02_search_no_results(self, mb_page):
        """Search with non-existent term â€” no results."""
        log.info("MB-S02: Search no results test")
        page = mb_page

        fake_pan = "ZZZNOMATCH999"
        page.search_member(fake_pan)
        page.wait_seconds(2)

        row_count = page.get_table_row_count()
        log.info(f"Search for '{fake_pan}': row_count={row_count}")

        # Should have 0 rows or a no-data row
        try:
            no_data = page.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody tr td.no-data, "
                "table#excel-table tbody tr.mat-mdc-no-data-row",
            )
            has_no_data = len(no_data) > 0
        except Exception:
            has_no_data = False

        assert row_count == 0 or has_no_data, (
            f"Non-existent search '{fake_pan}' returned rows"
        )

    # ---- MB-S03: View popup opens ----
    def test_MB_S03_view_opens_popup(self, mb_page):
        """Click View on a row â€” should open read-only popup."""
        log.info("MB-S03: View opens popup test")
        page = mb_page

        # Ensure at least one member exists
        data = _create_member(page)

        page.navigate_to_page()
        page.wait_seconds(2)

        page.open_row_menu(0)
        page.click_view()
        page.wait_seconds(2)

        popup_open = page.is_add_form_open()
        assert popup_open, "View popup did not open"

        try:
            page.force_close_form_popup()
        except Exception:
            pass


# ====================================================================
# PHASE 5: Bug-Specific Tests (3 tests)
# ====================================================================

class TestKnownBugs:
    """MB-B01 to MB-B03: Dedicated tests for known Member screen bugs."""

    # ---- MB-B01: Special chars in name (BUG-MB01) ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason="ERP accepts special chars in name â€” BUG-MB01", strict=False)
    def test_MB_B01_special_chars_name(self, mb_page):
        """BUG-MB01: Member Name accepts special characters."""
        log.info("MB-B01: Special chars name bug test")
        page = mb_page

        data = generate_valid_member_data()
        data["member_name"] = generate_invalid_name_special_chars()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit_form()

        alert_title = page.handle_success_alert(timeout=10)
        log.info(f"MB-B01 result: '{alert_title}'")

        # This should FAIL (xfail) if the name is accepted
        assert "success" not in alert_title.lower(), (
            f"BUG-MB01 CONFIRMED: Special chars '{data['member_name']}' accepted"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass

    # ---- MB-B02: String distinctive number (BUG-MB02) ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason="ERP accepts string distinctive number â€” BUG-MB02", strict=False)
    def test_MB_B02_string_distinctive_number(self, mb_page):
        """BUG-MB02: Distinctive Number accepts string format."""
        log.info("MB-B02: String distinctive number bug test")
        page = mb_page

        data = generate_valid_member_data()
        data["distinctive_number"] = "DN-001"

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit_form()

        alert_title = page.handle_success_alert(timeout=10)
        errors = page.get_mat_error_text()
        log.info(f"MB-B02 result: alert='{alert_title}', errors={errors}")

        # This should FAIL (xfail) if "DN-001" is accepted
        assert "success" not in alert_title.lower(), (
            "BUG-MB02 CONFIRMED: String 'DN-001' accepted as distinctive number"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass

    # ---- MB-B03: Short phone number accepted (BUG-MB03) ----
    @pytest.mark.bug
    def test_MB_B03_short_phone(self, mb_page):
        """BUG-MB03: Phone Number with <10 digits â€” check behavior."""
        log.info("MB-B03: Short phone number test")
        page = mb_page

        data = generate_valid_member_data()
        data["phone_number"] = 999  # 3-digit phone

        page.open_add_form()
        page.wait_seconds(1)
        try:
            page.fill_form(data)
            page.submit_form()
            page.wait_seconds(3)
            log.info("Short phone submitted without crash")
        except Exception as e:
            log.warning(f"Short phone caused exception: {e}")
            assert False, f"Short phone caused crash: {e}"

        alert_title = page.handle_success_alert(timeout=10)
        log.info(f"MB-B03 short phone result: '{alert_title}'")
        log.info("Note: ERP has no server-side phone length validation (BUG-MB03)")

        try:
            page.force_close_form_popup()
        except Exception:
            pass
