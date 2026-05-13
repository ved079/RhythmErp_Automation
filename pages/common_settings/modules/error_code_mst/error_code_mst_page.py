"""
Error Code Mst — Page Object
=============================
All locators and methods for the Error Code Mst module.
Based on Vehicle Master proven patterns (100% working).
Module: 4 fields (1 dropdown with 4 fixed options, 2 text, 1 toggle).
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    PAGE_URL,
    FIELD_ERROR_CODE_TYPE,
    FIELD_CODE,
    FIELD_DESCRIPTION,
    FIELD_IS_QTY_AMT,
    VALIDATION_FAILED_TITLE,
    VALIDATION_FAILED_CONTENT,
    POPUP_TITLE,
    HISTORY_POPUP_TITLE,
    ERROR_CODE_TYPE_OPTIONS,
    TOGGLE_AMOUNT,
    TOGGLE_QUANTITY,
)


class ErrorCodeMstPage:

    # ═══════════════════════════════════════════════════════════════════════════
    # Locators — Table & Toolbar
    # ═══════════════════════════════════════════════════════════════════════════

    TABLE = (By.CSS_SELECTOR, "table#excel-table")
    TABLE_BODY_ROWS = (By.CSS_SELECTOR, "table#excel-table tbody tr")
    ADD_BUTTON = (By.XPATH, "//*[@mattooltip='ADD']/button")
    REFRESH_BUTTON = (By.XPATH, "//*[@mattooltip='REFRESH']/button")
    MORE_BUTTON = (By.XPATH, "//button[@mattooltip='More']")

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
    POPUP_FOOTER = (By.XPATH, "//div[contains(@class,'popup-footer')]")
    CLOSE_X_BUTTON = (By.XPATH, "//div[contains(@class,'big-model')]//button//mat-icon[contains(text(),'close')]")
    CANCEL_BUTTON = (By.XPATH, "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]")
    SUBMIT_BUTTON = (By.XPATH, "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]")
    UPDATE_BUTTON = (By.XPATH, "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]")

    # ═══════════════════════════════════════════════════════════════════════════
    # Locators — Form Fields (4 fields)
    # ═══════════════════════════════════════════════════════════════════════════

    # Field 1: Error Code Type — Standard mat-select (NOT app-dropdown-v2)
    ERROR_CODE_TYPE_SELECT = (By.XPATH, "//mat-label[contains(.,'Error Code Type')]/ancestor::mat-form-field//mat-select")

    # Field 2: Code — text input, REQUIRED
    CODE_INPUT = (By.CSS_SELECTOR, "input[name='Code']")

    # Field 3: Description — text input, optional
    DESCRIPTION_INPUT = (By.CSS_SELECTOR, "input[name='Description']")

    # Field 4: Is Qty/Amt — custom app-slide-toggle-v2 (Amount/Quantity)
    TOGGLE_CONTAINER = (By.CSS_SELECTOR, ".switch-container.vertical")
    TOGGLE_CHECKBOX = (By.CSS_SELECTOR, ".switch-container.vertical input[type='checkbox']")

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
    HISTORY_TITLE = (By.XPATH, "//h3[contains(.,'History')]")
    HISTORY_CANCEL = (By.XPATH, "//div[contains(@class,'popup')]//button[contains(.,'Cancel')]")
    HISTORY_SEARCH_INPUT = (By.CSS_SELECTOR, ".edit_pop_up input[placeholder='Search box']")
    HISTORY_TABLE_ROWS = (By.CSS_SELECTOR, ".edit_pop_up table tbody tr")
    NO_DATA_IMAGE = (By.CSS_SELECTOR, ".edit_pop_up img[alt='No Data Available']")

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
        """Navigate to Error Code Mst page + force refresh + wait for table."""
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
                self.driver.execute_script(
                    "document.querySelector(\"div[mattooltip='ADD'] button\").click();"
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

    def fill_code(self, value):
        """Type into Code input."""
        self.type_text(self.CODE_INPUT, value)

    def fill_description(self, value):
        """Type into Description input."""
        self.type_text(self.DESCRIPTION_INPUT, value)

    def select_error_code_type(self, option_text):
        """
        Select from Error Code Type dropdown (4 fixed options).
        Standard mat-select with built-in search (NOT app-dropdown-v2).
        Returns True if selection succeeded, False if dropdown didn't open.
        """
        return self._select_mat_option(self.ERROR_CODE_TYPE_SELECT, option_text)

    def toggle_is_qty_amt(self, state):
        """
        Set Is Qty/Amt toggle to 'amount' (off) or 'quantity' (on).
        Clicks the switch container wrapper to toggle state.
        """
        try:
            container = self.driver.find_element(*self.TOGGLE_CONTAINER)
            current = self.is_toggle_quantity()

            want_on = (state == TOGGLE_QUANTITY)
            if current != want_on:
                self.driver.execute_script("arguments[0].click();", container)
                time.sleep(0.5)
        except Exception as e:
            print(f"  [Toggle] Error: {e}")

    def is_toggle_quantity(self):
        """Check if toggle is in Quantity (checked/Yes) state."""
        try:
            cb = self.driver.find_element(*self.TOGGLE_CHECKBOX)
            return cb.is_selected()
        except NoSuchElementException:
            return False

    def is_toggle_amount(self):
        """Check if toggle is in Amount (unchecked/No) state — default."""
        return not self.is_toggle_quantity()

    def fill_all_fields(self, data, max_retries=3):
        """
        Fill all form fields with retry logic for dropdown.
        Order: Dropdown FIRST → Text fields → Toggle.
        Returns True if all fields filled successfully.
        """
        for attempt in range(1, max_retries + 1):
            success = self._fill_all_fields_once(data)
            if success:
                return True
            print(f"  [Retry {attempt}/{max_retries}] Dropdown didn't register, retrying...")
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
        Single pass: fill Dropdown → Text fields → Toggle.
        Returns True if dropdown registered and all fields filled.
        """
        # 1. Dropdown FIRST (most likely to fail)
        error_type = data.get("error_code_type", "")
        if error_type:
            dropdown_ok = self.select_error_code_type(error_type)
            if not dropdown_ok:
                return False
            self._force_close_panels()

        # 2. Text fields
        code = data.get("code", "")
        desc = data.get("description", "")
        if code:
            self.fill_code(code)
        if desc:
            self.fill_description(desc)

        # 3. Toggle
        qty_amt = data.get("is_qty_amt", TOGGLE_AMOUNT)
        if qty_amt:
            self.toggle_is_qty_amt(qty_amt)

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
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", el
            )
        except Exception as e:
            raise Exception(f"Failed to type into {locator}: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # Dropdown — Select Option (Standard mat-select with built-in search)
    # ═══════════════════════════════════════════════════════════════════════════

    def _select_mat_option(self, select_locator, option_text):
        """
        Select a specific option from mat-select dropdown.
        Standard mat-select with built-in search panel.
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
                # Fallback: ActionChains click
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
                if opt.is_displayed() and option_text.strip() in (opt.text or ""):
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true); arguments[0].click();", opt
                    )
                    time.sleep(0.8)
                    self._force_close_panels()
                    return True

            # Fallback: try by role=option
            all_options = self.driver.find_elements(By.CSS_SELECTOR, "[role='option']")
            for opt in all_options:
                if opt.is_displayed() and option_text.strip() in (opt.text or ""):
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

    def get_dropdown_options(self):
        """Get all current options from Error Code Type dropdown. Returns list of strings."""
        options = []
        try:
            select_el = self.driver.find_element(*self.ERROR_CODE_TYPE_SELECT)
            self.driver.execute_script("arguments[0].click();", select_el)
            time.sleep(1.5)

            opts = self.driver.find_elements(By.CSS_SELECTOR, "div.mat-mdc-select-panel mat-option")
            for opt in opts:
                if opt.is_displayed() and (opt.text or "").strip():
                    options.append(opt.text.strip())

            self._force_close_panels()
        except Exception:
            self._force_close_panels()
        return options

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
    # NOTE: Error Code Mst does NOT show success SweetAlert2 on create/update.
    # Form closes silently. Only "Validation Failed" alert appears for errors.

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

    def is_sweetalert_visible(self, timeout=5):
        """Check if any SweetAlert2 popup is visible."""
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SWAL_CONTAINER)
            )
            return el.is_displayed()
        except TimeoutException:
            return False

    def is_validation_alert_present(self, timeout=5):
        """Check if validation SweetAlert2 is visible with 'Validation Failed'."""
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SWAL_TITLE)
            )
            return VALIDATION_FAILED_TITLE in (el.text or "")
        except TimeoutException:
            return False

    def get_sweetalert_title(self, timeout=5):
        """Get SweetAlert2 title text."""
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SWAL_TITLE)
            )
            return el.text or ""
        except TimeoutException:
            return ""

    def get_sweetalert_message(self, timeout=5):
        """Get SweetAlert2 body message."""
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SWAL_CONTENT)
            )
            return el.text or ""
        except TimeoutException:
            return ""

    def accept_sweetalert(self, timeout=10):
        """Click OK/confirm on SweetAlert2."""
        try:
            confirm = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(self.SWAL_CONFIRM)
            )
            self.driver.execute_script("arguments[0].click();", confirm)
            time.sleep(0.5)
        except Exception:
            self._cleanup_swal2()

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
            select_el = self.driver.find_element(*self.ERROR_CODE_TYPE_SELECT)
            values["error_code_type"] = select_el.text.strip() or ""
        except NoSuchElementException:
            values["error_code_type"] = ""

        try:
            values["code"] = self.driver.find_element(
                *self.CODE_INPUT
            ).get_attribute("value") or ""
        except NoSuchElementException:
            values["code"] = ""

        try:
            values["description"] = self.driver.find_element(
                *self.DESCRIPTION_INPUT
            ).get_attribute("value") or ""
        except NoSuchElementException:
            values["description"] = ""

        try:
            values["is_qty_amt"] = TOGGLE_QUANTITY if self.is_toggle_quantity() else TOGGLE_AMOUNT
        except Exception:
            values["is_qty_amt"] = TOGGLE_AMOUNT

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

    def is_code_in_table(self, code):
        """Check if Code value exists in table (partial match)."""
        try:
            rows = self.driver.find_elements(*self.TABLE_BODY_ROWS)
            for row in rows:
                cells = row.find_elements(By.CSS_SELECTOR, "td")
                for cell in cells:
                    if code in (cell.text or ""):
                        return True
        except Exception:
            pass
        return False

    def find_code_row_index(self, code):
        """Find row index by Code value (partial match). Returns -1 if not found."""
        try:
            rows = self.driver.find_elements(*self.TABLE_BODY_ROWS)
            for i, row in enumerate(rows):
                cells = row.find_elements(By.CSS_SELECTOR, "td")
                for cell in cells:
                    if code in (cell.text or ""):
                        return i
        except Exception:
            pass
        return -1

    def click_refresh(self):
        """Click Refresh button on toolbar."""
        try:
            btn = self.driver.find_element(*self.REFRESH_BUTTON)
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)
        except Exception:
            pass

    def wait_for_table_load(self, timeout=15):
        """Wait until table has at least 1 row."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(*self.TABLE_BODY_ROWS)) > 0
            )
        except TimeoutException:
            pass

    # ═══════════════════════════════════════════════════════════════════════════
    # Row Action Buttons — View / Edit / History
    # ═══════════════════════════════════════════════════════════════════════════

    def click_view_on_row(self, row_index=0):
        """Click View action button (eye icon) on specified row."""
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

    def click_edit_on_row(self, row_index=0):
        """Click Edit action button (pencil icon) on specified row."""
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

    def click_history_on_row(self, row_index=0):
        """Click History action button (archive icon) on specified row."""
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
            el = self.driver.find_element(*self.HISTORY_TITLE)
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
        """Check if history shows 'No Data Available'."""
        try:
            el = self.driver.find_element(*self.NO_DATA_IMAGE)
            return el.is_displayed()
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

        # Strategy 2: Force remove overlays
        self.driver.execute_script("""
            document.querySelectorAll('.popup-content').forEach(el => el.remove());
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove());
            document.querySelectorAll('.cdk-overlay-pane').forEach(el => el.remove());
        """)

    def search_in_history(self, search_text):
        """Search inside history popup."""
        try:
            inp = self.driver.find_element(*self.HISTORY_SEARCH_INPUT)
            inp.clear()
            inp.send_keys(str(search_text))
            time.sleep(1.5)
            return True
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # High-Level One-Call Methods
    # ═══════════════════════════════════════════════════════════════════════════

    def create_record(self, data):
        """
        One-call record creation: open form → fill all → submit.
        NOTE: Error Code Mst does NOT show success SweetAlert2.
        Form closes silently on success.
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

            # Wait for form to close (no success alert for this module)
            time.sleep(3)

            # Check if form closed = success
            if self.is_form_closed():
                result["status"] = "success"
                result["message"] = "Record created (form closed silently)"
            else:
                # Validation alert appeared
                if self.is_validation_alert_present(timeout=3):
                    warning = self.handle_validation_warning()
                    result["error"] = f"Validation: {warning}"
                else:
                    result["error"] = "Form still open after submit — unknown error"

        except Exception as e:
            result["error"] = str(e)
            self._cleanup_swal2()
            self._force_close_panels()

        return result

    def edit_record(self, row_index, updated_data):
        """
        One-call record edit: click edit → fill changed fields → update.
        NOTE: No success SweetAlert2 — form closes silently on success.
        Returns dict: {status, error, message}
        """
        result = {"status": "failed", "error": "", "message": ""}
        try:
            self.click_edit_on_row(row_index)
            time.sleep(1)

            if not self.is_edit_mode():
                result["error"] = "Edit form did not open"
                return result

            # Fill changed fields
            if updated_data.get("code"):
                self.fill_code(updated_data["code"])
            if updated_data.get("description"):
                self.fill_description(updated_data["description"])
            if updated_data.get("error_code_type"):
                self._select_mat_option(self.ERROR_CODE_TYPE_SELECT, updated_data["error_code_type"])
                self._force_close_panels()
            if updated_data.get("is_qty_amt"):
                self.toggle_is_qty_amt(updated_data["is_qty_amt"])

            self._force_close_panels()
            time.sleep(0.5)
            self.click_update()

            # Wait for form to close
            time.sleep(3)

            if self.is_form_closed():
                result["status"] = "success"
                result["message"] = "Record updated (form closed silently)"
            else:
                if self.is_validation_alert_present(timeout=3):
                    warning = self.handle_validation_warning()
                    result["error"] = f"Validation: {warning}"
                else:
                    result["error"] = "Form still open after update — unknown error"

        except Exception as e:
            result["error"] = str(e)
            self._cleanup_swal2()
            self._force_close_panels()

        return result

    def view_record(self, row_index):
        """
        One-call view: click view → read values → close.
        Returns dict with field values or None.
        """
        try:
            self.click_view_on_row(row_index)
            time.sleep(1)
            values = self.get_form_field_values()
            self.cancel()
            return values
        except Exception:
            self.cancel()
            return None

    def check_history(self, row_index):
        """
        One-call history check.
        Returns dict: {row_count, is_empty, error}
        """
        result = {"row_count": 0, "is_empty": True, "error": ""}
        try:
            self.click_history_on_row(row_index)
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
            document.querySelectorAll('.big-model').forEach(el => el.remove());
            document.querySelectorAll('.edit_pop_up').forEach(el => el.remove());
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove());
            document.querySelectorAll('.cdk-overlay-pane').forEach(el => el.remove());
        """)

    def force_cleanup_all(self):
        """Force close everything — popups, alerts, panels."""
        self._cleanup_swal2()
        self._force_close_panels()
        self.force_close_form_popup()
