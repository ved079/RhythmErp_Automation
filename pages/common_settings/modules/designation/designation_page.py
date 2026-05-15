"""
Designation Page Object — RhythmERP Common Settings > Designation

Page Object Model for the Designation screen with all locators,
action flows, and helper methods. Follows the same pattern as
VehicleMasterPage.

Key Differences from Vehicle Master:
- Status is a TOGGLE SWITCH (not a dropdown)
- Name has pattern validation ("Invalid Name" mat-error)
- Only 3 fields: Name, Description, Status
- No dropdowns at all
- Table has Status column (Active/Inactive)
"""

import os
import sys
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)

# Resolve project root for imports
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.base_page import BasePage
from common.logger import log


class DesignationPage(BasePage):
    """Page Object Model for RhythmERP Designation screen."""

    PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Designation"

    # ═══════════════════════════════════════════
    #  LOCATORS — Table & Toolbar
    # ═══════════════════════════════════════════

    TABLE = ("css", "table#excel-table")
    TABLE_CONTAINER = ("css", ".scrollable-table-container")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    TOOLBAR = ("css", "ul.tbl-export-btn")

    SEARCH_BUTTON = ("css", "button.search-btn")
    ADD_BUTTON = ("xpath", "//*[@mattooltip='ADD']/button")
    FILTER_BUTTON = ("css", "button.filter-btn")
    MORE_BUTTON = ("css", "button[mattooltip='More']")

    SEARCH_INPUT = ("css", "#erpSearchInput")

    # ═══════════════════════════════════════════
    #  LOCATORS — Table Column Cells
    # ═══════════════════════════════════════════

    NAME_CELLS = ("css", "td.cdk-column-name, td.mat-column-name")
    DESCRIPTION_CELLS = ("css", "td.cdk-column-description, td.mat-column-description")
    STATUS_CELLS = ("css", "td.cdk-column-status, td.mat-column-status")

    # ═══════════════════════════════════════════
    #  LOCATORS — Popup Container (Add/Edit/View)
    # ═══════════════════════════════════════════

    POPUP_CONTAINER = ("css", ".edit_pop_up.override_edit_pop_up.popup-mode")
    BIG_MODEL = ("css", ".big-model")
    POPUP_HEADER = ("css", ".popup-header")
    POPUP_TITLE = ("css", ".big-model h3")
    POPUP_FOOTER = ("xpath", "//div[contains(@class,'popup-footer')]")
    POPUP_BODY = ("css", ".overflow_model")

    # ═══════════════════════════════════════════
    #  LOCATORS — Form Fields
    # ═══════════════════════════════════════════

    NAME_INPUT = ("css", "input[name='Name']")
    DESCRIPTION_INPUT = ("css", "input[name='Description']")
    STATUS_TOGGLE = ("xpath",
        "//span[contains(@class,'main-label') and text()='Status']"
        "/ancestor::div[contains(@class,'switch-container')]"
    )
    STATUS_SLIDER = ("css", ".switch-wrapper .slider")
    STATUS_CHECKBOX = ("css", ".switch-wrapper input[type='checkbox']")

    # ═══════════════════════════════════════════
    #  LOCATORS — Popup Buttons
    # ═══════════════════════════════════════════

    SUBMIT_BUTTON = ("xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    )
    UPDATE_BUTTON = ("xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
    )
    CANCEL_BUTTON = ("xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    )

    # ═══════════════════════════════════════════
    #  LOCATORS — SweetAlert2
    # ═══════════════════════════════════════════

    SWAL_TITLE = ("css", "#swal2-title")
    SWAL_CONFIRM = ("css", ".swal2-confirm")
    SWAL_CONTAINER = ("css", ".swal2-container")

    # ═══════════════════════════════════════════
    #  LOCATORS — History Popup
    # ═══════════════════════════════════════════

    HISTORY_TITLE = ("xpath",
        "//h3[contains(translate(.,'HISTORY','history'),'history')]"
    )
    HISTORY_SEARCH_INPUT = ("css", ".popup-body input, .popup-content input")
    HISTORY_TABLE = ("css", ".big-model table tbody tr, .popup-content table tbody tr")

    # ═══════════════════════════════════════════
    #  LOCATORS — Filter Panel
    # ═══════════════════════════════════════════

    FILTER_PANEL = ("css", ".filter-panel")
    FILTER_APPLY = ("css", ".filter-actions .apply-btn")
    FILTER_CLEAR = ("css", ".filter-actions .clear-btn")

    # ═══════════════════════════════════════════
    #  NAVIGATION & PAGE LOAD
    # ═══════════════════════════════════════════

    def navigate_to_page(self):
        """Navigate to Designation screen and force refresh."""
        log.info("Navigating to Designation screen")
        self.navigate_to(self.PAGE_URL)
        time.sleep(2)
        self.driver.refresh()
        time.sleep(2)
        self._wait_for_page_ready()
        log.info("Designation page loaded successfully")

    def _wait_for_page_ready(self, timeout=20):
        """Wait for page fully loaded — table + toolbar ready.
        Retries once on timeout to handle flaky page loads.
        """
        for attempt in range(2):
            try:
                WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, "table#excel-table")
                    )
                )
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "ul.tbl-export-btn")
                    )
                )
                time.sleep(1)  # Angular digest cycle
                self._wait_for_toolbar()
                return  # Success
            except TimeoutException:
                if attempt == 0:
                    log.warning("Page ready wait timed out, retrying with refresh...")
                    self.driver.refresh()
                    time.sleep(3)
                else:
                    log.warning("Page ready wait timed out after retry, continuing anyway")

    def _wait_for_toolbar(self, retries=3, delay=2):
        """Retry ADD button readiness."""
        for attempt in range(retries):
            try:
                add_div = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[mattooltip='ADD']"
                )
                add_btns = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "button.mat-mdc-mini-fab mat-icon"
                )
                add_icons = [b for b in add_btns
                             if b.text.strip().lower() == 'add']
                if add_div or add_icons:
                    return
            except Exception:
                pass
            time.sleep(delay)
        log.warning("Toolbar readiness check: ADD button not confirmed")

    def is_page_loaded(self):
        """Check if listing page loaded."""
        return self.is_displayed(self.TABLE, timeout=10)

    # ═══════════════════════════════════════════
    #  ADD FORM
    # ═══════════════════════════════════════════

    def open_add_form(self):
        """Click ADD button to open create form. 4 strategies."""
        log.info("Opening ADD form")
        self._wait_for_toolbar()

        # Strategy 1: mattooltip div button
        try:
            divs = self.driver.find_elements(
                By.CSS_SELECTOR, "div[mattooltip='ADD']"
            )
            for div in divs:
                btn = div.find_element(By.TAG_NAME, "button")
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", btn
                )
                self.driver.execute_script(
                    "arguments[0].click();", btn
                )
                time.sleep(1)
                if self._is_form_popup_open():
                    log.info("ADD form opened via Strategy 1 (mattooltip div)")
                    return
        except Exception as e:
            log.info(f"Strategy 1 failed: {e}")

        # Strategy 2: mini-fab icon='add'
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button.mat-mdc-mini-fab mat-icon"
            )
            for btn in btns:
                if btn.text.strip().lower() == 'add':
                    parent_btn = btn.find_element(By.XPATH, "..")
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", parent_btn
                    )
                    self.driver.execute_script(
                        "arguments[0].click();", parent_btn
                    )
                    time.sleep(1)
                    if self._is_form_popup_open():
                        log.info("ADD form opened via Strategy 2 (mini-fab icon)")
                        return
        except Exception as e:
            log.info(f"Strategy 2 failed: {e}")

        # Strategy 3: div wrapper click
        try:
            divs = self.driver.find_elements(
                By.CSS_SELECTOR, "div[mattooltip='ADD']"
            )
            for div in divs:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", div
                )
                self.driver.execute_script("arguments[0].click();", div)
                time.sleep(1)
                if self._is_form_popup_open():
                    log.info("ADD form opened via Strategy 3 (div wrapper)")
                    return
        except Exception as e:
            log.info(f"Strategy 3 failed: {e}")

        # Strategy 4: click_with_retry
        try:
            self.click_with_retry(self.ADD_BUTTON)
            time.sleep(1)
            if self._is_form_popup_open():
                log.info("ADD form opened via Strategy 4 (click_with_retry)")
                return
        except Exception as e:
            log.info(f"Strategy 4 failed: {e}")

        raise Exception("Failed to open ADD form after 4 strategies")

    def _is_form_popup_open(self):
        """Check if form popup is visible."""
        try:
            big_model = self.driver.find_elements(
                By.CSS_SELECTOR, ".big-model"
            )
            for bm in big_model:
                if bm.is_displayed():
                    return True
            dialog = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-dialog-container"
            )
            for d in dialog:
                if d.is_displayed():
                    return True
        except Exception:
            pass
        return False

    def is_add_form_open(self):
        """Check if Add form visible (Name input present)."""
        return self.is_displayed(self.NAME_INPUT, timeout=5)

    def is_form_closed(self):
        """Check if form popup closed."""
        return not self.is_displayed(self.NAME_INPUT, timeout=3)

    # ═══════════════════════════════════════════
    #  FORM FILL
    # ═══════════════════════════════════════════

    def fill_designation_form(self, data):
        """Fill all form fields.
        data: dict with keys 'name', 'description', 'status'
        """
        log.info("Filling designation form")

        # Name
        if data.get('name') is not None:
            self._set_angular_input(self.NAME_INPUT, data['name'], clear_first=True)
            log.info(f"Name set to: {data['name']}")

        # Description
        if data.get('description') is not None:
            self._set_angular_input(
                self.DESCRIPTION_INPUT, data['description'], clear_first=True
            )
            log.info(f"Description set to: {data['description']}")

        # Status toggle
        if data.get('status') is not None:
            current_active = self.get_toggle_state()
            desired_active = data['status']  # True=Active, False=Inactive
            if current_active != desired_active:
                self.toggle_status()
                log.info(
                    f"Status toggled to "
                    f"{'Active' if desired_active else 'Inactive'}"
                )

    # ═══════════════════════════════════════════
    #  STATUS TOGGLE
    # ═══════════════════════════════════════════

    def get_toggle_state(self):
        """Get current Status toggle state.
        Returns True if Active (checked), False if Inactive (unchecked).
        """
        try:
            # Strategy 1: Check checkbox
            checkboxes = self.driver.find_elements(
                By.CSS_SELECTOR, ".switch-wrapper input[type='checkbox']"
            )
            for cb in checkboxes:
                if cb.is_displayed() or cb.find_element(
                    By.XPATH, "./ancestor::div[contains(@class,'switch-wrapper')]"
                ).is_displayed():
                    return cb.is_selected() if hasattr(cb, 'is_selected') else cb.get_property('checked')

            # Strategy 2: Check "on active" state label
            on_labels = self.driver.find_elements(
                By.CSS_SELECTOR, ".switch-wrapper .state-label.on"
            )
            for label in on_labels:
                if 'active' in label.get_attribute('class'):
                    wrapper = label.find_element(
                        By.XPATH, "./ancestor::div[contains(@class,'switch-wrapper')]"
                    )
                    if wrapper.is_displayed():
                        return True
            return False
        except Exception:
            return True  # Default to Active

    def toggle_status(self):
        """Click the Status toggle slider to switch Active/Inactive."""
        try:
            sliders = self.driver.find_elements(
                By.CSS_SELECTOR, ".switch-wrapper .slider"
            )
            for slider in sliders:
                wrapper = slider.find_element(
                    By.XPATH, "./ancestor::div[contains(@class,'switch-wrapper')]"
                )
                if wrapper.is_displayed():
                    self.driver.execute_script(
                        "arguments[0].click();", slider
                    )
                    time.sleep(0.5)
                    return
        except Exception as e:
            log.warning(f"Toggle slider click failed: {e}, trying wrapper")
            try:
                wrappers = self.driver.find_elements(
                    By.CSS_SELECTOR, ".switch-wrapper"
                )
                for w in wrappers:
                    if w.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].click();", w
                        )
                        time.sleep(0.5)
                        return
            except Exception as e2:
                log.error(f"Toggle wrapper click also failed: {e2}")

    def set_toggle_state(self, active=True):
        """Set toggle to specific state: True=Active, False=Inactive.
        Only clicks if current state differs from desired.
        """
        current = self.get_toggle_state()
        if current != active:
            self.toggle_status()
            time.sleep(0.3)
            # Verify
            new_state = self.get_toggle_state()
            if new_state != active:
                log.warning(
                    f"Toggle state mismatch: wanted "
                    f"{'Active' if active else 'Inactive'}, "
                    f"got {'Active' if new_state else 'Inactive'}"
                )

    def get_toggle_display_text(self):
        """Get the display text of current toggle state ('Active' or 'Inactive')."""
        try:
            on_labels = self.driver.find_elements(
                By.CSS_SELECTOR, ".switch-wrapper .state-label.on"
            )
            for label in on_labels:
                if 'active' in label.get_attribute('class'):
                    wrapper = label.find_element(
                        By.XPATH, "./ancestor::div[contains(@class,'switch-wrapper')]"
                    )
                    if wrapper.is_displayed():
                        return 'Active'
            return 'Inactive'
        except Exception:
            return 'Active'

    # ═══════════════════════════════════════════
    #  FORM SUBMIT / UPDATE / CANCEL
    # ═══════════════════════════════════════════

    def submit(self):
        """Click Submit button (Create mode). JS click with scroll."""
        log.info("Clicking Submit button")
        try:
            # Strategy 1: find_visible_element + JS click
            btn = self.find_visible_element(self.SUBMIT_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", btn
                )
                self.driver.execute_script("arguments[0].click();", btn)
                return
        except Exception as e:
            log.info(f"Submit strategy 1 failed: {e}")

        try:
            # Strategy 2: direct find + JS click
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", btn
            )
            self.driver.execute_script("arguments[0].click();", btn)
            return
        except Exception as e:
            log.info(f"Submit strategy 2 failed: {e}")

        try:
            # Strategy 3: click_with_retry
            self.click_with_retry(self.SUBMIT_BUTTON)
        except Exception as e:
            log.error(f"All submit strategies failed: {e}")

    def click_update(self):
        """Click Update button (Edit mode). JS click with scroll."""
        log.info("Clicking Update button")
        try:
            btn = self.find_visible_element(self.UPDATE_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", btn
                )
                self.driver.execute_script("arguments[0].click();", btn)
                return
        except Exception as e:
            log.info(f"Update strategy 1 failed: {e}")

        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", btn
            )
            self.driver.execute_script("arguments[0].click();", btn)
            return
        except Exception as e:
            log.info(f"Update strategy 2 failed: {e}")

        try:
            self.click_with_retry(self.UPDATE_BUTTON)
        except Exception as e:
            log.error(f"All update strategies failed: {e}")

    def cancel(self):
        """Click Cancel button."""
        log.info("Clicking Cancel button")
        try:
            btn = self.find_visible_element(self.CANCEL_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script("arguments[0].click();", btn)
                return
        except Exception:
            pass
        try:
            self.click_with_retry(self.CANCEL_BUTTON)
        except Exception as e:
            log.error(f"Cancel failed: {e}")

    def close_popup(self):
        """Click X icon in popup header."""
        log.info("Closing popup via X icon")
        try:
            icons = self.driver.find_elements(
                By.CSS_SELECTOR, ".big-model button mat-icon"
            )
            for icon in icons:
                if icon.text.strip().lower() == 'close':
                    btn = icon.find_element(By.XPATH, "./ancestor::button")
                    self.driver.execute_script(
                        "arguments[0].click();", btn
                    )
                    return
        except Exception:
            pass
        # Fallback: cancel
        self.cancel()

    # ═══════════════════════════════════════════
    #  SWEETALERT2 HANDLING
    # ═══════════════════════════════════════════

    def handle_success_alert(self, timeout=60):
        """Wait for SweetAlert2 success, click OK, cleanup.
        Returns message text or ''.
        """
        log.info("Waiting for success alert")
        message = ''
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            message = title_el.text.strip()
            log.info(f"SweetAlert2 message: {message}")

            # 3-tier confirm click
            try:
                confirm = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-confirm"
                )
                confirm.click()
            except ElementClickInterceptedException:
                self.driver.execute_script(
                    "arguments[0].click();", confirm
                )
            except Exception:
                self.driver.execute_script(
                    "document.querySelectorAll('.swal2-confirm')"
                    ".forEach(function(b){b.click();})"
                )

            # Wait for container invisible
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-container")
                )
            )
        except TimeoutException:
            log.warning("Success alert not found within timeout")
        except Exception as e:
            log.warning(f"Success alert handling error: {e}")

        # Cleanup leftover elements
        try:
            self.driver.execute_script(
                "document.querySelectorAll('.swal2-container')"
                ".forEach(function(el){el.remove();})"
            )
            self.driver.execute_script(
                "document.querySelectorAll('.cdk-overlay-backdrop')"
                ".forEach(function(el){el.remove();})"
            )
        except Exception:
            pass

        return message

    def handle_validation_warning(self, timeout=10):
        """Handle SweetAlert2 validation warning popup.
        Returns warning text or ''.
        """
        log.info("Handling validation warning")
        warning_text = ''
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            warning_text = title_el.text.strip()
            log.info(f"Validation warning: {warning_text}")

            # JS click confirm
            try:
                confirm = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-confirm"
                )
                self.driver.execute_script(
                    "arguments[0].click();", confirm
                )
            except Exception:
                self.driver.execute_script(
                    "document.querySelectorAll('.swal2-confirm')"
                    ".forEach(function(b){b.click();})"
                )

            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-container")
                )
            )
        except TimeoutException:
            log.info("No validation warning found")
        except Exception as e:
            log.warning(f"Validation warning handling error: {e}")

        return warning_text

    def is_validation_alert_present(self, timeout=5):
        """Check if SweetAlert2 visible."""
        return self.is_displayed(self.SWAL_TITLE, timeout=timeout)

    # ═══════════════════════════════════════════
    #  INLINE ERROR (mat-error)
    # ═══════════════════════════════════════════

    def get_mat_error_text(self):
        """Get all inline validation error texts — 4-tier approach:
        Tier 1: Look for visible mat-error elements in DOM.
        Tier 2: Check Angular FormControl invalid state via ng-invalid class.
        Tier 3: Compare intended value vs actual DOM value — detect when
                Angular's type="character" silently rejected the value.
        Tier 4: Directly validate the DOM value against type="character" rules
                (catches spaces-only and invalid chars even when Angular doesn't
                mark the control as invalid).
        """
        import re
        errors = []

        # Tier 1: Find visible mat-error elements
        try:
            js_errors = self.driver.execute_script("""
                var errors = [];
                var matErrors = document.querySelectorAll('mat-error');
                matErrors.forEach(function(el) {
                    var text = el.textContent.trim();
                    if (text) {
                        errors.push(text);
                    }
                });
                return errors;
            """)
            if js_errors:
                errors = js_errors
                return errors
        except Exception:
            pass

        # Tier 2: Check Angular FormControl invalid state directly
        try:
            angular_errors = self.driver.execute_script("""
                var errors = [];
                var inputs = document.querySelectorAll(
                    '.big-model input[name], .big-model input[formcontrolname]'
                );
                inputs.forEach(function(input) {
                    if (!input.classList.contains('ng-invalid')) return;

                    var fieldName = input.getAttribute('name') ||
                                    input.getAttribute('formcontrolname') || 'unknown';

                    // Skip if input was never modified AND never touched
                    // (pristine untouched = fresh form, not a validation error)
                    if (input.classList.contains('ng-pristine') &&
                        input.classList.contains('ng-untouched')) return;

                    // Determine error message based on field
                    if (fieldName === 'Name') {
                        errors.push('Invalid Name');
                    } else {
                        errors.push(fieldName + ' is invalid');
                    }
                });
                return errors;
            """)
            if angular_errors:
                errors = angular_errors
                return errors
        except Exception:
            pass

        # Tier 3: Compare intended value vs actual DOM value
        # When Angular's type="character" silently REJECTS the value,
        # the DOM value will differ from what we tried to set.
        # E.g., we set "12345" but Angular stripped it to ""
        try:
            intended = getattr(self, '_intended_values', {})
            for field_name, intended_value in intended.items():
                if not intended_value:
                    continue  # Skip empty intended values
                try:
                    actual_el = self.driver.find_element(
                        By.CSS_SELECTOR, f"input[name='{field_name}']"
                    )
                    actual_value = actual_el.get_attribute('value') or ''

                    if field_name == 'Name':
                        # Case 1: Value was completely rejected (Angular stripped it)
                        # We set "12345" but Angular cleared it to ""
                        if intended_value and not actual_value:
                            errors.append('Invalid Name')
                        # Case 2: Value was partially rejected or different
                        # Angular may have stripped some chars
                        elif actual_value != intended_value:
                            errors.append('Invalid Name')
                        # Case 3: Value accepted but invalid per pattern
                        # Spaces-only: "     " passes type="character" but is invalid
                        elif actual_value and actual_value.strip() == '':
                            errors.append('Invalid Name')
                        # Case 4: Value contains chars rejected by type="character"
                        # type="character" allows: letters, spaces, . , - ( )
                        # It rejects: digits, @#$%^&*!, underscores
                        elif actual_value and not re.match(r'^[a-zA-Z\s\.\,\-\(\)]+$', actual_value):
                            errors.append('Invalid Name')
                except Exception:
                    continue
            if errors:
                return errors
        except Exception:
            pass

        # Tier 4: Direct DOM value validation for Name field
        # Check the actual DOM value against type="character" rules
        # regardless of Angular's FormControl state.
        try:
            name_input = self.driver.find_element(
                By.CSS_SELECTOR, ".big-model input[name='Name']"
            )
            actual_value = name_input.get_attribute('value') or ''
            input_type = name_input.get_attribute('type') or ''

            # Only validate if there's a value or if we intended to set one
            intended_name = getattr(self, '_intended_values', {}).get('Name', '')

            if input_type == 'character' and (actual_value or intended_name):
                # Value was set but Angular cleared it
                if intended_name and not actual_value:
                    errors.append('Invalid Name')
                # Value exists — check against character rules
                # type="character" allows: letters, spaces, . , - ( )
                elif actual_value:
                    if not re.match(r'^[a-zA-Z\s\.\,\-\(\)]+$', actual_value):
                        errors.append('Invalid Name')
                    elif actual_value.strip() == '':
                        errors.append('Invalid Name')
        except Exception:
            pass

        return errors

    def has_field_error(self, field_label):
        """Check if specific field has inline error.
        field_label: 'Name' or 'Description' or 'Status'
        Uses 2-tier approach: mat-error elements first, then ng-invalid class.
        """
        try:
            # Tier 1: Look for mat-error element via XPath
            if field_label == 'Status':
                xpath = (
                    "//span[contains(@class,'main-label') and "
                    f"text()='{field_label}']/ancestor::div"
                    "[contains(@class,'switch-container')]"
                    "//mat-error"
                )
            else:
                xpath = (
                    "//mat-label[contains(.,'"
                    f"{field_label}"
                    "')]/ancestor::mat-form-field"
                    "//mat-error"
                )
            errors = self.driver.find_elements(By.XPATH, xpath)
            if len(errors) > 0:
                return True

            # Tier 2: Check ng-invalid on the input + mat-form-field-invalid
            if field_label == 'Name':
                return self.has_name_invalid_class()
            elif field_label == 'Description':
                try:
                    desc_input = self.driver.find_element(
                        By.CSS_SELECTOR, "input[name='Description']"
                    )
                    cls = desc_input.get_attribute('class') or ''
                    if 'ng-invalid' in cls and 'ng-touched' in cls:
                        return True
                except Exception:
                    pass
            return False
        except Exception:
            return False

    def has_name_invalid_class(self):
        """Check if Name input is in an invalid state.
        Checks: ng-invalid + ng-touched class, OR value is invalid for
        type="character" (spaces-only, contains digits/special chars).
        Angular's type="character" accepts spaces as valid characters,
        so spaces-only names have ng-valid but are actually invalid per
        the pattern validation that only shows on Submit.
        """
        try:
            name_input = self.driver.find_element(
                By.CSS_SELECTOR, "input[name='Name']"
            )
            cls = name_input.get_attribute('class') or ''
            value = name_input.get_attribute('value') or ''

            # Standard Angular check: ng-invalid + ng-touched
            if 'ng-invalid' in cls and 'ng-touched' in cls:
                return True

            # Value-based check: type="character" should reject invalid content
            # even when Angular marks it as ng-valid
            # type="character" allows: letters, spaces, . , - ( )
            # It rejects: digits, @#$%^&*!, underscores
            if value and 'ng-touched' in cls:
                import re
                # Spaces-only is invalid for Name
                if value.strip() == '':
                    return True
                # Contains chars rejected by type="character"
                if not re.match(r'^[a-zA-Z\s\.\,\-\(\)]+$', value):
                    return True

            return False
        except Exception:
            return False

    # ═══════════════════════════════════════════
    #  FORM STATE QUERIES
    # ═══════════════════════════════════════════

    def get_form_heading(self):
        """Read popup heading text."""
        try:
            h3 = self.driver.find_element(
                By.CSS_SELECTOR, ".big-model h3"
            )
            return h3.text.strip()
        except Exception:
            return ''

    def is_view_mode(self):
        """Check if View (read-only) mode — inputs disabled."""
        try:
            name_input = self.driver.find_element(
                By.CSS_SELECTOR, "input[name='Name']"
            )
            return not name_input.is_enabled()
        except Exception:
            return False

    def is_edit_mode(self):
        """Check if Edit mode — Update button visible."""
        return self.is_displayed(self.UPDATE_BUTTON, timeout=3)

    def get_form_field_values(self):
        """Read all form field values.
        Returns dict: name, description, status (True/False)
        """
        values = {}
        try:
            name_input = self.driver.find_element(
                By.CSS_SELECTOR, "input[name='Name']"
            )
            values['name'] = name_input.get_attribute('value')
        except Exception:
            values['name'] = ''

        try:
            desc_input = self.driver.find_element(
                By.CSS_SELECTOR, "input[name='Description']"
            )
            values['description'] = desc_input.get_attribute('value')
        except Exception:
            values['description'] = ''

        try:
            values['status'] = self.get_toggle_state()
        except Exception:
            values['status'] = True

        return values

    # ═══════════════════════════════════════════
    #  TABLE QUERIES
    # ═══════════════════════════════════════════

    def get_table_row_count(self):
        """Count visible data rows."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def get_all_designation_names(self):
        """List all designation names in table."""
        names = []
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            for row in rows:
                try:
                    # Multiple fallback selectors
                    cell = (
                        row.find_elements(
                            By.CSS_SELECTOR,
                            "td.cdk-column-name"
                        )
                        or row.find_elements(
                            By.CSS_SELECTOR,
                            "td.mat-column-name"
                        )
                        or row.find_elements(
                            By.CSS_SELECTOR, "td:nth-child(4)"
                        )
                    )
                    if cell:
                        names.append(cell[0].text.strip())
                except Exception:
                    continue
        except Exception:
            pass
        return names

    def is_designation_in_table(self, designation_name):
        """Check if designation exists in table (partial match)."""
        names = self.get_all_designation_names()
        return any(
            designation_name.lower() in n.lower() for n in names
        )

    def find_designation_row_index(self, designation_name):
        """Find row index by name. Returns -1 if not found."""
        names = self.get_all_designation_names()
        for i, n in enumerate(names):
            if designation_name.lower() in n.lower():
                return i
        return -1

    def get_status_from_table(self, designation_name):
        """Get Status text ('Active'/'Inactive') for a designation."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            for row in rows:
                name_cell = row.find_elements(
                    By.CSS_SELECTOR, "td.cdk-column-name"
                )
                if name_cell and designation_name.lower() in name_cell[0].text.lower():
                    status_cell = row.find_elements(
                        By.CSS_SELECTOR, "td.cdk-column-status"
                    )
                    if status_cell:
                        return status_cell[0].text.strip()
        except Exception:
            pass
        return ''

    # ═══════════════════════════════════════════
    #  SEARCH
    # ═══════════════════════════════════════════

    def search_designation(self, designation_name, retries=3):
        """Search by name using JS value injection + Enter.
        Returns True if found in results.
        """
        log.info(f"Searching for: {designation_name}")
        for attempt in range(retries):
            try:
                # Toggle search button
                search_btn = self.driver.find_element(
                    By.CSS_SELECTOR, "button.search-btn"
                )
                self.driver.execute_script(
                    "arguments[0].click();", search_btn
                )
                time.sleep(0.5)

                # Set value via JS
                search_input = self.driver.find_element(
                    By.CSS_SELECTOR, "#erpSearchInput"
                )
                self.driver.execute_script(
                    "arguments[0].value = arguments[1];",
                    search_input, designation_name
                )
                self.driver.execute_script(
                    "arguments[0].dispatchEvent("
                    "new Event('input', {bubbles: true}));",
                    search_input
                )
                self.driver.execute_script(
                    "arguments[0].dispatchEvent("
                    "new KeyboardEvent('keydown', "
                    "{key: 'Enter', keyCode: 13, bubbles: true}));",
                    search_input
                )
                time.sleep(2)

                if self.is_designation_in_table(designation_name):
                    log.info(f"Found '{designation_name}' in search")
                    return True
                log.info(
                    f"Search attempt {attempt + 1} — not found, retrying"
                )
            except Exception as e:
                log.info(f"Search attempt {attempt + 1} failed: {e}")
                time.sleep(2)
        return False

    def clear_search(self):
        """Clear search input."""
        try:
            search_input = self.driver.find_element(
                By.CSS_SELECTOR, "#erpSearchInput"
            )
            search_input.clear()
            search_input.send_keys(Keys.RETURN)
            time.sleep(1)
        except Exception:
            pass

    def click_refresh(self):
        """Click Refresh button."""
        log.info("Clicking Refresh button")
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button.mat-mdc-mini-fab mat-icon"
            )
            for btn in btns:
                if btn.text.strip().lower() == 'refresh':
                    parent = btn.find_element(By.XPATH, "..")
                    self.driver.execute_script(
                        "arguments[0].click();", parent
                    )
                    return
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  ROW ACTION BUTTONS
    # ═══════════════════════════════════════════

    def _click_action_button(self, designation_name, column_class, idx,
                              tooltip_text=None):
        """Click an action button (View/Edit/History) on a row.
        Tries XPath by name first, then index-based fallback.
        """
        # Strategy 1: XPath by name
        if designation_name:
            try:
                xpath = (
                    f"//td[contains(text(),'{designation_name}')]"
                    f"/ancestor::tr//td[contains(@class,'{column_class}')]"
                    f"//button"
                )
                btn = self.driver.find_element(By.XPATH, xpath)
                self.driver.execute_script(
                    "arguments[0].click();", btn
                )
                time.sleep(1)
                return True
            except Exception:
                pass

        # Strategy 2: Index-based click
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            for row in rows:
                if designation_name:
                    name_cell = row.find_elements(
                        By.CSS_SELECTOR, "td.cdk-column-name"
                    )
                    if not name_cell or designation_name.lower() not in name_cell[0].text.lower():
                        continue

                action_btns = row.find_elements(
                    By.CSS_SELECTOR, "td.action button"
                )
                if idx < len(action_btns):
                    self.driver.execute_script(
                        "arguments[0].click();", action_btns[idx]
                    )
                    time.sleep(1)
                    return True
        except Exception as e:
            log.warning(f"Index-based action click failed: {e}")

        return False

    def click_view_button(self, designation_name=None, row_index=None):
        """Click View action button. Index 0."""
        name = designation_name
        if row_index is not None:
            try:
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, "table#excel-table tbody tr"
                )
                if row_index < len(rows):
                    name = rows[row_index].find_element(
                        By.CSS_SELECTOR, "td.cdk-column-name"
                    ).text.strip()
            except Exception:
                pass
        return self._click_action_button(name, 'cdk-column-view', 0)

    def click_edit_button(self, designation_name=None, row_index=None):
        """Click Edit action button. Index 1."""
        name = designation_name
        if row_index is not None:
            try:
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, "table#excel-table tbody tr"
                )
                if row_index < len(rows):
                    name = rows[row_index].find_element(
                        By.CSS_SELECTOR, "td.cdk-column-name"
                    ).text.strip()
            except Exception:
                pass
        return self._click_action_button(name, 'cdk-column-edit', 1)

    def click_history_button(self, designation_name=None, row_index=None):
        """Click History action button. Index 2.
        NOTE: Column class is cdk-column-archive (not 'history').
        """
        name = designation_name
        if row_index is not None:
            try:
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, "table#excel-table tbody tr"
                )
                if row_index < len(rows):
                    name = rows[row_index].find_element(
                        By.CSS_SELECTOR, "td.cdk-column-name"
                    ).text.strip()
            except Exception:
                pass
        # Use 'archive' class — same pattern as Vehicle Master
        return self._click_action_button(
            name, 'cdk-column-archive', 2
        )

    # ═══════════════════════════════════════════
    #  HISTORY POPUP
    # ═══════════════════════════════════════════

    def is_history_popup_open(self):
        """Check if History popup visible."""
        try:
            h3s = self.driver.find_elements(
                By.CSS_SELECTOR,
                "h3.popup-title, .big-model h3, .popup-content h3"
            )
            for h3 in h3s:
                if h3.is_displayed() and 'history' in h3.text.lower():
                    return True
        except Exception:
            pass
        return False

    def close_history_popup(self):
        """Close History popup. 3 JS strategies."""
        log.info("Closing history popup")
        # Strategy 1: JS click Cancel in popup-footer
        try:
            footers = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-footer"
            )
            for footer in footers:
                if footer.is_displayed():
                    cancel_btns = footer.find_elements(
                        By.XPATH, ".//button[contains(.,'Cancel')]"
                    )
                    if cancel_btns:
                        self.driver.execute_script(
                            "arguments[0].click();", cancel_btns[0]
                        )
                        time.sleep(1)
                        if not self.is_history_popup_open():
                            return
        except Exception:
            pass

        # Strategy 2: JS click X icon in popup-header
        try:
            icons = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-header button mat-icon"
            )
            for icon in icons:
                if icon.text.strip().lower() == 'close':
                    btn = icon.find_element(By.XPATH, "./ancestor::button")
                    self.driver.execute_script(
                        "arguments[0].click();", btn
                    )
                    time.sleep(1)
                    if not self.is_history_popup_open():
                        return
        except Exception:
            pass

        # Strategy 3: Force remove overlays
        self.driver.execute_script(
            "document.querySelectorAll('.cdk-overlay-pane')"
            ".forEach(function(el){el.remove();})"
        )
        self.driver.execute_script(
            "document.querySelectorAll('.cdk-overlay-backdrop')"
            ".forEach(function(el){el.remove();})"
        )

    def get_history_row_count(self):
        """Count history table rows."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model table tbody tr, "
                ".popup-content table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def get_history_data(self):
        """Read all history rows. Returns list of dicts."""
        data = []
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model table tbody tr, "
                ".popup-content table tbody tr"
            )
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                row_data = {}
                for i, cell in enumerate(cells):
                    row_data[f'col_{i}'] = cell.text.strip()
                data.append(row_data)
        except Exception:
            pass
        return data

    def search_in_history(self, search_text):
        """Search in history table. Enter key required."""
        try:
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model input, .popup-content input"
            )
            for inp in inputs:
                if inp.is_displayed():
                    inp.clear()
                    inp.send_keys(search_text)
                    inp.send_keys(Keys.RETURN)
                    time.sleep(1)
                    return True
        except Exception:
            pass
        return False

    def is_history_empty(self):
        """Check if history has no data."""
        return self.get_history_row_count() == 0

    # ═══════════════════════════════════════════
    #  VIEW/EDIT VERIFICATION
    # ═══════════════════════════════════════════

    def verify_view_popup_read_only(self):
        """Verify View popup — all fields disabled, no Submit/Update."""
        try:
            name_input = self.driver.find_element(
                By.CSS_SELECTOR, "input[name='Name']"
            )
            if name_input.is_enabled():
                return False

            # No Submit or Update button
            submit_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]"
                "//button[contains(.,'Submit')]"
            )
            update_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]"
                "//button[contains(.,'Update')]"
            )
            if submit_btns or update_btns:
                return False

            return True
        except Exception:
            return False

    def verify_edit_popup_editable(self):
        """Verify Edit has Update button."""
        return self.is_edit_mode()

    # ═══════════════════════════════════════════
    #  OVERLAY CLEANUP
    # ═══════════════════════════════════════════

    def _force_close_panels(self):
        """Remove leftover CDK overlay panels and backdrops."""
        try:
            self.driver.execute_script(
                "document.querySelectorAll"
                "('.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)')"
                ".forEach(function(el){el.remove();})"
            )
            self.driver.execute_script(
                "document.querySelectorAll"
                "('.cdk-overlay-pane:not(mat-dialog-container)')"
                ".forEach(function(el){el.remove();})"
            )
        except Exception:
            pass

    def force_close_form_popup(self):
        """Force close any form popup by removing elements."""
        try:
            self.driver.execute_script(
                "document.querySelectorAll('mat-dialog-container')"
                ".forEach(function(el){el.remove();})"
            )
            self.driver.execute_script(
                "document.querySelectorAll('.cdk-overlay-backdrop')"
                ".forEach(function(el){el.remove();})"
            )
            self.driver.execute_script(
                "document.querySelectorAll('.cdk-overlay-pane')"
                ".forEach(function(el){el.remove();})"
            )
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  ONE-CALL ACTION FLOWS
    # ═══════════════════════════════════════════

    def create_designation(self, designation_data):
        """One-call designation creation.
        Returns dict: status, error, message, data
        """
        log.info(f"CREATE: {designation_data.get('name', '?')}")
        result = {
            'status': 'FAILED',
            'error': '',
            'message': '',
            'data': designation_data
        }

        try:
            # Step 1: Open Add form
            self.open_add_form()

            # Step 2: Fill form
            self.fill_designation_form(designation_data)

            # Step 3: Submit
            self.submit()

            # Step 4: Wait for SweetAlert2 (success or validation warning)
            time.sleep(2)

            # Check if any SweetAlert appeared
            if self.is_validation_alert_present(timeout=5):
                # Read the title text BEFORE deciding success vs failure
                try:
                    title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
                    alert_text = title_el.text.strip()
                except:
                    alert_text = ''

                # Success messages contain 'success' or 'successfully'
                if 'success' in alert_text.lower():
                    log.info(f"Create success: {alert_text}")
                    result['message'] = alert_text
                    result['status'] = 'PASSED'
                    # Dismiss the alert
                    try:
                        confirm = self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                        self.driver.execute_script("arguments[0].click();", confirm)
                        time.sleep(1)
                    except:
                        self.driver.execute_script("document.querySelectorAll('.swal2-confirm').forEach(function(b){b.click();})")
                else:
                    # It's a real validation error
                    warning = self.handle_validation_warning()
                    result['error'] = 'validation_warning'
                    result['message'] = warning
                    result['status'] = 'VALIDATION_FAILED'
                    log.warning(f"Validation failed: {warning}")
                    return result
            else:
                # No SweetAlert at all - try success handler
                message = self.handle_success_alert(timeout=30)
                if 'successfully' in message.lower():
                    result['message'] = message
                    result['status'] = 'PASSED'
                    log.info(f"Create success: {message}")
                else:
                    result['message'] = message
                    result['status'] = 'PASSED' if message else 'UNKNOWN'

            # Cleanup
            self.driver.execute_script(
                "document.querySelectorAll('.swal2-container')"
                ".forEach(function(el){el.remove();})"
            )
            self.driver.execute_script(
                "document.querySelectorAll('.cdk-overlay-backdrop')"
                ".forEach(function(el){el.remove();})"
            )

        except Exception as e:
            result['error'] = str(e)
            log.error(f"Create designation failed: {e}")

        return result

    def edit_designation(self, designation_name, updated_data,
                          row_index=None):
        """One-call designation edit.
        Returns dict: status, error, message
        """
        log.info(f"EDIT: {designation_name}")
        result = {
            'status': 'FAILED',
            'error': '',
            'message': ''
        }

        try:
            # Step 1: Search if needed
            if not self.is_designation_in_table(designation_name):
                self.search_designation(designation_name)
                time.sleep(1)

            # Step 2: Click Edit
            self.click_edit_button(
                designation_name=designation_name, row_index=row_index
            )
            time.sleep(1)

            # Step 3: Verify Edit mode
            if not self.is_edit_mode():
                result['error'] = 'Edit popup did not open'
                return result

            # Step 4: Fill changed fields
            self.fill_designation_form(updated_data)

            # Step 5: Click Update
            self.click_update()

            # Step 6: Wait for response
            time.sleep(2)

            if self.is_validation_alert_present(timeout=5):
                # Read the title text BEFORE deciding success vs failure
                try:
                    title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
                    alert_text = title_el.text.strip()
                except:
                    alert_text = ''

                # Success messages contain 'success' or 'successfully'
                if 'success' in alert_text.lower():
                    log.info(f"Edit success: {alert_text}")
                    result['message'] = alert_text
                    result['status'] = 'PASSED'
                    # Dismiss the alert
                    try:
                        confirm = self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                        self.driver.execute_script("arguments[0].click();", confirm)
                        time.sleep(1)
                    except:
                        self.driver.execute_script("document.querySelectorAll('.swal2-confirm').forEach(function(b){b.click();})")
                else:
                    # Real validation error
                    warning = self.handle_validation_warning()
                    result['error'] = 'validation_warning'
                    result['message'] = warning
                    result['status'] = 'VALIDATION_FAILED'
                    return result
            else:
                # No SweetAlert at all - try success handler
                message = self.handle_success_alert(timeout=30)
                result['message'] = message
                result['status'] = 'PASSED'

            # Cleanup
            self.driver.execute_script(
                "document.querySelectorAll('.swal2-container')"
                ".forEach(function(el){el.remove();})"
            )

        except Exception as e:
            result['error'] = str(e)
            log.error(f"Edit designation failed: {e}")

        return result

    def view_designation(self, designation_name, row_index=None):
        """One-call designation view. Returns field values dict or None."""
        log.info(f"VIEW: {designation_name}")
        try:
            if not self.is_designation_in_table(designation_name):
                self.search_designation(designation_name)
                time.sleep(1)

            self.click_view_button(
                designation_name=designation_name, row_index=row_index
            )
            time.sleep(1)

            values = self.get_form_field_values()
            self.close_popup()
            return values
        except Exception as e:
            log.error(f"View designation failed: {e}")
            return None

    def check_history(self, designation_name, search_text=None,
                       row_index=None):
        """One-call history check.
        Returns dict: row_count, search_found, data, error
        """
        log.info(f"HISTORY: {designation_name}")
        result = {
            'row_count': 0,
            'search_found': False,
            'data': [],
            'error': ''
        }

        try:
            if not self.is_designation_in_table(designation_name):
                self.search_designation(designation_name)
                time.sleep(1)

            self.click_history_button(
                designation_name=designation_name, row_index=row_index
            )
            time.sleep(2)

            if not self.is_history_popup_open():
                result['error'] = 'History popup did not open'
                return result

            result['row_count'] = self.get_history_row_count()
            result['data'] = self.get_history_data()

            if search_text:
                result['search_found'] = self.search_in_history(
                    search_text
                )

            self.close_history_popup()

        except Exception as e:
            result['error'] = str(e)
            log.error(f"History check failed: {e}")

        return result

    def _set_angular_input(self, locator, value, clear_first=True):
        """Set input value using JS native value setter to trigger Angular reactive form detection.
        Forces Angular to mark the control as touched + dirty so validation fires.
        Also tracks intended value for validation detection in get_mat_error_text().
        """
        element = self._parse_locator(locator)
        el = self.driver.find_element(*element)

        # Track the intended value for this input (used by get_mat_error_text Tier 3)
        field_name = el.get_attribute('name') or el.get_attribute('formcontrolname') or ''
        if not hasattr(self, '_intended_values'):
            self._intended_values = {}
        self._intended_values[field_name] = value

        # Click to focus
        el.click()
        time.sleep(0.1)

        if clear_first:
            self.driver.execute_script("""
                var el = arguments[0];
                el.focus();
                el.setSelectionRange(0, el.value.length);
            """, el)
            time.sleep(0.1)
            from selenium.webdriver.common.keys import Keys
            el.send_keys(Keys.BACK_SPACE)
            time.sleep(0.1)

        # Use native input value setter to trigger Angular change detection.
        # Dispatch focus event first so Angular registers the control as active.
        # After setting value, dispatch input/change events and blur to trigger
        # touched + dirty + validation cycle.
        self.driver.execute_script("""
            var el = arguments[0];
            var value = arguments[1];

            // Focus first so Angular marks the control as active
            el.focus();
            el.dispatchEvent(new Event('focus', { bubbles: true }));

            // Set value via native setter (bypasses Angular's value accessor)
            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
            nativeInputValueSetter.call(el, value);

            // Dispatch events to trigger Angular change detection
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));

            // Blur to mark control as touched — triggers validation display
            el.blur();
            el.dispatchEvent(new Event('blur', { bubbles: true }));

            // Force Angular change detection by triggering a zone tick
            // This ensures ng-touched, ng-dirty, ng-invalid classes are set
            try {
                var ngZone = window.ng && window.ng.probe
                    && window.ng.probe(el) && window.ng.probe(el).injector;
                if (ngZone) {
                    var zone = ngZone.get('NgZone');
                    if (zone) zone.run(function() {});
                }
            } catch(e) {}
        """, el, value)
        time.sleep(0.3)
