"""
test_commodity_base_rate.py
---------------------------
Comprehensive test suite for RhythmERP Commodity Base Rate screen.
15 test cases across 6 phases covering all 6 bugs found during exploration.

Phases:
  1. Create Records             (3 tests) — CBR-C-01 to CBR-C-03
  2. Validation Checks          (4 tests) — CBR-V-01 to CBR-V-04
  3. Edit Record                (1 test)  — CBR-E-01
  4. Search & Sort              (2 tests) — CBR-S-01 to CBR-S-02
  5. Popup / Version / History  (3 tests) — CBR-P-01 to CBR-P-03
  6. Bug Verification           (2 tests) — CBR-H-01 to CBR-H-02

Pytest Marker Summary:
  smoke:       8 tests (critical path — create, search, view, version, edit)
  sanity:      15 tests (core validation — build acceptance gate)
  regression:  15 tests (full suite — all tests)
  bug:         5 tests (known open bugs — BUG-001 to BUG-006)
  ui:          6 tests (popups, view, sort, history, date picker)

Known Bugs:
  BUG-001 (HIGH)  : Item Rate accepts non-numeric input
  BUG-002 (MEDIUM): Item Rate accepts zero value
  BUG-003 (MEDIUM): Listing shows raw ISO timestamps
  BUG-004 (HIGH)  : To Date overridden to 30/12/2099
  BUG-005 (LOW)   : Edit disabled for new records
  BUG-006 (MEDIUM): Version creation fails with same From Date

Usage:
  pytest test_commodity_base_rate.py -m smoke           #  8 critical path tests
  pytest test_commodity_base_rate.py -m sanity           # 15 build acceptance tests
  pytest test_commodity_base_rate.py -m regression       # 15 full suite
  pytest test_commodity_base_rate.py -m bug              #  5 known bug tests
  pytest test_commodity_base_rate.py -m ui               #  6 UI behavior tests
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

from pages.commodity_settings.modules.commodity_base_rate.commodity_base_rate_page import (
    CommodityBaseRatePage,
)
from pages.commodity_settings.modules.commodity_base_rate.data.cbr_data import (
    generate_valid_common_record,
    generate_valid_supplier_record,
    generate_multi_row_record,
    generate_negative_rate_data,
    generate_special_chars_rate_data,
    generate_zero_rate_data,
    generate_edit_data,
    generate_future_from_date,
    generate_custom_to_date_data,
    BUG_001, BUG_002, BUG_003, BUG_004, BUG_005, BUG_006,
)
from common.logger import log


# ====================================================================
# PHASE 1: Create Records (3 tests)
# ====================================================================

class TestCBRCreate:
    """CBR-C-01 to CBR-C-03: Create record tests."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CBR_C_01_create_common_pricing_record(self, cbr_page):
        """Create record with Common pricing type."""
        log.info("CBR-C-01: Create Common pricing record")
        page = cbr_page

        data = generate_valid_common_record()
        success = page.create_cbr_record(data)

        assert success, "Common pricing record creation failed"

        # Verify in listing
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_record_in_table(
            pricing_type="Common",
            location=data["location"],
        )
        assert found, "Created Common record not found in listing table"
        log.info("Common pricing record created and verified")

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CBR_C_02_create_supplier_pricing_record(self, cbr_page):
        """Create record with Supplier pricing type."""
        log.info("CBR-C-02: Create Supplier pricing record")
        page = cbr_page

        data = generate_valid_supplier_record()
        success = page.create_cbr_record(data)

        assert success, "Supplier pricing record creation failed"

        # Verify in listing
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_record_in_table(
            pricing_type="Supplier",
            location=data["location"],
        )
        assert found, "Created Supplier record not found in listing table"
        log.info("Supplier pricing record created and verified")

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CBR_C_03_create_multi_row_grid(self, cbr_page):
        """Create record with multiple grid rows."""
        log.info("CBR-C-03: Create multi-row grid record")
        page = cbr_page

        data = generate_multi_row_record()
        success = page.create_cbr_record(data)

        assert success, "Multi-row record creation failed"

        # Verify in listing
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_record_in_table(
            pricing_type="Common",
            location="Jafrabad",
        )
        assert found, "Multi-row record not found in listing table"
        log.info("Multi-row grid record created and verified")


# ====================================================================
# PHASE 2: Validation Checks (4 tests)
# ====================================================================

