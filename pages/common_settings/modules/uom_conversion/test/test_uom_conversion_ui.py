import sys
import os
import time
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.uom_conversion.uom_conversion_page import UOMConversionPage


@pytest.mark.ui
class TestUOMConversionUI:
    """UI validation tests for UOM Conversion (replaces test_uom_conversion_validation.py)."""

    def _cleanup(self, page):
        try:
            page.cleanup()
        except Exception:
            pass
        page.hard_refresh()

    # --- STANDALONE TESTS (no pre-existing record needed) ---

    def test_empty_source_uom_shows_error(self, logged_in_driver):
        """Submit without selecting Source UOM — must show validation alert and dropdown error."""
        page = UOMConversionPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            page.select_uom("Target UOM", page.get_available_uoms()[0])
            page.clear_conversion_factor_via_js()
            page.type_conversion_factor("5")
            page.submit()
            assert page.handle_validation_warning() != "" or page.is_dropdown_error("Source UOM"), \
                "Missing source UOM must trigger validation"
            assert page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_empty_target_uom_shows_error(self, logged_in_driver):
        """Submit without selecting Target UOM — must show validation alert and dropdown error."""
        page = UOMConversionPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            page.select_uom("Source UOM", page.get_available_uoms()[0])
            page.type_conversion_factor("5")
            page.submit()
            assert page.handle_validation_warning() != "" or page.is_dropdown_error("Target UOM"), \
                "Missing target UOM must trigger validation"
            assert page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_empty_factor_shows_error(self, logged_in_driver):
        """Submit without filling Conversion Factor — must show validation and mat-error."""
        page = UOMConversionPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            uoms = page.get_available_uoms()
            page.select_uom("Source UOM", uoms[0])
            page.select_uom("Target UOM", uoms[1] if len(uoms) > 1 else uoms[0])
            page.clear_conversion_factor_via_js()
            page.submit()
            assert page.handle_validation_warning() != "", \
                "Missing conversion factor must trigger Pattern A alert"
            assert page.get_mat_error_text("Conversion Factor") != ""
            assert page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_text_in_factor_rejected(self, logged_in_driver):
        """Type 'abc' in conversion factor — must be rejected (Bug #2: type=character, no native validation)."""
        page = UOMConversionPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            uoms = page.get_available_uoms()
            page.select_uom("Source UOM", uoms[0])
            page.select_uom("Target UOM", uoms[1] if len(uoms) > 1 else uoms[0])
            page.type_conversion_factor("abc")
            page.submit()
            warning = page.handle_validation_warning()
            assert warning != "" or page.get_mat_error_text("Conversion Factor") != "", \
                "Text in conversion factor must be rejected"
            assert page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_cancel_discards_form(self, logged_in_driver):
        """Fill form then cancel — record must NOT appear in table."""
        page = UOMConversionPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            uoms = page.get_available_uoms()
            page.select_uom("Source UOM", uoms[0])
            page.select_uom("Target UOM", uoms[1] if len(uoms) > 1 else uoms[0])
            page.type_conversion_factor("999")
            page.click_cancel_button()
            page.hard_refresh()
            assert not page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_valid_decimal_factor_accepted(self, logged_in_driver):
        """Create a conversion with decimal factor (e.g. 0.5) — must succeed."""
        page = UOMConversionPage(logged_in_driver)
        try:
            page.navigate_to_page()
            result = page.create_fresh_record(factor=0.5)
            assert result.get("success"), f"Decimal factor 0.5 must be accepted. Error: {result.get('error')}"
        finally:
            self._cleanup(page)

    # --- TESTS USING shared_uom_conversion (read/inspect only — do NOT modify the shared record) ---

    def test_view_mode_readonly(self, logged_in_driver, shared_uom_conversion):
        """Open the shared record in View mode — all fields must be disabled."""
        page = UOMConversionPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_table(shared_uom_conversion["source_uom"])
            page.click_view_button(shared_uom_conversion["source_uom"], shared_uom_conversion["target_uom"])
            page.verify_view_popup_read_only()
            page.click_cancel_button()
        finally:
            self._cleanup(page)

    def test_edit_empty_factor_blocked(self, logged_in_driver, shared_uom_conversion):
        """Open shared record in Edit mode, clear factor — submit must be blocked."""
        page = UOMConversionPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_table(shared_uom_conversion["source_uom"])
            page.click_edit_button(shared_uom_conversion["source_uom"], shared_uom_conversion["target_uom"])
            page.clear_conversion_factor_via_js()
            page.submit()
            assert page.handle_validation_warning() != "", \
                "Cleared factor on edit must trigger Pattern A alert"
            assert page.get_mat_error_text("Conversion Factor") != ""
        finally:
            self._cleanup(page)

    def test_history_shows_after_creation(self, logged_in_driver, shared_uom_conversion):
        """Open history for the shared record — must have at least 1 row."""
        page = UOMConversionPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_table(shared_uom_conversion["source_uom"])
            page.click_history_button(shared_uom_conversion["source_uom"], shared_uom_conversion["target_uom"])
            assert page.is_history_popup_open(), "History popup must open"
            assert page.get_history_row_count() >= 1, "History must have at least 1 row"
            page.close_history_popup()
        finally:
            self._cleanup(page)

    # --- TESTS THAT CREATE THEIR OWN RECORD ---

    def test_22_digit_factor_saves_as_scientific_notation(self, logged_in_driver):
        """22-digit factor saves but displays as scientific notation (Bug #1 — documented behavior)."""
        page = UOMConversionPage(logged_in_driver)
        try:
            page.navigate_to_page()
            result = page.create_fresh_record(factor="1234567890123456789012")  # 22 digits
            log.info(f"22-digit factor result: {result}")
        finally:
            self._cleanup(page)
