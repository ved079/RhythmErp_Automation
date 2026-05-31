"""
services_master_page.py
-----------------------
Page Object Model for RhythmERP Services Master screen.

Location: Commodity Settings > Commodity Master > Services Master
URL:      /#/dynamic-screens/Services%20Master

FORM LAYOUT (Simple popup — NOT a stepper):

  - Name                  (text input,   required, name="Name")
  - Base Uom              (mat-select,   required)
  - UOM                   (mat-select,   required)
  - HSN SAC Code          (mat-select,   required)
  - Base Uom Conversion   (text input,   required, name="Base Uom Conversion")
  - Status                (toggle switch, default ON = Active)
  [Cancel] [Submit]

TABLE COLUMNS (main listing):
  - View / Edit / History   (action buttons per row)
  - Name / UOM / HSN SAC Code / Status

KNOWN BUGS (confirmed via ERP exploration):
  BUG-001 (HIGH)  : No maxlength on Name input; accepts 300+ chars. Server rejects at 255.
  BUG-002 (HIGH)  : No maxlength on Base Uom Conversion; accepts 11+ chars. Server max is 10.
  BUG-003 (HIGH)  : Name accepts ALL characters — special chars, spaces-only — no restrictions.
  BUG-004 (HIGH)  : Base Uom Conversion accepts ALL input — letters, special chars, negative,
                     zero, spaces — no type or range validation at all.
  BUG-005 (MEDIUM): Duplicate Names ALLOWED — no uniqueness constraint.
  BUG-006 (MEDIUM): Generic "Failed to save record" error instead of specific field-level message.
  BUG-007 (LOW)   : History popup shows "No data available" even for existing records.

POPUP TYPES:
  Type A — "Validation Failed - Please correct the highlighted fields"
            Appears when required fields are empty (client-side).
            Has .swal2-confirm button.
  Type B — "Failed to save record"
            Appears when server-side validation rejects data
            (e.g., Name exceeds 255 char limit, Base Uom Conversion exceeds 10 chars).
            MUST use JS dismiss to avoid StaleElementReferenceException.

KEY RULES:
  - NEVER use Keys.ESCAPE (closes entire popup form!)
  - JS clicks for Angular Material overlays
  - ALL SweetAlert2 dismissals MUST use JS querySelector click
  - Name input uses capital 'N': name="Name"
  - Base Uom Conversion uses full name: name="Base Uom Conversion"
  - Only 1 toggle: Status (Active/Inactive)
  - Base Uom and UOM share same option list but are INDEPENDENT (no auto-sync)
  - HSN SAC Code has only 4 options: 271536, 780341, 748554, 655403
  - History column uses cdk-column-archive (NOT cdk-column-history)
  - Edit mode: all fields editable, button says "Update"
  - View mode: all fields disabled, only Cancel button
"""

import os
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
    InvalidSessionIdException,
    WebDriverException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT

# Global list to track every submission for reporting
SM_SUBMISSIONS = []


