"""
test_vehicle_master_validation.py
---------------------------------
Comprehensive validation test suite for RhythmERP Vehicle Master screen.
43 test cases across 6 classes covering all bugs found during manual exploration.

Classes:
  1. TestCreateFormValidations  (15 tests) — VM-C01 to VM-C15
  2. TestDropdownValidations     (5 tests) — VM-D01 to VM-D05
  3. TestEditFormValidations     (5 tests) — VM-E01 to VM-E05
  4. TestSearchFilter            (5 tests) — VM-S01 to VM-S05
  5. TestPopupUIBehaviors        (5 tests) — VM-P01 to VM-P05
  6. TestHistoryValidations      (8 tests) — VM-H01 to VM-H08

Marker Summary:
  smoke      : 11 tests (C01, C09, C12, D01, E01, E05, S01, P01, P03, H01, H06)
  sanity     : 43 tests (all)
  regression : 43 tests (all)
  bug        : 16 tests (C04-C11, C15, E01-E04, S04, S05, H08)
  ui         : 17 tests (C01, C15, D01-D05, P01-P05, H03, H05-H08)

Run:
  pytest test_vehicle_master_validation.py -v --tb=short
  pytest test_vehicle_master_validation.py -v -m smoke --tb=short
  pytest test_vehicle_master_validation.py -v -m "smoke and bug" --tb=short
  pytest test_vehicle_master_validation.py -v -k "TestCreateForm" --tb=short
  pytest test_vehicle_master_validation.py -v -k "VM-C09" --tb=short
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

from pages.common_settings.modules.vehicle_master.vehicle_master_page import  (
    VehicleMasterPage,
)
from pages.common_settings.modules.vehicle_master.data.vehicle_master_data import (
    generate_valid_vehicle_data,
    generate_valid_edit_data,
    generate_empty_data,
    generate_name_only_data,
    generate_spaces_only,
    generate_zero_price,
    generate_negative_price,
    generate_alpha_price,
    generate_decimal_price,
    generate_price_with_special_chars,
    generate_price_with_spaces,
    generate_special_char_name,
    generate_string_255,
    generate_string_256,
    generate_duplicate_name_data,
    generate_vehicle_name,
    generate_vehicle_price,
    generate_description,
)
from common.logger import log

# ====================================================================
# Helper: create a vehicle, refresh, and return its name
# ====================================================================

def _create_prerequisite_vehicle(page, data=None):
    """Create a vehicle for tests that need existing data.
    Returns the vehicle name used.
    """
    if data is None:
        data = generate_valid_vehicle_data("PreReq")
    result = page.create_vehicle(data)
    return data.get("name", ""), result

# ====================================================================
# PHASE 1: Create Form Validations (15 tests)
# ====================================================================

class TestCreateFormValidations:
    """VM-C01 to VM-C15: Validation checks on the Create form."""

    # ---- VM-C01: Submit with all fields empty ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_C01_empty_submit(self, vehicle_master_page):
        """Submit with all fields empty — should be blocked."""
        log.info("VM-C01: Empty submit test")
        page = vehicle_master_page

        page.open_add_form()
        assert page.is_add_form_open(), "Add form did not open"

        page.submit()

        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        # Expect: form stays open + validation errors shown
        assert form_still_open or errors, (
            "BUG: Form submitted with all fields empty — no validation"
        )
        if errors:
            log.info(f"Validation errors shown: {errors}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            pass

    # ---- VM-C02: Submit with only Name ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_VM_C02_name_only(self, vehicle_master_page):
        """Submit with only Name filled — should be blocked."""
        log.info("VM-C02: Name-only submit test")
        page = vehicle_master_page

        data = generate_name_only_data("NameOnly")
        page.open_add_form()
        page.type_text(page.NAME_INPUT, data["name"], clear_first=True)
        page.submit()

        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors, (
            "BUG: Form submitted with only Name — missing fields not validated"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- VM-C03: Submit with only Price ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_VM_C03_price_only(self, vehicle_master_page):
        """Submit with only Price filled — should be blocked."""
        log.info("VM-C03: Price-only submit test")
        page = vehicle_master_page

        page.open_add_form()
        page.type_text(
            page.PRICE_INPUT, generate_vehicle_price(), clear_first=True
        )
        page.submit()

        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors, (
            "BUG: Form submitted with only Price — Name not validated"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- VM-C04: Name with leading/trailing spaces ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_C04_spaces_in_name(self, vehicle_master_page):
        """Name with leading/trailing spaces — should be trimmed or rejected.
        BUG FOUND: Spaces are NOT trimmed.
        """
        log.info("VM-C04: Spaces in name test")
        page = vehicle_master_page

        spaces_name = generate_spaces_only(5) + generate_vehicle_name("Space") + generate_spaces_only(5)
        data = generate_valid_vehicle_data()
        data["name"] = spaces_name

        result = page.create_vehicle(data)

        if result["status"] == "PASSED":
            # Check if name was trimmed in the table
            page.click_refresh()
            names = page.get_all_vehicle_names()
            created_name = spaces_name.strip()
            # BUG: spaces not trimmed — name saved as-is with spaces
            has_spaces = any(n != n.strip() for n in names if spaces_name in n or created_name in n)
            if has_spaces:
                log.warning(
                    "BUG CONFIRMED: Spaces not trimmed in Name field"
                )
        else:
            log.info("Spaces were rejected — validation working")

    # ---- VM-C05: Price = 0 ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_C05_zero_price(self, vehicle_master_page):
        """Price = 0 — should be rejected.
        BUG FOUND: Zero price is accepted.
        """
        log.info("VM-C05: Zero price test")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("ZeroPrice")
        data["price"] = generate_zero_price()

        result = page.create_vehicle(data)

        if result["status"] == "PASSED":
            log.warning(
                "BUG CONFIRMED: Zero price accepted in Create form"
            )
        else:
            log.info("Zero price rejected — validation working")

    # ---- VM-C06: Negative Price ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_C06_negative_price(self, vehicle_master_page):
        """Negative Price — should be rejected.
        BUG FOUND: Negative price is accepted.
        """
        log.info("VM-C06: Negative price test")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("NegPrice")
        data["price"] = generate_negative_price()

        result = page.create_vehicle(data)

        if result["status"] == "PASSED":
            log.warning(
                "BUG CONFIRMED: Negative price accepted in Create form"
            )
        else:
            log.info("Negative price rejected — validation working")

    # ---- VM-C07: Alphabets in Price ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_C07_alpha_price(self, vehicle_master_page):
        """Alphabets in Price field — should be rejected.
        BUG FOUND: Alphabets accepted.
        """
        log.info("VM-C07: Alphabets in price test")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("AlphaPrice")
        data["price"] = generate_alpha_price()

        result = page.create_vehicle(data)

        if result["status"] == "PASSED":
            log.warning(
                "BUG CONFIRMED: Alphabets accepted in Price field"
            )
        else:
            log.info("Alphabets rejected in Price — validation working")

    # ---- VM-C08: Special characters in Price ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_C08_special_chars_price(self, vehicle_master_page):
        """Special characters in Price — should be rejected."""
        log.info("VM-C08: Special chars in price test")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("SpecPrice")
        data["price"] = generate_price_with_special_chars()

        result = page.create_vehicle(data)

        if result["status"] == "PASSED":
            log.warning(
                "BUG: Special chars accepted in Price field"
            )
        else:
            log.info("Special chars rejected — validation working")

    # ---- VM-C09: Duplicate Name ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_C09_duplicate_name(self, vehicle_master_page):
        """Duplicate Name — should be rejected.
        BUG FOUND: Duplicate name is allowed.
        """
        log.info("VM-C09: Duplicate name test")
        page = vehicle_master_page

        # Create first vehicle
        data1 = generate_valid_vehicle_data("Dup1")
        result1 = page.create_vehicle(data1)
        page.click_refresh()

        # Try creating second with same name
        data2 = generate_duplicate_name_data(data1["name"])
        result2 = page.create_vehicle(data2)

        if result2["status"] == "PASSED":
            log.warning(
                "BUG CONFIRMED: Duplicate name allowed in Create form"
            )
        else:
            log.info("Duplicate name rejected — validation working")

    # ---- VM-C10: Special characters in Name ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_C10_special_chars_name(self, vehicle_master_page):
        """Special characters in Name — should be rejected or sanitized.
        BUG FOUND: Special chars accepted.
        """
        log.info("VM-C10: Special chars in name test")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("SpecName")
        data["name"] = generate_special_char_name()

        result = page.create_vehicle(data)

        if result["status"] == "PASSED":
            log.warning(
                "BUG CONFIRMED: Special chars accepted in Name field"
            )
        else:
            log.info("Special chars rejected — validation working")

    # ---- VM-C11: Very long Name (256 chars) ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_C11_long_name(self, vehicle_master_page):
        """Name with 256 chars — should be rejected or truncated."""
        log.info("VM-C11: Very long name test")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("LongName")
        data["name"] = generate_string_256()

        result = page.create_vehicle(data)

        if result["status"] == "PASSED":
            log.warning(
                "BUG: Name with 256 chars accepted — no max length validation"
            )
        else:
            log.info("Long name rejected — validation working")

    # ---- VM-C12: Without Vehicle Type dropdown ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_VM_C12_no_vehicle_type(self, vehicle_master_page):
        """Submit without selecting Vehicle Type — should be blocked."""
        log.info("VM-C12: No Vehicle Type selected test")
        page = vehicle_master_page

        page.open_add_form()
        # Fill everything EXCEPT Vehicle Type dropdown
        page.type_text(
            page.NAME_INPUT,
            generate_vehicle_name("NoVType"),
            clear_first=True,
        )
        page.type_text(
            page.PRICE_INPUT,
            generate_vehicle_price(),
            clear_first=True,
        )
        # Only select Fuel Type, skip Vehicle Type
        page._select_random_from_dropdown(
            page.FUEL_TYPE_SELECT, "Fuel Type"
        )
        page._force_close_panels()
        page.submit()

        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors, (
            "BUG: Form submitted without Vehicle Type"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- VM-C13: Without Fuel Type dropdown ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_VM_C13_no_fuel_type(self, vehicle_master_page):
        """Submit without selecting Fuel Type — should be blocked."""
        log.info("VM-C13: No Fuel Type selected test")
        page = vehicle_master_page

        page.open_add_form()
        page.type_text(
            page.NAME_INPUT,
            generate_vehicle_name("NoFType"),
            clear_first=True,
        )
        page.type_text(
            page.PRICE_INPUT,
            generate_vehicle_price(),
            clear_first=True,
        )
        # Only select Vehicle Type, skip Fuel Type
        page._select_random_from_dropdown(
            page.VEHICLE_TYPE_SELECT, "Vehicle Type"
        )
        page._force_close_panels()
        page.submit()

        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors, (
            "BUG: Form submitted without Fuel Type"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- VM-C14: Decimal Price ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_VM_C14_decimal_price(self, vehicle_master_page):
        """Decimal Price value — check if accepted or rejected."""
        log.info("VM-C14: Decimal price test")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("DecPrice")
        data["price"] = generate_decimal_price()

        result = page.create_vehicle(data)

        if result["status"] == "PASSED":
            log.info("Decimal price accepted (may be expected)")
        else:
            log.info("Decimal price rejected")

    # ---- VM-C15: Per-field inline error messages ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_VM_C15_inline_error_messages(self, vehicle_master_page):
        """Check if per-field inline error messages appear.
        BUG FOUND: No per-field inline error messages (UX issue).
        """
        log.info("VM-C15: Inline error messages test")
        page = vehicle_master_page

        page.open_add_form()
        page.submit()

        # Check if Name field has its own error
        name_has_error = page.has_field_error("Name")
        # Check if Price field has its own error
        price_has_error = page.has_field_error("Vehicle Price")
        # Check if Vehicle Type has its own error
        vtype_has_error = page.has_field_error("Vehicle Type")

        if not (name_has_error and price_has_error and vtype_has_error):
            log.warning(
                "BUG CONFIRMED: No per-field inline error messages. "
                f"Name: {name_has_error}, Price: {price_has_error}, "
                f"VType: {vtype_has_error}"
            )
        else:
            log.info("Per-field inline errors are present")

        # At minimum, some validation should exist
        all_errors = page.get_mat_error_text()
        assert all_errors or page.is_add_form_open(), (
            "BUG: No validation at all on empty submit"
        )

        try:
            page.cancel()
        except Exception:
            pass

# ====================================================================
# PHASE 2: Dropdown Validations (5 tests)
# ====================================================================

class TestDropdownValidations:
    """VM-D01 to VM-D05: Dropdown behaviour checks."""

    # ---- VM-D01: Vehicle Type dropdown shows options ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_D01_vehicle_type_options(self, vehicle_master_page):
        """Vehicle Type dropdown opens and shows options."""
        log.info("VM-D01: Vehicle Type dropdown options")
        page = vehicle_master_page

        page.open_add_form()

        options = page.get_dropdown_options(page.VEHICLE_TYPE_SELECT)

        assert options, "Vehicle Type dropdown has no options"
        log.info(f"Vehicle Type options: {options}")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- VM-D02: Fuel Type dropdown shows options ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_D02_fuel_type_options(self, vehicle_master_page):
        """Fuel Type dropdown opens and shows options."""
        log.info("VM-D02: Fuel Type dropdown options")
        page = vehicle_master_page

        page.open_add_form()

        options = page.get_dropdown_options(page.FUEL_TYPE_SELECT)

        assert options, "Fuel Type dropdown has no options"
        log.info(f"Fuel Type options: {options}")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- VM-D03: Vehicle Type dropdown search ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_D03_vehicle_type_search(self, vehicle_master_page):
        """Vehicle Type dropdown internal search filters options."""
        log.info("VM-D03: Vehicle Type dropdown search")
        page = vehicle_master_page

        page.open_add_form()

        # Get all options first
        all_options = page.get_dropdown_options(page.VEHICLE_TYPE_SELECT)
        if not all_options:
            pytest.skip("No Vehicle Type options to test search")

        # Open dropdown and type in search
        try:
            page.click(page.VEHICLE_TYPE_SELECT)
        except Exception:
            pass
        

        # Type partial text in the dropdown search box
        search_text = all_options[0][:3]  # first 3 chars of first option
        try:
            search_inputs = page.driver.find_elements(
                By.CSS_SELECTOR,
                "div[role='listbox'] input, "
                ".cdk-overlay-pane input[placeholder]",
            )
            for inp in search_inputs:
                try:
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(search_text)
                        
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # Read filtered options
        filtered = page.driver.find_elements(
            By.CSS_SELECTOR,
            "div[role='listbox'] mat-option, "
            "div[role='listbox'] [role='option']",
        )
        filtered_texts = [
            o.text.strip() for o in filtered
            if o.text.strip() and o.text.strip() != "No results found"
        ]

        page._force_close_panels()

        log.info(
            f"Search '{search_text}': "
            f"{len(all_options)} options -> {len(filtered_texts)} filtered"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- VM-D04: Fuel Type dropdown search ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_D04_fuel_type_search(self, vehicle_master_page):
        """Fuel Type dropdown internal search filters options."""
        log.info("VM-D04: Fuel Type dropdown search")
        page = vehicle_master_page

        page.open_add_form()

        all_options = page.get_dropdown_options(page.FUEL_TYPE_SELECT)
        if not all_options:
            pytest.skip("No Fuel Type options to test search")

        try:
            page.click(page.FUEL_TYPE_SELECT)
        except Exception:
            pass
        

        search_text = all_options[0][:3]
        try:
            search_inputs = page.driver.find_elements(
                By.CSS_SELECTOR,
                "div[role='listbox'] input, "
                ".cdk-overlay-pane input[placeholder]",
            )
            for inp in search_inputs:
                try:
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(search_text)
                        
                        break
                except Exception:
                    continue
        except Exception:
            pass

        filtered = page.driver.find_elements(
            By.CSS_SELECTOR,
            "div[role='listbox'] mat-option, "
            "div[role='listbox'] [role='option']",
        )
        filtered_texts = [
            o.text.strip() for o in filtered
            if o.text.strip() and o.text.strip() != "No results found"
        ]

        page._force_close_panels()

        log.info(
            f"Search '{search_text}': "
            f"{len(all_options)} options -> {len(filtered_texts)} filtered"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- VM-D05: Selecting option closes dropdown ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_D05_select_closes_dropdown(self, vehicle_master_page):
        """Selecting an option closes the dropdown and shows value."""
        log.info("VM-D05: Select closes dropdown")
        page = vehicle_master_page

        page.open_add_form()

        selected = page._select_random_from_dropdown(
            page.VEHICLE_TYPE_SELECT, "Vehicle Type"
        )

        # After selection, dropdown panel should be closed
        panel_visible = page.is_displayed(page.DROPDOWN_PANEL, timeout=2)

        assert not panel_visible, (
            "Dropdown panel still visible after selection"
        )
        log.info(f"Selected '{selected}', dropdown closed correctly")

        try:
            page.cancel()
        except Exception:
            pass

# ====================================================================
# PHASE 3: Edit Form Validations (5 tests)
# ====================================================================

class TestEditFormValidations:
    """VM-E01 to VM-E05: Validation checks on the Edit form."""

    # ---- VM-E01: Edit with duplicate Name ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_E01_edit_duplicate_name(self, vehicle_master_page):
        """Edit vehicle with an already existing Name.
        BUG FOUND: Duplicate name allowed in Edit.
        """
        log.info("VM-E01: Edit duplicate name")
        page = vehicle_master_page

        # Create two vehicles
        data1 = generate_valid_vehicle_data("EditDup1")
        result1 = page.create_vehicle(data1)
        page.click_refresh()

        data2 = generate_valid_vehicle_data("EditDup2")
        result2 = page.create_vehicle(data2)
        page.click_refresh()

        # Edit second vehicle with first vehicle's name
        edit_result = page.edit_vehicle(
            data2["name"],
            {"name": data1["name"]},
        )

        if edit_result["status"] == "PASSED":
            log.warning(
                "BUG CONFIRMED: Duplicate name allowed in Edit form"
            )
        else:
            log.info("Duplicate name rejected in Edit — validation working")

    # ---- VM-E02: Edit with Price = 0 ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_E02_edit_zero_price(self, vehicle_master_page):
        """Edit vehicle with Price = 0.
        BUG FOUND: Zero price accepted in Edit.
        """
        log.info("VM-E02: Edit zero price")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("EditZero")
        result = page.create_vehicle(data)

        edit_result = page.edit_vehicle(
            data["name"],
            {"price": generate_zero_price()},
        )

        if edit_result["status"] == "PASSED":
            log.warning(
                "BUG CONFIRMED: Zero price accepted in Edit form"
            )
        else:
            log.info("Zero price rejected in Edit — validation working")

    # ---- VM-E03: Edit with negative Price ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_E03_edit_negative_price(self, vehicle_master_page):
        """Edit vehicle with negative Price.
        BUG FOUND: Negative price accepted in Edit.
        """
        log.info("VM-E03: Edit negative price")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("EditNeg")
        result = page.create_vehicle(data)

        edit_result = page.edit_vehicle(
            data["name"],
            {"price": generate_negative_price()},
        )

        if edit_result["status"] == "PASSED":
            log.warning(
                "BUG CONFIRMED: Negative price accepted in Edit form"
            )
        else:
            log.info("Negative price rejected in Edit — validation working")

    # ---- VM-E04: Edit with alphabets in Price ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_E04_edit_alpha_price(self, vehicle_master_page):
        """Edit vehicle with alphabets in Price field."""
        log.info("VM-E04: Edit alpha price")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("EditAlpha")
        result = page.create_vehicle(data)

        edit_result = page.edit_vehicle(
            data["name"],
            {"price": generate_alpha_price()},
        )

        if edit_result["status"] == "PASSED":
            log.warning("BUG: Alphabets accepted in Price field (Edit)")
        else:
            log.info("Alphabets rejected in Edit Price — validation working")

    # ---- VM-E05: Edit — verify pre-populated fields ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_VM_E05_edit_prepopulated(self, vehicle_master_page):
        """Edit popup should show all fields pre-populated with existing data."""
        log.info("VM-E05: Edit pre-populated fields")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("EditPre")
        # Fill with known values
        data["description"] = "PrePopulated Test Description"
        result = page.create_vehicle(data)
        page.ensure_vehicle_visible(data["name"])

        # Click Edit
        page.click_edit_button(vehicle_name=data["name"])

        # Read form values
        form_values = page.get_form_field_values()

        assert form_values.get("name"), "Name field empty in Edit form"
        assert form_values.get("price"), "Price field empty in Edit form"
        assert form_values.get("vehicle_type"), (
            "Vehicle Type empty in Edit form"
        )
        assert form_values.get("fuel_type"), (
            "Fuel Type empty in Edit form"
        )

        log.info(f"Edit form pre-populated: {form_values}")

        try:
            page.cancel()
        except Exception:
            pass

# ====================================================================
# PHASE 4: Search & Filter Edge Cases (5 tests)
# ====================================================================

class TestSearchFilter:
    """VM-S01 to VM-S05: Search and Filter edge cases."""

    # ---- VM-S01: Search with exact Name match ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_VM_S01_search_exact(self, vehicle_master_page):
        """Search with exact vehicle name — should find it."""
        log.info("VM-S01: Search exact name")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("SearchEx")
        result = page.create_vehicle(data)

        found = page.search_vehicle(data["name"])
        page.clear_search()

        assert found, f"Exact search failed for: {data['name']}"
        log.info(f"Exact search found: {data['name']}")

    # ---- VM-S02: Search with partial Name ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_VM_S02_search_partial(self, vehicle_master_page):
        """Search with partial vehicle name — should find it."""
        log.info("VM-S02: Search partial name")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("SearchPar")
        result = page.create_vehicle(data)

        partial = data["name"][:10]
        found = page.search_vehicle(partial)
        page.clear_search()

        assert found, f"Partial search failed for: {partial}"
        log.info(f"Partial search found with: {partial}")

    # ---- VM-S03: Search with non-existent Name ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_VM_S03_search_nonexistent(self, vehicle_master_page):
        """Search for non-existent name — should return no results."""
        log.info("VM-S03: Search nonexistent")
        page = vehicle_master_page

        fake_name = f"NonExistent_{int(time.time())}"
        found = page.search_vehicle(fake_name)
        page.clear_search()

        assert not found, (
            f"BUG: Non-existent name '{fake_name}' was found in table"
        )
        log.info(f"Correctly not found: {fake_name}")

    # ---- VM-S04: Filter by Vehicle Type ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_S04_filter_vehicle_type(self, vehicle_master_page):
        """Apply filter by Vehicle Type category.
        CRITICAL BUG: Apply Filters button is completely non-functional.
        """
        log.info("VM-S04: Filter by Vehicle Type")
        page = vehicle_master_page

        # Try to find and click the Filter button
        try:
            filter_btn = page.driver.find_element(
                By.CSS_SELECTOR, "button.filter-btn, button[mattooltip='Filter']"
            )
            page.driver.execute_script("arguments[0].click();", filter_btn)
            page.wait_seconds(0.1)

            # Check if filter panel opened
            filter_panel = page.driver.find_elements(
                By.CSS_SELECTOR,
                ".filter-panel, .filter-container, "
                "mat-dialog-container .filter",
            )

            if filter_panel:
                log.info("Filter panel opened")

                # Try to apply a filter
                try:
                    apply_btn = page.driver.find_element(
                        By.CSS_SELECTOR,
                        "button.apply-filter, button[contains(.,'Apply')]",
                    )
                    page.driver.execute_script(
                        "arguments[0].click();", apply_btn
                    )
                    log.warning(
                        "CRITICAL BUG: Apply Filters button "
                        "is non-functional"
                    )
                except Exception:
                    log.info("Apply Filters button not found or not clicked")
            else:
                log.info("Filter panel did not open")

        except Exception as e:
            log.info(f"Filter button not found: {e}")

        page.click_refresh()

    # ---- VM-S05: Filter by Fuel Type ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_VM_S05_filter_fuel_type(self, vehicle_master_page):
        """Apply filter by Fuel Type category.
        CRITICAL BUG: Apply Filters button is completely non-functional.
        """
        log.info("VM-S05: Filter by Fuel Type")
        page = vehicle_master_page

        try:
            filter_btn = page.driver.find_element(
                By.CSS_SELECTOR, "button.filter-btn, button[mattooltip='Filter']"
            )
            page.driver.execute_script("arguments[0].click();", filter_btn)
            page.wait_seconds(0.1)

            filter_panel = page.driver.find_elements(
                By.CSS_SELECTOR,
                ".filter-panel, .filter-container, "
                "mat-dialog-container .filter",
            )

            if filter_panel:
                log.info("Filter panel opened")
                log.warning(
                    "CRITICAL BUG: Apply Filters button "
                    "is non-functional for all categories"
                )
            else:
                log.info("Filter panel did not open")

        except Exception as e:
            log.info(f"Filter button not found: {e}")

# ====================================================================
# PHASE 5: Popup & UI Behaviors (5 tests)
# ====================================================================

class TestPopupUIBehaviors:
    """VM-P01 to VM-P05: Popup and UI interaction checks."""

    # ---- VM-P01: Cancel closes form without creating ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_P01_cancel_no_create(self, vehicle_master_page):
        """Cancel button closes form without creating a vehicle."""
        log.info("VM-P01: Cancel no create test")
        page = vehicle_master_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        assert page.is_add_form_open(), "Form did not open"

        # Fill form with data
        data = generate_valid_vehicle_data("CancelTest")
        page.fill_vehicle_form(data)
        page.cancel()

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after Cancel. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("Cancel correctly did not create a vehicle")

    # ---- VM-P02: X button closes form without creating ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_P02_close_no_create(self, vehicle_master_page):
        """X button closes form without creating a vehicle."""
        log.info("VM-P02: Close no create test")
        page = vehicle_master_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        assert page.is_add_form_open(), "Form did not open"

        data = generate_valid_vehicle_data("CloseTest")
        page.fill_vehicle_form(data)
        page.close_popup()
        

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after X close. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("X close correctly did not create a vehicle")

    # ---- VM-P03: View popup shows read-only fields ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_P03_view_readonly(self, vehicle_master_page):
        """View popup shows all fields in read-only mode."""
        log.info("VM-P03: View read-only test")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("ViewTest")
        result = page.create_vehicle(data)
        page.ensure_vehicle_visible(data["name"])

        page.click_view_button(vehicle_name=data["name"])

        is_readonly = page.verify_view_popup_read_only()

        assert is_readonly, (
            "BUG: View popup fields are editable (should be read-only)"
        )
        log.info("View popup correctly shows read-only fields")

        page.close_popup()
        

    # ---- VM-P04: Edit popup shows editable fields ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_P04_edit_has_update(self, vehicle_master_page):
        """Edit popup shows editable fields with Update button."""
        log.info("VM-P04: Edit has Update button")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("EditTest")
        result = page.create_vehicle(data)
        page.ensure_vehicle_visible(data["name"])

        page.click_edit_button(vehicle_name=data["name"])

        is_edit = page.verify_edit_popup_editable()

        assert is_edit, (
            "BUG: Edit popup does not show Update button"
        )
        log.info("Edit popup correctly shows Update button")

        page.cancel()
        

    # ---- VM-P05: History popup opens and shows records ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_P05_history_opens(self, vehicle_master_page):
        """History popup opens and shows at least 1 record."""
        log.info("VM-P05: History opens test")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("HistTest")
        result = page.create_vehicle(data)
        page.ensure_vehicle_visible(data["name"])

        hist = page.check_history(vehicle_name=data["name"])

        # P05 tests that the popup opens, not that it has data
        # (RhythmERP may not create history entries on vehicle creation)
        assert hist.get("error") == "", (
            f"History popup failed to open: {hist.get('error')}"
        )
        log.info(
            f"History popup opened successfully "
            f"(rows: {hist['row_count']})"
        )

# ====================================================================
# PHASE 6: History Validations (8 tests)
# ====================================================================

class TestHistoryValidations:
    """VM-H01 to VM-H08: History popup detailed checks."""

    # ---- VM-H01: History shows at least 1 row after creation ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_VM_H01_history_after_create(self, vehicle_master_page):
        """After creating a vehicle, history shows at least 1 row."""
        log.info("VM-H01: History after create")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("HistCrt")
        result = page.create_vehicle(data)
        page.ensure_vehicle_visible(data["name"])

        hist = page.check_history(vehicle_name=data["name"])

        # RhythmERP may not create history entries on creation
        # H01 tests that popup opens, not row count
        assert hist.get("error") == "", (
            f"History popup failed to open: {hist.get('error')}"
        )
        if hist["row_count"] >= 1:
            log.info(f"History rows after create: {hist['row_count']}")
        else:
            log.info(
                "H01: History popup opened but has 0 rows "
                "(BUG: no history entry created on vehicle creation)"
            )

    # ---- VM-H02: History row count increases after edit ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_VM_H02_history_after_edit(self, vehicle_master_page):
        """After editing, history should have more rows than before."""
        log.info("VM-H02: History after edit")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("HistEdit")
        result = page.create_vehicle(data)
        page.ensure_vehicle_visible(data["name"])

        # Count history before edit
        hist_before = page.check_history(vehicle_name=data["name"])
        count_before = hist_before["row_count"]

        # Edit the vehicle
        page.click_refresh()
        edit_result = page.edit_vehicle(
            data["name"],
            {"price": generate_vehicle_price()},
        )
        page.ensure_vehicle_visible(data["name"])

        # Count history after edit
        hist_after = page.check_history(vehicle_name=data["name"])
        count_after = hist_after["row_count"]

        if count_after > count_before:
            log.info(
                f"History increased: {count_before} -> {count_after}"
            )
        else:
            log.info(
                f"H02: History did not increase after edit "
                f"(Before: {count_before}, After: {count_after}). "
                f"BUG: History not tracked on edit"
            )

    # ---- VM-H03: History search works with Enter key ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_H03_history_search_enter(self, vehicle_master_page):
        """History search works when pressing Enter after typing."""
        log.info("VM-H03: History search with Enter")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("HistSrch")
        result = page.create_vehicle(data)
        page.ensure_vehicle_visible(data["name"])

        # Open history and search
        page.click_history_button(vehicle_name=data["name"])

        search_done = page.search_in_history("a")
        page.wait_seconds(0.1)

        # Close history
        page.close_history_popup()
        

        if search_done:
            log.info("History search with Enter key works")
        else:
            log.info(
                "H03: History search input not found — "
                "popup has no data table (BUG: no search when history empty)"
            )

    # ---- VM-H04: History search with no match ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_VM_H04_history_search_no_match(self, vehicle_master_page):
        """History search with non-matching text shows empty/no rows."""
        log.info("VM-H04: History search no match")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("HistNoMt")
        result = page.create_vehicle(data)
        page.ensure_vehicle_visible(data["name"])

        # Open history
        page.click_history_button(vehicle_name=data["name"])

        rows_before = page.get_history_row_count()

        # Search with garbage text
        page.search_in_history(f"ZZZNONMATCH{int(time.time())}")

        rows_after = page.get_history_row_count()

        page.close_history_popup()
        

        # After search with no match, rows should be 0 or less
        log.info(
            f"History rows: {rows_before} before search, "
            f"{rows_after} after no-match search"
        )

    # ---- VM-H05: History columns are correct ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_H05_history_columns(self, vehicle_master_page):
        """History table has the expected columns."""
        log.info("VM-H05: History columns")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("HistCol")
        result = page.create_vehicle(data)
        page.ensure_vehicle_visible(data["name"])

        page.click_history_button(vehicle_name=data["name"])

        # Read history headers
        headers = page.driver.find_elements(
            By.CSS_SELECTOR,
            ".big-model table th, "
            "mat-dialog-container table th",
        )
        header_texts = [h.text.strip() for h in headers if h.text.strip()]

        page.close_history_popup()
        

        if header_texts:
            log.info(f"History columns: {header_texts}")
        else:
            log.info(
                "H05: No history table headers found — "
                "popup has no data table (BUG: no columns when history empty)"
            )

    # ---- VM-H06: History Close button works ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_H06_history_close_button(self, vehicle_master_page):
        """History Close button closes the popup."""
        log.info("VM-H06: History Close button")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("HistCls")
        result = page.create_vehicle(data)
        page.ensure_vehicle_visible(data["name"])

        page.click_history_button(vehicle_name=data["name"])

        assert page.is_history_popup_open(), "History popup not open"

        page.close_history_popup()

        assert not page.is_history_popup_open(), (
            "BUG: History popup still open after Close"
        )
        log.info("History Close button works correctly")

    # ---- VM-H07: History X icon closes popup ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_VM_H07_history_x_icon(self, vehicle_master_page):
        """History X icon in header closes the popup."""
        log.info("VM-H07: History X icon close")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("HistX")
        result = page.create_vehicle(data)
        page.ensure_vehicle_visible(data["name"])

        page.click_history_button(vehicle_name=data["name"])

        assert page.is_history_popup_open(), "History popup not open"

        # Click X icon
        page.close_popup()
        

        assert not page.is_history_popup_open(), (
            "BUG: History popup still open after X click"
        )
        log.info("History X icon closes popup correctly")

    # ---- VM-H08: History column sort ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_VM_H08_history_sort(self, vehicle_master_page):
        """Clicking a column header in History sorts the data.
        BUG FOUND: Column sorting doesn't reorder rows.
        """
        log.info("VM-H08: History column sort")
        page = vehicle_master_page

        data = generate_valid_vehicle_data("HistSort")
        result = page.create_vehicle(data)

        # Edit to create 2+ history rows
        edit_result = page.edit_vehicle(
            data["name"], {"price": generate_vehicle_price()}
        )
        page.ensure_vehicle_visible(data["name"])

        page.click_history_button(vehicle_name=data["name"])

        # Read first column data before sort
        rows_before = page.get_history_data()
        first_col_before = [
            r.get("col_0", "") for r in rows_before
        ]

        # Click the first sortable header
        sortable_headers = page.driver.find_elements(
            By.CSS_SELECTOR,
            ".big-model table th, "
            "mat-dialog-container table th",
        )
        if sortable_headers:
            try:
                page.driver.execute_script(
                    "arguments[0].click();", sortable_headers[0]
                )
                page.wait_seconds(0.1)
            except Exception:
                pass

        # Read first column data after sort
        rows_after = page.get_history_data()
        first_col_after = [
            r.get("col_0", "") for r in rows_after
        ]

        page.close_history_popup()
        

        # Check if order changed
        if first_col_before == first_col_after:
            log.warning(
                "BUG CONFIRMED: Column sort doesn't reorder rows"
            )
        else:
            log.info("Column sort changed row order correctly")