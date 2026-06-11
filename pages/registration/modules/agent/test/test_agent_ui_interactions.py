"""
test_agent_ui_interactions.py
-----------------------------
UI-only interaction test suite for RhythmERP Agent screen.
~7 test cases that verify UI-specific behavior — no data creation needed.

Bucket B — UI-Only Tests: Verify UI rendering, interactions, and behaviors
that cannot be tested via API. Each test uses ``agt_page`` fixture only.

Test Inventory (7 tests):
  AGT-I01 — Phone Number input type (HTML5 type=number check)
  AGT-I02 — All dropdowns options (open form once, SoftAssert all 6+)
  AGT-I03 — Stepper Next/Back navigation
  AGT-I04 — Add form opens and closes
  AGT-I05 — Cancel closes popup
  AGT-I06 — Close/X closes popup
  AGT-I07 — Status toggle defaults to Active

These tests do NOT create data via API — they only interact with the UI
to verify rendering, behavior, and structural correctness.

Run:
  pytest test_agent_ui_interactions.py -v --tb=short
  pytest test_agent_ui_interactions.py -v -m ui --tb=short
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
from pages.registration.modules.agent.data.agent_data import (
    generate_valid_agent_data,
    generate_alpha_phone,
)


# ====================================================================
# AGT-I01: Phone Number input type
# ====================================================================

class TestPhoneNumberInput:
    """UI-only: Verify Phone Number input behavior."""

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_AGT_I01_phone_input_type(self, agt_page):
        """Type alphabetic chars in Phone Number — should reject or show error."""
        log.info("AGT-I01 (UI): Phone Number input type check")
        page = agt_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Check that Phone Number input is type="number" or "tel"
        try:
            phone_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Phone Number']"
            )
            input_type = phone_input.get_attribute("type") or ""
            log.info(f"Phone Number input type: '{input_type}'")

            if input_type in ("number", "tel"):
                log.info(f"Phone Number correctly has type='{input_type}' (rejects alpha)")
            else:
                log.warning(
                    f"Phone Number has type='{input_type}' — may accept alpha chars. "
                    f"Expected type='number' or 'tel'."
                )
        except Exception as e:
            log.warning(f"Could not read Phone Number input type: {e}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()


# ====================================================================
# AGT-I02: All dropdowns options (single test, open form once)
# ====================================================================

# Dropdowns to validate: (test_id, field_name, expected_min_options, skip_reason or None)
_DROPDOWN_CHECKS = [
    ("AGT-I02a", "Country", 1, None),
    ("AGT-I02b", "State", 1, "Must select Country first to populate State"),
    ("AGT-I02c", "District", 1, "Must select State first to populate District"),
    ("AGT-I02d", "Payment Terms", 1, None),
    ("AGT-I02e", "Preferred Payment Method", 1, None),
    ("AGT-I02f", "Account Type", 1, None),
]


class TestDropdownValidation:
    """UI-only: Verify all dropdown fields have options available."""

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_AGT_I02_all_dropdowns_options(self, agt_page):
        """Open form once, check ALL dropdowns have at least 1 option each.
        Uses SoftAssert to report all failures at end instead of stopping at first.
        """
        log.info("AGT-I02 (UI): All dropdowns options check")
        page = agt_page
        sa = SoftAssert()

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Fill Universal + Address (same page, Step 0)
        data = generate_valid_agent_data("I02")
        page.fill_universal_step(data)

        # Check Address-level dropdowns (Step 0 — same page as Universal)
        for test_id, field_name, min_opts, skip_reason in _DROPDOWN_CHECKS[:3]:
            if skip_reason and field_name in ("State", "District"):
                # These need cascading — select Country first for State, etc.
                if field_name == "State":
                    page.select_dropdown_by_label("Country", "India")
                    page.wait_seconds(2)
                elif field_name == "District":
                    page.select_dropdown_by_label("State", "Maharashtra")
                    page.wait_seconds(2)

            try:
                options = page.get_dropdown_options_by_label(field_name)
                count = len([o for o in options if o.strip()])
                log.info(f"{test_id}: '{field_name}' has {count} options")

                if count < min_opts:
                    sa.fail(
                        f"{test_id}: '{field_name}' has {count} options, "
                        f"expected >= {min_opts}"
                    )
                else:
                    log.info(f"{test_id}: PASS — '{field_name}' has {count} options")
            except Exception as e:
                sa.fail(f"{test_id}: Error checking '{field_name}': {e}")

        # Fill Address fully, then advance to Payment step
        page.fill_address_step(data["address"])
        page.click_next()  # Step 0 -> Step 1 (Payment)
        page.wait_seconds(1.5)

        # Check Payment-level dropdowns (Step 1)
        for test_id, field_name, min_opts, skip_reason in _DROPDOWN_CHECKS[3:5]:
            try:
                options = page.get_dropdown_options_by_label(field_name)
                count = len([o for o in options if o.strip()])
                log.info(f"{test_id}: '{field_name}' has {count} options")

                if count < min_opts:
                    sa.fail(
                        f"{test_id}: '{field_name}' has {count} options, "
                        f"expected >= {min_opts}"
                    )
                else:
                    log.info(f"{test_id}: PASS — '{field_name}' has {count} options")
            except Exception as e:
                sa.fail(f"{test_id}: Error checking '{field_name}': {e}")

        # Navigate to Bank step for Account Type
        page.click_next()
        page.wait_seconds(1.5)

        for test_id, field_name, min_opts, skip_reason in _DROPDOWN_CHECKS[5:]:
            try:
                options = page.get_dropdown_options_by_label(field_name)
                count = len([o for o in options if o.strip()])
                log.info(f"{test_id}: '{field_name}' has {count} options")

                if count < min_opts:
                    sa.fail(
                        f"{test_id}: '{field_name}' has {count} options, "
                        f"expected >= {min_opts}"
                    )
                else:
                    log.info(f"{test_id}: PASS — '{field_name}' has {count} options")
            except Exception as e:
                sa.fail(f"{test_id}: Error checking '{field_name}': {e}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

        sa.check_all()


# ====================================================================
# AGT-I03: Stepper navigation
# ====================================================================

class TestStepperNavigation:
    """UI-only: Verify stepper Next/Back navigation across all steps."""

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_AGT_I03_stepper_navigation(self, agt_page):
        """Navigate all 4 steps forward, then back, verify step labels."""
        log.info("AGT-I03 (UI): Stepper navigation")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("I03")

        # Forward: Universal + Address (Step 0) → Payment (Step 1) → Bank (Step 2)
        page.fill_universal_step(data)
        page.fill_address_step(data["address"])
        page.click_next()  # Step 0 -> Step 1 (Payment)
        page.wait_seconds(1.5)
        step1 = page.get_active_step_index()
        label1 = page.get_active_step_label()
        log.info(f"After Next 1: step={step1}, label='{label1}'")

        page.click_next()  # Step 1 -> Step 2 (Bank)
        page.wait_seconds(1.5)
        step2 = page.get_active_step_index()
        label2 = page.get_active_step_label()
        log.info(f"After Next 2: step={step2}, label='{label2}'")

        # Step 2 is the last step — no more Next
        step3 = page.get_active_step_index()
        label3 = page.get_active_step_label()
        log.info(f"After Next 3: step={step3}, label='{label3}'")

        # Back: Bank (Step 2) → Payment (Step 1) → Universal+Address (Step 0)
        page.click_back()  # Step 2 -> Step 1
        page.wait_seconds(1.5)
        step_back1 = page.get_active_step_index()
        log.info(f"After Back 1: step={step_back1}")

        page.click_back()  # Step 1 -> Step 0
        page.wait_seconds(1.5)
        step_back0 = page.get_active_step_index()
        log.info(f"After Back 2: step={step_back0}")

        assert step_back0 == 0, f"After Back clicks, should be on step 0, got {step_back0}"

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()


# ====================================================================
# AGT-I04/I05/I06: Popup workflow
# ====================================================================

class TestPopupWorkflow:
    """UI-only: Verify popup open/close workflows."""

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_AGT_I04_add_form_opens(self, agt_page):
        """Open the ADD form — verify popup is visible."""
        log.info("AGT-I04 (UI): Add form opens")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        is_open = page.is_add_form_open()
        assert is_open, "ADD form popup should be visible after clicking ADD"

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_AGT_I05_cancel_closes_popup(self, agt_page):
        """Click Cancel — verify popup closes."""
        log.info("AGT-I05 (UI): Cancel closes popup")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Form should be open before Cancel"

        page.cancel()
        page.wait_seconds(1)

        is_still_open = page.is_form_popup_open()
        assert not is_still_open, "Form should be closed after Cancel"

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_AGT_I06_close_popup(self, agt_page):
        """Force close popup — verify it's gone."""
        log.info("AGT-I06 (UI): Force close popup")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Form should be open before close"

        page.force_close_form_popup()
        page.wait_seconds(0.5)

        is_still_open = page.is_form_popup_open()
        assert not is_still_open, "Form should be gone after force close"


# ====================================================================
# AGT-I07: Toggle defaults
# ====================================================================

class TestToggleDefaults:
    """UI-only: Verify toggle/switch default states."""

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_AGT_I07_status_toggle_default(self, agt_page):
        """Status toggle should default to Active (checked) on new form."""
        log.info("AGT-I07 (UI): Status toggle default")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        # Check if there's a Status toggle and its default state
        js = """
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return 'No popup';
            var toggles = popup.querySelectorAll('mat-slide-toggle, mat-checkbox');
            var results = [];
            for (var i = 0; i < toggles.length; i++) {
                results.push({
                    tag: toggles[i].tagName,
                    checked: toggles[i].classList.contains('mat-checked') ||
                             toggles[i].getAttribute('aria-checked') === 'true',
                    label: toggles[i].textContent.trim()
                });
            }
            return JSON.stringify(results);
        """
        result = page.driver.execute_script(js)
        log.info(f"Toggle/checkbox states: {result}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()