class ServicesMasterPage(BasePage):
    """Page Object for Services Master screen."""

    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Services%20Master"

    # ==============================================================
    #  LOCATORS - Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    FILTER_BUTTON = ("css", "div[mattooltip='Filters'] button")

    # ==============================================================
    #  LOCATORS - Search bar
    # ==============================================================
    SEARCH_INPUT = ("css", "input#erpSearchInput, .erp-search-wrapper input")

    # ==============================================================
    #  LOCATORS - Table (main listing)
    # ==============================================================
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    TABLE_NAME_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-name, "
        "table#excel-table tbody td.mat-column-name",
    )
    TABLE_UOM_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-uom, "
        "table#excel-table tbody td.mat-column-uom",
    )
    TABLE_HSN_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-hsn_code, "
        "table#excel-table tbody td.mat-column-hsn_code",
    )
    TABLE_STATUS_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-status, "
        "table#excel-table tbody td.mat-column-status",
    )
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody tr td.no-data, "
        "table#excel-table tbody tr.mat-mdc-no-data-row",
    )

    # ==============================================================
    #  LOCATORS - Popup form
    # ==============================================================
    FORM_POPUP = (
        "css",
        ".edit_pop_up.override_edit_pop_up.popup-mode, "
        ".big-model, mat-dialog-container",
    )

    # Text inputs — NOTE: capital 'N' and full name in name attribute
    NAME_INPUT = (
        "css",
        "input[name='Name']",
    )
    BASE_UOM_CONVERSION_INPUT = (
        "css",
        "input[name='Base Uom Conversion']",
    )

    # Dropdowns (mat-select) — using XPath by label for reliability
    BASE_UOM_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Base Uom') and not(contains(.,'Conversion'))]"
        "/ancestor::mat-form-field//mat-select",
    )
    UOM_SELECT = (
        "xpath",
        "//mat-label[(contains(.,'UOM') or contains(.,'Uom') or contains(.,'uom'))"
        " and not(contains(.,'Base'))]"
        "/ancestor::mat-form-field//mat-select",
    )
    HSN_SAC_CODE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'HSN') or contains(.,'hsn')]"
        "/ancestor::mat-form-field//mat-select",
    )

    # Status toggle — uses <app-slide-toggle-v2> with <span class="main-label">
    STATUS_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(@class,'main-label') and contains(.,'Status')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    # Inner input checkbox inside the custom toggle — for reliable JS click
    STATUS_TOGGLE_INPUT = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(@class,'main-label') and contains(.,'Status')]]"
        "//input[@type='checkbox']",
    )

    # Popup buttons
    SUBMIT_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Submit')]",
    )
    UPDATE_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Update')]",
    )
    CANCEL_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Cancel')]",
    )

    # ==============================================================
    #  LOCATORS - Row action buttons
    # ==============================================================
    VIEW_BUTTON_BY_NAME = (
        "xpath",
        "//td[contains(text(),'{item_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-view')]"
        "//button",
    )
    EDIT_BUTTON_BY_NAME = (
        "xpath",
        "//td[contains(text(),'{item_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-edit')]"
        "//button",
    )
    HISTORY_BUTTON_BY_NAME = (
        "xpath",
        "//td[contains(text(),'{item_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-archive')]"
        "//button",
    )

    # ==============================================================
    #  LOCATORS - History popup
    # ==============================================================
    HISTORY_POPUP = (
        "xpath",
        "//div[contains(@class,'popup-overlay') or contains(@class,'big-model')]"
        "[.//h3[contains(translate(.,'HISTORY','history'),'history')]]",
    )
    HISTORY_TABLE_ROWS = (
        "css",
        ".popup-body table tbody tr, .big-model table tbody tr",
    )
    HISTORY_CLOSE_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Cancel') or contains(.,'Close')]",
    )

    # ==============================================================
    #  LOCATORS - SweetAlert2
    # ==============================================================
    SWAL_TITLE = ("css", "#swal2-title")
    SWAL_HTML = ("css", ".swal2-html-container")
    SWAL_CONFIRM = ("css", ".swal2-confirm")
    SWAL_CANCEL = ("css", ".swal2-cancel")

    # ==============================================================
    #  LOCATORS - Validation errors
    # ==============================================================
    MAT_ERROR = ("css", "mat-error, .mat-mdc-form-field-error")
    FIELD_ERROR = (
        "xpath",
        "//mat-label[contains(.,'{field_label}')]"
        "/ancestor::mat-form-field//mat-error",
    )

    # ==============================================================
    #  LOCATORS - Dropdown overlay
    # ==============================================================
    DROPDOWN_PANEL = (
        "css",
        "div.cdk-overlay-pane mat-select-panel, div[role='listbox']",
    )
    DROPDOWN_OPTIONS = (
        "css",
        "div[role='listbox'] mat-option, div[role='listbox'] [role='option']",
    )

    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Services Master listing page.
        Force-refreshes to clear leftover Angular state.
        """
        log.info("Navigating to Services Master page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the page is fully loaded."""
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table#excel-table")
                )
            )
            log.info("Services Master table loaded")
        except TimeoutException:
            log.warning("Services Master table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn")
                )
            )
            self.wait_seconds(1)
            log.info("Services Master toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the listing page has loaded."""
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

    def force_close_form_popup(self):
        """Force close any form popup via JS."""
        self.driver.execute_script("""
            document.querySelectorAll('.swal2-container').forEach(function(el) {
                el.remove();
            });
        """)
        self._force_close_panels()

    # ==============================================================
    #  Toolbar actions
    # ==============================================================

    def open_add_form(self):
        """Click the ADD (+) button to open the create popup form."""
        log.info("Clicking ADD button on Services Master...")
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
                    log.info("ADD form opened on Services Master")
                    return
        except Exception:
            pass

        # Strategy 2: mini-fab button with 'add' icon
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
                            log.info("ADD form opened via mini-fab on Services Master")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: click_with_retry
        try:
            self.click_with_retry(self.ADD_BUTTON)
            self.wait_seconds(1.5)
            if self._is_form_popup_open():
                log.info("ADD form opened via click_with_retry on Services Master")
                return
        except Exception:
            pass

        raise Exception("ADD button not found or not clickable on Services Master")

    def _wait_for_toolbar(self):
        """Wait for the toolbar and ADD button to be ready."""
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

    def _is_form_popup_open(self):
        """Quick check if any form popup is visible."""
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.big-model, mat-dialog-container, "
                "div.edit_pop_up.override_edit_pop_up.popup-mode",
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
        """Check if the Add form is open by looking for Name input."""
        return self.is_displayed(self.NAME_INPUT, timeout=5)

    def is_form_closed(self):
        """Check if the form popup is closed."""
        return not self._is_form_popup_open()

    def click_refresh(self):
        """Click the Refresh button."""
        log.info("Clicking Refresh button...")
        try:
            refresh_btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-mdc-mini-fab"
            )
            for btn in refresh_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "refresh" and btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(2)
                        log.info("Refresh clicked")
                        return
                except Exception:
                    continue
        except Exception:
            pass
        log.warning("Refresh button not found")

    # ==============================================================
    #  Fill form fields
    # ==============================================================

    def fill_form(self, data):
        """Fill all fields on the Services Master popup form.

        Fill order: Name → Base Uom → UOM → HSN SAC Code →
                    Base Uom Conversion → Status toggle
        """
        log.info("Filling Services Master form...")

        # 1. Name (required)
        if data.get("name"):
            self.type_text(self.NAME_INPUT, str(data["name"]), clear_first=True)

        # 2. Base Uom (required)
        self._fill_dropdown_if_provided(
            data, "base_uom", self.BASE_UOM_SELECT, "Base Uom"
        )

        # 3. UOM (required)
        self._fill_dropdown_if_provided(
            data, "uom", self.UOM_SELECT, "UOM"
        )

        # 4. HSN SAC Code (required)
        self._fill_dropdown_if_provided(
            data, "hsn_sac_code", self.HSN_SAC_CODE_SELECT, "HSN SAC Code"
        )

        # 5. Base Uom Conversion (required)
        if data.get("base_uom_conversion"):
            self.type_text(
                self.BASE_UOM_CONVERSION_INPUT,
                str(data["base_uom_conversion"]),
                clear_first=True,
            )

        # 6. Status toggle
        if "status" in data:
            self._set_status_toggle(bool(data["status"]))

        self._force_close_panels()
        log.info("Services Master form filled")

    def _fill_dropdown_if_provided(self, data, key, select_locator, label_name):
        """Fill a dropdown if the key exists in data."""
        if key not in data:
            return  # Key not provided — skip

        value = data[key]
        if value:
            self._select_mat_option(select_locator, str(value))
        else:
            self._select_random_from_dropdown(select_locator, label_name)

    def _select_mat_option(self, select_locator, value_text):
        """Select an option from a mat-select dropdown by visible text.
        Uses JS click for Angular Material compatibility.
        """
        log.info(f"Selecting '{value_text}' from dropdown")
        try:
            el = self.find_visible_element(select_locator, timeout=5)
            if el:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    el,
                )
                self.wait_seconds(0.5)

                # Wait for dropdown panel
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR, "div[role='listbox'] mat-option")
                        )
                    )
                except TimeoutException:
                    pass

                # Find and click the matching option
                options = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[role='listbox'] mat-option"
                )
                for opt in options:
                    try:
                        if opt.text.strip() == value_text and opt.is_displayed():
                            self.driver.execute_script("arguments[0].click();", opt)
                            self.wait_seconds(0.3)
                            log.info(f"Selected '{value_text}'")
                            return True
                    except Exception:
                        continue

                # If exact match not found, try contains
                for opt in options:
                    try:
                        if value_text in opt.text.strip() and opt.is_displayed():
                            self.driver.execute_script("arguments[0].click();", opt)
                            self.wait_seconds(0.3)
                            log.info(f"Selected '{opt.text.strip()}' (partial match)")
                            return True
                    except Exception:
                        continue

                log.warning(f"Option '{value_text}' not found in dropdown")
        except Exception as e:
            log.warning(f"Failed to select '{value_text}': {e}")
        finally:
            self._force_close_panels()
        return False

    def _select_random_from_dropdown(self, select_locator, label_name):
        """Select a random option from a mat-select dropdown."""
        log.info(f"Selecting random option from {label_name}")
        try:
            el = self.find_visible_element(select_locator, timeout=5)
            if el:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    el,
                )
                self.wait_seconds(0.5)

                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR, "div[role='listbox'] mat-option")
                        )
                    )
                except TimeoutException:
                    pass

                options = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[role='listbox'] mat-option"
                )
                visible_options = []
                for opt in options:
                    try:
                        if opt.is_displayed() and opt.text.strip():
                            visible_options.append(opt)
                    except Exception:
                        continue

                if visible_options:
                    import random
                    chosen = random.choice(visible_options)
                    chosen_text = chosen.text.strip()
                    self.driver.execute_script("arguments[0].click();", chosen)
                    self.wait_seconds(0.3)
                    log.info(f"Randomly selected '{chosen_text}' from {label_name}")
                    return True
                else:
                    log.warning(f"No visible options in {label_name} dropdown")
        except Exception as e:
            log.warning(f"Failed to select random from {label_name}: {e}")
        finally:
            self._force_close_panels()
        return False

    # ==============================================================
    #  Toggle switch helper (Status toggle only)
    #  FIX: Click the inner <input type="checkbox"> via JS for
    #  reliable Angular change detection. The outer div.switch-wrapper
    #  click does NOT reliably trigger the toggle state change.
    # ==============================================================

    def _set_status_toggle(self, desired_state):
        """Set the Status toggle to desired state.
        True = Active (ON), False = Inactive (OFF).

        Strategy:
          1. Try clicking the inner <input type='checkbox'> via JS
             (most reliable — triggers Angular change detection).
          2. If that fails, click the div.switch-wrapper via JS.
          3. If that fails, dispatch a click event via JS on the wrapper.
          4. Retry up to 3 times if state doesn't change.
        """
        current_state = self._get_status_toggle_state()
        if current_state == desired_state:
            log.info(f"Status toggle already {'Active' if desired_state else 'Inactive'}")
            return

        target_label = 'Active' if desired_state else 'Inactive'
        log.info(f"Setting Status toggle to {target_label}...")

        for attempt in range(1, 4):
            try:
                # --- Strategy 1: Click inner checkbox input via JS ---
                try:
                    checkbox = self.driver.find_element(
                        By.XPATH,
                        "//app-slide-toggle-v2[.//span[contains(@class,'main-label') "
                        "and contains(.,'Status')]]"
                        "//input[@type='checkbox']"
                    )
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    self.wait_seconds(0.5)
                    new_state = self._get_status_toggle_state()
                    if new_state == desired_state:
                        log.info(f"Status toggle set to {target_label} (via checkbox input, attempt {attempt})")
                        return
                    log.warning(f"Checkbox click didn't change state (attempt {attempt}, current: {new_state})")
                except Exception as e:
                    log.warning(f"Checkbox input not found or click failed: {e}")

                # --- Strategy 2: Click div.switch-wrapper via JS ---
                try:
                    wrapper = self.driver.find_element(
                        By.XPATH,
                        "//app-slide-toggle-v2[.//span[contains(@class,'main-label') "
                        "and contains(.,'Status')]]"
                        "//div[contains(@class,'switch-wrapper')]"
                    )
                    self.driver.execute_script("arguments[0].click();", wrapper)
                    self.wait_seconds(0.5)
                    new_state = self._get_status_toggle_state()
                    if new_state == desired_state:
                        log.info(f"Status toggle set to {target_label} (via wrapper click, attempt {attempt})")
                        return
                    log.warning(f"Wrapper click didn't change state (attempt {attempt}, current: {new_state})")
                except Exception as e:
                    log.warning(f"Wrapper click failed: {e}")

                # --- Strategy 3: Dispatch click event via JS on the wrapper ---
                try:
                    self.driver.execute_script("""
                        var wrapper = document.querySelector(
                            'app-slide-toggle-v2 .switch-wrapper'
                        );
                        if (wrapper) {
                            wrapper.dispatchEvent(new MouseEvent('click', {
                                bubbles: true, cancelable: true
                            }));
                        }
                    """)
                    self.wait_seconds(0.5)
                    new_state = self._get_status_toggle_state()
                    if new_state == desired_state:
                        log.info(f"Status toggle set to {target_label} (via dispatchEvent, attempt {attempt})")
                        return
                    log.warning(f"dispatchEvent didn't change state (attempt {attempt}, current: {new_state})")
                except Exception as e:
                    log.warning(f"dispatchEvent failed: {e}")

            except (InvalidSessionIdException, WebDriverException):
                log.error("Browser session lost during toggle operation")
                raise

        # After 3 attempts — log final warning but don't crash
        final_state = self._get_status_toggle_state()
        if final_state == desired_state:
            log.info(f"Status toggle eventually set to {target_label}")
        else:
            log.warning(
                f"Status toggle may not have changed after 3 attempts "
                f"(desired: {target_label}, current: {'Active' if final_state else 'Inactive'})"
            )

    def _get_status_toggle_state(self):
        """Read the current Status toggle state.
        Returns True if Active (ON), False if Inactive (OFF).

        Detection strategy (in order of reliability):
          1. Check if the inner checkbox input is checked.
          2. Check .state-label.on.active / .state-label.off.active classes.
          3. Check the wrapper div for an 'active' / 'inactive' class.
          4. Default to True (ON) if nothing found.
        """
        try:
            # --- Strategy 1: Read checkbox input checked property ---
            try:
                checkbox = self.driver.find_element(
                    By.XPATH,
                    "//app-slide-toggle-v2[.//span[contains(@class,'main-label') "
                    "and contains(.,'Status')]]"
                    "//input[@type='checkbox']"
                )
                is_checked = self.driver.execute_script("return arguments[0].checked;", checkbox)
                if is_checked is not None:
                    return bool(is_checked)
            except Exception:
                pass

            # --- Strategy 2: Check .state-label.on.active ---
            try:
                on_label = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "app-slide-toggle-v2 .state-label.on.active"
                )
                if on_label:
                    return True  # Active
            except Exception:
                pass

            # --- Strategy 3: Check .state-label.off.active ---
            try:
                off_label = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "app-slide-toggle-v2 .state-label.off.active, "
                    "app-slide-toggle-v2 .state-off.active"
                )
                if off_label:
                    return False  # Inactive
            except Exception:
                pass

            # --- Strategy 4: Check switch-wrapper for toggle position ---
            try:
                wrapper = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "app-slide-toggle-v2 .switch-wrapper"
                )
                wrapper_class = wrapper.get_attribute("class") or ""
                # Some implementations add 'toggle-off' or similar class
                if "toggle-off" in wrapper_class or "inactive" in wrapper_class:
                    return False
                if "toggle-on" in wrapper_class or "active" in wrapper_class:
                    return True
            except Exception:
                pass

        except (InvalidSessionIdException, WebDriverException):
            log.error("Browser session lost while reading toggle state")
            raise

        return True  # Default assumption (toggle defaults to ON)

    # ==============================================================
    #  Submit / Update / Cancel
    # ==============================================================

    def submit(self):
        """Click the Submit button (Create mode)."""
        log.info("Submitting Services Master form...")
        self._force_close_panels()
        try:
            btn = self.find_visible_element(self.SUBMIT_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                log.info("Submit clicked")
                return
        except Exception:
            pass

        # Fallback: find any Submit button in popup
        try:
            btns = self.driver.find_elements(By.CSS_SELECTOR, ".popup-footer button")
            for b in btns:
                if b.text.strip() == "Submit" and b.is_displayed():
                    self.driver.execute_script("arguments[0].click();", b)
                    log.info("Submit clicked via fallback")
                    return
        except Exception:
            pass

        log.warning("Submit button not found")

    def click_update(self):
        """Click the Update button (Edit mode)."""
        log.info("Clicking Update button...")
        self._force_close_panels()
        try:
            btn = self.find_visible_element(self.UPDATE_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                log.info("Update clicked")
                return
        except Exception:
            pass
        log.warning("Update button not found")

    def cancel(self):
        """Click the Cancel button."""
        log.info("Clicking Cancel button...")
        try:
            btn = self.find_visible_element(self.CANCEL_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(0.5)
                return
        except Exception:
            pass
        log.warning("Cancel button not found")

    # ==============================================================
    #  SweetAlert2 handlers — JS-only dismissals
    # ==============================================================

    def handle_success_alert(self, timeout=15):
        """Handle success SweetAlert2 popup.
        Returns the alert title text, or '' if no alert appeared.
        """
        log.info("Handling success alert...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            title = self.get_swal_title()
            log.info(f"Success alert: {title}")

            # Dismiss via JS
            self._dismiss_swal_confirm()
            self._cleanup_swal_containers()

            return title or ""
        except TimeoutException:
            log.info("No success alert appeared")
            return ""

    def handle_validation_warning(self, timeout=10):
        """Handle 'Validation Failed' SweetAlert2 popup (Type A).
        Appears when required fields are empty (client-side).
        Returns the alert title text, or '' if no alert appeared.
        """
        log.info("Handling validation warning...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            title = self.get_swal_title()
            log.info(f"Validation warning: {title}")

            # Dismiss via JS (avoids StaleElementReferenceException)
            self._dismiss_swal_confirm()
            self._cleanup_swal_containers()

            return title or ""
        except TimeoutException:
            log.info("No validation warning appeared")
            return ""

    def handle_save_failure_alert(self, timeout=10):
        """Handle 'Failed to save record' SweetAlert2 popup (Type B).
        This popup appears when server-side validation rejects the data
        (e.g., Name exceeds 255 char limit, Base Uom Conversion exceeds 10 chars).
        BUG-006: Generic error message instead of specific field error.
        Uses JS click to avoid StaleElementReferenceException.
        Returns the alert title text, or '' if no alert appeared.
        """
        log.info("Handling save failure alert...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            title = self.get_swal_title()
            log.info(f"Save failure alert: {title}")

            # Read the HTML message if available
            try:
                html_el = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-html-container"
                )
                html_msg = html_el.text.strip()
                if html_msg:
                    log.info(f"Save failure detail: {html_msg}")
            except Exception:
                pass

            # Dismiss via JS (avoids stale element issues)
            self._dismiss_swal_confirm()
            self._cleanup_swal_containers()

            return title or ""
        except TimeoutException:
            log.info("No save failure alert appeared")
            return ""

    # ==============================================================
    #  SweetAlert2 — internal helpers (JS-only, no Selenium .click())
    # ==============================================================

    def _dismiss_swal_confirm(self):
        """Dismiss a SweetAlert2 popup via JS querySelector."""
        self.wait_seconds(0.5)
        self.driver.execute_script(
            "document.querySelector('.swal2-confirm')?.click();"
        )
        self.wait_seconds(0.3)

        # Fallback: click ALL swal2-confirm buttons
        try:
            remaining = self.driver.find_elements(
                By.CSS_SELECTOR, ".swal2-confirm"
            )
            if remaining:
                self.driver.execute_script("""
                    document.querySelectorAll('.swal2-confirm').forEach(
                        function(b) { b.click(); }
                    );
                """)
                self.wait_seconds(0.3)
        except Exception:
            pass

    def _cleanup_swal_containers(self):
        """Remove all leftover .swal2-container elements from the DOM."""
        try:
            WebDriverWait(self.driver, 3).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-container")
                )
            )
        except Exception:
            pass

        self.driver.execute_script("""
            document.querySelectorAll('.swal2-container')
            .forEach(function(el) { el.remove(); });
        """)
        self.wait_seconds(0.2)

    def get_swal_title(self):
        """Read the SweetAlert2 title text."""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            return el.text.strip()
        except Exception:
            return ""

    def is_validation_alert_present(self, timeout=5):
        """Check if SweetAlert2 is visible."""
        return self.is_displayed(self.SWAL_TITLE, timeout=timeout)

    # ==============================================================
    #  Validation error helpers
    # ==============================================================

    def has_field_error(self, field_label):
        """Check if a specific field has a validation error."""
        try:
            locator = (
                "xpath",
                f"//mat-label[contains(.,'{field_label}')]"
                "/ancestor::mat-form-field//mat-error",
            )
            return self.is_displayed(locator, timeout=3)
        except Exception:
            return False

    def get_mat_error_text(self):
        """Get all mat-error text messages on the form."""
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
        return errors

    # ==============================================================
    #  Row action buttons
    # ==============================================================

    def click_view_button(self, item_name=None, row_index=0):
        """Click the View button on a table row."""
        log.info(f"Clicking View button (name={item_name}, row={row_index})...")
        if item_name:
            try:
                locator = (
                    "xpath",
                    f"//td[contains(text(),'{item_name}')]"
                    "/ancestor::tr//td[contains(@class,'cdk-column-view')]"
                    "//button",
                )
                btn = self.find_visible_element(locator, timeout=5)
                if btn:
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_seconds(1)
                    return True
            except Exception:
                pass

        # Fallback: use row index
        return self._click_action_button_by_index(row_index, 0)

    def click_edit_button(self, item_name=None, row_index=0):
        """Click the Edit button on a table row."""
        log.info(f"Clicking Edit button (name={item_name}, row={row_index})...")
        if item_name:
            try:
                locator = (
                    "xpath",
                    f"//td[contains(text(),'{item_name}')]"
                    "/ancestor::tr//td[contains(@class,'cdk-column-edit')]"
                    "//button",
                )
                btn = self.find_visible_element(locator, timeout=5)
                if btn:
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_seconds(1)
                    return True
            except Exception:
                pass

        return self._click_action_button_by_index(row_index, 1)

    def click_history_button(self, item_name=None, row_index=0):
        """Click the History button on a table row.
        Note: Uses cdk-column-archive (NOT cdk-column-history).
        """
        log.info(f"Clicking History button (name={item_name}, row={row_index})...")
        if item_name:
            try:
                locator = (
                    "xpath",
                    f"//td[contains(text(),'{item_name}')]"
                    "/ancestor::tr//td[contains(@class,'cdk-column-archive')]"
                    "//button",
                )
                btn = self.find_visible_element(locator, timeout=5)
                if btn:
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_seconds(1)
                    return True
            except Exception:
                pass

        return self._click_action_button_by_index(row_index, 2)

    def _click_action_button_by_index(self, row_index, btn_index):
        """Click an action button by row and button index."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_index < len(rows):
                btns = rows[row_index].find_elements(By.CSS_SELECTOR, "button")
                if btn_index < len(btns):
                    self.driver.execute_script(
                        "arguments[0].click();", btns[btn_index]
                    )
                    self.wait_seconds(1)
                    return True
        except (InvalidSessionIdException, WebDriverException):
            log.error("Browser session lost during action button click")
            raise
        except Exception as e:
            log.warning(f"Failed to click action button: {e}")
        return False

    # ==============================================================
    #  Mode detection
    # ==============================================================

    def is_edit_mode(self):
        """Check if the form is in Edit mode (has Update button)."""
        try:
            return self.is_displayed(self.UPDATE_BUTTON, timeout=5)
        except (InvalidSessionIdException, WebDriverException):
            raise
        except Exception:
            return False

    def is_view_mode(self):
        """Check if the form is in View mode (all fields disabled, no Submit/Update)."""
        try:
            has_submit = self.is_displayed(self.SUBMIT_BUTTON, timeout=2)
            has_update = self.is_displayed(self.UPDATE_BUTTON, timeout=2)
            if has_submit or has_update:
                return False

            # Check if Name input is disabled
            try:
                name_input = self.driver.find_element(
                    By.CSS_SELECTOR, "input[name='Name']"
                )
                if not name_input.is_enabled():
                    return True
            except Exception:
                pass
        except (InvalidSessionIdException, WebDriverException):
            log.error("Browser session lost during view mode check")
            raise
        except Exception:
            pass
        return False

    # ==============================================================
    #  History popup
    # ==============================================================

    def is_history_popup_open(self):
        """Check if the History popup is visible."""
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.big-model, div.edit_pop_up"
            )
            for p in popups:
                try:
                    h3 = p.find_elements(By.CSS_SELECTOR, "h3")
                    for h in h3:
                        if "history" in h.text.lower() and p.is_displayed():
                            return True
                except Exception:
                    continue
        except (InvalidSessionIdException, WebDriverException):
            log.error("Browser session lost during history popup check")
            raise
        except Exception:
            pass
        return False

    def close_history_popup(self):
        """Close the History popup."""
        log.info("Closing History popup...")
        try:
            close_btn = self.find_visible_element(self.HISTORY_CLOSE_BUTTON, timeout=5)
            if close_btn:
                self.driver.execute_script("arguments[0].click();", close_btn)
                self.wait_seconds(0.5)
                return
        except Exception:
            pass

        # Fallback: find any Cancel/Close in visible popup
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'big-model')]//button"
                "[contains(.,'Cancel') or contains(.,'Close')]"
            )
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(0.5)
                        return
                except Exception:
                    continue
        except Exception:
            pass

        log.warning("Could not close History popup")

    def get_history_row_count(self):
        """Count rows in the History popup table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, ".big-model table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    # ==============================================================
    #  Table data helpers
    # ==============================================================

    def get_table_row_count(self):
        """Count visible data rows in the table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def get_all_item_names(self):
        """List all Name values in the table."""
        names = []
        try:
            cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody td.cdk-column-name, "
                "table#excel-table tbody td.mat-column-name",
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

    def search_item(self, search_text):
        """Search for an item by name in the table.
        Uses JS value injection + event dispatch for Angular compatibility.
        """
        log.info(f"Searching for: {search_text}")
        try:
            # Toggle search input
            search_btn = self.driver.find_element(
                By.CSS_SELECTOR, "button.search-btn"
            )
            self.driver.execute_script("arguments[0].click();", search_btn)
            self.wait_seconds(0.5)

            # Set value via JS
            search_input = self.driver.find_element(
                By.CSS_SELECTOR, "input#erpSearchInput"
            )
            self.driver.execute_script("""
                var inp = arguments[0];
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(inp, arguments[1]);
                inp.dispatchEvent(new Event('input', { bubbles: true }));
            """, search_input, search_text)
            self.wait_seconds(0.3)

            # Press Enter
            search_input.send_keys(Keys.RETURN)
            self.wait_seconds(2)

            return True
        except Exception as e:
            log.warning(f"Search failed: {e}")
            return False

    def is_record_in_table(self, name):
        """Check if a record exists in the table (partial match)."""
        names = self.get_all_item_names()
        return any(name.lower() in n.lower() for n in names)

    # ==============================================================
    #  High-level convenience methods
    # ==============================================================

    def create_record(self, data):
        """One-call record creation.
        Returns dict: {status, error, message, data}
        """
        result = {"status": "", "error": "", "message": "", "data": data}

        try:
            self.open_add_form()
            self.fill_form(data)
            self.submit()

            # Check for success alert (popups appear quickly)
            title = self.handle_success_alert(timeout=15)

            if title and "success" in title.lower():
                result["status"] = "PASSED"
                result["message"] = title
            elif title and "failed" in title.lower():
                result["status"] = "FAILED"
                result["message"] = title
                result["error"] = "Server rejected"
            else:
                # Check for validation warning
                val_title = self.handle_validation_warning(timeout=5)
                if val_title:
                    result["status"] = "FAILED"
                    result["message"] = val_title
                    result["error"] = "Validation failed"
                else:
                    # Check for save failure alert
                    fail_title = self.handle_save_failure_alert(timeout=5)
                    if fail_title:
                        result["status"] = "FAILED"
                        result["message"] = fail_title
                        result["error"] = "Save failed"
                    else:
                        result["status"] = "PASSED"
                        result["message"] = "Form submitted (no popup)"

            # Cleanup
            try:
                self.cancel()
            except Exception:
                pass
            self.force_close_form_popup()

            # Refresh to see new record
            self.click_refresh()
            self.wait_seconds(2)

            SM_SUBMISSIONS.append(result)
            return result

        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
            try:
                self.force_close_form_popup()
            except Exception:
                pass
            SM_SUBMISSIONS.append(result)
            return result
