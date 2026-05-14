"""
HSN SAC — Page Object
======================
All locators and methods for the HSN SAC module.
Based on Vehicle Master proven patterns (100% working).
Module: 3 fields (2 text + 1 dropdown with 4 fixed options).
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from pages.common_settings.modules.hsn_sac.data.hsn_sac_data import (
    PAGE_URL,
    FIELD_HSN_NUMBER,
    FIELD_HSN_TYPE,
    FIELD_HSN_DESC,
    SUCCESS_ADD_MESSAGE,
    SUCCESS_UPDATE_MESSAGE,
    VALIDATION_FAILED_TITLE,
    VALIDATION_FAILED_CONTENT,
    POPUP_TITLE,
    HISTORY_POPUP_TITLE,
    HSN_SAC_TYPE_OPTIONS,
)


class HsnSacPage:

    # ═══════════════════════════════════════════════════════════════════════════
    # Locators — Table & Toolbar
    # ═══════════════════════════════════════════════════════════════════════════

    TABLE = (By.CSS_SELECTOR, "table#excel-table")
    TABLE_BODY_ROWS = (By.CSS_SELECTOR, "table#excel-table tbody tr")
    SEARCH_TOGGLE = (By.CSS_SELECTOR, "button.search-btn")
    SEARCH_INPUT = (By.CSS_SELECTOR, "#erpSearchInput")
    ADD_BUTTON = (By.XPATH, "//*[@mattooltip='ADD']/button")
    FILTER_BUTTON = (By.XPATH, "//*[@mattooltip='Filters']/button")
    REFRESH_BUTTON = (By.XPATH, "//*[@mattooltip='REFRESH']/button")

    # Row action buttons
    VIEW_BUTTON = (By.XPATH, "//td[contains(@class,'mat-column-view')]//button")
    EDIT_BUTTON = (By.XPATH, "//td[contains(@class,'mat-column-edit')]//button")
    HISTORY_BUTTON = (By.XPATH, "//td[contains(@class,'mat-column-archive')]//button")

    # ═══════════════════════════════════════════════════════════════════════════
    # Locators — Form Popup
    # ═══════════════════════════════════════════════════════════════════════════

    POPUP_CONTAINER = (By.XPATH, "//div[contains(@class,'edit_pop_up') and contains(@class,'popup-mode')]")
    POPUP_HEADER = (By.CSS_SELECTOR, ".popup-header")
    POPUP_TITLE = (By.CSS_SELECTOR, ".big-model h3")
    POPUP_BODY = (By.XPATH, "//div[contains(@class,'overflow_model')]")
    POPUP_FOOTER = (By.XPATH, "//div[contains(@class,'popup-footer')]")
    CLOSE_X_BUTTON = (By.XPATH, "//div[contains(@class,'big-model')]//button//mat-icon[contains(text(),'close')]")
    CANCEL_BUTTON = (By.XPATH, "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]")
    SUBMIT_BUTTON = (By.XPATH, "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]")
    UPDATE_BUTTON = (By.XPATH, "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]")

    # ═══════════════════════════════════════════════════════════════════════════
    # Locators — Form Fields (3 fields — ALL REQUIRED)
    # ═══════════════════════════════════════════════════════════════════════════

    HSN_NUMBER_INPUT = (By.CSS_SELECTOR, "input[name='HSN SAC Number']")
    HSN_TYPE_SELECT = (By.XPATH, "//mat-label[contains(.,'HSN SAC Type')]/ancestor::mat-form-field//mat-select")
    HSN_DESC_INPUT = (By.CSS_SELECTOR, "input[name='HSN SAC Description']")

    # ═══════════════════════════════════════════════════════════════════════════
    # Locators — SweetAlert2
    # ═══════════════════════════════════════════════════════════════════════════

    SWAL_CONTAINER = (By.CSS_SELECTOR, ".swal2-container")
    SWAL_TITLE = (By.CSS_SELECTOR, "#swal2-title")
    SWAL_CONTENT = (By.CSS_SELECTOR, ".swal2-html-container")
    SWAL_CONFIRM = (By.CSS_SELECTOR, ".swal2-confirm")

    # ═══════════════════════════════════════════════════════════════════════════
    # Locators — History Popup
    # ═══════════════════════════════════════════════════════════════════════════

    HISTORY_POPUP = (By.CSS_SELECTOR, ".popup-content")
    HISTORY_TITLE = (By.XPATH, "//div[contains(@class,'popup-content')]//h3[contains(@class,'popup-title')]")
    HISTORY_CLOSE = (By.XPATH, "//div[contains(@class,'popup-content')]//button//mat-icon[contains(text(),'close')]")
    HISTORY_CANCEL = (By.XPATH, "//div[contains(@class,'popup-content')]//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]")
    HISTORY_BODY = (By.CSS_SELECTOR, ".popup-body")
    HISTORY_TABLE_ROWS = (By.CSS_SELECTOR, ".popup-body table tbody tr")
    NO_DATA_MSG = (By.XPATH, "//p[contains(text(),'No data available')]")

    # ═══════════════════════════════════════════════════════════════════════════
    # Init
    # ═══════════════════════════════════════════════════════════════════════════

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)

    # ═══════════════════════════════════════════════════════════════════════════
    # Navigation
    # ═══════════════════════════════════════════════════════════════════════════

    def navigate_to_page(self):
        """Navigate to HSN SAC page + force refresh + wait for table."""
        self.driver.get(PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait for page fully loaded — table visible + toolbar ready."""
        try:
            self.wait.until(EC.visibility_of_element_located(self.TABLE))
            time.sleep(1)
            self._wait_for_toolbar()
        except TimeoutException:
            pass

    def _wait_for_toolbar(self):
        """Retry ADD button readiness (3 retries x 2s)."""
        for _ in range(3):
            try:
                btn = self.driver.find_element(*self.ADD_BUTTON)
                if btn.is_displayed():
                    return
            except NoSuchElementException:
                pass
            time.sleep(2)

    def is_page_loaded(self):
        """Check if listing page is loaded."""
        try:
            return self.driver.find_element(*self.TABLE).is_displayed()
        except NoSuchElementException:
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # Add Form — Open / Close
    # ═══════════════════════════════════════════════════════════════════════════

    def open_add_form(self):
        """Click ADD button to open create form. JS click + verify popup."""
        try:
            btn = self.driver.find_element(*self.ADD_BUTTON)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(1.5)
            if not self._is_form_popup_open():
                # Fallback: direct find + JS click
                self.driver.execute_script(
                    "document.querySelector(\"//*[@mattooltip='ADD']/button\").click();"
                )
                time.sleep(1.5)
        except Exception as e:
            raise Exception(f"Failed to open Add form: {e}")

    def _is_form_popup_open(self):
        """Check if form popup is visible."""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "div.big-model")
            return el.is_displayed()
        except NoSuchElementException:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, "mat-dialog-container")
                return el.is_displayed()
            except NoSuchElementException:
                return False

    def is_form_open(self):
        """Check if form popup is currently open."""
        return self._is_form_popup_open()

    def is_form_closed(self):
        """Check if form popup is closed."""
        return not self._is_form_popup_open()

    def close_popup(self):
        """Click X icon in popup header."""
        try:
            icons = self.driver.find_elements(By.CSS_SELECTOR,
                                               ".big-model button mat-icon")
            for icon in icons:
                if "close" in (icon.text or "").lower():
                    btn = icon.find_element(By.XPATH, "./ancestor::button")
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    return
        except Exception:
            self.cancel()

    def cancel(self):
        """Click Cancel button in popup footer."""
        try:
            btn = self.driver.find_element(*self.CANCEL_BUTTON)
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(1)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════════
    # Form — Fill Fields
    # ═══════════════════════════════════════════════════════════════════════════

    def fill_hsn_sac_number(self, value):
        """Type into HSN SAC Number input."""
        self.type_text(self.HSN_NUMBER_INPUT, value)

    def fill_hsn_sac_description(self, value):
        """Type into HSN SAC Description input."""
        self.type_text(self.HSN_DESC_INPUT, value)

    def select_hsn_sac_type(self, option_text):
        """
        Select from HSN SAC Type dropdown (4 fixed options).
        Returns True if selection succeeded, False if dropdown didn't open.
        """
        return self._select_mat_option(self.HSN_TYPE_SELECT, option_text)

    def fill_all_fields(self, data, max_retries=3):
        """
        Fill all form fields with retry logic for dropdown.
        Order: Dropdown FIRST → Text fields → (handles refresh if needed).
        Returns True if all fields filled successfully.
        """
        for attempt in range(1, max_retries + 1):
            success = self._fill_all_fields_once(data)
            if success:
                return True
            # Dropdown failed — retry with page refresh
            print(f"  [Retry {attempt}/{max_retries}] Dropdown didn't open, refreshing page...")
            self.cancel()
            time.sleep(1)
            self.driver.refresh()
            time.sleep(2)
            self._wait_for_page_ready()
            time.sleep(1)
            self.open_add_form()
            time.sleep(1.5)
        return False

    def _fill_all_fields_once(self, data):
        """
        Single pass: fill Dropdown → Text fields.
        Returns True if dropdown opened and all fields filled.
        """
        # 1. Dropdown FIRST (most likely to fail)
        hsn_type = data.get("hsn_sac_type", "")
        if hsn_type:
            dropdown_ok = self.select_hsn_sac_type(hsn_type)
            if not dropdown_ok:
                return False
            self._force_close_panels()

        # 2. Text fields
        number = data.get("hsn_sac_number", "")
        desc = data.get("hsn_sac_description", "")
        if number:
            self.fill_hsn_sac_number(number)
        if desc:
            self.fill_hsn_sac_description(desc)

        return True

    def type_text(self, locator, text, clear_first=True):
        """Type text into an input field with JS value set for reliability."""
        try:
            el = self.driver.find_element(*locator)
            if clear_first:
                el.clear()
                self.driver.execute_script(
                    "arguments[0].value = '';", el
                )
            el.send_keys(str(text))
            # Dispatch input event so Angular registers the change
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", el
            )
        except Exception as e:
            raise Exception(f"Failed to type into {locator}: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # Dropdown — Select Option
    # ═══════════════════════════════════════════════════════════════════════════

    def _select_mat_option(self, select_locator, option_text):
        """
        Select a specific option from mat-select dropdown.
        Returns True if option selected, False if dropdown didn't open.
        """
        try:
            # Click the dropdown trigger
            select_el = self.driver.find_element(*select_locator)
            self.driver.execute_script("arguments[0].click();", select_el)
            time.sleep(1.5)

            # Check if overlay panel opened
            panels = self.driver.find_elements(
                By.CSS_SELECTOR, "div.cdk-overlay-pane:not(.mat-mdc-dialog-container)"
            )
            if not panels:
                # Fallback 2: ActionChains click
                ActionChains(self.driver).move_to_element(select_el).click().perform()
                time.sleep(2)
                panels = self.driver.find_elements(
                    By.CSS_SELECTOR, "div.cdk-overlay-pane:not(.mat-mdc-dialog-container)"
                )
                if not panels:
                    return False

            # Find the matching option
            options = self.driver.find_elements(
                By.CSS_SELECTOR, "div.mat-mdc-select-panel mat-option"
            )
            for opt in options:
                if opt.is_displayed() and option_text in (opt.text or ""):
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true); arguments[0].click();", opt
                    )
                    time.sleep(0.8)
                    self._force_close_panels()
                    return True

            # Fallback: try by text match with role=option
            all_options = self.driver.find_elements(By.CSS_SELECTOR, "[role='option']")
            for opt in all_options:
                if opt.is_displayed() and option_text in (opt.text or ""):
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true); arguments[0].click();", opt
                    )
                    time.sleep(0.8)
                    self._force_close_panels()
                    return True

            return False

        except Exception as e:
            print(f"  [Dropdown] Error selecting '{option_text}': {e}")
            return False

    def _force_close_panels(self):
        """Remove leftover CDK overlay panels (not dialogs)."""
        self.driver.execute_script("""
            document.querySelectorAll('.cdk-overlay-backdrop:not(.cdk-overlay-dark)').forEach(el => el.remove());
            document.querySelectorAll('.cdk-overlay-pane:not(.mat-mdc-dialog-container)').forEach(el => el.remove());
        """)

    def _close_select_panel(self):
        """Close dropdown panel via backdrop click."""
        try:
            backdrop = self.driver.find_element(By.CSS_SELECTOR, ".cdk-overlay-backdrop")
            self.driver.execute_script("arguments[0].click();", backdrop)
            time.sleep(0.5)
        except Exception:
            self._force_close_panels()

    # ═══════════════════════════════════════════════════════════════════════════
    # Submit / Update
    # ═══════════════════════════════════════════════════════════════════════════

    def submit(self):
        """Click Submit button (Add mode). 3-tier JS click."""
        self._click_popup_button(self.SUBMIT_BUTTON)

    def click_update(self):
        """Click Update button (Edit mode). 3-tier JS click."""
        self._click_popup_button(self.UPDATE_BUTTON)

    def _click_popup_button(self, button_locator):
        """3-tier click: find visible → JS scroll+click → fallback."""
        try:
            btn = self.driver.find_element(*button_locator)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", btn)
        except Exception:
            try:
                btn = self.driver.find_element(*button_locator)
                btn.click()
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════════════════════
    # SweetAlert2 — Handle Alerts
    # ═══════════════════════════════════════════════════════════════════════════

    def handle_success_alert(self, timeout=15):
        """
        Wait for SweetAlert2 success, read message, click OK, cleanup.
        Returns the success message text or empty string.
        """
        try:
            title_el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SWAL_TITLE)
            )
            message = title_el.text or ""

            # 3-tier confirm click
            try:
                confirm = self.driver.find_element(*self.SWAL_CONFIRM)
                self.driver.execute_script("arguments[0].click();", confirm)
            except Exception:
                try:
                    self.driver.execute_script(
                        "document.querySelector('.swal2-confirm').click();"
                    )
                except Exception:
                    self.driver.execute_script("""
                        var btns = document.querySelectorAll('.swal2-confirm');
                        if(btns.length) btns[0].click();
                    """)

            # Wait for alert to disappear
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located(self.SWAL_CONTAINER)
                )
            except TimeoutException:
                pass

            # Cleanup leftover swal2 elements
            self._cleanup_swal2()

            return message

        except TimeoutException:
            self._cleanup_swal2()
            return ""

    def handle_validation_warning(self, timeout=10):
        """
        Handle SweetAlert2 validation warning.
        Returns the warning title text or empty string.
        """
        try:
            title_el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SWAL_TITLE)
            )
            message = title_el.text or ""

            try:
                confirm = self.driver.find_element(*self.SWAL_CONFIRM)
                self.driver.execute_script("arguments[0].click();", confirm)
            except Exception:
                self.driver.execute_script(
                    "document.querySelector('.swal2-confirm').click();"
                )

            try:
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located(self.SWAL_CONTAINER)
                )
            except TimeoutException:
                pass

            self._cleanup_swal2()
            return message

        except TimeoutException:
            self._cleanup_swal2()
            return ""

    def is_validation_alert_present(self, timeout=5):
        """Check if validation SweetAlert2 is visible."""
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SWAL_TITLE)
            )
            return VALIDATION_FAILED_TITLE in (el.text or "")
        except TimeoutException:
            return False

    def _cleanup_swal2(self):
        """Remove leftover swal2 container + backdrops."""
        self.driver.execute_script("""
            document.querySelectorAll('.swal2-container').forEach(el => el.remove());
            document.querySelectorAll('.swal2-backdrop-show').forEach(el => el.remove());
        """)

    # ═══════════════════════════════════════════════════════════════════════════
    # Form Mode Detection
    # ═══════════════════════════════════════════════════════════════════════════

    def is_edit_mode(self):
        """Check if Update button is present (Edit mode)."""
        try:
            btn = self.driver.find_element(*self.UPDATE_BUTTON)
            return btn.is_displayed()
        except NoSuchElementException:
            return False

    def is_view_mode(self):
        """Check if no Submit/Update button (View mode)."""
        return not self.is_edit_mode() and not self._is_submit_visible()

    def _is_submit_visible(self):
        try:
            btn = self.driver.find_element(*self.SUBMIT_BUTTON)
            return btn.is_displayed()
        except NoSuchElementException:
            return False

    def get_form_heading(self):
        """Read popup heading text."""
        try:
            return self.driver.find_element(*self.POPUP_TITLE).text
        except NoSuchElementException:
            return ""

    # ═══════════════════════════════════════════════════════════════════════════
    # Read Form Field Values
    # ═══════════════════════════════════════════════════════════════════════════

    def get_form_field_values(self):
        """Read all form field values. Returns dict."""
        values = {}
        try:
            values["hsn_sac_number"] = self.driver.find_element(
                *self.HSN_NUMBER_INPUT
            ).get_attribute("value") or ""
        except NoSuchElementException:
            values["hsn_sac_number"] = ""

        try:
            select_el = self.driver.find_element(*self.HSN_TYPE_SELECT)
            values["hsn_sac_type"] = select_el.text or ""
        except NoSuchElementException:
            values["hsn_sac_type"] = ""

        try:
            values["hsn_sac_description"] = self.driver.find_element(
                *self.HSN_DESC_INPUT
            ).get_attribute("value") or ""
        except NoSuchElementException:
            values["hsn_sac_description"] = ""

        return values

    # ═══════════════════════════════════════════════════════════════════════════
    # Table Operations
    # ═══════════════════════════════════════════════════════════════════════════

    def get_table_row_count(self):
        """Count visible data rows in table."""
        try:
            rows = self.driver.find_elements(*self.TABLE_BODY_ROWS)
            return len(rows)
        except NoSuchElementException:
            return 0

    def get_cell_text(self, row_index, css_class):
        """Read text from a table cell by row index and column CSS class."""
        try:
            rows = self.driver.find_elements(*self.TABLE_BODY_ROWS)
            if row_index < len(rows):
                cell = rows[row_index].find_element(
                    By.CSS_SELECTOR, f"td.{css_class}"
                )
                return cell.text or ""
        except Exception:
            pass
        return ""

    def is_hsn_in_table(self, hsn_number):
        """Check if HSN SAC Number exists in table (partial match)."""
        try:
            cells = self.driver.find_elements(
                By.CSS_SELECTOR, f"td.{FIELD_HSN_NUMBER.lower().replace(' ', '_')}"
            )
            # Fallback column class
            if not cells:
                cells = self.driver.find_elements(
                    By.CSS_SELECTOR, "td.mat-column-hsn_sac_no"
                )
            for cell in cells:
                if hsn_number in (cell.text or ""):
                    return True
        except Exception:
            pass
        return False

    def find_hsn_row_index(self, hsn_number):
        """Find row index by HSN SAC Number (partial match). Returns -1 if not found."""
        try:
            rows = self.driver.find_elements(*self.TABLE_BODY_ROWS)
            for i, row in enumerate(rows):
                cells = row.find_elements(By.CSS_SELECTOR, "td")
                for cell in cells:
                    if hsn_number in (cell.text or ""):
                        return i
        except Exception:
            pass
        return -1

    def search_record(self, search_text, max_retries=3):
        """
        Search table by HSN SAC Number. Toggle search → type → Enter.
        Returns True if search executed successfully.
        """
        for attempt in range(max_retries):
            try:
                # Toggle search input
                try:
                    toggle = self.driver.find_element(*self.SEARCH_TOGGLE)
                    self.driver.execute_script("arguments[0].click();", toggle)
                    time.sleep(1)
                except Exception:
                    pass

                # Type search text
                search_input = self.driver.find_element(*self.SEARCH_INPUT)
                search_input.clear()
                search_input.send_keys(str(search_text))
                time.sleep(0.5)

                # Dispatch input event + Enter
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                    search_input
                )
                search_input.send_keys(Keys.RETURN)
                time.sleep(2)

                return True

            except Exception as e:
                print(f"  [Search] Attempt {attempt + 1} failed: {e}")
                time.sleep(2)

        return False

    def clear_search(self):
        """Clear search input."""
        try:
            inp = self.driver.find_element(*self.SEARCH_INPUT)
            inp.clear()
            inp.send_keys(Keys.RETURN)
            time.sleep(1.5)
        except Exception:
            pass

    def click_refresh(self):
        """Click Refresh button on toolbar."""
        try:
            btn = self.driver.find_element(*self.REFRESH_BUTTON)
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════════
    # Row Action Buttons — View / Edit / History
    # ═══════════════════════════════════════════════════════════════════════════

    def click_view_button(self, row_index=0):
        """Click View action button on specified row."""
        try:
            rows = self.driver.find_elements(*self.TABLE_BODY_ROWS)
            if row_index < len(rows):
                btn = rows[row_index].find_element(
                    By.CSS_SELECTOR, "td.mat-column-view button"
                )
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(1.5)
                return True
        except Exception:
            pass
        return False

    def click_edit_button(self, row_index=0):
        """Click Edit action button on specified row."""
        try:
            rows = self.driver.find_elements(*self.TABLE_BODY_ROWS)
            if row_index < len(rows):
                btn = rows[row_index].find_element(
                    By.CSS_SELECTOR, "td.mat-column-edit button"
                )
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(1.5)
                return True
        except Exception:
            pass
        return False

    def click_history_button(self, row_index=0):
        """Click History action button on specified row."""
        try:
            rows = self.driver.find_elements(*self.TABLE_BODY_ROWS)
            if row_index < len(rows):
                btn = rows[row_index].find_element(
                    By.CSS_SELECTOR, "td.mat-column-archive button"
                )
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(1.5)
                return True
        except Exception:
            pass
        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # History Popup
    # ═══════════════════════════════════════════════════════════════════════════

    def is_history_popup_open(self):
        """Check if History popup is visible."""
        try:
            el = self.driver.find_element(*self.HISTORY_POPUP)
            return el.is_displayed()
        except NoSuchElementException:
            return False

    def get_history_row_count(self):
        """Count rows in history table."""
        try:
            rows = self.driver.find_elements(*self.HISTORY_TABLE_ROWS)
            return len(rows)
        except NoSuchElementException:
            return 0

    def is_history_empty(self):
        """Check if history shows 'No data available'."""
        try:
            return self.driver.find_element(*self.NO_DATA_MSG).is_displayed()
        except NoSuchElementException:
            return False

    def close_history_popup(self):
        """Close History popup — 3 JS strategies."""
        # Strategy 1: Cancel button
        try:
            btn = self.driver.find_element(*self.HISTORY_CANCEL)
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(1)
            if not self.is_history_popup_open():
                return
        except Exception:
            pass

        # Strategy 2: X icon
        try:
            icons = self.driver.find_elements(By.CSS_SELECTOR,
                                               ".popup-content button mat-icon")
            for icon in icons:
                if "close" in (icon.text or "").lower():
                    btn = icon.find_element(By.XPATH, "./ancestor::button")
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    if not self.is_history_popup_open():
                        return
        except Exception:
            pass

        # Strategy 3: Force remove overlays
        self.driver.execute_script("""
            document.querySelectorAll('.popup-content').forEach(el => el.remove());
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove());
            document.querySelectorAll('.cdk-overlay-pane').forEach(el => el.remove());
        """)

    def search_in_history(self, search_text):
        """Search inside history popup (requires Enter key)."""
        try:
            inp = self.driver.find_element(By.CSS_SELECTOR,
                                            ".popup-body input[placeholder='Search in table']")
            inp.clear()
            inp.send_keys(str(search_text))
            inp.send_keys(Keys.RETURN)
            time.sleep(1.5)
            return True
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # High-Level One-Call Methods
    # ═══════════════════════════════════════════════════════════════════════════

    def create_hsn_sac(self, data):
        """
        One-call HSN SAC creation.
        Returns dict: {status, error, message, data}
        """
        result = {"status": "failed", "error": "", "message": "", "data": data}
        try:
            self.open_add_form()
            time.sleep(1)

            fill_ok = self.fill_all_fields(data)
            if not fill_ok:
                result["error"] = "Dropdown failed to open after retries"
                return result

            self._force_close_panels()
            time.sleep(0.5)
            self.submit()

            msg = self.handle_success_alert(timeout=20)
            if msg:
                result["status"] = "success"
                result["message"] = msg
            else:
                # Check if validation warning appeared instead
                if self.is_validation_alert_present(timeout=3):
                    warning = self.handle_validation_warning()
                    result["error"] = f"Validation: {warning}"
                else:
                    result["error"] = "No success alert after submit"

        except Exception as e:
            result["error"] = str(e)
            self._cleanup_swal2()
            self._force_close_panels()

        return result

    def edit_hsn_sac(self, row_index, updated_data):
        """
        One-call HSN SAC edit.
        Returns dict: {status, error, message}
        """
        result = {"status": "failed", "error": "", "message": ""}
        try:
            self.click_edit_button(row_index)
            time.sleep(1)

            if not self.is_edit_mode():
                result["error"] = "Edit form did not open"
                return result

            # Fill changed fields
            if updated_data.get("hsn_sac_number"):
                self.fill_hsn_sac_number(updated_data["hsn_sac_number"])
            if updated_data.get("hsn_sac_description"):
                self.fill_hsn_sac_description(updated_data["hsn_sac_description"])
            if updated_data.get("hsn_sac_type"):
                self._select_mat_option(self.HSN_TYPE_SELECT, updated_data["hsn_sac_type"])
                self._force_close_panels()

            self._force_close_panels()
            time.sleep(0.5)
            self.click_update()

            msg = self.handle_success_alert(timeout=20)
            if msg:
                result["status"] = "success"
                result["message"] = msg
            else:
                if self.is_validation_alert_present(timeout=3):
                    warning = self.handle_validation_warning()
                    result["error"] = f"Validation: {warning}"
                else:
                    result["error"] = "No success alert after update"

        except Exception as e:
            result["error"] = str(e)
            self._cleanup_swal2()
            self._force_close_panels()

        return result

    def view_hsn_sac(self, row_index):
        """
        One-call HSN SAC view.
        Returns dict with field values or None.
        """
        try:
            self.click_view_button(row_index)
            time.sleep(1)
            values = self.get_form_field_values()
            self.close_popup()
            return values
        except Exception:
            self.close_popup()
            return None

    def check_history(self, row_index):
        """
        One-call history check.
        Returns dict: {row_count, is_empty, error}
        """
        result = {"row_count": 0, "is_empty": True, "error": ""}
        try:
            self.click_history_button(row_index)
            time.sleep(1.5)

            if not self.is_history_popup_open():
                result["error"] = "History popup did not open"
                return result

            result["row_count"] = self.get_history_row_count()
            result["is_empty"] = self.is_history_empty()

        except Exception as e:
            result["error"] = str(e)
        finally:
            self.close_history_popup()

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # Force Cleanup
    # ═══════════════════════════════════════════════════════════════════════════

    def force_close_form_popup(self):
        """Force close any form popup via JS."""
        self.driver.execute_script("""
            document.querySelectorAll('mat-dialog-container').forEach(el => el.remove());
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove());
            document.querySelectorAll('.cdk-overlay-pane').forEach(el => el.remove());
        """)
