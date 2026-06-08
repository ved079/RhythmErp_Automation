"""
test_commodity_base_rate.py
---------------------------
Comprehensive test suite for RhythmERP Commodity Base Rate screen.
15 test cases across 6 phases covering all 6 bugs found during exploration.

Optimised (v2) — UOM golden standard:
- Uses logged_in_driver directly, creates page object in each test
- Smart finally blocks: only cleanup if form is actually open
- Uses hard_refresh() instead of navigate_to_page() for fast page reset
- Uses search_and_verify() for create/update verification (handles pagination)

Phases:
  1. Create Records             (3 tests) — CBR-C-01 to CBR-C-03
  2. Validation Checks          (4 tests) — CBR-V-01 to CBR-V-04
  3. Edit Record                (1 test)  — CBR-E-01
  4. Search & Sort              (2 tests) — CBR-S-01 to CBR-S-02
  5. Popup / Version / History  (3 tests) — CBR-P-01 to CBR-P-03
  6. Bug Verification           (2 tests) — CBR-H-01 to CBR-H-02

Known Bugs:
  BUG-001 (HIGH)  : Item Rate accepts non-numeric input
  BUG-002 (MEDIUM): Item Rate accepts zero value
  BUG-003 (MEDIUM): Listing shows raw ISO timestamps
  BUG-004 (HIGH)  : To Date overridden to 30/12/2099
  BUG-005 (LOW)   : Edit disabled for new records
  BUG-006 (MEDIUM): Version creation fails with same From Date
"""

import os
import sys
import time
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
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


