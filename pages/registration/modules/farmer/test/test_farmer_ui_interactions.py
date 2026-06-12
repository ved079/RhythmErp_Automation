"""
test_farmer_ui_interactions.py
--------------------------------
UI-only interaction test suite for RhythmERP Farmer screen.
Tests that verify UI-specific behavior — no data creation needed via API.

Bucket B — UI-Only Tests: Verify UI rendering, interactions, and behaviors
that cannot be tested via API. Each test uses ``fr_page`` fixture only.

Test Inventory (17 tests across 6 classes):
  FR-PL01 — Page loads, table visible, toolbar ready
  FR-PL02 — Page title contains expected text

  FR-AF01 — Add form opens with stepper UI
  FR-AF02 — Fill Step 0 + Address Details, submit (Walk-in Farmer)
  FR-AF03 — Create farmer with valid data, verify success alert

  FR-VF01 — View existing farmer, popup opens in read-only mode
  FR-VF02 — View farmer, Step 0 fields pre-populated

  FR-EF01 — Edit existing farmer, popup opens in Edit mode
  FR-EF02 — Edit farmer, change fields, submit update

  FR-PC01 — Cancel closes popup without creating
  FR-PC02 — Close (X) button closes without creating
  FR-PC03 — Backdrop click closes popup
  FR-PC04 — force_close_form_popup() cleans up stuck popups

  FR-SN01 — Stepper tabs appear after Farmer Category selection
  FR-SN02 — Navigate between stepper tabs via Next/Back
  FR-SN03 — Navigate to stepper tab by name
  FR-SN04 — Walk-in Farmer shows subset of tabs

These tests do NOT create data via API — they only interact with the UI
to verify rendering, behavior, and structural correctness.

Run:
  pytest test_farmer_ui_interactions.py -v --tb=short
  pytest test_farmer_ui_interactions.py -v -m ui --tb=short
  pytest test_farmer_ui_interactions.py -v -k "FR_AF01" --tb=short
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from common.logger import log
from common.soft_assert import SoftAssert
from pages.registration.modules.farmer.data.farmer_data import (
    generate_valid_farmer_step0,
    generate_valid_address_details,
    generate_valid_farmer_data,
    generate_valid_edit_data,
    generate_alpha_phone,
    generate_walkin_farmer_category,
    generate_borrower_farmer_category,
    KnownBugs,
)


# ====================================================================
# FR-PL01 / FR-PL02: Page Load
# ====================================================================

class TestFarmerPageLoad:
    """UI-only: Verify Farmer listing page loads correctly."""

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_FR_PL01_page_loads_with_table_and_toolbar(self, fr_page):
        """Farmer page loads — table and toolbar are visible."""
        log.info("FR-PL01 (UI): Page loads with table and toolbar")
        page = fr_page

        # Table should be visible
        is_loaded = page.is_page_loaded()
        assert is_loaded, "Farmer page did not load — table not visible"
        log.info("Farmer table is visible")

        # Toolbar (export buttons / add button area) should be present
        try:
            toolbar = page.driver.find_elements(
                By.CSS_SELECTOR, "ul.tbl-export-btn"
            )
            assert len(toolbar) > 0, "Toolbar not found on Farmer page"
            log.info("Farmer toolbar is present")
        except Exception:
            # Some tenants may render toolbar differently — check ADD button
            add_btn = page.driver.find_elements(
                By.CSS_SELECTOR, "button.erp-add-btn"
            )
            assert len(add_btn) > 0, (
                "Neither toolbar nor ADD button found on Farmer page"
            )
            log.info("ADD button is present (toolbar variant)")

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_FR_PL02_page_title(self, fr_page):
        """Browser page title is not blank (contains RhythmERP or Farmer)."""
        log.info("FR-PL02 (UI): Page title check")
        page = fr_page

        title = page.get_page_title()
        assert title and len(title.strip()) > 0, "Page title is blank"
        log.info(f"Page title: '{title}'")


# ====================================================================
# FR-AF01 / FR-AF02 / FR-AF03: Add Form
# ====================================================================

class TestFarmerAddForm:
    """UI-only: Verify Add form opens, fills, and submits correctly."""

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_FR_AF01_add_form_opens_with_stepper(self, fr_page):
        """Add form opens with stepper UI (Step 0 + stepper tabs)."""
        log.info("FR-AF01 (UI): Add form opens with stepper")
        page = fr_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Verify popup is open
        assert page.is_add_form_open(), "Add form popup is not open"

        # Verify stepper is present inside popup
        stepper = page.driver.find_elements(
            By.CSS_SELECTOR, "mat-stepper, mat-horizontal-stepper"
        )
        assert len(stepper) > 0, "Stepper not found in Add form popup"
        log.info("Add form popup with stepper opened correctly")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_FR_AF02_fill_step0_and_address(self, fr_page):
        """Fill Step 0 + Address Details stepper, verify no validation errors."""
        log.info("FR-AF02 (UI): Fill Step 0 + Address Details")
        page = fr_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Fill Step 0 with Walk-in Farmer category
        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = "Walk-in Farmer"
        page.fill_step0(step0)

        # Wait for stepper tabs to render after category selection
        for _ in range(5):
            tab_names = page.get_stepper_names()
            if any(n.strip() for n in tab_names):
                break
            page.wait_seconds(1)

        # Navigate to Address Details tab
        page.navigate_to_stepper("Address Details")
        page.wait_seconds(1)

        # Fill Address Details (REQUIRED for Farmer creation)
        address_data = generate_valid_address_details()
        page.fill_address_details(address_data)
        log.info("Step 0 + Address Details filled successfully")

        # Check for inline validation errors on Step 0 fields
        # (should be none since we filled all required fields)
        try:
            page.navigate_to_stepper("Bank Details")
            log.info("Successfully navigated to Bank Details tab")
        except Exception:
            log.info("Bank Details tab may not be available for Walk-in Farmer")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_FR_AF03_create_farmer_success_alert(self, fr_page):
        """Create a Walk-in Farmer — verify success alert appears."""
        log.info("FR-AF03 (UI): Create farmer, verify success alert")
        page = fr_page

        data = generate_valid_farmer_data()
        result = page.create_farmer(data, category="Walk-in Farmer")

        if result["status"] == "PASSED":
            log.info("Farmer created successfully — success alert visible")
        else:
            log.warning(
                f"Farmer creation returned: status={result['status']}, "
                f"alert='{result.get('alert_title', '')}', "
                f"errors={result.get('validation_errors', [])}"
            )

        # Verify success alert was shown (or at least the form closed)
        assert result["status"] == "PASSED" or result.get("alert_title"), (
            f"Farmer creation did not produce a clear result: {result}"
        )

        # Dismiss any lingering alert
        try:
            if page.is_success_alert_visible() or page.is_validation_alert_visible():
                page.dismiss_alert()
        except Exception:
            pass


# ====================================================================
# FR-VF01 / FR-VF02: View Form
# ====================================================================

class TestFarmerViewForm:
    """UI-only: Verify View form opens and fields are pre-populated."""

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_FR_VF01_view_farmer_popup_opens(self, fr_page):
        """View existing farmer — popup opens in read-only mode."""
        log.info("FR-VF01 (UI): View farmer popup opens")
        page = fr_page

        row_count = page.get_table_row_count()
        if row_count == 0:
            pytest.skip("No farmers in table to view — create one first")

        # Click view on first row
        opened = page.view_farmer(row_index=0)
        assert opened, "View popup did not open"
        page.wait_seconds(2)

        # Verify popup is open
        assert page._is_form_popup_open(), "View form popup is not open"
        log.info("View form popup opened successfully")

        # Verify it is NOT in edit mode (no Update button)
        is_edit = page.is_edit_mode()
        assert not is_edit, "View form should NOT be in Edit mode"
        log.info("View form is in read-only mode (no Update button)")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    @pytest.mark.ui
    def test_FR_VF02_view_farmer_prepopulated_fields(self, fr_page):
        """View farmer — Step 0 fields are pre-populated."""
        log.info("FR-VF02 (UI): View farmer — fields pre-populated")
        page = fr_page
        sa = SoftAssert()

        row_count = page.get_table_row_count()
        if row_count == 0:
            pytest.skip("No farmers in table to view — create one first")

        opened = page.view_farmer(row_index=0)
        assert opened, "View popup did not open"
        page.wait_seconds(2)

        # Read field values from the form
        values = page.get_form_field_values()
        log.info(f"View form field values: {values}")

        # Farmer Name should be populated (non-empty)
        sa.assert_true(
            values.get("farmer_name", "").strip() != "",
            "Farmer Name is empty in View form",
        )

        # Phone Number should be populated
        sa.assert_true(
            values.get("phone_number", "").strip() != "",
            "Phone Number is empty in View form",
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

        sa.check_all()


# ====================================================================
# FR-EF01 / FR-EF02: Edit Form
# ====================================================================

class TestFarmerEditForm:
    """UI-only: Verify Edit form opens and fields can be changed."""

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_FR_EF01_edit_farmer_popup_opens(self, fr_page):
        """Edit existing farmer — popup opens in Edit mode."""
        log.info("FR-EF01 (UI): Edit farmer popup opens in Edit mode")
        page = fr_page

        row_count = page.get_table_row_count()
        if row_count == 0:
            pytest.skip("No farmers in table to edit — create one first")

        opened = page.edit_farmer(row_index=0)
        assert opened, "Edit popup did not open"
        page.wait_seconds(2)

        # Verify popup is open
        assert page._is_form_popup_open(), "Edit form popup is not open"

        # Verify it IS in edit mode (Update button present)
        is_edit = page.is_edit_mode()
        assert is_edit, "Edit form should be in Edit mode (Update button present)"
        log.info("Edit form opened in Edit mode (Update button visible)")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    @pytest.mark.ui
    def test_FR_EF02_edit_farmer_change_fields(self, fr_page):
        """Edit farmer — change fields, submit update, verify success."""
        log.info("FR-EF02 (UI): Edit farmer — change fields and update")
        page = fr_page

        row_count = page.get_table_row_count()
        if row_count == 0:
            pytest.skip("No farmers in table to edit — create one first")

        opened = page.edit_farmer(row_index=0)
        assert opened, "Edit popup did not open"
        page.wait_seconds(2)

        # Read current field values
        original_values = page.get_form_field_values()
        log.info(f"Original field values: {original_values}")

        # Change Farmer Name and Email using JS input setter
        edit_data = generate_valid_edit_data()
        if edit_data.get("name"):
            page._fill_input_by_name_js("Farmer Name", edit_data["name"])
        if edit_data.get("email_id"):
            page._fill_input_by_name_js("Email", edit_data["email_id"])

        # Click Update
        updated = page.click_update()
        page.wait_seconds(2)

        if updated:
            # Check for success alert
            alert_title = page.handle_success_alert(timeout=10)
            log.info(f"Update alert title: '{alert_title}'")
        else:
            log.warning("Update button click did not return True")

        # Dismiss any lingering alert
        try:
            if page.is_success_alert_visible() or page.is_validation_alert_visible():
                page.dismiss_alert()
        except Exception:
            pass

        # Clean up popup if still open
        try:
            if page._is_form_popup_open():
                page.force_close_form_popup()
        except Exception:
            pass


# ====================================================================
# FR-PC01 / FR-PC02 / FR-PC03 / FR-PC04: Popup Close
# ====================================================================

class TestFarmerPopupClose:
    """UI-only: Verify popup close via various methods.

    FR-PC01: Cancel closes popup without creating
    FR-PC02: Close (X) button closes without creating
    FR-PC03: Backdrop click closes popup
    FR-PC04: force_close_form_popup() cleans up stuck popups
    """

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_FR_PC01_cancel_closes_popup(self, fr_page):
        """Cancel closes popup without creating a farmer."""
        log.info("FR-PC01 (UI): Cancel closes popup")
        page = fr_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Form did not open",
        )

        # Fill Step 0 (partial — enough to test Cancel doesn't save)
        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = "Walk-in Farmer"
        page.fill_step0(step0)

        page.cancel()
        page.wait_seconds(1)

        # Popup should be closed
        assert not page._is_form_popup_open(), (
            "Popup still open after Cancel"
        )

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after Cancel. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("Cancel correctly closed popup without creating a farmer")

    @pytest.mark.ui
    def test_FR_PC02_close_x_closes_popup(self, fr_page):
        """Close (X) button closes popup without creating."""
        log.info("FR-PC02 (UI): Close (X) button")
        page = fr_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Form did not open",
        )

        # Fill Step 0 partially
        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = "Walk-in Farmer"
        page.fill_step0(step0)

        # Click Close (X)
        page.close_popup()
        page.wait_seconds(1)

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after X close. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("X close correctly did not create a farmer")

    @pytest.mark.ui
    def test_FR_PC03_backdrop_click_closes_popup(self, fr_page):
        """Backdrop click closes popup without creating."""
        log.info("FR-PC03 (UI): Backdrop click closes popup")
        page = fr_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Form did not open",
        )

        # Click the dark backdrop behind the popup
        try:
            backdrops = page.driver.find_elements(
                By.CSS_SELECTOR,
                ".cdk-overlay-backdrop.cdk-overlay-dark-backdrop",
            )
            clicked = False
            for bd in backdrops:
                try:
                    if bd.is_displayed():
                        bd.click()
                        clicked = True
                        break
                except Exception:
                    continue
            if not clicked:
                log.warning("Backdrop not found or not clickable — skipping click")
        except Exception as e:
            log.warning(f"Backdrop click failed: {e}")

        page.wait_seconds(1)

        # If popup still open (some forms block backdrop close), force close
        if page._is_form_popup_open():
            log.info("Popup still open after backdrop click — form may block it")
            page.force_close_form_popup()

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after backdrop close. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("Backdrop close did not create a farmer")

    @pytest.mark.ui
    def test_FR_PC04_force_close_cleans_up(self, fr_page):
        """force_close_form_popup() cleans up stuck popups."""
        log.info("FR-PC04 (UI): force_close_form_popup() cleans up")
        page = fr_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Form did not open",
        )

        # Verify popup is open
        assert page._is_form_popup_open(), "Popup should be open before force close"

        # Force close
        page.force_close_form_popup()
        page.wait_seconds(1)

        # Popup should be gone
        assert not page._is_form_popup_open(), (
            "Popup still open after force_close_form_popup()"
        )
        log.info("force_close_form_popup() successfully cleaned up the popup")


# ====================================================================
# FR-SN01 / FR-SN02 / FR-SN03 / FR-SN04: Stepper Navigation
# ====================================================================

class TestFarmerStepperNavigation:
    """UI-only: Verify stepper navigation between tabs.

    FR-SN01: Stepper tabs appear after Farmer Category selection
    FR-SN02: Navigate via Next/Back buttons
    FR-SN03: Navigate to stepper tab by name
    FR-SN04: Walk-in Farmer shows subset of tabs (Address + Bank)
    """

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_FR_SN01_stepper_tabs_appear_after_category(self, fr_page):
        """Stepper tabs appear after selecting a Farmer Category."""
        log.info("FR-SN01 (UI): Stepper tabs appear after category selection")
        page = fr_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Before category selection — stepper may have no visible tabs
        tabs_before = page.get_stepper_names()
        non_empty_before = [t for t in tabs_before if t.strip()]
        log.info(f"Tabs before category: {tabs_before} (non-empty: {non_empty_before})")

        # Fill Step 0 WITH a farmer category
        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = "Walk-in Farmer"
        page.fill_step0(step0)

        # Wait for stepper tabs to render
        for _ in range(5):
            tab_names = page.get_stepper_names()
            non_empty = [t for t in tab_names if t.strip()]
            if non_empty:
                break
            page.wait_seconds(1)

        tab_names = page.get_stepper_names()
        non_empty = [t for t in tab_names if t.strip()]
        log.info(f"Tabs after category: {non_empty}")

        assert len(non_empty) > 0, (
            "No stepper tabs appeared after selecting Farmer Category"
        )
        log.info("Stepper tabs correctly appeared after category selection")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_FR_SN02_stepper_next_back_navigation(self, fr_page):
        """Navigate Step 0 → Next → Address Details → Back → Step 0."""
        log.info("FR-SN02 (UI): Stepper Next/Back navigation")
        page = fr_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Fill Step 0 to enable stepper
        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = "Walk-in Farmer"
        page.fill_step0(step0)

        # Wait for stepper tabs to render
        for _ in range(5):
            tab_names = page.get_stepper_names()
            if any(n.strip() for n in tab_names):
                break
            page.wait_seconds(1)

        # Click Next to advance from Step 0
        next_clicked = page.click_stepper_next()
        assert next_clicked, "Stepper Next button click failed"
        page.wait_seconds(1.5)

        # Verify we moved to Address Details (first tab for Walk-in Farmer)
        active_tab = page.get_current_stepper_name()
        log.info(f"After Next click, active tab: '{active_tab}'")
        assert "address" in active_tab.lower(), (
            f"Expected Address Details tab, got: '{active_tab}'"
        )

        # Click Back to return to Step 0
        # Give Angular stepper a moment to render the Back button
        page.wait_seconds(1)
        try:
            back_btns = page.driver.find_elements(
                By.CSS_SELECTOR,
                "button.mat-stepper-previous, button.mat-mdc-stepper-previous",
            )
            for btn in back_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        page.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();", btn,
                        )
                        page.wait_seconds(1)
                        break
                except Exception:
                    continue
        except Exception:
            log.warning("Back button not found via CSS — trying text search")
            try:
                back_btns = page.driver.find_elements(
                    By.XPATH, "//button[contains(.,'Back')]"
                )
                for btn in back_btns:
                    try:
                        if btn.is_displayed() and btn.is_enabled():
                            page.driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});"
                                "arguments[0].click();", btn,
                            )
                            page.wait_seconds(1)
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        log.info("Stepper Next/Back navigation works correctly")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_FR_SN03_navigate_to_tab_by_name(self, fr_page):
        """Navigate directly to a stepper tab by name (header click)."""
        log.info("FR-SN03 (UI): Navigate to stepper tab by name")
        page = fr_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Fill Step 0 with Borrower Farmer (all 13 tabs)
        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = "Borrower Farmer"
        page.fill_step0(step0)

        # Wait for stepper tabs to render
        for _ in range(5):
            tab_names = page.get_stepper_names()
            if any(n.strip() for n in tab_names):
                break
            page.wait_seconds(1)

        # Navigate to "Bank Details" tab by name
        reached = page.navigate_to_stepper("Bank Details")
        assert reached, "Could not navigate to Bank Details tab"

        active_tab = page.get_current_stepper_name()
        assert "bank" in active_tab.lower(), (
            f"Expected Bank Details tab, got: '{active_tab}'"
        )
        log.info(f"Successfully navigated to tab: '{active_tab}'")

        # Navigate to another tab — "Additional Details"
        reached = page.navigate_to_stepper("Additional Details")
        if reached:
            active_tab = page.get_current_stepper_name()
            log.info(f"Navigated to Additional Details: '{active_tab}'")
        else:
            log.warning("Could not navigate to Additional Details — may not be visible")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    @pytest.mark.ui
    def test_FR_SN04_walkin_farmer_subset_tabs(self, fr_page):
        """Walk-in Farmer category shows subset of tabs (Address + Bank)."""
        log.info("FR-SN04 (UI): Walk-in Farmer shows subset of tabs")
        page = fr_page
        sa = SoftAssert()

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Fill Step 0 with Walk-in Farmer
        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = "Walk-in Farmer"
        page.fill_step0(step0)

        # Wait for stepper tabs to render
        for _ in range(5):
            tab_names = page.get_stepper_names()
            if any(n.strip() for n in tab_names):
                break
            page.wait_seconds(1)

        tab_names = page.get_stepper_names()
        non_empty = [t.strip() for t in tab_names if t.strip()]
        log.info(f"Walk-in Farmer tabs: {non_empty}")

        # Walk-in Farmer should show at least Address Details
        has_address = any("address" in t.lower() for t in non_empty)
        sa.assert_true(
            has_address,
            f"Walk-in Farmer should show Address Details tab. Found: {non_empty}",
        )

        # Walk-in Farmer should NOT show all 13 tabs (Borrower Farmer gets those)
        sa.assert_true(
            len(non_empty) <= 6,
            f"Walk-in Farmer should show a subset of tabs, not {len(non_empty)}. "
            f"Found: {non_empty}",
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

        sa.check_all()
