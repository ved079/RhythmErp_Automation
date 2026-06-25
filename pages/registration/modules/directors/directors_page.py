"""
directors_page.py
-----------------
Page Object Model for RhythmERP Directors screen.

The Directors screen is a flat popup form (no mat-horizontal-stepper).
All 15 master fields fill top-to-bottom in one fill_form() call.
KYC Details is a child grid inside an app-dynamic-details component.

Location: Registration > Directors
URL:      /#/dynamic-screens/Directors/Directors
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
    ElementClickInterceptedException,
    StaleElementReferenceException,
    InvalidSessionIdException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT
from pages.registration.modules.directors.data.directors_data import (
    PREFIX_NAMES,
    KYC_DOC_NAMES,
    SWAL_TITLE_VALIDATION_FAILED,
    SWAL_TITLE_SUCCESS,
    SWAL_TITLE_UPDATED,
)


class DirectorsPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Directors/Directors"

    # ── Toolbar ──────────────────────────────────────────────────
    ADD_BUTTON = ("css", "button.erp-add-btn")
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    SEARCH_INPUT = ("css", ".erp-search-wrapper input, input#erpSearchInput")

    # ── Popup structure ──────────────────────────────────────────
    FORM_POPUP = ("css", ".big-model, mat-dialog-container")
    FORM_HEADING = ("css", ".popup-header h3")
    SUBMIT_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]",
    )
    CANCEL_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]",
    )
    CLOSE_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-header')]//button[.//mat-icon[text()='close']]",
    )

    # ── Top-level field locators ─────────────────────────────────
    PARTY_REFERENCE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Party Reference')]/ancestor::mat-form-field//mat-select",
    )
    PREFIX_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Prefix')]/ancestor::mat-form-field//mat-select",
    )
    DIRECTOR_NAME_INPUT = ("css", "input[name='Director Name']")
    DESIGNATION_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Designation')]/ancestor::mat-form-field//mat-select",
    )
    PAN_INPUT = ("css", "input[name='PAN/Other']")
    ADDRESS_INPUT = ("css", "input[name='Residential Address']")
    PHONE_INPUT = ("css", "input[name='Phone Number']")
    NO_CLASS_SHARES_INPUT = (
        "css",
        "input[name='Number and Class of Shares ']",
    )
    OTHER_DIRECTORSHIPS_INPUT = (
        "css",
        "input[name='Details of Other Directorships']",
    )
    PERCENTAGE_SHARES_INPUT = ("css", "input[name='Percentage of Shares']")
    AGE_INPUT = ("css", "input[name='Age']")
    QUALIFICATION_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Qualification')]/ancestor::mat-form-field//mat-select",
    )
    EXPERIENCE_INPUT = ("css", "input[name='Experience in Years']")

    # ── KYC Details child grid ───────────────────────────────────
    KYC_ADD_ROW_BUTTON = (
        "xpath",
        "//app-dynamic-details//button[.//mat-icon[text()='add']]",
    )
    KYC_NUMBER_INPUT = ("css", "input[name='KYC Number']")

    # ── SweetAlert2 ──────────────────────────────────────────────
    SWAL_TITLE = ("css", "#swal2-title")
    SWAL_CONFIRM = ("css", ".swal2-confirm")

    # ── Validation errors ────────────────────────────────────────
    MAT_ERROR = ("css", "mat-error, .mat-mdc-form-field-error")

    # ── Row action menu ──────────────────────────────────────────
    ROW_ACTION_TRIGGER = ("css", "button.mat-mdc-menu-trigger.erp-row-trigger")
    MENU_EDIT = (
        "xpath",
        "//button[contains(@class,'erp-menu-item')][.//span[contains(.,'Edit')]]",
    )
    MENU_VIEW = (
        "xpath",
        "//button[contains(@class,'erp-menu-item')][.//span[contains(.,'View')]]",
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
    #  Navigation & page load
    # ══════════════════════════════════════════════════════════════

    def navigate_to_page(self):
        log.info("Navigating to Directors page...")
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
            log.info("Directors page loaded")
        except TimeoutException:
            log.warning("Directors page elements not found, may be empty")

    # ══════════════════════════════════════════════════════════════
    #  Add form
    # ══════════════════════════════════════════════════════════════

    def open_add_form(self):
        log.info("Opening ADD Directors form...")
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
                    log.info("ADD form opened via erp-add-btn")
                    return
        except Exception:
            pass
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
                            log.info("ADD form opened via mini-fab icon")
                            return
                except Exception:
                    continue
        except Exception:
            pass
        raise Exception("ADD button not found or not clickable")

    # ══════════════════════════════════════════════════════════════
    #  Form fill
    # ══════════════════════════════════════════════════════════════

    def fill_form(self, data):
        log.info("Filling Directors form fields...")

        # 1. Party Reference dropdown
        if data.get("party_reference") is not None:
            self._select_mat_option_by_label(
                "Party Reference", str(data["party_reference"])
            )

        # 2. Prefix — convert FK int to label
        prefix_val = data.get("prefix")
        if prefix_val is not None and prefix_val != "":
            label = PREFIX_NAMES.get(
                int(prefix_val) if not isinstance(prefix_val, int) else prefix_val,
                str(prefix_val),
            )
            self._select_mat_option_by_label("Prefix", label)

        # 3. Director Name — ERP label: "Name of Director/KMP"
        if data.get("director_name"):
            self._fill_input_by_label_js("Name of Director/KMP", data["director_name"])

        # 4. Designation — pick first available option (universal across tenants)
        desig_val = data.get("designation")
        if desig_val is not None and desig_val != "":
            self._select_first_available_mat_option("Designation")

        # 5. PAN/Other
        if data.get("pan_no"):
            self._fill_input_by_label_js("PAN/Other", data["pan_no"])

        # 6. Residential Address
        if data.get("residential_address"):
            self._fill_input_by_label_js("Residential Address", data["residential_address"])

        # 7. Phone Number
        if data.get("phone_number") is not None:
            self._fill_input_by_label_js("Phone Number", str(data["phone_number"]))

        # 8. Date of Appointment
        if data.get("date_of_appointment"):
            self._fill_date_input("Date of Appointment", data["date_of_appointment"])

        # 9. Date of Cessation
        if data.get("date_of_cessation"):
            self._fill_date_input("Date of Cessation", data["date_of_cessation"])

        # 10. Number and Class of Shares — trailing space intentional
        if data.get("no_class_shares_held"):
            self._fill_input_by_label_js(
                "Number and Class of Shares ", data["no_class_shares_held"]
            )

        # 11. Details of Other Directorships
        if data.get("details_of_other_directorships"):
            self._fill_input_by_label_js(
                "Details of Other Directorships", data["details_of_other_directorships"]
            )

        # 12. Percentage of Shares
        if data.get("percentage_of_shares") is not None:
            self._fill_input_by_label_js(
                "Percentage of Shares", str(data["percentage_of_shares"])
            )

        # 13. Age
        if data.get("age") is not None:
            self._fill_input_by_label_js("Age", str(data["age"]))

        # 14. Qualification — pick first available option (universal across tenants)
        qual_val = data.get("qualification")
        if qual_val is not None and qual_val != "":
            self._select_first_available_mat_option("Qualification")

        # 15. Experience in Years
        if data.get("experience_in_years") is not None:
            self._fill_input_by_label_js(
                "Experience in Years", str(data["experience_in_years"])
            )

        # 16. KYC Details child grid
        kyc_rows = data.get("kyc_details")
        if kyc_rows and isinstance(kyc_rows, list) and len(kyc_rows) > 0:
            self.fill_kyc_details(kyc_rows)

        self._force_close_panels()
        log.info("Directors form filled")

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
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-container")
                )
            )
            self.wait_seconds(1)
        except (TimeoutException, InvalidSessionIdException):
            inline_errors = self.get_mat_error_text()
            if inline_errors:
                error_summary = "; ".join(inline_errors[:5])
                log.warning(
                    f"No SweetAlert, but inline validation errors found: {error_summary}"
                )
                return f"VALIDATION_ERRORS: {error_summary}"
            log.warning("No SweetAlert2 alert appeared (timeout or session died)")
            return ""

        try:
            title = self.driver.find_element(
                By.CSS_SELECTOR, "#swal2-title"
            ).text.strip()
        except Exception:
            try:
                container = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-container"
                )
                title = container.text.strip()
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
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-container")
                )
            )
            try:
                title = self.driver.find_element(
                    By.CSS_SELECTOR, "#swal2-title"
                ).text.strip()
            except Exception:
                try:
                    container = self.driver.find_element(
                        By.CSS_SELECTOR, ".swal2-container"
                    )
                    title = container.text.strip()
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
        for attempt in range(3):
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

    def _fill_input_by_name_js(self, field_name, value, scope=None):
        if not value:
            return
        log.info(f"JS fill input: name='{field_name}', value='{str(value)[:50]}...'")
        try:
            result = self.driver.execute_script("""
                var fieldName = arguments[0];
                var val = arguments[1];
                var popup = document.querySelector('.big-model, .edit_pop_up, mat-dialog-container');
                if (!popup) return false;

                var inputs = popup.querySelectorAll('input[name="' + fieldName + '"]');
                if (inputs.length === 0) {
                    var allInputs = popup.querySelectorAll('input[name]');
                    for (var i = 0; i < allInputs.length; i++) {
                        var name = allInputs[i].getAttribute('name') || '';
                        if (name.indexOf(fieldName) === 0 && allInputs[i].offsetParent !== null) {
                            inputs = [allInputs[i]];
                            break;
                        }
                    }
                }

                if (inputs.length === 0) return false;

                var targetInput = null;
                for (var j = 0; j < inputs.length; j++) {
                    if (inputs[j].offsetParent !== null) {
                        targetInput = inputs[j];
                        break;
                    }
                }
                if (!targetInput && inputs.length > 0) {
                    targetInput = inputs[0];
                }
                if (!targetInput) return false;

                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;

                nativeInputValueSetter.call(targetInput, val);
                targetInput.dispatchEvent(new Event('input', {bubbles: true}));
                targetInput.dispatchEvent(new Event('change', {bubbles: true}));

                return true;
            """, field_name, str(value))

            if result:
                log.info(f"JS fill succeeded: '{field_name}'")
            else:
                log.warning(f"JS fill failed: input '{field_name}' not found")
        except Exception as e:
            log.warning(f"JS fill input failed: {e}")

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
                        var txt = labels[i].textContent.trim();
                        if (txt.indexOf(labelText) !== -1) {
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
                if (popup) {
                    targetInput = tryFind(popup);
                }

                if (!targetInput) {
                    targetInput = tryFind(document);
                }

                if (!targetInput) {
                    return {success: false, error: 'Input not found for: ' + labelText};
                }

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
                log.info(f"Falling back to name-based fill for '{label_text}'")
                self._fill_input_by_name_js(label_text, value)
        except Exception as e:
            log.warning(f"Label-based input fill exception for '{label_text}': {e}")

            try:
                self._fill_input_by_name_js(label_text, value)
            except Exception:
                pass

    def _select_mat_option_by_label(self, label_text, option_text, scope=None):
        log.info(f"Label-based select: label='{label_text}', option='{option_text}'")
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
                log.warning(f"Label-based dropdown not found: '{label_text}'")
                return

            self.driver.execute_script("""
                arguments[0].scrollIntoView({block:'center'});
                arguments[0].click();
            """, select_el)
            self.wait_seconds(0.8)

            # Scroll through virtual listbox to find option across all rendered batches
            low_target = option_text.lower()
            matched = False
            seen_texts = set()
            for _scroll_pass in range(20):
                options = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[role='listbox'] mat-option"
                )
                new_texts = set()
                for opt in options:
                    try:
                        opt_text = opt.text.strip()
                        new_texts.add(opt_text)
                        low_opt = opt_text.lower()
                        match = (
                            low_opt == low_target
                            or low_opt.startswith(low_target + " ")
                            or low_opt.startswith(low_target + ",")
                            or f" {low_target} " in f" {low_opt} "
                        )
                        if match and opt.is_displayed():
                            self.driver.execute_script("arguments[0].click();", opt)
                            self.wait_seconds(0.5)
                            try:
                                self.driver.execute_script("""
                                    arguments[0].dispatchEvent(
                                        new Event('change', {bubbles: true})
                                    );
                                """, select_el)
                            except Exception:
                                pass
                            self._close_select_panel()
                            log.info(
                                f"Label-based select succeeded: "
                                f"'{label_text}' -> '{option_text}' (matched: '{opt_text}')"
                            )
                            matched = True
                            break
                    except Exception:
                        continue
                if matched:
                    break
                # No new options rendered — stop scrolling
                if new_texts and new_texts.issubset(seen_texts):
                    break
                seen_texts.update(new_texts)
                # Scroll the listbox panel down to render next batch
                try:
                    self.driver.execute_script("""
                        var lb = document.querySelector('div[role="listbox"]');
                        if (lb) lb.scrollTop += 300;
                    """)
                    self.wait_seconds(0.2)
                except Exception:
                    break

            if not matched:
                self._close_select_panel()
                log.warning(f"Option '{option_text}' not found for label '{label_text}' after full scroll")
        except InvalidSessionIdException:
            raise
        except Exception as e:
            log.warning(f"Label-based dropdown selection failed: {e}")
            self._close_select_panel()

    def _select_first_available_mat_option(self, label_text):
        """Open a mat-select by its label and pick the first available option.
        Universal — works on any tenant regardless of what options are configured."""
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

            self.driver.execute_script("""
                arguments[0].scrollIntoView({block:'center'});
                arguments[0].click();
            """, select_el)
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
            log.warning(f"No options found in dropdown for '{label_text}'")
        except InvalidSessionIdException:
            raise
        except Exception as e:
            log.warning(f"_select_first_available_mat_option failed for '{label_text}': {e}")
            self._close_select_panel()

    # ══════════════════════════════════════════════════════════════
    #  Date input helpers
    # ══════════════════════════════════════════════════════════════

    def _iso_to_dmy(self, iso_str):
        if not iso_str:
            return ""
        try:
            date_part = iso_str.split("T")[0]
            parts = date_part.split("-")
            if len(parts) == 3:
                return f"{parts[2]}/{parts[1]}/{parts[0]}"
        except Exception:
            pass
        return ""

    def _fill_date_input(self, label_text, iso_date_str):
        if not iso_date_str:
            return
        dmy = self._iso_to_dmy(iso_date_str)
        if not dmy:
            log.warning(f"Could not convert date: {iso_date_str}")
            return

        log.info(f"Filling date input: label='{label_text}', value='{dmy}'")
        try:
            result = self.driver.execute_script("""
                var labelText = arguments[0];
                var dateValue = arguments[1];

                var popup = document.querySelector('.big-model, .edit_pop_up, mat-dialog-container');
                if (!popup) return {success: false, error: 'No popup found'};

                var labels = popup.querySelectorAll('mat-label');
                var dateInput = null;
                for (var i = 0; i < labels.length; i++) {
                    if (labels[i].textContent.trim().includes(labelText)) {
                        var field = labels[i].closest(
                            'mat-form-field, .mat-mdc-form-field'
                        );
                        if (field) {
                            var inputs = field.querySelectorAll('input');
                            for (var j = 0; j < inputs.length; j++) {
                                var style = inputs[j].getAttribute('style') || '';
                                if (inputs[j].offsetParent !== null
                                    && style.indexOf('display: none') === -1) {
                                    dateInput = inputs[j];
                                    break;
                                }
                            }
                            if (dateInput) break;
                        }
                    }
                }

                if (!dateInput) {
                    return {success: false, error: 'Date input not found for: ' + labelText};
                }

                dateInput.scrollIntoView({block: 'center'});
                dateInput.focus();

                var nativeSet = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;

                nativeSet.call(dateInput, '');
                dateInput.dispatchEvent(new Event('input', {bubbles: true}));
                dateInput.dispatchEvent(new Event('change', {bubbles: true}));

                nativeSet.call(dateInput, dateValue);
                dateInput.dispatchEvent(new Event('input', {bubbles: true}));
                dateInput.dispatchEvent(new Event('change', {bubbles: true}));
                dateInput.dispatchEvent(new Event('blur', {bubbles: true}));

                return {success: true};
            """, label_text, dmy)

            if result and result.get("success"):
                log.info(f"Date input '{label_text}' filled: {dmy}")
            else:
                error = result.get("error", "Unknown") if result else "JS returned null"
                log.warning(f"Date input '{label_text}' fill failed: {error}")
        except Exception as e:
            log.warning(f"Date input exception for '{label_text}': {e}")

    # ══════════════════════════════════════════════════════════════
    #  KYC Details helpers
    # ══════════════════════════════════════════════════════════════

    def add_kyc_row(self):
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//app-dynamic-details//button[.//mat-icon[text()='add']]",
            )
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(0.5)
                log.info("KYC Add Row clicked")
        except Exception as e:
            log.warning(f"KYC Add Row failed: {e}")

    def fill_kyc_details(self, rows):
        if not rows:
            return
        log.info(f"Filling {len(rows)} KYC row(s)...")

        for i, row in enumerate(rows):
            if i > 0:
                self.add_kyc_row()
            self.wait_seconds(0.5)

            kyc_doc_id = row.get("kyc_doc_id")
            kyc_account_no = row.get("kyc_account_no")

            if kyc_doc_id is not None:
                doc_label = KYC_DOC_NAMES.get(kyc_doc_id, str(kyc_doc_id))
                log.info(f"  Row {i}: selecting KYC doc '{doc_label}'")
                try:
                    self.driver.execute_script("""
                        var docLabel = arguments[0];
                        var lastRow = document.querySelector(
                            'app-dynamic-details tbody tr:last-child'
                        );
                        if (!lastRow) return false;

                        var select = lastRow.querySelector('mat-select');
                        if (!select) return false;

                        select.scrollIntoView({block: 'center'});
                        select.click();

                        var checkExist = setInterval(function() {
                            var options = document.querySelectorAll(
                                'div[role="listbox"] mat-option'
                            );
                            for (var i = 0; i < options.length; i++) {
                                if (options[i].textContent.trim() === docLabel
                                    && options[i].offsetParent !== null) {
                                    options[i].click();
                                    clearInterval(checkExist);
                                    return;
                                }
                            }
                        }, 200);

                        setTimeout(function() { clearInterval(checkExist); }, 3000);
                        return true;
                    """, doc_label)
                    self.wait_seconds(1)
                    self._force_close_panels()
                    self.wait_seconds(0.3)
                except Exception as e:
                    log.warning(f"  Row {i}: KYC doc selection failed: {e}")
                    self._close_select_panel()

            if kyc_account_no:
                log.info(f"  Row {i}: typing KYC number '{kyc_account_no}'")
                try:
                    self.driver.execute_script("""
                        var accountNo = arguments[0];
                        var lastRow = document.querySelector(
                            'app-dynamic-details tbody tr:last-child'
                        );
                        if (!lastRow) return false;

                        var input = lastRow.querySelector(
                            'input[name="KYC Number"]'
                        );
                        if (!input) return false;

                        input.scrollIntoView({block: 'center'});

                        var nativeSet = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value'
                        ).set;

                        nativeSet.call(input, '');
                        input.dispatchEvent(new Event('input', {bubbles: true}));
                        input.dispatchEvent(new Event('change', {bubbles: true}));

                        nativeSet.call(input, accountNo);
                        input.dispatchEvent(new Event('input', {bubbles: true}));
                        input.dispatchEvent(new Event('change', {bubbles: true}));
                        input.dispatchEvent(new Event('blur', {bubbles: true}));

                        return true;
                    """, kyc_account_no)
                    self.wait_seconds(0.3)
                except Exception as e:
                    log.warning(f"  Row {i}: KYC number fill failed: {e}")

        log.info("KYC Details filled")

    def remove_kyc_row(self, index=0):
        log.info(f"Removing KYC row {index}...")
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "app-dynamic-details tbody tr"
            )
            if index < len(rows):
                remove_btn = rows[index].find_element(
                    By.XPATH, ".//button[.//mat-icon[text()='remove']]"
                )
                if remove_btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", remove_btn)
                    self.wait_seconds(0.5)
                    log.info(f"KYC row {index} removed")
            else:
                log.warning(f"KYC row {index} not found (only {len(rows)} rows)")
        except Exception as e:
            log.warning(f"Failed to remove KYC row {index}: {e}")

    # ══════════════════════════════════════════════════════════════
    #  Overlay helpers
    # ══════════════════════════════════════════════════════════════

    def _force_close_panels(self):
        try:
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
        except InvalidSessionIdException:
            log.warning("Session dead in _force_close_panels()")
            raise
        except Exception as e:
            log.warning(f"_force_close_panels() failed: {e}")

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
        except InvalidSessionIdException:
            raise
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
                    By.CSS_SELECTOR,
                    "div.big-model input, mat-dialog-container input",
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

    # ══════════════════════════════════════════════════════════════
    #  Force close form popup
    # ══════════════════════════════════════════════════════════════

    def force_close_form_popup(self):
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]"
                "//button[contains(.,'Cancel')]",
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
                "//div[contains(@class,'popup-header')]"
                "//button[.//mat-icon[text()='close']]",
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
            backdrops = self.driver.find_elements(
                By.CSS_SELECTOR, ".cdk-overlay-backdrop.cdk-overlay-dark-backdrop"
            )
            for bd in backdrops:
                try:
                    if bd.is_displayed():
                        bd.click()
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
    #  Validation error helpers
    # ══════════════════════════════════════════════════════════════

    def get_mat_error_text(self):
        errors = []
        try:
            error_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
            )
            for el in error_elements:
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

    def search_director(self, text):
        log.info(f"Searching for: {text}")
        try:
            toggle = self.find_elements(self.SEARCH_TOGGLE)
            if toggle:
                self.driver.execute_script("arguments[0].click();", toggle[0])
                self.wait_seconds(0.5)

            inp = self.find_elements(self.SEARCH_INPUT)
            if inp:
                inp[0].clear()
                inp[0].send_keys(text)
                inp[0].send_keys(Keys.ENTER)
                self.wait_seconds(2)
                log.info(f"Search executed for: {text}")
            else:
                log.warning("Search input not found — skipping search")
        except Exception as e:
            log.warning(f"Search failed: {e}")

    def is_director_in_table(self, search_text):
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
            btn = self.driver.find_element(
                By.XPATH,
                "//button[contains(@class,'erp-menu-item')][.//span[contains(.,'Edit')]]",
            )
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
            btn = self.driver.find_element(
                By.XPATH,
                "//button[contains(@class,'erp-menu-item')][.//span[contains(.,'View')]]",
            )
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
