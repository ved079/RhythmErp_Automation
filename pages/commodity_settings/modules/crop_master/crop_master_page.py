"""
Crop Master Page Object — RhythmERP Commodity Settings > Crop Master

Page Object Model for the Crop Master screen with all locators,
action flows, and helper methods. Follows the same pattern as
DesignationPage and VehicleMasterPage.

Key Differences from other modules:
- NO dropdown fields (simpler than Vehicle Master)
- 4 fields: Name (text), Description (text), File Upload, Status Toggle
- History popup uses .popup-overlay (NOT .big-model like Vehicle Master)
- History column CSS class is 'archive' (cdk-column-archive)
- Form popup uses .edit_pop_up.override_edit_pop_up.popup-mode
- Status is a custom switch component (.slider click, NOT checkbox click)
- Search uses JS value injection + event dispatch (Angular reactive forms)
- driver.refresh() REQUIRED after navigate_to() to clear SPA state
- SweetAlert2 success toast may auto-dismiss quickly
"""

import os
import sys
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)

# Resolve project root for imports
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.base_page import BasePage
from common.logger import log


class CropMasterPage(BasePage):
    """Page Object Model for RhythmERP Crop Master screen."""

    PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Crop%20Master"

    # ═══════════════════════════════════════════
    #  LOCATORS — Table & Toolbar
    # ═══════════════════════════════════════════

    TABLE = ("css", "table#excel-table")
    TABLE_CONTAINER = ("css", ".scrollable-table-container")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")

    SEARCH_BUTTON = ("css", "button.search-btn")
    ADD_BUTTON = ("xpath", "//button[contains(@class,'erp-add-btn')]")
    FILTER_BUTTON = ("xpath", "//*[@mattooltip='Filters']/button")
    REFRESH_BUTTON = ("xpath", "//*[@mattooltip='REFRESH']/button")
    MORE_BUTTON = ("css", "button[mattooltip='More']")

    SEARCH_INPUT = ("css", "#erpSearchInput")

    # ═══════════════════════════════════════════
    #  LOCATORS — Table Column Cells
    # ═══════════════════════════════════════════

    NAME_CELLS = ("css", "td.cdk-column-name, td.mat-column-name")
    DESCRIPTION_CELLS = ("css", "td.cdk-column-description, td.mat-column-description")
    STATUS_CELLS = ("css", "td.cdk-column-status, td.mat-column-status")

    # ═══════════════════════════════════════════
    #  LOCATORS — Popup Container (Add/Edit/View)
    # ═══════════════════════════════════════════

    POPUP_CONTAINER = ("css", ".edit_pop_up.override_edit_pop_up.popup-mode")
    POPUP_HEADER = ("css", ".popup-header")
    POPUP_TITLE = ("css", ".edit_pop_up h3")
    POPUP_BODY = ("css", ".overflow_model")
    POPUP_FOOTER = ("xpath", "//div[contains(@class,'popup-footer')]")

    # ═══════════════════════════════════════════
    #  LOCATORS — Form Fields (NO Dropdowns!)
    # ═══════════════════════════════════════════

    NAME_INPUT = ("css", ".edit_pop_up input[name='Name']")
    DESCRIPTION_INPUT = ("css", ".edit_pop_up input[name='Description']")
    FILE_INPUT = ("css", ".edit_pop_up input[type='file']")
    FILE_UPLOAD_CONTAINER = ("css", ".edit_pop_up .custom-file-upload")

    # ═══════════════════════════════════════════
    #  LOCATORS — Status Toggle
    # ═══════════════════════════════════════════

    STATUS_SLIDER = ("css", ".edit_pop_up .slider")
    STATUS_CHECKBOX = ("css", ".edit_pop_up input[type='checkbox']")
    STATUS_MAIN_LABEL = ("css", ".edit_pop_up .main-label")
    STATUS_ON_LABEL = ("css", ".edit_pop_up .state-label.on.active")
    STATUS_OFF_LABEL = ("css", ".edit_pop_up .state-label.off")

    # ═══════════════════════════════════════════
    #  LOCATORS — Popup Buttons
    # ═══════════════════════════════════════════

    SUBMIT_BUTTON = ("xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    )
    UPDATE_BUTTON = ("xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
    )
    CANCEL_BUTTON = ("xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    )

    # ═══════════════════════════════════════════
    #  LOCATORS — SweetAlert2
    # ═══════════════════════════════════════════

    SWAL_TITLE = ("css", "#swal2-title")
    SWAL_CONFIRM = ("css", ".swal2-confirm")
    SWAL_CONTAINER = ("css", ".swal2-container")
    SWAL_WARNING_ICON = ("css", ".swal2-icon.swal2-warning")
    SWAL_SUCCESS_ICON = ("css", ".swal2-icon.swal2-success")

    # ═══════════════════════════════════════════
    #  LOCATORS — History Popup (.popup-overlay!)
    # ═══════════════════════════════════════════

    HISTORY_TITLE = ("xpath",
        "//div[contains(@class,'popup-overlay')]//h3[contains(translate(.,'HISTORY','history'),'history')]"
    )
    HISTORY_SEARCH_INPUT = ("css", ".popup-overlay input")
    HISTORY_TABLE_ROWS = ("css", ".popup-overlay table tbody tr")
    HISTORY_TABLE_HEADERS = ("css", ".popup-overlay table th")

    # ═══════════════════════════════════════════
    #  LOCATORS — Filter Panel
    # ═══════════════════════════════════════════

    FILTER_PANEL = ("css", ".filter-panel")
    FILTER_APPLY = ("css", ".apply-btn")
    FILTER_CLEAR = ("css", ".clear-btn")
    FILTER_CLOSE = ("css", ".filter-panel .close-btn")

    # ═══════════════════════════════════════════
    #  NAVIGATION & PAGE LOAD
    # ═══════════════════════════════════════════

    def navigate_to_page(self):
        """Navigate to Crop Master screen and force refresh.
        CRITICAL: refresh() clears leftover Angular SPA state.
        Without it, stale overlays can block the ADD button.
        """
        log.info("Navigating to Crop Master page")
        self.navigate_to(self.PAGE_URL)
        time.sleep(2)
        self.driver.refresh()
        self._wait_for_page_ready()
        log.info("Arrived at Crop Master page")

    def _wait_for_page_ready(self, timeout=30):
        """Wait for page fully loaded — table + toolbar ready.
        2-step wait ensures toolbar (incl. ADD) is ready.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table#excel-table")
                )
            )
        except TimeoutException:
            log.warning(f"[WARNING] Page may not be fully ready after {timeout}s")

        self._wait_for_toolbar()
        time.sleep(1)

    def _wait_for_toolbar(self, retries=3, delay=2):
        """Retry ADD button readiness. 3 retries x 2s."""
        for attempt in range(retries):
            try:
                add_div = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.erp-add-btn"
                )
                add_btns = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.mat-mdc-mini-fab mat-icon"
                )
                add_icons = [b for b in add_btns
                             if b.text.strip().lower() == 'add']
                if add_div or add_icons:
                    return
            except Exception:
                pass
            time.sleep(delay)
        log.warning("Toolbar readiness check: ADD button not confirmed")

    def is_page_loaded(self):
        """Check if listing page loaded."""
        return self.is_displayed(self.TABLE, timeout=10)

    # ═══════════════════════════════════════════
    #  ADD FORM — 4-Strategy Approach
    # ═══════════════════════════════════════════

    def open_add_form(self):
        """Click ADD button to open create form. 4 strategies with verification."""
        log.info("Opening ADD form")
        self._wait_for_toolbar()

        # Strategy 1: mattooltip div button
        try:
            divs = self.driver.find_elements(
                By.CSS_SELECTOR, "button.erp-add-btn"
            )
            for div in divs:
                try:
                    btn = div.find_element(By.TAG_NAME, "button")
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", btn
                    )
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    if self._is_form_popup_open():
                        log.info("Open add form: clicked add icon")
                        return
                except Exception:
                    continue
        except Exception as e:
            log.info(f"Strategy 1 failed: {e}")

        # Strategy 2: mini-fab icon='add'
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-mdc-mini-fab mat-icon"
            )
            for btn in btns:
                if btn.text.strip().lower() == 'add':
                    parent_btn = btn.find_element(By.XPATH, "..")
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", parent_btn
                    )
                    self.driver.execute_script("arguments[0].click();", parent_btn)
                    time.sleep(1)
                    if self._is_form_popup_open():
                        log.info("ADD form opened via Strategy 2 (mini-fab icon)")
                        return
        except Exception as e:
            log.info(f"Strategy 2 failed: {e}")

        # Strategy 3: div wrapper click
        try:
            divs = self.driver.find_elements(
                By.CSS_SELECTOR, "button.erp-add-btn"
            )
            for div in divs:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", div
                )
                self.driver.execute_script("arguments[0].click();", div)
                time.sleep(1)
                if self._is_form_popup_open():
                    log.info("ADD form opened via Strategy 3 (div wrapper)")
                    return
        except Exception as e:
            log.info(f"Strategy 3 failed: {e}")

        # Strategy 4: click_with_retry
        try:
            self.click_with_retry(self.ADD_BUTTON)
            time.sleep(1)
            if self._is_form_popup_open():
                log.info("ADD form opened via Strategy 4 (click_with_retry)")
                return
        except Exception as e:
            log.info(f"Strategy 4 failed: {e}")

        raise Exception("Failed to open ADD form after 4 strategies")

    def _is_form_popup_open(self):
        """Check if form popup is visible."""
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR, "div.edit_pop_up"
            )
            for p in popups:
                if p.is_displayed():
                    return True
            big_models = self.driver.find_elements(
                By.CSS_SELECTOR, ".big-model"
            )
            for bm in big_models:
                if bm.is_displayed():
                    return True
        except Exception:
            pass
        return False

    def is_add_form_open(self):
        """Check if Add form visible (Name input present)."""
        return self.is_displayed(self.NAME_INPUT, timeout=5)

    def is_form_closed(self):
        """Check if form popup closed."""
        return not self.is_displayed(self.NAME_INPUT, timeout=3)

    # ═══════════════════════════════════════════
    #  FORM FILL
    # ═══════════════════════════════════════════

    def fill_crop_form(self, data):
        """Fill all form fields.
        data: dict with keys 'name', 'description', 'status', 'file_path'
        NO dropdowns — much simpler than Vehicle Master.
        """
        log.info("Filling crop form")

        if data.get('name') is not None:
            self.type_text(self.NAME_INPUT, data['name'], clear_first=True)
            log.info(f"Name set to: {data['name']}")

        if data.get('description') is not None:
            self.type_text(self.DESCRIPTION_INPUT, data['description'], clear_first=True)
            log.info(f"Description set to: {data['description']}")

        if data.get('file_path') is not None:
            self.upload_file(data['file_path'])

        if data.get('status') is not None:
            self.set_status(data['status'])

    # ═══════════════════════════════════════════
    #  STATUS TOGGLE
    # ═══════════════════════════════════════════

    def toggle_status(self):
        """Toggle Status switch. Clicks .slider element via JS.
        DO NOT click the hidden checkbox directly.
        """
        try:
            sliders = self.driver.find_elements(
                By.CSS_SELECTOR, ".edit_pop_up .slider"
            )
            for slider in sliders:
                try:
                    wrapper = slider.find_element(
                        By.XPATH,
                        "./ancestor::div[contains(@class,'switch-container')]"
                    )
                    if wrapper.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].click();", slider
                        )
                        time.sleep(0.5)
                        log.info("Status toggled")
                        return
                except Exception:
                    continue
            # Fallback: .switch-wrapper .slider
            sliders2 = self.driver.find_elements(
                By.CSS_SELECTOR, ".switch-wrapper .slider"
            )
            for slider in sliders2:
                try:
                    wrapper = slider.find_element(
                        By.XPATH,
                        "./ancestor::div[contains(@class,'switch-wrapper')]"
                    )
                    if wrapper.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].click();", slider
                        )
                        time.sleep(0.5)
                        log.info("Status toggled (fallback)")
                        return
                except Exception:
                    continue
        except Exception as e:
            log.warning(f"Toggle status failed: {e}")

    def get_current_status(self):
        """Read current status from toggle.
        Returns 'Active' or 'Inactive'.
        """
        try:
            checkboxes = self.driver.find_elements(
                By.CSS_SELECTOR, ".edit_pop_up input[type='checkbox']"
            )
            for cb in checkboxes:
                try:
                    wrapper = cb.find_element(
                        By.XPATH,
                        "./ancestor::div[contains(@class,'switch-container')]"
                    )
                    if wrapper.is_displayed():
                        is_checked = cb.is_selected() if hasattr(cb, 'is_selected') \
                            else cb.get_property('checked')
                        return 'Active' if is_checked else 'Inactive'
                except Exception:
                    continue
            on_labels = self.driver.find_elements(
                By.CSS_SELECTOR, ".edit_pop_up .state-label.on"
            )
            for label in on_labels:
                if 'active' in (label.get_attribute('class') or ''):
                    return 'Active'
            return 'Inactive'
        except Exception:
            return 'Active'

    def set_status(self, desired_status):
        """Set status to specific value. No-op if already in desired state."""
        current = self.get_current_status()
        if current != desired_status:
            self.toggle_status()
            time.sleep(0.3)

    # ═══════════════════════════════════════════
    #  FILE UPLOAD
    # ═══════════════════════════════════════════

    def upload_file(self, file_path):
        """Upload file to form via send_keys on input[type='file'].
        Accepts .png, .jpg, .pdf only.
        Returns True if upload attempted, False otherwise.
        """
        if not file_path:
            return False
        if not os.path.exists(file_path):
            log.warning(f"File not found: {file_path}")
            return False
        try:
            file_input = self.driver.find_element(
                By.CSS_SELECTOR, ".edit_pop_up input[type='file']"
            )
            file_input.send_keys(file_path)
            time.sleep(1)
            log.info(f"File uploaded: {os.path.basename(file_path)}")
            return True
        except Exception as e:
            log.warning(f"File upload failed: {e}")
            return False

    def is_file_uploaded(self):
        """Check if file has been uploaded."""
        try:
            containers = self.driver.find_elements(
                By.CSS_SELECTOR, ".edit_pop_up .custom-file-upload"
            )
            for c in containers:
                text = c.text.strip()
                if 'No File Uploaded' not in text and text:
                    return True
            return False
        except Exception:
            return False

    def get_uploaded_file_text(self):
        """Get file upload display text."""
        try:
            containers = self.driver.find_elements(
                By.CSS_SELECTOR, ".edit_pop_up .custom-file-upload"
            )
            for c in containers:
                text = c.text.strip()
                if text:
                    return text
            return ''
        except Exception:
            return ''

    # ═══════════════════════════════════════════
    #  FORM SUBMIT / UPDATE / CANCEL
    # ═══════════════════════════════════════════

    def submit(self):
        """Click Submit button (Create mode). JS click with scroll + fallback."""
        log.info("Clicked Submit button")
        try:
            btn = self.find_visible_element(self.SUBMIT_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", btn
                )
                self.driver.execute_script("arguments[0].click();", btn)
                return
        except Exception as e:
            log.info(f"Submit strategy 1 failed: {e}")

        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", btn
            )
            self.driver.execute_script("arguments[0].click();", btn)
            return
        except Exception as e:
            log.info(f"Submit strategy 2 failed: {e}")

        try:
            self.click_with_retry(self.SUBMIT_BUTTON)
        except Exception as e:
            log.error(f"All submit strategies failed: {e}")

    def click_update(self):
        """Click Update button (Edit mode). JS click with scroll + fallback."""
        log.info("Clicked Update button")
        try:
            btn = self.find_visible_element(self.UPDATE_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", btn
                )
                self.driver.execute_script("arguments[0].click();", btn)
                return
        except Exception as e:
            log.info(f"Update strategy 1 failed: {e}")

        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", btn
            )
            self.driver.execute_script("arguments[0].click();", btn)
            return
        except Exception as e:
            log.info(f"Update strategy 2 failed: {e}")

        try:
            self.click_with_retry(self.UPDATE_BUTTON)
        except Exception as e:
            log.error(f"All update strategies failed: {e}")

    def cancel(self):
        """Click Cancel button. JS click."""
        log.info("Clicking Cancel button")
        try:
            btn = self.find_visible_element(self.CANCEL_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script("arguments[0].click();", btn)
                return
        except Exception:
            pass
        try:
            self.click_with_retry(self.CANCEL_BUTTON)
        except Exception as e:
            log.error(f"Cancel failed: {e}")

    def close_popup(self):
        """Click X icon in popup header."""
        log.info("Closing popup via X icon")
        try:
            icons = self.driver.find_elements(
                By.CSS_SELECTOR, ".edit_pop_up button mat-icon"
            )
            for icon in icons:
                if icon.text.strip().lower() == 'close':
                    btn = icon.find_element(By.XPATH, "./ancestor::button")
                    self.driver.execute_script("arguments[0].click();", btn)
                    return
        except Exception:
            pass
        self.cancel()

    # ═══════════════════════════════════════════
    #  SWEETALERT2 HANDLING
    # ═══════════════════════════════════════════

    def handle_success_alert(self, timeout=60):
        """Wait for SweetAlert2 success, click OK, cleanup.
        Returns message text or ''.
        """
        log.info("Waiting for success alert")
        message = ''
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            message = title_el.text.strip()
            log.info(f"SweetAlert2 message: {message}")

            self._swal2_confirm_click()

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, ".swal2-container")
                    )
                )
            except TimeoutException:
                pass
        except TimeoutException:
            log.warning("Success alert not found within timeout")
        except Exception as e:
            log.warning(f"Success alert handling error: {e}")

        self._cleanup_swal2()
        return message

    def handle_validation_warning(self, timeout=15):
        """Handle SweetAlert2 validation warning popup.
        Returns warning text or ''.
        """
        log.info("Handling validation warning")
        warning_text = ''
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            warning_text = title_el.text.strip()
            log.info(f"Validation warning: {warning_text}")

            self._swal2_confirm_click()

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, ".swal2-container")
                    )
                )
            except TimeoutException:
                pass
        except TimeoutException:
            log.info("No validation warning found")
        except Exception as e:
            log.warning(f"Validation warning handling error: {e}")

        return warning_text

    def is_validation_alert_present(self, timeout=5):
        """Check if SweetAlert2 visible."""
        return self.is_displayed(self.SWAL_TITLE, timeout=timeout)

    def is_success_alert_present(self, timeout=5):
        """Check if SweetAlert2 success alert visible."""
        try:
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            if title_el.is_displayed():
                text = title_el.text.strip().lower()
                return 'success' in text or 'added' in text or 'updated' in text
        except Exception:
            pass
        return False

    def _swal2_confirm_click(self):
        """3-tier SWAL2 confirm click."""
        try:
            confirm = self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
            confirm.click()
            return
        except ElementClickInterceptedException:
            pass
        except Exception:
            pass

        try:
            confirm = self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
            self.driver.execute_script("arguments[0].click();", confirm)
            return
        except Exception:
            pass

        try:
            self.driver.execute_script(
                "document.querySelectorAll('.swal2-confirm')"
                ".forEach(function(b){b.click();})"
            )
        except Exception:
            pass

    def _cleanup_swal2(self):
        """Remove leftover SweetAlert2 containers and backdrops via JS."""
        try:
            self.driver.execute_script(
                "document.querySelectorAll('.swal2-container')"
                ".forEach(function(el){el.remove();})"
            )
        except Exception:
            pass
        try:
            self.driver.execute_script(
                "document.querySelectorAll('.swal2-backdrop-show')"
                ".forEach(function(el){el.remove();})"
            )
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  INLINE ERROR (mat-error)
    # ═══════════════════════════════════════════

    def get_mat_error_text(self):
        """Get all visible mat-error texts.
        Note: Crop Master has NO inline mat-error elements (BUG-CM04).
        """
        errors = []
        try:
            mat_errors = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
            )
            for el in mat_errors:
                text = el.text.strip()
                if text and el.is_displayed():
                    errors.append(text)
        except Exception:
            pass
        return errors

    def has_field_error(self, field_label):
        """Check if specific field has inline error."""
        try:
            xpath = (
                f"//mat-label[contains(.,'{field_label}')]"
                "/ancestor::mat-form-field//mat-error"
            )
            errors = self.driver.find_elements(By.XPATH, xpath)
            return len(errors) > 0
        except Exception:
            return False

    # ═══════════════════════════════════════════
    #  FORM STATE QUERIES
    # ═══════════════════════════════════════════

    def get_form_heading(self):
        """Read popup heading text."""
        try:
            h3 = self.driver.find_element(By.CSS_SELECTOR, ".edit_pop_up h3")
            return h3.text.strip()
        except Exception:
            return ''

    def is_view_mode(self):
        """Check if View (read-only) mode — inputs disabled."""
        try:
            name_input = self.driver.find_element(
                By.CSS_SELECTOR, ".edit_pop_up input[name='Name']"
            )
            return not name_input.is_enabled()
        except Exception:
            return False

    def is_edit_mode(self):
        """Check if Edit mode — Update button visible."""
        return self.is_displayed(self.UPDATE_BUTTON, timeout=3)

    def get_form_field_values(self):
        """Read all form field values.
        Returns dict: name, description, status, has_file
        """
        values = {}
        try:
            name_input = self.driver.find_element(
                By.CSS_SELECTOR, ".edit_pop_up input[name='Name']"
            )
            values['name'] = name_input.get_attribute('value') or ''
        except Exception:
            values['name'] = ''

        try:
            desc_input = self.driver.find_element(
                By.CSS_SELECTOR, ".edit_pop_up input[name='Description']"
            )
            values['description'] = desc_input.get_attribute('value') or ''
        except Exception:
            values['description'] = ''

        try:
            values['status'] = self.get_current_status()
        except Exception:
            values['status'] = 'Active'

        try:
            values['has_file'] = self.is_file_uploaded()
        except Exception:
            values['has_file'] = False

        return values

    def verify_view_popup_read_only(self):
        """Verify all View fields disabled + no Submit/Update button."""
        try:
            name_input = self.driver.find_element(
                By.CSS_SELECTOR, ".edit_pop_up input[name='Name']"
            )
            desc_input = self.driver.find_element(
                By.CSS_SELECTOR, ".edit_pop_up input[name='Description']"
            )
            name_disabled = not name_input.is_enabled()
            desc_disabled = not desc_input.is_enabled()

            primary_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(@class,'mat-primary')]"
            )
            no_primary = len(primary_btns) == 0

            return name_disabled and desc_disabled and no_primary
        except Exception:
            return False

    def verify_edit_popup_editable(self):
        """Verify Edit has Update button and editable fields."""
        try:
            update_visible = self.is_displayed(self.UPDATE_BUTTON, timeout=3)
            name_input = self.driver.find_element(
                By.CSS_SELECTOR, ".edit_pop_up input[name='Name']"
            )
            name_enabled = name_input.is_enabled()
            return update_visible and name_enabled
        except Exception:
            return False

    # ═══════════════════════════════════════════
    #  TABLE QUERIES
    # ═══════════════════════════════════════════

    def get_table_row_count(self):
        """Count visible data rows."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def get_all_crop_names(self):
        """List all crop names in table. Multiple fallback selectors."""
        names = []
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            for row in rows:
                try:
                    cell = (
                        row.find_elements(By.CSS_SELECTOR, "td.cdk-column-name")
                        or row.find_elements(By.CSS_SELECTOR, "td.mat-column-name")
                        or row.find_elements(By.CSS_SELECTOR, "td:nth-child(4)")
                    )
                    if cell:
                        names.append(cell[0].text.strip())
                except Exception:
                    continue
        except Exception:
            pass
        return names

    def is_crop_in_table(self, crop_name):
        """Check if crop exists in table (partial match)."""
        names = self.get_all_crop_names()
        return any(crop_name.lower() in n.lower() for n in names)

    def find_crop_row_index(self, crop_name):
        """Find row index by name. Returns -1 if not found."""
        names = self.get_all_crop_names()
        for i, n in enumerate(names):
            if crop_name.lower() in n.lower():
                return i
        return -1

    def get_status_from_table(self, crop_name):
        """Get Status text ('Active'/'Inactive') for a crop."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            for row in rows:
                name_cell = row.find_elements(
                    By.CSS_SELECTOR, "td.cdk-column-name"
                )
                if name_cell and crop_name.lower() in name_cell[0].text.lower():
                    status_cell = row.find_elements(
                        By.CSS_SELECTOR, "td.cdk-column-status"
                    )
                    if status_cell:
                        return status_cell[0].text.strip()
        except Exception:
            pass
        return ''

    # ═══════════════════════════════════════════
    #  ROW ACTION BUTTONS (View/Edit/History)
    # ═══════════════════════════════════════════

    def click_view_button(self, crop_name=None, row_index=None):
        """Click View action button."""
        return self._click_action_button('view', crop_name, row_index)

    def click_edit_button(self, crop_name=None, row_index=None):
        """Click Edit action button."""
        return self._click_action_button('edit', crop_name, row_index)

    def click_history_button(self, crop_name=None, row_index=None):
        """Click History action button.
        CRITICAL: Column class is cdk-column-archive (NOT 'history').
        """
        return self._click_action_button('history', crop_name, row_index)

    def _click_action_button(self, action, crop_name=None, row_index=None):
        """Click action button in a table row."""
        col_map = {
            'view': 'cdk-column-view',
            'edit': 'cdk-column-edit',
            'history': 'cdk-column-archive',
        }
        col_class = col_map.get(action, action)
        fallback_index = {'view': 0, 'edit': 1, 'history': 2}.get(action, 0)

        # Strategy 1: XPath by crop name
        if crop_name:
            try:
                xpath = (
                    f"//td[contains(text(),'{crop_name}')]/ancestor::tr"
                    f"//td[contains(@class,'{col_class}')]//button"
                )
                btns = self.driver.find_elements(By.XPATH, xpath)
                for btn in btns:
                    try:
                        if btn.is_displayed():
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView(true);", btn
                            )
                            self.driver.execute_script(
                                "arguments[0].click();", btn
                            )
                            time.sleep(1)
                            log.info(f"Clicked {action} button for: {crop_name}")
                            return True
                    except Exception:
                        continue
            except Exception:
                pass

        # Strategy 2: Index-based button click
        idx = row_index if row_index is not None else 0
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if idx < len(rows):
                row = rows[idx]
                buttons = row.find_elements(By.CSS_SELECTOR, "td button")
                if fallback_index < len(buttons):
                    btn = buttons[fallback_index]
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", btn
                    )
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    log.info(f"Clicked {action} button (index {idx})")
                    return True
        except Exception as e:
            log.warning(f"Index-based {action} click failed: {e}")

        log.warning(f"Could not click {action} button")
        return False

    # ═══════════════════════════════════════════
    #  SEARCH — JS Value Injection + Event Dispatch
    # ═══════════════════════════════════════════

    def search_crop(self, crop_name):
        """Search by name in table. 5 retries x 2s.
        Uses JS value injection + input event + Enter key.
        """
        log.info(f"Searching for: {crop_name}")

        for attempt in range(5):
            try:
                search_btns = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.search-btn"
                )
                for btn in search_btns:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        time.sleep(0.5)
                        break

                self.driver.execute_script("""
                    var input = document.getElementById('erpSearchInput');
                    if (input) {
                        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value'
                        ).set;
                        nativeInputValueSetter.call(input, arguments[0]);
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new KeyboardEvent('keydown', {
                            key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                        }));
                    }
                """, crop_name)
                time.sleep(2)

                if self.is_crop_in_table(crop_name):
                    log.info(f"Found: {crop_name}")
                    return True

            except Exception as e:
                log.info(f"Search attempt {attempt+1}/5 failed: {e}")

            time.sleep(1)

        log.warning(f"Crop not found after search: {crop_name}")
        return False

    def clear_search(self):
        """Clear search input."""
        try:
            input_el = self.driver.find_element(
                By.CSS_SELECTOR, "#erpSearchInput"
            )
            input_el.clear()
            input_el.send_keys(Keys.RETURN)
            time.sleep(1)
        except Exception:
            pass

    def click_refresh(self):
        """Click Refresh button."""
        log.info("Refreshing table")
        try:
            divs = self.driver.find_elements(
                By.CSS_SELECTOR, "div[mattooltip='REFRESH']"
            )
            for div in divs:
                try:
                    btn = div.find_element(By.TAG_NAME, "button")
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", btn
                    )
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    return
                except Exception:
                    continue
        except Exception:
            pass

        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-mdc-mini-fab mat-icon"
            )
            for btn in btns:
                if btn.text.strip().lower() == 'refresh':
                    parent_btn = btn.find_element(By.XPATH, "..")
                    self.driver.execute_script(
                        "arguments[0].click();", parent_btn
                    )
                    time.sleep(1)
                    return
        except Exception:
            log.warning("Refresh button not found")

    # ═══════════════════════════════════════════
    #  HISTORY POPUP (.popup-overlay structure!)
    # ═══════════════════════════════════════════

    def is_history_popup_open(self):
        """Check if History popup is visible."""
        try:
            titles = self.driver.find_elements(
                By.CSS_SELECTOR, "h3.popup-title"
            )
            for t in titles:
                if t.is_displayed() and 'history' in t.text.lower():
                    return True
            overlays = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-overlay"
            )
            for o in overlays:
                if o.is_displayed():
                    return True
        except Exception:
            pass
        return False

    def is_history_empty(self):
        """Check if history has no data."""
        return self.get_history_row_count() == 0

    def get_history_row_count(self):
        """Count history table rows."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-overlay table tbody tr"
            )
            if rows:
                return len(rows)
        except Exception:
            pass
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, ".big-model table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def get_history_data(self):
        """Read all history rows as list of dicts."""
        data = []
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-overlay table tbody tr"
            )
            if not rows:
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, ".big-model table tbody tr"
                )
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    row_data = {}
                    for i, cell in enumerate(cells):
                        row_data[f'col_{i}'] = cell.text.strip()
                    if row_data:
                        data.append(row_data)
                except Exception:
                    continue
        except Exception:
            pass
        return data

    def get_history_headers(self):
        """Read history table column headers."""
        headers = []
        try:
            ths = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-overlay table th"
            )
            for th in ths:
                text = th.text.strip()
                if text:
                    headers.append(text)
        except Exception:
            pass
        return headers

    def search_in_history(self, search_text):
        """Search in history table. MUST send Keys.RETURN."""
        try:
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-overlay input"
            )
            for inp in inputs:
                try:
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(search_text)
                        inp.send_keys(Keys.RETURN)
                        time.sleep(1)
                        log.info(f"History search: {search_text}")
                        return True
                except Exception:
                    continue
        except Exception:
            log.warning("History search input not found")
        return False

    def close_history_popup(self):
        """Close History popup. 3 JS strategies."""
        # Strategy 1: Cancel button
        try:
            cancel_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-overlay')]//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
            )
            for btn in cancel_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        time.sleep(0.5)
                        if not self.is_history_popup_open():
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 2: X icon
        try:
            icons = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-overlay .popup-header button mat-icon"
            )
            for icon in icons:
                try:
                    if icon.text.strip().lower() == 'close':
                        btn = icon.find_element(By.XPATH, "./ancestor::button")
                        self.driver.execute_script("arguments[0].click();", btn)
                        time.sleep(0.5)
                        if not self.is_history_popup_open():
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: Force remove overlays
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.popup-overlay').forEach(function(el){el.remove();});
                document.querySelectorAll('.cdk-overlay-pane').forEach(function(el){el.remove();});
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el){el.remove();});
            """)
            time.sleep(0.5)
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  FILTER PANEL
    # ═══════════════════════════════════════════

    def open_filter_panel(self):
        """Open the filter panel via JS click."""
        try:
            divs = self.driver.find_elements(
                By.CSS_SELECTOR, "div[mattooltip='Filters']"
            )
            for div in divs:
                try:
                    btn = div.find_element(By.TAG_NAME, "button")
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def is_filter_panel_open(self):
        """Check if filter panel is visible."""
        return self.is_displayed(self.FILTER_PANEL, timeout=5)

    def close_filter_panel(self):
        """Close filter panel."""
        try:
            close_btns = self.driver.find_elements(
                By.CSS_SELECTOR, ".filter-panel .close-btn"
            )
            for btn in close_btns:
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.5)
                    return
        except Exception:
            pass

    def apply_filters(self):
        """Click Apply Filters button."""
        try:
            btns = self.driver.find_elements(By.CSS_SELECTOR, ".apply-btn")
            for btn in btns:
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    return True
        except Exception:
            pass
        return False

    def clear_filters(self):
        """Click Clear All button."""
        try:
            btns = self.driver.find_elements(By.CSS_SELECTOR, ".clear-btn")
            for btn in btns:
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.5)
                    return True
        except Exception:
            pass
        return False

    def get_filter_categories(self):
        """Get list of filter category names."""
        categories = []
        try:
            cats = self.driver.find_elements(
                By.CSS_SELECTOR, ".filter-category"
            )
            for cat in cats:
                text = cat.text.strip()
                if text:
                    categories.append(text)
        except Exception:
            pass
        return categories

    # ═══════════════════════════════════════════
    #  OVERLAY CLEANUP
    # ═══════════════════════════════════════════

    def _force_close_panels(self):
        """Remove leftover overlay panels via JS."""
        try:
            self.driver.execute_script("""
                var backdrops = document.querySelectorAll('.cdk-overlay-backdrop');
                backdrops.forEach(function(el) {
                    if (!el.classList.contains('cdk-overlay-dark-backdrop')) {
                        el.remove();
                    }
                });
                var panes = document.querySelectorAll('.cdk-overlay-pane');
                panes.forEach(function(el) {
                    if (!el.querySelector('mat-dialog-container')) {
                        el.remove();
                    }
                });
            """)
        except Exception:
            pass

    def force_close_form_popup(self):
        """Force close any form popup via JS removal."""
        log.info("Force close form popup")
        try:
            popup = self.driver.find_elements(
                By.CSS_SELECTOR, ".edit_pop_up"
            )
            if popup:
                icons = self.driver.find_elements(
                    By.CSS_SELECTOR, ".edit_pop_up button mat-icon"
                )
                for icon in icons:
                    if icon.text.strip().lower() == 'close':
                        btn = icon.find_element(By.XPATH, "./ancestor::button")
                        self.driver.execute_script("arguments[0].click();", btn)
                        time.sleep(0.5)
                        return
                cancel_btns = self.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
                )
                for btn in cancel_btns:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        time.sleep(0.5)
                        return
                log.info("Force close form popup: popup found but no close button")
            else:
                log.info("Close popup: no popup button found")
        except Exception:
            pass
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.edit_pop_up').forEach(function(el){el.remove();});
                document.querySelectorAll('.cdk-overlay-pane').forEach(function(el){el.remove();});
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el){el.remove();});
            """)
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  HIGH-LEVEL ACTION FLOWS
    # ═══════════════════════════════════════════

    def create_crop(self, data):
        """One-call crop creation.
        Returns dict: status ('PASSED'/'FAILED'), error, message, data
        """
        log.info("Creating crop record")
        result = {'status': 'FAILED', 'error': '', 'message': '', 'data': data}

        try:
            self.open_add_form()
            time.sleep(0.5)
            self.fill_crop_form(data)
            self._force_close_panels()
            self.submit()
            message = self.handle_success_alert(timeout=60)

            if message:
                result['message'] = message
                result['status'] = 'PASSED'
                log.info(f"Record created successfully: {data.get('name', '')}")
            else:
                result['error'] = 'No success alert appeared'

            self._cleanup_swal2()

        except Exception as e:
            result['error'] = str(e)
            log.error(f"Crop creation failed: {e}")

        return result

    def edit_crop(self, crop_name, updated_data, row_index=None):
        """One-call crop edit.
        Returns dict: status, error, message
        """
        log.info(f"Editing crop: {crop_name}")
        result = {'status': 'FAILED', 'error': '', 'message': ''}

        try:
            if not self.is_crop_in_table(crop_name):
                self.search_crop(crop_name)
                time.sleep(1)

            clicked = self.click_edit_button(crop_name=crop_name, row_index=row_index)
            if not clicked:
                result['error'] = f"Could not click Edit for: {crop_name}"
                return result
            time.sleep(1)

            if not self.is_edit_mode():
                result['error'] = 'Edit form did not open'
                return result

            self.fill_crop_form(updated_data)
            self._force_close_panels()
            self.click_update()
            message = self.handle_success_alert(timeout=60)

            if message:
                result['message'] = message
                result['status'] = 'PASSED'
                log.info(f"Record updated: {crop_name}")
            else:
                result['error'] = 'No success alert after update'

        except Exception as e:
            result['error'] = str(e)
            log.error(f"Crop edit failed: {e}")

        return result

    def view_crop(self, crop_name=None, row_index=None):
        """One-call crop view. Returns dict of field values or None."""
        log.info(f"Viewing crop: {crop_name}")

        try:
            if crop_name and not self.is_crop_in_table(crop_name):
                self.search_crop(crop_name)
                time.sleep(1)

            self.click_view_button(crop_name=crop_name, row_index=row_index)
            time.sleep(1)
            values = self.get_form_field_values()
            self.close_popup()
            time.sleep(0.5)
            return values

        except Exception as e:
            log.error(f"Crop view failed: {e}")
            return None

    def check_history(self, crop_name=None, row_index=None, search_text=None):
        """One-call history check.
        Returns dict: row_count, search_found, data, error
        """
        log.info(f"Checking history for: {crop_name}")
        result = {
            'row_count': 0,
            'search_found': False,
            'data': [],
            'error': ''
        }

        try:
            if crop_name and not self.is_crop_in_table(crop_name):
                self.search_crop(crop_name)
                time.sleep(1)

            clicked = self.click_history_button(
                crop_name=crop_name, row_index=row_index
            )
            if not clicked:
                result['error'] = 'Could not click History button'
                return result
            time.sleep(1)

            if not self.is_history_popup_open():
                result['error'] = 'History popup did not open'
                return result

            result['row_count'] = self.get_history_row_count()
            result['data'] = self.get_history_data()

            if search_text:
                result['search_found'] = self.search_in_history(search_text)

            self.close_history_popup()
            time.sleep(0.5)

        except Exception as e:
            result['error'] = str(e)
            log.error(f"History check failed: {e}")

        return result