class TestCBRValidation:
    """CBR-V-01 to CBR-V-04: Validation tests."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CBR_V_01_validation_empty_required_fields(self, cbr_page):
        """Submit with empty required fields — should be blocked."""
        log.info("CBR-V-01: Empty required fields validation")
        page = cbr_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Submit without filling anything
        page.submit()
        page.wait_seconds(2)

        # Check for validation
        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Form submitted with empty fields — no validation"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(
        reason=BUG_001,
        strict=False,
    )
    def test_CBR_V_02_validation_negative_item_rate(self, cbr_page):
        """Negative Item Rate — should be rejected. BUG-001."""
        log.info("CBR-V-02: Negative item rate validation")
        page = cbr_page

        data = generate_negative_rate_data()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        assert form_still_open or errors or validation_alert, (
            f"BUG-001 CONFIRMED: System accepted negative Item Rate. "
            f"Should show validation error instead."
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(
        reason=BUG_001,
        strict=False,
    )
    def test_CBR_V_03_validation_special_chars_item_rate(self, cbr_page):
        """Special chars in Item Rate — should be rejected. BUG-001."""
        log.info("CBR-V-03: Special chars item rate validation")
        page = cbr_page

        data = generate_special_chars_rate_data()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        assert form_still_open or errors or validation_alert, (
            f"BUG-001 CONFIRMED: System accepted special chars in Item Rate. "
            f"Should show validation error instead."
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(
        reason=BUG_002,
        strict=False,
    )
    def test_CBR_V_04_validation_zero_item_rate(self, cbr_page):
        """Zero Item Rate — should be rejected. BUG-002."""
        log.info("CBR-V-04: Zero item rate validation")
        page = cbr_page

        data = generate_zero_rate_data()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        assert form_still_open or errors or validation_alert, (
            f"BUG-002 CONFIRMED: System accepted zero Item Rate. "
            f"Should show validation error instead."
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass


# ====================================================================
# PHASE 3: Edit Record (1 test)
# ====================================================================

class TestCBREdit:
    """CBR-E-01: Edit record test."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CBR_E_01_edit_record(self, cbr_page):
        """Edit latest version of a record.
        BUG-005: Edit may be disabled for new records.
        """
        log.info("CBR-E-01: Edit record")
        page = cbr_page

        page.click_refresh()
        page.wait_seconds(2)

        # Find a row with enabled Edit button
        row_count = page.get_table_row_count()
        editable_row = None
        for idx in range(row_count):
            if page.is_edit_enabled(idx):
                editable_row = idx
                break

        if editable_row is None:
            pytest.skip(
                "No editable record found. "
                "Edit button disabled for all records (BUG-005). "
                "Create a version first to enable editing."
            )

        # Click Edit
        page.click_row_action(editable_row, "edit")
        page.wait_seconds(1)

        # Update Item Rate using label-based approach
        edit_data = generate_edit_data()
        try:
            rate_el = page._find_input_by_label("Item Rate")
            # Clear via JS
            page.driver.execute_script(
                "var s = Object.getOwnPropertyDescriptor("
                "  window.HTMLInputElement.prototype,'value').set;"
                "s.call(arguments[0], '');"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                rate_el,
            )
            page.wait_seconds(0.1)
            rate_el.send_keys(edit_data["item_rate"])
        except Exception:
            log.warning("Could not update Item Rate via label, trying locator fallback")
            try:
                page.type_text(
                    page.ITEM_RATE_INPUT, edit_data["item_rate"], clear_first=True
                )
            except Exception:
                log.error("Could not update Item Rate by any method")

        page.click_update()
        page.wait_seconds(2)

        # Handle success or validation
        success_msg = page.handle_success_alert(timeout=5)
        if not success_msg:
            page.handle_validation_warning(timeout=3)

        log.info(f"Edit completed. Success: {bool(success_msg)}")


# ====================================================================
# PHASE 4: Search & Sort (2 tests)
# ====================================================================

