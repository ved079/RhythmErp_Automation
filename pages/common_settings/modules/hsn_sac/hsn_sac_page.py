"""
HSN SAC — Page Object (Optimised v2)
=====================================
UOM gold-standard speed patterns applied:
  - hard_refresh() for fast page reset between tests
  - JS-first interactions (offsetParent checks, JS clicks)
  - Single-strategy methods instead of multi-fallback loops
  - _click_action_menu_item() for 3-dot kebab menu (with row-index fallback)
  - _js_click_popup_button() for Submit/Update
  - Fast polling (0.1s) in _wait_for_page_ready()
  - Reduced all time.sleep() to bare minimum

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
    ADD_BUTTON = (By.XPATH, "button.erp-add-btn")
    FILTER_BUTTON = (By.XPATH, "//*[@mattooltip='Filters']/button")
    REFRESH_BUTTON = (By.XPATH, "//*[@mattooltip='REFRESH']/button")

    # Row action buttons — kept for row-index fallback
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
    # Navigation & page load — FAST (UOM pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def navigate_to_page(self):
        """Navigate to HSN SAC page via direct URL (fast)."""
        self.driver.get(PAGE_URL)
        self._wait_for_page_ready()

    def hard_refresh(self):
        """Hard refresh the current page and wait for ready.
        Much faster than full navigate_to_page() for resetting between tests."""
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait for page table + at least 1 data row with text content.
        Fast polling (0.1s intervals), 5s timeout."""
        end = time.monotonic() + 5
        while time.monotonic() < end:
            try:
                ready = self.driver.execute_script("""
                    var table = document.querySelector('table#excel-table');
                    if (!table) return {table: false};
                    var rows = table.querySelectorAll('tbody tr');
                    var hasData = false;
                    for (var i = 0; i < rows.length; i++) {
                        var cells = rows[i].querySelectorAll('td');
                        for (var j = 0; j < cells.length; j++) {
                            if (cells[j].textContent.trim()) { hasData = true; break; }
                        }
                        if (hasData) break;
                    }
                    return {table: true, data: hasData};
                """)
                if ready and ready.get('table') and ready.get('data'):
                    return
            except Exception:
                pass
            time.sleep(0.1)
        # Fallback: just table is enough if no data yet
        try:
            if self.driver.find_elements("css selector", "table#excel-table"):
                return
        except Exception:
            pass

    def is_page_loaded(self):
        """Check if listing page is loaded — fast JS offsetParent check."""
        try:
            return self.driver.execute_script(
                "var t = document.querySelector('table#excel-table');"
                "return t && t.offsetParent !== null;"
            )
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # Add Form — Open / Close — JS-first (UOM pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def open_add_form(self):
        """Click ADD button via JS click. Single strategy, fast."""
        js_click_add = """
        var btn = document.querySelector('button.erp-add-btn');
        if (!btn) { throw new Error('Add button not found in DOM'); }
        btn.scrollIntoView({block:'center'});
        btn.click();
        return 'clicked';
        """
        try:
            self.driver.execute_script(js_click_add)
        except Exception as e:
            # Fallback: Selenium click
            try:
                btn = self.driver.find_element(*self.ADD_BUTTON)
                self.driver.execute_script("arguments[0].click();", btn)
            except Exception:
                raise Exception(f"Failed to open Add form: {e}")
        # Wait for form popup — fast offsetParent check
        try:
            WebDriverWait(self.driver, 2).until(
                lambda d: d.execute_script(
                    "var el = document.querySelector('input[name=\"HSN SAC Number\"]');"
                    "return el && el.offsetParent !== null;"
                )
            )
        except Exception:
            pass

    def _is_form_popup_open(self):
        """Check if form popup is visible — fast JS offsetParent check."""
        try:
            return self.driver.execute_script("""
                var el = document.querySelector('div.big-model');
                if (el && el.offsetParent !== null) return true;
                var dlg = document.querySelector('mat-dialog-container');
                return dlg && dlg.offsetParent !== null;
            """)
        except Exception:
            return False

    def is_form_open(self):
        """Check if form popup is currently open."""
        return self._is_form_popup_open()

    def is_form_closed(self):
        """Check if form popup is closed."""
        return not self._is_form_popup_open()

    def close_popup(self):
        """Close popup via Cancel button — pure JS (UOM pattern)."""
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
            // Fallback: try X/close icon
            var icons = document.querySelectorAll(
                '.big-model button mat-icon, mat-dialog-container button mat-icon'
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

    def cancel(self):
        """Click Cancel button — pure JS (UOM pattern)."""
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

    # ═══════════════════════════════════════════════════════════════════════════
    # Form — Fill Fields — JS-first
    # ═══════════════════════════════════════════════════════════════════════════

    def fill_hsn_sac_number(self, value):
        """Type into HSN SAC Number input."""
        self.type_text(self.HSN_NUMBER_INPUT, value)

    def fill_hsn_sac_description(self, value):
        """Type into HSN SAC Description input."""
        self.type_text(self.HSN_DESC_INPUT, value)

    def select_hsn_sac_type(self, option_text):
        """Select from HSN SAC Type dropdown (4 fixed options).
        Returns True if selection succeeded, False if dropdown didn't open."""
        return self._select_mat_option(self.HSN_TYPE_SELECT, option_text)

    def fill_all_fields(self, data, max_retries=2):
        """Fill all form fields with retry logic for dropdown.
        Returns True if all fields filled successfully."""
        for attempt in range(1, max_retries + 1):
            success = self._fill_all_fields_once(data)
            if success:
                return True
            # Dropdown failed — retry with page refresh
            self.cancel()
            self.hard_refresh()
            self.open_add_form()
        return False

    def _fill_all_fields_once(self, data):
        """Single pass: fill Dropdown → Text fields."""
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
                self.driver.execute_script("arguments[0].value = '';", el)
            el.send_keys(str(text))
            # Dispatch input event so Angular registers the change
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", el
            )
        except Exception as e:
            raise Exception(f"Failed to type into {locator}: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # Dropdown — Select Option — FAST
    # ═══════════════════════════════════════════════════════════════════════════

    def _select_mat_option(self, select_locator, option_text):
        """Select a specific option from mat-select dropdown.
        Returns True if option selected, False if dropdown didn't open."""
        try:
            # Click the dropdown trigger via JS
            select_el = self.driver.find_element(*select_locator)
            self.driver.execute_script("arguments[0].click();", select_el)

            # Wait for overlay panel to appear — fast poll
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div.cdk-overlay-pane:not(.mat-mdc-dialog-container)")
                    )
                )
            except TimeoutException:
                # Fallback: ActionChains click
                ActionChains(self.driver).move_to_element(select_el).click().perform()
                try:
                    WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "div.cdk-overlay-pane:not(.mat-mdc-dialog-container)")
                        )
                    )
                except TimeoutException:
                    return False

            # Find the matching option via JS (fast)
            clicked = self.driver.execute_script("""
                var options = document.querySelectorAll(
                    'div.mat-mdc-select-panel mat-option, [role="option"]'
                );
                for (var i = 0; i < options.length; i++) {
                    if (options[i].offsetParent !== null
                        && options[i].textContent.indexOf(arguments[0]) !== -1) {
                        options[i].scrollIntoView({block:'center'});
                        options[i].click();
                        return true;
                    }
                }
                return false;
            """, option_text)

            if clicked:
                self._force_close_panels()
                return True
            return False

        except Exception:
            return False

    def _force_close_panels(self):
        """Remove leftover CDK overlay panels (not dialogs)."""
        self.driver.execute_script("""
            document.querySelectorAll(
                'div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)'
            ).forEach(function(el) { el.remove(); });
            document.querySelectorAll('div.cdk-overlay-pane').forEach(function(el) {
                if (!el.querySelector('mat-dialog-container')) el.remove();
            });
        """)

    def _close_select_panel(self):
        """Close dropdown panel via backdrop click."""
        try:
            backdrop = self.driver.find_element(By.CSS_SELECTOR, ".cdk-overlay-backdrop")
            self.driver.execute_script("arguments[0].click();", backdrop)
        except Exception:
            self._force_close_panels()

    # ═══════════════════════════════════════════════════════════════════════════
    # Submit / Update — JS-first (UOM pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def submit(self):
        """Click Submit button via JS click (fast)."""
        self._force_close_panels()
        self._js_click_popup_button('Submit')

    def click_update(self):
        """Click Update button via JS click (fast)."""
        self._force_close_panels()
        self._js_click_popup_button('Update')

    def _js_click_popup_button(self, button_text):
        """Click a popup footer button (Submit/Update) via JS — bypasses overlay issues."""
        js = """
        var footers = document.querySelectorAll('.popup-footer');
        for (var i = 0; i < footers.length; i++) {
            var buttons = footers[i].querySelectorAll('button');
            for (var j = 0; j < buttons.length; j++) {
                if (buttons[j].textContent.trim().indexOf(arguments[0]) !== -1
                    && buttons[j].offsetParent !== null) {
                    buttons[j].click();
                    return 'clicked_' + arguments[0];
                }
            }
        }
        throw new Error('Button "' + arguments[0] + '" not found in popup footer');
        """
        try:
            self.driver.execute_script(js, button_text)
        except Exception:
            # Fallback: Selenium click
            try:
                if button_text == 'Submit':
                    btn = self.driver.find_element(*self.SUBMIT_BUTTON)
                else:
                    btn = self.driver.find_element(*self.UPDATE_BUTTON)
                self.driver.execute_script("arguments[0].click();", btn)
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════════════════════
    # SweetAlert2 — Handle Alerts — FAST (UOM pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def handle_success_alert(self, timeout=3):
        """Handle SweetAlert2 success — instant dismiss via JS.
        Returns the success message text or empty string."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SWAL_CONTAINER)
            )
            # Read title + dismiss + cleanup in ONE JS call
            result = self.driver.execute_script("""
                var title = '';
                var titleEl = document.querySelector('#swal2-title');
                if (titleEl) title = titleEl.textContent.trim();
                var btn = document.querySelector('.swal2-confirm');
                if (btn) btn.click();
                document.querySelectorAll('.swal2-container').forEach(function(el) { el.remove(); });
                return title;
            """)
            return result if result else ""
        except TimeoutException:
            return ""

    def handle_validation_warning(self, timeout=3):
        """Handle SweetAlert2 validation warning — instant dismiss via JS.
        Returns the warning title text or empty string."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SWAL_TITLE)
            )
            # Read + dismiss + cleanup in one JS call
            result = self.driver.execute_script("""
                var title = '';
                var titleEl = document.querySelector('#swal2-title');
                if (titleEl) title = titleEl.textContent.trim();
                var btn = document.querySelector('.swal2-confirm');
                if (btn) btn.click();
                document.querySelectorAll('.swal2-container').forEach(function(el) { el.remove(); });
                return title;
            """)
            return result if result else ""
        except TimeoutException:
            return ""

    def is_validation_alert_present(self, timeout=3):
        """Check if validation SweetAlert2 is visible — fast JS offsetParent poll."""
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
            time.sleep(0.1)
        return False

    def _cleanup_swal2(self):
        """Remove leftover swal2 container + backdrops — pure JS."""
        self.driver.execute_script("""
            document.querySelectorAll('.swal2-container').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.swal2-backdrop-show').forEach(function(el) { el.remove(); });
        """)

    # ═══════════════════════════════════════════════════════════════════════════
    # Form Mode Detection — JS offsetParent checks
    # ═══════════════════════════════════════════════════════════════════════════

    def is_edit_mode(self):
        """Check if Update button is present (Edit mode) — fast JS check."""
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

    def is_view_mode(self):
        """Check if no Submit/Update button (View mode) — fast JS check."""
        try:
            return self.driver.execute_script("""
                var hasSubmit = false, hasUpdate = false;
                var footers = document.querySelectorAll('.popup-footer');
                for (var i = 0; i < footers.length; i++) {
                    var buttons = footers[i].querySelectorAll('button');
                    for (var j = 0; j < buttons.length; j++) {
                        if (buttons[j].textContent.indexOf('Submit') !== -1
                            && buttons[j].offsetParent !== null) hasSubmit = true;
                        if (buttons[j].textContent.indexOf('Update') !== -1
                            && buttons[j].offsetParent !== null) hasUpdate = true;
                    }
                }
                return !hasSubmit && !hasUpdate;
            """)
        except Exception:
            return False

    def _is_submit_visible(self):
        """Check if Submit button is visible — fast JS check."""
        try:
            return self.driver.execute_script("""
                var footers = document.querySelectorAll('.popup-footer');
                for (var i = 0; i < footers.length; i++) {
                    var buttons = footers[i].querySelectorAll('button');
                    for (var j = 0; j < buttons.length; j++) {
                        if (buttons[j].textContent.indexOf('Submit') !== -1
                            && buttons[j].offsetParent !== null) return true;
                    }
                }
                return false;
            """)
        except Exception:
            return False

    def get_form_heading(self):
        """Read popup heading text — JS."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('.big-model h3');"
                "return el ? el.textContent.trim() : '';"
            )
        except Exception:
            return ""

    # ═══════════════════════════════════════════════════════════════════════════
    # Read Form Field Values — JS-first
    # ═══════════════════════════════════════════════════════════════════════════

    def get_form_field_values(self):
        """Read all form field values via JS. Returns dict."""
        try:
            result = self.driver.execute_script("""
                var values = {};
                var numEl = document.querySelector("input[name='HSN SAC Number']");
                values.hsn_sac_number = numEl ? numEl.value : '';
                try {
                    var typeLabel = document.evaluate(
                        "//mat-label[contains(.,'HSN SAC Type')]",
                        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                    ).singleNodeValue;
                    if (typeLabel) {
                        var typeSelect = typeLabel.closest('mat-form-field')
                            ? typeLabel.closest('mat-form-field').querySelector('mat-select')
                            : null;
                        values.hsn_sac_type = typeSelect ? typeSelect.textContent.trim() : '';
                    } else { values.hsn_sac_type = ''; }
                } catch(e) { values.hsn_sac_type = ''; }
                var descEl = document.querySelector("input[name='HSN SAC Description']");
                values.hsn_sac_description = descEl ? descEl.value : '';
                return JSON.stringify(values);
            """)
            import json
            return json.loads(result) if result else {}
        except Exception:
            # Fallback to Selenium
            values = {}
            try:
                values["hsn_sac_number"] = self.driver.find_element(
                    *self.HSN_NUMBER_INPUT).get_attribute("value") or ""
            except Exception:
                values["hsn_sac_number"] = ""
            try:
                values["hsn_sac_type"] = self.driver.find_element(
                    *self.HSN_TYPE_SELECT).text or ""
            except Exception:
                values["hsn_sac_type"] = ""
            try:
                values["hsn_sac_description"] = self.driver.find_element(
                    *self.HSN_DESC_INPUT).get_attribute("value") or ""
            except Exception:
                values["hsn_sac_description"] = ""
            return values

    # ═══════════════════════════════════════════════════════════════════════════
    # Table Operations — JS-first
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
                cell = rows[row_index].find_element(By.CSS_SELECTOR, f"td.{css_class}")
                return cell.text or ""
        except Exception:
            pass
        return ""

    def is_hsn_in_table(self, hsn_number):
        """Check if HSN SAC Number exists in table — pure JS, fast poll."""
        end_time = time.monotonic() + 5
        while time.monotonic() < end_time:
            try:
                found = self.driver.execute_script("""
                    var search = arguments[0].toLowerCase();
                    var table = document.querySelector('table#excel-table');
                    if (!table) return false;
                    var rows = table.querySelectorAll('tbody tr');
                    for (var i = 0; i < rows.length; i++) {
                        var cells = rows[i].querySelectorAll('td');
                        for (var j = 0; j < cells.length; j++) {
                            if (cells[j].textContent.trim().toLowerCase().indexOf(search) !== -1)
                                return true;
                        }
                    }
                    return false;
                """, hsn_number)
                if found:
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def find_hsn_row_index(self, hsn_number):
        """Find row index by HSN SAC Number — pure JS. Returns -1 if not found."""
        try:
            idx = self.driver.execute_script("""
                var search = arguments[0].toLowerCase();
                var table = document.querySelector('table#excel-table');
                if (!table) return -1;
                var rows = table.querySelectorAll('tbody tr');
                for (var i = 0; i < rows.length; i++) {
                    var cells = rows[i].querySelectorAll('td');
                    for (var j = 0; j < cells.length; j++) {
                        if (cells[j].textContent.trim().toLowerCase().indexOf(search) !== -1)
                            return i;
                    }
                }
                return -1;
            """, hsn_number)
            return idx if isinstance(idx, int) else -1
        except Exception:
            return -1

    # ═══════════════════════════════════════════════════════════════════════════
    # Search — JS-first (UOM pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def search_record(self, search_text, max_retries=2):
        """Search table by HSN SAC Number. JS clicks for search toggle + submit.
        Returns True if search executed successfully."""
        for attempt in range(max_retries):
            try:
                # Check if search input already visible
                search_input = None
                try:
                    el = self.driver.find_element("css selector", "input#erpSearchInput")
                    visible = self.driver.execute_script(
                        "var r = arguments[0].getBoundingClientRect();"
                        "return r.width > 0 && r.height > 0;", el
                    )
                    if visible:
                        search_input = el
                except Exception:
                    pass

                # If not visible, click search toggle via JS
                if search_input is None:
                    self.driver.execute_script("""
                        var btn = document.querySelector('button.search-btn');
                        if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
                    """)
                    try:
                        search_input = WebDriverWait(self.driver, 3).until(
                            EC.visibility_of_element_located(("css selector", "input#erpSearchInput"))
                        )
                    except Exception:
                        continue

                # Clear + set value via JS
                self.driver.execute_script("arguments[0].value = '';", search_input)
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                    search_input
                )
                self.driver.execute_script(
                    "arguments[0].value = arguments[1];", search_input, str(search_text)
                )
                search_input.click()
                for event in ["input", "keyup", "change"]:
                    self.driver.execute_script(
                        f"arguments[0].dispatchEvent(new Event('{event}', {{bubbles: true}}));",
                        search_input
                    )

                # Click search button to submit
                self.driver.execute_script("""
                    var btn = document.querySelector('button.search-btn');
                    if (btn) btn.click();
                """)

                # Wait for table refresh
                try:
                    WebDriverWait(self.driver, 3).until(
                        lambda d: d.find_elements("css selector", "table#excel-table tbody tr")
                    )
                except Exception:
                    pass

                return True

            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(0.5)

        return False

    def search_and_verify(self, hsn_number):
        """Search for HSN number, then verify it exists in the filtered results.
        Returns True if found."""
        self.search_record(hsn_number)
        return self.is_hsn_in_table(hsn_number)

    def clear_search(self):
        """Clear search — hard refresh (fastest, like UOM)."""
        self.hard_refresh()

    def click_refresh(self):
        """Click Refresh — use hard_refresh (browser refresh is more reliable)."""
        self.hard_refresh()

    # ═══════════════════════════════════════════════════════════════════════════
    # Row Action Buttons — 3-dot menu + row-index fallback (UOM pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def _click_action_menu_item(self, hsn_number, action_name, retries=3):
        """Click an action menu item (View/Edit/History) for a specific HSN row.
        Tries 3-dot menu first, falls back to individual column buttons.
        Pure JS — fast."""
        self._force_close_panels()

        # Step 1: Try 3-dot menu via JS
        js_open_menu = """
        var search = arguments[0].toLowerCase();
        var table = document.querySelector('table#excel-table');
        if (!table) return null;
        var rows = table.querySelectorAll('tbody tr');
        for (var i = 0; i < rows.length; i++) {
            var cells = rows[i].querySelectorAll('td');
            for (var j = 0; j < cells.length; j++) {
                if (cells[j].textContent.trim().toLowerCase().indexOf(search) !== -1) {
                    // Try 3-dot menu first
                    var menuBtn = rows[i].querySelector('td.cdk-column-actions button');
                    if (menuBtn) {
                        menuBtn.scrollIntoView({block:'center'});
                        menuBtn.click();
                        return 'menu_opened';
                    }
                    return null;
                }
            }
        }
        return null;
        """
        menu_opened = None
        for attempt in range(retries):
            try:
                menu_opened = self.driver.execute_script(js_open_menu, hsn_number)
                if menu_opened:
                    break
            except Exception:
                pass
            if attempt < retries - 1:
                # Try search to bring it into view
                try:
                    self.search_record(hsn_number)
                except Exception:
                    pass

        if menu_opened:
            # Wait for dropdown overlay
            time.sleep(0.1)
            # Click the action item from dropdown
            result = self.driver.execute_script("""
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
                // Fallback: case-insensitive partial match
                for (var i = 0; i < items.length; i++) {
                    var text = items[i].textContent.trim().toLowerCase();
                    if (text.indexOf(arguments[0].toLowerCase()) !== -1) {
                        items[i].click();
                        return 'clicked_partial_' + arguments[0];
                    }
                }
                return null;
            """, action_name)
            if result:
                return result

        # Step 2: Fallback — individual column buttons by row index
        row_index = self.find_hsn_row_index(hsn_number)
        if row_index >= 0:
            return self._click_action_button_by_index(row_index, action_name)

        raise Exception(f"HSN '{hsn_number}' not found in table after {retries} retries")

    def _click_action_button_by_index(self, row_index, action_name):
        """Click an action button on a specific row using individual column buttons.
        Fallback when 3-dot menu is not available."""
        try:
            rows = self.driver.find_elements(*self.TABLE_BODY_ROWS)
            if row_index >= len(rows):
                raise Exception(f"Row index {row_index} out of range ({len(rows)} rows)")

            if action_name == "View":
                col = "mat-column-view"
            elif action_name == "Edit":
                col = "mat-column-edit"
            elif action_name in ("History", "Archive"):
                col = "mat-column-archive"
            else:
                col = "mat-column-view"

            btn = rows[row_index].find_element(By.CSS_SELECTOR, f"td.{col} button")
            self.driver.execute_script("arguments[0].click();", btn)
            return f'clicked_{action_name}_by_index'
        except Exception:
            # Final fallback: try cdk-column-actions
            try:
                rows = self.driver.find_elements(*self.TABLE_BODY_ROWS)
                if row_index < len(rows):
                    btn = rows[row_index].find_element(
                        By.CSS_SELECTOR, "td.cdk-column-actions button"
                    )
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.1)
                    # Click the action from dropdown
                    result = self.driver.execute_script("""
                        var overlay = document.querySelector('.cdk-overlay-container');
                        if (!overlay) return null;
                        var items = overlay.querySelectorAll('button, span, div');
                        for (var i = 0; i < items.length; i++) {
                            if (items[i].textContent.trim() === arguments[0]) {
                                items[i].click();
                                return 'clicked_' + arguments[0];
                            }
                        }
                        return null;
                    """, action_name)
                    if result:
                        return result
            except Exception:
                pass
            raise Exception(f"Failed to click {action_name} on row {row_index}")

    def click_view_button(self, row_index=0, hsn_number=None):
        """Click View action button — uses 3-dot menu if hsn_number provided."""
        if hsn_number:
            self._click_action_menu_item(hsn_number, "View")
        else:
            self._click_action_button_by_index(row_index, "View")
        # Wait for popup to appear
        try:
            WebDriverWait(self.driver, 2).until(
                lambda d: d.execute_script(
                    "var el = document.querySelector('.big-model');"
                    "return el && el.offsetParent !== null;"
                )
            )
        except Exception:
            pass

    def click_edit_button(self, row_index=0, hsn_number=None):
        """Click Edit action button — uses 3-dot menu if hsn_number provided."""
        if hsn_number:
            self._click_action_menu_item(hsn_number, "Edit")
        else:
            self._click_action_button_by_index(row_index, "Edit")
        # Wait for edit popup to appear
        try:
            WebDriverWait(self.driver, 2).until(
                lambda d: d.execute_script(
                    "var el = document.querySelector('input[name=\"HSN SAC Number\"]');"
                    "return el && el.offsetParent !== null;"
                )
            )
        except Exception:
            pass

    def click_history_button(self, row_index=0, hsn_number=None):
        """Click History action button — uses 3-dot menu if hsn_number provided."""
        if hsn_number:
            self._click_action_menu_item(hsn_number, "History")
        else:
            self._click_action_button_by_index(row_index, "History")

    # ═══════════════════════════════════════════════════════════════════════════
    # History Popup — JS-first
    # ═══════════════════════════════════════════════════════════════════════════

    def is_history_popup_open(self):
        """Check if History popup is visible — fast JS offsetParent check."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('.popup-content');"
                "return el && el.offsetParent !== null;"
            )
        except Exception:
            return False

    def get_history_row_count(self):
        """Count rows in history table."""
        try:
            rows = self.driver.find_elements(*self.HISTORY_TABLE_ROWS)
            return len(rows)
        except NoSuchElementException:
            return 0

    def is_history_empty(self):
        """Check if history shows 'No data available' — JS check."""
        try:
            return self.driver.execute_script("""
                var el = document.querySelector('.popup-body p, .popup-body .no-data');
                return el && el.offsetParent !== null
                    && el.textContent.indexOf('No data') !== -1;
            """)
        except Exception:
            return False

    def close_history_popup(self):
        """Close History popup — pure JS (UOM pattern)."""
        # Try Cancel button first
        self.driver.execute_script("""
            var footers = document.querySelectorAll('.popup-content .popup-footer');
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
            // Fallback: try X/close icon
            var icons = document.querySelectorAll('.popup-content button mat-icon');
            for (var i = 0; i < icons.length; i++) {
                if (icons[i].textContent.trim().toLowerCase() === 'close') {
                    var btn = icons[i].closest('button');
                    if (btn) { btn.click(); return 'closed_x'; }
                }
            }
            // Final fallback: force remove overlays
            document.querySelectorAll('.popup-content').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
        """)

    def search_in_history(self, search_text):
        """Search inside history popup — JS-based."""
        try:
            inp = self.driver.find_element(By.CSS_SELECTOR,
                                           ".popup-body input[placeholder='Search in table']")
            self.driver.execute_script("arguments[0].value = '';", inp)
            self.driver.execute_script(
                "arguments[0].value = arguments[1];", inp, str(search_text)
            )
            for event in ["input", "keyup", "change"]:
                self.driver.execute_script(
                    f"arguments[0].dispatchEvent(new Event('{event}', {{bubbles: true}}));",
                    inp
                )
            inp.send_keys(Keys.RETURN)
            return True
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # High-Level One-Call Methods — FAST
    # ═══════════════════════════════════════════════════════════════════════════

    def create_hsn_sac(self, data):
        """One-call HSN SAC creation. Returns dict: {status, error, message, data}"""
        result = {"status": "failed", "error": "", "message": "", "data": data}
        try:
            self.open_add_form()

            fill_ok = self.fill_all_fields(data)
            if not fill_ok:
                result["error"] = "Dropdown failed to open after retries"
                return result

            self._force_close_panels()
            self.submit()

            msg = self.handle_success_alert(timeout=3)
            if msg:
                result["status"] = "success"
                result["message"] = msg
            else:
                # Check if validation warning appeared instead
                if self.is_validation_alert_present(timeout=2):
                    warning = self.handle_validation_warning(timeout=2)
                    result["error"] = f"Validation: {warning}"
                else:
                    result["error"] = "No success alert after submit"

        except Exception as e:
            result["error"] = str(e)
            self._cleanup_swal2()
            self._force_close_panels()

        return result

    def edit_hsn_sac(self, row_index, updated_data, hsn_number=None):
        """One-call HSN SAC edit. Returns dict: {status, error, message}"""
        result = {"status": "failed", "error": "", "message": ""}
        try:
            self.click_edit_button(row_index, hsn_number=hsn_number)

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
            self.click_update()

            msg = self.handle_success_alert(timeout=3)
            if msg:
                result["status"] = "success"
                result["message"] = msg
            else:
                if self.is_validation_alert_present(timeout=2):
                    warning = self.handle_validation_warning(timeout=2)
                    result["error"] = f"Validation: {warning}"
                else:
                    result["error"] = "No success alert after update"

        except Exception as e:
            result["error"] = str(e)
            self._cleanup_swal2()
            self._force_close_panels()

        return result

    def view_hsn_sac(self, row_index, hsn_number=None):
        """One-call HSN SAC view. Returns dict with field values or None."""
        try:
            self.click_view_button(row_index, hsn_number=hsn_number)
            values = self.get_form_field_values()
            self.close_popup()
            return values
        except Exception:
            self.close_popup()
            return None

    def check_history(self, row_index, hsn_number=None):
        """One-call history check. Returns dict: {row_count, is_empty, error}"""
        result = {"row_count": 0, "is_empty": True, "error": ""}
        try:
            self.click_history_button(row_index, hsn_number=hsn_number)

            # Wait for history popup — fast poll
            end_time = time.monotonic() + 3
            while time.monotonic() < end_time:
                if self.is_history_popup_open():
                    break
                time.sleep(0.1)

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
            document.querySelectorAll('mat-dialog-container').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
        """)
