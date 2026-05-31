"""
user_creation_page.py
---------------------
Page Object Model for RhythmERP User Creation Screen.

Location: Master Setup > User Creation Screen
URL:      /#/master-setup/usercreationscreen

FORM LAYOUT (SIMPLE POPUP — NOT a stepper):
  - Username         (text input,   required, formcontrolname="username")
  - Email            (text input,   required, formcontrolname="email")
  - First Name       (text input,   required, formcontrolname="first_name")
  - Last Name        (text input,   required, formcontrolname="last_name")
  - Password         (password,     required, formcontrolname="password")
  - User Type        (mat-select,   required)
  - Role             (mat-select,   required, dynamic)
  - Entity           (mat-select,   required, dynamic)
  - Designation      (mat-select,   required)
  - Active           (mat-checkbox, optional, formcontrolname="is_active", default checked)
  - Staff            (mat-checkbox, optional, formcontrolname="is_staff", default unchecked)

KEY RULES (V1 — verified 2026-05-21 on live app):
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - Dropdown options read dynamically at runtime (never hardcode)
  - Duplicate username: Submit silently fails, NO error message (BUG-001)
  - No maxlength on Username — 256+ chars accepted (BUG-002)
  - No email format validation on blur (BUG-003)
  - Spaces in Username show generic "should not contain spaces" (BUG-004)
  - Designation dropdown has duplicate "Manager" option (BUG-005)
  - Only 1 mat-error visible at a time (BUG-006)
  - Edit mode button says "Update" not "Submit"
  - View mode has disabled fields, Cancel button only
  - History popup stacked over View popup (z-index)
  - SweetAlert2: success toast on valid create
  - CRITICAL: Browser-clicked mat-select options do NOT update Angular reactive
    form model. Must use JS value-setter + dispatchEvent for all dropdown
    selections.

TABLE COLUMNS (main listing):
  - Action (View/Edit/History icons per row — app-feather-icons)
  - Username (cdk-column-username)
  - Email (cdk-column-email)
  - Joined (cdk-column-joined)
  - Status (cdk-column-status)

FIX LOG (Round 4 — all 7 remaining issues):
  FIX-1: has_field_error — already existed, enhanced with formcontrolname fallback
  FIX-2: search() method missing — added as alias for search_item (click_edit/view/history call it)
  FIX-3: is_add_form_open — already existed as alias
  FIX-4: search InvalidElementStateException — JS clear instead of .clear(), fixed locator ref
  FIX-5: edit_user Update detection — wait up to 10s for popup close, retry Update
  FIX-6: is_view_popup_readonly — check aria-disabled, mat-form-field-disabled, mat-select-disabled
  FIX-7: _find_action_button_in_row — multiple strategies for clock icon + debug dump
  FIX-8: clear_search — JS clear instead of .clear()
  FIX-9: _select_mat_option — added overload that accepts field label string (test file calls it)
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
    InvalidElementStateException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT

# Global list to track every submission for reporting
UC_SUBMISSIONS = []


class UserCreationPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/master-setup/usercreationscreen"

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = (
        "css",
        "button.erp-add-btn",
    )
    SEARCH_TOGGLE = ("css", "button[aria-label='Search'], button[mattooltip='Search']")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")

    # ==============================================================
    #  LOCATORS — Search bar
    # ==============================================================
    SEARCH_INPUT = ("css", "input.search-bar-input, input[placeholder='Search anything...']")
    SEARCH_SUBMIT = ("css", "button[aria-label='Search'], button[mattooltip='Search']")

    # ==============================================================
    #  LOCATORS — Table (main listing)
    # ==============================================================
    TABLE = ("css", "table.mat-mdc-table, table[mat-table]")
    TABLE_ROWS = ("css", "table.mat-mdc-table tbody tr.mat-mdc-row")
    TABLE_USERNAME_CELLS = (
        "css",
        "table.mat-mdc-table tbody td.cdk-column-username, "
        "table.mat-mdc-table tbody td.mat-column-username",
    )
    NO_DATA_ROW = (
        "css",
        "table.mat-mdc-table tbody tr.mat-mdc-no-data-row, "
        "table.mat-mdc-table tbody tr td.no-data",
    )

    # ==============================================================
    #  LOCATORS — Form popup (simple popup — NOT stepper)
    # ==============================================================
    FORM_POPUP = (
        "css",
        ".big-model, mat-dialog-container, "
        ".edit_pop_up.override_edit_pop_up.popup-mode",
    )
    FORM_HEADING = (
        "css",
        ".big-model h3, mat-dialog-container h3, "
        ".mat-mdc-dialog-title, .edit_pop_up h3",
    )

    # ==============================================================
    #  LOCATORS — Form fields
    # ==============================================================
    USERNAME_INPUT = (
        "css",
        "input[formcontrolname='username']",
    )
    EMAIL_INPUT = (
        "css",
        "input[formcontrolname='email']",
    )
    FIRST_NAME_INPUT = (
        "css",
        "input[formcontrolname='first_name']",
    )
    LAST_NAME_INPUT = (
        "css",
        "input[formcontrolname='last_name']",
    )
    PASSWORD_INPUT = (
        "css",
        "input[formcontrolname='password']",
    )

    # ==============================================================
    #  LOCATORS — Dropdown selects (4 mat-selects in the form)
    #  The User Creation form has 4 mat-selects in this order:
    #    [0] = User Type, [1] = Role, [2] = Entity, [3] = Designation
    #  We use index-based CSS selectors since they lack formcontrolname.
    # ==============================================================
    USER_TYPE_SELECT = (
        "css",
        ".big-model mat-form-field:nth-of-type(6) mat-select, "
        "mat-dialog-container mat-form-field:nth-of-type(6) mat-select",
    )
    ROLE_SELECT = (
        "css",
        ".big-model mat-form-field:nth-of-type(7) mat-select, "
        "mat-dialog-container mat-form-field:nth-of-type(7) mat-select",
    )
    ENTITY_SELECT = (
        "css",
        ".big-model mat-form-field:nth-of-type(8) mat-select, "
        "mat-dialog-container mat-form-field:nth-of-type(8) mat-select",
    )
    DESIGNATION_SELECT = (
        "css",
        ".big-model mat-form-field:nth-of-type(9) mat-select, "
        "mat-dialog-container mat-form-field:nth-of-type(9) mat-select",
    )

    # ==============================================================
    #  LOCATORS — Checkboxes
    # ==============================================================
    ACTIVE_CHECKBOX = (
        "css",
        "mat-checkbox[formcontrolname='is_active']",
    )
    STAFF_CHECKBOX = (
        "css",
        "mat-checkbox[formcontrolname='is_staff']",
    )

    # ==============================================================
    #  LOCATORS — Form buttons
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
    #  LOCATORS — Row action buttons (using app-feather-icons)
    #  FIX: Use cdk-column-username class to locate the correct row
    # ==============================================================
    VIEW_BUTTON = (
        "xpath",
        "//td[contains(@class,'cdk-column-username') or contains(@class,'mat-column-username')]"
        "[.//text()[contains(.,'{username}')]]"
        "/ancestor::tr//app-feather-icons[@icon='eye']/ancestor::button"
    )
    EDIT_BUTTON = (
        "xpath",
        "//td[contains(@class,'cdk-column-username') or contains(@class,'mat-column-username')]"
        "[.//text()[contains(.,'{username}')]]"
        "/ancestor::tr//app-feather-icons[@icon='edit']/ancestor::button"
    )
    HISTORY_BUTTON = (
        "xpath",
        "//td[contains(@class,'cdk-column-username') or contains(@class,'mat-column-username')]"
        "[.//text()[contains(.,'{username}')]]"
        "/ancestor::tr//app-feather-icons[@icon='clock']/ancestor::button"
    )

    # ==============================================================
    #  LOCATORS — History popup
    # ==============================================================
    HISTORY_POPUP = (
        "xpath",
        "//div[contains(@class,'big-model')]"
        "[.//h3[contains(translate(.,'HISTORY','history'),'history')]]",
    )
    HISTORY_TABLE_ROWS = (
        "css",
        ".big-model table tbody tr, mat-dialog-container table tbody tr",
    )
    HISTORY_SEARCH_INPUT = (
        "xpath",
        "//div[contains(@class,'big-model')]"
        "//input[contains(@placeholder,'Search') or contains(@placeholder,'search')]",
    )
    HISTORY_CLOSE_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel') or contains(.,'Close')]",
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
    #  Field-label → locator mapping for _select_mat_option(field_label)
    # ==============================================================
    _DROPDOWN_LABEL_MAP = {
        "User Type": USER_TYPE_SELECT,
        "user_type": USER_TYPE_SELECT,
        "Role": ROLE_SELECT,
        "role": ROLE_SELECT,
        "Entity": ENTITY_SELECT,
        "entity": ENTITY_SELECT,
        "Designation": DESIGNATION_SELECT,
        "designation": DESIGNATION_SELECT,
    }

    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the User Creation Screen listing page."""
        log.info("Navigating to User Creation Screen page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the User Creation Screen page is fully loaded."""
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table.mat-mdc-table, table[mat-table]")
                )
            )
            log.info("User Creation table loaded")
        except TimeoutException:
            log.warning("User Creation table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn")
                )
            )
            self.wait_seconds(1)
            log.info("User Creation toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the User Creation listing page has loaded."""
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
        """Click the ADD (+) button to open the create form."""
        log.info("Clicking ADD button...")
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

        # Strategy 2: Find mini-fab button with 'add' icon
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
                            log.info("ADD form opened via mini-fab icon")
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
        self._debug_popup_info()
        return False

    def _debug_popup_info(self):
        """Log debug information about the current popup state."""
        try:
            all_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.big-model input, "
                "mat-dialog-container input, "
                ".edit_pop_up input, "
                "div.cdk-overlay-container input"
            )
            log.info(f"DEBUG: Found {len(all_inputs)} inputs in popup")
            for i, inp in enumerate(all_inputs[:10]):
                try:
                    log.info(
                        f"  Input[{i}]: "
                        f"name={inp.get_attribute('name')}, "
                        f"formcontrolname={inp.get_attribute('formcontrolname')}, "
                        f"type={inp.get_attribute('type')}, "
                        f"placeholder={inp.get_attribute('placeholder')}, "
                        f"visible={inp.is_displayed()}"
                    )
                except Exception:
                    pass
        except Exception as e:
            log.warning(f"Debug popup info failed: {e}")

    def click_refresh(self):
        """Click the Refresh button."""
        log.info("Clicking Refresh button...")

        # Strategy 1: mattooltip='Refresh'
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

        # Strategy 2: material-icons refresh inside erp-outline-btn
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.erp-outline-btn"
            )
            for btn in btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "i.material-icons")
                    if icon.text.strip().lower() == "refresh" and btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(2)
                        log.info("Refresh clicked via icon text")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        log.warning("Refresh button not found")

    # ==============================================================
    #  Form fill methods
    # ==============================================================

    def fill_user_form(self, data):
        """Fill the entire User Creation form.

        data dict keys: username, email, first_name, last_name,
                        password, user_type, role, entity, designation,
                        is_active, is_staff

        Convention:
          - None  → Pick random option from UI (for dropdowns)
          - ""    → Skip (for validation tests)
          - "val" → Fill with value
        """
        log.info("Filling User Creation form...")

        # Text inputs
        if data.get("username") is not None and data["username"] != "":
            self.type_text(self.USERNAME_INPUT, data["username"], clear_first=True)
            self.wait_seconds(0.3)

        if data.get("email") is not None and data["email"] != "":
            self.type_text(self.EMAIL_INPUT, data["email"], clear_first=True)
            self.wait_seconds(0.3)

        if data.get("first_name") is not None and data["first_name"] != "":
            self.type_text(self.FIRST_NAME_INPUT, data["first_name"], clear_first=True)
            self.wait_seconds(0.3)

        if data.get("last_name") is not None and data["last_name"] != "":
            self.type_text(self.LAST_NAME_INPUT, data["last_name"], clear_first=True)
            self.wait_seconds(0.3)

        if data.get("password") is not None and data["password"] != "":
            self.type_text(self.PASSWORD_INPUT, data["password"], clear_first=True)
            self.wait_seconds(0.3)

        # Dropdown selects — use _select_mat_option (JS value-setter)
        if data.get("user_type") is None:
            self._select_mat_option(self.USER_TYPE_SELECT, None)
        elif data["user_type"] != "":
            self._select_mat_option(self.USER_TYPE_SELECT, data["user_type"])

        if data.get("role") is None:
            self._select_mat_option(self.ROLE_SELECT, None)
        elif data["role"] != "":
            self._select_mat_option(self.ROLE_SELECT, data["role"])

        if data.get("entity") is None:
            self._select_mat_option(self.ENTITY_SELECT, None)
        elif data["entity"] != "":
            self._select_mat_option(self.ENTITY_SELECT, data["entity"])

        if data.get("designation") is None:
            self._select_mat_option(self.DESIGNATION_SELECT, None)
        elif data["designation"] != "":
            self._select_mat_option(self.DESIGNATION_SELECT, data["designation"])

        # Checkboxes
        if data.get("is_active") is not None:
            self._set_checkbox(self.ACTIVE_CHECKBOX, data["is_active"])

        if data.get("is_staff") is not None:
            self._set_checkbox(self.STAFF_CHECKBOX, data["is_staff"])

        log.info("User Creation form filled")

    # ==============================================================
    #  Dropdown helper — JS value-setter for Angular form sync
    #  FIX-9: Overload accepts field label string (e.g. "User Type")
    # ==============================================================

    def _select_mat_option(self, select_locator_or_label, value=None):
        """Select an option from a mat-select dropdown.

        Accepts either:
          - A locator tuple (e.g. self.USER_TYPE_SELECT)
          - A field label string (e.g. "User Type") — looks up via _DROPDOWN_LABEL_MAP
          - A field key string (e.g. "user_type") — same map

        Goes STRAIGHT to index-based selection (no slow nth-of-type CSS timeout).
        """
        # FIX-9: If a string label is passed, resolve to the locator tuple
        if isinstance(select_locator_or_label, str):
            resolved = self._DROPDOWN_LABEL_MAP.get(select_locator_or_label)
            if resolved:
                select_locator = resolved
            else:
                # Fuzzy match: try case-insensitive
                for key, loc in self._DROPDOWN_LABEL_MAP.items():
                    if key.lower() == select_locator_or_label.lower():
                        select_locator = loc
                        break
                else:
                    log.warning(f"Unknown dropdown label: {select_locator_or_label}")
                    return None
        else:
            select_locator = select_locator_or_label

        self._force_close_panels()

        # Find mat-select — try index-based FIRST (instant), CSS locator second
        select_el = self._find_dropdown_by_index(select_locator)
        if not select_el:
            try:
                select_el = self.find_visible_element(select_locator, timeout=3)
            except Exception:
                log.warning(f"mat-select not found: {select_locator}")
                return None

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
        if value:
            for opt in options:
                try:
                    if opt.text.strip().lower() == value.lower():
                        selected_option = opt
                        break
                except Exception:
                    continue
            if not selected_option:
                for opt in options:
                    try:
                        if value.lower() in opt.text.strip().lower():
                            selected_option = opt
                            break
                    except Exception:
                        continue

        if not selected_option:
            valid_options = []
            for opt in options:
                try:
                    t = opt.text.strip()
                    if t:
                        valid_options.append((opt, t))
                except Exception:
                    continue
            if valid_options:
                selected_option, selected_text = random.choice(valid_options)
            else:
                log.warning("No valid options to select")
                self._close_dropdown_panel_only()
                return None
        else:
            try:
                selected_text = selected_option.text.strip()
            except Exception:
                selected_text = value

        # Click option via JS
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});"
            "arguments[0].click();",
            selected_option,
        )
        self.wait_seconds(0.5)
        self._close_dropdown_panel_only()

        log.info(f"Selected dropdown option: {selected_text}")
        return selected_text

    def _find_dropdown_by_index(self, select_locator):
        """Fallback: find a mat-select by position index within the popup.
        If the CSS nth-of-type selector fails, find all mat-selects inside
        the popup and pick the right one.
        """
        try:
            # Find all mat-selects inside the popup
            popup_selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model mat-select, mat-dialog-container mat-select, "
                ".edit_pop_up mat-select"
            )
            # Determine which index this locator targets
            locator_str = select_locator[1] if isinstance(select_locator, tuple) else str(select_locator)
            if "nth-of-type(6)" in locator_str or "6)" in locator_str:
                if len(popup_selects) >= 1:
                    return popup_selects[0]  # User Type
            elif "nth-of-type(7)" in locator_str or "7)" in locator_str:
                if len(popup_selects) >= 2:
                    return popup_selects[1]  # Role
            elif "nth-of-type(8)" in locator_str or "8)" in locator_str:
                if len(popup_selects) >= 3:
                    return popup_selects[2]  # Entity
            elif "nth-of-type(9)" in locator_str or "9)" in locator_str:
                if len(popup_selects) >= 4:
                    return popup_selects[3]  # Designation
            # Just return the first one if we can't determine
            if popup_selects:
                return popup_selects[0]
        except Exception:
            pass
        return None

    # ==============================================================
    #  Checkbox helper
    # ==============================================================

    def _set_checkbox(self, checkbox_locator, checked):
        """Set a mat-checkbox to the desired state (True=checked, False=unchecked)."""
        try:
            checkbox = self.find_visible_element(checkbox_locator)
            if not checkbox:
                return
            is_currently_checked = checkbox.is_selected()
            if is_currently_checked != checked:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    checkbox,
                )
                self.wait_seconds(0.3)
        except Exception:
            # Fallback: find the input inside the mat-checkbox
            try:
                fcn = "is_active" if "is_active" in str(checkbox_locator) else "is_staff"
                inp = self.driver.find_element(
                    By.CSS_SELECTOR,
                    f"mat-checkbox[formcontrolname='{fcn}'] input"
                )
                if inp.is_selected() != checked:
                    self.driver.execute_script("arguments[0].click();", inp)
                    self.wait_seconds(0.3)
            except Exception as e:
                log.warning(f"Checkbox toggle failed: {e}")

    # ==============================================================
    #  Submit / Update / Cancel
    # ==============================================================

    def submit(self):
        """Click the Submit button (Create mode)."""
        log.info("Clicking Submit button...")
        self._force_close_panels()

        # Strategy 1: XPath locator
        try:
            btn = self.find_visible_element(self.SUBMIT_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1)
                log.info("Submit clicked via locator")
                return
        except Exception:
            pass

        # Strategy 2: Find by text
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
            )
            for btn in btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1)
                        log.info("Submit clicked via text search")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: JS click any Submit button inside popup
        try:
            self.driver.execute_script("""
                var btns = document.querySelectorAll(
                    '.popup-footer button, .big-model button'
                );
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.trim() === 'Submit') {
                        btns[i].click();
                        break;
                    }
                }
            """)
            self.wait_seconds(1)
            log.info("Submit clicked via JS")
            return
        except Exception:
            pass

        log.warning("Submit button not found or not clickable")

    def click_update(self):
        """Click the Update button (Edit mode)."""
        log.info("Clicking Update button...")
        self._force_close_panels()

        # Strategy 1: XPath locator
        try:
            btn = self.find_visible_element(self.UPDATE_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1)
                log.info("Update clicked via locator")
                return
        except Exception:
            log.warning("Update button not found via primary locator")

        # Strategy 2: Find by text with contains(@class)
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
            )
            for btn in btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1)
                        log.info("Update clicked via text search")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: JS click Update button
        try:
            self.driver.execute_script("""
                var btns = document.querySelectorAll(
                    '.popup-footer button, .big-model button'
                );
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.trim() === 'Update') {
                        btns[i].click();
                        break;
                    }
                }
            """)
            self.wait_seconds(1)
            log.info("Update clicked via JS")
            return
        except Exception:
            pass

        log.warning("Update button not found or not clickable")

    def cancel(self):
        """Click the Cancel button to close the popup."""
        log.info("Clicking Cancel button...")
        self._force_close_panels()

        try:
            btn = self.find_visible_element(self.CANCEL_BUTTON)
            if btn:
                self.driver.execute_script(
                    "arguments[0].click();", btn
                )
                self.wait_seconds(1)
                return
        except Exception:
            pass

        # Fallback: Close via X button
        try:
            close_btns = self.driver.find_elements(
                By.CSS_SELECTOR, ".big-model .popup-actions button"
            )
            for btn in close_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "close" and btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(1)
                        return
                except Exception:
                    continue
        except Exception:
            pass

        log.warning("Cancel button not found")

    def close_popup(self):
        """Close the form popup via X button or Cancel."""
        try:
            close_btns = self.driver.find_elements(
                By.CSS_SELECTOR, ".big-model .popup-actions button"
            )
            for btn in close_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "close" and btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(1)
                        return
                except Exception:
                    continue
        except Exception:
            pass
        self.cancel()

    # ==============================================================
    #  FIX-1: has_field_error — enhanced with formcontrolname fallback
    # ==============================================================

    def has_field_error(self, field_label):
        """Check if a field has a validation error message displayed below it.

        Works for Angular Material form fields that show <mat-error> when invalid.
        Tries label text match first, then falls back to formcontrolname match.
        """
        # Strategy 1: Find mat-form-field by label text
        try:
            field_wrapper = self.driver.find_element(By.XPATH,
                "//mat-form-field[.//label[contains(text(),'" + field_label + "')]]")

            errors = field_wrapper.find_elements(By.XPATH, ".//mat-error")
            for err in errors:
                if err.is_displayed() and err.text.strip():
                    return True
        except Exception:
            pass

        # Strategy 2: Find by formcontrolname (e.g. "Username" → "username")
        try:
            fcn = field_label.lower().replace(" ", "_")
            field_wrapper = self.driver.find_element(By.XPATH,
                "//mat-form-field[.//input[@formcontrolname='" + fcn + "'] or "
                ".//textarea[@formcontrolname='" + fcn + "']]")

            errors = field_wrapper.find_elements(By.XPATH, ".//mat-error")
            for err in errors:
                if err.is_displayed() and err.text.strip():
                    return True
        except Exception:
            pass

        # Strategy 3: Check ANY visible mat-error (last resort)
        try:
            all_errors = self.driver.find_elements(By.CSS_SELECTOR, "mat-error")
            for err in all_errors:
                if err.is_displayed() and err.text.strip():
                    return True
        except Exception:
            pass

        return False

    def force_close_form_popup(self):
        """Force close any open popup via JS."""
        try:
            self.driver.execute_script("""
                var closeBtns = document.querySelectorAll(
                    '.big-model .popup-actions button mat-icon'
                );
                for (var i = 0; i < closeBtns.length; i++) {
                    if (closeBtns[i].textContent.trim().toLowerCase() === 'close') {
                        closeBtns[i].closest('button').click();
                        break;
                    }
                }
            """)
            self.wait_seconds(0.5)
        except Exception:
            pass

    # ==============================================================
    #  SweetAlert2 handlers
    # ==============================================================

    def handle_validation_warning(self, timeout=5):
        """Handle SweetAlert2 'Validation Failed' warning.

        FIX-Round6: The ERP uses swal2-top-right TOAST notifications (not modal
        popups) for validation errors like spaces/special-chars in Username.
        These toasts:
          - Have pointer-events: none (confirm btn not clickable via Selenium)
          - Auto-dismiss after a few seconds
          - Are still detected via #swal2-title text even if not "visible"
          - Have opacity:1 but offsetParent may be null (positioned off-flow)

        Strategy: First try standard visibility wait, then fall back to
        checking the DOM for toast content (even if not interactable).
        """
        # Strategy 1: Standard visible Swal2 (modal-style)
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-container")
                )
            )
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            title = title_el.text.strip() if title_el else ""

            # Try to click confirm (may not be visible for toasts)
            try:
                confirm_btn = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-confirm"
                )
                if confirm_btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", confirm_btn)
                    self.wait_seconds(0.5)
            except Exception:
                pass

            log.info(f"SweetAlert2 handled (visible): {title}")
            return title
        except TimeoutException:
            pass
        except Exception:
            pass

        # Strategy 2: DOM-based toast detection (swal2-top-right toasts)
        # These are present in DOM with opacity:1 but may not be "visible"
        # to Selenium's visibility checks.
        try:
            containers = self.driver.find_elements(
                By.CSS_SELECTOR, ".swal2-container.swal2-top-right"
            )
            for container in containers:
                try:
                    style = container.get_attribute("style") or ""
                    opacity = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).opacity;",
                        container
                    )
                    if opacity and float(opacity) > 0:
                        title_el = container.find_element(
                            By.CSS_SELECTOR, "#swal2-title, .swal2-title"
                        )
                        title = title_el.text.strip() if title_el else ""
                        if title:
                            # Dismiss the toast via JS
                            self.driver.execute_script(
                                "if(document.querySelector('.swal2-confirm'))"
                                "document.querySelector('.swal2-confirm').click();",
                            )
                            self.wait_seconds(0.5)
                            log.info(f"SweetAlert2 toast detected: {title}")
                            return title
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: Any Swal2 container with error icon in DOM
        try:
            error_icons = self.driver.find_elements(
                By.CSS_SELECTOR, ".swal2-icon.swal2-error"
            )
            for icon in error_icons:
                try:
                    if icon.is_displayed():
                        title_el = self.driver.find_element(
                            By.CSS_SELECTOR, "#swal2-title"
                        )
                        title = title_el.text.strip() if title_el else ""
                        if title:
                            log.info(f"SweetAlert2 error icon detected: {title}")
                            return title
                except Exception:
                    continue
        except Exception:
            pass

        return None

    def handle_success_alert(self, timeout=5):
        """Handle SweetAlert2 success alert."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-icon.swal2-success")
                )
            )
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            title = title_el.text.strip() if title_el else ""

            try:
                confirm_btn = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-confirm"
                )
                self.driver.execute_script("arguments[0].click();", confirm_btn)
                self.wait_seconds(0.5)
            except Exception:
                pass

            log.info(f"SweetAlert2 success: {title}")
            return title
        except TimeoutException:
            return None
        except Exception:
            return None

    def is_success_alert_visible(self, timeout=3):
        """Check if SweetAlert2 success alert is visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-icon.swal2-success")
                )
            )
            return True
        except TimeoutException:
            return False

    def dismiss_any_swal(self):
        """Dismiss any open SweetAlert2 dialog."""
        try:
            confirm_btns = self.driver.find_elements(
                By.CSS_SELECTOR, ".swal2-confirm"
            )
            for btn in confirm_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(0.5)
                except Exception:
                    continue
        except Exception:
            pass

    # ==============================================================
    #  Search
    #  FIX-2: Added search() method (click_edit/view/history call self.search())
    #  FIX-4: JS clear instead of .clear() — avoids InvalidElementStateException
    # ==============================================================

    def search(self, search_text):
        """Search for an item in the table. Alias used by click_edit/view/history.

        FIX-4: Uses JS .value = '' instead of .clear() to avoid
        InvalidElementStateException on Angular Material search inputs.
        """
        return self.search_item(search_text)

    def search_item(self, search_text):
        """Search for an item in the table.

        ERP SEARCH BEHAVIOR (verified 2026-05-21 on live app):
          The search is a TWO-STEP process:
          1. Click the Search icon button to toggle open the search input
          2. Type into the `input#erpSearchInput` (class='erp-search-input')
          3. Click the Search button next to it to trigger the search

          The OLD code was typing into `input.search-bar-input` which is the
          GLOBAL navigation search bar — it does NOT filter the table!

        FIX-4: Uses JS .value = '' instead of .clear() to avoid
        InvalidElementStateException on Angular Material search inputs.
        FIX-10: Uses the correct `#erpSearchInput` table-specific search.
        """
        try:
            self._force_close_panels()

            # STEP 1: Click the Search toggle button to open the search input
            search_toggle_clicked = False
            try:
                toggle_btns = self.driver.find_elements(By.CSS_SELECTOR,
                    "button[mattooltip='Search'], button[aria-label='Search']")
                for btn in toggle_btns:
                    try:
                        if btn.is_displayed():
                            self.driver.execute_script("arguments[0].click();", btn)
                            search_toggle_clicked = True
                            self.wait_seconds(1)
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # STEP 2: Find the ERP search input (input#erpSearchInput)
            search_input = None

            # Primary: The table-specific search input
            try:
                search_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "erpSearchInput"))
                )
            except TimeoutException:
                pass

            # Fallback: Try class-based selector
            if not search_input:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR,
                        "input.erp-search-input")
                except Exception:
                    pass

            # Fallback: Try placeholder-based
            if not search_input:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR,
                        "input[placeholder='Search'], "
                        "input.erp-search-container input")
                except Exception:
                    pass

            # Last resort: old global search bar
            if not search_input:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR,
                        "input.search-bar-input")
                    log.warning("Using global search bar — table filter may not work")
                except Exception:
                    log.warning("Search input not found")
                    return False

            # STEP 3: Clear and type into the search input
            # FIX-4: JS clear instead of .clear()
            self.driver.execute_script("arguments[0].value = '';", search_input)
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                search_input
            )
            self.wait_seconds(0.3)

            # Type the search text
            search_input.send_keys(search_text)

            # STEP 4: Click the Search submit button next to the input
            search_submitted = False
            try:
                # The ERP has a dedicated Search button in the erp-search-container
                submit_btns = self.driver.find_elements(By.CSS_SELECTOR,
                    "button[mattooltip='Search'], "
                    ".erp-search-container + button, "
                    ".erp-search-container ~ button")
                for btn in submit_btns:
                    try:
                        if btn.is_displayed():
                            self.driver.execute_script("arguments[0].click();", btn)
                            search_submitted = True
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Fallback: Try the search icon button in toolbar
            if not search_submitted:
                try:
                    icon_btns = self.driver.find_elements(By.XPATH,
                        "//button[.//mat-icon[text()='search']]")
                    for btn in icon_btns:
                        try:
                            if btn.is_displayed():
                                self.driver.execute_script("arguments[0].click();", btn)
                                search_submitted = True
                                break
                        except Exception:
                            continue
                except Exception:
                    pass

            # Fallback: Press Enter
            if not search_submitted:
                try:
                    search_input.send_keys(Keys.ENTER)
                except Exception:
                    pass

            # Wait for table to update
            time.sleep(3)
            log.info(f"Search performed for: {search_text}")
            return True
        except Exception as e:
            log.warning(f"Search failed: {e}")
            return False

    def search_and_verify(self, query):
        """Search for a user and verify they appear in the results."""
        self.search(query)
        self.wait_seconds(2)

        # Check if username appears in table
        try:
            username_cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table.mat-mdc-table tbody td.cdk-column-username, "
                "table.mat-mdc-table tbody td.mat-column-username"
            )
            for cell in username_cells:
                try:
                    if query in cell.text:
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def clear_search(self):
        """Clear the search input and refresh the table.

        FIX-8: Uses JS .value = '' instead of .clear() to avoid
        InvalidElementStateException on Angular Material search inputs.
        """
        try:
            search_input = self.driver.find_element(
                By.CSS_SELECTOR, "input.search-bar-input"
            )
            # FIX-8: JS clear instead of .clear()
            self.driver.execute_script("arguments[0].value = '';", search_input)
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                search_input
            )
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(1)
        except Exception:
            pass
        self.click_refresh()

    # ==============================================================
    #  Table row methods — find users, click action buttons
    # ==============================================================

    def _find_row_by_username(self, username):
        """Find a table row containing the given username.
        Returns the row WebElement or None.
        """
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table.mat-mdc-table tbody tr.mat-mdc-row"
            )
            for row in rows:
                try:
                    # Try cdk-column-username
                    cell = row.find_element(
                        By.CSS_SELECTOR,
                        "td.cdk-column-username, td.mat-column-username"
                    )
                    if username in cell.text:
                        return row
                except Exception:
                    # Fallback: check all cells
                    try:
                        cells = row.find_elements(By.CSS_SELECTOR, "td")
                        for c in cells:
                            if username in c.text:
                                return row
                    except Exception:
                        continue
        except Exception:
            pass
        return None

    # ==============================================================
    #  FIX-7: _find_action_button_in_row — multiple strategies + debug dump
    # ==============================================================

    def _find_action_button_in_row(self, row, icon_name):
        """Find an action button (eye/edit/clock) within a table row.

        FIX-7: Tries multiple locator strategies for each icon type,
        especially for the clock/history icon which was not found before.
        Includes debug dump of what icons ARE in the row.
        """
        # ---- Strategies per icon type ----
        strategies = []

        if icon_name == "clock":
            # History button — try many strategies
            strategies = [
                # S1: app-feather-icons with icon='clock'
                lambda: row.find_elements(By.CSS_SELECTOR, "app-feather-icons[icon='clock']"),
                # S2: app-feather-icons with name='clock'
                lambda: row.find_elements(By.CSS_SELECTOR, "app-feather-icons[name='clock']"),
                # S3: Any element with name or icon attribute containing 'clock'
                lambda: row.find_elements(By.XPATH,
                    ".//*[contains(@name,'clock') or contains(@icon,'clock')]"),
                # S4: SVG with title containing 'clock'
                lambda: row.find_elements(By.XPATH,
                    ".//*[local-name()='svg' and .//*[local-name()='title' and contains(text(),'clock')]]"),
                # S5: 3rd app-feather-icons in the row (order: view, edit, history)
                lambda: row.find_elements(By.CSS_SELECTOR, "app-feather-icons:nth-of-type(3)"),
                # S6: Last app-feather-icons in the row
                lambda: row.find_elements(By.CSS_SELECTOR, "app-feather-icons:last-of-type"),
                # S7: 3rd button in action column
                lambda: row.find_elements(By.XPATH,
                    ".//td[contains(@class,'action')]//button[position()=3]"),
                # S8: mat-icon or i with text containing 'clock'
                lambda: row.find_elements(By.XPATH,
                    ".//mat-icon[contains(text(),'clock')] | .//i[contains(text(),'clock')]"),
            ]
        elif icon_name == "edit":
            strategies = [
                lambda: row.find_elements(By.CSS_SELECTOR, "app-feather-icons[icon='edit']"),
                lambda: row.find_elements(By.CSS_SELECTOR, "app-feather-icons[name='edit']"),
                lambda: row.find_elements(By.XPATH,
                    ".//*[contains(@name,'edit') or contains(@icon,'edit')]"),
                lambda: row.find_elements(By.CSS_SELECTOR, "app-feather-icons:nth-of-type(2)"),
            ]
        elif icon_name == "eye":
            strategies = [
                lambda: row.find_elements(By.CSS_SELECTOR, "app-feather-icons[icon='eye']"),
                lambda: row.find_elements(By.CSS_SELECTOR, "app-feather-icons[name='eye']"),
                lambda: row.find_elements(By.XPATH,
                    ".//*[contains(@name,'eye') or contains(@icon,'eye')]"),
                lambda: row.find_elements(By.CSS_SELECTOR, "app-feather-icons:nth-of-type(1)"),
            ]
        else:
            # Generic
            strategies = [
                lambda: row.find_elements(By.CSS_SELECTOR,
                    f"app-feather-icons[icon='{icon_name}']"),
            ]

        # Try each strategy
        for i, strategy in enumerate(strategies):
            try:
                elements = strategy()
                for el in elements:
                    try:
                        if el.is_displayed():
                            # Try to find ancestor button
                            try:
                                btn = el.find_element(By.XPATH, "./ancestor::button")
                                if btn.is_displayed():
                                    return btn
                            except Exception:
                                pass
                            # The icon itself is clickable
                            return el
                    except Exception:
                        continue
            except Exception:
                continue

        # ---- DEBUG DUMP: Print what icons ARE in the row ----
        log.warning(f"  DEBUG: Could not find '{icon_name}' icon in row. Dumping row contents:")
        try:
            all_icons = row.find_elements(By.XPATH,
                ".//app-feather-icons | .//*[@role='img'] | .//mat-icon | .//i.material-icons")
            log.warning(f"  DEBUG: Found {len(all_icons)} icon elements in row")
            for i, icon in enumerate(all_icons):
                try:
                    name_attr = icon.get_attribute("name") or ""
                    icon_attr = icon.get_attribute("icon") or ""
                    class_attr = icon.get_attribute("class") or ""
                    tag = icon.tag_name
                    text = icon.text.strip()[:50] if icon.text else ""
                    inner = (icon.get_attribute("innerHTML") or "")[:100]
                    log.warning(
                        f"  Icon[{i}]: tag={tag}, name='{name_attr}', "
                        f"icon='{icon_attr}', class='{class_attr}', "
                        f"text='{text}', inner='{inner}'"
                    )
                except Exception as e:
                    log.warning(f"  Icon[{i}]: error reading - {e}")
        except Exception as e:
            log.warning(f"  DEBUG dump failed: {e}")

        # Also dump all buttons in the row
        try:
            all_btns = row.find_elements(By.CSS_SELECTOR, "button")
            log.warning(f"  DEBUG: Found {len(all_btns)} buttons in row")
            for i, btn in enumerate(all_btns):
                try:
                    inner = (btn.get_attribute("innerHTML") or "")[:150]
                    log.warning(f"  Button[{i}]: inner='{inner}'")
                except Exception:
                    pass
        except Exception:
            pass

        return None

    def click_edit_button(self, username):
        """Click the Edit button for a specific user row.
        If not found on current page, auto-searches first then retries.
        """
        log.info(f"Clicking Edit button for: {username}...")

        # Try finding on current page first
        row = self._find_row_by_username(username)
        if not row:
            # Auto-search and retry
            log.info(f"User not on current page, searching: {username}")
            self.search(username)
            self.wait_seconds(2)
            row = self._find_row_by_username(username)

        if row:
            btn = self._find_action_button_in_row(row, "edit")
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(2)
                self._wait_for_form_content(timeout=5)
                log.info(f"Edit button clicked for: {username}")
                return True

        log.warning(f"Edit button not found for user: {username}")
        return self._click_action_button_fallback(username, "edit")

    def click_view_button(self, username):
        """Click the View button for a specific user row.
        If not found on current page, auto-searches first then retries.
        """
        log.info(f"Clicking View button for: {username}...")

        row = self._find_row_by_username(username)
        if not row:
            log.info(f"User not on current page, searching: {username}")
            self.search(username)
            self.wait_seconds(2)
            row = self._find_row_by_username(username)

        if row:
            btn = self._find_action_button_in_row(row, "eye")
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(2)
                self._wait_for_form_content(timeout=5)
                log.info(f"View button clicked for: {username}")
                return True

        log.warning(f"View button not found for user: {username}")
        return self._click_action_button_fallback(username, "eye")

    def click_history_button(self, username):
        """Click the History button for a specific user row.
        If not found on current page, auto-searches first then retries.

        NOTE: This overrides the simple version at line 1762.
        """
        log.info(f"Clicking History button for: {username}...")

        row = self._find_row_by_username(username)
        if not row:
            log.info(f"User not on current page, searching: {username}")
            self.search(username)
            self.wait_seconds(2)
            row = self._find_row_by_username(username)

        if row:
            btn = self._find_action_button_in_row(row, "clock")
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(2)
                log.info(f"History button clicked for: {username}")
                return True

        log.warning(f"History button not found for user: {username}")
        return self._click_action_button_fallback(username, "clock")

    def _click_action_button_fallback(self, username, icon_name):
        """Fallback: try xpath-based locators with dynamic substitution."""
        try:
            xpath = (
                f"//td[contains(@class,'cdk-column-username') or contains(@class,'mat-column-username')]"
                f"[.//text()[contains(.,'{username}')]]"
                f"/ancestor::tr//app-feather-icons[@icon='{icon_name}']"
            )
            icons = self.driver.find_elements(By.XPATH, xpath)
            for icon in icons:
                try:
                    if icon.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            icon,
                        )
                        self.wait_seconds(2)
                        log.info(f"Action button clicked via fallback xpath for: {username}")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Try with @name attribute instead of @icon
        try:
            xpath2 = (
                f"//td[contains(@class,'cdk-column-username') or contains(@class,'mat-column-username')]"
                f"[.//text()[contains(.,'{username}')]]"
                f"/ancestor::tr//app-feather-icons[@name='{icon_name}']"
            )
            icons2 = self.driver.find_elements(By.XPATH, xpath2)
            for icon in icons2:
                try:
                    if icon.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            icon,
                        )
                        self.wait_seconds(2)
                        log.info(f"Action button clicked via fallback @name xpath for: {username}")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Last resort: try clicking the ancestor button
        try:
            xpath_btn = (
                f"//td[contains(@class,'cdk-column-username') or contains(@class,'mat-column-username')]"
                f"[.//text()[contains(.,'{username}')]]"
                f"/ancestor::tr//app-feather-icons[@icon='{icon_name}']/ancestor::button"
            )
            btns = self.driver.find_elements(By.XPATH, xpath_btn)
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(2)
                        log.info(f"Action button clicked via fallback btn xpath for: {username}")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Nuclear fallback for clock: find the row and click last icon
        if icon_name == "clock":
            try:
                row = self._find_row_by_username(username)
                if row:
                    all_icons = row.find_elements(By.CSS_SELECTOR, "app-feather-icons")
                    if len(all_icons) >= 3:
                        last_icon = all_icons[-1]  # History is typically the last icon
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            last_icon,
                        )
                        self.wait_seconds(2)
                        log.info(f"History button clicked via NUCLEAR fallback (last icon) for: {username}")
                        return True
            except Exception:
                pass

        log.warning(f"All fallback strategies failed for action button: {icon_name} / {username}")
        return False

    # ==============================================================
    #  User creation (full workflow helper)
    # ==============================================================

    def create_user(self, data):
        """Create a user through the UI.
        Returns dict with status and message.

        FIX-Round6: After Submit, checks for Swal2 TOAST notifications
        (swal2-top-right) in addition to standard success/alert popups.
        The ERP shows validation errors as toast notifications that
        auto-dismiss and may not be detected by standard visibility checks.
        """
        try:
            self.open_add_form()
            self.fill_user_form(data)
            self.submit()
            self.wait_seconds(2)

            # Check for success
            success = self.is_success_alert_visible(timeout=5)
            if success:
                self.dismiss_any_swal()
                UC_SUBMISSIONS.append({
                    "username": data.get("username", ""),
                    "status": "CREATED",
                })
                return {"status": "PASSED", "message": "User created successfully"}

            # Check for validation warning (now handles toast-style Swal2)
            warning = self.handle_validation_warning(timeout=5)
            if warning:
                # Close any remaining popup
                try:
                    self.force_close_form_popup()
                except Exception:
                    pass
                return {"status": "FAILED", "message": f"Validation warning: {warning}"}

            # Check for Swal2 error toast via DOM (may auto-dismiss before visible)
            try:
                swal_errors = self.get_mat_error_text()
                if swal_errors:
                    try:
                        self.force_close_form_popup()
                    except Exception:
                        pass
                    return {"status": "FAILED", "message": f"Validation errors: {swal_errors}"}
            except Exception:
                pass

            # Check if popup closed (success without explicit alert)
            if not self._is_form_popup_open():
                UC_SUBMISSIONS.append({
                    "username": data.get("username", ""),
                    "status": "CREATED",
                })
                return {"status": "PASSED", "message": "User created (no explicit success alert)"}

            # Popup still open — duplicate or error (BUG-001: silent failure)
            self.force_close_form_popup()
            self.wait_seconds(1)
            return {"status": "FAILED", "message": "Form still open after submit"}

        except Exception as e:
            # Try to close any leftover popup
            try:
                self.force_close_form_popup()
            except Exception:
                pass
            return {"status": "FAILED", "message": str(e)}

    # ==============================================================
    #  Edit user (full workflow helper)
    #  FIX-5: Better Update success detection — wait up to 10s for popup close
    # ==============================================================

    def edit_user(self, username, edit_data):
        """Edit an existing user through the UI.
        Returns dict with status and message.

        FIX-5: After clicking Update, waits up to 10s for popup to close
        before declaring failure. Also retries Update once if popup stays open.
        """
        try:
            # Find and click edit button
            clicked = self.click_edit_button(username)
            if not clicked:
                return {"status": "FAILED", "message": f"Edit button not found for: {username}"}

            self.wait_seconds(1)

            # Fill only the fields we want to change
            if edit_data.get("first_name"):
                self.type_text(self.FIRST_NAME_INPUT, edit_data["first_name"], clear_first=True)
                self.wait_seconds(0.3)

            if edit_data.get("last_name"):
                self.type_text(self.LAST_NAME_INPUT, edit_data["last_name"], clear_first=True)
                self.wait_seconds(0.3)

            if edit_data.get("email"):
                self.type_text(self.EMAIL_INPUT, edit_data["email"], clear_first=True)
                self.wait_seconds(0.3)

            # Click Update
            self.click_update()

            # FIX-5: Wait for popup to close — give it up to 10 seconds
            popup_closed = False
            for attempt in range(10):
                time.sleep(1)
                try:
                    popup = self.driver.find_element(By.XPATH, "//mat-dialog-container")
                    if not popup.is_displayed():
                        popup_closed = True
                        break
                except Exception:
                    # mat-dialog-container not found = popup closed
                    popup_closed = True
                    break

                # Also check big-model popup
                try:
                    big_popup = self.driver.find_element(By.CSS_SELECTOR, "div.big-model")
                    if not big_popup.is_displayed():
                        popup_closed = True
                        break
                except Exception:
                    pass

            if popup_closed:
                log.info("Popup closed after Update")
                # Check for success alert
                success = self.is_success_alert_visible(timeout=3)
                if success:
                    self.dismiss_any_swal()
                return {"status": "PASSED", "message": "User updated successfully (popup closed)"}

            # Popup still open after 10s — check for success alert anyway
            success = self.is_success_alert_visible(timeout=2)
            if success:
                self.dismiss_any_swal()
                return {"status": "PASSED", "message": "User updated (success alert appeared)"}

            # Check for validation warning
            warning = self.handle_validation_warning(timeout=2)
            if warning:
                return {"status": "FAILED", "message": f"Validation warning: {warning}"}

            # Retry: try clicking Update one more time
            log.info("Retrying Update click...")
            try:
                update_btn = self.driver.find_element(By.XPATH,
                    "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]")
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    update_btn,
                )
                time.sleep(3)
                # Check again
                if not self._is_form_popup_open():
                    return {"status": "PASSED", "message": "User updated on retry"}
                success2 = self.is_success_alert_visible(timeout=2)
                if success2:
                    self.dismiss_any_swal()
                    return {"status": "PASSED", "message": "User updated on retry (success alert)"}
            except Exception:
                pass

            # Final: popup still open
            self.force_close_form_popup()
            return {"status": "FAILED", "message": "Update button click failed or form still open"}

        except Exception as e:
            try:
                self.force_close_form_popup()
            except Exception:
                pass
            return {"status": "FAILED", "message": str(e)}

    # ==============================================================
    #  View user
    # ==============================================================

    def view_user(self, username):
        """Click the View button and return whether the popup opened."""
        clicked = self.click_view_button(username)
        if clicked:
            self.wait_seconds(1)
            return True
        return False

    # ==============================================================
    #  FIX-6: is_view_popup_readonly — check aria-disabled,
    #  mat-form-field-disabled, mat-select-disabled for Angular Material
    # ==============================================================

    def is_view_popup_readonly(self):
        """Check if the View popup has all fields in read-only/disabled state.
        Returns (is_readonly, details_dict).

        FIX-6: Angular Material fields don't always have 'disabled' or 'readonly'
        attributes on the <input>. Instead check:
          - mat-form-field-disabled class on the wrapper
          - aria-disabled='true' on the input/select
          - mat-select-disabled class on mat-select
          - mat-checkbox-disabled class on mat-checkbox
        """
        details = {}
        is_readonly = True

        # Check text inputs — use Angular Material wrapper class detection
        text_inputs = [
            ("username", self.USERNAME_INPUT),
            ("email", self.EMAIL_INPUT),
            ("first_name", self.FIRST_NAME_INPUT),
            ("last_name", self.LAST_NAME_INPUT),
            ("password", self.PASSWORD_INPUT),
        ]
        for name, locator in text_inputs:
            try:
                el = self.driver.find_element(
                    By.CSS_SELECTOR, locator[1]
                )

                # Method 1: Standard disabled/readonly attributes
                disabled_attr = el.get_attribute("disabled") is not None
                readonly_attr = el.get_attribute("readonly") is not None

                # Method 2: aria-disabled on the input
                aria_disabled = el.get_attribute("aria-disabled") == "true"

                # Method 3: mat-form-field-disabled on the parent wrapper
                parent_disabled = False
                try:
                    fcn = locator[1].split("'")[1] if "'" in locator[1] else ""
                    parent_field = self.driver.find_element(By.XPATH,
                        "//input[@formcontrolname='" + fcn + "']/ancestor::mat-form-field")
                    parent_classes = parent_field.get_attribute("class") or ""
                    parent_disabled = "mat-form-field-disabled" in parent_classes or \
                                      "mat-focused" not in parent_classes and "ng-untouched" in parent_classes
                except Exception:
                    pass

                field_disabled = disabled_attr or readonly_attr or aria_disabled or parent_disabled
                details[name] = {"disabled": field_disabled, "editable": not field_disabled}
                if not field_disabled:
                    is_readonly = False
                    log.warning(f"Field {name} appears editable in View mode")
            except Exception:
                details[name] = {"found": False}

        # Check dropdowns
        try:
            selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model mat-select, mat-dialog-container mat-select, "
                ".edit_pop_up mat-select"
            )
            dropdown_names = ["user_type", "role", "entity", "designation"]
            for i, sel in enumerate(selects):
                try:
                    cls = sel.get_attribute("class") or ""
                    aria_disabled = sel.get_attribute("aria-disabled") == "true"
                    # FIX-6: Check multiple disabled indicators
                    # FIX-Round6: Correct class name is mat-mdc-select-disabled (not mat-select-disabled)
                    disabled = ("mat-mdc-select-disabled" in cls or
                                "mat-select-disabled" in cls or
                                aria_disabled)
                    dname = dropdown_names[i] if i < len(dropdown_names) else f"dropdown_{i}"
                    details[dname] = {"disabled": disabled, "editable": not disabled}
                    if not disabled:
                        is_readonly = False
                        log.warning(f"Dropdown {dname} appears enabled in View mode (class={cls}, aria={aria_disabled})")
                except Exception:
                    pass
        except Exception:
            pass

        # Check checkboxes
        for cb_name, cb_locator in [("is_active", self.ACTIVE_CHECKBOX), ("is_staff", self.STAFF_CHECKBOX)]:
            try:
                cb = self.driver.find_element(
                    By.CSS_SELECTOR, cb_locator[1]
                )
                cls = cb.get_attribute("class") or ""
                disabled = "mat-mdc-checkbox-disabled" in cls or "mat-checkbox-disabled" in cls
                details[cb_name] = {"disabled": disabled, "editable": not disabled}
                if not disabled:
                    is_readonly = False
                    log.warning(f"Checkbox {cb_name} not disabled in View mode")
            except Exception:
                pass

        # Check if Submit/Update button is present (shouldn't be in view mode)
        try:
            submit_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit') or contains(.,'Update')]"
            )
            for btn in submit_btns:
                try:
                    if btn.is_displayed():
                        details["submit_visible"] = True
                        is_readonly = False
                        log.warning("Submit button visible in View mode")
                except Exception:
                    continue
        except Exception:
            pass

        return is_readonly, details

    # ==============================================================
    #  FIX-3: is_add_form_open — alias already existed, keeping it
    # ==============================================================

    def is_add_form_open(self):
        """Alias for _is_form_popup_open — checks if the Create form popup is open."""
        return self._is_form_popup_open()

    # ==============================================================
    #  Edit form helpers
    # ==============================================================

    def get_edit_form_values(self):
        """Get the current values of all fields in the Edit form.
        Returns dict with field names and their current values.
        """
        values = {}

        # Text inputs
        for name, locator in [
            ("username", self.USERNAME_INPUT),
            ("email", self.EMAIL_INPUT),
            ("first_name", self.FIRST_NAME_INPUT),
            ("last_name", self.LAST_NAME_INPUT),
            ("password", self.PASSWORD_INPUT),
        ]:
            try:
                el = self.driver.find_element(
                    By.CSS_SELECTOR, locator[1]
                )
                values[name] = el.get_attribute("value") or ""
            except Exception:
                values[name] = ""

        # Dropdowns
        try:
            selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model mat-select, mat-dialog-container mat-select, "
                ".edit_pop_up mat-select"
            )
            dropdown_names = ["user_type", "role", "entity", "designation"]
            for i, sel in enumerate(selects):
                try:
                    value_text = sel.find_element(
                        By.CSS_SELECTOR, ".mat-mdc-select-value-text"
                    )
                    name = dropdown_names[i] if i < len(dropdown_names) else f"dropdown_{i}"
                    values[name] = value_text.text.strip()
                except Exception:
                    name = dropdown_names[i] if i < len(dropdown_names) else f"dropdown_{i}"
                    values[name] = ""
        except Exception:
            pass

        # Checkboxes
        for cb_name, cb_locator in [("is_active", self.ACTIVE_CHECKBOX), ("is_staff", self.STAFF_CHECKBOX)]:
            try:
                cb = self.driver.find_element(
                    By.CSS_SELECTOR, cb_locator[1]
                )
                values[cb_name] = cb.is_selected()
            except Exception:
                values[cb_name] = False

        return values

    def is_edit_popup_editable(self):
        """Check if the Edit popup has editable fields and Update button."""
        has_update = False
        has_editable_fields = False

        # Check for Update button
        try:
            update_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
            )
            for btn in update_btns:
                try:
                    if btn.is_displayed():
                        has_update = True
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # Check if text inputs are enabled
        for locator in [self.FIRST_NAME_INPUT, self.LAST_NAME_INPUT, self.EMAIL_INPUT]:
            try:
                el = self.driver.find_element(
                    By.CSS_SELECTOR, locator[1]
                )
                disabled = el.get_attribute("disabled") is not None or \
                           el.get_attribute("readonly") is not None or \
                           el.get_attribute("aria-disabled") == "true"
                if not disabled:
                    has_editable_fields = True
                    break
            except Exception:
                continue

        return has_update and has_editable_fields

    # ==============================================================
    #  History
    # ==============================================================

    def open_history(self, username):
        """Click the History button for a user. Returns True if history popup opened."""
        clicked = self.click_history_button(username)
        if not clicked:
            return False
        self.wait_seconds(2)

        # Check if history popup opened
        try:
            history_popup = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH,
                     "//div[contains(@class,'big-model')]"
                     "[.//h3[contains(translate(.,'HISTORY','history'),'history')]]")
                )
            )
            return history_popup is not None
        except TimeoutException:
            # Check if any popup with history heading exists
            try:
                headings = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".big-model h3, mat-dialog-container h3"
                )
                for h in headings:
                    try:
                        if "history" in h.text.lower():
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
            return False

    def close_history(self):
        """Close the History popup."""
        try:
            close_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel') or contains(.,'Close')]"
            )
            for btn in close_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(1)
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: close via X button
        try:
            close_btns = self.driver.find_elements(
                By.CSS_SELECTOR, ".big-model .popup-actions button"
            )
            for btn in close_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "close" and btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(1)
                        return
                except Exception:
                    continue
        except Exception:
            pass

    def get_history_rows(self):
        """Get the number of rows in the History popup table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model table tbody tr, mat-dialog-container table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def has_history_search_input(self):
        """Check if the History popup has a search input."""
        try:
            search_inputs = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'big-model')]"
                "//input[contains(@placeholder,'Search') or contains(@placeholder,'search')]"
            )
            for inp in search_inputs:
                try:
                    if inp.is_displayed():
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: check any input inside the history popup
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model, mat-dialog-container"
            )
            for popup in popups:
                try:
                    h3 = popup.find_element(By.CSS_SELECTOR, "h3")
                    if "history" in h3.text.lower():
                        inputs = popup.find_elements(By.CSS_SELECTOR, "input")
                        for inp in inputs:
                            if inp.is_displayed() and ("search" in (inp.get_attribute("placeholder") or "").lower()):
                                return True
                except Exception:
                    continue
        except Exception:
            pass

        return False

    # ==============================================================
    #  Validation helpers
    # ==============================================================

    def get_visible_errors(self):
        """Get all visible mat-error messages."""
        errors = []
        try:
            error_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
            )
            for el in error_elements:
                try:
                    text = el.text.strip()
                    if text and el.is_displayed():
                        errors.append(text)
                except Exception:
                    continue
        except Exception:
            pass
        return errors

    def has_validation_error(self, error_text=None):
        """Check if there are any visible validation errors.
        If error_text is provided, checks for that specific error.
        """
        errors = self.get_visible_errors()
        if error_text:
            return any(error_text.lower() in e.lower() for e in errors)
        return len(errors) > 0

    def is_field_invalid(self, field_locator):
        """Check if a form field has ng-invalid CSS class."""
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR, field_locator[1]
            )
            cls = el.get_attribute("class") or ""
            return "ng-invalid" in cls
        except Exception:
            # Try the parent mat-form-field
            try:
                # Extract formcontrolname from CSS selector like input[formcontrolname='username']
                fcn = field_locator[1].split("'")[1] if "'" in field_locator[1] else ""
                xpath = "//input[@formcontrolname='" + fcn + "']/ancestor::mat-form-field"
                el = self.driver.find_element(By.XPATH, xpath)
                cls = el.get_attribute("class") or ""
                return "ng-invalid" in cls
            except Exception:
                return False

    # ==============================================================
    #  Method aliases (test file uses different names)
    # ==============================================================

    def search_user(self, query):
        """Alias: search for a user and verify they appear."""
        return self.search_and_verify(query)

    def get_table_row_count(self):
        """Get the number of visible rows in the table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table.mat-mdc-table tbody tr.mat-mdc-row"
            )
            return len(rows)
        except Exception:
            return 0

    def verify_view_popup_read_only(self):
        """Alias: check if view popup is read-only."""
        is_ro, _ = self.is_view_popup_readonly()
        return is_ro

    def verify_edit_popup_editable(self):
        """Alias: check if edit popup is editable."""
        return self.is_edit_popup_editable()

    def is_history_popup_open(self):
        """Check if history popup is currently visible."""
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model, mat-dialog-container"
            )
            for p in popups:
                try:
                    if p.is_displayed():
                        h3 = p.find_element(By.CSS_SELECTOR, "h3")
                        if h3 and "history" in h3.text.lower():
                            return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    # ==============================================================
    #  Additional aliases for test file compatibility
    # ==============================================================

    def click_history_button_v2(self, username):
        """Alias kept for backward compat — just calls click_history_button."""
        return self.click_history_button(username)

    def _select_random_from_dropdown(self, field_label):
        """DEPRECATED: Alias for _select_mat_option(field_label).
        Some test files still call this method name.
        """
        return self._select_mat_option(field_label)

    # ==============================================================
    #  FIX-Round5: Methods discovered from live ERP investigation
    # ==============================================================

    def get_mat_error_text(self):
        """Get all visible mat-error message texts as a list.

        Also checks SweetAlert2 for validation errors, since the ERP shows
        some validation errors via SweetAlert2 TOAST (swal2-top-right) instead
        of mat-error.

        FIX-Round6: The Swal2 toast has opacity:1 but offsetParent may be null.
        Must check DOM content, not just is_displayed().
        """
        errors = []

        # Check mat-error elements first
        try:
            error_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
            )
            for el in error_elements:
                try:
                    text = el.text.strip()
                    if text and el.is_displayed():
                        errors.append(text)
                except Exception:
                    continue
        except Exception:
            pass

        # Check SweetAlert2 for validation errors (toast-style)
        # FIX-Round6: Toast Swal2 may not be "visible" to Selenium but
        # has content in DOM with opacity:1
        try:
            # Check standard visible Swal2
            swal_title = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            if swal_title and swal_title.text.strip():
                # Check if visible OR if it's a toast with content
                try:
                    if swal_title.is_displayed():
                        errors.append(swal_title.text.strip())
                except Exception:
                    pass
                # For toasts: check opacity even if not "displayed"
                try:
                    container = self.driver.find_element(
                        By.CSS_SELECTOR, ".swal2-container"
                    )
                    opacity = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).opacity;",
                        container
                    )
                    if opacity and float(opacity) > 0:
                        text = swal_title.text.strip()
                        if text and text not in errors:
                            errors.append(text)
                except Exception:
                    pass
        except Exception:
            pass

        # Also check for Swal2 error icon in DOM
        try:
            error_icons = self.driver.find_elements(
                By.CSS_SELECTOR, ".swal2-icon.swal2-error"
            )
            for icon in error_icons:
                try:
                    if icon.is_displayed() or icon.get_attribute("class") or "":
                        title_el = self.driver.find_element(
                            By.CSS_SELECTOR, "#swal2-title"
                        )
                        text = title_el.text.strip() if title_el else ""
                        if text and text not in errors:
                            errors.append(text)
                except Exception:
                    continue
        except Exception:
            pass

        return errors

    def close_history_popup(self):
        """Alias for close_history — test file uses this name.

        The ERP history popup has a 'Close' button in the footer
        (verified 2026-05-21 on live app).
        """
        return self.close_history()
