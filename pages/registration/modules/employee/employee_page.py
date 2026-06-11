"""
employee_page.py
----------------
Page Object Model for RhythmERP Employee Screen (Flat Form — No Steppers).

Location: Dynamic Screens > Employee
URL:      /#/dynamic-screens/Employee/Employee

FORM LAYOUT (FLAT — verified 2026-06-02 on live app):

  All fields on a single screen (no stepper navigation):
    1. Party Reference      (mat-select, optional) — FK to party_master (excludes Customers)
       Auto-patches: name, email_id, mobile_no when selected
    2. Employee Name         (text input, optional, maxlength=255)
       Validation: ^[A-Za-z ]+$ — letters and spaces only
    3. Email                 (text input, optional, maxlength=255)
       Validation: standard email regex
    4. Phone Number          (integer input, optional)
       Validation: ^[6-9]\\d{9}$ — 10-digit Indian mobile starting with 6-9
    5. Designation           (mat-select, optional) — 56 options
    6. Department            (mat-select, optional) — 0 options currently
    7. Status                (toggle switch, REQUIRED, default=true)

KEY RULES (verified 2026-06-02):
  - FLAT FORM: No steppers, no children array
  - Only `status` is required — all other fields optional
  - party_ref_id auto-fills name, email, mobile when selected
  - Employee Name: letters and spaces only (no numbers, no special chars)
  - Phone: must start with 6-9, exactly 10 digits
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - Dropdown options read dynamically at runtime (never hardcode)
  - Department has 0 options currently — skip in tests

TABLE COLUMNS (main listing):
  - View / Edit  (action buttons per row)
  - Employee Name (name)
  - Email (email_id)
  - Phone Number (mobile_no)
  - Designation
  - Department
  - Status
"""

import os
import sys
import time
import random

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT


