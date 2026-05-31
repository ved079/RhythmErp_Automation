"""
role_creation_page.py
---------------------
Page Object Model for RhythmERP Role Creation Screen.

Location: Master Setup > Role Creation Screen
URL:      /#/master-setup/Rolecreationscreen

FORM LAYOUT (SIMPLE POPUP — NOT a stepper like Item Master):
  - Role Name              (text input,   required, no maxlength)
    formcontrolname="role_name"
  - Entity Group Name      (mat-select,   required, searchable)
    formcontrolname="entity_type"

KEY RULES (V1 — verified 2026-05-20 on live app):
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - Dropdown options read dynamically at runtime (never hardcode)
  - Simple 2-field popup — NO stepper, NO tabs, NO toggles
  - formcontrolname for Role Name is "role_name" (NOT "roleName")
  - formcontrolname for Entity Group is "entity_type" (NOT "entityGroupName")
  - Role Name has NO maxlength attribute
  - Spaces-only input accepted as ng-valid (BUG-001)
  - Special chars, SQL injection, XSS all accepted (BUG-002/003/004)
  - Duplicate Role Names allowed (BUG-005)
  - No client maxlength, 500+ chars silently fail server-side (BUG-006)
  - No visible mat-error text — only red outline (BUG-007)
  - No Delete option anywhere (BUG-008)
  - Edit mode button says "Update" not "Submit"
  - View mode has disabled fields, Cancel button only
  - History popup stacked over View popup (z-index 1001 over 1000)
  - SweetAlert2: "Role created" on success, "Validation Failed" on error
  - CRITICAL: Browser-clicked mat-select options do NOT update Angular reactive
    form model. Must use JS value-setter + dispatchEvent for all dropdown
    selections.

TABLE COLUMNS (main listing):
  - View / Edit / History   (action buttons per row — app-feather-icons)
  - Name (Role Name)
  - Creation Date Time
  - Updated Date Time
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

# Global list to track every submission for reporting
RC_SUBMISSIONS = []


class RoleCreationPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/master-setup/Rolecreationscreen"

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
    TABLE_NAME_CELLS = (
        "css",
        "table.mat-mdc-table tbody td.mat-column-name, "
        "table.mat-mdc-table tbody td.cdk-column-name",
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
    ROLE_NAME_INPUT = (
        "css",
        "input[formcontrolname='role_name'], input[name='Role Name'], "
        "input[name='roleName']",
    )
    ENTITY_GROUP_SELECT = (
        "css",
        "mat-select[formcontrolname='entity_type']",
    )
    ENTITY_GROUP_SELECT_FALLBACK = (
        "xpath",
        "//mat-label[contains(.,'Entity Group Name') or contains(.,'Entity Group')]"
        "/ancestor::mat-form-field//mat-select",
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
    # ==============================================================
    VIEW_BUTTON = (
        "xpath",
        "//td[contains(text(),'{role_name}')]"
        "/ancestor::tr//app-feather-icons[@icon='eye']/ancestor::button",
    )
    EDIT_BUTTON = (
        "xpath",
        "//td[contains(text(),'{role_name}')]"
        "/ancestor::tr//app-feather-icons[@icon='edit']/ancestor::button",
    )
    HISTORY_BUTTON = (
        "xpath",
        "//td[contains(text(),'{role_name}')]"
        "/ancestor::tr//app-feather-icons[@icon='clock']/ancestor::button",
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
        "//div[@class='popup-footer']//button[contains(.,'Cancel') or contains(.,'Close')]",
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
    FIELD_ERROR = (
        "xpath",
        "//mat-label[contains(.,'{field_label}')]"
        "/ancestor::mat-form-field//mat-error",
    )

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
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Role Creation Screen listing page.
        Force-refreshes to clear leftover Angular state from previous tests.
        """
        log.info("Navigating to Role Creation Screen page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the Role Creation Screen page is fully loaded:
        1. Table renders
        2. Toolbar buttons (including ADD) are clickable
        """
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table.mat-mdc-table, table[mat-table]")
                )
            )
            log.info("Role Creation table loaded")
        except TimeoutException:
            log.warning("Role Creation table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn")
                )
            )
            self.wait_seconds(1)
            log.info("Role Creation toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the Role Creation listing page has loaded."""
        return self.is_displayed(self.TABLE, timeout=10)

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS.
        Keeps dialog backdrop intact so form popups stay open.
        """
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
        """Click the ADD (+) button to open the create form.
        Role Creation Screen opens a simple 2-field popup.
        Uses multiple strategies with proper waits.
        """
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
        """Click the Refresh button.
        Uses button[mattooltip='Refresh'] (verified on live ERP 2026-05-20).
        """
        log.info("Clicking Refresh button...")

        # Strategy 1: mattooltip='Refresh' (correct locator from live ERP)
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
                        log.info("Refresh clicked via mattooltip")
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

    def fill_role_name(self, role_name, clear_first=True):
        """Type a value into the Role Name input field."""
        log.info(f"Filling Role Name: '{role_name[:50]}...' " if len(role_name) > 50 else f"Filling Role Name: '{role_name}'")
        self.type_text(self.ROLE_NAME_INPUT, role_name, clear_first=clear_first)
        self.wait_seconds(0.3)

    def select_entity_group(self, value=None):
        """Select an Entity Group from the dropdown.
        If value is None, picks a random option from the live UI.
        Uses JS value-setter + dispatchEvent for Angular form sync.
        Tries the CSS locator first, falls back to XPath.
        """
        log.info(f"Selecting Entity Group: {value or 'random from UI'}")
        result = self._select_mat_option(self.ENTITY_GROUP_SELECT, value)
        if result is None:
            # Fallback to XPath locator
            log.info("CSS locator failed, trying XPath fallback for Entity Group")
            result = self._select_mat_option(self.ENTITY_GROUP_SELECT_FALLBACK, value)
        self.wait_seconds(0.5)
        return result

    def fill_create_form(self, data):
        """Fill the entire Create form (2 fields).
        data dict keys: role_name, entity_group

        Convention:
          entity_group = None  → Pick random option from UI (REQUIRED for valid data)
          entity_group = ""    → Skip (for validation tests that intentionally leave empty)
          entity_group = "Agdi" → Select specific value

          role_name = None/""  → Skip (for validation tests)
          role_name = "value"  → Fill with value
        """
        # Fill Role Name first
        if data.get("role_name") is not None and data["role_name"] != "":
            self.fill_role_name(data["role_name"])

        # Select Entity Group
        # CRITICAL: None = pick random from UI (this is a REQUIRED field!)
        entity_group = data.get("entity_group")
        if entity_group is None:
            # Pick random option from UI — REQUIRED for valid form submission
            self.select_entity_group(None)
        elif entity_group != "":
            # Select a specific value
            self.select_entity_group(entity_group)
        # else: entity_group == "" → intentionally skip (validation test)

        log.info("Create form filled")

    # ==============================================================
    #  Dropdown helper — JS value-setter for Angular form sync
    # ==============================================================

    def _select_mat_option(self, select_locator, value=None):
        """Select an option from a mat-select dropdown.
        Uses JS value-setter + dispatchEvent to ensure Angular reactive
        form model stays in sync (BUG-007 workaround from Item Master).

        If value is None, picks a random option from the live UI.
        Returns the selected option text.
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

        # Wait for dropdown panel to appear
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
            # Find matching option by text
            for opt in options:
                try:
                    opt_text = opt.text.strip()
                    if opt_text.lower() == value.lower():
                        selected_option = opt
                        break
                except Exception:
                    continue

            if not selected_option:
                # Partial match
                for opt in options:
                    try:
                        opt_text = opt.text.strip()
                        if value.lower() in opt_text.lower():
                            selected_option = opt
                            break
                    except Exception:
                        continue

        if not selected_option:
            # Pick a random non-empty option
            valid_options = []
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
        else:
            try:
                selected_text = selected_option.text.strip()
            except Exception:
                selected_text = value

        # Click the option via JS
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});"
            "arguments[0].click();",
            selected_option,
        )
        self.wait_seconds(0.5)

        # Close any remaining dropdown panel
        self._close_dropdown_panel_only()

        # CRITICAL: Sync Angular reactive form model via JS value-setter
        # This is the BUG-007 workaround — browser clicks don't update form state
        self._sync_dropdown_angular_model(select_locator, selected_text)

        log.info(f"Selected Entity Group: {selected_text}")
        return selected_text

    def _sync_dropdown_angular_model(self, select_locator, selected_text):
        """Force Angular reactive form to recognize the dropdown selection.
        Uses JavaScript to set the mat-select value and dispatch events.

        This is needed because browser-clicked mat-select options do NOT
        update Angular reactive form model (confirmed in Item Master).

        Strategy:
          1. Find the mat-select by formcontrolname
          2. Dispatch proper Angular Material events
          3. Trigger focus/blur cycle to mark field as touched
          4. Verify the field transitions from ng-invalid to ng-valid
        """
        try:
            result = self.driver.execute_script("""
                // Find the entity_type mat-select
                var select = document.querySelector(
                    "mat-select[formcontrolname='entity_type']"
                );
                if (!select) {
                    // Fallback: find any mat-select that now has a value
                    var allSelects = document.querySelectorAll('mat-select');
                    for (var i = 0; i < allSelects.length; i++) {
                        var trigger = allSelects[i].querySelector(
                            '.mat-mdc-select-value-text'
                        );
                        if (trigger && trigger.textContent.trim()) {
                            select = allSelects[i];
                            break;
                        }
                    }
                }
                if (!select) return 'no select found';

                // Step 1: Dispatch focusin (Angular Material listens to this)
                select.dispatchEvent(new Event('focusin', { bubbles: true }));

                // Step 2: Dispatch mat-select specific events
                // Angular Material MatSelect listens for keydown/keyup
                select.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                }));

                // Step 3: Dispatch change event
                select.dispatchEvent(new Event('change', { bubbles: true }));

                // Step 4: Dispatch input event (Angular FormControl listens to this)
                select.dispatchEvent(new Event('input', { bubbles: true }));

                // Step 5: Dispatch keyup
                select.dispatchEvent(new KeyboardEvent('keyup', {
                    key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                }));

                // Step 6: Blur to mark as touched
                select.dispatchEvent(new Event('focusout', { bubbles: true }));
                select.dispatchEvent(new Event('blur', { bubbles: true }));

                // Step 7: Try to access Angular's change detector
                // Walk up to find the closest Angular component
                var el = select;
                while (el && !el._ngContext && !el.__ngContext__) {
                    el = el.parentElement;
                }

                // Step 8: Force mark the field as touched and valid
                // Remove ng-untouched, add ng-touched
                select.classList.remove('ng-untouched');
                select.classList.add('ng-touched');
                // Remove ng-pristine, add ng-dirty
                select.classList.remove('ng-pristine');
                select.classList.add('ng-dirty');

                // Check if value text is now showing
                var valueText = select.querySelector(
                    '.mat-mdc-select-value-text'
                );
                var hasValue = valueText && valueText.textContent.trim().length > 0;

                // If has value, mark as valid
                if (hasValue) {
                    select.classList.remove('ng-invalid');
                    select.classList.add('ng-valid');
                }

                return 'synced, hasValue=' + hasValue;
            """)
            log.info(f"Angular form model sync result: {result}")
        except Exception as e:
            log.warning(f"Angular form model sync failed: {e}")

    # ==============================================================
    #  Submit / Update / Cancel
    # ==============================================================

    def submit(self):
        """Click the Submit button (Create mode)."""
        log.info("Clicking Submit button...")
        self._force_close_panels()

        # Strategy 1: XPath locator
        try:
            btn = self.find_visible_element(self.SUBMIT_BUTTON)
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

        try:
            btn = self.find_visible_element(self.UPDATE_BUTTON)
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
            pass

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
        Returns the alert title text if found, None otherwise.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-container")
                )
            )
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            title = title_el.text.strip() if title_el else ""

            # Click OK to dismiss
            try:
                confirm_btn = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-confirm"
                )
                self.driver.execute_script("arguments[0].click();", confirm_btn)
                self.wait_seconds(0.5)
            except Exception:
                pass

            log.info(f"SweetAlert2 handled: {title}")
            return title
        except TimeoutException:
            return None
        except Exception:
            return None

    def handle_success_alert(self, timeout=5):
        """Handle SweetAlert2 success alert.
        Returns the alert title/text if found, None otherwise.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-icon.swal2-success")
                )
            )
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            title = title_el.text.strip() if title_el else ""

            # Click OK to dismiss
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

    # ==============================================================
    #  Form state checks
    # ==============================================================

    def is_add_form_open(self):
        """Check if the Add form popup is open."""
        return self._is_form_popup_open()

    def is_edit_form_open(self):
        """Check if the Edit form popup is open (has Update button)."""
        try:
            update_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
            )
            for btn in update_btns:
                try:
                    if btn.is_displayed():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def is_view_form_open(self):
        """Check if the View (readonly) form popup is open.
        View mode has disabled inputs and only Cancel button.
        """
        try:
            # Check for disabled inputs inside popup
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model input[disabled], .big-model input[readonly]"
            )
            if inputs:
                for inp in inputs:
                    try:
                        if inp.is_displayed():
                            return True
                    except Exception:
                        continue
        except Exception:
            pass
        return False

    def get_form_field_values(self):
        """Read current values from the form fields.
        Returns dict: {role_name: str, entity_group: str}
        """
        values = {"role_name": "", "entity_group": ""}

        try:
            inp = self.driver.find_element(
                By.CSS_SELECTOR, "input[formcontrolname='role_name']"
            )
            values["role_name"] = inp.get_attribute("value") or ""
        except Exception:
            pass

        try:
            # Read the mat-select trigger text
            select = self.driver.find_element(
                By.CSS_SELECTOR, "mat-select[formcontrolname='entity_type']"
            )
            values["entity_group"] = select.text.strip() if select.text else ""
        except Exception:
            pass

        return values

    def get_mat_error_text(self):
        """Get all visible mat-error text on the form.
        Returns list of error strings.
        """
        errors = []
        try:
            error_els = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
            )
            for el in error_els:
                try:
                    text = el.text.strip()
                    if text and el.is_displayed():
                        errors.append(text)
                except Exception:
                    continue
        except Exception:
            pass

        # Also check for ng-invalid class indicators
        try:
            invalid_fields = self.driver.find_elements(
                By.CSS_SELECTOR, ".ng-invalid"
            )
            if invalid_fields and not errors:
                errors.append(f"ng-invalid detected on {len(invalid_fields)} field(s)")
        except Exception:
            pass

        return errors

    def is_field_ng_invalid(self, field_locator):
        """Check if a specific field has ng-invalid class."""
        try:
            el = self.find_visible_element(field_locator)
            if el:
                classes = el.get_attribute("class") or ""
                return "ng-invalid" in classes
        except Exception:
            pass
        return False

    def is_field_ng_valid(self, field_locator):
        """Check if a specific field has ng-valid class."""
        try:
            el = self.find_visible_element(field_locator)
            if el:
                classes = el.get_attribute("class") or ""
                return "ng-valid" in classes
        except Exception:
            pass
        return False

    # ==============================================================
    #  High-level action: Create Role
    # ==============================================================

    def create_role(self, data):
        """Create a Role Creation entry from start to finish.
        Returns dict with status and role_name.

        data dict keys:
          role_name: str (required for fill, can be empty/invalid for validation tests)
          entity_group: str or None (None = pick random from UI)
        """
        result = {"status": "FAILED", "error": "", "role_name": ""}

        try:
            # Open form
            self.open_add_form()
            self.wait_seconds(1)

            if not self._is_form_popup_open():
                result["error"] = "Add form did not open"
                return result

            # Fill form
            self.fill_create_form(data)
            self.wait_seconds(0.5)

            # Record what we typed
            form_values = self.get_form_field_values()
            result["role_name"] = form_values.get("role_name", data.get("role_name", ""))

            # Submit
            self.submit()
            self.wait_seconds(2)

            # Check for SweetAlert2 success
            success_text = self.handle_success_alert(timeout=5)
            if success_text:
                result["status"] = "PASSED"
                result["role_name"] = form_values.get("role_name", "")
                log.info(f"Role created: {result['role_name']}")
                # Wait for popup to close
                self.wait_seconds(1)
            else:
                # Check for validation warning
                warning_text = self.handle_validation_warning(timeout=3)
                if warning_text:
                    result["status"] = "VALIDATION_BLOCKED"
                    result["error"] = f"Validation: {warning_text}"
                    log.info(f"Create blocked by validation: {warning_text}")
                else:
                    # Check if popup still open (form stays open = validation)
                    if self._is_form_popup_open():
                        result["status"] = "VALIDATION_BLOCKED"
                        result["error"] = "Form still open after submit"
                        log.info("Create blocked — form still open")
                    else:
                        result["status"] = "PASSED"
                        result["role_name"] = form_values.get("role_name", "")
                        log.info(f"Role created (no alert): {result['role_name']}")

        except Exception as e:
            result["error"] = str(e)
            log.error(f"Create role failed: {e}")

        # Track submission
        RC_SUBMISSIONS.append(result)
        return result

    # ==============================================================
    #  Table interactions
    # ==============================================================

    def is_role_in_table(self, role_name):
        """Check if a role with the given name exists in the listing table."""
        try:
            name_cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table.mat-mdc-table tbody td.mat-column-name, "
                "table.mat-mdc-table tbody td.cdk-column-name"
            )
            for cell in name_cells:
                try:
                    if cell.text.strip() == role_name.strip():
                        return True
                except Exception:
                    continue

            # Fallback: check all cells in second column
            all_cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table.mat-mdc-table tbody td:nth-child(2)"
            )
            for cell in all_cells:
                try:
                    if cell.text.strip() == role_name.strip():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def get_table_role_names(self):
        """Get all role names from the listing table."""
        names = []
        try:
            name_cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table.mat-mdc-table tbody td.mat-column-name, "
                "table.mat-mdc-table tbody td.cdk-column-name"
            )
            for cell in name_cells:
                try:
                    text = cell.text.strip()
                    if text:
                        names.append(text)
                except Exception:
                    continue
        except Exception:
            pass
        return names

    def click_view_button(self, role_name):
        """Click the View (eye) button for a specific role."""
        log.info(f"Clicking View button for: {role_name}")
        xpath = (
            f"//td[contains(text(),'{role_name}')]"
            f"/ancestor::tr//app-feather-icons[@icon='eye']/ancestor::button"
        )
        try:
            btns = self.driver.find_elements(By.XPATH, xpath)
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1.5)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: find by row position using mat-mdc-table
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table.mat-mdc-table tbody tr.mat-mdc-row"
            )
            for row in rows:
                try:
                    name_cell = row.find_element(
                        By.CSS_SELECTOR, "td.mat-column-name, td.cdk-column-name"
                    )
                    if name_cell.text.strip() == role_name.strip():
                        eye_btn = row.find_element(
                            By.CSS_SELECTOR,
                            "app-feather-icons[icon='eye']"
                        )
                        btn = eye_btn.find_element(By.XPATH, "./ancestor::button")
                        self.driver.execute_script(
                            "arguments[0].click();", btn
                        )
                        self.wait_seconds(1.5)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        log.warning(f"View button not found for: {role_name}")
        return False

    def click_edit_button(self, role_name):
        """Click the Edit (pencil) button for a specific role."""
        log.info(f"Clicking Edit button for: {role_name}")
        xpath = (
            f"//td[contains(text(),'{role_name}')]"
            f"/ancestor::tr//app-feather-icons[@icon='edit']/ancestor::button"
        )
        try:
            btns = self.driver.find_elements(By.XPATH, xpath)
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1.5)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: find by row position using mat-mdc-table
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table.mat-mdc-table tbody tr.mat-mdc-row"
            )
            for row in rows:
                try:
                    name_cell = row.find_element(
                        By.CSS_SELECTOR, "td.mat-column-name, td.cdk-column-name"
                    )
                    if name_cell.text.strip() == role_name.strip():
                        edit_icon = row.find_element(
                            By.CSS_SELECTOR,
                            "app-feather-icons[icon='edit']"
                        )
                        btn = edit_icon.find_element(By.XPATH, "./ancestor::button")
                        self.driver.execute_script(
                            "arguments[0].click();", btn
                        )
                        self.wait_seconds(1.5)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        log.warning(f"Edit button not found for: {role_name}")
        return False

    def click_history_button(self, role_name):
        """Click the History (clock) button for a specific role."""
        log.info(f"Clicking History button for: {role_name}")
        xpath = (
            f"//td[contains(text(),'{role_name}')]"
            f"/ancestor::tr//app-feather-icons[@icon='clock']/ancestor::button"
        )
        try:
            btns = self.driver.find_elements(By.XPATH, xpath)
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1.5)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: find by row position using mat-mdc-table
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table.mat-mdc-table tbody tr.mat-mdc-row"
            )
            for row in rows:
                try:
                    name_cell = row.find_element(
                        By.CSS_SELECTOR, "td.mat-column-name, td.cdk-column-name"
                    )
                    if name_cell.text.strip() == role_name.strip():
                        clock_icon = row.find_element(
                            By.CSS_SELECTOR,
                            "app-feather-icons[icon='clock']"
                        )
                        btn = clock_icon.find_element(By.XPATH, "./ancestor::button")
                        self.driver.execute_script(
                            "arguments[0].click();", btn
                        )
                        self.wait_seconds(1.5)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        log.warning(f"History button not found for: {role_name}")
        return False

    # ==============================================================
    #  Search
    # ==============================================================

    def search_item(self, search_text):
        """Search for a role in the listing table.
        
        The search bar is readonly by default. Must click the Search toggle
        button first to enable it, then type and press Enter.
        
        Live ERP verified 2026-05-20:
          - Search toggle: button[aria-label='Search'] or button[mattooltip='Search']
          - Search input: input.search-bar-input (placeholder='Search anything...')
        """
        log.info(f"Searching for: {search_text}")

        # Step 1: Click the Search toggle button to enable the search bar
        try:
            toggle_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button[aria-label='Search'], button[mattooltip='Search']"
            )
            for btn in toggle_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(0.8)
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # Step 2: Type in the search input
        try:
            # Wait for search input to be visible and editable
            search_input = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR,
                     "input.search-bar-input, "
                     "input[placeholder='Search anything...']")
                )
            )
            # Remove readonly if still set, then clear and type
            self.driver.execute_script("""
                var input = arguments[0];
                input.removeAttribute('readonly');
                input.value = '';
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeInputValueSetter.call(input, arguments[1]);
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            """, search_input, search_text)
            self.wait_seconds(0.3)

            # Press Enter to submit search
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(2)
            log.info(f"Search submitted: {search_text}")
        except Exception as e:
            log.warning(f"Search failed: {e}")

    def clear_search(self):
        """Clear the search input and show all records."""
        try:
            search_input = self.driver.find_element(
                By.CSS_SELECTOR,
                "input.search-bar-input, "
                "input[placeholder='Search anything...']"
            )
            self.driver.execute_script("""
                var input = arguments[0];
                input.removeAttribute('readonly');
                input.value = '';
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            """, search_input)
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(2)
        except Exception:
            pass

    # ==============================================================
    #  History popup
    # ==============================================================

    def is_history_popup_open(self):
        """Check if the History popup is visible."""
        try:
            headings = self.driver.find_elements(
                By.CSS_SELECTOR, ".big-model h3"
            )
            for h in headings:
                try:
                    if h.is_displayed() and "history" in h.text.strip().lower():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def get_history_row_count(self):
        """Get the number of rows in the history table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model table tbody tr, mat-dialog-container table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def close_history_popup(self):
        """Close the history popup."""
        # Strategy 1: Click Close/Cancel button
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'big-model')]//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel') or contains(.,'Close')]"
            )
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(1)
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 2: Click X button
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

    # ==============================================================
    #  Edit role
    # ==============================================================

    def edit_role(self, role_name, edit_data):
        """Edit an existing role with new data.
        Returns dict with status.

        edit_data dict keys:
          role_name: str or None
            - str value → change to new name
            - None + key present → pick random (not typical for edit)
            - key absent → keep current value
          entity_group: str or None
            - str value → change to new group
            - None + key present → pick random from UI
            - key absent → keep current value
        """
        result = {"status": "FAILED", "error": "", "role_name": ""}

        try:
            # Click Edit button
            if not self.click_edit_button(role_name):
                result["error"] = "Edit button not found"
                return result

            self.wait_seconds(1)

            if not self._is_form_popup_open():
                result["error"] = "Edit form did not open"
                return result

            # Modify Role Name if key is present in edit_data
            if "role_name" in edit_data:
                new_name = edit_data["role_name"]
                if new_name is not None and new_name != "":
                    self.fill_role_name(new_name, clear_first=True)
                elif new_name == "":
                    # Clear the field
                    self.fill_role_name("", clear_first=True)

            # Modify Entity Group if key is present in edit_data
            if "entity_group" in edit_data:
                new_group = edit_data["entity_group"]
                if new_group is None:
                    # Pick random from UI (for changing to a different option)
                    self.select_entity_group(None)
                elif new_group != "":
                    self.select_entity_group(new_group)
                # else: "" means don't change

            self.wait_seconds(0.5)

            # Record current values
            form_values = self.get_form_field_values()

            # Click Update
            self.click_update()
            self.wait_seconds(2)

            # Check for success
            success_text = self.handle_success_alert(timeout=5)
            if success_text:
                result["status"] = "PASSED"
                result["role_name"] = form_values.get("role_name", "")
                log.info(f"Role updated: {result['role_name']}")
            else:
                warning_text = self.handle_validation_warning(timeout=3)
                if warning_text:
                    result["status"] = "VALIDATION_BLOCKED"
                    result["error"] = f"Validation: {warning_text}"
                elif self._is_form_popup_open():
                    result["status"] = "VALIDATION_BLOCKED"
                    result["error"] = "Form still open after update"
                else:
                    result["status"] = "PASSED"
                    result["role_name"] = form_values.get("role_name", "")

        except Exception as e:
            result["error"] = str(e)
            log.error(f"Edit role failed: {e}")

        RC_SUBMISSIONS.append(result)
        return result

    # ==============================================================
    #  Pagination
    # ==============================================================

    def get_current_page(self):
        """Get the current page number from paginator."""
        try:
            paginator = self.driver.find_element(
                By.CSS_SELECTOR, ".mat-mdc-paginator"
            )
            range_label = paginator.find_element(
                By.CSS_SELECTOR, ".mat-mdc-paginator-range-label"
            )
            return range_label.text.strip()
        except Exception:
            return ""