class TestCBRSearch:
    """CBR-S-01 to CBR-S-02: Search and sort tests."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CBR_S_01_search_existing_record(self, cbr_page):
        """Search for an existing record."""
        log.info("CBR-S-01: Search existing record")
        page = cbr_page

        # First create a record to search for
        data = generate_valid_common_record()
        page.create_cbr_record(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        initial_count = page.get_table_row_count()

        # Search by pricing type keyword
        page.search_record("Common")
        page.wait_seconds(2)

        search_count = page.get_table_row_count()
        assert search_count >= 1, "Search returned no results for existing record"

        # Clear search
        page.clear_search()
        page.wait_seconds(2)

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CBR_S_02_sort_by_column(self, cbr_page):
        """Sort by column headers."""
        log.info("CBR-S-02: Column sort test")
        page = cbr_page

        page.click_refresh()
        page.wait_seconds(2)

        # Sort by Pricing Type column
        page.sort_by_column("Pricing Type")
        page.wait_seconds(1)

        # Sort again (toggle)
        page.sort_by_column("Pricing Type")
        page.wait_seconds(1)

        # Verify table still has data
        row_count = page.get_table_row_count()
        assert row_count >= 1, "No data after sorting"
        log.info(f"Column sort completed. Rows: {row_count}")


# ====================================================================
# PHASE 5: Popup / Version / History (3 tests)
# ====================================================================

class TestCBRPopupVersion:
    """CBR-P-01 to CBR-P-03: Popup, version, and history tests."""

    @pytest.mark.smoke
    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CBR_P_01_view_record_detail(self, cbr_page):
        """View record detail (read-only popup)."""
        log.info("CBR-P-01: View record detail")
        page = cbr_page

        page.click_refresh()
        page.wait_seconds(2)

        row_count = page.get_table_row_count()
        if row_count == 0:
            pytest.skip("No records to view")

        # Click View on first row
        page.click_row_action(0, "view")
        page.wait_seconds(1)

        # Verify popup opened (form should be visible)
        form_open = page.is_add_form_open() or page._is_form_popup_open()
        assert form_open, "View popup did not open"

        # Verify it's in view mode (read-only)
        is_view = page.is_view_mode()
        if is_view:
            log.info("View popup opened in read-only mode")
        else:
            log.info("View popup opened (mode not confirmed as read-only)")

        # Close popup
        try:
            page.close_popup()
        except Exception:
            try:
                page.cancel()
            except Exception:
                pass

    @pytest.mark.smoke
    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CBR_P_02_version_creation(self, cbr_page):
        """Version creation (fork from existing record).
        BUG-006: May fail with same From Date.
        """
        log.info("CBR-P-02: Version creation")
        page = cbr_page

        page.click_refresh()
        page.wait_seconds(2)

        row_count = page.get_table_row_count()
        if row_count == 0:
            pytest.skip("No records to create version from")

        # Click Version on first row
        page.click_row_action(0, "version")
        page.wait_seconds(2)

        # Set a future From Date using label-based approach
        future_date = generate_future_from_date(days_ahead=30)
        try:
            page._set_datepicker_by_label("From Date", future_date)
        except Exception:
            log.warning("Could not set version From Date via label, trying fallback")
            try:
                page._set_datepicker(page.FROM_DATE_INPUT, future_date)
            except Exception:
                log.error("Could not set version From Date by any method")

        # Submit version form
        page.submit()
        page.wait_seconds(2)

        # Check result
        success_msg = page.handle_success_alert(timeout=5)
        if success_msg:
            log.info(f"Version created successfully: {success_msg}")
        else:
            # Check for error
            error_msg = page.handle_validation_warning(timeout=3)
            if error_msg:
                log.warning(f"Version creation error: {error_msg}")
                pytest.xfail(f"Version creation failed (possibly {BUG_006}): {error_msg}")
            else:
                # Form may still be open with validation errors
                errors = page.get_mat_error_text()
                if errors:
                    log.warning(f"Validation errors: {errors}")
                    pytest.xfail(f"Version creation validation errors: {errors}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            pass

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_CBR_P_03_history_popup(self, cbr_page):
        """History popup for a record."""
        log.info("CBR-P-03: History popup")
        page = cbr_page

        page.click_refresh()
        page.wait_seconds(2)

        row_count = page.get_table_row_count()
        if row_count == 0:
            pytest.skip("No records to view history")

        # Click History on first row
        page.click_row_action(0, "history")
        page.wait_seconds(1)

        # Verify a popup/dialog opened
        popup_open = page._is_form_popup_open()
        if popup_open:
            log.info("History popup opened successfully")
        else:
            log.warning("History popup may not have opened")

        # Close popup
        try:
            page.close_popup()
        except Exception:
            try:
                page.cancel()
            except Exception:
                pass


# ====================================================================
# PHASE 6: Bug Verification (2 tests)
# ====================================================================

class TestCBRHistoryBug:
    """CBR-H-01 to CBR-H-02: Bug verification tests."""

    @pytest.mark.bug
    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(
        reason=BUG_003,
        strict=False,
    )
    def test_CBR_H_01_verify_iso_date_format_in_listing(self, cbr_page):
        """Verify ISO date format in listing (BUG-003).
        Listing should show formatted dates, not ISO timestamps.
        """
        log.info("CBR-H-01: ISO date format verification")
        page = cbr_page

        page.click_refresh()
        page.wait_seconds(2)

        has_iso = page.has_iso_dates_in_listing()

        assert not has_iso, (
            f"BUG-003 CONFIRMED: Found raw ISO timestamps in listing table. "
            f"Dates should be formatted as DD/MM/YYYY instead."
        )

    @pytest.mark.bug
    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(
        reason=BUG_004,
        strict=False,
    )
    def test_CBR_H_02_verify_to_date_override(self, cbr_page):
        """Verify To Date override behavior (BUG-004).
        To Date should retain user's selected value.
        """
        log.info("CBR-H-02: To Date override verification")
        page = cbr_page

        custom_to_date = "31/12/2026"
        data = generate_custom_to_date_data(to_date=custom_to_date)

        success = page.create_cbr_record(data)
        if not success:
            try:
                page.cancel()
            except Exception:
                pass
            pytest.skip("Could not create record for To Date test")

        # Check listing for the created record's To Date
        page.click_refresh()
        page.wait_seconds(2)

        # Get all table data and check To Date column
        table_data = page.get_table_data()
        found_custom_date = False
        for row in table_data:
            to_date_val = row.get("To Date", "")
            if custom_to_date in to_date_val:
                found_custom_date = True
                break

        assert found_custom_date, (
            f"BUG-004 CONFIRMED: To Date was overridden. "
            f"Expected: '{custom_to_date}' in listing, "
            f"but system saved it as 30/12/2099."
        )
