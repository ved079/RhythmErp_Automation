"""
vehicle_master_page.py
----------------------
Page Object Model for RhythmERP Vehicle Master screen.

Location: Common Settings > Vehicle Master
URL:      /#/dynamic-screens/Vehicle%20Master

FORM LAYOUT (single-page, no stepper):
  - Name            (text input,   required)
  - Vehicle Price   (text input,   required, numeric)
  - Vehicle Type    (mat-select,   required, searchable dropdown)
  - Fuel Type       (mat-select,   required, searchable dropdown)
  - Description     (text input,   optional)

TABLE COLUMNS (visible):
  - View / Edit / History  (action buttons per row)
  - Name
  - Vehicle Price
  - Description

KEY RULES:
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - Dropdown options read dynamically at runtime (never hardcode)
  - History search requires Enter key after typing
  - Stacked popups: History -> View (z-index 1001 over 1000)

Optimised (v2) — UOM speed patterns applied:
  - Replaced most time.sleep/wait_seconds with WebDriverWait
  - hard_refresh() for fast page reset between tests
  - JS-first interactions (offsetParent checks, JS clicks)
  - Single-strategy methods instead of multi-fallback loops
  - Reduced unnecessary waits throughout
"""

import os
import sys
import time
import random
import copy

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL

# Global list to track every submission for reporting
VM_SUBMISSIONS = []


class VehicleMasterPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Vehicle%20Master"

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")

    # ==============================================================
    #  LOCATORS — Search bar
    # ==============================================================
    SEARCH_INPUT = ("css", "input#erpSearchInput, .erp-search-wrapper input")
    SEARCH_SUBMIT = ("css", "button.search-btn")

    # ==============================================================
    #  LOCATORS — Table
    # ==============================================================
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    TABLE_NAME_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-name, "
        "table#excel-table tbody td.mat-column-name, "
        "table#excel-table tbody td:nth-child(4)",
    )
    TABLE_PRICE_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-vehiclePrice, "
        "table#excel-table tbody td.mat-column-vehiclePrice, "
        "table#excel-table tbody td:nth-child(5)",
    )
    TABLE_DESC_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-description, "
        "table#excel-table tbody td.mat-column-description, "
        "table#excel-table tbody td:nth-child(6)",
    )
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody tr td.no-data, "
        "table#excel-table tbody tr.mat-mdc-no-data-row",
    )

    # ==============================================================
    #  LOCATORS — Add / Edit Form popup
    # ==============================================================
    FORM_POPUP = ("css", ".big-model, mat-dialog-container")
    FORM_HEADING = (
        "css",
        ".big-model h3, mat-dialog-container h3, .mat-mdc-dialog-title",
    )

    NAME_INPUT = (
        "css",
        "input[name='Name'], input[formcontrolname='name']",
    )
    PRICE_INPUT = (
        "css",
        "input[name='Vehicle Price'], "
        "input[formcontrolname='vehiclePrice'], "
        "input[name='vehiclePrice']",
    )
    VEHICLE_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Vehicle Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    FUEL_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Fuel Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    DESCRIPTION_INPUT = (
        "css",
        "input[name='Description'], textarea[formcontrolname='description']",
    )

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
    #  LOCATORS — Row action buttons (3-dot kebab menu)
    # ==============================================================
    ACTION_MENU_TRIGGER = ("css", "td.cdk-column-actions button")

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
        "//div[@class='popup-footer']//button[contains(.,'Close')]",
    )

    # ==============================================================
    #  LOCATORS — SweetAlert2
    # ==============================================================
    SWAL_TITLE = ("css", "#swal2-title")
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
    #  Navigation & page load — FAST (UOM pattern)
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to Vehicle Master page via direct URL (fast)."""
        log.info("Navigating to Vehicle Master page...")
        self.driver.get(self.PAGE_URL)
        self._wait_for_page_ready()

    def hard_refresh(self):
        """Hard refresh the current page and wait for ready.
        Much faster than full navigate_to_page() for resetting between tests."""
        log.info("Hard refreshing Vehicle Master page...")
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait for the page table, data rows, AND toolbar to be fully rendered.
        Uses fast JS polling (0.3s intervals) to avoid blind sleeps.
        Waits for: table element + at least 1 data row + search button VISIBLE.
        The key fix: checks offsetParent !== null for toolbar buttons,
        not just DOM existence — Angular renders the toolbar AFTER data."""
        end = time.monotonic() + 20
        while time.monotonic() < end:
            try:
                ready = self.driver.execute_script("""
                    var table = document.querySelector('table#excel-table');
                    if (!table || table.offsetParent === null) return {table: false};
                    var rows = table.querySelectorAll('tbody tr');
                    var hasData = false;
                    for (var i = 0; i < rows.length; i++) {
                        var cells = rows[i].querySelectorAll('td');
                        for (var j = 0; j < cells.length; j++) {
                            if (cells[j].textContent.trim()) { hasData = true; break; }
                        }
                        if (hasData) break;
                    }
                    var searchBtn = document.querySelector('button.search-btn');
                    var addBtn = document.querySelector('button.erp-add-btn');
                    var toolbarReady = (searchBtn && searchBtn.offsetParent !== null)
                                      && (addBtn && addBtn.offsetParent !== null);
                    return {
                        table: true, data: hasData,
                        toolbar: toolbarReady
                    };
                """)
                if ready and ready.get('table') and ready.get('data') and ready.get('toolbar'):
                    log.info("Page ready (table+data+toolbar visible)")
                    return
            except Exception:
                pass
            time.sleep(0.3)
        # Fallback: if toolbar didn't become visible but we have data, continue
        log.warning("Page ready: toolbar not fully visible within 20s, continuing anyway")

    def is_page_loaded(self):
        """Check if the Vehicle Master listing page has loaded."""
        try:
            return self.driver.execute_script(
                "var t = document.querySelector('table#excel-table');"
                "return t && t.offsetParent !== null;"
            )
        except Exception:
            return False

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS.
        Keeps dialog backdrop intact so form popups stay open."""
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

    # ==============================================================
    #  Toolbar actions — JS-first (UOM pattern)
    # ==============================================================

    def open_add_form(self):
        """Click the ADD (+) button via JS click. Single strategy, fast."""
        log.info("Opening Add Vehicle Master form...")
        js_click_add = """
        var btn = document.querySelector('button.erp-add-btn');
        if (!btn) { throw new Error('Add button not found in DOM'); }
        btn.scrollIntoView({block:'center'});
        btn.click();
        return 'clicked';
        """
        try:
            result = self.driver.execute_script(js_click_add)
            log.info("Add button clicked via JS: " + str(result))
        except Exception as e:
            log.warning("JS click failed, falling back to Selenium: " + str(e))
            self.click_with_retry(self.ADD_BUTTON)
        # Wait for the form popup to appear
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.execute_script(
                    "var el = document.querySelector("
                    "\"input[name='Name'], input[formcontrolname='name']\");"
                    "return el && el.offsetParent !== null;"
                )
            )
            log.info("Add form opened")
        except Exception:
            log.warning("Add form may not have opened — Name input not found")

    def click_refresh(self):
        """Click the Refresh button via JS. Falls back to hard_refresh.
        After refresh click, waits for stale data to clear (table briefly
        disappears), then waits for fresh data + toolbar to be ready."""
        log.info("Clicking Refresh button...")
        refresh_done = False
        try:
            result = self.driver.execute_script("""
            var btns = document.querySelectorAll('button[mattooltip]');
            for (var i = 0; i < btns.length; i++) {
                var tip = btns[i].getAttribute('mattooltip') || '';
                if (tip.toLowerCase() === 'refresh') {
                    btns[i].click();
                    return 'refresh_clicked';
                }
            }
            var allBtns = document.querySelectorAll('button.mat-mdc-mini-fab');
            for (var i = 0; i < allBtns.length; i++) {
                var icon = allBtns[i].querySelector('mat-icon');
                if (icon && icon.textContent.trim().toLowerCase() === 'refresh'
                    && allBtns[i].offsetParent !== null) {
                    allBtns[i].click();
                    return 'refresh_clicked_icon';
                }
            }
            return null;
            """)
            if result:
                log.info("Refresh clicked")
                refresh_done = True
        except Exception:
            pass

        if not refresh_done:
            log.warning("Refresh button not found, doing hard_refresh instead")
            self.hard_refresh()
            return

        # Wait for Angular to process the refresh — brief pause for stale
        # data to clear, then full page ready check
        time.sleep(0.5)
        self._wait_for_page_ready()

    # ==============================================================
    #  Fill form fields
    # ==============================================================

    def fill_vehicle_form(self, data):
        """Fill all fields on the Vehicle Master add/edit form.
        Dropdown values: if None/empty, picks a random option from the live UI."""
        log.info("Filling Vehicle Master form...")

        # Name
        if data.get("name"):
            self.type_text(self.NAME_INPUT, str(data["name"]), clear_first=True)

        # Price
        if data.get("price"):
            self.type_text(
                self.PRICE_INPUT, str(data["price"]), clear_first=True
            )

        # Vehicle Type dropdown (dynamic)
        if data.get("vehicle_type"):
            self._select_mat_option(
                self.VEHICLE_TYPE_SELECT, str(data["vehicle_type"])
            )
        else:
            self._select_random_from_dropdown(
                self.VEHICLE_TYPE_SELECT, "Vehicle Type"
            )

        # Fuel Type dropdown (dynamic)
        if data.get("fuel_type"):
            self._select_mat_option(
                self.FUEL_TYPE_SELECT, str(data["fuel_type"])
            )
        else:
            self._select_random_from_dropdown(
                self.FUEL_TYPE_SELECT, "Fuel Type"
            )

        # Description
        if data.get("description"):
            self.type_text(
                self.DESCRIPTION_INPUT, str(data["description"]),
                clear_first=True,
            )

        self._force_close_panels()
        log.info("Vehicle Master form filled")

    # ==============================================================
    #  Form submission & cancellation — JS-first (UOM pattern)
    # ==============================================================

    def submit(self):
        """Click the Submit button via JS click (fast)."""
        log.info("Submitting Vehicle Master form...")
        self._force_close_panels()
        self._js_click_popup_button('Submit')

    def click_update(self):
        """Click the Update button via JS click (fast)."""
        log.info("Clicking Update button...")
        self._force_close_panels()
        self._js_click_popup_button('Update')

    def cancel(self):
        """Click Cancel button via pure JS (fast)."""
        log.info("Clicking Cancel button...")
        self.driver.execute_script("""
            var footers = document.querySelectorAll('.popup-footer');
            for (var i = 0; i < footers.length; i++) {
                var buttons = footers[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.indexOf('Cancel') !== -1
                        && buttons[j].offsetParent !== null) {
                        buttons[j].click();
                        return 'clicked';
                    }
                }
            }
            return 'not found';
        """)

    def close_popup(self):
        """Close any popup by clicking Cancel button via JS (fast)."""
        log.info("Closing popup...")
        self.driver.execute_script("""
            var footers = document.querySelectorAll('.popup-footer');
            for (var i = 0; i < footers.length; i++) {
                var buttons = footers[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.indexOf('Cancel') !== -1) {
                        buttons[j].click();
                        return 'clicked';
                    }
                }
            }
            // Fallback: try X/close icon
            var icons = document.querySelectorAll(
                '.big-model button mat-icon, '
                + 'mat-dialog-container button mat-icon, '
                + '.popup-wrapper button mat-icon'
            );
            for (var i = 0; i < icons.length; i++) {
                if (icons[i].textContent.trim().toLowerCase() === 'close'
                    && icons[i].offsetParent !== null) {
                    var btn = icons[i].closest('button');
                    if (btn) { btn.click(); return 'closed_x'; }
                }
            }
            return 'not found';
        """)

    # ==============================================================
    #  SweetAlert2 handlers — FAST (UOM pattern)
    # ==============================================================

    def handle_success_alert(self, timeout=5):
        """Handle SweetAlert2 success notification — fast dismiss.
        Returns the alert message text, or '' if no alert appeared.
        Default 5s timeout — success alerts appear within 1-2s."""
        log.info("Handling success alert...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-container")
                )
            )
            # Read title text
            msg = ""
            try:
                title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
                msg = title_el.text.strip()
            except Exception:
                pass

            log.info("SweetAlert detected, dismissing via JS")
            self.driver.execute_script("""
                var btn = document.querySelector('.swal2-confirm');
                if (btn) { btn.click(); return 'clicked'; }
                return 'not found';
            """)
            # Wait for SweetAlert to disappear (short wait)
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, ".swal2-container")
                    )
                )
            except Exception:
                pass
            log.info(f"Success alert handled: {msg}")
            return msg
        except TimeoutException:
            log.info("No success alert appeared within timeout")
            return ""

    def handle_validation_warning(self, timeout=5):
        """Handle SweetAlert2 validation warning popup — fast dismiss.
        Returns the warning message text, or ''."""
        log.info("Checking for validation warning...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            msg = ""
            try:
                title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
                msg = title_el.text.strip()
            except Exception:
                pass
            self._dismiss_swal(button=".swal2-confirm", label="OK")
            log.info(f"Validation warning handled: {msg}")
            return msg
        except TimeoutException:
            return ""

    def handle_error_toast(self, timeout=3):
        """Check for error toast notification.
        Returns the toast message text, or ''."""
        log.info("Checking for error toast...")
        toast_loc = (
            "css",
            "snack-bar-container .mat-mdc-snack-bar-label, "
            "[role='alert'], .mat-mdc-snack-bar .mdc-snackbar__label",
        )
        if self.is_displayed(toast_loc, timeout=timeout):
            text = self.get_text(toast_loc)
            log.info(f"Error toast found: {text}")
            return text
        return ""

    def is_validation_alert_present(self, timeout=3):
        """Check if any SweetAlert2 popup is currently visible. Fast JS poll."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script("""
                    var el = document.querySelector('.swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error');
                    return el && el.offsetParent !== null;
                """)
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    # ==============================================================
    #  Field-level error checking
    # ==============================================================

    def get_mat_error_text(self):
        """Get all visible mat-error texts from the form.
        Returns a list of error strings."""
        errors = self.driver.find_elements(
            By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
        )
        texts = []
        for e in errors:
            try:
                t = e.text.strip()
                if t:
                    texts.append(t)
            except StaleElementReferenceException:
                continue
        if texts:
            log.warning(f"Validation errors found: {texts}")
        return texts

    def has_field_error(self, field_label):
        """Check if a specific form field has a visible mat-error."""
        try:
            locator = (
                "xpath",
                f"//mat-label[contains(.,'{field_label}')]"
                "/ancestor::mat-form-field//mat-error",
            )
            return self.is_displayed(locator, timeout=3)
        except Exception:
            return False

    # ==============================================================
    #  Verification helpers — JS-first (UOM pattern)
    # ==============================================================

    def is_add_form_open(self):
        """Check if the Add form popup is currently visible. Fast JS check."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector("
                "\"input[name='Name'], input[formcontrolname='name']\");"
                "return el && el.offsetParent !== null;"
            )
        except Exception:
            return False

    def is_form_closed(self):
        """Check if the form popup is no longer visible."""
        return not self.is_add_form_open()

    def get_form_heading(self):
        """Read the heading text of the current popup."""
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR,
                ".big-model h3, mat-dialog-container h3, "
                ".mat-mdc-dialog-title",
            )
            return el.text.strip()
        except Exception:
            return ""

    def is_view_mode(self):
        """Check if the currently open form is in View (read-only) mode."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector("
                "\"input[name='Name'], input[formcontrolname='name']\");"
                "return el && el.disabled;"
            )
        except Exception:
            return False

    def is_edit_mode(self):
        """Check if the currently open form is in Edit mode
        (Update button visible). Fast JS check."""
        try:
            return self.driver.execute_script("""
                var footers = document.querySelectorAll('.popup-footer');
                for (var i = 0; i < footers.length; i++) {
                    var buttons = footers[i].querySelectorAll('button');
                    for (var j = 0; j < buttons.length; j++) {
                        if (buttons[j].textContent.indexOf('Update') !== -1
                            && buttons[j].offsetParent !== null) {
                            return true;
                        }
                    }
                }
                return false;
            """)
        except Exception:
            return False

    def get_form_field_values(self):
        """Read all form field values from the currently open popup via JS.
        Returns a dict with keys: name, price, vehicle_type,
        fuel_type, description."""
        try:
            result = self.driver.execute_script("""
            var values = {};
            var nameEl = document.querySelector(
                "input[name='Name'], input[formcontrolname='name']"
            );
            values.name = nameEl ? nameEl.value : '';

            var priceEl = document.querySelector(
                "input[name='Vehicle Price'], input[formcontrolname='vehiclePrice']"
            );
            values.price = priceEl ? priceEl.value : '';

            try {
                var vtLabel = document.evaluate(
                    "//mat-label[contains(.,'Vehicle Type')]",
                    document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                ).singleNodeValue;
                if (vtLabel) {
                    var vtSelect = vtLabel.closest('mat-form-field')
                        ? vtLabel.closest('mat-form-field').querySelector('mat-select')
                        : null;
                    values.vehicle_type = vtSelect ? vtSelect.textContent.trim() : '';
                } else { values.vehicle_type = ''; }
            } catch(e) { values.vehicle_type = ''; }

            try {
                var ftLabel = document.evaluate(
                    "//mat-label[contains(.,'Fuel Type')]",
                    document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                ).singleNodeValue;
                if (ftLabel) {
                    var ftSelect = ftLabel.closest('mat-form-field')
                        ? ftLabel.closest('mat-form-field').querySelector('mat-select')
                        : null;
                    values.fuel_type = ftSelect ? ftSelect.textContent.trim() : '';
                } else { values.fuel_type = ''; }
            } catch(e) { values.fuel_type = ''; }

            var descEl = document.querySelector(
                "input[name='Description'], textarea[formcontrolname='description']"
            );
            values.description = descEl ? descEl.value : '';

            return JSON.stringify(values);
            """)
            import json
            return json.loads(result) if result else {}
        except Exception:
            # Fallback to Selenium
            values = {}
            try:
                values["name"] = (
                    self.driver.find_element(By.CSS_SELECTOR,
                        "input[name='Name'], input[formcontrolname='name']"
                    ).get_attribute("value") or ""
                )
            except Exception:
                values["name"] = ""
            try:
                values["price"] = (
                    self.driver.find_element(By.CSS_SELECTOR,
                        "input[name='Vehicle Price'], input[formcontrolname='vehiclePrice']"
                    ).get_attribute("value") or ""
                )
            except Exception:
                values["price"] = ""
            try:
                vt = self.driver.find_element(By.XPATH,
                    "//mat-label[contains(.,'Vehicle Type')]"
                    "/ancestor::mat-form-field//mat-select")
                values["vehicle_type"] = vt.text.strip()
            except Exception:
                values["vehicle_type"] = ""
            try:
                ft = self.driver.find_element(By.XPATH,
                    "//mat-label[contains(.,'Fuel Type')]"
                    "/ancestor::mat-form-field//mat-select")
                values["fuel_type"] = ft.text.strip()
            except Exception:
                values["fuel_type"] = ""
            try:
                values["description"] = (
                    self.driver.find_element(By.CSS_SELECTOR,
                        "input[name='Description'], textarea[formcontrolname='description']"
                    ).get_attribute("value") or ""
                )
            except Exception:
                values["description"] = ""
            return values

    # ==============================================================
    #  Table interactions — JS-first
    # ==============================================================

    def get_table_row_count(self):
        """Return the number of visible data rows in the table."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        return len(rows)

    def get_all_vehicle_names(self):
        """Return a list of all vehicle names in the current table view."""
        cells = self.driver.find_elements(
            By.CSS_SELECTOR,
            "table#excel-table tbody td.cdk-column-name, "
            "table#excel-table tbody td.mat-column-name, "
            "table#excel-table tbody td:nth-child(4)",
        )
        names = []
        for cell in cells:
            try:
                text = cell.text.strip()
                if text:
                    names.append(text)
            except StaleElementReferenceException:
                continue
        return names

    def is_vehicle_in_table(self, vehicle_name):
        """Check if a vehicle with the given name appears in the table.
        Polls up to 10s to handle slow Angular re-renders."""
        end_time = time.monotonic() + 10
        while time.monotonic() < end_time:
            try:
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, "table#excel-table tbody tr"
                )
                for row in rows:
                    cells = row.find_elements(By.CSS_SELECTOR, "td")
                    for cell in cells:
                        if vehicle_name.strip().lower() in cell.text.strip().lower():
                            return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def find_vehicle_row_index(self, vehicle_name):
        """Find the 0-based row index for a vehicle by name.
        Returns -1 if not found."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        for i, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                for cell in cells:
                    if (
                        vehicle_name.strip().lower()
                        in cell.text.strip().lower()
                    ):
                        return i
            except StaleElementReferenceException:
                continue
        return -1

    def get_vehicle_details_from_row(self, row_index=0):
        """Read text from a table row. Returns dict with
        name, price, description."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        if row_index >= len(rows):
            return {}
        row = rows[row_index]
        cells = row.find_elements(By.TAG_NAME, "td")
        data_cells = [c for c in cells if c.text.strip()]
        result = {}
        if len(data_cells) >= 1:
            result["name"] = data_cells[0].text.strip()
        if len(data_cells) >= 2:
            result["price"] = data_cells[1].text.strip()
        if len(data_cells) >= 3:
            result["description"] = data_cells[2].text.strip()
        return result

    # ==============================================================
    #  Row action buttons — pure JS 3-dot menu (UOM pattern)
    # ==============================================================

    def _click_action_menu_item(self, vehicle_name, action_name, retries=5):
        """Click an action menu item (View/Edit/History) for a specific
        vehicle row. Pure JS — retries with polling if data not yet loaded.
        On later retries, does a hard_refresh to force Angular data reload."""
        log.info(f"Clicking {action_name} via 3-dot menu for: {vehicle_name}")
        self._force_close_panels()

        # Step 1: Open the 3-dot menu — JS returns null instead of throwing
        js_open_menu = """
        var table = document.querySelector('table#excel-table');
        if (!table) return null;
        var rows = table.querySelectorAll('tbody tr');
        for (var i = 0; i < rows.length; i++) {
            var cells = rows[i].querySelectorAll('td');
            for (var j = 0; j < cells.length; j++) {
                if (cells[j].textContent.trim().indexOf(arguments[0]) !== -1) {
                    var menuBtn = rows[i].querySelector(
                        'td.cdk-column-actions button'
                    );
                    if (!menuBtn) return null;
                    menuBtn.scrollIntoView({block:'center'});
                    menuBtn.click();
                    return 'menu_opened';
                }
            }
        }
        return null;
        """
        menu_opened = None
        for attempt in range(retries):
            try:
                menu_opened = self.driver.execute_script(js_open_menu, vehicle_name)
                if menu_opened:
                    break
            except Exception:
                pass
            if attempt < retries - 1:
                log.info(f"Vehicle not in table yet, retrying ({attempt+1}/{retries})...")
                # After 2nd failed attempt, do a hard_refresh to reload data
                if attempt >= 2:
                    log.info("Doing hard_refresh to force data reload...")
                    self.hard_refresh()
                else:
                    time.sleep(1.5)

        # Fallback: try by row index
        if not menu_opened:
            log.warning(f"3-dot menu not found for '{vehicle_name}', trying row index...")
            row_idx = self.find_vehicle_row_index(vehicle_name)
            if row_idx >= 0:
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, "table#excel-table tbody tr"
                )
                if row_idx < len(rows):
                    menu_btn = rows[row_idx].find_element(
                        By.CSS_SELECTOR, "td.cdk-column-actions button"
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});"
                        "arguments[0].click();",
                        menu_btn,
                    )
                    menu_opened = 'menu_opened_via_index'

        if not menu_opened:
            raise Exception(f"Vehicle '{vehicle_name}' not found in table after {retries} retries")

        log.info(f"3-dot menu opened for: {vehicle_name}")

        # Wait briefly for dropdown overlay to render
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    ".cdk-overlay-container .cdk-overlay-pane",
                ))
            )
        except Exception:
            pass

        # Step 2: Click the specific menu item from the dropdown overlay
        js_click_item = """
        var overlay = document.querySelector('.cdk-overlay-container');
        if (!overlay) return null;
        var items = overlay.querySelectorAll('button, span, div');
        for (var i = 0; i < items.length; i++) {
            var text = items[i].textContent.trim();
            if (text === arguments[0]) {
                items[i].click();
                return 'clicked_' + arguments[0];
            }
        }
        // Fallback: try case-insensitive partial match
        for (var i = 0; i < items.length; i++) {
            var text = items[i].textContent.trim().toLowerCase();
            if (text.indexOf(arguments[0].toLowerCase()) !== -1) {
                items[i].click();
                return 'clicked_partial_' + arguments[0];
            }
        }
        return null;
        """
        result = self.driver.execute_script(js_click_item, action_name)
        if not result:
            raise Exception(f"Menu item '{action_name}' not found in dropdown overlay")
        log.info(f"Successfully clicked {action_name} for: {vehicle_name}")
        return result

    # -- DEPRECATED: kept for backward compat; delegates to kebab menu --

    def _click_action_button(self, vehicle_name, action_xpath_template):
        """DEPRECATED — delegates to _click_action_menu_item()."""
        if "cdk-column-view" in action_xpath_template:
            return self._click_action_menu_item(vehicle_name, "View")
        elif "cdk-column-edit" in action_xpath_template:
            return self._click_action_menu_item(vehicle_name, "Edit")
        elif "cdk-column-history" in action_xpath_template:
            return self._click_action_menu_item(vehicle_name, "History")
        return self._click_action_menu_item(vehicle_name, "View")

    def _click_action_button_by_index(self, row_index, action_xpath_template):
        """DEPRECATED — finds vehicle name by index, then uses
        _click_action_menu_item()."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        if row_index >= len(rows):
            raise Exception(
                f"Row index {row_index} out of range "
                f"(total rows: {len(rows)})"
            )
        cells = rows[row_index].find_elements(By.TAG_NAME, "td")
        name = ""
        for cell in cells:
            t = cell.text.strip()
            if t:
                name = t
                break
        if "cdk-column-view" in action_xpath_template:
            action = "View"
        elif "cdk-column-edit" in action_xpath_template:
            action = "Edit"
        elif "cdk-column-history" in action_xpath_template:
            action = "History"
        else:
            action = "View"
        return self._click_action_menu_item(name, action)

    def click_view_button(self, vehicle_name=None, row_index=0):
        """Click the View button for a vehicle row via 3-dot menu."""
        log.info(f"Clicking View button for: {vehicle_name or row_index}...")
        if vehicle_name:
            self._click_action_menu_item(vehicle_name, "View")
        else:
            self._click_action_button_by_index(row_index, "cdk-column-view")
        # Wait for view popup to appear
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.execute_script(
                    "var el = document.querySelector("
                    "\"input[name='Name'], input[formcontrolname='name']\");"
                    "return el && el.offsetParent !== null;"
                )
            )
        except Exception:
            pass

    def click_edit_button(self, vehicle_name=None, row_index=0):
        """Click the Edit button for a vehicle row via 3-dot menu."""
        log.info(f"Clicking Edit button for: {vehicle_name or row_index}...")
        if vehicle_name:
            self._click_action_menu_item(vehicle_name, "Edit")
        else:
            self._click_action_button_by_index(row_index, "cdk-column-edit")
        # Wait for edit popup to appear
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.execute_script(
                    "var el = document.querySelector("
                    "\"input[name='Name'], input[formcontrolname='name']\");"
                    "return el && el.offsetParent !== null;"
                )
            )
        except Exception:
            pass

    def click_history_button(self, vehicle_name=None, row_index=0):
        """Click the History button for a vehicle row via 3-dot menu."""
        log.info(f"Clicking History button for: {vehicle_name or row_index}...")
        if vehicle_name:
            self._click_action_menu_item(vehicle_name, "History")
        else:
            self._click_action_button_by_index(row_index, "cdk-column-history")
        # Wait for history popup to appear
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.execute_script(
                    "var headings = document.querySelectorAll("
                    "'h3.popup-title, .big-model h3, mat-dialog-container h3');"
                    "for (var i = 0; i < headings.length; i++) {"
                    "  if (headings[i].offsetParent !== null"
                    "      && headings[i].textContent.toLowerCase()"
                    "         .indexOf('history') !== -1)"
                    "    return true;"
                    "}"
                    "return false;"
                )
            )
        except Exception:
            pass

    # ==============================================================
    #  View & Edit specific verifications
    # ==============================================================

    def verify_view_popup_read_only(self):
        """Verify that the View popup fields are read-only / disabled.
        Returns True if all fields are non-editable."""
        log.info("Verifying View popup is read-only...")
        all_readonly = True

        try:
            name_disabled = self.driver.execute_script(
                "var el = document.querySelector("
                "\"input[name='Name'], input[formcontrolname='name']\");"
                "return el ? el.disabled : true;"
            )
            if not name_disabled:
                all_readonly = False
                log.warning("Name field is editable in View mode")
        except Exception:
            pass

        try:
            price_disabled = self.driver.execute_script(
                "var el = document.querySelector("
                "\"input[name='Vehicle Price'], input[formcontrolname='vehiclePrice']\");"
                "return el ? el.disabled : true;"
            )
            if not price_disabled:
                all_readonly = False
                log.warning("Price field is editable in View mode")
        except Exception:
            pass

        # Submit/Update should NOT be visible
        try:
            has_submit = self.driver.execute_script("""
                var footers = document.querySelectorAll('.popup-footer');
                for (var i = 0; i < footers.length; i++) {
                    var buttons = footers[i].querySelectorAll('button');
                    for (var j = 0; j < buttons.length; j++) {
                        if ((buttons[j].textContent.indexOf('Submit') !== -1
                             || buttons[j].textContent.indexOf('Update') !== -1)
                            && buttons[j].offsetParent !== null)
                            return true;
                    }
                }
                return false;
            """)
            if has_submit:
                all_readonly = False
                log.warning("Submit/Update button visible in View mode")
        except Exception:
            pass

        return all_readonly

    def verify_edit_popup_editable(self):
        """Verify that the Edit popup fields are editable.
        Returns True if the Update button is visible (edit mode)."""
        log.info("Verifying Edit popup is editable...")
        return self.is_edit_mode()

    # ==============================================================
    #  Search functionality — JS-first (UOM pattern)
    # ==============================================================

    def search_vehicle(self, vehicle_name):
        """Search for a vehicle by name using JS clicks (UOM pattern).
        Uses pure JS to click the search button — bypasses offsetParent
        visibility checks that fail when toolbar hasn't rendered yet.
        Returns True if the vehicle is found in the table results."""
        log.info(f"Searching for vehicle: {vehicle_name}")
        self._force_close_panels()

        # Step 1: Check if search input is already visible
        search_input = None
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR, "input#erpSearchInput, .erp-search-wrapper input"
            )
            rect = self.driver.execute_script(
                "var r = arguments[0].getBoundingClientRect(); "
                "return r.width > 0 && r.height > 0;", el
            )
            if rect:
                search_input = el
                log.info("Search input already visible, skipping button click")
        except Exception:
            pass

        # Step 2: If search input not visible, click search button via JS (UOM pattern)
        if search_input is None:
            log.info("Search input not visible, clicking search button via JS")
            # Ensure page is fully loaded first
            self._wait_for_page_ready()
            # JS click — bypasses visibility/offsetParent issues entirely
            js_click_search = """
            var btn = document.querySelector('button.search-btn');
            if (!btn) { return 'not_found'; }
            btn.scrollIntoView({block:'center'});
            btn.click();
            return 'clicked';
            """
            try:
                result = self.driver.execute_script(js_click_search)
                log.info("Search button clicked via JS: " + str(result))
                if result == 'not_found':
                    log.error("Search button not found in DOM")
                    return False
            except Exception as e:
                log.error("Failed to click search button via JS: " + str(e))
                return False

            # Wait for search input to become visible
            try:
                search_input = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((
                        By.CSS_SELECTOR,
                        "input#erpSearchInput, .erp-search-wrapper input"
                    ))
                )
                log.info("Search input became visible")
            except Exception:
                log.warning("Search input did not become visible after clicking search button")
                return False

        # Step 3: Clear existing value completely
        self.driver.execute_script("arguments[0].value = '';", search_input)
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
            search_input,
        )

        # Step 4: Set new value and fire Angular change events
        self.driver.execute_script(
            "arguments[0].value = arguments[1];", search_input, vehicle_name
        )
        search_input.click()
        for event in ["input", "keyup", "change"]:
            self.driver.execute_script(
                f"arguments[0].dispatchEvent(new Event('{event}', {{ bubbles: true }}));",
                search_input,
            )

        # Step 5: Click the search button again via JS to submit/filter
        js_click_search = """
        var btn = document.querySelector('button.search-btn');
        if (btn) { btn.click(); return 'clicked'; }
        return 'not found';
        """
        self.driver.execute_script(js_click_search)
        log.info("Search submit clicked via JS")

        # Step 6: Wait for table to refresh
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.find_elements("css selector", "table#excel-table tbody tr")
            )
        except Exception:
            pass  # Table might be empty (no results)

        # Step 7: Check results with polling
        found = self.is_vehicle_in_table(vehicle_name)
        if found:
            log.info(f"Vehicle found in table: {vehicle_name}")
        else:
            log.warning(f"Vehicle NOT found in table: {vehicle_name}")
        return found

    def clear_search(self):
        """Clear search and reset — use hard_refresh (fast, guaranteed clean)."""
        log.info("Clearing search - hard refreshing")
        self.hard_refresh()

    def verify_vehicle_exists(self, vehicle_name):
        """Navigate to page, search, and verify a vehicle exists."""
        self.navigate_to_page()
        found = self.search_vehicle(vehicle_name)
        self.clear_search()
        return found

    # ==============================================================
    #  History panel — JS-first (UOM pattern)
    # ==============================================================

    def is_history_popup_open(self):
        """Check if the History popup is currently visible. Fast JS check."""
        try:
            return self.driver.execute_script("""
                var headings = document.querySelectorAll(
                    'h3.popup-title, .big-model h3, mat-dialog-container h3'
                );
                for (var i = 0; i < headings.length; i++) {
                    if (headings[i].offsetParent !== null
                        && headings[i].textContent.toLowerCase()
                           .indexOf('history') !== -1)
                        return true;
                }
                return false;
            """)
        except Exception:
            return False

    def is_history_empty(self):
        """Check if the history table has no data rows."""
        return self.get_history_row_count() == 0

    def get_history_row_count(self):
        """Return the number of rows in the history popup table."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            ".big-model table tbody tr, "
            "mat-dialog-container table tbody tr",
        )
        return len(rows)

    def get_history_data(self):
        """Read all data from the history popup table.
        Returns a list of dicts, one per row."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            ".big-model table tbody tr, "
            "mat-dialog-container table tbody tr",
        )
        data = []
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                row_data = {}
                for idx, cell in enumerate(cells):
                    row_data[f"col_{idx}"] = cell.text.strip()
                data.append(row_data)
            except StaleElementReferenceException:
                continue
        return data

    def search_in_history(self, search_text):
        """Search within the history popup. Requires Enter key press.
        Returns True if search was executed."""
        log.info(f"Searching in history for: {search_text}")
        try:
            search_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model input, mat-dialog-container input",
            )
            for inp in search_inputs:
                try:
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(search_text)
                        inp.send_keys(Keys.RETURN)
                        log.info("History search executed with Enter")
                        return True
                except Exception:
                    continue
            log.warning("No search input found in history panel")
            return False
        except Exception as e:
            log.error(f"History search failed: {e}")
            return False

    def close_history_popup(self):
        """Close the history popup by clicking Cancel via pure JS (fast)."""
        log.info("Closing history popup...")
        self.driver.execute_script("""
            var footers = document.querySelectorAll('.popup-footer');
            for (var i = 0; i < footers.length; i++) {
                var buttons = footers[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.indexOf('Cancel') !== -1
                        || buttons[j].textContent.indexOf('Close') !== -1) {
                        buttons[j].click();
                        return 'clicked';
                    }
                }
            }
            // Fallback: try X icon
            var icons = document.querySelectorAll('.popup-header button mat-icon');
            for (var i = 0; i < icons.length; i++) {
                if (icons[i].textContent.trim().toLowerCase() === 'close') {
                    icons[i].closest('button').click();
                    return 'closed_x';
                }
            }
            throw new Error('Cancel/Close button not found in history popup');
        """)

    # ==============================================================
    #  Dropdown helpers — dynamic option reading (NEVER hardcode)
    # ==============================================================

    def _select_mat_option(self, select_locator, option_text):
        """Open a mat-select dropdown and select a specific option by text.
        Handles internal search textbox if present."""
        log.info(f"Selecting '{option_text}' from dropdown...")

        # Click the mat-select trigger
        try:
            self.click(select_locator)
        except Exception:
            trigger_xpath = (
                f"{select_locator[1]}"
                f"//div[contains(@class,'mat-mdc-select-trigger')]"
            )
            try:
                self.driver.find_element(By.XPATH, trigger_xpath).click()
            except Exception:
                el = self.driver.find_element(By.XPATH, select_locator[1])
                self.driver.execute_script("arguments[0].click();", el)

        # If dropdown has a search textbox, type into it
        try:
            search_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[role='listbox'] input, "
                ".cdk-overlay-pane input[placeholder]",
            )
            for inp in search_inputs:
                try:
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(option_text)
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # Click the matching option
        try:
            opt_locator = (
                "xpath",
                f"//div[@role='listbox']//mat-option"
                f"[contains(.,'{option_text}')]",
            )
            self.click_with_retry(opt_locator)
        except Exception:
            try:
                opt_locator2 = (
                    "xpath",
                    f"//div[@role='listbox']//div[@role='option']"
                    f"[contains(.,'{option_text}')]",
                )
                self.click_with_retry(opt_locator2)
            except Exception:
                opts = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[role='listbox'] mat-option, "
                    "div[role='listbox'] [role='option']",
                )
                for opt in opts:
                    try:
                        if option_text in opt.text:
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});"
                                "arguments[0].click();",
                                opt,
                            )
                            break
                    except Exception:
                        continue

        self._force_close_panels()
        log.info(f"Selected '{option_text}'")

    def _select_random_from_dropdown(
        self, select_locator, label_name, exclude=None
    ):
        """Open a mat-select dropdown and pick a random option.
        Returns the selected option text. Never hardcodes options."""
        log.info(f"Selecting random option from '{label_name}'...")

        # Click the mat-select trigger
        try:
            self.click(select_locator)
        except Exception:
            trigger_xpath = (
                f"{select_locator[1]}"
                f"//div[contains(@class,'mat-mdc-select-trigger')]"
            )
            try:
                self.driver.find_element(By.XPATH, trigger_xpath).click()
            except Exception:
                el = self.driver.find_element(By.XPATH, select_locator[1])
                self.driver.execute_script("arguments[0].click();", el)

        # Wait for options to appear (visibility, not just presence)
        try:
            WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "div[role='listbox'] mat-option, "
                        "div[role='listbox'] [role='option']",
                    )
                )
            )
        except TimeoutException:
            raise Exception(
                f"No options loaded in '{label_name}' dropdown"
            )

        # Small wait for Angular to populate option text content
        time.sleep(0.3)

        # Read all option texts
        options = self.driver.find_elements(
            By.CSS_SELECTOR,
            "div[role='listbox'] mat-option, "
            "div[role='listbox'] [role='option']",
        )
        option_texts = []
        for opt in options:
            try:
                t = opt.text.strip()
                if t and t != "No results found" and not t.startswith("Select"):
                    option_texts.append(t)
            except Exception:
                continue

        if not option_texts:
            raise Exception(
                f"No valid options found in '{label_name}' dropdown"
            )

        # Exclude specific options if requested
        if exclude:
            option_texts = [t for t in option_texts if t not in exclude]
            if not option_texts:
                raise Exception(
                    f"No remaining options in '{label_name}' "
                    f"after excluding {exclude}"
                )

        # Pick a random option and click it
        selected = random.choice(option_texts)
        log.info(f"Random '{label_name}' selected: '{selected}'")
        for opt in options:
            try:
                if opt.text.strip() == selected:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});"
                        "arguments[0].click();",
                        opt,
                    )
                    break
            except Exception:
                continue

        self._force_close_panels()
        return selected

    def get_dropdown_options(self, select_locator):
        """Open a dropdown, read all option texts, then close it."""
        log.info("Reading dropdown options...")
        self._close_select_panel()

        try:
            self.click(select_locator)
        except Exception:
            trigger_xpath = (
                f"{select_locator[1]}"
                f"//div[contains(@class,'mat-mdc-select-trigger')]"
            )
            try:
                self.driver.find_element(By.XPATH, trigger_xpath).click()
            except Exception:
                el = self.driver.find_element(By.XPATH, select_locator[1])
                self.driver.execute_script("arguments[0].click();", el)

        try:
            WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "div.mat-mdc-select-panel mat-option")
                )
            )
        except TimeoutException:
            log.warning("Timed out waiting for dropdown options")

        options = self.driver.find_elements(
            By.CSS_SELECTOR, "div.mat-mdc-select-panel mat-option"
        )
        option_texts = []
        for opt in options:
            try:
                if not opt.is_displayed():
                    continue
                t = opt.text.strip()
                if t and t != "No results found":
                    option_texts.append(t)
            except Exception:
                continue

        self._close_select_panel()
        log.info(f"Dropdown options: {option_texts}")
        return option_texts

    # ==============================================================
    #  Force close form popup (cleanup)
    # ==============================================================

    def force_close_form_popup(self):
        """Force close any open form popup via JS."""
        log.info("Force closing form popup via JS...")
        result = self.driver.execute_script("""
            var popup = document.querySelector('div.edit_pop_up');
            if (popup) {
                var closeBtn = popup.querySelector('button[mat-icon-button] mat-icon');
                if (closeBtn) {
                    var btn = closeBtn.closest('button');
                    if (btn) { btn.click(); return 'clicked close'; }
                }
            }
            // Fallback: remove all overlays
            document.querySelectorAll('mat-dialog-container').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
            return 'force_removed';
        """)
        log.info("Force close result: " + str(result))

    # ==============================================================
    #  One-call convenience methods — optimized with hard_refresh
    # ==============================================================

    def create_vehicle(self, vehicle_data):
        """One-call vehicle creation.
        Returns result dict: status, error, message, data."""
        name = vehicle_data.get("name", "N/A")
        log.info(f"Creating vehicle: {name}")
        result = {
            "status": "FAILED",
            "error": "",
            "message": "",
            "data": copy.deepcopy(vehicle_data),
        }

        try:
            self.open_add_form()
            if not self.is_add_form_open():
                raise Exception("Add form did not open")

            self.fill_vehicle_form(vehicle_data)
            self.submit()

            msg = self.handle_success_alert(timeout=5)
            if msg:
                result["message"] = msg
                result["status"] = "PASSED"
            else:
                if self.is_form_closed():
                    result["message"] = "Form closed (assumed success)"
                    result["status"] = "PASSED"
                else:
                    errors = self.get_mat_error_text()
                    if errors:
                        result["error"] = f"Validation errors: {errors}"
                    else:
                        result["error"] = (
                            "No success message and dialog did not close"
                        )
        except Exception as e:
            result["error"] = str(e)
            log.error(f"Failed to create vehicle '{name}': {e}")

        # Always clean up: remove any leftover overlays/swals
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.swal2-container').forEach(function(el) { el.remove(); });
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            """)
        except Exception:
            pass

        VM_SUBMISSIONS.append(result)
        return result

    def edit_vehicle(self, vehicle_name, updated_data, row_index=0):
        """One-call vehicle edit. Clicks Edit, fills changed fields,
        clicks Update. Returns result dict: status, error, message."""
        log.info(f"Editing vehicle: {vehicle_name}")
        result = {"status": "FAILED", "error": "", "message": ""}

        try:
            if not self.is_vehicle_in_table(vehicle_name):
                self.search_vehicle(vehicle_name)

            self.click_edit_button(vehicle_name=vehicle_name, row_index=row_index)

            if not self.is_edit_mode():
                raise Exception("Edit form did not open (no Update button)")

            # Fill only provided fields
            if updated_data.get("name"):
                self.type_text(
                    self.NAME_INPUT, str(updated_data["name"]),
                    clear_first=True,
                )
            if updated_data.get("price"):
                self.type_text(
                    self.PRICE_INPUT, str(updated_data["price"]),
                    clear_first=True,
                )
            if updated_data.get("vehicle_type"):
                self._select_mat_option(
                    self.VEHICLE_TYPE_SELECT,
                    str(updated_data["vehicle_type"]),
                )
            if updated_data.get("fuel_type"):
                self._select_mat_option(
                    self.FUEL_TYPE_SELECT,
                    str(updated_data["fuel_type"]),
                )
            if updated_data.get("description"):
                self.type_text(
                    self.DESCRIPTION_INPUT,
                    str(updated_data["description"]),
                    clear_first=True,
                )

            self._force_close_panels()
            self.click_update()

            msg = self.handle_success_alert(timeout=5)
            if msg:
                result["message"] = msg
                result["status"] = "PASSED"
            else:
                if self.is_form_closed():
                    result["message"] = "Form closed (assumed success)"
                    result["status"] = "PASSED"
                else:
                    result["error"] = "No success message after edit"
        except Exception as e:
            result["error"] = str(e)
            log.error(f"Failed to edit vehicle '{vehicle_name}': {e}")

        VM_SUBMISSIONS.append(result)
        return result

    def view_vehicle(self, vehicle_name=None, row_index=0):
        """One-call vehicle view. Clicks View, reads fields,
        closes popup. Returns dict of field values."""
        log.info(f"Viewing vehicle: {vehicle_name or row_index}")
        try:
            self.click_view_button(
                vehicle_name=vehicle_name, row_index=row_index
            )
            values = self.get_form_field_values()
            log.info(f"Vehicle details: {values}")
            self.close_popup()
            return values
        except Exception as e:
            log.error(f"Failed to view vehicle: {e}")
            return None

    def check_history(self, vehicle_name=None, row_index=0,
                      search_text=None):
        """One-call history check. Opens History, reads row count,
        optionally searches, then closes popup."""
        log.info(f"Checking history for: {vehicle_name or row_index}")
        result = {
            "row_count": 0,
            "search_found": None,
            "data": [],
            "error": "",
        }

        try:
            if vehicle_name and not self.is_vehicle_in_table(vehicle_name):
                self.search_vehicle(vehicle_name)

            self.click_history_button(
                vehicle_name=vehicle_name, row_index=row_index
            )

            result["row_count"] = self.get_history_row_count()
            result["data"] = self.get_history_data()

            if search_text:
                result["search_found"] = self.search_in_history(search_text)

            self.close_history_popup()

        except Exception as e:
            result["error"] = str(e)

        return result

    # ==============================================================
    #  Bulk creation — optimized with hard_refresh
    # ==============================================================

    def create_bulk_vehicles(self, vehicles_list, on_progress=None):
        """Create multiple vehicles in sequence.
        Returns list of result dicts."""
        total = len(vehicles_list)
        results = []

        for i, vdata in enumerate(vehicles_list, 1):
            name = vdata.get("name", f"Vehicle_{i}")
            log.info(f"[{i}/{total}] Creating: {name}")
            start_time = time.time()
            result = self.create_vehicle(vdata)
            elapsed = time.time() - start_time
            result["index"] = i
            result["duration"] = round(elapsed, 1)
            results.append(result)

            # Cleanup between creations — use hard_refresh (fast)
            try:
                self.force_close_form_popup()
                self.hard_refresh()
            except Exception:
                try:
                    self.navigate_to_page()
                except Exception:
                    pass

            if on_progress:
                on_progress(i, total, name)

        passed = sum(1 for r in results if r["status"] == "PASSED")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        log.separator()
        log.info(
            f" BULK COMPLETE: {passed}/{total} passed, {failed} failed"
        )
        log.separator()

    # ==============================================================
    #  Internal utilities — UOM pattern
    # ==============================================================

    def _js_click_popup_button(self, button_text):
        """Click a popup footer button (Submit/Update) via JS — bypasses overlay issues."""
        js = """
        var footers = document.querySelectorAll('.popup-footer');
        for (var i = 0; i < footers.length; i++) {
            var buttons = footers[i].querySelectorAll('button');
            for (var j = 0; j < buttons.length; j++) {
                if (buttons[j].textContent.trim().indexOf(arguments[0]) !== -1) {
                    buttons[j].click();
                    return 'clicked_' + arguments[0];
                }
            }
        }
        throw new Error('Button "' + arguments[0] + '" not found in popup footer');
        """
        try:
            result = self.driver.execute_script(js, button_text)
            log.info("JS click " + button_text + ": " + str(result))
        except Exception as e:
            log.warning("JS click failed for " + button_text + ", falling back to Selenium: " + str(e))
            if button_text == 'Submit':
                self.click_with_retry(self.SUBMIT_BUTTON)
            elif button_text == 'Update':
                self.click_with_retry(self.UPDATE_BUTTON)

    def _dismiss_swal(self, button, label):
        """Dismiss a SweetAlert popup by clicking the specified button via JS."""
        try:
            self.driver.find_element("css selector", ".swal2-popup")
            self.driver.execute_script("""
                var btn = document.querySelector(arguments[0]);
                if (btn) { btn.click(); }
            """, button)
            log.info("Dismissed SweetAlert via " + label)
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
                )
            except Exception:
                pass
        except Exception as e:
            log.warning("No SweetAlert to dismiss: " + str(e))
