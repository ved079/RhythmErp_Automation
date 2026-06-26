import sys
import os
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.vehicle_master.vehicle_master_page import VehicleMasterPage
from pages.common_settings.modules.vehicle_master.data.vehicle_master_data import (
    generate_valid_vehicle_data,
    generate_vehicle_name,
)


@pytest.mark.ui
class TestVehicleMasterUI:
    """UI tests for Vehicle Master (replaces test_vehicle_master_validation.py)."""

    def _cleanup(self, page):
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.hard_refresh()

    # --- STANDALONE TESTS ---

    def test_empty_form_shows_error(self, logged_in_driver):
        """Submit empty form — must show Validation Failed alert."""
        page = VehicleMasterPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Empty form must trigger Validation Failed alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_missing_name_rejected(self, logged_in_driver):
        """Submit without name — must show validation error."""
        page = VehicleMasterPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = generate_valid_vehicle_data()
            data["name"] = ""
            page.fill_vehicle_form(data)
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Missing name must trigger validation alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_missing_price_rejected(self, logged_in_driver):
        """Submit without vehicle price — must show validation error."""
        page = VehicleMasterPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = generate_valid_vehicle_data()
            data["price"] = ""
            page.fill_vehicle_form(data)
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Missing price must trigger validation alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_special_chars_in_name_rejected(self, logged_in_driver):
        """Vehicle name with special characters must be rejected."""
        page = VehicleMasterPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = generate_valid_vehicle_data()
            data["name"] = "TRUCK@#$!"
            page.fill_vehicle_form(data)
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Special chars in vehicle name must trigger validation alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_cancel_discards_form(self, logged_in_driver):
        """Fill form then cancel — record must NOT be created."""
        page = VehicleMasterPage(logged_in_driver)
        try:
            page.navigate_to_page()
            data = generate_valid_vehicle_data()
            page.open_add_form()
            page.fill_vehicle_form(data)
            page.cancel()
            page.hard_refresh()
            assert not page.is_vehicle_in_table(data["name"]), \
                "Cancelled record must not appear in table"
        finally:
            self._cleanup(page)

    def test_successful_create_and_search(self, logged_in_driver):
        """Create a vehicle and verify it appears in search results."""
        page = VehicleMasterPage(logged_in_driver)
        try:
            page.navigate_to_page()
            data = generate_valid_vehicle_data()
            result = page.create_vehicle(data)
            assert result.get("status") == "PASSED", \
                f"Create failed: {result.get('error')}"
            page.search_vehicle(data["name"])
            assert page.is_vehicle_in_table(data["name"]), \
                "Created vehicle must appear in search results"
        finally:
            self._cleanup(page)

    def test_description_is_optional(self, logged_in_driver):
        """Create vehicle without description — must succeed."""
        page = VehicleMasterPage(logged_in_driver)
        try:
            page.navigate_to_page()
            data = generate_valid_vehicle_data()
            data["description"] = ""
            result = page.create_vehicle(data)
            assert result.get("status") == "PASSED", \
                f"Create without description must succeed: {result.get('error')}"
        finally:
            self._cleanup(page)

    # --- TESTS USING shared_vehicle_master ---

    def test_view_mode_readonly(self, logged_in_driver, shared_vehicle_master):
        """View mode must have all fields disabled."""
        page = VehicleMasterPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_vehicle(shared_vehicle_master["name"])
            page.click_view_button(vehicle_name=shared_vehicle_master["name"])
            assert page.is_view_mode(), "All fields must be disabled in view mode"
            page.force_close_form_popup()
        finally:
            self._cleanup(page)

    def test_history_opens_after_create(self, logged_in_driver, shared_vehicle_master):
        """History popup must open for a created vehicle record."""
        page = VehicleMasterPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_vehicle(shared_vehicle_master["name"])
            page.click_history_button(vehicle_name=shared_vehicle_master["name"])
            history_els = page.driver.find_elements("css selector", "app-dynamic-history")
            assert len(history_els) > 0, "History component must be present after click"
        finally:
            self._cleanup(page)

    def test_edit_mode_loads_prepopulated(self, logged_in_driver, shared_vehicle_master):
        """Open edit mode — form must open with existing name prepopulated."""
        page = VehicleMasterPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_vehicle(shared_vehicle_master["name"])
            page.click_edit_button(vehicle_name=shared_vehicle_master["name"])
            assert page.is_edit_mode(), "Form must open in edit mode"
            # Verify name is prepopulated
            actual_name = page.driver.execute_script(
                "var inp = document.querySelector(\"input[name='Name']\");"
                "return inp ? inp.value : '';"
            )
            assert shared_vehicle_master["name"] in actual_name, \
                f"Vehicle name must be prepopulated in edit mode. Got: '{actual_name}'"
        finally:
            self._cleanup(page)
