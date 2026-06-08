"""
item_category_page.py
---------------------
Page Object Model for RhythmERP Item Category screen.

Location: Commodity Settings > Item Category
URL:      /#/dynamic-screens/Item%20Category

FORM LAYOUT (Simple popup — NOT a stepper):
  - Item Category       (text input,   required)
  - Item Description    (text input,   required)
  - Level               (number input, required — accepts negatives, no decimals,
                         leading zeros stripped on save, accepts 0)
  [Cancel] [Submit]

TABLE COLUMNS (main listing):
  - Actions (3-dot menu: View / Edit / History)
  - Item Category / Item Description / Level

NOTES:
  - NO Status toggle
  - NO dropdowns
  - NO Delete button
  - HAS History button (via 3-dot menu)
  - Duplicates ALLOWED for Item Category name
  - Level field: accepts negative integers, strips leading zeros on save,
    accepts 0, does NOT accept decimals

POPUP TYPES:
  Type A — "Validation Failed - Please correct the highlighted fields"
            Appears when required fields are empty (client-side).
            Has .swal2-confirm button.
  Type B — "Failed to save record"
            Appears when server-side validation rejects data.
            MUST use JS dismiss to avoid StaleElementReferenceException.

KEY RULES:
  - NEVER use Keys.ESCAPE (closes entire popup form!)
  - JS clicks for Angular Material overlays
  - ALL SweetAlert2 dismissals MUST use JS querySelector click
  - Row actions use 3-dot menu (cdk-column-actions) matching UOM golden standard
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
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT

# Global list to track every submission for reporting
IC_SUBMISSIONS = []


class ItemCategoryPage(BasePage):
    """Page Object for Item Category screen."""

    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Item%20Category"

    # ==============================================================
    #  LOCATORS - Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    SEARCH_BUTTON = ("css", "button.search-btn")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    FILTER_BUTTON = ("css", "div[mattooltip='Filters'] button")

    # ==============================================================
    #  LOCATORS - Search bar
    # ==============================================================
    SEARCH_INPUT = ("css", "input#erpSearchInput")

    # ==============================================================
    #  LOCATORS - Table (main listing)
    # ==============================================================
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    TABLE_CATEGORY_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-item_category, "
        "table#excel-table tbody td.mat-column-item_category, "
        "table#excel-table tbody td.cdk-column-itemCategory, "
        "table#excel-table tbody td.mat-column-itemCategory",
    )
    TABLE_DESCRIPTION_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-item_description, "
        "table#excel-table tbody td.mat-column-item_description, "
        "table#excel-table tbody td.cdk-column-itemDescription, "
        "table#excel-table tbody td.mat-column-itemDescription",
    )
    TABLE_LEVEL_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-level, "
        "table#excel-table tbody td.mat-column-level",
    )
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody tr td.no-data, "
        "table#excel-table tbody tr.mat-mdc-no-data-row",
    )

    # ==============================================================
    #  LOCATORS - Row action buttons (3-dot menu pattern — UOM golden standard)
    # ==============================================================
    ACTIONS_COLUMN = ("css", "td.cdk-column-actions")
    THREE_DOT_MENU_BUTTON = ("css", "td.cdk-column-actions button")

    # ==============================================================
    #  LOCATORS - Popup form
    # ==============================================================
    FORM_POPUP = (
        "css",
        ".edit_pop_up.override_edit_pop_up.popup-mode, "
        ".big-model, mat-dialog-container",
    )

    # Text inputs — using XPath by label for reliability
    ITEM_CATEGORY_INPUT = (
        "xpath",
        "//mat-label[contains(.,'Item Category') or contains(.,'Item category')]"
        "/ancestor::mat-form-field//input",
    )
    ITEM_DESCRIPTION_INPUT = (
        "xpath",
        "//mat-label[contains(.,'Item Description') or contains(.,'Item description')]"
        "/ancestor::mat-form-field//input",
    )
    LEVEL_INPUT = (
        "xpath",
        "//mat-label[contains(.,'Level') or contains(.,'level')]"
        "/ancestor::mat-form-field//input",
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
    #  LOCATORS - History popup (UOM golden standard — app-dynamic-history)
    # ==============================================================
    HISTORY_HEADER = ("css", "app-dynamic-history .tbl-title h2")
    HISTORY_NO_DATA = ("css", "app-dynamic-history .no-data, app-dynamic-history img[alt='No Data Available']")
    HISTORY_NO_DATA_TEXT = ("xpath", "//app-dynamic-history//*[contains(text(),'No data available')]")
    HISTORY_SEARCH_INPUT = ("css", "app-dynamic-history input#erpSearchInput")
    HISTORY_TABLE_ROWS = ("css", "app-dynamic-history table#excel-table tbody tr")
    HISTORY_CANCEL_BUTTON = ("xpath", "//app-dynamic-history//div[@class='popup-footer']//button[contains(.,'Cancel')]")
    HISTORY_COL_CREATED_TIME = ("css", "app-dynamic-history td.cdk-column-created_date_time")
    HISTORY_COL_UPDATED_TIME = ("css", "app-dynamic-history td.cdk-column-updated_date_time")

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
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Item Category listing page.
        Force-refreshes to clear leftover Angular state.
        """
        log.info("Navigating to Item Category page...")
        self.navigate_to(self.PAGE_URL)
        self._wait_for_page_ready()

    def hard_refresh(self):
        """Hard refresh the current page (Ctrl+R) and wait for it to be ready.
        Much faster than full navigate_to_page() for resetting between tests."""
        log.info("Hard refreshing page")
        self.driver.refresh()
        self._wait_for_page_ready()
        log.info("Page refreshed and ready")

    def _wait_for_page_ready(self):
        """Wait until the page is fully loaded. Fast — uses short timeouts.
        Optimised (v3): reduced primary timeout from 15s→10s, fallback from 5s→3s
        matching QP Master / Services Master golden standard."""
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: d.find_elements("css selector", "table#excel-table")
            )
            log.info("Page ready (table found)")
        except Exception:
            # Fallback: check for search button
            try:
                WebDriverWait(self.driver, 3).until(
                    lambda d: d.find_elements("css selector", "button.search-btn")
                )
                log.info("Page ready (search button found, no table)")
            except Exception:
                log.warning("Page ready check timed out")

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
        log.info("Clicking ADD button on Item Category...")
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
                    log.info("ADD form opened on Item Category")
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
                            log.info("ADD form opened via mini-fab on Item Category")
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
                log.info("ADD form opened via click_with_retry on Item Category")
                return
        except Exception:
            pass

        raise Exception("ADD button not found or not clickable on Item Category")

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
        """Check if the Add form is open by looking for Item Category input."""
        return self.is_displayed(self.ITEM_CATEGORY_INPUT, timeout=5)

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
        """Fill all fields on the Item Category popup form.

        Fill order: Item Category -> Item Description -> Level
        """
        log.info("Filling Item Category form...")

        # 1. Item Category (required)
        if "item_category" in data:
            if data["item_category"] is not None:
                self.type_text(self.ITEM_CATEGORY_INPUT, str(data["item_category"]), clear_first=True)

        # 2. Item Description (required)
        if "item_description" in data:
            if data["item_description"] is not None:
                self.type_text(self.ITEM_DESCRIPTION_INPUT, str(data["item_description"]), clear_first=True)

        # 3. Level (required — number field)
        if "level" in data:
            if data["level"] is not None:
                self.type_text(self.LEVEL_INPUT, str(data["level"]), clear_first=True)

        self._force_close_panels()
        log.info("Item Category form filled")

    # ==============================================================
    #  Submit / Update / Cancel
    # ==============================================================

    def submit(self):
        """Click the Submit button (Create mode)."""
        log.info("Submitting Item Category form...")
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
    #  Row action buttons (3-dot menu — UOM golden standard)
    # ==============================================================

    def _get_row_category_name(self, row_index):
        """Get the Item Category name from a specific row by index.
        Used as fallback when clicking action menu by index."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_index < len(rows):
                cells = rows[row_index].find_elements(By.CSS_SELECTOR, "td")
                for cell in cells:
                    cls = cell.get_attribute("class") or ""
                    if "cdk-column-item_category" in cls or "mat-column-item_category" in cls \
                            or "cdk-column-itemCategory" in cls or "mat-column-itemCategory" in cls:
                        return cell.text.strip()
                # Fallback: return first non-action cell text
                for cell in cells:
                    cls = cell.get_attribute("class") or ""
                    if "cdk-column-actions" not in cls:
                        text = cell.text.strip()
                        if text:
                            return text
        except Exception:
            pass
        return ""

    def _click_action_menu_item(self, item_name, action_name):
        """Click an action menu item (View/Edit/History) for a specific Item Category row.
        The live system uses a 3-dot (⋮) menu button in cdk-column-actions.
        Pure JS — finds row by name, clicks 3-dot menu, waits for CDK overlay, clicks named item.
        Matches UOM golden standard pattern."""
        log.info("Clicking " + action_name + " via 3-dot menu for Item Category: " + item_name)
        js = """
        var table = document.querySelector('table#excel-table');
        if (!table) { throw new Error('Table not found'); }
        var rows = table.querySelectorAll('tbody tr');
        for (var i = 0; i < rows.length; i++) {
            var cells = rows[i].querySelectorAll('td');
            for (var j = 0; j < cells.length; j++) {
                if (cells[j].textContent.trim().indexOf(arguments[0]) !== -1) {
                    var menuBtn = rows[i].querySelector('td.cdk-column-actions button');
                    if (!menuBtn) { throw new Error('3-dot menu button not found in actions column'); }
                    menuBtn.scrollIntoView({block:'center'});
                    menuBtn.click();
                    return 'menu_opened';
                }
            }
        }
        throw new Error('Item Category ' + arguments[0] + ' not found in table');
        """
        result = self.driver.execute_script(js, item_name)
        log.info("3-dot menu opened for Item Category: " + item_name)

        # Wait briefly for dropdown to render
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(("css selector", ".cdk-overlay-container .cdk-overlay-pane"))
            )
        except Exception:
            pass

        # Click the specific menu item from the dropdown overlay
        js_click_item = """
        var overlay = document.querySelector('.cdk-overlay-container');
        if (!overlay) { throw new Error('CDK overlay not found after menu click'); }
        var items = overlay.querySelectorAll('button, span, div');
        for (var i = 0; i < items.length; i++) {
            var text = items[i].textContent.trim();
            if (text === arguments[0]) {
                items[i].click();
                return 'clicked_' + arguments[0];
            }
        }
        // Fallback: try partial match
        for (var i = 0; i < items.length; i++) {
            var text = items[i].textContent.trim().toLowerCase();
            if (text.indexOf(arguments[0].toLowerCase()) !== -1) {
                items[i].click();
                return 'clicked_partial_' + arguments[0];
            }
        }
        throw new Error('Menu item "' + arguments[0] + '" not found in dropdown overlay');
        """
        result = self.driver.execute_script(js_click_item, action_name)
        log.info("Successfully clicked " + action_name + " for Item Category: " + item_name)
        return result

    def _click_action_menu_by_index(self, row_index, action_name):
        """Click an action menu item by row index (fallback when item_name is not available).
        Opens the 3-dot menu for the row at the given index, then clicks the named action."""
        log.info("Clicking " + action_name + " via 3-dot menu by row index: " + str(row_index))
        js = """
        var table = document.querySelector('table#excel-table');
        if (!table) { throw new Error('Table not found'); }
        var rows = table.querySelectorAll('tbody tr');
        if (arguments[0] >= rows.length) { throw new Error('Row index ' + arguments[0] + ' out of range'); }
        var menuBtn = rows[arguments[0]].querySelector('td.cdk-column-actions button');
        if (!menuBtn) { throw new Error('3-dot menu button not found in actions column for row ' + arguments[0]); }
        menuBtn.scrollIntoView({block:'center'});
        menuBtn.click();
        return 'menu_opened';
        """
        try:
            result = self.driver.execute_script(js, row_index)
            log.info("3-dot menu opened for row index: " + str(row_index))
        except Exception as e:
            log.warning("Failed to open 3-dot menu for row index " + str(row_index) + ": " + str(e))
            return False

        # Wait briefly for dropdown to render
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(("css selector", ".cdk-overlay-container .cdk-overlay-pane"))
            )
        except Exception:
            pass

        # Click the specific menu item
        js_click_item = """
        var overlay = document.querySelector('.cdk-overlay-container');
        if (!overlay) { throw new Error('CDK overlay not found after menu click'); }
        var items = overlay.querySelectorAll('button, span, div');
        for (var i = 0; i < items.length; i++) {
            var text = items[i].textContent.trim();
            if (text === arguments[0]) {
                items[i].click();
                return 'clicked_' + arguments[0];
            }
        }
        // Fallback: try partial match
        for (var i = 0; i < items.length; i++) {
            var text = items[i].textContent.trim().toLowerCase();
            if (text.indexOf(arguments[0].toLowerCase()) !== -1) {
                items[i].click();
                return 'clicked_partial_' + arguments[0];
            }
        }
        throw new Error('Menu item "' + arguments[0] + '" not found in dropdown overlay');
        """
        try:
            result = self.driver.execute_script(js_click_item, action_name)
            log.info("Successfully clicked " + action_name + " for row index: " + str(row_index))
            return True
        except Exception as e:
            log.warning("Failed to click " + action_name + " for row index " + str(row_index) + ": " + str(e))
            return False

    def click_view_button(self, item_name=None, row_index=0):
        """Click the View button on a table row via 3-dot menu (UOM golden standard)."""
        log.info("Clicking View button (name={}, row={})...".format(item_name, row_index))
        if item_name:
            self._click_action_menu_item(item_name, "View")
            # Wait for view popup to appear
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(("css selector", ".popup-header h3"))
                )
            except Exception:
                pass
            return True
        else:
            # Fallback: use row index
            return self._click_action_menu_by_index(row_index, "View")

    def click_edit_button(self, item_name=None, row_index=0):
        """Click the Edit button on a table row via 3-dot menu (UOM golden standard)."""
        log.info("Clicking Edit button (name={}, row={})...".format(item_name, row_index))
        if item_name:
            self._click_action_menu_item(item_name, "Edit")
            # Wait for edit popup to appear
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(("css selector", "input"))
                )
            except Exception:
                pass
            return True
        else:
            # Fallback: use row index
            return self._click_action_menu_by_index(row_index, "Edit")

    def click_history_button(self, item_name=None, row_index=0):
        """Click the History button on a table row via 3-dot menu (UOM golden standard)."""
        log.info("Clicking History button (name={}, row={})...".format(item_name, row_index))

        self._force_close_panels()

        if item_name:
            self._click_action_menu_item(item_name, "History")
            # Wait for history popup to appear
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(("css selector", "app-dynamic-history"))
                )
            except Exception:
                pass
            return True
        else:
            # Fallback: use row index
            return self._click_action_menu_by_index(row_index, "History")

    # ==============================================================
    #  Mode detection
    # ==============================================================

    def is_edit_mode(self):
        """Check if the form is in Edit mode (has Update button)."""
        return self.is_displayed(self.UPDATE_BUTTON, timeout=5)

    def is_view_mode(self):
        """Check if the form is in View mode (all fields disabled, no Submit/Update)."""
        has_submit = self.is_displayed(self.SUBMIT_BUTTON, timeout=2)
        has_update = self.is_displayed(self.UPDATE_BUTTON, timeout=2)
        if has_submit or has_update:
            return False

        # Check if Item Category input is disabled
        try:
            cat_input = self.driver.find_element(
                By.XPATH,
                "//mat-label[contains(.,'Item Category')]"
                "/ancestor::mat-form-field//input"
            )
            if not cat_input.is_enabled():
                return True
        except Exception:
            pass
        return False

    # ==============================================================
    #  History popup (UOM golden standard — app-dynamic-history)
    # ==============================================================

    def is_history_popup_open(self):
        """Check if the History popup is visible (UOM golden standard — checks for app-dynamic-history element)."""
        try:
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, "app-dynamic-history"
            )
            for el in elements:
                try:
                    if el.is_displayed():
                        log.info("History popup found via app-dynamic-history")
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def close_history_popup(self):
        """Close the History popup by clicking Cancel using pure JS (UOM golden standard)."""
        log.info("Closing History popup")
        js = """
        var footers = document.querySelectorAll('app-dynamic-history .popup-footer');
        if (footers.length === 0) {
            footers = document.querySelectorAll('.popup-footer');
        }
        for (var i = 0; i < footers.length; i++) {
            var buttons = footers[i].querySelectorAll('button');
            for (var j = 0; j < buttons.length; j++) {
                if (buttons[j].textContent.indexOf('Cancel') !== -1) {
                    buttons[j].click();
                    return 'clicked';
                }
            }
        }
        throw new Error('Cancel button not found in any popup-footer');
        """
        try:
            self.driver.execute_script(js)
            log.info("History popup closed via JS Cancel click")
        except Exception as e:
            log.warning("JS Cancel click failed: " + str(e))
            # Force close via JS
            self.driver.execute_script("""
                document.querySelectorAll('.big-model, .edit_pop_up').forEach(
                    function(el) { el.remove(); }
                );
            """)
        self._force_close_panels()

    def is_history_empty(self):
        """Check if the History popup shows 'No data available'.
        Returns True if empty, False if data exists. (UOM golden standard)"""
        log.info("Checking if History is empty")
        no_data = self.is_present(self.HISTORY_NO_DATA, timeout=5)
        no_data_text = self.is_present(self.HISTORY_NO_DATA_TEXT, timeout=5)
        is_empty = no_data or no_data_text
        log.info("History empty: " + str(is_empty))
        return is_empty

    def get_history_table_row_count(self):
        """Get the number of rows in the history popup table (UOM golden standard — app-dynamic-history selectors)."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "app-dynamic-history table#excel-table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def get_history_table_headers(self):
        """Get the column headers from the history popup table (UOM golden standard — app-dynamic-history selectors)."""
        headers = []
        try:
            ths = self.driver.find_elements(
                By.CSS_SELECTOR, "app-dynamic-history table thead th"
            )
            for th in ths:
                try:
                    text = th.text.strip()
                    if text:
                        headers.append(text)
                except Exception:
                    continue
        except Exception:
            pass
        return headers

    # ==============================================================
    #  Table data helpers
    # ==============================================================

    def get_table_row_count(self):
        """Get the number of data rows in the main table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            # Filter out "no data" rows
            data_rows = []
            for row in rows:
                try:
                    tds = row.find_elements(By.CSS_SELECTOR, "td")
                    if tds and not any("no-data" in (td.get_attribute("class") or "")
                                       for td in tds):
                        data_rows.append(row)
                except Exception:
                    continue
            return len(data_rows)
        except Exception:
            return 0

    def get_all_item_names(self):
        """Get all Item Category names from the table."""
        names = []
        try:
            # Try multiple column class names
            cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody td.cdk-column-item_category, "
                "table#excel-table tbody td.mat-column-item_category, "
                "table#excel-table tbody td.cdk-column-itemCategory, "
                "table#excel-table tbody td.mat-column-itemCategory"
            )
            if not cells:
                # Fallback: get first non-action cell from each row
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, "table#excel-table tbody tr"
                )
                for row in rows:
                    try:
                        tds = row.find_elements(By.CSS_SELECTOR, "td")
                        for td in tds:
                            cls = td.get_attribute("class") or ""
                            if "cdk-column-actions" not in cls:
                                text = td.text.strip()
                                if text:
                                    names.append(text)
                                    break
                    except Exception:
                        continue
            else:
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

    def get_cell_text_by_row(self, row_index, column_index):
        """Get text from a specific cell by row and column index."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_index < len(rows):
                cells = rows[row_index].find_elements(By.CSS_SELECTOR, "td")
                if column_index < len(cells):
                    return cells[column_index].text.strip()
        except Exception:
            pass
        return ""

    def is_record_in_table(self, name):
        """Check if a record with the given name exists in the table."""
        names = self.get_all_item_names()
        return any(name in n for n in names)

    # ==============================================================
    #  Search (UOM golden standard — JS-based with Angular events)
    # ==============================================================

    def search_item(self, search_text):
        """Search for an item using the search input. Uses JS clicks to bypass overlay issues.
        The search button (button.search-btn) is often overlapped on the live system
        and never becomes Selenium-clickable, so we click it via JavaScript instead.
        Matches UOM golden standard search_uom() pattern."""
        log.info("Searching for: " + str(search_text))

        # Step 1: Check if search input is already visible
        search_input = None
        try:
            el = self.driver.find_element("css selector", "input#erpSearchInput")
            rect = self.driver.execute_script(
                "var r = arguments[0].getBoundingClientRect(); "
                "return r.width > 0 && r.height > 0;", el
            )
            if rect:
                search_input = el
                log.info("Search input already visible, skipping button click")
        except Exception:
            pass

        # Step 2: If search input not visible, click search button via JS to open it
        if search_input is None:
            log.info("Search input not visible, clicking search button via JS")
            js_click_search = """
            var btn = document.querySelector('button.search-btn');
            if (!btn) { throw new Error('Search button not found in DOM'); }
            btn.scrollIntoView({block:'center'});
            btn.click();
            return 'clicked';
            """
            try:
                result = self.driver.execute_script(js_click_search)
                log.info("Search button clicked via JS: " + str(result))
            except Exception as e:
                log.error("Failed to click search button via JS: " + str(e))
                return

            # Wait for search input to become visible
            try:
                search_input = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located(("css selector", "input#erpSearchInput"))
                )
                log.info("Search input became visible")
            except Exception:
                log.warning("Search input did not become visible after clicking search button")
                return

        # Step 3: Clear existing value completely
        self.driver.execute_script("arguments[0].value = '';", search_input)
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
            search_input,
        )

        # Step 4: Set new value and fire Angular change events
        self.driver.execute_script(
            "arguments[0].value = arguments[1];", search_input, search_text
        )
        search_input.click()
        for event in ["input", "keyup", "change"]:
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('" + event + "', { bubbles: true }));",
                search_input,
            )

        # Step 5: Click the search button again via JS to submit/filter the table
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

        log.info("Search completed for: " + str(search_text))

    def search_and_verify(self, name):
        """Search for an item category name, then verify it exists in the filtered results.
        This is the recommended way to verify a create/update — uses search
        instead of scanning all rows (handles pagination automatically).
        Returns True if found. (UOM golden standard pattern)"""
        log.info("Searching and verifying Item Category: " + str(name))
        self.search_item(name)
        return self.is_ic_in_table(name)

    def is_ic_in_table(self, name):
        """Check if an Item Category name exists in the main table (current view only).
        Polls up to 10s to handle slow Angular re-renders.
        Returns True if found, raises AssertionError if not. (UOM golden standard pattern)"""
        log.info("Verifying Item Category '{}' exists in table".format(name))
        end_time = time.monotonic() + 10
        last_seen = []
        while time.monotonic() < end_time:
            try:
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, "table#excel-table tbody tr"
                )
                last_seen = []
                for row in rows:
                    cells = row.find_elements(By.CSS_SELECTOR, "td")
                    row_text = " | ".join(c.text.strip() for c in cells if c.text.strip())
                    last_seen.append(row_text)
                    for cell in cells:
                        if name in cell.text.strip():
                            log.info("Item Category '{}' found in table".format(name))
                            return True
            except Exception:
                pass
            time.sleep(0.5)
        log.error("Item Category '{}' NOT found. Table contents were: {}".format(name, last_seen))
        raise AssertionError(
            "Item Category '{}' NOT found in table after search. Last table rows: {}".format(name, last_seen)
        )

    def clear_search(self):
        """Clear the search input and refresh to get clean state. (UOM golden standard pattern)"""
        log.info("Clearing search - hard refreshing")
        self.hard_refresh()

    # ==============================================================
    #  Field value helpers
    # ==============================================================

    def get_field_value(self, field_locator):
        """Get the current value of a form field."""
        try:
            el = self.find_visible_element(field_locator, timeout=5)
            return el.get_attribute("value") or ""
        except Exception:
            return ""

    def is_field_enabled(self, field_locator):
        """Check if a form field is enabled (not disabled)."""
        try:
            el = self.find_visible_element(field_locator, timeout=5)
            return el.is_enabled()
        except Exception:
            return False

    def get_input_value(self, locator):
        """Get the value attribute of an input field."""
        try:
            el = self.find_visible_element(locator, timeout=5)
            return el.get_attribute("value") or ""
        except Exception:
            return ""

    # ==============================================================
    #  Smart cleanup (golden standard — UOM/SM pattern)
    # ==============================================================

    def _cleanup(self):
        """Smart cleanup — close any open popups/forms, then hard refresh.
        (UOM golden standard pattern — much faster than try/except/cancel/force_close/refresh)
        Uses JS checks instead of Selenium is_displayed for speed.
        """
        # Fast JS check: is any popup/form open?
        try:
            popup_open = self.driver.execute_script("""
                var popup = document.querySelector(
                    'div.big-model, mat-dialog-container, ' +
                    'div.edit_pop_up.override_edit_pop_up.popup-mode'
                );
                return popup && popup.offsetParent !== null;
            """)
            if popup_open:
                # Close popup via JS (fast, no Selenium)
                self.driver.execute_script("""
                    var closeBtn = document.querySelector(
                        '.popup-header button[mat-icon-button], ' +
                        '.popup-header button mat-icon'
                    );
                    if (closeBtn) {
                        var btn = closeBtn.closest('button') || closeBtn;
                        btn.click();
                    }
                """)
                time.sleep(0.1)
        except Exception:
            pass

        # Always clean up any leftover overlays/swal
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.swal2-container')
                    .forEach(function(el) { el.remove(); });
            """)
        except Exception:
            pass
        self._force_close_panels()

        # Hard refresh — fastest way to reset between tests
        self.hard_refresh()

    def dismiss_any_validation_alert(self):
        """Dismiss any SweetAlert validation popup — try Cancel first, then OK. (UOM golden standard)"""
        log.info("Dismissing any validation alert")
        self.driver.execute_script("""
            var cancel = document.querySelector('.swal2-cancel');
            if (cancel) { cancel.click(); return 'Cancel'; }
            var confirm = document.querySelector('.swal2-confirm');
            if (confirm) { confirm.click(); return 'OK'; }
            return 'none';
        """)
        # Wait for SweetAlert to disappear
        try:
            WebDriverWait(self.driver, 2).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-container")
                )
            )
        except Exception:
            pass