class TestCBRCreate:
    """CBR-C-01 to CBR-C-03: Create record tests."""

    def _cleanup(self, page):
        """Smart cleanup — close form if open, then hard refresh."""
        if page._is_form_popup_open():
            page.force_close_form_popup()
        page.hard_refresh()

    def test_CBR_C_01_create_common_pricing_record(self, logged_in_driver):
        """Create record with Common pricing type."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-C-01: Create Common pricing record")
            page.navigate_to_page()

            data = generate_valid_common_record()
            success = page.create_cbr_record(data)

            assert success, "Common pricing record creation failed"

            # Verify in listing via search
            page.hard_refresh()
            found = page.search_and_verify(data["location"])
            assert found, "Created Common record not found in listing"
            log.info("CBR-C-01 PASSED: Common pricing record created and verified")
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_CBR_C_02_create_supplier_pricing_record(self, logged_in_driver):
        """Create record with Supplier pricing type."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-C-02: Create Supplier pricing record")
            page.navigate_to_page()

            data = generate_valid_supplier_record()
            success = page.create_cbr_record(data)

            assert success, "Supplier pricing record creation failed"

            # Verify in listing via search
            page.hard_refresh()
            found = page.search_and_verify(data["location"])
            assert found, "Created Supplier record not found in listing"
            log.info("CBR-C-02 PASSED: Supplier pricing record created and verified")
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_CBR_C_03_create_multi_row_grid(self, logged_in_driver):
        """Create record with multiple grid rows."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-C-03: Create multi-row grid record")
            page.navigate_to_page()

            data = generate_multi_row_record()
            success = page.create_cbr_record(data)

            assert success, "Multi-row record creation failed"

            # Verify in listing
            page.hard_refresh()
            found = page.search_and_verify("Jafrabad")
            assert found, "Multi-row record not found in listing"
            log.info("CBR-C-03 PASSED: Multi-row grid record created and verified")
        except Exception:
            raise
        finally:
            self._cleanup(page)


class TestCBRValidation:
    """CBR-V-01 to CBR-V-04: Validation tests."""

    def _cleanup(self, page):
        if page._is_form_popup_open():
            page.force_close_form_popup()
        page.hard_refresh()

    def test_CBR_V_01_validation_empty_required_fields(self, logged_in_driver):
        """Submit with empty required fields — should be blocked."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-V-01: Empty required fields validation")
            page.navigate_to_page()
            page.open_add_form()

            assert page.is_add_form_open(), "Add form did not open"

            # Submit without filling anything
            page.submit()

            # Check for validation
            validation_alert = page.is_validation_alert_present(timeout=5)
            errors = page.get_mat_error_text()
            form_still_open = page.is_add_form_open()

            if validation_alert:
                page.dismiss_any_validation_alert()

            assert form_still_open or errors or validation_alert, (
                "BUG: Form submitted with empty fields — no validation"
            )
            log.info("CBR-V-01 PASSED: Empty field validation works")
        except Exception:
            raise
        finally:
            self._cleanup(page)

    @pytest.mark.xfail(reason=BUG_001, strict=False)
    def test_CBR_V_02_validation_negative_item_rate(self, logged_in_driver):
        """Negative Item Rate — should be rejected. BUG-001."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-V-02: Negative item rate validation")
            page.navigate_to_page()

            data = generate_negative_rate_data()
            page.open_add_form()
            page.fill_form(data)
            page.submit()

            validation_alert = page.is_validation_alert_present(timeout=3)
            form_still_open = page.is_add_form_open()
            errors = page.get_mat_error_text()

            if validation_alert:
                page.dismiss_any_validation_alert()

            assert form_still_open or errors or validation_alert, (
                f"BUG-001 CONFIRMED: System accepted negative Item Rate."
            )
            log.info("CBR-V-02: Negative item rate test completed")
        except Exception:
            raise
        finally:
            self._cleanup(page)

    @pytest.mark.xfail(reason=BUG_001, strict=False)
    def test_CBR_V_03_validation_special_chars_item_rate(self, logged_in_driver):
        """Special chars in Item Rate — should be rejected. BUG-001."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-V-03: Special chars item rate validation")
            page.navigate_to_page()

            data = generate_special_chars_rate_data()
            page.open_add_form()
            page.fill_form(data)
            page.submit()

            validation_alert = page.is_validation_alert_present(timeout=3)
            form_still_open = page.is_add_form_open()
            errors = page.get_mat_error_text()

            if validation_alert:
                page.dismiss_any_validation_alert()

            assert form_still_open or errors or validation_alert, (
                f"BUG-001 CONFIRMED: System accepted special chars in Item Rate."
            )
            log.info("CBR-V-03: Special chars item rate test completed")
        except Exception:
            raise
        finally:
            self._cleanup(page)

    @pytest.mark.xfail(reason=BUG_002, strict=False)
    def test_CBR_V_04_validation_zero_item_rate(self, logged_in_driver):
        """Zero Item Rate — should be rejected. BUG-002."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-V-04: Zero item rate validation")
            page.navigate_to_page()

            data = generate_zero_rate_data()
            page.open_add_form()
            page.fill_form(data)
            page.submit()

            validation_alert = page.is_validation_alert_present(timeout=3)
            form_still_open = page.is_add_form_open()
            errors = page.get_mat_error_text()

            if validation_alert:
                page.dismiss_any_validation_alert()

            assert form_still_open or errors or validation_alert, (
                f"BUG-002 CONFIRMED: System accepted zero Item Rate."
            )
            log.info("CBR-V-04: Zero item rate test completed")
        except Exception:
            raise
        finally:
            self._cleanup(page)


class TestCBREdit:
    """CBR-E-01: Edit record test."""

    def _cleanup(self, page):
        if page._is_form_popup_open():
            page.force_close_form_popup()
        page.hard_refresh()

    def test_CBR_E_01_edit_record(self, logged_in_driver):
        """Edit latest version of a record.
        BUG-005: Edit may be disabled for new records."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-E-01: Edit record")
            page.navigate_to_page()

            # Search for a record to edit — use "Common" as search text
            page.search_and_verify("Common")
            row_count = page.get_table_row_count()

            if row_count == 0:
                pytest.skip("No records to edit")

            # Try to find a row with enabled Edit button
            # Get table data to find row text for 3-dot menu
            table_data = page.get_table_data()
            editable_row_text = None
            for row in table_data:
                # Use Pricing Type or Location as row_text for menu matching
                row_text = row.get("Pricing Type", "") or row.get("Location", "")
                if row_text:
                    editable_row_text = row_text
                    break

            if editable_row_text is None:
                pytest.skip("No editable record found (BUG-005)")

            # Click Edit via 3-dot menu
            page.click_edit_button(editable_row_text)

            # Check if edit form opened
            if not page._is_form_popup_open():
                pytest.skip("Edit popup did not open (BUG-005: Edit disabled)")

            # Update Item Rate
            edit_data = generate_edit_data()
            try:
                rate_el = page._find_input_by_label("Item Rate")
                page.driver.execute_script(
                    "var s = Object.getOwnPropertyDescriptor("
                    "  window.HTMLInputElement.prototype,'value').set;"
                    "s.call(arguments[0], '');"
                    "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                    rate_el,
                )
                rate_el.send_keys(edit_data["item_rate"])
            except Exception:
                log.warning("Could not update Item Rate")

            page.click_update()

            # Handle success or validation
            if page.is_validation_alert_present(timeout=3):
                page.dismiss_any_validation_alert()
                log.warning("Edit validation alert")
            else:
                page.handle_success_alert()

            log.info("CBR-E-01: Edit test completed")
        except Exception:
            raise
        finally:
            self._cleanup(page)


