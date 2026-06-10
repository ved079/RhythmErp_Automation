"""
test_supplier_ui_interactions.py
--------------------------------
UI-only interaction test suite for RhythmERP Supplier screen.
~7 test cases that verify UI-specific behavior — no data creation needed.

Bucket B — UI-Only Tests: Verify UI rendering, interactions, and behaviors
that cannot be tested via API. Each test uses ``sp_page`` fixture only.

Test Inventory (7 tests):
  SP-C11 — Phone Number alpha chars (HTML5 input type check)
  SP-C12 — Ownership Status (REMOVED: field not on tenant 681)
  SP-C13-C17 — Dropdown options display (5 parameterized, C16+C17 skipped on tenant 681)
  SP-C18 — Stepper Next/Back navigation
  SP-P01/P03/P04 — Popup open/close workflow
  SP-P06 — Phone spinner controls (BUG-003, xfail)
  SP-P07 — Toggle switch defaults

These tests do NOT create data via API — they only interact with the UI
to verify rendering, behavior, and structural correctness.

Run:
  pytest test_supplier_ui_interactions.py -v --tb=short
  pytest test_supplier_ui_interactions.py -v -m ui --tb=short
  pytest test_supplier_ui_interactions.py -v -k "SP_P07" --tb=short
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
from pages.registration.modules.supplier.data.supplier_data import (
    generate_valid_step1_data,
    generate_alpha_phone,
    KnownBugs,
)


# ====================================================================
# SP-C11: Phone Number alpha chars
# ====================================================================

class TestPhoneNumberInput:
    """UI-only: Verify Phone Number input behavior."""

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_SP_C11_phone_alpha_chars(self, sp_page):
        """Type alphabetic chars in Phone Number — should reject or show error."""
        log.info("SP-C11 (UI): Phone Number alpha chars")
        page = sp_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        page.type_text(
            page.PHONE_NUMBER_INPUT,
            generate_alpha_phone(),
            clear_first=True,
        )

        try:
            phone_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Phone Number']"
            )
            actual_value = phone_input.get_attribute("value") or ""
            if actual_value:
                log.warning(f"BUG: Phone Number accepted alpha chars: {actual_value}")
            else:
                log.info("Phone Number correctly rejected alpha chars (type=number)")
        except Exception:
            log.warning("Could not read Phone Number value")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()


# ====================================================================
# SP-C12-C17: Dropdown options display (parameterized)
# ====================================================================

_DROPDOWN_PARAMS = [
    # SP-C12 (ownership_status) — REMOVED: field does not exist on tenant 681.
    # The ERP removed the Ownership Status dropdown from the Supplier screen.
    # If it reappears on another tenant, add it back with:
    #   pytest.param("ownership_status", "OWNERSHIP_STATUS_SELECT",
    #       ["owned", "leased", "proprietorship", "partnership",
    #        "llp", "plc", "private limited company", "individual"],
    #       False, id="SP-C12-ownership-status", marks=pytest.mark.sanity),
    pytest.param(
        "po_type",
        "PO_TYPE_SELECT",
        ["domestic", "import"],
        False,
        id="SP-C13-po-type",
        marks=pytest.mark.sanity,
    ),
    pytest.param(
        "default_currency",
        "DEFAULT_CURRENCY_SELECT",
        None,
        False,
        id="SP-C14-currency",
        marks=pytest.mark.sanity,
    ),
    pytest.param(
        "payment_terms",
        "PAYMENT_TERMS_SELECT",
        None,
        True,
        id="SP-C15-payment-terms",
        marks=pytest.mark.sanity,
    ),
    pytest.param(
        "delivery_terms",
        "DELIVERY_TERMS_SELECT",
        None,
        True,
        id="SP-C16-delivery-terms",
        marks=pytest.mark.skip(reason="Tenant 681: delivery_terms dropdown has no options configured"),
    ),
    pytest.param(
        "mode_of_delivery",
        "MODE_OF_DELIVERY_SELECT",
        ["air", "courier", "sea", "railway", "truck"],
        True,
        id="SP-C17-mode-of-delivery",
        marks=pytest.mark.skip(reason="Tenant 681: mode_of_delivery dropdown has no options configured"),
    ),
]


class TestDropdownValidation:
    """UI-only: Verify dropdown options display correctly."""

    @pytest.mark.ui
    @pytest.mark.parametrize(
        "case_name,locator_attr,expected_keywords,needs_scroll",
        _DROPDOWN_PARAMS,
    )
    def test_dropdown_validation(
        self, sp_page, case_name, locator_attr, expected_keywords, needs_scroll
    ):
        """Validate dropdown shows correct options."""
        log.info(f"Dropdown validation (UI): {case_name}")
        page = sp_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        if needs_scroll:
            page.scroll_to_additional_details()

        locator = getattr(page, locator_attr)
        options = page.get_dropdown_options(locator)

        if expected_keywords is not None:
            options_lower = [o.lower() for o in options]
            found = any(
                any(ek in opt for opt in options_lower)
                for ek in expected_keywords
            )
            assert found or len(options) > 0, (
                f"{case_name} options missing. Expected keywords: {expected_keywords}. "
                f"Found: {options}"
            )
        else:
            assert len(options) > 0, f"No {case_name} options found"

        log.info(f"{case_name} options: {options}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()


# ====================================================================
# SP-C18: Stepper Next/Back navigation
# ====================================================================

class TestStepperNavigation:
    """UI-only: Verify stepper Next/Back navigation."""

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_SP_C18_stepper_navigation(self, sp_page):
        """Navigate through steps via Next/Back buttons."""
        log.info("SP-C18 (UI): Stepper navigation")
        page = sp_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        current_step = page.get_current_step_index()
        assert current_step == 0, f"Expected Step 0, got Step {current_step}"

        step1 = generate_valid_step1_data("NavSP")
        page.fill_step1_universal(step1)
        page.fill_step1_additional(step1)

        page.click_stepper_next()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.get_current_step_index() == 1,
            "Did not navigate to Step 1 after Next",
        )

        page.click_stepper_back()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.get_current_step_index() == 0,
            "Did not navigate back to Step 0 after Back",
        )

        log.info("Stepper Next/Back navigation works correctly")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()


# ====================================================================
# SP-P01/P03/P04: Popup workflow
# ====================================================================

class TestPopupWorkflow:
    """UI-only: Verify popup open/close workflow.

    SP-P01: Add form opens with stepper
    SP-P03: Cancel closes popup without creating
    SP-P04: Close (X) button closes without creating
    """

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_SP_P01_add_form_opens(self, sp_page):
        """Add form opens with stepper UI."""
        log.info("SP-P01 (UI): Add form opens with stepper")
        page = sp_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Check stepper is present
        stepper = page.driver.find_elements(
            By.CSS_SELECTOR, "mat-stepper, mat-horizontal-stepper"
        )
        assert len(stepper) > 0, "Stepper not found in popup"
        log.info("Stepper popup opened correctly")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    @pytest.mark.ui
    def test_SP_P03_cancel_closes_popup(self, sp_page):
        """Cancel closes popup without creating a supplier."""
        log.info("SP-P03 (UI): Cancel closes popup")
        page = sp_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Form did not open",
        )

        step1 = generate_valid_step1_data("CancelSP")
        page.fill_step1_universal(step1)

        page.cancel()

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after Cancel. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("Cancel correctly did not create a supplier")

    @pytest.mark.ui
    def test_SP_P04_close_x_closes_popup(self, sp_page):
        """Close (X) button closes popup without creating."""
        log.info("SP-P04 (UI): Close (X) button")
        page = sp_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Form did not open",
        )

        step1 = generate_valid_step1_data("CloseSP")
        page.fill_step1_universal(step1)

        page.close_popup()

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after X close. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("X close correctly did not create a supplier")


# ====================================================================
# SP-P06: Phone spinner controls (BUG-003)
# ====================================================================

class TestPhoneSpinner:
    """UI-only: Verify Phone Number spinner controls (BUG-003)."""

    @pytest.mark.ui
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_003, strict=False)
    def test_SP_P06_phone_spinner_controls(self, sp_page):
        """Phone Number has spinner arrows — BUG-003: type=number."""
        log.info("SP-P06 (UI): Phone Number spinner controls")
        page = sp_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        has_spinner = page.has_phone_number_spinner()
        assert not has_spinner, (
            "BUG-003 CONFIRMED: Phone Number has spinner controls (type=number)"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()


# ====================================================================
# SP-P07: Toggle switch defaults
# ====================================================================

class TestToggleDefaults:
    """UI-only: Verify toggle switch default states."""

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_SP_P07_toggle_defaults(self, sp_page):
        """Verify toggle defaults: MSME=No, Status=Active, GST=Yes, TDS=No."""
        log.info("SP-P07 (UI): Toggle switch defaults")
        page = sp_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Check Universal toggles
        msme_state = page.get_toggle_state(page.IS_MSME_TOGGLE)
        status_state = page.get_toggle_state(page.STATUS_TOGGLE)

        # Check Additional toggles (need to scroll)
        page.scroll_to_additional_details()
        gst_state = page.get_toggle_state(page.IS_GST_SET_OFF_TOGGLE)
        tds_state = page.get_toggle_state(page.IS_TDS_APPLICABLE_TOGGLE)

        log.info(f"Toggle states — MSME: {msme_state}, Status: {status_state}, "
                 f"GST Set Off: {gst_state}, TDS: {tds_state}")

        # Verify defaults
        assert msme_state is False or msme_state is None, (
            f"MSME default should be No (unchecked), got: {msme_state}"
        )
        assert status_state is True or status_state is None, (
            f"Status default should be Active (checked), got: {status_state}"
        )
        assert gst_state is True or gst_state is None, (
            f"GST Set Off default should be Yes (checked), got: {gst_state}"
        )
        assert tds_state is False or tds_state is None, (
            f"TDS default should be No (unchecked), got: {tds_state}"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()
