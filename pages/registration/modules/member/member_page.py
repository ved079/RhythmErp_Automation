"""
member_page.py
--------------
Page Object Model for RhythmERP Member screen.

The Member screen is a flat popup form — NO mat-horizontal-stepper.
All fields fill top-to-bottom in one fill_form() call.
KYC Details is a child grid inside an app-dynamic-details component.

Location: Registration > Member
URL:      /#/dynamic-screens/Member/Member
"""

import os
import sys
import time
import random

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
from pages.registration.modules.member.data.member_data import (
    PREFIX_NAMES,
    KYC_DOC_NAMES,
)


class MemberPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Member/Member"

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    SEARCH_INPUT = ("css", ".erp-search-wrapper input, input#erpSearchInput")
    SEARCH_SUBMIT = ("css", "button.search-btn")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    MORE_BUTTON = ("css", "button[mattooltip='More']")

    # ==============================================================
    #  LOCATORS — Popup structure
    # ==============================================================
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

    # ==============================================================
    #  LOCATORS — Top-level fields
    # ==============================================================
    COPY_FROM_PARTY_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(.,'Copy From Existing Party')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    PARTY_REFERENCE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Party Reference')]/ancestor::mat-form-field//mat-select",
    )
    PREFIX_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Prefix')]/ancestor::mat-form-field//mat-select",
    )
    MEMBER_NAME_INPUT = ("css", "input[name='Member Name']")
    MEMBER_ADDRESS_INPUT = ("css", "input[name='Member Address']")
    PAN_OTHER_INPUT = ("css", "input[name='PAN/Other']")
    FOLIO_NUMBER_INPUT = ("css", "input[name='Folio Number']")
    NO_CLASS_SHARES_INPUT = (
        "css",
        "input[name='Number and Class of Shares ']",
    )
    DISTINCTIVE_NUMBER_INPUT = ("css", "input[name='Distintive Number']")
    AMOUNT_PAID_INPUT = ("css", "input[name='Amount Paid on Shares']")
    PERCENTAGE_SHARES_INPUT = ("css", "input[name='Percentage of Shares']")
    PHONE_INPUT = ("css", "input[name='Phone Number']")
    IS_MEMBER_DIRECTOR_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(.,'Is Member Director')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    REGISTRATION_DATE_INPUT = (
        "xpath",
        "(//mat-label[contains(.,'Registration Date')]"
        "/ancestor::mat-form-field//input[not(@style)])[1]",
    )
    DATE_OF_ALLOTMENT_INPUT = (
        "xpath",
        "(//mat-label[contains(.,'Date of Allotment')]"
        "/ancestor::mat-form-field//input[not(@style)])[1]",
    )

    # ==============================================================
    #  LOCATORS — KYC Details child grid
    # ==============================================================
    KYC_ADD_ROW_BUTTON = (
        "xpath",
        "//app-dynamic-details//button[.//mat-icon[text()='add']]",
    )
    KYC_DOC_SELECT = (
        "xpath",
        "//app-dynamic-details//mat-label[contains(.,'KYC Document')]"
        "/ancestor::mat-form-field//mat-select",
    )
    KYC_NUMBER_INPUT = ("css", "input[name='KYC Number']")

    # ==============================================================
    #  LOCATORS — SweetAlert2
    # ==============================================================
    SWAL_TITLE = ("css", "#swal2-title")
    SWAL_CONFIRM = ("css", ".swal2-confirm")

    # ==============================================================
    #  LOCATORS — Validation errors
    # ==============================================================
    MAT_ERROR = ("css", "mat-error, .mat-mdc-form-field-error")

    # ==============================================================
    #  LOCATORS — Row action menu
    # ==============================================================
    ROW_ACTION_TRIGGER = ("css", "button.mat-mdc-menu-trigger.erp-row-trigger")
    MENU_VIEW = (
        "xpath",
        "//button[contains(@class,'erp-menu-item')][.//span[contains(.,'View')]]",
    )
    MENU_EDIT = (
        "xpath",
        "//button[contains(@class,'erp-menu-item')][.//span[contains(.,'Edit')]]",
    )

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS."""
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
            log.warning("Session is dead in _force_close_panels() — cannot clean up overlays")
            raise
        except Exception as e:
            log.warning(f"_force_close_panels() failed: {e}")

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
                        self.wait_seconds(0.3)
                        return
                except InvalidSessionIdException:
                    log.warning("Session dead while clicking backdrop in _close_select_panel()")
                    raise
                except Exception:
                    pass
        except InvalidSessionIdException:
            log.warning("Session dead in _close_select_panel() — re-raising")
            raise
        except Exception:
            pass

        try:
            self._force_close_panels()
        except InvalidSessionIdException:
            raise
        except Exception:
            pass

    # ==============================================================
    #  Form popup detection
    # ==============================================================

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
        """Check if the Add form popup is open."""
        return self._is_form_popup_open()

    def _wait_for_form_content(self, timeout=5):
        """Wait for form content to render inside the popup."""
        import time as _time

        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.big-model input, "
                    "mat-dialog-container input",
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

    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Member listing page."""
        log.info("Navigating to Member page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the Member page is fully loaded."""
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table#excel-table")
                )
            )
            log.info("Member table loaded")
        except TimeoutException:
            log.warning("Member table not found, page may be empty")

    # ==============================================================
    #  Toolbar actions
    # ==============================================================

    def open_add_form(self):
        """Click the ADD (+) button to open the create form."""
        log.info("Clicking ADD Member button...")

        # Strategy 1: button.erp-add-btn
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
                            log.info("ADD form opened via mini-fab icon")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        raise Exception("ADD button not found or not clickable")

    # ==============================================================
    #  JS fill input helper
    # ==============================================================

    def _fill_input_by_name_js(self, field_name, value, scope=None):
        """Fill a text input using JS nativeInputValueSetter + dispatchEvent.

        Uses Object.getOwnPropertyDescriptor to set the value, then fires
        'input' and 'change' events with bubbles: true so Angular's
        reactive form model detects the change.

        Args:
            field_name: HTML name attribute of the input.
            value: Value to set.
            scope: Ignored for Member (flat form, no stepper panels).
        """
        if not value:
            return
        log.info(f"JS fill input: name='{field_name}', value='{str(value)[:50]}...'")
        try:
            result = self.driver.execute_script("""
                var fieldName = arguments[0];
                var val = arguments[1];
                var popup = document.querySelector('.big-model, mat-dialog-container');
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

    # ==============================================================
    #  Dropdown selection helpers
    # ==============================================================

    def _select_mat_option_by_label(self, label_text, option_text, scope=None):
        """Select a mat-select dropdown option by its mat-label text.

        Finds the dropdown by searching for a mat-label containing label_text,
        then clicks the associated mat-select and selects option_text.

        Args:
            label_text: Text to search for in mat-label.
            option_text: Option text to select.
            scope: Ignored for Member (flat form).
        """
        log.info(f"Label-based select: label='{label_text}', option='{option_text}'")
        try:
            select_el = self.driver.execute_script("""
                var labelText = arguments[0];
                var popup = document.querySelector('.big-model, mat-dialog-container');
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

            options = self.driver.find_elements(
                By.CSS_SELECTOR, "div[role='listbox'] mat-option"
            )
            for opt in options:
                try:
                    if opt.text.strip() == option_text and opt.is_displayed():
                        self.driver.execute_script("arguments[0].click();", opt)
                        self.wait_seconds(0.5)
                        self.driver.execute_script("""
                            arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                        """, select_el)
                        self._close_select_panel()
                        log.info(
                            f"Label-based select succeeded: "
                            f"'{label_text}' -> '{option_text}'"
                        )
                        return
                except Exception:
                    continue

            self._close_select_panel()
            log.warning(f"Option '{option_text}' not found for label '{label_text}'")
        except Exception as e:
            log.warning(f"Label-based dropdown selection failed: {e}")
            self._close_select_panel()

    def _dispatch_change_event(self, dropdown_locator):
        """BUG-001 WORKAROUND: Re-find the mat-select trigger and fire a
        'change' event with bubbles: true so Angular's reactive form
        model picks up the JS-clicked selection.
        """
        try:
            trigger = self.find_clickable_element(dropdown_locator, timeout=3)
            if trigger:
                self.driver.execute_script("""
                    var el = arguments[0];
                    var trigger = el.tagName === 'MAT-SELECT' ? el : el.querySelector('mat-select');
                    if (trigger) {
                        trigger.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                """, trigger)
        except Exception as e:
            log.debug(f"BUG-001 dispatchEvent failed (non-critical): {e}")

    # ==============================================================
    #  Toggle switch helpers
    # ==============================================================

    def _toggle_switch(self, locator, desired_state):
        """Set a toggle switch to the desired state (True=ON, False=OFF).

        Uses multi-strategy _is_toggle_on() for reliable state detection.
        """
        try:
            toggle = self.find_visible_element(locator, timeout=5)
            current_state = self._is_toggle_on(toggle)

            if current_state != desired_state:
                self.driver.execute_script("arguments[0].click();", toggle)
                self.wait_seconds(0.5)
                new_state = self._is_toggle_on(toggle)
                if new_state != desired_state:
                    try:
                        switch = toggle.find_element(
                            By.CSS_SELECTOR,
                            ".switch, .slide-toggle, .mat-slide-toggle-bar",
                        )
                        self.driver.execute_script("arguments[0].click();", switch)
                        self.wait_seconds(0.3)
                    except Exception:
                        pass
                log.info(f"Toggle set to {'ON' if desired_state else 'OFF'}")
        except Exception as e:
            log.warning(f"Toggle switch failed: {e}")

    def _is_toggle_on(self, toggle_element):
        """Multi-strategy check if a toggle switch is currently ON."""
        try:
            try:
                checkbox = toggle_element.find_element(
                    By.CSS_SELECTOR, "input[type='checkbox']"
                )
                if checkbox.is_selected():
                    return True
            except Exception:
                pass

            classes = toggle_element.get_attribute("class") or ""
            if "active" in classes.split():
                return True

            try:
                slide_toggle = toggle_element.find_element(
                    By.CSS_SELECTOR, "mat-slide-toggle, .mat-slide-toggle"
                )
                slide_classes = slide_toggle.get_attribute("class") or ""
                if (
                    "mat-checked" in slide_classes
                    or "mat-slide-toggle-checked" in slide_classes
                ):
                    return True
            except Exception:
                pass

            try:
                aria = toggle_element.get_attribute("aria-checked")
                if aria == "true":
                    return True
            except Exception:
                pass

            try:
                parent = toggle_element.find_element(By.XPATH, "..")
                parent_classes = parent.get_attribute("class") or ""
                if "checked" in parent_classes.split():
                    return True
            except Exception:
                pass

        except Exception:
            pass
        return False

    # ==============================================================
    #  Date input helpers
    # ==============================================================

    def _iso_to_dmy(self, iso_str):
        """Convert ISO date string to DD/MM/YYYY format.

        Args:
            iso_str: ISO date string like "2025-06-15T18:30:00Z"
                     or "2025-06-15".

        Returns:
            str: Date in DD/MM/YYYY format, or empty string on failure.
        """
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
        """Fill a date input via JS nativeInputValueSetter.

        Finds the visible input by label text, converts ISO to DD/MM/YYYY,
        then sets value via JS with input/change/blur events.

        Args:
            label_text: The mat-label text (e.g., "Registration Date").
            iso_date_str: ISO date string to convert and type.
        """
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

                var popup = document.querySelector('.big-model, mat-dialog-container');
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

    # ==============================================================
    #  KYC Details helpers
    # ==============================================================

    def add_kyc_row(self):
        """Click the KYC Add Row button."""
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
        """Fill KYC Details grid rows.

        Each row is a dict with keys:
            kyc_doc_id: int (65=PAN, 66=AADHAR)
            kyc_account_no: str

        After clicking Add Row, scopes to the last <tr> in the grid.

        Args:
            rows: List of KYC row dicts.
        """
        if not rows:
            return
        log.info(f"Filling {len(rows)} KYC row(s)...")

        for i, row in enumerate(rows):
            if i > 0:
                self.add_kyc_row()
            self.wait_seconds(0.5)

            kyc_doc_id = row.get("kyc_doc_id")
            kyc_account_no = row.get("kyc_account_no")

            # Scope to last <tr> in app-dynamic-details tbody
            if kyc_doc_id is not None:
                doc_label = KYC_DOC_NAMES.get(kyc_doc_id, str(kyc_doc_id))
                log.info(f"  Row {i}: selecting KYC doc '{doc_label}'")
                try:
                    self.driver.execute_script("""
                        var docLabel = arguments[0];
                        // Find the last tr in app-dynamic-details tbody
                        var lastRow = document.querySelector(
                            'app-dynamic-details tbody tr:last-child'
                        );
                        if (!lastRow) return false;

                        // Find mat-select in that row
                        var select = lastRow.querySelector('mat-select');
                        if (!select) return false;

                        select.scrollIntoView({block: 'center'});
                        select.click();

                        // Wait for overlay, then find and click the option
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

                        var input = lastRow.querySelector('input[name="KYC Number"]');
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

    # ==============================================================
    #  fill_form — top-to-bottom field fill
    # ==============================================================

    def fill_form(self, data):
        """Fill all top-level Member form fields in order.

        Skip any field if its value is None or empty string.
        Convert integer FK IDs to labels for dropdown selection.

        Data dict keys:
            copy_from_party (bool/None)
            party_reference (str/None)
            prefix (int FK like 1896)
            member_name (str)
            member_address (str)
            pan_no (str)
            folio_number (str)
            registration_date (ISO str)
            no_class_shares_held (str)
            distinctive_number (int or str)
            amount_paid_on_shares (int)
            date_of_allotment (ISO str)
            percentage_of_shares (int)
            phone_number (int)
            is_member_director (bool/None)
            kyc_details (list of dict or None)
        """
        log.info("Filling Member form fields...")

        # 1. Copy From Existing Party toggle
        if data.get("copy_from_party") is True:
            self._toggle_switch(self.COPY_FROM_PARTY_TOGGLE, True)
            self.wait_seconds(0.5)

        # 2. Party Reference dropdown
        if data.get("party_reference") is not None:
            self._select_mat_option_by_label(
                "Party Reference", str(data["party_reference"])
            )

        # 3. Prefix — convert FK int to label
        prefix_val = data.get("prefix")
        if prefix_val is not None and prefix_val != "":
            label = PREFIX_NAMES.get(
                int(prefix_val) if not isinstance(prefix_val, int) else prefix_val,
                str(prefix_val),
            )
            self._select_mat_option_by_label("Prefix", label)

        # 4. Member Name
        if data.get("member_name"):
            self._fill_input_by_name_js("Member Name", data["member_name"])

        # 5. Member Address
        if data.get("member_address"):
            self._fill_input_by_name_js("Member Address", data["member_address"])

        # 6. PAN/Other
        if data.get("pan_no"):
            self._fill_input_by_name_js("PAN/Other", data["pan_no"])

        # 7. Folio Number
        if data.get("folio_number"):
            self._fill_input_by_name_js("Folio Number", data["folio_number"])

        # 8. Registration Date
        if data.get("registration_date"):
            self._fill_date_input("Registration Date", data["registration_date"])

        # 9. Number and Class of Shares — trailing space intentional
        if data.get("no_class_shares_held"):
            self._fill_input_by_name_js(
                "Number and Class of Shares ", data["no_class_shares_held"]
            )

        # 10. Distinctive Number — ERP typo: "Distintive"
        if data.get("distinctive_number") is not None:
            self._fill_input_by_name_js(
                "Distintive Number", str(data["distinctive_number"])
            )

        # 11. Amount Paid on Shares
        if data.get("amount_paid_on_shares") is not None:
            self._fill_input_by_name_js(
                "Amount Paid on Shares", str(data["amount_paid_on_shares"])
            )

        # 12. Date of Allotment
        if data.get("date_of_allotment"):
            self._fill_date_input("Date of Allotment", data["date_of_allotment"])

        # 13. Percentage of Shares
        if data.get("percentage_of_shares") is not None:
            self._fill_input_by_name_js(
                "Percentage of Shares", str(data["percentage_of_shares"])
            )

        # 14. Phone Number
        if data.get("phone_number") is not None:
            self._fill_input_by_name_js("Phone Number", str(data["phone_number"]))

        # 15. Is Member Director toggle
        if data.get("is_member_director") is not None:
            self._toggle_switch(
                self.IS_MEMBER_DIRECTOR_TOGGLE, bool(data["is_member_director"])
            )

        # 16. KYC Details child grid
        kyc_rows = data.get("kyc_details")
        if kyc_rows and isinstance(kyc_rows, list) and len(kyc_rows) > 0:
            self.fill_kyc_details(kyc_rows)

        # Close any open overlays before submit
        self._force_close_panels()
        log.info("Member form filled")

    # ==============================================================
    #  Submit / Cancel / Close
    # ==============================================================

    def submit_form(self):
        """Click Submit button (Create mode)."""
        log.info("Clicking Submit...")
        self._force_close_panels()
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]"
                "//button[contains(.,'Submit') or contains(.,'Update')]",
            )
            if btn.is_displayed():
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1)
                return True
        except Exception:
            pass

        try:
            btn = self.find_clickable_element(self.SUBMIT_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1)
                return True
        except Exception:
            pass
        return False

    def cancel(self):
        """Click Cancel button."""
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]"
                "//button[contains(.,'Cancel')]",
            )
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
                return True
        except Exception:
            pass
        try:
            btn = self.find_clickable_element(self.CANCEL_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
                return True
        except Exception:
            pass
        return False

    def force_close_form_popup(self):
        """Force close any open popup via 4-step cascade:
        1. Cancel button
        2. Close(X) button
        3. Backdrop click
        4. Nuclear JS removal
        """
        # Step 1: Cancel
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

        # Step 2: Close(X) button
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

        # Step 3: Backdrop click
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

        # Step 4: Nuclear JS removal
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

    # ==============================================================
    #  SweetAlert2 handling
    # ==============================================================

    def handle_success_alert(self, timeout=15):
        """Handle SweetAlert2 success alert. Returns alert title text.

        Also checks for inline validation errors when no SweetAlert appears.
        """
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
        """Handle SweetAlert2 validation warning. Returns alert title text."""
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
        """Click the confirm button on SweetAlert2 (3-tier strategy)."""
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

    # ==============================================================
    #  Validation errors
    # ==============================================================

    def get_mat_error_text(self):
        """Get all visible mat-error texts."""
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

    # ==============================================================
    #  Table operations
    # ==============================================================

    def is_member_in_table(self, search_text):
        """Check if a member with the given text exists in the listing table.

        Scans all table cells for a case-insensitive match.

        Args:
            search_text: Text to search for in table cells.

        Returns:
            bool: True if found.
        """
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
        """Get the number of data rows in the main listing table."""
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

    def search_member(self, text):
        """Search for a member using the page-specific search locators."""
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

    # ==============================================================
    #  Row action menu
    # ==============================================================

    def open_row_menu(self, row_index=0):
        """Open the three-dot action menu for a table row.

        Args:
            row_index: 0-based index of the row.
        """
        log.info(f"Opening row action menu at index {row_index}...")
        try:
            triggers = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-mdc-menu-trigger.erp-row-trigger"
            )
            if row_index < len(triggers):
                self.driver.execute_script("arguments[0].click();", triggers[row_index])
                self.wait_seconds(1)
                return True
        except Exception as e:
            log.warning(f"Open row menu failed: {e}")
        return False

    def click_view(self):
        """Click the View option in the row action menu."""
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//button[contains(@class,'erp-menu-item')]"
                "[.//span[contains(.,'View')]]",
            )
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
                return True
        except Exception as e:
            log.warning(f"Click View failed: {e}")
        return False

    def click_edit(self):
        """Click the Edit option in the row action menu."""
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//button[contains(@class,'erp-menu-item')]"
                "[.//span[contains(.,'Edit')]]",
            )
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
                return True
        except Exception as e:
            log.warning(f"Click Edit failed: {e}")
        return False