class EmployeePage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Employee/Employee"

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[mattooltip='Search']")
    SEARCH_INPUT = ("css", "#erpSearchInput, input.erp-search-input")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    FILTER_BUTTON = ("css", "button.erp-outline-btn")

    # ==============================================================
    #  LOCATORS — Table (main listing)
    # ==============================================================
    TABLE = ("css", "table#excel-table, table.mat-mdc-table, table[mat-table]")
    TABLE_ROWS = ("css", "table#excel-table tbody tr, table.mat-mdc-table tbody tr.mat-mdc-row")
    TABLE_NAME_CELLS = (
        "css",
        "td.cdk-column-name, td.mat-column-name",
    )
    TABLE_EMAIL_CELLS = (
        "css",
        "td.cdk-column-email_id, td.mat-column-email_id",
    )
    TABLE_PHONE_CELLS = (
        "css",
        "td.cdk-column-mobile_no, td.mat-column-mobile_no",
    )
    TABLE_DESIGNATION_CELLS = (
        "css",
        "td.cdk-column-designation, td.mat-column-designation",
    )
    TABLE_STATUS_CELLS = (
        "css",
        "td.cdk-column-status, td.mat-column-status",
    )
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody tr td.no-data, "
        "table.mat-mdc-table tbody tr.mat-mdc-no-data-row, "
        "table.mat-mdc-table tbody tr td.no-data",
    )

    # ==============================================================
    #  LOCATORS — Row action buttons (3-dot menu)
    # ==============================================================
    ROW_MENU_TRIGGER = (
        "css",
        "button.mat-mdc-menu-trigger.erp-row-trigger",
    )
    ROW_MENU_VIEW = (
        "xpath",
        "//div[contains(@class,'mat-mdc-menu-content')]"
        "//button[.//i[contains(@class,'material-icons') and text()='visibility']]"
        "| //div[contains(@class,'mat-mdc-menu-content')]"
        "//span[contains(@class,'erp-menu-title') and text()='View']"
        "/ancestor::button",
    )
    ROW_MENU_EDIT = (
        "xpath",
        "//div[contains(@class,'mat-mdc-menu-content')]"
        "//button[.//i[contains(@class,'material-icons') and text()='edit']]"
        "| //div[contains(@class,'mat-mdc-menu-content')]"
        "//span[contains(@class,'erp-menu-title') and text()='Edit']"
        "/ancestor::button",
    )

    # ==============================================================
    #  LOCATORS — Form popup (FLAT — no steppers)
    # ==============================================================
    FORM_POPUP = (
        "css",
        ".big-model, .edit_pop_up, mat-dialog-container, "
        "div.cdk-overlay-container div.popup-wrapper",
    )
    FORM_HEADING = ("css", ".big-model h3, .edit_pop_up h3, mat-dialog-container h3")

    # ==============================================================
    #  LOCATORS — Form Fields (all on single flat screen)
    # ==============================================================
    PARTY_REFERENCE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Party Reference')]"
        "/ancestor::mat-form-field//mat-select",
    )
    EMPLOYEE_NAME_INPUT = ("css", "input[name='Employee Name']")
    EMAIL_INPUT = ("css", "input[name='Email']")
    PHONE_NUMBER_INPUT = ("css", "input[name='Phone Number']")
    DESIGNATION_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Designation')]"
        "/ancestor::mat-form-field//mat-select",
    )
    DEPARTMENT_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Department')]"
        "/ancestor::mat-form-field//mat-select",
    )
    STATUS_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(.,'Status')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )

    # ==============================================================
    #  LOCATORS — Form buttons (Submit/Cancel/Update)
    # ==============================================================
    SUBMIT_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]",
    )
    UPDATE_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]",
    )
    CANCEL_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]",
    )

    # ==============================================================
    #  LOCATORS — Popup actions
    # ==============================================================
    FULLSCREEN_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-actions')]/button[1]",
    )
    CLOSE_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-actions')]/button[last()]",
    )

    # ==============================================================
    #  LOCATORS — SweetAlert2
    # ==============================================================
    SWAL_TITLE = ("css", "#swal2-title")
    SWAL_HTML = ("css", ".swal2-html-container")
    SWAL_CONFIRM = ("css", ".swal2-confirm")
    SWAL_CANCEL = ("css", ".swal2-cancel")
    SWAL_CONTAINER = ("css", ".swal2-container")

    # ==============================================================
    #  LOCATORS — Validation errors
    # ==============================================================
    MAT_ERROR = ("css", "mat-error, .mat-mdc-form-field-error")
    NG_INVALID_FIELDS = ("css", ".ng-invalid")

    # ==============================================================
    #  LOCATORS — Dropdown overlay
    # ==============================================================
    DROPDOWN_PANEL = (
        "css",
        "div.cdk-overlay-pane mat-select-panel, div[role='listbox']",
    )
    DROPDOWN_OPTIONS = (
        "css",
        "div[role='listbox'] mat-option, div[role='listbox'] [role='option']",
    )
    DROPDOWN_SEARCH = (
        "css",
        "div[role='listbox'] input, .cdk-overlay-pane input[placeholder]",
    )

    # ==============================================================
    #  LOCATORS — Pagination
    # ==============================================================
    ITEMS_PER_PAGE = ("css", "mat-select.mat-mdc-paginator-page-size-select")
    NEXT_PAGE = ("css", "button.mat-mdc-paginator-navigation-next")
    PREV_PAGE = ("css", "button.mat-mdc-paginator-navigation-previous")

    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Employee Screen listing page."""
        log.info("Navigating to Employee Screen page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the Employee listing page is fully loaded."""
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR,
                     "table#excel-table, table.mat-mdc-table, table[mat-table]")
                )
            )
            log.info("Employee table loaded")
        except TimeoutException:
            log.warning("Employee table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn, button.erp-add-btn")
                )
            )
            self.wait_seconds(1)
            log.info("Employee toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the Employee listing page has loaded."""
        return self.is_displayed(self.TABLE, timeout=10)

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS."""
        self.driver.execute_script("""
            document.querySelectorAll(
                'div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)'
            ).forEach(function(el) { el.remove(); });
            document.querySelectorAll(
                'div.cdk-overlay-pane'
            ).forEach(function(el) {
                if (!el.querySelector('mat-dialog-container')) el.remove();
            });
        """)
        self.wait_seconds(0.2)

    def _close_select_panel(self):
        """Try backdrop click first; fall back to JS removal."""
        try:
            backdrops = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)",
            )
            for bd in backdrops:
                try:
                    if bd.is_displayed():
                        bd.click()
                        self.wait_seconds(0.3)
                        return
                except Exception:
                    pass
        except Exception:
            pass

        remaining = self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop), "
            "div.cdk-overlay-pane mat-option",
        )
        if remaining:
            self._force_close_panels()

    def _close_dropdown_panel_only(self):
        """Close an open mat-select dropdown panel WITHOUT sending ESC."""
        self._close_select_panel()

    # ==============================================================
    #  Toolbar actions
    # ==============================================================

    def open_add_form(self):
        """Click the ADD (+) button to open the flat form popup."""
        log.info("Clicking ADD button for Employee...")
        self._wait_for_toolbar()

        # Strategy 1: button.erp-add-btn
        try:
            btn = self.driver.find_element(
                By.CSS_SELECTOR, "button.erp-add-btn"
            )
            if btn.is_displayed():
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1.5)
                if self._is_form_popup_open():
                    self._wait_for_form_content(timeout=5)
                    log.info("ADD form opened via erp-add-btn")
                    return
        except Exception:
            pass

        # Strategy 2: mini-fab with 'add' icon
        try:
            add_btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-mdc-mini-fab"
            )
            for btn in add_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "add" and btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1.5)
                        if self._is_form_popup_open():
                            self._wait_for_form_content(timeout=5)
                            log.info("ADD form opened via mini-fab")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: BasePage click_with_retry
        try:
            self.click_with_retry(self.ADD_BUTTON)
            self.wait_seconds(1.5)
            if self._is_form_popup_open():
                self._wait_for_form_content(timeout=5)
                log.info("ADD form opened via click_with_retry")
                return
        except Exception:
            pass

        raise Exception("ADD button not found or not clickable")

    def _wait_for_toolbar(self):
        """Wait for the toolbar and ADD button to be present and visible."""
        for attempt in range(3):
            try:
                add_container = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.erp-add-btn"
                )
                if add_container and add_container[0].is_displayed():
                    return
            except Exception:
                pass

            try:
                mini_fabs = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.mat-mdc-mini-fab"
                )
                for btn in mini_fabs:
                    try:
                        icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                        if icon.text.strip().lower() == "add":
                            return
                    except Exception:
                        continue
            except Exception:
                pass

            log.info(f"Waiting for toolbar... attempt {attempt + 1}/3")
            self.wait_seconds(2)

        log.warning("Toolbar wait exhausted, ADD button may not be ready")

    def _is_form_popup_open(self):
        """Quick check if any form popup is visible."""
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.big-model, mat-dialog-container, "
                "div.edit_pop_up.override_edit_pop_up.popup-mode, "
                "div.cdk-overlay-container div.popup-wrapper",
            )
            for p in popups:
                try:
                    if p.is_displayed():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def is_add_form_open(self):
        """Public alias for _is_form_popup_open."""
        return self._is_form_popup_open()

    def _wait_for_form_content(self, timeout=5):
        """Wait for form content (inputs) to render inside the popup."""
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.big-model input, "
                    "mat-dialog-container input, "
                    ".edit_pop_up input, "
                    "div.cdk-overlay-container input"
                )
                for el in elements:
                    try:
                        if el.is_displayed():
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
            self.wait_seconds(0.5)

        log.warning(f"Form content did not render within {timeout}s")
        return False

    def click_refresh(self):
        """Click the Refresh button."""
        log.info("Clicking Refresh button...")
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button[mattooltip='Refresh']"
            )
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(2)
                        log.info("Refresh clicked")
                        return
                except Exception:
                    continue
        except Exception:
            pass
        log.warning("Refresh button not found")

    # ==============================================================
    #  Dropdown helper — JS value-setter for Angular form sync
    # ==============================================================

    def _select_mat_option(self, select_locator, value=None):
        """Select an option from a mat-select dropdown.
        Uses JS click + Angular form sync for reliability.

        If value is None, picks a random non-empty option.
        Returns the selected option text, or None on failure.
        """
        self._force_close_panels()

        # Find and click the mat-select trigger
        select_el = self.find_visible_element(select_locator)
        if not select_el:
            log.warning(f"mat-select not found: {select_locator}")
            return None

        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});"
            "arguments[0].click();",
            select_el,
        )
        self.wait_seconds(1)

        # Wait for dropdown panel
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[role='listbox'] mat-option")
                )
            )
        except TimeoutException:
            log.warning("Dropdown options did not appear")
            self._close_dropdown_panel_only()
            return None

        # Get all options
        options = self.driver.find_elements(
            By.CSS_SELECTOR, "div[role='listbox'] mat-option"
        )
        if not options:
            log.warning("No options found in dropdown")
            self._close_dropdown_panel_only()
            return None

        # Pick option
        selected_option = None
        selected_text = None

        if value:
            for opt in options:
                try:
                    opt_text = opt.text.strip()
                    if opt_text.lower() == value.lower():
                        selected_option = opt
                        selected_text = opt_text
                        break
                except Exception:
                    continue
            if not selected_option:
                for opt in options:
                    try:
                        opt_text = opt.text.strip()
                        if value.lower() in opt_text.lower():
                            selected_option = opt
                            selected_text = opt_text
                            break
                    except Exception:
                        continue

        if not selected_option:
            valid_options = []
            for opt in options:
                try:
                    opt_text = opt.text.strip()
                    if opt_text and not opt_text.lower().startswith("select "):
                        valid_options.append((opt, opt_text))
                except Exception:
                    continue

            if not valid_options:
                for opt in options:
                    try:
                        opt_text = opt.text.strip()
                        if opt_text:
                            valid_options.append((opt, opt_text))
                    except Exception:
                        continue

            if valid_options:
                selected_option, selected_text = random.choice(valid_options)
            else:
                log.warning("No valid options to select")
                self._close_dropdown_panel_only()
                return None

        # Click the option via JS
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});"
            "arguments[0].click();",
            selected_option,
        )
        self.wait_seconds(0.5)

        # Close remaining dropdown panel
        self._close_dropdown_panel_only()

        # Sync Angular reactive form model
        self._sync_dropdown_angular_model(select_el)

        log.info(f"Selected dropdown option: {selected_text}")
        return selected_text

    def _sync_dropdown_angular_model(self, select_el):
        """Force Angular reactive form to recognize the dropdown selection."""
        try:
            self.driver.execute_script("""
                var select = arguments[0];
                if (!select) return 'no element';

                select.dispatchEvent(new Event('focusin', { bubbles: true }));
                select.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                }));
                select.dispatchEvent(new Event('change', { bubbles: true }));
                select.dispatchEvent(new Event('input', { bubbles: true }));
                select.dispatchEvent(new KeyboardEvent('keyup', {
                    key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                }));
                select.dispatchEvent(new Event('focusout', { bubbles: true }));
                select.dispatchEvent(new Event('blur', { bubbles: true }));

                select.classList.remove('ng-untouched');
                select.classList.add('ng-touched');
                select.classList.remove('ng-pristine');
                select.classList.add('ng-dirty');

                var valueText = select.querySelector('.mat-mdc-select-value-text');
                var hasValue = valueText && valueText.textContent.trim().length > 0;

                if (hasValue) {
                    select.classList.remove('ng-invalid');
                    select.classList.add('ng-valid');
                }

                return 'synced, hasValue=' + hasValue;
            """, select_el)
        except Exception as e:
            log.warning(f"Angular form model sync failed: {e}")

    # ==============================================================
    #  Toggle switch helper
    # ==============================================================

    def _toggle_switch(self, toggle_locator, target_state=True):
        """Set a toggle switch to the desired state (True=on, False=off)."""
        try:
            toggle_el = self.find_visible_element(toggle_locator)
            if not toggle_el:
                log.warning(f"Toggle switch not found: {toggle_locator}")
                return False

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                toggle_el,
            )
            self.wait_seconds(0.3)

            # Check current state
            is_currently_on = self.driver.execute_script("""
                var wrapper = arguments[0];
                var onLabel = wrapper.querySelector('span.state-label.on');
                if (onLabel && onLabel.classList.contains('active')) return true;
                return false;
            """, toggle_el)

            if is_currently_on != target_state:
                slider = self.driver.execute_script("""
                    var wrapper = arguments[0];
                    var slider = wrapper.querySelector('.slider');
                    return slider || wrapper;
                """, toggle_el)
                self.driver.execute_script("arguments[0].click();", slider)
                self.wait_seconds(0.3)
                log.info(f"Toggle switched to {'ON' if target_state else 'OFF'}")
            else:
                log.info(f"Toggle already {'ON' if target_state else 'OFF'}")

            return True
        except Exception as e:
            log.warning(f"Toggle switch operation failed: {e}")
            return False

    # ==============================================================
    #  Fill ALL fields (flat form — single method)
    # ==============================================================

    def fill_employee_form(self, data):
        """Fill ALL fields on the Employee flat form.

        Since the Employee form is flat (no steppers), all fields are
        filled in a single pass — much simpler than Supplier/Customer.

        Args:
            data: Dict from generate_valid_employee_data() with keys:
                  party_reference, employee_name, email, phone_number,
                  designation, department, status
        """
        log.info("Filling Employee form (flat — no steppers)...")

        # 1. Party Reference (optional — skip if None/empty)
        party_ref = data.get("party_reference")
        if party_ref:
            self._select_mat_option(self.PARTY_REFERENCE_SELECT, party_ref)
            self.wait_seconds(0.5)  # Wait for auto-patch to fill name/email/phone

        # 2. Employee Name (text input)
        employee_name = data.get("employee_name", "")
        if employee_name:
            self.type_text(self.EMPLOYEE_NAME_INPUT, employee_name, clear_first=True)
            self.wait_seconds(0.3)

        # 3. Email (text input)
        email = data.get("email", "")
        if email:
            self.type_text(self.EMAIL_INPUT, email, clear_first=True)
            self.wait_seconds(0.3)

        # 4. Phone Number (number input)
        phone = data.get("phone_number", "")
        if phone:
            self.type_text(self.PHONE_NUMBER_INPUT, str(phone), clear_first=True)
            self.wait_seconds(0.3)

        # 5. Designation (dropdown — optional)
        designation = data.get("designation")
        if designation is None:
            # Auto-pick random from UI
            self._select_mat_option(self.DESIGNATION_SELECT)
        elif designation != "":
            self._select_mat_option(self.DESIGNATION_SELECT, designation)
        self.wait_seconds(0.3)

        # 6. Department (dropdown — 0 options currently, skip)
        department = data.get("department")
        if department:
            self._select_mat_option(self.DEPARTMENT_SELECT, department)
        self.wait_seconds(0.3)

        # 7. Status (toggle — REQUIRED, default=True)
        if "status" in data:
            self._toggle_switch(self.STATUS_TOGGLE, data["status"])

        log.info("Employee form filled (all 7 fields)")

    # ==============================================================
    #  Form submission
    # ==============================================================

    def submit_form(self):
        """Click the Submit button on the Employee form."""
        log.info("Submitting Employee form...")
        try:
            submit_btn = self.find_visible_element(self.SUBMIT_BUTTON)
            if submit_btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    submit_btn,
                )
                self.wait_seconds(1)
                log.info("Submit button clicked")
            else:
                log.warning("Submit button not found")
        except Exception as e:
            log.warning(f"Submit form failed: {e}")

    def cancel_form(self):
        """Click the Cancel button on the Employee form."""
        log.info("Cancelling Employee form...")
        try:
            cancel_btn = self.find_visible_element(self.CANCEL_BUTTON)
            if cancel_btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    cancel_btn,
                )
                self.wait_seconds(1)
                log.info("Cancel button clicked")
        except Exception as e:
            log.warning(f"Cancel form failed: {e}")

    # ==============================================================
    #  SweetAlert2 handling
    # ==============================================================

    def is_success_alert_visible(self):
        """Check if the SweetAlert2 success alert is showing."""
        try:
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            if title_el.is_displayed():
                title = title_el.text.strip().lower()
                return "success" in title or "created" in title or "saved" in title
        except Exception:
            pass
        return False

    def is_validation_alert_visible(self):
        """Check if the SweetAlert2 validation error alert is showing."""
        try:
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            if title_el.is_displayed():
                title = title_el.text.strip().lower()
                return "validation" in title or "error" in title or "failed" in title
        except Exception:
            pass
        return False

    def get_alert_title(self):
        """Get the SweetAlert2 title text."""
        try:
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            if title_el.is_displayed():
                return title_el.text.strip()
        except Exception:
            pass
        return ""

    def get_alert_message(self):
        """Get the SweetAlert2 message text."""
        try:
            msg_el = self.driver.find_element(By.CSS_SELECTOR, ".swal2-html-container")
            if msg_el.is_displayed():
                return msg_el.text.strip()
        except Exception:
            pass
        return ""

    def dismiss_alert(self):
        """Click the confirm button on SweetAlert2 to dismiss."""
        try:
            confirm = self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
            if confirm.is_displayed():
                confirm.click()
                self.wait_seconds(0.5)
        except Exception:
            pass

    # ==============================================================
    #  Validation error detection
    # ==============================================================

    def get_validation_errors(self):
        """Get all visible mat-error messages on the form.

        Returns:
            List of error message strings.
        """
        errors = []
        try:
            error_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
            )
            for el in error_elements:
                try:
                    if el.is_displayed():
                        text = el.text.strip()
                        if text:
                            errors.append(text)
                except Exception:
                    continue
        except Exception:
            pass
        return errors

    def has_validation_errors(self):
        """Check if any validation errors are visible on the form."""
        return len(self.get_validation_errors()) > 0

    # ==============================================================
    #  Table operations
    # ==============================================================

    def get_table_row_count(self):
        """Get the number of data rows in the Employee listing table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody tr, "
                "table.mat-mdc-table tbody tr.mat-mdc-row",
            )
            return len(rows)
        except Exception:
            return 0

    def get_table_employee_names(self):
        """Get all employee names from the listing table.

        Returns:
            List of employee name strings.
        """
        names = []
        try:
            cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "td.cdk-column-name, td.mat-column-name",
            )
            for cell in cells:
                try:
                    text = cell.text.strip()
                    if text:
                        names.append(text)
                except Exception:
                    continue
        except Exception:
            pass
        return names

    def employee_exists_in_table(self, name):
        """Check if an employee with the given name exists in the table."""
        return name in self.get_table_employee_names()

    def search_employee(self, search_text):
        """Search for an employee using the search input.

        Args:
            search_text: The search string to enter.
        """
        log.info(f"Searching for: {search_text}")
        try:
            # Toggle search if needed
            search_input = self.driver.find_elements(
                By.CSS_SELECTOR, "#erpSearchInput, input.erp-search-input"
            )
            if not search_input:
                try:
                    toggle = self.driver.find_element(
                        By.CSS_SELECTOR, "button.search-btn, button[mattooltip='Search']"
                    )
                    toggle.click()
                    self.wait_seconds(0.5)
                except Exception:
                    pass
                search_input = self.driver.find_elements(
                    By.CSS_SELECTOR, "#erpSearchInput, input.erp-search-input"
                )

            if search_input:
                search_input[0].clear()
                search_input[0].send_keys(search_text)
                self.wait_seconds(2)
                log.info(f"Search entered: {search_text}")
        except Exception as e:
            log.warning(f"Search failed: {e}")

    # ==============================================================
    #  Convenience: Full create workflow (UI)
    # ==============================================================

    def create_employee_via_ui(self, data=None):
        """Complete workflow: navigate → add form → fill → submit.

        Args:
            data: Dict from generate_valid_employee_data().
                  If None, generates random data automatically.

        Returns:
            The data dict used for creation (for assertions).
        """
        from pages.registration.modules.employee.data.employee_data import (
            generate_valid_employee_data,
        )

        if data is None:
            data = generate_valid_employee_data()

        self.navigate_to_page()
        self.open_add_form()
        self.fill_employee_form(data)
        self.submit_form()
        self.wait_seconds(2)

        return data

    # ==============================================================
    #  View/Edit operations
    # ==============================================================

    def open_row_menu(self, row_index=0):
        """Click the 3-dot menu trigger on a table row.

        Args:
            row_index: 0-based row index.
        """
        try:
            triggers = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-mdc-menu-trigger.erp-row-trigger"
            )
            if row_index < len(triggers):
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    triggers[row_index],
                )
                self.wait_seconds(0.5)
                log.info(f"Row menu opened for row {row_index}")
        except Exception as e:
            log.warning(f"Row menu open failed: {e}")

    def click_view_from_menu(self):
        """Click the View option from the opened row menu."""
        try:
            view_btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'mat-mdc-menu-content')]"
                "//button[.//i[contains(@class,'material-icons') and text()='visibility']]"
            )
            self.driver.execute_script("arguments[0].click();", view_btn)
            self.wait_seconds(1)
            log.info("View clicked from menu")
        except Exception as e:
            log.warning(f"View click failed: {e}")

    def click_edit_from_menu(self):
        """Click the Edit option from the opened row menu."""
        try:
            edit_btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'mat-mdc-menu-content')]"
                "//button[.//i[contains(@class,'material-icons') and text()='edit']]"
            )
            self.driver.execute_script("arguments[0].click();", edit_btn)
            self.wait_seconds(1)
            log.info("Edit clicked from menu")
        except Exception as e:
            log.warning(f"Edit click failed: {e}")

    # ==============================================================
    #  Form state helpers (for hybrid/UI tests)
    # ==============================================================

    def is_edit_mode(self):
        """Check if the form is in edit mode (Update button present).

        In add mode, only Submit is shown. In edit mode, Update is shown.
        Returns True if Update button is visible, False otherwise.
        """
        try:
            update_btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
            )
            if update_btn.is_displayed():
                return True
        except Exception:
            pass
        return False

    def get_form_field_values(self):
        """Read all field values from the currently open form popup.

        Returns a dict with UI-facing field names as keys:
          - Employee Name, Email, Phone Number
          - Designation (selected text), Department (selected text)
          - Status (True/False)
          - Party Reference (selected text or None)
        """
        values = {}
        try:
            # --- Find the popup container first ---
            # The popup could be .big-model, .edit_pop_up, or mat-dialog-container
            popup_js = """
                var popup = document.querySelector(
                    '.big-model, .edit_pop_up.override_edit_pop_up.popup-mode, '
                    + 'mat-dialog-container, div.cdk-overlay-container div.popup-wrapper'
                );
                return popup;
            """

            # Text inputs — read via JS for Angular Material compatibility
            for field_name, key in [
                ("Employee Name", "Employee Name"),
                ("Email", "Email"),
                ("Phone Number", "Phone Number"),
            ]:
                try:
                    val = self.driver.execute_script(f"""
                        var popup = document.querySelector(
                            '.big-model, .edit_pop_up.override_edit_pop_up.popup-mode, '
                            + 'mat-dialog-container, div.cdk-overlay-container div.popup-wrapper'
                        );
                        if (!popup) return '';
                        var inp = popup.querySelector("input[name='{field_name}']");
                        return inp ? (inp.value || '') : '';
                    """)
                    values[key] = val
                except Exception:
                    values[key] = ""

            # Dropdown values — try multiple strategies for both Edit and View mode
            # In Edit mode: mat-select with .mat-mdc-select-value-text works
            # In View mode: the dropdown may be disabled/readonly, or rendered
            #   as plain text, or the value may be in a sibling element
            for label, key in [
                ("Party Reference", "Party Reference"),
                ("Designation", "Designation"),
                ("Department", "Department"),
            ]:
                try:
                    selected = self.driver.execute_script(f"""
                        var popup = document.querySelector(
                            '.big-model, .edit_pop_up.override_edit_pop_up.popup-mode, '
                            + 'mat-dialog-container, div.cdk-overlay-container div.popup-wrapper'
                        );
                        if (!popup) return '';

                        // Strategy 1: mat-label → mat-form-field → mat-select value text
                        var labels = popup.querySelectorAll('mat-label');
                        for (var i = 0; i < labels.length; i++) {{
                            if (labels[i].textContent.trim().includes('{label}')) {{
                                var field = labels[i].closest('mat-form-field');
                                if (field) {{
                                    // 1a: Standard value text
                                    var vt = field.querySelector('.mat-mdc-select-value-text');
                                    if (vt && vt.textContent.trim()) return vt.textContent.trim();
                                    // 1b: Any span in trigger
                                    var tr = field.querySelector('.mat-mdc-select-trigger span');
                                    if (tr && tr.textContent.trim()) return tr.textContent.trim();
                                    // 1c: Scan all spans in mat-select
                                    var ms = field.querySelector('mat-select');
                                    if (ms) {{
                                        var spans = ms.querySelectorAll('span');
                                        for (var s = 0; s < spans.length; s++) {{
                                            var txt = spans[s].textContent.trim();
                                            if (txt && txt !== '{label}'
                                                && !txt.toLowerCase().startsWith('select')) {{
                                                return txt;
                                            }}
                                        }}
                                    }}
                                    // 1d: .mat-mdc-select-value direct child span
                                    var sv = field.querySelector('.mat-mdc-select-value');
                                    if (sv) {{
                                        var kids = sv.querySelectorAll('span');
                                        for (var k = 0; k < kids.length; k++) {{
                                            var kt = kids[k].textContent.trim();
                                            if (kt && kt !== '{label}'
                                                && !kt.toLowerCase().startsWith('select')) {{
                                                return kt;
                                            }}
                                        }}
                                    }}
                                }}
                                // 1e: Label's parent wrapper — search siblings
                                var parent = labels[i].parentElement;
                                if (parent) {{
                                    // Check sibling elements that might contain the value
                                    var siblings = parent.parentElement
                                        ? parent.parentElement.children
                                        : [];
                                    for (var j = 0; j < siblings.length; j++) {{
                                        if (siblings[j] !== parent && siblings[j] !== labels[i]) {{
                                            var st = siblings[j].textContent.trim();
                                            if (st && st !== '{label}'
                                                && !st.toLowerCase().startsWith('select')
                                                && st.length < 100) {{
                                                return st;
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                        }}

                        // Strategy 2: Look for any element with a label-like text
                        // and read the next sibling or associated value element
                        var allLabels = popup.querySelectorAll(
                            'label, .field-label, .form-label, '
                            + 'span.label, div.label, mat-label'
                        );
                        for (var i = 0; i < allLabels.length; i++) {{
                            if (allLabels[i].textContent.trim().includes('{label}')) {{
                                // Check next sibling
                                var next = allLabels[i].nextElementSibling;
                                if (next) {{
                                    var nt = next.textContent.trim();
                                    if (nt && nt !== '{label}'
                                        && !nt.toLowerCase().startsWith('select')
                                        && nt.length < 100) {{
                                        return nt;
                                    }}
                                }}
                                // Check parent's other children
                                var p = allLabels[i].parentElement;
                                if (p) {{
                                    var pc = p.children;
                                    for (var c = 0; c < pc.length; c++) {{
                                        if (pc[c] !== allLabels[i]) {{
                                            var ct = pc[c].textContent.trim();
                                            if (ct && ct !== '{label}'
                                                && !ct.toLowerCase().startsWith('select')
                                                && ct.length < 100) {{
                                                // Skip if it's another label
                                                if (!pc[c].querySelector('mat-label')
                                                    && pc[c].tagName !== 'LABEL') {{
                                                    return ct;
                                                }}
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                        }}

                        return '';
                    """)
                    values[key] = selected
                except Exception:
                    values[key] = ""

            # Status toggle state
            try:
                is_active = self.driver.execute_script("""
                    var toggle = document.querySelector(
                        'app-slide-toggle-v2 .switch-wrapper'
                    );
                    if (!toggle) return null;
                    var onLabel = toggle.querySelector('span.state-label.on');
                    return onLabel && onLabel.classList.contains('active');
                """)
                values["Status"] = is_active
            except Exception:
                values["Status"] = None

        except Exception as e:
            log.warning(f"Error reading form field values: {e}")

        return values

    def update(self):
        """Click the Update button on the Employee edit form."""
        log.info("Updating Employee form...")
        try:
            update_btn = self.find_visible_element(self.UPDATE_BUTTON)
            if update_btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    update_btn,
                )
                self.wait_seconds(1)
                log.info("Update button clicked")
            else:
                log.warning("Update button not found")
        except Exception as e:
            log.warning(f"Update form failed: {e}")

    def force_close_form_popup(self):
        """Force close any open form popup.

        Strategy order:
          1. Cancel button
          2. Close (X) button
          3. Click dark backdrop
          4. JS removal of all overlays (including dialog containers)
        """
        # Try Cancel button first
        try:
            cancel_btn = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
            )
            if cancel_btn and cancel_btn[0].is_displayed():
                self.driver.execute_script("arguments[0].click();", cancel_btn[0])
                self.wait_seconds(0.5)
                if not self._is_form_popup_open():
                    return
        except Exception:
            pass

        # Try Close (X) button
        try:
            close_btn = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-actions')]/button[last()]"
            )
            if close_btn and close_btn[0].is_displayed():
                self.driver.execute_script("arguments[0].click();", close_btn[0])
                self.wait_seconds(0.5)
                if not self._is_form_popup_open():
                    return
        except Exception:
            pass

        # Try clicking the dark backdrop
        try:
            backdrops = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.cdk-overlay-backdrop.cdk-overlay-dark-backdrop"
            )
            for bd in backdrops:
                try:
                    if bd.is_displayed():
                        self.driver.execute_script("arguments[0].click();", bd)
                        self.wait_seconds(0.5)
                        if not self._is_form_popup_open():
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Nuclear: JS remove ALL overlays including dialog containers
        self.driver.execute_script("""
            document.querySelectorAll(
                'div.cdk-overlay-backdrop'
            ).forEach(function(el) { el.remove(); });
            document.querySelectorAll(
                'div.cdk-overlay-pane'
            ).forEach(function(el) { el.remove(); });
        """)
        self.wait_seconds(0.3)

    # ==============================================================
    #  Cascading dropdown helpers (Agent-pattern search-input strategy)
    # ==============================================================

    def get_dropdown_options_by_label(self, field_label):
        """Open a dropdown by its mat-label text and return all option texts.

        Uses the Agent search-input strategy for cascading dropdowns:
          1. Find the mat-select by label
          2. Click to open
          3. If a search/filter input appears, type a space to trigger loading
          4. Collect all option texts
          5. Close the dropdown panel

        Args:
            field_label: The mat-label text (e.g., "Designation", "Department").

        Returns:
            List of option text strings.
        """
        options_text = []
        self._force_close_panels()

        # Find the mat-select by label
        select_el = self.driver.execute_script(f"""
            var labels = document.querySelectorAll('mat-label');
            for (var i = 0; i < labels.length; i++) {{
                if (labels[i].textContent.trim().includes('{field_label}')) {{
                    var field = labels[i].closest('mat-form-field');
                    if (field) {{
                        return field.querySelector('mat-select');
                    }}
                }}
            }}
            return null;
        """)

        if not select_el:
            log.warning(f"get_dropdown_options: mat-select for '{field_label}' not found")
            return options_text

        # Click to open the dropdown
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});"
            "arguments[0].click();",
            select_el,
        )
        self.wait_seconds(1)

        # Strategy: If there's a search/filter input, type a space to trigger loading
        try:
            search_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[role='listbox'] input, .cdk-overlay-pane input[placeholder]"
            )
            if search_inputs:
                search_inputs[0].send_keys(" ")
                self.wait_seconds(1)
        except Exception:
            pass

        # Wait for options to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[role='listbox'] mat-option")
                )
            )
        except TimeoutException:
            log.warning(f"get_dropdown_options: No options appeared for '{field_label}'")
            self._close_dropdown_panel_only()
            return options_text

        # Collect option texts
        try:
            options = self.driver.find_elements(
                By.CSS_SELECTOR, "div[role='listbox'] mat-option"
            )
            for opt in options:
                try:
                    text = opt.text.strip()
                    if text:
                        options_text.append(text)
                except Exception:
                    continue
        except Exception:
            pass

        # Close the dropdown
        self._close_dropdown_panel_only()

        log.info(f"get_dropdown_options('{field_label}'): found {len(options_text)} options")
        return options_text

    def select_dropdown_by_label(self, field_label, value=None):
        """Select an option from a dropdown by its mat-label text.

        Uses the Agent search-input strategy for cascading dropdowns:
          1. Find the mat-select by label
          2. Click to open
          3. If a search/filter input appears, type the value to filter
          4. Find and click the matching option
          5. Close panel and sync Angular form

        Args:
            field_label: The mat-label text (e.g., "Designation", "Department").
            value:       Option text to select. If None, picks a random option.

        Returns:
            Selected option text, or None on failure.
        """
        self._force_close_panels()

        # Find the mat-select by label
        select_el = self.driver.execute_script(f"""
            var labels = document.querySelectorAll('mat-label');
            for (var i = 0; i < labels.length; i++) {{
                if (labels[i].textContent.trim().includes('{field_label}')) {{
                    var field = labels[i].closest('mat-form-field');
                    if (field) {{
                        return field.querySelector('mat-select');
                    }}
                }}
            }}
            return null;
        """)

        if not select_el:
            log.warning(f"select_dropdown: mat-select for '{field_label}' not found")
            return None

        # Click to open
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});"
            "arguments[0].click();",
            select_el,
        )
        self.wait_seconds(1)

        # Strategy 1: If there's a search/filter input, type the value to filter
        if value:
            try:
                search_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[role='listbox'] input, .cdk-overlay-pane input[placeholder]"
                )
                if search_inputs:
                    search_inputs[0].clear()
                    search_inputs[0].send_keys(value)
                    self.wait_seconds(1)
            except Exception:
                pass

        # Wait for options
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[role='listbox'] mat-option")
                )
            )
        except TimeoutException:
            log.warning(f"select_dropdown: No options for '{field_label}'")
            self._close_dropdown_panel_only()
            return None

        # Find and click the option
        options = self.driver.find_elements(
            By.CSS_SELECTOR, "div[role='listbox'] mat-option"
        )

        selected_option = None
        selected_text = None

        if value:
            # Strategy 2: Exact match
            for opt in options:
                try:
                    opt_text = opt.text.strip()
                    if opt_text.lower() == value.lower():
                        selected_option = opt
                        selected_text = opt_text
                        break
                except Exception:
                    continue

            # Strategy 3: Partial match
            if not selected_option:
                for opt in options:
                    try:
                        opt_text = opt.text.strip()
                        if value.lower() in opt_text.lower():
                            selected_option = opt
                            selected_text = opt_text
                            break
                    except Exception:
                        continue

        # Strategy 4: Pick random valid option
        if not selected_option:
            valid_options = []
            for opt in options:
                try:
                    opt_text = opt.text.strip()
                    if opt_text and not opt_text.lower().startswith("select "):
                        valid_options.append((opt, opt_text))
                except Exception:
                    continue

            if valid_options:
                selected_option, selected_text = random.choice(valid_options)
            else:
                log.warning(f"select_dropdown: No valid options for '{field_label}'")
                self._close_dropdown_panel_only()
                return None

        # Click the option via JS
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});"
            "arguments[0].click();",
            selected_option,
        )
        self.wait_seconds(0.5)

        # Close panel and sync Angular form
        self._close_dropdown_panel_only()
        self._sync_dropdown_angular_model(select_el)

        log.info(f"select_dropdown('{field_label}'): selected '{selected_text}'")
        return selected_text

    # ==============================================================
    #  Additional helpers (Phase 3 hardening)
    # ==============================================================

    def is_field_readonly(self, field_name):
        """Check if a form field is read-only (disabled/readonly attribute).

        Used in View mode verification — fields should be read-only when
        viewing an existing employee record.

        Args:
            field_name: The input name attribute (e.g., 'Employee Name', 'Email').

        Returns:
            True if the field is readonly/disabled, False otherwise.
        """
        try:
            inp = self.driver.find_element(
                By.CSS_SELECTOR, f"input[name='{field_name}']"
            )
            is_readonly = inp.get_attribute("readonly") is not None
            is_disabled = inp.get_attribute("disabled") is not None
            aria_disabled = inp.get_attribute("aria-disabled") == "true"
            # Also check via ng-readonly directive
            ng_readonly = self.driver.execute_script(
                f"""var el = document.querySelector("input[name='{field_name}']");
                return el ? el.hasAttribute('ng-readonly') || el.readOnly : false;"""
            )
            return is_readonly or is_disabled or aria_disabled or ng_readonly
        except Exception:
            return False

    def is_dropdown_readonly(self, field_label):
        """Check if a mat-select dropdown is disabled (read-only in view mode).

        Args:
            field_label: The mat-label text (e.g., 'Designation', 'Department').

        Returns:
            True if the dropdown is disabled, False otherwise.
        """
        try:
            is_disabled = self.driver.execute_script(f"""
                var labels = document.querySelectorAll('mat-label');
                for (var i = 0; i < labels.length; i++) {{
                    if (labels[i].textContent.trim().includes('{field_label}')) {{
                        var field = labels[i].closest('mat-form-field');
                        if (field) {{
                            var select = field.querySelector('mat-select');
                            if (select) {{
                                return select.classList.contains('mat-mdc-select-disabled')
                                    || select.hasAttribute('disabled')
                                    || select.getAttribute('aria-disabled') === 'true';
                            }}
                        }}
                    }}
                }}
                return false;
            """)
            return bool(is_disabled)
        except Exception:
            return False

    def get_table_cell_value(self, row_index, column_name):
        """Get the text value of a specific table cell.

        Args:
            row_index: 0-based row index.
            column_name: CSS column class name (e.g., 'name', 'email_id',
                         'mobile_no', 'designation', 'status').

        Returns:
            Cell text string, or '' if not found.
        """
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody tr, "
                "table.mat-mdc-table tbody tr.mat-mdc-row",
            )
            if row_index < len(rows):
                cell = rows[row_index].find_element(
                    By.CSS_SELECTOR,
                    f"td.cdk-column-{column_name}, td.mat-column-{column_name}"
                )
                return cell.text.strip()
        except Exception:
            pass
        return ""

    def get_table_row_data(self, row_index):
        """Get all visible cell values from a table row.

        Args:
            row_index: 0-based row index.

        Returns:
            Dict with column names as keys, or empty dict if not found.
        """
        data = {}
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody tr, "
                "table.mat-mdc-table tbody tr.mat-mdc-row",
            )
            if row_index < len(rows):
                row = rows[row_index]
                for col in ["name", "email_id", "mobile_no", "designation", "status"]:
                    try:
                        cell = row.find_element(
                            By.CSS_SELECTOR,
                            f"td.cdk-column-{col}, td.mat-column-{col}"
                        )
                        data[col] = cell.text.strip()
                    except Exception:
                        data[col] = ""
        except Exception:
            pass
        return data

    def clear_search(self):
        """Clear the search input and reset the table listing."""
        log.info("Clearing search input...")
        try:
            search_input = self.driver.find_elements(
                By.CSS_SELECTOR, "#erpSearchInput, input.erp-search-input"
            )
            if search_input:
                search_input[0].clear()
                search_input[0].send_keys("\b")  # Trigger Angular change detection
                self.wait_seconds(1)
                log.info("Search input cleared")
        except Exception as e:
            log.warning(f"Clear search failed: {e}")

    def wait_for_table_refresh(self, timeout=10):
        """Wait for the table to reload after refresh/search.

        Args:
            timeout: Max seconds to wait.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR,
                     "table#excel-table, table.mat-mdc-table, table[mat-table]")
                )
            )
            self.wait_seconds(1)
        except TimeoutException:
            log.warning("Table did not refresh within timeout")

    def is_submit_button_visible(self):
        """Check if the Submit button is visible on the form.

        Returns True if in add mode (Submit button present).
        """
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
            )
            return btn.is_displayed()
        except Exception:
            return False

    def is_update_button_visible(self):
        """Check if the Update button is visible on the form.

        Returns True if in edit mode (Update button present).
        """
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
            )
            return btn.is_displayed()
        except Exception:
            return False

    def get_form_heading(self):
        """Get the heading text of the form popup.

        Returns:
            Heading text string, or '' if not found.
        """
        try:
            heading = self.driver.find_element(
                By.CSS_SELECTOR, ".big-model h3, .edit_pop_up h3, mat-dialog-container h3"
            )
            return heading.text.strip()
        except Exception:
            return ""

    def click_close_button(self):
        """Click the Close (X) button on the form popup."""
        log.info("Clicking Close (X) button...")
        try:
            close_btn = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-actions')]/button[last()]"
            )
            if close_btn and close_btn[0].is_displayed():
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    close_btn[0],
                )
                self.wait_seconds(0.5)
                log.info("Close button clicked")
                return
        except Exception:
            pass
        log.warning("Close button not found")

    def get_all_table_data(self):
        """Get all rows from the Employee listing table.

        Returns:
            List of dicts, each with column_name: value pairs.
        """
        all_data = []
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody tr, "
                "table.mat-mdc-table tbody tr.mat-mdc-row",
            )
            for row in rows:
                row_data = {}
                for col in ["name", "email_id", "mobile_no", "designation", "status"]:
                    try:
                        cell = row.find_element(
                            By.CSS_SELECTOR,
                            f"td.cdk-column-{col}, td.mat-column-{col}"
                        )
                        row_data[col] = cell.text.strip()
                    except Exception:
                        row_data[col] = ""
                if any(v for v in row_data.values()):
                    all_data.append(row_data)
        except Exception:
            pass
        return all_data

    def find_employee_row_index(self, name):
        """Find the row index of an employee by name.

        Args:
            name: The employee name to search for.

        Returns:
            0-based row index, or -1 if not found.
        """
        try:
            cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "td.cdk-column-name, td.mat-column-name",
            )
            for i, cell in enumerate(cells):
                try:
                    if cell.text.strip().lower() == name.lower():
                        return i
                except Exception:
                    continue
        except Exception:
            pass
        return -1

    def is_status_active(self, row_index=0):
        """Check if the status column shows Active for a given row.

        Args:
            row_index: 0-based row index.

        Returns:
            True if status shows Active/Yes, False otherwise.
        """
        try:
            status_text = self.get_table_cell_value(row_index, "status")
            if status_text:
                return status_text.lower() in ("active", "yes", "true", "1")
        except Exception:
            pass
        return False