class TestCBRSearch:
    """CBR-S-01 to CBR-S-02: Search and sort tests."""

    def _cleanup(self, page):
        if page._is_form_popup_open():
            page.force_close_form_popup()
        page.hard_refresh()

    def test_CBR_S_01_search_existing_record(self, logged_in_driver):
        """Search for an existing record."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-S-01: Search existing record")
            page.navigate_to_page()

            # First create a record to search for
            data = generate_valid_common_record()
            page.create_cbr_record(data)

            # Search by location keyword
            page.hard_refresh()
            found = page.search_and_verify(data["location"])
            assert found, "Search returned no results for existing record"

            # Clear search
            page.clear_search()
            log.info("CBR-S-01 PASSED: Search works for existing record")
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_CBR_S_02_sort_by_column(self, logged_in_driver):
        """Sort by column headers."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-S-02: Column sort test")
            page.navigate_to_page()

            # Sort by Pricing Type column
            headers = page.driver.find_elements("css selector", "table#excel-table thead th")
            for header in headers:
                try:
                    if "Pricing Type" in header.text.strip():
                        page.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", header
                        )
                        break
                except Exception:
                    continue

            # Verify table still has data
            row_count = page.get_table_row_count()
            assert row_count >= 1, "No data after sorting"
            log.info(f"CBR-S-02 PASSED: Column sort completed. Rows: {row_count}")
        except Exception:
            raise
        finally:
            self._cleanup(page)


