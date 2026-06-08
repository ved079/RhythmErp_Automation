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
  - View / Edit / History   (action buttons per row)
  - Item Category / Item Description / Level

NOTES:
  - NO Status toggle
  - NO dropdowns
  - NO Delete button
  - HAS History button
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
        """Click the History button on a table row."""
        log.info(f"Clicking History button (name={item_name}, row={row_index})...")

        self._force_close_panels()

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
                    self.wait_seconds(2)
                    return True
            except Exception as e:
                log.warning(f"History button by name failed: {e}")

        # Fallback: find archive column button by row index
        row = row_index + 1

        # Debug: count rows and archive cells
        rows_found = self.driver.find_elements(By.CSS_SELECTOR, "tr.mat-mdc-row")
        archive_cells = self.driver.find_elements(By.CSS_SELECTOR, "td.cdk-column-archive")
        log.info(f"Debug: {len(rows_found)} table rows, {len(archive_cells)} archive cells")

        # Try CSS selector approach (more reliable than XPath)
        try:
            archive_btn = self.driver.find_elements(
                By.CSS_SELECTOR,
                f"tr.mat-mdc-row:nth-child({row}) td.cdk-column-archive button"
            )
            log.info(f"Debug: Found {len(archive_btn)} archive buttons in row {row}")

            if archive_btn:
                btn = archive_btn[0]
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", btn
                )
                self.wait_seconds(0.5)
                self.driver.execute_script("arguments[0].click();", btn)
                log.info("History button clicked via JS")
                self.wait_seconds(2)
                return True
        except Exception as e:
            log.warning(f"CSS selector approach failed: {e}")

        # Last resort: find ALL archive buttons and click by index
        try:
            all_archive_btns = self.driver.find_elements(
                By.CSS_SELECTOR, "td.cdk-column-archive button"
            )
            log.info(f"Debug: Total {len(all_archive_btns)} archive buttons on page")

            if row_index < len(all_archive_btns):
                btn = all_archive_btns[row_index]
                self.driver.execute_script("arguments[0].click();", btn)
                log.info(f"History button clicked by index {row_index}")
                self.wait_seconds(2)
                return True
        except Exception as e:
            log.warning(f"Index approach failed: {e}")

        raise Exception(f"History button not found for row {row_index}")

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
        except Exception as e:
            log.warning(f"Failed to click action button: {e}")
        return False

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
    #  History popup
    # ==============================================================

    def is_history_popup_open(self):
        """Check if the History popup is visible."""
        try:
            # Check all possible popup/overlay containers
            selectors = [
                "mat-dialog-container",
                "cdk-overlay-pane",
                "div.big-model",
                "div.edit_pop_up",
                "div.cdk-overlay-pane",
                "div.mat-mdc-dialog-surface",
            ]
            for sel in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for el in elements:
                    try:
                        if el.is_displayed():
                            text = el.text.lower()
                            if "history" in text:
                                log.info(f"History popup found via selector: {sel}")
                                return True
                    except Exception:
                        continue

            # Nuclear option: find ANY visible overlay with "history" text
            overlays = self.driver.find_elements(
                By.CSS_SELECTOR,
                "[class*='overlay'], [class*='dialog'], [class*='popup'], [class*='modal']"
            )
            for o in overlays:
                try:
                    if o.is_displayed():
                        text = o.text.lower()
                        if "history" in text:
                            log.info(f"History popup found via overlay search")
                            return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def close_history_popup(self):
        """Close the History popup by clicking Cancel/Close."""
        try:
            btn = self.find_visible_element(self.HISTORY_CLOSE_BUTTON, timeout=5)
            if btn:
                log.info(f"History button found, clicking...")
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
        except Exception:
            # Force close via JS
            self.driver.execute_script("""
                document.querySelectorAll('.big-model, .edit_pop_up').forEach(
                    function(el) { el.remove(); }
                );
            """)
        self._force_close_panels()

    def get_history_table_row_count(self):
        """Get the number of rows in the history popup table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-body table tbody tr, .big-model table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def get_history_table_headers(self):
        """Get the column headers from the history popup table."""
        headers = []
        try:
            ths = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-body table thead th, .big-model table thead th"
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
                # Fallback: get all non-action cells from column 3 (after View/Edit/History)
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, "table#excel-table tbody tr"
                )
                for row in rows:
                    try:
                        tds = row.find_elements(By.CSS_SELECTOR, "td")
                        # Skip action columns (typically first 3)
                        for td in tds[3:]:
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

    def search_item(self, search_text):
        """Search for an item using the search input."""
        log.info(f"Searching for: {search_text}")
        try:
            # Toggle search bar if needed
            try:
                search_toggle = self.driver.find_element(
                    By.CSS_SELECTOR, "button.search-btn, button[aria-label='Search']"
                )
                if search_toggle.is_displayed():
                    self.driver.execute_script("arguments[0].click();", search_toggle)
                    self.wait_seconds(0.5)
            except Exception:
                pass

            # Type in search input
            search_input = self.driver.find_element(
                By.CSS_SELECTOR,
                "input#erpSearchInput, .erp-search-wrapper input"
            )
            search_input.clear()
            search_input.send_keys(search_text)
            self.wait_seconds(2)

        except Exception as e:
            log.warning(f"Search failed: {e}")

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
