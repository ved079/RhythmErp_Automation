"""
register_charges_page.py
------------------------
Page Object Model for RhythmERP Register Charges screen.

Flat popup form — no steppers, no child grids.
Fields: Charge ID (ROC), Type of Charge, Description, Amount Secured,
        Charge Holder Details, Date of Satisfaction.

Location: Registration > Register Charges
URL:      /#/dynamic-screens/Register%20Charges/Register%20Charges
"""

import os
import sys

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
    InvalidSessionIdException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL


class RegisterChargesPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Register%20Charges/Register%20Charges"

    # ── Toolbar ──────────────────────────────────────────────────
    ADD_BUTTON = ("css", "button.erp-add-btn")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    SEARCH_INPUT = ("css", ".erp-search-wrapper input, input#erpSearchInput")

    # ── Popup structure ──────────────────────────────────────────
    FORM_POPUP = ("css", ".big-model, mat-dialog-container")
    CANCEL_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]",
    )
    CLOSE_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-header')]//button[.//mat-icon[text()='close']]",
    )

    # ── SweetAlert2 ──────────────────────────────────────────────
    SWAL_TITLE = ("css", "#swal2-title")
    SWAL_CONFIRM = ("css", ".swal2-confirm")

    # ── Validation errors ────────────────────────────────────────
    MAT_ERROR = ("css", "mat-error, .mat-mdc-form-field-error")

    # ── Row action menu ──────────────────────────────────────────
    ROW_ACTION_TRIGGER = ("css", "button.mat-mdc-menu-trigger.erp-row-trigger")
    MENU_EDIT = (
        "xpath",
        "//button[contains(@class,'erp-menu-item')][.//span[contains(.,'Modify this record')]]",
    )
    MENU_VIEW = (
        "xpath",
        "//button[contains(@class,'erp-menu-item')][.//span[contains(.,'Open record details')]]",
    )
    MENU_HISTORY = (
        "xpath",
        "//button[contains(@class,'erp-menu-item')][.//span[contains(.,'View change log')]]",
    )
    CHANGE_LOG_PANEL = (
        "xpath",
        "//th[contains(@class,'cdk-column-created_date_time')]",
    )

    # ══════════════════════════════════════════════════════════════
    #  Navigation
    # ══════════════════════════════════════════════════════════════

    def navigate_to_page(self):
        log.info("Navigating to Register Charges page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "table#excel-table, button.erp-add-btn")
                )
            )
            log.info("Register Charges page loaded")
        except TimeoutException:
            log.warning("Register Charges page elements not found, may be empty")

    # ══════════════════════════════════════════════════════════════
    #  Add form
    # ══════════════════════════════════════════════════════════════

    def open_add_form(self):
        log.info("Opening ADD Register Charges form...")
        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, "button.erp-add-btn")
            if btn.is_displayed():
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1.5)
                if self._is_form_popup_open():
                    self._wait_for_form_content(timeout=5)
                    log.info("ADD form opened")
                    return
        except Exception:
            pass
        raise Exception("ADD button not found or not clickable")

    # ══════════════════════════════════════════════════════════════
    #  Form fill
    # ══════════════════════════════════════════════════════════════

    def fill_form(self, data):
        log.info("Filling Register Charges form fields...")

        if data.get("date_of_creation"):
            self._fill_date_input("Date of Creation", data["date_of_creation"])

        if data.get("date_of_modification"):
            self._fill_date_input("Date of Modification", data["date_of_modification"])

        if data.get("roc_charge_id"):
            self._fill_input_by_label_js("Charge ID (ROC)", str(data["roc_charge_id"]))

        # Type of Charge — pick first available (tenant-universal)
        if data.get("type_of_charge") is not None and data.get("type_of_charge") != "":
            self._select_first_available_mat_option("Type of Charge")

        if data.get("description_of_assets_property"):
            self._fill_input_by_label_js(
                "Description of Assets/Property",
                data["description_of_assets_property"],
            )

        if data.get("amount_secured") is not None and data.get("amount_secured") != "":
            self._fill_input_by_label_js("Amount Secured", str(data["amount_secured"]))

        if data.get("charge_holder_details"):
            self._fill_input_by_label_js(
                "Charge Holder Details", data["charge_holder_details"]
            )

        if data.get("date_of_satisfaction"):
            self._fill_date_input("Date of Satisfaction", data["date_of_satisfaction"])

        self._force_close_panels()
        log.info("Register Charges form filled")

    # ══════════════════════════════════════════════════════════════
    #  Submit form
    # ══════════════════════════════════════════════════════════════

    def submit_form(self):
        log.info("Clicking Submit button...")
        xpaths = [
            "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]",
            "//button[contains(.,'Update')]",
        ]
        btn = None
        for xp in xpaths:
            try:
                el = self.driver.find_element(By.XPATH, xp)
                if el.is_displayed():
                    btn = el
                    break
            except Exception:
                continue
        if btn is None:
            raise RuntimeError("Submit/Update button not found")
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});"
            "arguments[0].click();",
            btn,
        )
        self.wait_seconds(1)
        log.info("Submit button clicked")

    # ══════════════════════════════════════════════════════════════
    #  SweetAlert handlers
    # ══════════════════════════════════════════════════════════════

    def handle_success_alert(self, timeout=15):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-container"))
            )
            self.wait_seconds(1)
        except (TimeoutException, InvalidSessionIdException):
            inline_errors = self.get_mat_error_text()
            if inline_errors:
                return f"VALIDATION_ERRORS: {'; '.join(inline_errors[:5])}"
            log.warning("No SweetAlert2 alert appeared")
            return ""

        try:
            title = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title").text.strip()
        except Exception:
            try:
                title = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-container"
                ).text.strip()
            except Exception:
                title = ""

        try:
            self._swal2_confirm_click()
            self.wait_seconds(1)
        except Exception:
            pass

        return title

    def handle_validation_warning(self, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-container"))
            )
            try:
                title = self.driver.find_element(
                    By.CSS_SELECTOR, "#swal2-title"
                ).text.strip()
            except Exception:
                try:
                    title = self.driver.find_element(
                        By.CSS_SELECTOR, ".swal2-container"
                    ).text.strip()
                except Exception:
                    title = ""
            try:
                self._swal2_confirm_click()
                self.wait_seconds(0.5)
            except Exception:
                pass
            return title
        except (TimeoutException, InvalidSessionIdException):
            return ""

    def _swal2_confirm_click(self):
        for _ in range(3):
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_seconds(0.5)
                    return
            except Exception:
                pass
            self.wait_seconds(0.5)

    # ══════════════════════════════════════════════════════════════
    #  JS fill helpers
    # ══════════════════════════════════════════════════════════════

    def _fill_input_by_label_js(self, label_text, value):
        if not value:
            return
        log.info(f"Label-based input fill: label='{label_text}', value='{str(value)[:50]}...'")
        try:
            result = self.driver.execute_script("""
                var labelText = arguments[0];
                var val = arguments[1];
                var targetInput = null;
                var tryFind = function(scope) {
                    var labels = scope.querySelectorAll('mat-label');
                    for (var i = 0; i < labels.length; i++) {
                        if (labels[i].textContent.trim().indexOf(labelText) !== -1) {
                            var field = labels[i].closest('mat-form-field, .mat-mdc-form-field');
                            if (field) {
                                var inputs = field.querySelectorAll('input');
                                for (var j = 0; j < inputs.length; j++) {
                                    var style = inputs[j].getAttribute('style') || '';
                                    if (inputs[j].offsetParent !== null
                                        && style.indexOf('display: none') === -1) {
                                        return inputs[j];
                                    }
                                }
                            }
                        }
                    }
                    return null;
                };
                var popup = document.querySelector('.big-model, .edit_pop_up, mat-dialog-container');
                if (popup) targetInput = tryFind(popup);
                if (!targetInput) targetInput = tryFind(document);
                if (!targetInput) return {success: false, error: 'Input not found for: ' + labelText};
                targetInput.scrollIntoView({block: 'center'});
                targetInput.focus();
                var nativeSet = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSet.call(targetInput, '');
                targetInput.dispatchEvent(new Event('input', {bubbles: true}));
                targetInput.dispatchEvent(new Event('change', {bubbles: true}));
                nativeSet.call(targetInput, val);
                targetInput.dispatchEvent(new Event('input', {bubbles: true}));
                targetInput.dispatchEvent(new Event('change', {bubbles: true}));
                targetInput.dispatchEvent(new Event('blur', {bubbles: true}));
                return {success: true};
            """, label_text, str(value))
            if result and result.get("success"):
                log.info(f"Label-based input fill succeeded: '{label_text}'")
            else:
                error = result.get("error", "Unknown") if result else "JS returned null"
                log.warning(f"Label-based input fill failed: '{label_text}' — {error}")
        except Exception as e:
            log.warning(f"Label-based input fill exception for '{label_text}': {e}")

    def _select_first_available_mat_option(self, label_text):
        log.info(f"Selecting first available option for: '{label_text}'")
        try:
            select_el = self.driver.execute_script("""
                var labelText = arguments[0];
                var popup = document.querySelector('.big-model, .edit_pop_up, mat-dialog-container');
                if (!popup) return null;
                var labels = popup.querySelectorAll('mat-label');
                for (var i = 0; i < labels.length; i++) {
                    if (labels[i].textContent.trim().includes(labelText)) {
                        var field = labels[i].closest('mat-form-field, .mat-mdc-form-field');
                        if (field) {
                            var s = field.querySelector('mat-select');
                            if (s && s.offsetParent !== null) return s;
                        }
                    }
                }
                return null;
            """, label_text)
            if not select_el:
                log.warning(f"Dropdown not found for label: '{label_text}'")
                return
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
                select_el,
            )
            self.wait_seconds(0.8)
            options = self.driver.find_elements(
                By.CSS_SELECTOR, "div[role='listbox'] mat-option"
            )
            for opt in options:
                try:
                    if opt.is_displayed():
                        opt_text = opt.text.strip()
                        self.driver.execute_script("arguments[0].click();", opt)
                        self.wait_seconds(0.4)
                        self._close_select_panel()
                        log.info(f"Selected first available option '{opt_text}' for '{label_text}'")
                        return
                except Exception:
                    continue
            self._close_select_panel()
            log.warning(f"No options found for '{label_text}'")
        except InvalidSessionIdException:
            raise
        except Exception as e:
            log.warning(f"_select_first_available_mat_option failed for '{label_text}': {e}")
            self._close_select_panel()

    def _fill_date_input(self, label_text, iso_date_str):
        if not iso_date_str:
            return
        try:
            date_part = iso_date_str.split("T")[0]
            parts = date_part.split("-")
            dmy = f"{parts[2]}/{parts[1]}/{parts[0]}" if len(parts) == 3 else ""
        except Exception:
            dmy = ""
        if not dmy:
            return
        log.info(f"Filling date input: label='{label_text}', value='{dmy}'")
        try:
            self.driver.execute_script("""
                var labelText = arguments[0]; var dateValue = arguments[1];
                var popup = document.querySelector('.big-model, .edit_pop_up, mat-dialog-container');
                if (!popup) return;
                var labels = popup.querySelectorAll('mat-label');
                for (var i = 0; i < labels.length; i++) {
                    if (labels[i].textContent.trim().includes(labelText)) {
                        var field = labels[i].closest('mat-form-field, .mat-mdc-form-field');
                        if (field) {
                            var inp = field.querySelector('input');
                            if (!inp) continue;
                            inp.scrollIntoView({block:'center'}); inp.focus();
                            var nativeSet = Object.getOwnPropertyDescriptor(
                                window.HTMLInputElement.prototype, 'value').set;
                            nativeSet.call(inp, '');
                            inp.dispatchEvent(new Event('input', {bubbles: true}));
                            nativeSet.call(inp, dateValue);
                            inp.dispatchEvent(new Event('input', {bubbles: true}));
                            inp.dispatchEvent(new Event('change', {bubbles: true}));
                            inp.dispatchEvent(new Event('blur', {bubbles: true}));
                            return;
                        }
                    }
                }
            """, label_text, dmy)
            log.info(f"Date input '{label_text}' filled: {dmy}")
        except Exception as e:
            log.warning(f"Date input exception for '{label_text}': {e}")

    # ══════════════════════════════════════════════════════════════
    #  Overlay helpers
    # ══════════════════════════════════════════════════════════════

    def _force_close_panels(self):
        try:
            self.driver.execute_script("""
                document.querySelectorAll(
                    'div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)'
                ).forEach(function(el) { el.remove(); });
                document.querySelectorAll('div.cdk-overlay-pane').forEach(function(el) {
                    if (!el.querySelector('mat-dialog-container')) el.remove();
                });
            """)
            self.wait_seconds(0.2)
        except InvalidSessionIdException:
            raise
        except Exception:
            pass

    def _close_select_panel(self):
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
                except InvalidSessionIdException:
                    raise
                except Exception:
                    pass
        except InvalidSessionIdException:
            raise
        except Exception:
            pass
        try:
            self._force_close_panels()
        except Exception:
            pass

    def _is_form_popup_open(self):
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

    def _wait_for_form_content(self, timeout=5):
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR, "div.big-model input, mat-dialog-container input"
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
        return False

    def force_close_form_popup(self):
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]",
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
        try:
            close_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-header')]//button[.//mat-icon[text()='close']]",
            )
            for btn in close_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(0.5)
                        return
                except Exception:
                    continue
        except Exception:
            pass
        try:
            self.driver.execute_script("""
                document.querySelectorAll('mat-dialog-container').forEach(function(el) { el.remove(); });
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
                document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
                document.querySelectorAll('.big-model').forEach(function(el) { el.remove(); });
            """)
            self.wait_seconds(0.5)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════
    #  Validation errors
    # ══════════════════════════════════════════════════════════════

    def get_mat_error_text(self):
        errors = []
        try:
            for el in self.driver.find_elements(
                By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
            ):
                try:
                    text = el.text.strip()
                    if text and el.is_displayed():
                        errors.append(text)
                except Exception:
                    continue
        except Exception:
            pass
        return errors

    # ══════════════════════════════════════════════════════════════
    #  Table operations
    # ══════════════════════════════════════════════════════════════

    def search_entry(self, text):
        log.info(f"Searching for: {text}")
        try:
            # Open search bar via JS click on the search/filter button
            self.driver.execute_script("""
                var btns = document.querySelectorAll(
                    'button[mattooltip="Search"], button.search-btn, button[aria-label="Search"]'
                );
                for (var b of btns) {
                    if (b.offsetParent !== null) { b.click(); return; }
                }
            """)
            self.wait_seconds(0.5)

            inp = self.driver.execute_script("""
                var candidates = document.querySelectorAll(
                    '#erpSearchInput, .erp-search-wrapper input, input[placeholder*="Search"]'
                );
                for (var c of candidates) {
                    if (c.offsetParent !== null) return c;
                }
                return null;
            """)
            if inp:
                self.driver.execute_script("""
                    var inp = arguments[0]; var val = arguments[1];
                    inp.focus();
                    var nativeSet = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value').set;
                    nativeSet.call(inp, '');
                    inp.dispatchEvent(new Event('input', {bubbles: true}));
                    nativeSet.call(inp, val);
                    inp.dispatchEvent(new Event('input', {bubbles: true}));
                    inp.dispatchEvent(new Event('change', {bubbles: true}));
                """, inp, text)
                # Send actual Enter via Selenium to trigger search
                from selenium.webdriver.common.keys import Keys as _Keys
                try:
                    inp.send_keys(_Keys.ENTER)
                except Exception:
                    self.driver.execute_script(
                        "arguments[0].dispatchEvent(new KeyboardEvent('keydown',"
                        "{bubbles:true,cancelable:true,key:'Enter',keyCode:13}));",
                        inp,
                    )
                self.wait_seconds(3)
                log.info(f"Search executed for: {text}")
            else:
                log.warning("Search input not found")
        except Exception as e:
            log.warning(f"Search failed: {e}")

    def is_entry_in_table(self, search_text):
        try:
            cells = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody td"
            )
            for cell in cells:
                try:
                    if search_text.lower() in cell.text.strip().lower():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def get_table_row_count(self):
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            count = 0
            for row in rows:
                try:
                    cells = row.find_elements(By.CSS_SELECTOR, "td")
                    has_data = any(cell.text.strip() for cell in cells)
                    no_data_classes = row.get_attribute("class") or ""
                    if (
                        has_data
                        and "no-data" not in no_data_classes
                        and "mat-mdc-no-data-row" not in no_data_classes
                    ):
                        count += 1
                except Exception:
                    continue
            return count
        except Exception:
            return 0

    # ══════════════════════════════════════════════════════════════
    #  Row action menu
    # ══════════════════════════════════════════════════════════════

    def click_row_action(self, row_index=0):
        triggers = self.driver.find_elements(
            By.CSS_SELECTOR, "button.mat-mdc-menu-trigger.erp-row-trigger"
        )
        if row_index < len(triggers):
            self.driver.execute_script("arguments[0].click();", triggers[row_index])
            self.wait_seconds(0.5)
        else:
            raise Exception(f"Row action trigger {row_index} not found")

    def click_menu_edit(self):
        try:
            btn = self.driver.find_element(*self.MENU_EDIT)
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
                if self._is_form_popup_open():
                    self._wait_for_form_content(timeout=5)
                    log.info("Edit form opened")
        except Exception as e:
            log.warning(f"Menu Edit click failed: {e}")

    def click_menu_view(self):
        try:
            btn = self.driver.find_element(*self.MENU_VIEW)
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
                if self._is_form_popup_open():
                    self._wait_for_form_content(timeout=5)
                    log.info("View form opened")
        except Exception as e:
            log.warning(f"Menu View click failed: {e}")

    def click_cancel_button(self):
        try:
            btn = self.driver.find_element(*self.CANCEL_BUTTON)
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
                log.info("Cancel button clicked")
        except Exception as e:
            log.warning(f"Cancel button click failed: {e}")

    def click_close_button(self):
        try:
            btn = self.driver.find_element(*self.CLOSE_BUTTON)
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
                log.info("Close button clicked")
        except Exception as e:
            log.warning(f"Close button click failed: {e}")

    def click_menu_history(self):
        try:
            btn = self.driver.find_element(*self.MENU_HISTORY)
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1.5)
                log.info("Menu View change log clicked")
        except Exception as e:
            log.warning(f"Menu View change log click failed: {e}")