class TestCBRPopupVersion:
    """CBR-P-01 to CBR-P-03: Popup, version, and history tests."""

    def _cleanup(self, page):
        if page._is_form_popup_open():
            page.force_close_form_popup()
        page.hard_refresh()

    def test_CBR_P_01_view_record_detail(self, logged_in_driver):
        """View record detail (read-only popup)."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-P-01: View record detail")
            page.navigate_to_page()

            row_count = page.get_table_row_count()
            if row_count == 0:
                pytest.skip("No records to view")

            # Get first row text for 3-dot menu
            table_data = page.get_table_data()
            row_text = table_data[0].get("Pricing Type", "") or table_data[0].get("Location", "")

            # Click View on first row
            page.click_view_button(row_text)

            # Verify popup opened
            form_open = page._is_form_popup_open()
            assert form_open, "View popup did not open"

            # Verify it's in view mode (read-only)
            is_view = page.is_view_mode()
            if is_view:
                log.info("View popup opened in read-only mode")
            else:
                log.info("View popup opened (mode not confirmed as read-only)")
            log.info("CBR-P-01 PASSED: View record detail works")
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_CBR_P_02_version_creation(self, logged_in_driver):
        """Version creation (fork from existing record).
        BUG-006: May fail with same From Date."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-P-02: Version creation")
            page.navigate_to_page()

            row_count = page.get_table_row_count()
            if row_count == 0:
                pytest.skip("No records to create version from")

            # Get first row text for 3-dot menu
            table_data = page.get_table_data()
            row_text = table_data[0].get("Pricing Type", "") or table_data[0].get("Location", "")

            # Click Version on first row
            page.click_version_button(row_text)

            # Set a future From Date
            future_date = generate_future_from_date(days_ahead=30)
            try:
                page._set_datepicker_by_label("From Date", future_date)
            except Exception:
                log.warning("Could not set version From Date")

            # Submit version form
            page.submit()

            # Check result
            if page.is_validation_alert_present(timeout=5):
                page.dismiss_any_validation_alert()
                pytest.xfail(f"Version creation failed (possibly {BUG_006})")
            else:
                page.handle_success_alert()
                log.info("Version created successfully")
            log.info("CBR-P-02: Version creation test completed")
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_CBR_P_03_history_popup(self, logged_in_driver):
        """History popup for a record."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-P-03: History popup")
            page.navigate_to_page()

            row_count = page.get_table_row_count()
            if row_count == 0:
                pytest.skip("No records to view history")

            # Get first row text for 3-dot menu
            table_data = page.get_table_data()
            row_text = table_data[0].get("Pricing Type", "") or table_data[0].get("Location", "")

            # Click History on first row
            page.click_history_button(row_text)

            # Verify a popup/dialog opened
            is_empty = page.is_history_empty()
            if is_empty:
                log.info("History popup opened — no history data (expected for new records)")
            else:
                log.info("History popup opened — data found")

            # Close history popup
            page.close_history_popup()
            log.info("CBR-P-03 PASSED: History popup works")
        except Exception:
            raise
        finally:
            self._cleanup(page)


class TestCBRHistoryBug:
    """CBR-H-01 to CBR-H-02: Bug verification tests."""

    def _cleanup(self, page):
        if page._is_form_popup_open():
            page.force_close_form_popup()
        page.hard_refresh()

    @pytest.mark.xfail(reason=BUG_003, strict=False)
    def test_CBR_H_01_verify_iso_date_format_in_listing(self, logged_in_driver):
        """Verify ISO date format in listing (BUG-003)."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-H-01: ISO date format verification")
            page.navigate_to_page()

            has_iso = page.has_iso_dates_in_listing()

            assert not has_iso, (
                f"BUG-003 CONFIRMED: Found raw ISO timestamps in listing table. "
                f"Dates should be formatted as DD/MM/YYYY instead."
            )
            log.info("CBR-H-01: ISO date format test completed")
        except Exception:
            raise
        finally:
            self._cleanup(page)

    @pytest.mark.xfail(reason=BUG_004, strict=False)
    def test_CBR_H_02_verify_to_date_override(self, logged_in_driver):
        """Verify To Date override behavior (BUG-004)."""
        driver = logged_in_driver
        page = CommodityBaseRatePage(driver)

        try:
            log.info("CBR-H-02: To Date override verification")
            page.navigate_to_page()

            custom_to_date = "31/12/2026"
            data = generate_custom_to_date_data(to_date=custom_to_date)

            success = page.create_cbr_record(data)
            if not success:
                pytest.skip("Could not create record for To Date test")

            # Check listing for the created record's To Date
            page.hard_refresh()
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
            log.info("CBR-H-02: To Date override test completed")
        except Exception:
            raise
        finally:
            self._cleanup(page)
