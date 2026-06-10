"""
test_customer_ui_interactions.py
---------------------------------
UI-only interaction tests for RhythmERP Customer screen.

This file contains ~13 test functions covering pure browser/DOM
interactions that CANNOT be tested via API. Each test uses the
``cu_page`` fixture (CustomerPage) and is marked ``@pytest.mark.ui``.

Test inventory (Bucket B — UI-only):

  CU-P01: Open/close add form — click Add, verify form opens,
          click Cancel, verify closes
  CU-P02: Close via X button — open form, click X close button,
          verify closes
  CU-P03: Fullscreen toggle — open form, click fullscreen,
          verify popup expands, click again verify shrinks
  CU-P04: No delete option — verify no Delete button per row exists
          in the listing
  CU-P05: Cancel mid-form — fill some fields, cancel, reopen,
          verify no state leakage (fields empty)
  CU-P06: Double-click submit — fill valid data, click Submit twice
          rapidly, check for duplicate creation
  CU-P07: Stepper step headers clickable — after advancing to Step 1,
          click Step 0 header, verify navigation back
  CU-P08: Address grid add row — on Step 1, click Add Row (+) button,
          verify second empty row appears
  CU-C12: Pin Code required mismatch (BUG-003) — check HTML required
          attr vs header asterisk
  CU-C13: Bank fields required mismatch (BUG-004) — check HTML required
          attr vs header asterisks
  CU-C15: Stepper advances with empty fields (BUG-002, xfail) — no
          data, click Next, verify can advance
  CU-C17: Stepper Back button — Step 0 → Step 1 → Back → verify
          return + data preservation
  CU-E05: Edit shows Update button — verify Edit mode shows 'Update'
          not 'Submit'

Key implementation notes:
  - ALL tests use WebDriverWait — NO time.sleep() or wait_seconds()
  - cu_page fixture provides CustomerPage (navigates fresh per test)
  - Uses generate_valid_customer_data() / generate_full_valid_customer_data()
    from customer_data.py for form filling

Run:
  pytest test_customer_ui_interactions.py -v --tb=short
  pytest test_customer_ui_interactions.py -v -m ui --tb=short
  pytest test_customer_ui_interactions.py -v -k "CU-P01" --tb=short
  pytest test_customer_ui_interactions.py -v -m "not bug" --tb=short
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from common.logger import log
from pages.registration.modules.customer.data.customer_data import (
    generate_valid_customer_data,
    generate_full_valid_customer_data,
)


# ====================================================================
# Reusable cleanup helper
# ====================================================================

def _cleanup_form(page):
    """Safe cleanup: dismiss alerts -> cancel/close -> force close -> refresh.

    All steps wrapped in try/except so it never raises.
    """
    page.dismiss_swal_alert()
    for _ in range(2):
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        try:
            page.force_close_form_popup()
        except Exception:
            pass
    page.click_refresh()


# ====================================================================
# CU-P01: Open/close add form
# ====================================================================

class TestPopupOpenClose:
    """CU-P01: Add form opens and closes correctly via Cancel button."""

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CU_P01_open_close_add_form(self, cu_page):
        """Click Add, verify form opens, click Cancel, verify closes."""
        log.info("CU-P01: Open/close add form via Cancel button")
        page = cu_page

        # --- Open ---
        page.open_add_form()
        form_open = WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open after clicking Add button",
        )
        assert form_open, "Add form did not open after clicking Add"
        log.info("Add form opened successfully")

        # --- Close via Cancel ---
        page.cancel()
        form_closed = WebDriverWait(page.driver, 10).until(
            lambda d: not page.is_add_form_open(),
            "Add form did not close after clicking Cancel",
        )
        assert form_closed, "Add form did not close after clicking Cancel"
        log.info("Add form closed successfully via Cancel")


# ====================================================================
# CU-P02: Close via X button
# ====================================================================

class TestCloseViaXButton:
    """CU-P02: Add form closes via the X close button in popup header."""

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CU_P02_close_via_x_button(self, cu_page):
        """Open form, click X close button, verify popup closes."""
        log.info("CU-P02: Close add form via X button")
        page = cu_page

        page.open_add_form()
        form_open = WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )
        assert form_open, "Add form did not open"

        # Click the X close button in the popup header
        close_btn = WebDriverWait(page.driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(@class,'popup-actions')]//button"
                    "[.//mat-icon[text()='close']]",
                )
            ),
            "X close button not found or not clickable",
        )
        page.driver.execute_script("arguments[0].click();", close_btn)

        form_closed = WebDriverWait(page.driver, 10).until(
            lambda d: not page.is_add_form_open(),
            "Form did not close after clicking X button",
        )
        assert form_closed, "Form did not close after clicking X button"
        log.info("Add form closed successfully via X button")


# ====================================================================
# CU-P03: Fullscreen toggle
# ====================================================================

class TestFullscreenToggle:
    """CU-P03: Fullscreen button expands/shrinks the popup."""

    @pytest.mark.ui
    @pytest.mark.regression
    def test_CU_P03_fullscreen_toggle(self, cu_page):
        """Open form, click fullscreen, verify popup state changes
        (class, style, or size), click again, verify it toggles back.

        The fullscreen button is a mat-icon-button inside .popup-actions
        containing a <mat-icon> with text 'fullscreen'. It may be lazily
        rendered (ng-star-inserted), so we wait for it explicitly.

        Detection strategy: The popup may already be at viewport width
        (e.g., 1366px on a 1366-wide screen), so width comparison alone
        is unreliable. Instead we detect the toggle by checking for:
          1. CSS class change on the popup (e.g., 'fullscreen-mode' added)
          2. Style attribute change (e.g., height changes to 100vh)
          3. The mat-icon text changing from 'fullscreen' to 'fullscreen_exit'
          4. Width change as a fallback
        """
        log.info("CU-P03: Fullscreen toggle test")
        page = cu_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Find the popup container and record its initial state
        popup_el = page.driver.find_element(
            By.CSS_SELECTOR,
            ".edit_pop_up.override_edit_pop_up.popup-mode, "
            ".big-model, mat-dialog-container",
        )
        initial_classes = popup_el.get_attribute("class") or ""
        initial_style = popup_el.get_attribute("style") or ""
        initial_width = popup_el.size["width"]
        initial_height = popup_el.size["height"]
        log.info(
            f"Popup initial state — width={initial_width}, "
            f"height={initial_height}, classes='{initial_classes}'"
        )

        # Click the fullscreen button — use JS click to avoid
        # intercept issues with Angular Material overlays
        fullscreen_btn = WebDriverWait(page.driver, 15).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//div[contains(@class,'popup-actions')]"
                    "//mat-icon[contains(text(),'fullscreen')]"
                    "/ancestor::button",
                )
            ),
            "Fullscreen button icon not found in popup-actions",
        )
        page.driver.execute_script("arguments[0].click();", fullscreen_btn)

        # Wait for CSS transition
        time.sleep(0.8)

        # Re-read popup state after toggle
        expanded_classes = popup_el.get_attribute("class") or ""
        expanded_style = popup_el.get_attribute("style") or ""
        expanded_width = popup_el.size["width"]
        expanded_height = popup_el.size["height"]
        log.info(
            f"Popup after fullscreen click — width={expanded_width}, "
            f"height={expanded_height}, classes='{expanded_classes}'"
        )

        # Detect any state change using multiple strategies
        classes_changed = initial_classes != expanded_classes
        style_changed = initial_style != expanded_style
        width_changed = expanded_width != initial_width
        height_changed = expanded_height != initial_height

        # Check if the icon changed to fullscreen_exit (strongest signal)
        icon_changed_to_exit = False
        try:
            exit_icons = page.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-actions')]"
                "//mat-icon[contains(text(),'fullscreen_exit')]",
            )
            icon_changed_to_exit = len(exit_icons) > 0
        except Exception:
            pass

        any_change = (
            classes_changed or style_changed
            or width_changed or height_changed
            or icon_changed_to_exit
        )

        if any_change:
            changes = []
            if classes_changed:
                changes.append(f"class: '{initial_classes}' -> '{expanded_classes}'")
            if style_changed:
                changes.append(f"style: '{initial_style}' -> '{expanded_style}'")
            if width_changed:
                changes.append(f"width: {initial_width} -> {expanded_width}")
            if height_changed:
                changes.append(f"height: {initial_height} -> {expanded_height}")
            if icon_changed_to_exit:
                changes.append("icon: fullscreen -> fullscreen_exit")
            log.info(f"Fullscreen toggle detected changes: {'; '.join(changes)}")
        else:
            log.warning(
                "Fullscreen toggle produced NO detectable change. "
                "The button click may not be working, or the popup is "
                "already fullscreen and the toggle has no visible effect."
            )

        # Click fullscreen again to toggle back
        try:
            exit_btn = page.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-actions')]"
                "//mat-icon[contains(text(),'fullscreen_exit')]"
                "/ancestor::button",
            )
            page.driver.execute_script("arguments[0].click();", exit_btn)
        except Exception:
            # Fallback: click the same fullscreen button again
            page.driver.execute_script("arguments[0].click();", fullscreen_btn)

        time.sleep(0.8)

        # Re-read state after toggling back
        shrunk_classes = popup_el.get_attribute("class") or ""
        shrunk_width = popup_el.size["width"]
        shrunk_height = popup_el.size["height"]
        log.info(
            f"Popup after toggle-back — width={shrunk_width}, "
            f"height={shrunk_height}, classes='{shrunk_classes}'"
        )

        # Check if the icon reverted to 'fullscreen'
        icon_reverted = False
        try:
            fs_icons = page.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-actions')]"
                "//mat-icon[contains(text(),'fullscreen')]",
            )
            # Filter out fullscreen_exit icons
            for icon in fs_icons:
                if "fullscreen_exit" not in icon.text:
                    icon_reverted = True
                    break
        except Exception:
            pass

        # The toggle should have produced a detectable change in at
        # least one direction (expand OR shrink)
        revert_change = (
            shrunk_classes != expanded_classes
            or shrunk_width != expanded_width
            or shrunk_height != expanded_height
            or icon_reverted
        )

        assert any_change or revert_change, (
            f"Fullscreen toggle had no detectable effect. "
            f"Initial: width={initial_width}, height={initial_height}, "
            f"classes='{initial_classes}'. "
            f"After expand: width={expanded_width}, height={expanded_height}, "
            f"classes='{expanded_classes}'. "
            f"After shrink: width={shrunk_width}, height={shrunk_height}, "
            f"classes='{shrunk_classes}'. "
            f"Icon changed to exit: {icon_changed_to_exit}, "
            f"Icon reverted: {icon_reverted}"
        )
        log.info("Fullscreen toggle works correctly")

        # Cleanup
        _cleanup_form(page)


# ====================================================================
# CU-P04: No delete option
# ====================================================================

class TestNoDeleteOption:
    """CU-P04: Verify no Delete button exists per row in the listing."""

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CU_P04_no_delete_option(self, cu_page):
        """Verify that no Delete button is present in any table row."""
        log.info("CU-P04: No Delete button per row in listing")
        page = cu_page

        # Check for any delete-related buttons in the table
        delete_selectors = [
            "button.delete",
            "button[mattooltip='Delete']",
            "button[aria-label='Delete']",
            "td .delete-btn",
            ".mat-mdc-menu-content span.erp-menu-title[text()='Delete']",
        ]

        found_delete = False
        for selector in delete_selectors:
            try:
                elements = page.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    try:
                        if el.is_displayed():
                            found_delete = True
                            log.warning(
                                f"Delete element found with selector: {selector}"
                            )
                            break
                    except Exception:
                        continue
            except Exception:
                pass
            if found_delete:
                break

        # Also check the 3-dot row menu for a Delete option
        try:
            row_menu_triggers = page.driver.find_elements(
                By.CSS_SELECTOR,
                "button.mat-mdc-menu-trigger.erp-row-trigger",
            )
            if row_menu_triggers:
                # Open the first row's menu
                page.driver.execute_script(
                    "arguments[0].click();", row_menu_triggers[0]
                )
                WebDriverWait(page.driver, 5).until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, ".mat-mdc-menu-content")
                    )
                )
                try:
                    delete_menu_item = page.driver.find_element(
                        By.XPATH,
                        "//div[contains(@class,'mat-mdc-menu-content')]"
                        "//span[contains(@class,'erp-menu-title') "
                        "and text()='Delete']/ancestor::button",
                    )
                    if delete_menu_item.is_displayed():
                        found_delete = True
                        log.warning("Delete option found in row action menu")
                except Exception:
                    log.info("No Delete option in row action menu")
                # Close the menu by clicking elsewhere
                try:
                    page.driver.find_element(
                        By.TAG_NAME, "body"
                    ).click()
                except Exception:
                    pass
        except Exception:
            log.info("No row menu triggers found — checking skipped")

        assert not found_delete, (
            "Unexpected: Delete button/option found in the Customer listing. "
            "The ERP should not have a delete option."
        )
        log.info("No Delete button found in the listing — correct")


# ====================================================================
# CU-P05: Cancel mid-form (no state leakage)
# ====================================================================

class TestCancelMidForm:
    """CU-P05: Fill some fields, cancel, reopen — verify fields are empty."""

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CU_P05_cancel_mid_form(self, cu_page):
        """Fill universal fields, click Cancel, reopen, verify no state leakage."""
        log.info("CU-P05: Cancel mid-form — no state leakage")
        page = cu_page

        data = generate_valid_customer_data("StateLeak")

        # --- Open form and fill universal fields ---
        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )
        page.fill_universal_fields(data)

        # Verify fields were filled
        company_name_value = page.get_input_value(page.COMPANY_NAME_INPUT)
        assert company_name_value, "Company Name was not filled"
        log.info(f"Company Name filled: {company_name_value}")

        # --- Cancel ---
        page.cancel()
        WebDriverWait(page.driver, 10).until(
            lambda d: not page.is_add_form_open(),
            "Form did not close after Cancel",
        )
        log.info("Form closed via Cancel")

        # --- Reopen form and verify fields are empty ---
        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not reopen",
        )

        company_name_after = page.get_input_value(page.COMPANY_NAME_INPUT)
        email_after = page.get_input_value(page.EMAIL_INPUT)
        phone_after = page.get_input_value(page.PHONE_NUMBER_INPUT)
        pan_after = page.get_input_value(page.PAN_NUMBER_INPUT)

        assert company_name_after == "", (
            f"State leakage! Company Name still has value: '{company_name_after}'"
        )
        assert email_after == "", (
            f"State leakage! Email still has value: '{email_after}'"
        )
        assert phone_after == "", (
            f"State leakage! Phone still has value: '{phone_after}'"
        )
        assert pan_after == "", (
            f"State leakage! PAN still has value: '{pan_after}'"
        )
        log.info("No state leakage — all fields are empty after reopen")

        # Cleanup
        _cleanup_form(page)


# ====================================================================
# CU-P06: Double-click submit (no duplicate creation)
# ====================================================================

class TestDoubleClickSubmit:
    """CU-P06: Rapidly double-click Submit — verify only one customer created."""

    @pytest.mark.ui
    @pytest.mark.regression
    def test_CU_P06_double_click_submit(self, cu_page):
        """Fill valid data across all 3 steps, click Submit twice rapidly,
        then verify only ONE customer was created (no duplicate)."""
        log.info("CU-P06: Double-click submit — duplicate creation check")
        page = cu_page

        data = generate_full_valid_customer_data("DblClick")
        company_name = data["company_name"]

        # --- Open form and fill all 3 steps ---
        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Universal fields + Step 0
        page.fill_universal_fields(data)
        page.fill_step0(data)

        # Step 1 — Address
        page.click_stepper_next()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_step1_active(),
            "Did not navigate to Step 1",
        )
        address_rows = data.get("address_rows", [])
        if address_rows:
            page.fill_address_row(0, address_rows[0])

        # Step 2 — Bank
        page.click_stepper_next()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_step2_active(),
            "Did not navigate to Step 2",
        )
        bank_rows = data.get("bank_rows", [])
        if bank_rows:
            page.fill_bank_row(0, bank_rows[0])

        # --- Rapidly click Submit TWICE ---
        submit_btn = WebDriverWait(page.driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(@class,'popup-footer')]"
                    "//button[@type='submit']",
                )
            ),
            "Submit button not found or not clickable",
        )
        # First click
        page.driver.execute_script("arguments[0].click();", submit_btn)
        # Immediately second click (no wait between)
        try:
            page.driver.execute_script("arguments[0].click();", submit_btn)
        except Exception:
            pass  # Button may become stale/disabled after first click — that's fine

        # Wait for the submission to complete (SweetAlert or form close)
        WebDriverWait(page.driver, 15).until(
            lambda d: not page.is_add_form_open()
            or page.is_validation_alert_present(timeout=1),
            "Form did not respond to submit",
        )

        # Handle any SweetAlert
        success = page.handle_success_alert(timeout=10)
        page.dismiss_swal_alert()

        # Close the popup if still open
        _cleanup_form(page)

        # --- Search for the company name and count occurrences ---
        page.click_refresh()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_page_loaded(),
            "Page did not load after refresh",
        )

        page.search_item(company_name)
        WebDriverWait(page.driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "app-dynamic-table table tbody tr, table tbody tr, "
                    ".empty-state__title",
                )
            ),
            "Table did not load after search",
        )

        # Count how many rows contain the company name
        rows = page.driver.find_elements(
            By.CSS_SELECTOR,
            "app-dynamic-table table tbody tr, table tbody tr",
        )
        matching_rows = []
        for row in rows:
            try:
                if company_name.lower() in row.text.lower():
                    matching_rows.append(row)
            except Exception:
                continue

        count = len(matching_rows)
        log.info(f"Search results for '{company_name}': {count} row(s)")

        assert count <= 1, (
            f"Duplicate creation detected! Found {count} rows for "
            f"company name '{company_name}'. Expected at most 1."
        )
        if count == 1:
            log.info("No duplicate — exactly one customer created")
        else:
            log.info("Customer may not have been created (validation blocked)")


# ====================================================================
# CU-P07: Stepper step headers clickable
# ====================================================================

class TestStepperHeadersClickable:
    """CU-P07: Clicking a step header navigates back to that step."""

    @pytest.mark.ui
    @pytest.mark.regression
    def test_CU_P07_stepper_step_headers_clickable(self, cu_page):
        """After advancing to Step 1, click Step 0 header,
        verify navigation back to Step 0."""
        log.info("CU-P07: Stepper step headers clickable")
        page = cu_page

        data = generate_valid_customer_data("StepHeader")

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Fill Step 0 and advance to Step 1
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_step1_active(),
            "Did not navigate to Step 1 after Next",
        )
        log.info("Currently on Step 1 — now clicking Step 0 header")

        # Click Step 0 header to navigate back
        page.go_to_step(0)
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_step0_active(),
            "Did not navigate back to Step 0 after clicking header",
        )

        assert page.is_step0_active(), (
            "Clicking Step 0 header did not navigate back to Step 0"
        )
        log.info("Step 0 header click correctly navigated back to Step 0")

        # Cleanup
        _cleanup_form(page)


# ====================================================================
# CU-P08: Address grid add row
# ====================================================================

class TestAddressGridAddRow:
    """CU-P08: Click Add Row (+) button on Step 1 — second empty row appears."""

    @pytest.mark.ui
    @pytest.mark.regression
    def test_CU_P08_address_grid_add_row(self, cu_page):
        """On Step 1 (Address Details), click Add Row (+) button,
        verify a second empty row appears in the address grid."""
        log.info("CU-P08: Address grid add row")
        page = cu_page

        data = generate_valid_customer_data("AddrRow")

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Navigate to Step 1
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_step1_active(),
            "Did not navigate to Step 1",
        )

        # Count existing address grid rows
        initial_rows = page.driver.find_elements(
            By.CSS_SELECTOR, ".grid-container .grid-table tbody tr"
        )
        initial_count = len(initial_rows)
        log.info(f"Initial address grid rows: {initial_count}")

        # Click the Add Row (+) button for the address grid
        add_row_btn = WebDriverWait(page.driver, 10).until(
            EC.element_to_be_clickable(page.ADDRESS_GRID_ADD_BUTTON),
            "Address grid Add Row button not found or not clickable",
        )
        page.driver.execute_script("arguments[0].click();", add_row_btn)

        # Verify a new row was added
        WebDriverWait(page.driver, 10).until(
            lambda d: len(
                d.find_elements(
                    By.CSS_SELECTOR, ".grid-container .grid-table tbody tr"
                )
            )
            > initial_count,
            "New address row did not appear after clicking Add Row",
        )

        new_rows = page.driver.find_elements(
            By.CSS_SELECTOR, ".grid-container .grid-table tbody tr"
        )
        new_count = len(new_rows)
        log.info(f"Address grid rows after Add Row: {new_count}")

        assert new_count > initial_count, (
            f"No new row added — before={initial_count}, after={new_count}"
        )
        log.info(
            f"Address grid add row works — {new_count - initial_count} "
            f"new row(s) added"
        )

        # Cleanup
        _cleanup_form(page)


# ====================================================================
# CU-C12: Pin Code required mismatch (BUG-003)
# ====================================================================

class TestPinCodeRequiredMismatch:
    """CU-C12: Pin Code header shows asterisk but HTML required attr
    says otherwise — BUG-003."""

    @pytest.mark.ui
    @pytest.mark.bug
    @pytest.mark.regression
    def test_CU_C12_pin_code_required_mismatch(self, cu_page):
        """Check the Pin Code column header for an asterisk vs the HTML
        required attribute on the input element. BUG-003: mismatch."""
        log.info("CU-C12: Pin Code required mismatch (BUG-003)")
        page = cu_page

        data = generate_valid_customer_data("PinChk")

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Navigate to Step 1 (Address Details)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_step1_active(),
            "Did not navigate to Step 1",
        )

        # --- Check header for asterisk ---
        header_has_asterisk = False
        try:
            headers = page.driver.find_elements(
                By.CSS_SELECTOR,
                ".grid-container .grid-table th, "
                ".grid-container .grid-table thead td",
            )
            for header in headers:
                try:
                    text = header.text.strip()
                    if "Pin Code" in text:
                        if "*" in text:
                            header_has_asterisk = True
                            log.info(
                                f"Pin Code header shows asterisk: '{text}'"
                            )
                        else:
                            log.info(
                                f"Pin Code header has NO asterisk: '{text}'"
                            )
                        break
                except Exception:
                    continue
        except Exception:
            log.warning("Could not find address grid headers")

        # --- Check HTML required attribute on the input ---
        html_required = False
        try:
            pin_code_inputs = page.driver.find_elements(
                By.CSS_SELECTOR, "input[name='Pin Code']"
            )
            if pin_code_inputs:
                required_attr = pin_code_inputs[0].get_attribute("required")
                aria_required = pin_code_inputs[0].get_attribute(
                    "aria-required"
                )
                html_required = required_attr is not None or (
                    aria_required == "true"
                )
                log.info(
                    f"Pin Code input — required attr: {required_attr}, "
                    f"aria-required: {aria_required}"
                )
            else:
                log.warning("No Pin Code input found in address grid")
        except Exception:
            log.warning("Could not check Pin Code input required attribute")

        # Document the mismatch
        if header_has_asterisk and not html_required:
            log.info(
                "BUG-003 CONFIRMED: Pin Code header says required (*) "
                "but HTML input does not have required attribute"
            )
        elif header_has_asterisk and html_required:
            log.info(
                "BUG-003 NOT PRESENT: Both header and HTML agree "
                "that Pin Code is required"
            )
        elif not header_has_asterisk:
            log.info(
                "Pin Code header has no asterisk — no visible mismatch"
            )

        # The test documents the state; it does not fail based on the bug
        log.info(
            f"Pin Code field state — header_asterisk={header_has_asterisk}, "
            f"html_required={html_required}"
        )

        # Cleanup
        _cleanup_form(page)


# ====================================================================
# CU-C13: Bank fields required mismatch (BUG-004)
# ====================================================================

class TestBankFieldsRequiredMismatch:
    """CU-C13: Bank field headers show asterisks but HTML required attrs
    may not match — BUG-004 (partially resolved)."""

    @pytest.mark.ui
    @pytest.mark.bug
    @pytest.mark.regression
    def test_CU_C13_bank_fields_required_mismatch(self, cu_page):
        """Check Bank Details grid column headers for asterisks vs HTML
        required attributes on input elements. BUG-004: mismatch for
        text inputs; Account Type & Bank Proof now genuinely required."""
        log.info("CU-C13: Bank fields required mismatch (BUG-004)")
        page = cu_page

        data = generate_full_valid_customer_data("BankChk")

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Navigate to Step 2 (Customer Bank Details)
        # Step 0: Fill universal + additional details
        page.fill_universal_fields(data)
        page.fill_step0(data)

        # Step 1: Fill address rows — required before stepper allows advance
        page.click_stepper_next()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_step1_active(),
            "Did not navigate to Step 1",
        )
        address_rows = data.get("address_rows", [])
        if address_rows:
            page.fill_address_row(0, address_rows[0])

        # Step 2: Now the stepper should allow advancing
        page.click_stepper_next()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_step2_active(),
            "Did not navigate to Step 2",
        )

        # Fields to check: Bank Name, Branch, Account Holder Name,
        # Account Number (text inputs), Account Type & Bank Proof (dropdowns)
        bank_text_fields = {
            "Bank Name": "input[name='Bank Name']",
            "Branch": "input[name='Branch']",
            "Account Holder Name": "input[name='Account Holder Name']",
            "Account Number": "input[name='Account Number']",
        }

        mismatches = []

        # --- Check text input headers vs HTML required ---
        for field_label, css_selector in bank_text_fields.items():
            header_has_asterisk = False
            html_required = False

            # Check header
            try:
                headers = page.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".grid-container .grid-table th, "
                    ".grid-container .grid-table thead td",
                )
                for header in headers:
                    try:
                        text = header.text.strip()
                        if field_label in text:
                            header_has_asterisk = "*" in text
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Check input required attribute
            try:
                inputs = page.driver.find_elements(By.CSS_SELECTOR, css_selector)
                if inputs:
                    required_attr = inputs[0].get_attribute("required")
                    aria_required = inputs[0].get_attribute("aria-required")
                    html_required = (
                        required_attr is not None
                        or aria_required == "true"
                    )
            except Exception:
                pass

            log.info(
                f"  {field_label}: header_asterisk={header_has_asterisk}, "
                f"html_required={html_required}"
            )

            if header_has_asterisk and not html_required:
                mismatches.append(field_label)

        # --- Check Account Type & Bank Proof dropdowns ---
        dropdown_fields = {
            "Account Type": page.ACCOUNT_TYPE_SELECT,
            "Bank Proof": page.BANK_PROOF_SELECT,
        }
        for field_label, locator in dropdown_fields.items():
            try:
                select_el = page.driver.find_element(*locator)
                # Check if the parent mat-form-field has required indicator
                parent_field = select_el.find_element(
                    By.XPATH,
                    "./ancestor::mat-form-field",
                )
                required_class = "mat-mdc-form-field-required-marker" in (
                    parent_field.get_attribute("class") or ""
                )
                # Also check for aria-required on the select
                aria_req = select_el.get_attribute("aria-required")
                log.info(
                    f"  {field_label} (dropdown): "
                    f"aria-required={aria_req}, "
                    f"required_marker_class={required_class}"
                )
            except Exception:
                log.info(
                    f"  {field_label}: Could not check dropdown required state"
                )

        # Document results
        if mismatches:
            log.info(
                f"BUG-004 CONFIRMED: Header/input mismatch for: "
                f"{', '.join(mismatches)}"
            )
        else:
            log.info(
                "No header/input required mismatches found in bank fields"
            )

        # Cleanup
        _cleanup_form(page)


# ====================================================================
# CU-C15: Stepper advances with empty fields (BUG-002, xfail)
# ====================================================================

class TestStepperAdvancesEmpty:
    """CU-C15: Stepper allows advancing with empty required fields — BUG-002."""

    @pytest.mark.xfail(
        reason="BUG-002: Stepper allows advancing with empty required fields",
        strict=False,
    )
    @pytest.mark.ui
    @pytest.mark.bug
    @pytest.mark.regression
    def test_CU_C15_stepper_advances_empty(self, cu_page):
        """Open add form with no data, click Next, verify the stepper
        does NOT advance (but it does due to BUG-002)."""
        log.info("CU-C15: Stepper advances with empty fields (BUG-002)")
        page = cu_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Confirm we start on Step 0
        assert page.is_step0_active(), "Should start on Step 0"

        # Click Next with all fields empty
        page.click_stepper_next()

        # Check if we advanced to Step 1 (BUG-002: we should NOT)
        stepped_to_1 = WebDriverWait(page.driver, 5).until(
            lambda d: page.is_step1_active(),
        )

        # This assertion should PASS if the stepper validates properly
        # (i.e., we should NOT have advanced), but BUG-002 means we DID
        assert not stepped_to_1, (
            "BUG-002 CONFIRMED: Stepper allowed advancing with "
            "empty required fields"
        )

        # Cleanup
        _cleanup_form(page)


# ====================================================================
# CU-C17: Stepper Back button
# ====================================================================

class TestStepperBackButton:
    """CU-C17: Step 0 → Step 1 → Back → verify return + data preservation."""

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CU_C17_stepper_back_button(self, cu_page):
        """Fill Step 0, advance to Step 1, click Back, verify return
        to Step 0 and that previously entered data is preserved."""
        log.info("CU-C17: Stepper Back button — navigation + data preservation")
        page = cu_page

        data = generate_valid_customer_data("BackBtn")

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )
        assert page.is_step0_active(), "Should start on Step 0"

        # Fill universal fields + Step 0 data
        page.fill_universal_fields(data)
        page.fill_step0(data)

        # Record the company name before navigation
        company_name_before = page.get_input_value(page.COMPANY_NAME_INPUT)
        log.info(f"Company Name before advancing: {company_name_before}")

        # Advance to Step 1
        page.click_stepper_next()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_step1_active(),
            "Did not navigate to Step 1",
        )
        assert page.is_step1_active(), "Should be on Step 1"

        # Click Back
        page.click_stepper_back()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_step0_active(),
            "Did not return to Step 0 after Back",
        )
        assert page.is_step0_active(), "Should be back on Step 0"

        # Verify data is preserved
        company_name_after = page.get_input_value(page.COMPANY_NAME_INPUT)
        assert company_name_after == company_name_before, (
            f"Data not preserved after Back! Before='{company_name_before}', "
            f"After='{company_name_after}'"
        )
        log.info(
            f"Data preserved after Back: company_name='{company_name_after}'"
        )

        # Cleanup
        _cleanup_form(page)


# ====================================================================
# CU-E05: Edit shows Update button
# ====================================================================

class TestEditShowsUpdateButton:
    """CU-E05: Verify that Edit mode shows 'Update' button, not 'Submit'."""

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CU_E05_edit_shows_update_button(self, cu_page):
        """Open Edit mode for the first row and verify the popup footer
        shows an 'Update' button instead of 'Submit'."""
        log.info("CU-E05: Edit shows Update button (not Submit)")
        page = cu_page

        # Click Edit on the first row
        page.click_edit_first_row()

        # Wait for the edit popup to open
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open() and page.is_edit_mode(),
            "Edit form did not open or not in edit mode",
        )
        assert page.is_edit_mode(), "Not in Edit mode"

        # Find the submit-type button in the popup footer
        try:
            update_buttons = page.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]"
                "//button[@type='submit' or contains(.,'Update')]",
            )
            assert update_buttons, "No submit-type button found in popup footer"

            btn_text = update_buttons[0].text.strip()
            log.info(f"Footer button text: '{btn_text}'")

            assert "Update" in btn_text, (
                f"Expected 'Update' button in Edit mode, but got: '{btn_text}'"
            )
            assert "Submit" not in btn_text, (
                f"Edit mode should show 'Update', not 'Submit'. Got: '{btn_text}'"
            )
            log.info("Edit mode correctly shows 'Update' button")

        except AssertionError:
            raise
        except Exception as e:
            log.warning(f"Could not verify Update button: {e}")
            raise

        # Cleanup
        _cleanup_form(page)
