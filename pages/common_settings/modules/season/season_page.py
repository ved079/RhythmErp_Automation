"""
season_page.py
--------------
Page Object Model for RhythmERP Season screen (Common Settings).
Extends BasePage with Season-specific locators and methods.

Fields: Name (required), Description (optional), Status (checkbox).
Pattern: List view + popup form (Add / Edit / View).

Live-verified: 2026-06-02 against https://rhythmerp.algorhythms.in
Key DOM findings:
  - Action buttons use kebab menu (more_vert) -> menu items, NOT tblActnBtn
  - Icon elements are <i class="material-icons">, NOT <mat-icon>
  - Table columns: Actions(1), Name(2), Description(3), Status(4)
  - History "No data" uses <img> + <p>, NOT div[style*='text-align']
"""

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from common.base_page import BasePage
from common.logger import log


class SeasonPage(BasePage):
    """
    Page Object for Common Settings > Season screen.
    """

    # ================================================================
    # COLUMN INDICES — 1-based for XPath td[N]
    # Live DOM: Actions=td[1], Name=td[2], Description=td[3], Status=td[4]
    # ================================================================
    COL_ACTIONS = 1
    COL_NAME = 2
    COL_DESCRIPTION = 3
    COL_STATUS = 4

    # ================================================================
    # LOCATORS — Form Popup
    # ================================================================

    # --- Form Container ---
    FORM_POPUP = ("css", "div.edit_pop_up")
    FORM_CONTENT = ("css", "div.edit_pop_up div.overflow_model")
    FORM_HEADER_TITLE = ("css", "div.edit_pop_up .popup-header h3")

    # --- Form Fields ---
    NAME_INPUT = ("css", "input[name='Name']")
    DESCRIPTION_INPUT = ("css", "input[name='Description']")

    # Status checkbox (angular material checkbox inside the form)
    STATUS_CHECKBOX = ("css", "div.edit_pop_up input[type='checkbox']")

    # --- Form Buttons ---
    SUBMIT_BUTTON = ("css", "div.popup-footer button[type='submit']")
    CANCEL_BUTTON = ("css", "div.popup-footer button[type='button']")

    # --- Popup Header Buttons ---
    CLOSE_X_BUTTON = ("xpath", "//div[@class='popup-actions']//button[contains(.,'close')]")
    FULLSCREEN_BUTTON = ("xpath", "//div[@class='popup-actions']//button[contains(.,'fullscreen')]")

    # ================================================================
    # LOCATORS — SweetAlert Popups
    # ================================================================

    SWEET_ALERT_POPUP = ("css", ".swal2-popup")
    SWEET_ALERT_TITLE = ("css", ".swal2-title")
    SWEET_ALERT_MESSAGE = ("css", ".swal2-html-container")
    SWEET_ALERT_CONFIRM_BTN = ("css", "button.swal2-confirm")
    SWEET_ALERT_CANCEL_BTN = ("css", "button.swal2-cancel")

    # ================================================================
    # LOCATORS — List Page (live-verified 2026-06-02)
    # ================================================================

    # Add button — uses <i class="material-icons">add</i>, NOT <mat-icon>
    ADD_BUTTON = ("xpath", "//button[i[text()='add']]")

    # Refresh button — same pattern: <i class="material-icons">refresh</i>
    REFRESH_BUTTON = ("xpath", "//button[i[text()='refresh']]")

    # Data table
    TABLE = ("css", "table#excel-table")
    TABLE_BODY = ("css", "table#excel-table tbody")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")

    # Kebab menu (more_vert) per row — opens context menu with View/Edit/History
    _row_kebab = lambda self, row_index: (
        "xpath",
        f"(//table[@id='excel-table']//tbody//tr)[{row_index + 1}]"
        f"//button[contains(@class,'erp-row-trigger')]"
    )

    # Menu items inside the CDK overlay after kebab click
    _menu_view = ("xpath", "//div[contains(@class,'cdk-overlay')]//span[contains(text(),'View')]/ancestor::button")
    _menu_edit = ("xpath", "//div[contains(@class,'cdk-overlay')]//span[contains(text(),'Edit')]/ancestor::button")
    _menu_history = ("xpath", "//div[contains(@class,'cdk-overlay')]//span[contains(text(),'History')]/ancestor::button")

    # Table cell text (row=0-based, col=1-based for XPath)
    def _table_cell(self, row, col):
        return ("xpath", f"(//table[@id='excel-table']//tbody//tr)[{row + 1}]/td[{col}]")

    # ================================================================
    # LOCATORS - History Popup (live-verified 2026-06-02)
    # ================================================================

    HISTORY_POPUP_TITLE = ("xpath", "//h3[contains(text(),'History')]")
    HISTORY_TABLE_ROWS = ("css", "div.popup-overlay .scrollable-table-container tr")
    # "No data" state: image + paragraphs (NOT div[style*='text-align'])
    HISTORY_NO_DATA_IMG = ("css", "div.popup-overlay .scrollable-table-container img")
    HISTORY_NO_DATA_TEXT = ("css", "div.popup-overlay .scrollable-table-container p")

    # Cancel button: mat-button with label span "Cancel" inside popup-footer
    HISTORY_CANCEL_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-overlay')]"
        "//div[contains(@class,'popup-footer')]"
        "//span[contains(@class,'mdc-button__label') and normalize-space(text())='Cancel']/.."
    )

    # History search — same pattern as main search: button opens input
    HISTORY_SEARCH_BUTTON = ("css", "div.popup-overlay button[aria-label='Search']")
    HISTORY_SEARCH_INPUT = ("css", "div.popup-overlay input#erpSearchInput")

    # ================================================================
    # NAVIGATION
    # ================================================================

    def navigate_to_season(self):
        """Navigate directly to the Season screen via URL."""
        from pages.common_settings.modules.season.data.season_data import SEASON_PAGE_URL
        log.info("Navigating to Season screen...")
        self._force_close_panels()
        self.navigate_to(SEASON_PAGE_URL)
        try:
            self.wait_for_visible(self.TABLE, timeout=15)
            self.wait_seconds(1)  # let Angular finish change detection
            log.info("Season screen loaded successfully")
        except Exception:
            log.warning("Table not found — page may still be loading or empty")
            self.take_screenshot("season_page_load")

    # ================================================================
    # ADD FORM — Open / Close
    # ================================================================

    def open_add_form(self):
        """Click the Add (+) button to open the form popup."""
        log.step(1, "Opening Add form")
        self._force_close_panels()
        self.wait_seconds(0.5)
        self.click(self.ADD_BUTTON)
        self.wait_for_form_to_open()
        log.info("Add form opened")

    def close_form_via_cancel(self):
        """Click the Cancel button to close the form."""
        log.info("Closing form via Cancel button")
        self.click(self.CANCEL_BUTTON)
        self.wait_for_form_to_close()

    def close_form_via_x(self):
        """Click the X button to close the form."""
        log.info("Closing form via X button")
        self.click(self.CLOSE_X_BUTTON)
        self.wait_for_form_to_close()

    # ================================================================
    # FORM — Fill Fields
    # ================================================================

    def enter_name(self, name):
        """Type season name into the Name field."""
        log.step(2, f"Entering Name: {name}")
        self.type_text(self.NAME_INPUT, name, clear_first=True)

    def enter_description(self, description):
        """Type description into the Description field."""
        log.step(3, f"Entering Description: {description}")
        if description:
            self.type_text(self.DESCRIPTION_INPUT, description, clear_first=True)
        else:
            log.info("Description left blank (optional field)")

    def fill_form(self, name, description=""):
        """Fill all form fields at once."""
        self.enter_name(name)
        if description:
            self.enter_description(description)

    def clear_form(self):
        """Clear all text fields in the form."""
        log.info("Clearing form fields")
        self.clear_field(self.NAME_INPUT)
        self.clear_field(self.DESCRIPTION_INPUT)

    # ================================================================
    # FORM — Submit
    # ================================================================

    def click_submit(self):
        """Click the Submit button (Add mode)."""
        log.step(4, "Clicking Submit button")
        self.click(self.SUBMIT_BUTTON)

    def click_update(self):
        """Click the Update button (Edit mode)."""
        log.step(4, "Clicking Update button")
        self.click(self.SUBMIT_BUTTON)

    # ================================================================
    # SWEET ALERT — Detection & Handling
    # ================================================================

    def is_validation_alert_present(self, timeout=5):
        """Check if SweetAlert 'Validation Failed' popup is visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup"))
            )
            title = self.get_text(self.SWEET_ALERT_TITLE)
            if "Validation Failed" in title:
                log.info("Validation Failed alert detected")
                return True
        except Exception:
            pass
        return False

    def is_success_alert_present(self, timeout=5):
        """Check if SweetAlert success popup is visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup"))
            )
            title = self.get_text(self.SWEET_ALERT_TITLE)
            if "successfully" in title.lower() or "success" in title.lower():
                log.info(f"Success alert detected: {title}")
                return True
        except Exception:
            pass
        return False

    def is_any_alert_present(self, timeout=3):
        """Check if any SweetAlert popup is visible."""
        return self.is_displayed(self.SWEET_ALERT_POPUP, timeout=timeout)

    def get_alert_title(self):
        """Get the title text from the current SweetAlert popup."""
        try:
            return self.get_text(self.SWEET_ALERT_TITLE)
        except Exception:
            return ""

    def get_alert_message(self):
        """Get the message text from the current SweetAlert popup."""
        try:
            return self.get_text(self.SWEET_ALERT_MESSAGE)
        except Exception:
            return ""

    def handle_validation_alert(self):
        """Click OK on the Validation Failed SweetAlert."""
        log.info("Handling Validation Failed alert — clicking OK")
        try:
            self.click(self.SWEET_ALERT_CONFIRM_BTN)
            self.wait_seconds(0.5)
        except Exception:
            log.warning("Could not click validation alert OK button")

    def wait_for_success_alert_to_dismiss(self, timeout=5):
        """Wait for the success toast to auto-dismiss."""
        log.info("Waiting for success toast to auto-dismiss...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup"))
            )
            log.info("Success toast dismissed")
        except Exception:
            log.warning("Success toast did not dismiss within timeout")

    def handle_success_alert(self):
        """Handle the success SweetAlert — wait for auto-dismiss."""
        self.wait_for_success_alert_to_dismiss()

    # ================================================================
    # FORM — State Checks
    # ================================================================

    def is_form_open(self):
        """Check if the Season form popup is currently visible."""
        return self.is_displayed(self.FORM_POPUP, timeout=5)

    def wait_for_form_to_open(self, timeout=10):
        """Wait until the form popup appears."""
        try:
            self.wait_for_visible(self.FORM_POPUP, timeout=timeout)
            log.info("Form popup is now open")
        except Exception:
            log.error("Form popup did not open within timeout")
            self.take_screenshot("form_not_opened")
            raise

    def wait_for_form_to_close(self, timeout=10):
        """Wait until the form popup disappears."""
        try:
            self.wait_for_invisible(self.FORM_POPUP, timeout=timeout)
            log.info("Form popup closed")
            self.wait_seconds(0.5)
        except Exception:
            log.warning("Form popup still visible after timeout")

    def is_field_disabled(self, locator):
        """Check if a form field is disabled (used for View mode)."""
        try:
            element = self.find_element(locator)
            disabled = element.get_attribute("disabled")
            aria_disabled = element.get_attribute("aria-disabled")
            return disabled == "true" or aria_disabled == "true"
        except Exception:
            return False

    def is_form_in_view_mode(self):
        """Check if the form is in View mode (no Submit/Update button visible)."""
        try:
            return not self.is_displayed(self.SUBMIT_BUTTON, timeout=3)
        except Exception:
            return True

    # ================================================================
    # TABLE — Read Data
    # ================================================================

    def get_table_row_count(self):
        """Get the number of data rows in the Season list table."""
        try:
            rows = self.find_elements(self.TABLE_ROWS)
            count = len(rows)
            log.info(f"Table has {count} row(s)")
            return count
        except Exception:
            return 0

    def get_cell_text(self, row_index, col_index):
        """Get text from a specific table cell.

        Args:
            row_index: 0-based row index.
            col_index: 1-based column index (XPath td[N]).
        """
        cell_locator = self._table_cell(row_index, col_index)
        return self.get_text(cell_locator)

    def find_row_by_name(self, name):
        """Find a table row index by matching the Name column.

        Returns:
            int: 0-based row index, or -1 if not found.
        """
        row_count = self.get_table_row_count()
        for i in range(row_count):
            cell_text = self.get_cell_text(i, self.COL_NAME)
            if cell_text.strip().lower() == name.strip().lower():
                log.info(f"Found '{name}' at row {i}")
                return i
        log.warning(f"Record '{name}' not found in table")
        return -1

    def is_record_present(self, name):
        """Check if a season record exists in the table by Name."""
        return self.find_row_by_name(name) != -1

    def get_name_from_row(self, row_index):
        """Get the Name value from a specific row."""
        return self.get_cell_text(row_index, self.COL_NAME)

    def get_description_from_row(self, row_index):
        """Get the Description value from a specific row."""
        return self.get_cell_text(row_index, self.COL_DESCRIPTION)

    def get_status_from_row(self, row_index):
        """Get the Status value from a specific row."""
        return self.get_cell_text(row_index, self.COL_STATUS)

    # ================================================================
    # TABLE — Row Actions via Kebab Menu (live-verified 2026-06-02)
    # ================================================================
    # Live ERP uses a kebab menu (more_vert) per row that opens a
    # CDK overlay with menu items: View, Edit, History.
    # Old code used tblActnBtn class which NO LONGER EXISTS in the DOM.

    def _open_kebab_menu(self, row_index):
        """Open the kebab menu for a specific row and wait for menu items."""
        log.info(f"Opening kebab menu on row {row_index}")
        kebab_locator = self._row_kebab(row_index)
        self.click(kebab_locator)
        # Wait for the CDK overlay menu to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".cdk-overlay-pane .mat-mdc-menu-item")
                )
            )
            self.wait_seconds(0.3)  # let animation settle
        except TimeoutException:
            log.warning("Kebab menu overlay did not appear")

    def _close_kebab_menu(self):
        """Dismiss any open kebab menu overlay."""
        try:
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            self.wait_seconds(0.3)
        except Exception:
            pass

    def click_view_button(self, row_index=0):
        """Click the View button on a specific row via kebab menu."""
        log.info(f"Clicking View on row {row_index}")
        self._open_kebab_menu(row_index)
        self.click(self._menu_view)
        self.wait_for_form_to_open()

    def click_edit_button(self, row_index=0):
        """Click the Edit button on a specific row via kebab menu."""
        log.info(f"Clicking Edit on row {row_index}")
        self._open_kebab_menu(row_index)
        self.click(self._menu_edit)
        self.wait_for_form_to_open()

    def click_history_button(self, row_index=0):
        """Click the History button on a specific row via kebab menu."""
        log.info(f"Clicking History on row {row_index}")
        self._open_kebab_menu(row_index)
        self.click(self._menu_history)
        self.wait_for_history_popup()

    def close_history_popup(self):
        """Close the History popup."""
        self.close_history_via_cancel()

    # ================================================================
    # HISTORY POPUP - Helper Methods
    # ================================================================

    def is_history_popup_open(self, timeout=5):
        """Check if History popup is currently open."""
        return self.is_displayed(self.HISTORY_POPUP_TITLE, timeout=timeout)

    def wait_for_history_popup(self, timeout=10):
        """Wait for History popup to open and async content to settle.

        Waits for EITHER a table row OR the 'No data' indicators (img or p)
        to appear — all confirm the async load completed.
        """
        try:
            self.wait_for_visible(self.HISTORY_POPUP_TITLE, timeout=timeout)
            log.info("History popup opened")
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: (
                        len(d.find_elements(By.CSS_SELECTOR,
                            "div.popup-overlay .scrollable-table-container tr")) > 0
                        or
                        len(d.find_elements(By.CSS_SELECTOR,
                            "div.popup-overlay .scrollable-table-container img")) > 0
                        or
                        len(d.find_elements(By.CSS_SELECTOR,
                            "div.popup-overlay .scrollable-table-container p")) > 0
                    )
                )
                log.info("History popup content loaded")
            except Exception:
                log.warning("History popup content did not settle within timeout")
        except Exception:
            log.error("History popup did not open")
            self.take_screenshot("history_popup_not_opened")
            raise

    def get_history_title(self):
        """Get the History popup title text."""
        return self.get_text(self.HISTORY_POPUP_TITLE)

    def search_in_history(self, text):
        """Search within the History popup table.

        Uses the same JS-based search pattern as the main search to
        avoid stale element issues with Angular animations.
        """
        log.info(f"Searching in history for: {text}")

        # Open search bar within history popup if not already open
        self.driver.execute_script("""
            var input = document.querySelector('div.popup-overlay #erpSearchInput');
            if (!input) {
                var btn = document.querySelector('div.popup-overlay button[aria-label="Search"]');
                if (btn) btn.click();
            }
        """)
        self.wait_seconds(1)

        # Use JS to type and search (avoids stale elements)
        self.driver.execute_script("""
            var input = document.querySelector('div.popup-overlay #erpSearchInput');
            if (!input) input = document.querySelector('div.popup-overlay input[type="text"]');
            if (input) {
                var nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSetter.call(input, '');
                input.dispatchEvent(new Event('input', {bubbles: true}));
                nativeSetter.call(input, arguments[0]);
                input.dispatchEvent(new Event('input', {bubbles: true}));
                input.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                }));
            }
        """, text)
        self.wait_seconds(2)

    def get_history_row_count(self):
        """Get number of rows in the history table.

        Uses direct find_elements (no wait) because wait_for_history_popup()
        already confirmed the content is settled. Returns 0 if no table exists
        (i.e. the 'No data' state is showing).
        """
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.popup-overlay .scrollable-table-container tr"
            )
            count = len(rows)
            log.info(f"History table has {count} row(s)")
            return count
        except Exception as e:
            log.warning(f"History table rows not found: {e}")
            return 0

    def get_history_cell_text(self, row_index, col_index):
        """Get text from a specific history table cell (0-based).

        History columns (0-indexed):
            0 = View (button)
            1 = Creation Time
            2 = Updated Time
            3 = Name
            4 = Description
            5 = Status
        """
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.popup-overlay .scrollable-table-container tr"
            )
            if row_index < len(rows):
                cells = rows[row_index].find_elements(By.CSS_SELECTOR, "td, th")
                if col_index < len(cells):
                    text = cells[col_index].text.strip()
                    log.info(f"History cell [{row_index},{col_index}] = {text}")
                    return text
            text = "ROW_NOT_FOUND"
            log.warning(f"History cell [{row_index},{col_index}] = {text}")
            return text
        except Exception as e:
            log.warning(f"History cell [{row_index},{col_index}] error: {e}")
            return "ROW_NOT_FOUND"

    def close_history_via_cancel(self):
        """Close the History popup via the Cancel button.

        The Cancel button in this popup is a mat-button (no type attribute).
        We locate it via the mdc-button__label span text inside popup-footer.
        Falls back to Escape key if the button is not interactable.
        """
        log.info("Closing History popup via Cancel button")
        try:
            self.click(self.HISTORY_CANCEL_BUTTON)
            self.wait_seconds(0.5)
        except Exception:
            log.warning("Cancel button not found in History popup, trying Escape")
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

    def _ensure_record_has_history(self):
        """Create a record, edit it once, and return its final name.

        The app only logs history rows on UPDATE events — a brand-new record
        shows "No data available." in the history popup. Tests that need
        history data must call this method first.
        """
        from pages.common_settings.modules.season.data.season_data import valid_season_with_description
        data = valid_season_with_description()
        name = data["Name"]

        # Create
        self.open_add_form()
        self.fill_form(name, data["Description"])
        self.click_submit()
        self.wait_for_form_to_close(timeout=10)
        self.refresh_table()
        self.wait_seconds(1)
        assert self.search_record(name), f"Prereq: could not create '{name}'"
        log.info(f"Created '{name}' for history test")

        # Edit (this is what creates the history row)
        row_index = self.find_row_by_name(name)
        assert row_index != -1, f"Prereq: row not found for '{name}'"
        self.click_edit_button(row_index)
        self.clear_form()
        edited_name = f"HIST_{name}"
        self.fill_form(edited_name, "Edited for history test")
        self.click_update()
        self.wait_for_form_to_close(timeout=10)
        self.refresh_table()
        self.wait_seconds(1)
        assert self.search_record(edited_name), f"Prereq: edited record '{edited_name}' not found"
        log.info(f"Edited to '{edited_name}' — history now has rows")

        self.clear_search()
        return edited_name

    # ================================================================
    # REFRESH / RELOAD TABLE
    # ================================================================

    def refresh_table(self):
        """Click the Refresh button to reload the table data."""
        log.info("Refreshing Season table...")
        try:
            self.click(self.REFRESH_BUTTON)
            self.wait_seconds(2)
            log.info("Table refreshed")
        except Exception:
            log.warning("Refresh button not found, falling back to page refresh")
            self.navigate_to_season()
            self.wait_seconds(2)

    # ================================================================
    # SEARCH
    # ================================================================

    SEARCH_BUTTON = ("css", "button[aria-label='Search']")
    SEARCH_INPUT = ("css", "input#erpSearchInput")

    def _open_search_bar(self):
        """Open the search toggle bar and wait for the input to be DOM-stable."""
        if self.is_displayed(self.SEARCH_INPUT, timeout=1):
            return  # bar already open

        self.click(self.SEARCH_BUTTON)

        by, value = self._parse_locator(self.SEARCH_INPUT)

        def input_is_stable(driver):
            """Return element only once it's visible AND survives a second read."""
            try:
                el = driver.find_element(by, value)
                if not el.is_displayed():
                    return False
                _ = el.get_attribute("id")
                return el
            except StaleElementReferenceException:
                return False
            except Exception:
                return False

        try:
            WebDriverWait(self.driver, 8).until(input_is_stable)
            self.wait_seconds(0.2)
            log.info("Search bar open and stable")
        except Exception:
            log.warning("Search input did not stabilise within timeout")

    def search_record(self, text, exact=False):
        """Search for a record in the Season table.

        Uses JS-based search to avoid stale element issues.
        The Name column is td[2] (1-based XPath).

        Args:
            text: Search query.
            exact: If True, scans all rows for exact name match.

        Returns:
            bool: True if matching record(s) found.
        """
        try:
            log.info(f"Searching for record: {text} (exact={exact})")

            # Step 1: Open search bar if needed (pure JS — no stale risk)
            self.driver.execute_script("""
                var input = document.querySelector('#erpSearchInput');
                if (!input) {
                    document.querySelector('button[aria-label="Search"]').click();
                }
            """)

            # Step 2: Wait for Angular to inject the input
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#erpSearchInput"))
            )
            self.wait_seconds(1)

            # Step 3: Clear + Type + Enter — ALL in ONE JS call (atomic, no stale)
            self.driver.execute_script("""
                var input = document.querySelector('#erpSearchInput');
                var nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;

                nativeSetter.call(input, '');
                input.dispatchEvent(new Event('input', {bubbles: true}));

                nativeSetter.call(input, arguments[0]);
                input.dispatchEvent(new Event('input', {bubbles: true}));

                input.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                }));
            """, text)

            self.wait_seconds(2)

            # Step 4: Check results — Name is column 2 (1-based XPath = td[2])
            row_count = self.get_table_row_count()

            if row_count == 0:
                log.info(f"Search returned 0 results for '{text}'")
                return False

            if not exact:
                first_name = ""
                try:
                    first_name = self.get_text(
                        ("xpath", f"(//table[@id='excel-table']//tbody//tr)[1]/td[{self.COL_NAME}]")
                    )
                except Exception:
                    first_name = "(could not read)"
                log.info(f"Search found {row_count} result(s), first: '{first_name}'")
                return True

            # Exact mode: scan ALL visible rows for exact name match
            text_lower = text.strip().lower()
            for i in range(row_count):
                try:
                    row_name = self.get_text(
                        ("xpath", f"(//table[@id='excel-table']//tbody//tr)[{i + 1}]/td[{self.COL_NAME}]")
                    ).strip().lower()
                    if row_name == text_lower:
                        log.info(f"Exact match found at row {i}")
                        return True
                except Exception:
                    continue
            log.info(f"No exact match for '{text}' in {row_count} result(s)")
            return False

        except Exception as e:
            log.error(f"[ERROR] Search failed: {e}")
            return False

    # ================================================================
    # UTILITY - CDK OVERLAY CLEANUP
    # ================================================================

    def _force_close_panels(self):
        """Remove any lingering CDK overlay panels that block clicks."""
        try:
            overlays = self.driver.find_elements(
                "css selector", ".cdk-overlay-backdrop"
            )
            for overlay in overlays:
                self.driver.execute_script("arguments[0].remove();", overlay)
            panels = self.driver.find_elements(
                "css selector", ".cdk-overlay-pane"
            )
            for panel in panels:
                self.driver.execute_script("arguments[0].remove();", panel)
            # Also close any open form popups via JS
            self.driver.execute_script("""
                var popups = document.querySelectorAll('div.edit_pop_up');
                popups.forEach(function(p) { p.remove(); });
            """)
        except Exception:
            pass

    def _dismiss_any_sweet_alert(self):
        """Dismiss any SweetAlert popup (Pattern A or Pattern B)."""
        try:
            self.driver.find_element("css selector", ".swal2-popup")
            log.info("SweetAlert detected, attempting to dismiss")
            try:
                cancel_btn = self.driver.find_element("css selector", ".swal2-cancel")
                self.driver.execute_script("arguments[0].click();", cancel_btn)
                log.info("Dismissed via Cancel button (Pattern B)")
            except Exception:
                confirm_btn = self.driver.find_element("css selector", ".swal2-confirm")
                self.driver.execute_script("arguments[0].click();", confirm_btn)
                log.info("Dismissed via OK button (Pattern A)")
            self.wait_seconds(1)
        except Exception:
            pass

    def clear_search(self):
        """Clear the search filter by re-navigating to the Season screen.

        Re-navigation is the most reliable reset. navigate_to_season() waits
        for TABLE visibility before returning, so callers get a fully settled
        DOM immediately after this call exits.
        """
        log.info("Clearing search filter...")
        self._force_close_panels()
        self.navigate_to_season()
