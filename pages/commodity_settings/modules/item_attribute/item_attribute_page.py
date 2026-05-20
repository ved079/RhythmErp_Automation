"""
item_attribute_page.py
----------------------
Page Object Model for RhythmERP Item Attribute 1-5 screens.

Location: Commodity Settings > Commodity Attributes > Item Attribute1-5
URLs:
  /#/dynamic-screens/Item%20Attribute1  (has Base UOM)
  /#/dynamic-screens/Item%20Attribute2  (no Base UOM)
  /#/dynamic-screens/Item%20Attribute3  (no Base UOM)
  /#/dynamic-screens/Item%20Attribute4  (no Base UOM)
  /#/dynamic-screens/Item%20Attribute5  (no Base UOM)

FORM LAYOUT (Simple popup — NOT a stepper):

  Item Attribute 1:
    - Name            (text input,   required, name="Name", type="character")
    - Base UOM        (mat-select,   required, searchable)
    - Description     (text input,   optional, name="Description")
    - Status          (toggle switch, default ON = Active)
    [Cancel] [Submit]

  Item Attribute 2-5:
    - Name            (text input,   required, name="Name", type="character")
    - Description     (text input,   optional, name="Description")
    - Status          (toggle switch, default ON = Active)
    [Cancel] [Submit]

TABLE COLUMNS (main listing):
  - View / Edit / History   (action buttons per row)
  - Name / Base UOM (IA1) or Description (IA2-5) / Status

KNOWN BUGS (confirmed via ERP exploration):
  BUG-001 (HIGH)  : Duplicate Names ALLOWED (no uniqueness constraint)
  BUG-002 (HIGH)  : Browser-clicked mat-select values don't register in
                     Angular reactive form model — MUST use JS value-setter
  BUG-003 (MEDIUM): History popup shows "No data available" even for
                     existing records
  BUG-004 (HIGH)  : No maxlength attribute / no client-side length validation
                     on Name & Description fields. Server accepts 255 chars,
                     rejects 256+ but user can type freely with no warning.
  BUG-005 (MEDIUM): Generic "Failed to save record" error message when
                     Name/Description exceeds server max length, instead of
                     a specific error indicating which field and why.

POPUP TYPES (SweetAlert2):
  Type A — "Validation Failed" popup: Client-side required-field check.
           Title: "Validation Failed". Has .swal2-confirm button.
           Triggered by: Submit with empty required fields.
  Type B — "Failed to save record" popup: Server-side rejection.
           Title: "Failed to save record" (or similar).
           Triggered by: Name/Description exceeding 255 char server limit.
           Different DOM timing/structure — prone to StaleElementReferenceException
           if clicked via Selenium. MUST use JS click only.

KEY RULES:
  - NEVER use Keys.ESCAPE (closes entire popup form!)
  - JS clicks for Angular Material overlays
  - Name input uses capital 'N': name="Name"
  - Description input uses capital 'D': name="Description"
  - Only 1 toggle: Status (Active/Inactive)
  - Base UOM only exists on Item Attribute 1
  - Edit mode: all fields editable (Name IS editable, NOT readonly!)
  - View mode: all fields disabled, only Cancel button
  - Validation: SweetAlert2 "Validation Failed" + ng-invalid class
  - History column: cdk-column-archive (NOT mat-column-history)
  - ALL SweetAlert2 dismissals MUST use JS querySelector click to
    avoid StaleElementReferenceException (never Selenium .click())
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
IA_SUBMISSIONS = []


class ItemAttributePage(BasePage):
    """Page Object for Item Attribute 1-5 screens.
    Constructor takes attr_num (1-5) to determine which screen to use.
    """

    # Screen names used in URL
    SCREEN_NAMES = {
        1: "dynamic-screens/Item%20Attribute1",
        2: "dynamic-screens/Item%20Attribute2",
        3: "dynamic-screens/Item%20Attribute3",
        4: "dynamic-screens/Item%20Attribute4",
        5: "dynamic-screens/Item%20Attribute5",
    }

    # Display names for headings/logs
    DISPLAY_NAMES = {
        1: "Item Attribute1",
        2: "Item Attribute2",
        3: "Item Attribute3",
        4: "Item Attribute4",
        5: "Item Attribute5",
    }

    def __init__(self, driver, attr_num=1):
        """Initialize the page object for a specific Item Attribute screen.

        Args:
            driver: WebDriver instance
            attr_num: 1-5, determines which Item Attribute screen
        """
        super().__init__(driver)
        self.attr_num = attr_num
        screen_name = self.SCREEN_NAMES.get(attr_num, self.SCREEN_NAMES[1])
        self.PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/{screen_name}"
        self.display_name = self.DISPLAY_NAMES.get(attr_num, "Item Attribute1")
        self.has_base_uom = (attr_num == 1)

    # ==============================================================
    #  LOCATORS - Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    REFRESH_BUTTON = ("css", "buttonattooltip='Refresh']")

    # ==============================================================
    #  LOCATORS - Search bar
    # ==============================================================
    SEARCH_INPUT = ("css", "input#erpSearchInput, .erp-search-wrapper input")

    # ==============================================================
    #  LOCATORS - Table (main listing)
    # ==============================================================
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    TABLE_NAME_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-name, "
        "table#excel-table tbody td.mat-column-name",
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

    # Text inputs — NOTE: capital 'N' and 'D' in name attribute
    NAME_INPUT = (
        "css",
        "input[name='Name'], input[formcontrolname='name']",
    )
    DESCRIPTION_INPUT = (
        "css",
        "input[name='Description'], textarea[formcontrolname='description'], "
        "input[formcontrolname='description']",
    )

    # Base UOM dropdown (Item Attribute 1 ONLY)
    BASE_UOM_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Base UOM') or contains(.,'Base Uom')]"
        "/ancestor::mat-form-field//mat-select",
    )

    # Status toggle — only 1 toggle on these screens
    STATUS_TOGGLE = (
        "css",
        ".switch-wrapper.compact, .switch-wrapper compact",
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
        "//div[contains(@class,'popup-overlay')]"
        "[.//h3[contains(.,'History')]]",
    )
    HISTORY_TABLE_ROWS = (
        "css",
        ".popup-body table tbody tr",
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
    #  LOCATORS - Dropdown overlay
    # ==============================================================
    DROPDOWN_PANEL = (
        "css",
        "div.cdk-overlay-pane mat-select-panel, div[role='listbox']",
    )
    DROPDOWN_OPTIONS = (
        "css",
        "div[role='listbox'] mat-option, div[role='listbox'] [role='option']",
    )

    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Item Attribute listing page.
        Force-refreshes to clear leftover Angular state.
        """
        log.info(f"Navigating to {self.display_name} page...")
        self.navigate_to(self.PAGE_URL)
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the page is fully loaded."""
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table#excel-table")
                )
            )
            log.info(f"{self.display_name} table loaded")
        except TimeoutException:
            log.warning(f"{self.display_name} table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn")
                )
            )
            self.wait_seconds(2)
            log.info(f"{self.display_name} toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

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
        self.wait_seconds(0.2)

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
        log.info(f"Clicking ADD button on {self.display_name}...")
        self._wait_for_toolbar()

        # Strategy 1: divattooltip='ADD'] button
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
                    log.info(f"ADD form opened on {self.display_name}")
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
                            log.info(f"ADD form opened via mini-fab on {self.display_name}")
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
                log.info(f"ADD form opened via click_with_retry on {self.display_name}")
                return
        except Exception:
            pass

        raise Exception(f"ADD button not found or not clickable on {self.display_name}")

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
        """Check if the Add form is open by looking for Name input."""
        return self.is_displayed(self.NAME_INPUT, timeout=5)

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
        """Fill all fields on the Item Attribute popup form.

        Fill order: Name → Base UOM (IA1 only) → Description → Status toggle
        """
        log.info(f"Filling {self.display_name} form...")

        # 1. Name (required)
        if data.get("name"):
            self.type_text(self.NAME_INPUT, str(data["name"]), clear_first=True)

        # 2. Base UOM (Item Attribute 1 ONLY)
        if self.has_base_uom and "base_uom" in data:
            self._fill_dropdown_if_provided(
                data, "base_uom", self.BASE_UOM_SELECT, "Base UOM"
            )

        # 3. Description (optional)
        if data.get("description"):
            self.type_text(
                self.DESCRIPTION_INPUT, str(data["description"]), clear_first=True
            )

        # 4. Status toggle
        if "status" in data:
            self._set_status_toggle(bool(data["status"]))

        self._force_close_panels()
        log.info(f"{self.display_name} form filled")

    def _fill_dropdown_if_provided(self, data, key, select_locator, label_name):
        """Fill a dropdown if the key exists in data."""
        if key not in data:
            return  # Key not provided — skip this dropdown entirely

        value = data[key]
        if value:
            self._select_mat_option(select_locator, str(value))
        else:
            self._select_random_from_dropdown(select_locator, label_name)

    def _select_mat_option(self, select_locator, value_text):
        """Select an option from a mat-select dropdown by visible text.
        Uses JS click for Angular Material compatibility.
        """
        log.info(f"Selecting '{value_text}' from {select_locator}")
        try:
            # Click the mat-select to open the dropdown
            el = self.find_visible_element(select_locator, timeout=5)
            if el:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    el,
                )
                self.wait_seconds(0.5)

                # Wait for dropdown panel
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR, "div[role='listbox'] mat-option")
                        )
                    )
                except TimeoutException:
                    pass

                # Find and click the matching option
                options = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[role='listbox'] mat-option"
                )
                for opt in options:
                    try:
                        if opt.text.strip() == value_text and opt.is_displayed():
                            self.driver.execute_script("arguments[0].click();", opt)
                            self.wait_seconds(0.3)
                            log.info(f"Selected '{value_text}'")
                            return True
                    except Exception:
                        continue

                # If exact match not found, try contains
                for opt in options:
                    try:
                        if value_text in opt.text.strip() and opt.is_displayed():
                            self.driver.execute_script("arguments[0].click();", opt)
                            self.wait_seconds(0.3)
                            log.info(f"Selected '{opt.text.strip()}' (partial match)")
                            return True
                    except Exception:
                        continue

                log.warning(f"Option '{value_text}' not found in dropdown")
        except Exception as e:
            log.warning(f"Failed to select '{value_text}': {e}")
        finally:
            self._force_close_panels()
        return False

    def _select_random_from_dropdown(self, select_locator, label_name):
        """Select a random option from a mat-select dropdown."""
        log.info(f"Selecting random option from {label_name}")
        try:
            el = self.find_visible_element(select_locator, timeout=5)
            if el:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    el,
                )
                self.wait_seconds(0.5)

                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR, "div[role='listbox'] mat-option")
                        )
                    )
                except TimeoutException:
                    pass

                options = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[role='listbox'] mat-option"
                )
                visible_options = []
                for opt in options:
                    try:
                        if opt.is_displayed() and opt.text.strip():
                            visible_options.append(opt)
                    except Exception:
                        continue

                if visible_options:
                    import random
                    chosen = random.choice(visible_options)
                    chosen_text = chosen.text.strip()
                    self.driver.execute_script("arguments[0].click();", chosen)
                    self.wait_seconds(0.3)
                    log.info(f"Randomly selected '{chosen_text}' from {label_name}")
                    return True
                else:
                    log.warning(f"No visible options in {label_name} dropdown")
        except Exception as e:
            log.warning(f"Failed to select random from {label_name}: {e}")
        finally:
            self._force_close_panels()
        return False

    # ==============================================================
    #  Toggle switch helpers (Status toggle only)
    # ==============================================================

    def _set_status_toggle(self, desired_state):
        """Set the Status toggle to desired state.
        True = Active (ON), False = Inactive (OFF).
        Toggle uses .switch-wrapper compact with .state-label.on.active / .state-label.off.active
        """
        current_state = self._get_status_toggle_state()
        if current_state == desired_state:
            log.info(f"Status toggle already {'Active' if desired_state else 'Inactive'}")
            return

        log.info(f"Setting Status toggle to {'Active' if desired_state else 'Inactive'}...")
        try:
            toggle = self.driver.find_element(
                By.CSS_SELECTOR, ".switch-wrapper.compact, .switch-wrapper"
            )
            if toggle.is_displayed():
                self.driver.execute_script("arguments[0].click();", toggle)
                self.wait_seconds(0.3)

                # Verify state changed
                new_state = self._get_status_toggle_state()
                if new_state == desired_state:
                    log.info(f"Status toggle set to {'Active' if desired_state else 'Inactive'}")
                else:
                    log.warning(f"Status toggle may not have changed (current: {new_state})")
        except Exception as e:
            log.warning(f"Failed to set Status toggle: {e}")

    def _get_status_toggle_state(self):
        """Read the current Status toggle state.
        Returns True if Active (ON), False if Inactive (OFF).
        """
        try:
            on_label = self.driver.find_element(
                By.CSS_SELECTOR, ".switch-wrapper .state-label.on.active"
            )
            if on_label:
                return True  # Active
        except Exception:
            pass

        try:
            off_label = self.driver.find_element(
                By.CSS_SELECTOR, ".switch-wrapper .state-label.off.active"
            )
            if off_label:
                return False  # Inactive
        except Exception:
            pass

        return True  # Default assumption

    # ==============================================================
    #  Submit / Update / Cancel
    # ==============================================================

    def submit(self):
        """Click the Submit button (Create mode)."""
        log.info(f"Submitting {self.display_name} form...")
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
        log.info(f"Clicking Update on {self.display_name}...")
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
        """Click the Cancel button to close the form."""
        log.info("Clicking Cancel...")
        try:
            btn = self.find_visible_element(self.CANCEL_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(0.5)
                log.info("Cancel clicked")
                return
        except Exception:
            pass
        log.warning("Cancel button not found")

    # ==============================================================
    #  SweetAlert2 handlers
    #  IMPORTANT: All popup dismissals use JS querySelector click to
    #  avoid StaleElementReferenceException. Never use Selenium .click()
    #  on swal buttons — the DOM can re-render between find and click,
    #  especially for "Failed to save record" (Type B) popups.
    # ==============================================================

    def get_swal_title(self):
        """Get the SweetAlert2 title text."""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            if el.is_displayed():
                return el.text.strip()
        except Exception:
            pass
        return None

    def _dismiss_swal_confirm(self):
        """Dismiss a SweetAlert2 popup by clicking .swal2-confirm via JS.

        Uses document.querySelector with optional chaining so that if the
        element is not found or has been re-rendered, no exception is raised.
        This is the ONLY safe way to click swal buttons — Selenium .click()
        causes StaleElementReferenceException on server-side error popups.
        """
        self.wait_seconds(0.5)
        self.driver.execute_script(
            "document.querySelector('.swal2-confirm')?.click();"
        )
        self.wait_seconds(0.5)

        # Fallback: try all confirm buttons (rare: multiple swal instances)
        self.driver.execute_script("""
            document.querySelectorAll('.swal2-confirm').forEach(function(b) {
                try { b.click(); } catch(e) {}
            });
        """)

    def _cleanup_swal_containers(self):
        """Remove all leftover .swal2-container elements from the DOM."""
        try:
            WebDriverWait(self.driver, 3).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-container")
                )
            )
        except Exception:
            # Force remove if still lingering
            self.driver.execute_script("""
                document.querySelectorAll('.swal2-container')
                .forEach(function(el) { el.remove(); });
            """)

    def handle_success_alert(self, timeout=15):
        """Handle a SweetAlert2 success alert (Type A or Type B).

        Waits for the swal title to appear, reads it, dismisses via JS,
        and cleans up any leftover containers.
        Returns the title text, or '' if no alert appeared.
        """
        log.info(f"Waiting for success alert (timeout={timeout}s)...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            title = self.get_swal_title()
            log.info(f"SweetAlert2 title: {title}")

            # Dismiss via JS (avoids StaleElementReferenceException)
            self._dismiss_swal_confirm()
            self.wait_seconds(1)
            self._cleanup_swal_containers()

            return title or ""
        except TimeoutException:
            log.info("No success alert appeared within timeout")
            return ""

    def handle_validation_warning(self, timeout=10):
        """Handle a SweetAlert2 "Validation Failed" popup (Type A).

        This popup is triggered by client-side required-field validation.
        Title is typically "Validation Failed" with message
        "Please correct the highlighted fields".
        Dismisses via JS to avoid stale element issues.
        Returns the title text, or '' if no popup appeared.
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

        This popup appears when server-side validation rejects the data
        (e.g., Name/Description exceeds 255 char limit). Unlike
        'Validation Failed' (Type A) which is client-side, this is a
        server error with a generic message.

        Known bugs:
          BUG-004 (HIGH): No maxlength on inputs — user can type 256+ chars.
          BUG-005 (MEDIUM): Generic error instead of specific field/message.

        Uses JS click exclusively to avoid StaleElementReferenceException
        (Type B popup DOM timing is different from Type A).
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
            html_msg = ""
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

        # Fallback: use row index
        return self._click_action_button_by_index(row_index, 1)

    def click_history_button(self, item_name=None, row_index=0):
        """Click the History button on a table row.
        Note: Uses cdk-column-archive (NOT cdk-column-history).
        """
        log.info(f"Clicking History button (name={item_name}, row={row_index})...")
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
                    self.wait_seconds(1)
                    return True
            except Exception:
                pass

        # Fallback: use row index
        return self._click_action_button_by_index(row_index, 2)

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

        # Check if Name input is disabled
        try:
            name_input = self.driver.find_element(
                By.CSS_SELECTOR, "input[name='Name']"
            )
            if not name_input.is_enabled():
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
            h3s = self.driver.find_elements(By.CSS_SELECTOR, "h3")
            for h3 in h3s:
                if "History" in h3.text and h3.is_displayed():
                    return True
        except Exception:
            pass
        return False

    def close_history_popup(self):
        """Close the History popup."""
        log.info("Closing History popup...")
        try:
            # Find the Cancel button inside the history popup
            cancel_btns = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-footer button"
            )
            for btn in cancel_btns:
                if btn.text.strip() == "Cancel" and btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_seconds(0.5)
                    return
        except Exception:
            pass
        log.warning("Could not close History popup")

    def get_history_row_count(self):
        """Get the number of rows in the History popup table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-body table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    # ==============================================================
    #  Table data helpers
    # ==============================================================

    def get_table_row_count(self):
        """Count visible data rows in the table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def get_all_item_names(self):
        """List all Name values in the table."""
        names = []
        try:
            cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody td.cdk-column-name, "
                "table#excel-table tbody td.mat-column-name",
            )
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

    def search_item(self, search_text):
        """Search for an item by name."""
        log.info(f"Searching for: {search_text}")
        try:
            # Toggle search bar
            search_btn = self.driver.find_element(
                By.CSS_SELECTOR, "button.search-btn"
            )
            self.driver.execute_script("arguments[0].click();", search_btn)
            self.wait_seconds(0.5)

            # Set search input value
            search_input = self.driver.find_element(
                By.CSS_SELECTOR, "input#erpSearchInput"
            )
            # Use JS value setter for Angular reactivity
            self.driver.execute_script("""
                var input = arguments[0];
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeInputValueSetter.call(input, arguments[1]);
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            """, search_input, search_text)
            self.wait_seconds(0.3)

            # Press Enter
            search_input.send_keys(Keys.RETURN)
            self.wait_seconds(2)
            log.info(f"Search submitted for: {search_text}")
            return True
        except Exception as e:
            log.warning(f"Search failed: {e}")
            return False

    def get_dropdown_options(self, select_locator):
        """Get all option texts from a dropdown (for exploration/testing)."""
        options = []
        try:
            el = self.find_visible_element(select_locator, timeout=5)
            if el:
                self.driver.execute_script("arguments[0].click();", el)
                self.wait_seconds(0.5)

                opt_els = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[role='listbox'] mat-option"
                )
                for opt in opt_els:
                    try:
                        text = opt.text.strip()
                        if text:
                            options.append(text)
                    except Exception:
                        continue

                self._force_close_panels()
        except Exception as e:
            log.warning(f"Failed to get dropdown options: {e}")
        return options