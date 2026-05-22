"""
agent_page.py
-------------
Page Object Model for RhythmERP Agent screen.

Location: Registration > Agent
URL:      /#/dynamic-screens/Agent

FORM LAYOUT (multi-step STEPPER popup):

  Step 1 — Universal:
    - Agent Name             (text input,   required)
    - Phone Number           (text input,   required)
    - Email                  (text input,   required)

  Step 2 — Address Details (click "Next" to advance):
    - Add Row button         (to add address rows)
    For EACH row:
    - Address Type           (mat-select,   required, searchable)
    - Country                (mat-select,   required, searchable)
    - State                  (mat-select,   required, searchable, dependent on Country)
    - District               (mat-select,   required, searchable, dependent on State)
    - Taluka                 (mat-select,   optional, searchable, dependent on District)
    - Village                (mat-select,   optional, searchable)
    - Address                (text input,   required)
    - Pin Code               (text input,   required)
    - GST                    (text input,   optional)

  Step 3 — Payment Details (click "Next"):
    - Payment Terms          (mat-select,   optional)
    - Preferred Payment Method (mat-select, optional)

  Step 4 — Bank Details (click "Next"):
    - Add Row button         (to add bank rows)
    For EACH row:
    - Bank Name              (text input,   required)
    - Branch                 (text input,   optional)
    - IFSC Code              (text input,   required)
    - Account Type           (mat-select,   required, searchable)
    - Account Holder Name    (text input,   required)
    - Account Number         (text input,   required)
    - Bank Proof             (file upload,  required)
    - Attachment             (file upload,  optional)

  Step 5 — Submit (click "Submit" on the last step or footer)

KEY RULES:
  - Multi-step STEPPER form — must click "Next" / "Back" to navigate steps
  - Angular Material UI — use execute_script for reading/writing input values
  - Address and Bank Details are repeatable rows (add multiple)
  - State depends on Country, District depends on State (cascading dropdowns)
  - SweetAlert2 for success/validation popups
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
)

from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT


class AgentPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Agent"

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    MORE_BUTTON = ("css", "button[mattooltip='More']")

    # ==============================================================
    #  LOCATORS — Search bar
    # ==============================================================
    SEARCH_INPUT = ("css", ".erp-search-wrapper input, input#erpSearchInput")
    SEARCH_SUBMIT = ("css", "button.search-btn")

    # ==============================================================
    #  LOCATORS — Table (main listing)
    # ==============================================================
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody td.no-data, "
        "table#excel-table tbody tr.mat-mdc-no-data-row",
    )

    # ==============================================================
    #  LOCATORS — Form popup (stepper)
    # ==============================================================
    FORM_POPUP = (
        "css",
        ".edit_pop_up.override_edit_pop_up.popup-mode",
    )
    FORM_HEADING = (
        "css",
        ".edit_pop_up h3, .edit_pop_up.override_edit_pop_up.popup-mode h3",
    )

    # ==============================================================
    #  LOCATORS — Stepper navigation
    # ==============================================================
    NEXT_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Next')]",
    )
    BACK_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Back')]",
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
    #  LOCATORS — Stepper step indicators
    # ==============================================================
    STEPPER_STEPS = ("css", "mat-horizontal-stepper mat-step-header")
    ACTIVE_STEP = ("css", "mat-horizontal-stepper mat-step-header[aria-selected='true']")

    # ==============================================================
    #  LOCATORS — SweetAlert2
    # ==============================================================
    SWAL_TITLE = ("css", "#swal2-title")
    SWAL_HTML = ("css", ".swal2-html-container")
    SWAL_CONFIRM = ("css", ".swal2-confirm")
    SWAL_CANCEL = ("css", ".swal2-cancel")
    SWAL_CONTAINER = ("css", ".swal2-container")

    # ==============================================================
    #  LOCATORS — Validation errors
    # ==============================================================
    MAT_ERROR = ("css", "mat-error, .mat-mdc-form-field-error")
    FIELD_ERROR = (
        "xpath",
        "//mat-label[contains(.,'{field_label}')]"
        "/ancestor::mat-form-field//mat-error",
    )

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
    #  LOCATORS — Pagination
    # ==============================================================
    PAGINATION_NEXT = ("css", "button[aria-label='Next page'], button.mat-mdc-paginator-navigation-next")
    PAGINATION_PREV = ("css", "button[aria-label='Previous page'], button.mat-mdc-paginator-navigation-previous")

    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Agent listing page."""
        log.info("Navigating to Agent page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the Agent page is fully loaded."""
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table#excel-table")
                )
            )
            log.info("Agent table loaded")
        except TimeoutException:
            log.warning("Agent table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn")
                )
            )
            self.wait_seconds(1)
            log.info("Agent toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the Agent listing page has loaded."""
        return self.is_displayed(self.TABLE, timeout=10)

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS.
        Keeps dialog backdrop intact so form popups stay open.
        """
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

    def _close_dropdown_panel(self):
        """Close any open dropdown overlay panel."""
        self._force_close_panels()
        self.wait_seconds(0.3)

    # ==============================================================
    #  Toolbar actions
    # ==============================================================

    def open_add_form(self):
        """Click the ADD (+) button to open the create form.
        Agent opens a multi-step stepper popup.
        """
        log.info("Clicking ADD Agent button...")
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
                    self._wait_for_form_content(timeout=5)
                    log.info("ADD form opened via erp-add-btn")
                    return
        except Exception:
            pass

        # Strategy 2: Find mini-fab button with 'add' icon
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
                            self._wait_for_form_content(timeout=5)
                            log.info("ADD form opened via mini-fab icon")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: Button with 'Add Agent' text
        try:
            btns = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in btns:
                try:
                    if "Add Agent" in btn.text and btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1.5)
                        if self._is_form_popup_open():
                            self._wait_for_form_content(timeout=5)
                            log.info("ADD form opened via text match")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 4: BasePage click_with_retry
        try:
            self.click_with_retry(self.ADD_BUTTON)
            self.wait_seconds(1.5)
            if self._is_form_popup_open():
                self._wait_for_form_content(timeout=5)
                log.info("ADD form opened via click_with_retry")
                return
        except Exception:
            pass

        raise Exception("ADD Agent button not found or not clickable")

    def _wait_for_toolbar(self):
        """Wait for the toolbar and ADD button to be present and visible."""
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
                btns = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in btns:
                    try:
                        if "Add Agent" in btn.text and btn.is_displayed():
                            return
                    except Exception:
                        continue
            except Exception:
                pass

            log.info(f"Waiting for toolbar... attempt {attempt + 1}/3")
            self.wait_seconds(2)

        log.warning("Toolbar wait exhausted, ADD button may not be ready")

    def _is_form_popup_open(self):
        """Quick check if the Agent form popup is visible."""
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up.popup-mode, "
                "mat-dialog-container, "
                "div.cdk-overlay-container div.popup-wrapper",
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
        """Wait for form content to render inside the popup."""
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".edit_pop_up.override_edit_pop_up.popup-mode input, "
                    ".edit_pop_up.override_edit_pop_up.popup-mode mat-select, "
                    ".edit_pop_up.override_edit_pop_up.popup-mode .popup-footer button",
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

        log.warning(f"Form content did not render within {timeout}s")
        return False

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
    #  Stepper navigation
    # ==============================================================

    def click_next(self):
        """Click the Next button to go to the next stepper step."""
        log.info("Clicking Next button...")
        self._force_close_panels()
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[@class='popup-footer']//button[contains(.,'Next')]"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                btn,
            )
            self.wait_seconds(1.5)
            log.info("Next clicked")
        except Exception as e:
            log.warning(f"Next button not found: {e}")

    def click_back(self):
        """Click the Back button to go to the previous stepper step."""
        log.info("Clicking Back button...")
        self._force_close_panels()
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[@class='popup-footer']//button[contains(.,'Back')]"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                btn,
            )
            self.wait_seconds(1.5)
            log.info("Back clicked")
        except Exception as e:
            log.warning(f"Back button not found: {e}")

    def get_active_step_index(self):
        """Get the current active stepper step index (0-based)."""
        js = """
            var steps = document.querySelectorAll(
                'mat-horizontal-stepper mat-step-header'
            );
            for (var i = 0; i < steps.length; i++) {
                if (steps[i].getAttribute('aria-selected') === 'true') {
                    return i;
                }
            }
            return -1;
        """
        return self.driver.execute_script(js)

    def get_active_step_label(self):
        """Get the label text of the current active stepper step."""
        js = """
            var steps = document.querySelectorAll(
                'mat-horizontal-stepper mat-step-header'
            );
            for (var i = 0; i < steps.length; i++) {
                if (steps[i].getAttribute('aria-selected') === 'true') {
                    var label = steps[i].querySelector('.mat-step-label');
                    return label ? label.textContent.trim() : '';
                }
            }
            return '';
        """
        return self.driver.execute_script(js)

    def navigate_to_step(self, step_index):
        """Navigate to a specific stepper step by clicking the step header.
        Returns True if step was changed, False otherwise.
        """
        js = f"""
            var steps = document.querySelectorAll(
                'mat-horizontal-stepper mat-step-header'
            );
            if (steps[{step_index}]) {{
                steps[{step_index}].click();
                return 'Clicked step ' + {step_index};
            }}
            return 'Step not found';
        """
        result = self.driver.execute_script(js)
        self.wait_seconds(1)
        log.info(f"Navigate to step {step_index}: {result}")
        return "Clicked" in str(result)

    # ==============================================================
    #  Form filling — JS value-setter for Angular compatibility
    # ==============================================================

    def _fill_input_by_name(self, name_attr, value, row_index=None):
        """Fill an input field by its name attribute using JS value-setter.

        Args:
            name_attr: The name attribute of the input.
            value: Value to set.
            row_index: Optional row index (0-based) for repeatable rows.
        """
        row_selector = ""
        if row_index is not None:
            # Target specific row in a repeatable section
            row_selector = f"/*[{row_index}]//"

        js = f"""
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return 'No popup';
            var inputs = popup.querySelectorAll('input[name="{name_attr}"]');
            var idx = {row_index if row_index is not None else 0};
            if (inputs[idx]) {{
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeInputValueSetter.call(inputs[idx], arguments[0]);
                inputs[idx].dispatchEvent(new Event('input', {{ bubbles: true }}));
                inputs[idx].dispatchEvent(new Event('change', {{ bubbles: true }}));
                return 'OK';
            }}
            return 'Not found: {name_attr} (idx=' + idx + ', total=' + inputs.length + ')';
        """
        result = self.driver.execute_script(js, str(value))
        if "OK" not in str(result):
            log.warning(f"Input not filled: {name_attr} — {result}")

    def _fill_input_by_placeholder(self, placeholder_text, value):
        """Fill an input field by its placeholder text using JS value-setter."""
        js = f"""
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return 'No popup';
            var inputs = popup.querySelectorAll('input');
            for (var i = 0; i < inputs.length; i++) {{
                if (inputs[i].placeholder && inputs[i].placeholder.trim() === '{placeholder_text}') {{
                    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    nativeInputValueSetter.call(inputs[i], arguments[0]);
                    inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return 'OK';
                }}
            }}
            return 'Not found: {placeholder_text}';
        """
        result = self.driver.execute_script(js, str(value))
        if "OK" not in str(result):
            log.warning(f"Input not filled by placeholder '{placeholder_text}': {result}")

    def _clear_input_by_name(self, name_attr, row_index=None):
        """Clear an input field by its name attribute using JS value-setter."""
        self._fill_input_by_name(name_attr, "", row_index=row_index)

    # ==============================================================
    #  Dropdown selection — JS approach (Angular Material)
    # ==============================================================

    def _open_dropdown_by_label(self, label_text):
        """Open a mat-select dropdown by finding its form-field label."""
        js = f"""
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return 'No popup';
            var formFields = popup.querySelectorAll('mat-form-field');
            for (var i = 0; i < formFields.length; i++) {{
                var label = formFields[i].querySelector('mat-label');
                if (label && label.textContent.trim() === '{label_text}') {{
                    var select = formFields[i].querySelector('mat-select');
                    if (select) {{
                        select.click();
                        return 'Opened';
                    }}
                }}
            }}
            return 'Not found: {label_text}';
        """
        result = self.driver.execute_script(js)
        self.wait_seconds(1.5)
        if "Opened" in str(result):
            return True
        log.warning(f"Dropdown not opened: {label_text} — {result}")
        return False

    def _open_dropdown_by_placeholder(self, placeholder_text):
        """Open a mat-select dropdown by finding its placeholder text."""
        js = f"""
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return 'No popup';
            var selects = popup.querySelectorAll('mat-select');
            for (var i = 0; i < selects.length; i++) {{
                var placeholder = selects[i].querySelector('.mat-select-placeholder, .mat-mdc-select-placeholder');
                if (placeholder && placeholder.textContent.trim() === '{placeholder_text}') {{
                    selects[i].click();
                    return 'Opened';
                }}
            }}
            // Also check mat-form-field appearance
            var formFields = popup.querySelectorAll('mat-form-field');
            for (var j = 0; j < formFields.length; j++) {{
                var matSelect = formFields[j].querySelector('mat-select');
                if (matSelect) {{
                    var allPlaceholders = formFields[j].querySelectorAll('.mat-select-placeholder, .mat-mdc-select-placeholder, span');
                    for (var k = 0; k < allPlaceholders.length; k++) {{
                        if (allPlaceholders[k].textContent.trim() === '{placeholder_text}') {{
                            matSelect.click();
                            return 'Opened via span';
                        }}
                    }}
                }}
            }}
            return 'Not found: {placeholder_text}';
        """
        result = self.driver.execute_script(js)
        self.wait_seconds(1.5)
        if "Opened" in str(result):
            return True
        log.warning(f"Dropdown not opened by placeholder '{placeholder_text}': {result}")
        return False

    def _select_option_by_text(self, option_text):
        """Select a mat-option from the currently open dropdown panel."""
        js = f"""
            var options = document.querySelectorAll(
                '.cdk-overlay-pane mat-option'
            );
            for (var i = 0; i < options.length; i++) {{
                if (options[i].textContent.trim() === '{option_text}') {{
                    options[i].click();
                    return 'Selected';
                }}
            }}
            var allOpts = document.querySelectorAll(
                '.cdk-overlay-pane [role="option"]'
            );
            for (var i = 0; i < allOpts.length; i++) {{
                if (allOpts[i].textContent.trim() === '{option_text}') {{
                    allOpts[i].click();
                    return 'Selected (role=option)';
                }}
            }}
            return 'Not found: {option_text}';
        """
        result = self.driver.execute_script(js)
        self.wait_seconds(1)
        if "Selected" in str(result):
            return True
        log.warning(f"Option not selected: {option_text} — {result}")
        return False

    def _select_option_contains(self, partial_text):
        """Select a mat-option whose text contains the given partial text."""
        js = f"""
            var options = document.querySelectorAll(
                '.cdk-overlay-pane mat-option'
            );
            for (var i = 0; i < options.length; i++) {{
                if (options[i].textContent.trim().indexOf('{partial_text}') > -1) {{
                    options[i].click();
                    return 'Selected: ' + options[i].textContent.trim();
                }}
            }}
            return 'Not found containing: {partial_text}';
        """
        result = self.driver.execute_script(js)
        self.wait_seconds(1)
        if "Selected" in str(result):
            return str(result).split("Selected: ")[1] if "Selected: " in str(result) else True
        log.warning(f"Option not selected (contains '{partial_text}'): {result}")
        return False

    def _search_and_select_option(self, search_text, exact_match=False):
        """Type search text in dropdown filter, then select the matching option."""
        # Type search text in the dropdown search input
        try:
            search_input = self.driver.find_element(
                By.CSS_SELECTOR,
                ".cdk-overlay-pane input, .cdk-overlay-pane [role='combobox']"
            )
            if search_input.is_displayed():
                search_input.clear()
                search_input.send_keys(search_text)
                self.wait_seconds(1.5)
        except Exception:
            pass

        # Now select
        if exact_match:
            return self._select_option_by_text(search_text)
        else:
            return self._select_option_contains(search_text)

    def _get_dropdown_options(self):
        """Get all option texts from the currently open dropdown panel."""
        js = """
            var options = document.querySelectorAll(
                '.cdk-overlay-pane mat-option'
            );
            var texts = [];
            for (var i = 0; i < options.length; i++) {
                texts.push(options[i].textContent.trim());
            }
            return texts;
        """
        return self.driver.execute_script(js) or []

    def select_dropdown_by_label(self, label_text, option_text):
        """Open dropdown by label and select option by exact text."""
        log.info(f"Selecting '{label_text}': {option_text}")
        self._open_dropdown_by_label(label_text)
        self._select_option_by_text(option_text)
        self._close_dropdown_panel()

    def select_dropdown_by_placeholder(self, placeholder_text, option_text):
        """Open dropdown by placeholder and select option by exact text."""
        log.info(f"Selecting (placeholder '{placeholder_text}'): {option_text}")
        self._open_dropdown_by_placeholder(placeholder_text)
        self._select_option_by_text(option_text)
        self._close_dropdown_panel()

    def select_random_from_dropdown_by_label(self, label_text):
        """Open dropdown by label, select a random option. Returns the text."""
        log.info(f"Selecting random option for: {label_text}")
        self._open_dropdown_by_label(label_text)
        options = self._get_dropdown_options()
        if not options:
            self._close_dropdown_panel()
            return None
        valid_opts = [o for o in options if o.strip()]
        if not valid_opts:
            self._close_dropdown_panel()
            return None
        chosen = random.choice(valid_opts)
        self._select_option_by_text(chosen)
        self._close_dropdown_panel()
        log.info(f"Selected: {chosen}")
        return chosen

    def select_random_from_dropdown_by_placeholder(self, placeholder_text):
        """Open dropdown by placeholder, select a random option. Returns the text."""
        log.info(f"Selecting random option for placeholder: {placeholder_text}")
        self._open_dropdown_by_placeholder(placeholder_text)
        options = self._get_dropdown_options()
        if not options:
            self._close_dropdown_panel()
            return None
        valid_opts = [o for o in options if o.strip()]
        if not valid_opts:
            self._close_dropdown_panel()
            return None
        chosen = random.choice(valid_opts)
        self._select_option_by_text(chosen)
        self._close_dropdown_panel()
        log.info(f"Selected: {chosen}")
        return chosen

    def get_dropdown_options_by_label(self, label_text):
        """Get all dropdown options by opening dropdown via label."""
        self._open_dropdown_by_label(label_text)
        opts = self._get_dropdown_options()
        self._close_dropdown_panel()
        return opts

    # ==============================================================
    #  Add Row buttons (for address and bank repeatable sections)
    # ==============================================================

    def click_add_address_row(self):
        """Click the Add Row button in the Address Details section."""
        log.info("Clicking Add Address Row button...")
        js = """
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return 'No popup';
            var buttons = popup.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.trim().toLowerCase().indexOf('add row') > -1 ||
                    buttons[i].textContent.trim().toLowerCase().indexOf('add') > -1) {
                    // Check if this is in the address section context
                    var parent = buttons[i].closest('mat-tab-content, .mat-tab-body-active, [ng-reflect-label]');
                    if (parent) {
                        buttons[i].click();
                        return 'Clicked: ' + buttons[i].textContent.trim();
                    }
                }
            }
            // Fallback: find any button with "+" icon in the form
            var addButtons = popup.querySelectorAll('button mat-icon');
            for (var j = 0; j < addButtons.length; j++) {
                if (addButtons[j].textContent.trim() === 'add' ||
                    addButtons[j].textContent.trim() === 'plus_one') {
                    addButtons[j].click();
                    return 'Clicked icon: ' + addButtons[j].textContent.trim();
                }
            }
            return 'Add row button not found';
        """
        result = self.driver.execute_script(js)
        self.wait_seconds(1)
        log.info(f"Add address row: {result}")

    def click_add_bank_row(self):
        """Click the Add Row button in the Bank Details section."""
        log.info("Clicking Add Bank Row button...")
        # Navigate to Bank Details step first
        # Try to find and click add row in bank section
        js = """
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return 'No popup';
            // Look for all "Add" or "+" buttons
            var buttons = popup.querySelectorAll('button');
            var addButtons = [];
            for (var i = 0; i < buttons.length; i++) {
                var txt = buttons[i].textContent.trim().toLowerCase();
                if (txt.indexOf('add') > -1 || txt.indexOf('+') > -1) {
                    addButtons.push(buttons[i]);
                }
            }
            // Try the last add button (likely bank section)
            if (addButtons.length > 0) {
                addButtons[addButtons.length - 1].click();
                return 'Clicked last add button';
            }
            return 'No add buttons found';
        """
        result = self.driver.execute_script(js)
        self.wait_seconds(1)
        log.info(f"Add bank row: {result}")

    # ==============================================================
    #  Form fill — Step 1: Universal
    # ==============================================================

    def fill_universal_step(self, data):
        """Fill Step 1 (Universal) fields: Agent Name, Phone Number, Email."""
        log.info("Filling Universal step...")

        if data.get("agent_name"):
            self._fill_input_by_name("Agent Name", data["agent_name"])
        if data.get("phone_number"):
            self._fill_input_by_name("Phone Number", data["phone_number"])
        if data.get("email"):
            self._fill_input_by_name("Email", data["email"])

        self.wait_seconds(0.5)

    # ==============================================================
    #  Form fill — Step 2: Address Details
    # ==============================================================

    def fill_address_step(self, data, row_index=0):
        """Fill Step 2 (Address Details) for a specific row.

        Args:
            data: Dict with address fields.
            row_index: Row index (0 for first row).
        """
        log.info(f"Filling Address Details (row {row_index})...")

        if data.get("address_type"):
            self.select_dropdown_by_placeholder("Address Type", data["address_type"])
        if data.get("country"):
            self.select_dropdown_by_placeholder("Country", data["country"])
            self.wait_seconds(1)
        if data.get("state"):
            self.select_dropdown_by_placeholder("State", data["state"])
            self.wait_seconds(1)
        if data.get("district"):
            self.select_dropdown_by_placeholder("District", data["district"])
            self.wait_seconds(1)
        if data.get("taluka"):
            self.select_dropdown_by_placeholder("Taluka", data["taluka"])
        if data.get("village"):
            self.select_dropdown_by_placeholder("Village", data["village"])
        if data.get("address"):
            self._fill_input_by_name("Address", data["address"], row_index=row_index)
        if data.get("pin_code"):
            self._fill_input_by_name("Pin Code", data["pin_code"], row_index=row_index)
        if data.get("gst"):
            self._fill_input_by_name("GST", data["gst"], row_index=row_index)

        self.wait_seconds(0.5)

    # ==============================================================
    #  Form fill — Step 3: Payment Details
    # ==============================================================

    def fill_payment_step(self, data):
        """Fill Step 3 (Payment Details): Payment Terms, Preferred Payment Method."""
        log.info("Filling Payment Details step...")

        if data.get("payment_terms"):
            self.select_dropdown_by_placeholder("Payment Terms", data["payment_terms"])
        if data.get("preferred_payment_method"):
            self.select_dropdown_by_placeholder(
                "Preferred Payment Method", data["preferred_payment_method"]
            )

        self.wait_seconds(0.5)

    # ==============================================================
    #  Form fill — Step 4: Bank Details
    # ==============================================================

    def fill_bank_detail_step(self, data, row_index=0):
        """Fill Step 4 (Bank Details) for a specific row.

        Args:
            data: Dict with bank detail fields.
            row_index: Row index (0 for first row).
        """
        log.info(f"Filling Bank Details (row {row_index})...")

        if data.get("bank_name"):
            self._fill_input_by_name("Bank Name", data["bank_name"], row_index=row_index)
        if data.get("branch"):
            self._fill_input_by_name("Branch", data["branch"], row_index=row_index)
        if data.get("ifsc_code"):
            self._fill_input_by_name("IFSC Code", data["ifsc_code"], row_index=row_index)
        if data.get("account_type"):
            self.select_dropdown_by_placeholder("Account Type", data["account_type"])
        if data.get("account_holder_name"):
            self._fill_input_by_name(
                "Account Holder Name", data["account_holder_name"], row_index=row_index
            )
        if data.get("account_number"):
            self._fill_input_by_name("Account Number", data["account_number"], row_index=row_index)
        # Bank Proof and Attachment are file uploads — handled separately

        self.wait_seconds(0.5)

    # ==============================================================
    #  Form fill — Complete all steps
    # ==============================================================

    def fill_agent_form(self, data):
        """Fill all stepper steps with provided data dict.

        Args:
            data: Dict with keys: agent_name, phone_number, email,
                  address (dict), payment (dict), bank (dict).
        """
        log.info("Filling Agent form (all steps)...")

        # Step 1: Universal
        self.fill_universal_step(data)
        self.click_next()
        self.wait_seconds(1)

        # Step 2: Address Details
        if data.get("address"):
            self.fill_address_step(data["address"])
        self.click_next()
        self.wait_seconds(1)

        # Step 3: Payment Details
        if data.get("payment"):
            self.fill_payment_step(data["payment"])
        self.click_next()
        self.wait_seconds(1)

        # Step 4: Bank Details
        if data.get("bank"):
            self.fill_bank_detail_step(data["bank"])

        self.wait_seconds(0.5)

    # ==============================================================
    #  Create / Edit / Submit / Cancel
    # ==============================================================

    def create_agent(self, data):
        """Open Add form, fill all steps, and submit.

        Returns dict with:
            status: "PASSED" or "FAILED"
            agent_name: the agent name used
            error: error message if any
        """
        log.info("Creating Agent record...")
        self.open_add_form()
        self.wait_seconds(1)
        assert self._is_form_popup_open(), "Add form did not open"

        self.fill_agent_form(data)
        self.wait_seconds(0.5)

        return self._submit_and_handle_result(data)

    def _submit_and_handle_result(self, data):
        """Click Submit and handle the result."""
        result = {"status": "FAILED", "agent_name": "", "error": ""}

        self._force_close_panels()
        try:
            submit_btn = self.driver.find_element(
                By.XPATH,
                "//div[@class='popup-footer']//button[contains(.,'Submit')]"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                submit_btn,
            )
        except Exception:
            try:
                update_btn = self.driver.find_element(
                    By.XPATH,
                    "//div[@class='popup-footer']//button[contains(.,'Update')]"
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    update_btn,
                )
            except Exception as e:
                log.error(f"Submit/Update button not found: {e}")
                result["error"] = "Submit/Update button not found"
                return result

        self.wait_seconds(3)

        # Check SweetAlert
        swal_title = self.get_swal_title()

        if swal_title and "success" in swal_title.lower():
            result["status"] = "PASSED"
            result["agent_name"] = data.get("agent_name", "")
            log.info(f"Agent created successfully: {result['agent_name']}")
        elif swal_title and "validation" in swal_title.lower():
            result["error"] = f"{swal_title} — validation failed"
            log.warning(f"Validation failed: {result['error']}")
            self._dismiss_swal()
        else:
            popup_visible = self._is_form_popup_open()
            if popup_visible:
                result["error"] = "Submit clicked but no SweetAlert appeared"
                log.warning(result["error"])
            else:
                result["status"] = "PASSED"
                result["agent_name"] = data.get("agent_name", "")
                log.info(f"Agent created (no alert): {result['agent_name']}")

        return result

    def submit(self):
        """Click the Submit button on the form."""
        log.info("Clicking Submit button...")
        self._force_close_panels()
        try:
            submit_btn = self.driver.find_element(
                By.XPATH,
                "//div[@class='popup-footer']//button[contains(.,'Submit')]"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                submit_btn,
            )
            self.wait_seconds(2)
        except Exception as e:
            log.error(f"Submit button not found: {e}")

    def update(self):
        """Click the Update button on the edit form."""
        log.info("Clicking Update button...")
        self._force_close_panels()
        try:
            update_btn = self.driver.find_element(
                By.XPATH,
                "//div[@class='popup-footer']//button[contains(.,'Update')]"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                update_btn,
            )
            self.wait_seconds(2)
        except Exception as e:
            log.error(f"Update button not found: {e}")

    def cancel(self):
        """Click the Cancel button on the form popup."""
        log.info("Clicking Cancel button...")
        try:
            cancel_btn = self.driver.find_element(
                By.XPATH,
                "//div[@class='popup-footer']//button[contains(.,'Cancel')]"
            )
            self.driver.execute_script("arguments[0].click();", cancel_btn)
            self.wait_seconds(1)
        except Exception as e:
            log.warning(f"Cancel button not found: {e}")

    def close_popup(self):
        """Close the form popup via Cancel button or JS removal."""
        try:
            self.cancel()
        except Exception:
            pass
        try:
            self.force_close_form_popup()
        except Exception:
            pass

    def force_close_form_popup(self):
        """Force close the form popup by removing it from DOM."""
        self.driver.execute_script("""
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (popup) {
                popup.remove();
            }
            var backdrop = document.querySelector(
                '.cdk-overlay-dark-backdrop, .cdk-overlay-backdrop'
            );
            if (backdrop) {
                backdrop.remove();
            }
        """)
        self.wait_seconds(0.5)

    # ==============================================================
    #  SweetAlert2 handling
    # ==============================================================

    def get_swal_title(self):
        """Get the SweetAlert2 title text."""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            if el.is_displayed():
                return el.text.strip()
        except Exception:
            pass
        return ""

    def get_swal_content(self):
        """Get the SweetAlert2 content text."""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, ".swal2-html-container")
            if el.is_displayed():
                return el.text.strip()
        except Exception:
            pass
        return ""

    def _dismiss_swal(self):
        """Dismiss a SweetAlert2 popup by clicking OK/Confirm."""
        try:
            confirm = self.driver.find_element(
                By.CSS_SELECTOR, ".swal2-confirm"
            )
            if confirm.is_displayed():
                self.driver.execute_script("arguments[0].click();", confirm)
                self.wait_seconds(0.5)
                log.info("SweetAlert dismissed")
        except Exception:
            pass

    def handle_validation_warning(self, timeout=5):
        """Check for and handle validation warning SweetAlert.
        Returns the alert title text if found, empty string otherwise.
        """
        try:
            title = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            alert_text = title.text.strip()
            log.info(f"Validation alert: {alert_text}")
            self._dismiss_swal()
            return alert_text
        except TimeoutException:
            return ""

    def handle_success_alert(self, timeout=5):
        """Check for success SweetAlert and dismiss it.
        Returns the alert title text if found.
        """
        return self.handle_validation_warning(timeout=timeout)

    # ==============================================================
    #  Form state checks
    # ==============================================================

    def is_add_form_open(self):
        """Check if the add form popup is currently open."""
        return self._is_form_popup_open()

    def is_form_popup_open(self):
        """Check if any form popup is currently open."""
        return self._is_form_popup_open()

    def get_form_field_values(self):
        """Read all input values from the current form step using JS.

        Uses execute_script with querySelectorAll('input') and inp.value
        for reliable Angular Material value reading.
        """
        js = """
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return {};
            var result = {};
            var inputs = popup.querySelectorAll('input');
            for (var i = 0; i < inputs.length; i++) {
                var inp = inputs[i];
                var key = inp.name || inp.placeholder || ('input_' + i);
                if (key && result[key] === undefined) {
                    result[key] = inp.value || '';
                }
            }
            return result;
        """
        return self.driver.execute_script(js) or {}

    def get_input_value(self, name_attr):
        """Get the current value of an input by its name attribute using JS."""
        js = f"""
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return '';
            var input = popup.querySelector('input[name="{name_attr}"]');
            return input ? input.value : '';
        """
        return self.driver.execute_script(js) or ""

    def get_field_validation_state(self, field_label):
        """Check if a field has validation errors.

        Returns dict: {"invalid": bool, "error": str}
        """
        js = f"""
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return {{invalid: false, error: ''}};
            var formFields = popup.querySelectorAll('mat-form-field');
            for (var i = 0; i < formFields.length; i++) {{
                var label = formFields[i].querySelector('mat-label');
                if (label && label.textContent.trim().indexOf('{field_label}') > -1) {{
                    var matError = formFields[i].querySelector('mat-error');
                    if (matError && matError.textContent.trim()) {{
                        return {{invalid: true, error: matError.textContent.trim()}};
                    }}
                    var hasErrorClass = formFields[i].classList.contains('mat-form-field-invalid') ||
                                       formFields[i].getAttribute('aria-invalid') === 'true';
                    return {{invalid: hasErrorClass, error: hasErrorClass ? '(red highlight, no text)' : ''}};
                }}
            }}
            return {{invalid: false, error: ''}};
        """
        return self.driver.execute_script(js) or {"invalid": False, "error": ""}

    def get_mat_error_text(self):
        """Get all mat-error texts currently visible in the form."""
        js = """
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return [];
            var errors = popup.querySelectorAll('mat-error');
            var texts = [];
            for (var i = 0; i < errors.length; i++) {
                var t = errors[i].textContent.trim();
                if (t && texts.indexOf(t) === -1) {
                    texts.push(t);
                }
            }
            return texts;
        """
        return self.driver.execute_script(js) or []

    # ==============================================================
    #  Table operations
    # ==============================================================

    def search(self, search_text):
        """Search for a record in the Agent table."""
        log.info(f"Searching for: {search_text}")
        try:
            # Toggle search if needed
            search_toggle = self.driver.find_elements(
                By.CSS_SELECTOR, "button.search-btn, button[aria-label='Search']"
            )
            for btn in search_toggle:
                try:
                    if btn.is_displayed():
                        btn.click()
                        self.wait_seconds(0.5)
                        break
                except Exception:
                    continue

            # Type in search input
            search_input = self.driver.find_element(
                By.CSS_SELECTOR,
                ".erp-search-wrapper input, input#erpSearchInput"
            )
            search_input.clear()
            search_input.send_keys(search_text)
            self.wait_seconds(0.5)

            # Click search submit
            search_submit = self.driver.find_elements(
                By.CSS_SELECTOR, "button.search-btn"
            )
            for btn in search_submit:
                try:
                    if btn.is_displayed():
                        btn.click()
                        self.wait_seconds(2)
                        break
                except Exception:
                    continue

            log.info(f"Search submitted for: {search_text}")
        except Exception as e:
            log.warning(f"Search failed: {e}")

    def is_agent_in_table(self, agent_name):
        """Check if an agent name exists in the table rows."""
        js = f"""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            for (var i = 0; i < rows.length; i++) {
                if (rows[i].textContent.indexOf('{agent_name}') > -1) {
                    return true;
                }
            }
            return false;
        """
        return self.driver.execute_script(js)

    def get_table_row_count(self):
        """Get the number of data rows in the Agent table."""
        js = """
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            var count = 0;
            for (var i = 0; i < rows.length; i++) {
                if (rows[i].textContent.trim() !== '' &&
                    !rows[i].querySelector('.no-data')) {
                    count++;
                }
            }
            return count;
        """
        return self.driver.execute_script(js)

    # ==============================================================
    #  Row action buttons
    # ==============================================================

    def click_edit_button(self, agent_name):
        """Click the Edit button for a specific agent in the table."""
        log.info(f"Clicking Edit for: {agent_name}")
        js = f"""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            for (var i = 0; i < rows.length; i++) {
                if (rows[i].textContent.indexOf('{agent_name}') > -1) {
                    var editBtn = rows[i].querySelector('td:nth-child(2) button');
                    if (editBtn) {{
                        editBtn.click();
                        return 'Clicked edit';
                    }}
                    // Try any button with edit icon
                    var buttons = rows[i].querySelectorAll('button');
                    for (var j = 0; j < buttons.length; j++) {{
                        if (buttons[j].textContent.trim().toLowerCase().indexOf('edit') > -1) {{
                            buttons[j].click();
                            return 'Clicked edit (text match)';
                        }}
                    }}
                }
            }
            return 'Not found';
        """
        result = self.driver.execute_script(js)
        self.wait_seconds(2)
        log.info(f"Edit button: {result}")

    def click_view_button(self, agent_name):
        """Click the View button for a specific agent in the table."""
        log.info(f"Clicking View for: {agent_name}")
        js = f"""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            for (var i = 0; i < rows.length; i++) {
                if (rows[i].textContent.indexOf('{agent_name}') > -1) {
                    var viewBtn = rows[i].querySelector('td:nth-child(1) button');
                    if (viewBtn) {{
                        viewBtn.click();
                        return 'Clicked view';
                    }}
                }
            }
            return 'Not found';
        """
        result = self.driver.execute_script(js)
        self.wait_seconds(2)
        log.info(f"View button: {result}")