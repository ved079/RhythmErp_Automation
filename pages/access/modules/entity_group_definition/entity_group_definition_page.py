"""
entity_group_definition_page.py
-------------------------------
Page Object Model for RhythmERP Entity Group Definition screen.

Location: Access > Entity Group Definition
URL:      /#/master-setup/entitygroupdefinition

FORM LAYOUT (single-page popup, no stepper):
  - Entity Group Name  (text input,   required, formcontrolname="entity_group")
  - Level              (number input, required, formcontrolname="level")

TABLE COLUMNS (visible):
  - Actions            (view + edit buttons per row)
  - Entity Group       (text column, cdk-column-entity_group)
  - Level              (number column, cdk-column-level)

KNOWN BUGS (documented at time of inspection):
  BUG-001 (HIGH)  : Spaces-only Entity Group Name accepted — creates blank record
  BUG-002 (HIGH)  : Exact duplicate name silently rejected with NO user feedback
  BUG-003 (HIGH)  : Case-insensitive duplicate NOT blocked ("agdi" alongside "Agdi")
  BUG-004 (MEDIUM): Negative Level values accepted (no min validation)
  BUG-005 (MEDIUM): Decimal Level values accepted (no step="1" validation)
  BUG-006 (LOW)   : Special characters in Entity Group Name accepted
  BUG-007 (LOW)   : No maxlength on Entity Group Name
  BUG-008 (LOW)   : No success SweetAlert after create/update

KEY RULES:
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - No dropdowns on this screen — no mat-select logic needed
  - No Delete option anywhere on this screen
  - No History / Audit trail feature on this screen
  - Popup uses .big-model container (not .edit_pop_up)
  - SweetAlert2 only appears on validation failure (not on success)
  - Table has no ID — use table.mat-mdc-table selector
  - Add button uses class "erp-add-btn" (not mattooltip)
  - URL is /master-setup/entitygroupdefinition (NOT dynamic-screens)
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
    StaleElementReferenceException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT

# Global list to track every submission for reporting
EGD_SUBMISSIONS = []


class EntityGroupDefinitionPage(BasePage):
    PAGE_URL = (
        f"{RHYTHMERP_BASE_URL}"
        "/#/master-setup/entitygroupdefinition"
    )

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = (
        "css",
        "button.erp-add-btn",
    )
    SEARCH_TOGGLE = (
        "css",
        "div[mattooltip='Search'] button, button[mattooltip='Search']",
    )
    REFRESH_BUTTON = (
        "css",
        "div[mattooltip='Refresh'] button, button[mattooltip='Refresh']",
    )
    MORE_BUTTON = (
        "css",
        "div[mattooltip='More'] button, button[mattooltip='More']",
    )
    FILTER_TOGGLE = (
        "css",
        "div[mattooltip='Filters'] button, button[mattooltip='Filters']",
    )

    # ==============================================================
    #  LOCATORS — Search bar
    # ==============================================================
    SEARCH_INPUT = (
        "css",
        "input[placeholder='Search'], .erp-search-wrapper input",
    )
    SEARCH_SUBMIT = (
        "css",
        "div[mattooltip='Search'] button",
    )

    # ==============================================================
    #  LOCATORS — Table (no ID on this screen!)
    # ==============================================================
    TABLE = ("css", "table.mat-mdc-table")
    TABLE_ROWS = ("css", "table.mat-mdc-table tbody tr")
    TABLE_ENTITY_GROUP_CELLS = (
        "css",
        "table.mat-mdc-table tbody td.cdk-column-entity_group, "
        "table.mat-mdc-table tbody td.mat-column-entity_group",
    )
    TABLE_LEVEL_CELLS = (
        "css",
        "table.mat-mdc-table tbody td.cdk-column-level, "
        "table.mat-mdc-table tbody td.mat-column-level",
    )
    NO_DATA_ROW = (
        "css",
        "table.mat-mdc-table tbody tr.mat-mdc-no-data-row, "
        "table.mat-mdc-table tbody td.no-data",
    )

    # ==============================================================
    #  LOCATORS — Add / Edit Form popup (.big-model)
    # ==============================================================
    FORM_POPUP = (
        "css",
        ".big-model, .edit_pop_up.override_edit_pop_up.popup-mode, "
        "mat-dialog-container",
    )
    FORM_HEADING = (
        "css",
        ".big-model h3, .edit_pop_up h3, "
        "mat-dialog-container h3, .mat-mdc-dialog-title",
    )

    ENTITY_GROUP_INPUT = (
        "css",
        "input[formcontrolname='entity_group']",
    )

    LEVEL_INPUT = (
        "css",
        "input[formcontrolname='level']",
    )

    SUBMIT_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Submit')]"
        " | //div[contains(@class,'big-model')]//button[contains(.,'Submit')]",
    )
    UPDATE_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Update')]"
        " | //div[contains(@class,'big-model')]//button[contains(.,'Update')]",
    )
    CANCEL_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Cancel')]"
        " | //div[contains(@class,'big-model')]//button[contains(.,'Cancel')]",
    )

    # ==============================================================
    #  LOCATORS — Row action buttons (parametrised by name)
    # ==============================================================
    VIEW_BUTTON = (
        "xpath",
        "//td[contains(@class,'cdk-column-entity_group') and "
        "contains(text(),'{egd_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-actions')]"
        "//button[.//i-feather[contains(@class,'tbl-fav-eye')]]",
    )
    EDIT_BUTTON = (
        "xpath",
        "//td[contains(@class,'cdk-column-entity_group') and "
        "contains(text(),'{egd_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-actions')]"
        "//button[.//i-feather[contains(@class,'tbl-fav-edit')]]",
    )

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
    #  LOCATORS — Fullscreen toggle
    # ==============================================================
    FULLSCREEN_BUTTON = (
        "css",
        ".big-model .popup-header button[mattooltip='Fullscreen'], "
        ".edit_pop_up .popup-header button[mattooltip='Fullscreen']",
    )
    FULLSCREEN_CONTAINER = ("css", ".big-model.fullscreen")

    # ==============================================================
    #  LOCATORS — Filter panel
    # ==============================================================
    FILTER_PANEL = ("css", ".filter-panel")
    FILTER_CLOSE = ("css", ".filter-panel .close-btn")
    FILTER_APPLY = ("css", ".filter-panel button.apply-btn, .filter-panel button.check")
    FILTER_CLEAR = ("css", ".filter-panel button.clear-btn, .filter-panel button.clear_all")

    # ==============================================================
    #  LOCATORS — Pagination
    # ==============================================================
    PAGINATION_NEXT = (
        "css",
        "button.mat-paginator-navigation-next, "
        "button[aria-label='Next page']",
    )
    PAGINATION_PREVIOUS = (
        "css",
        "button.mat-paginator-navigation-previous, "
        "button[aria-label='Previous page']",
    )
    PAGINATION_INFO = (
        "css",
        ".mat-mdc-paginator-range-label, "
        ".mat-paginator-range-label",
    )

    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Entity Group Definition listing page.
        Force-refreshes to clear leftover Angular state from previous tests.
        """
        log.info("Navigating to Entity Group Definition page...")
        self.navigate_to(self.PAGE_URL)
        # Force full page reload to clear Angular SPA state
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the EGD page is fully loaded:
        1. Table renders
        2. Toolbar buttons (including Add) are clickable
        """
        # Step 1: Wait for table
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table.mat-mdc-table")
                )
            )
            log.info("Entity Group Definition table loaded")
        except TimeoutException:
            log.warning("EGD table not found, page may be empty")

        # Step 2: Wait for Add button to render
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "button.erp-add-btn")
                )
            )
            self.wait_seconds(1)
            log.info("Entity Group Definition toolbar ready")
        except TimeoutException:
            log.warning("Add button not found, toolbar may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the EGD listing page has loaded."""
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
                except Exception:
                    pass
        except Exception:
            pass

        remaining = self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop), "
            "div.cdk-overlay-pane mat-option",
        )
        if remaining:
            self._force_close_panels()

    # ==============================================================
    #  Toolbar actions
    # ==============================================================

    def open_add_form(self):
        """Click the ADD (+) button to open the create form.
        Uses multiple strategies with proper waits.
        """
        log.info("Clicking ADD button...")
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

        # Strategy 2: Find button by text "Add Entity Group Definition"
        try:
            btns = self.driver.find_elements(By.CSS_SELECTOR, "button")
            for btn in btns:
                try:
                    if (
                        "add entity group definition" in btn.text.strip().lower()
                        and btn.is_displayed()
                    ):
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

        # Strategy 3: BasePage click_with_retry
        try:
            self.click_with_retry(self.ADD_BUTTON)
            self.wait_seconds(1.5)
            if self._is_form_popup_open():
                self._wait_for_form_content(timeout=5)
                log.info("ADD form opened via click_with_retry")
                return
        except Exception:
            pass

        raise Exception("ADD button not found or not clickable")

    def _wait_for_toolbar(self):
        """Wait for the toolbar and ADD button to be present."""
        for attempt in range(3):
            try:
                add_btn = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.erp-add-btn"
                )
                if add_btn and add_btn[0].is_displayed():
                    return
            except Exception:
                pass
            log.info(f"Waiting for toolbar... attempt {attempt + 1}/3")
            self.wait_seconds(2)
        log.warning("Toolbar wait exhausted, ADD button may not be ready")

    def _is_form_popup_open(self):
        """Quick check if any form popup is visible.
        EGD primarily uses .big-model container.
        """
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.big-model, "
                "div.edit_pop_up.override_edit_pop_up.popup-mode, "
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
        """Wait for form content (inputs) to render inside the popup."""
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.big-model input, "
                    "div.edit_pop_up input, "
                    "mat-dialog-container input, "
                    "div.cdk-overlay-container input"
                )
                for inp in inputs:
                    try:
                        if inp.is_displayed():
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
            self.wait_seconds(0.5)
        log.warning(f"Form content did not render within {timeout}s")
        self._debug_popup_info()
        return False

    def click_refresh(self):
        """Click the Refresh button."""
        log.info("Clicking Refresh button...")
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button[mattooltip='Refresh'], "
                "div[mattooltip='Refresh'] button"
            )
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].click();", btn
                        )
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
        """Fill the Entity Group Definition add/edit form.

        Args:
            data: dict with keys:
                - entity_group (str): Entity Group Name
                - level (int|str|float): Level value
        """
        log.info("Filling Entity Group Definition form...")

        # Entity Group Name
        if data.get("entity_group") is not None:
            self.type_text(
                self.ENTITY_GROUP_INPUT,
                str(data["entity_group"]),
                clear_first=True,
            )

        # Level — number input; use JS for reliable Angular binding
        if data.get("level") is not None and data.get("level") != "":
            level_str = str(data["level"])
            self.js_type_text(
                self.LEVEL_INPUT,
                level_str,
                clear_first=True,
            )

        self._force_close_panels()
        log.info("Entity Group Definition form filled")

    # ==============================================================
    #  Form submission & cancellation
    # ==============================================================

    def submit(self):
        """Click the Submit button on the Create form."""
        log.info("Submitting Entity Group Definition form...")
        self._force_close_panels()
        try:
            btn = self.find_visible_element(self.SUBMIT_BUTTON, timeout=5)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                btn,
            )
        except Exception:
            try:
                btn = self.driver.find_element(
                    By.XPATH,
                    "//div[contains(@class,'big-model')]//button[contains(.,'Submit')]",
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
            except Exception:
                self.click_with_retry(self.SUBMIT_BUTTON)
        self.wait_seconds(2)
        log.info("Submit clicked")

    def click_update(self):
        """Click the Update button on the Edit form."""
        log.info("Clicking Update button...")
        self._force_close_panels()
        try:
            btn = self.find_visible_element(self.UPDATE_BUTTON, timeout=5)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                btn,
            )
        except Exception:
            try:
                btn = self.driver.find_element(
                    By.XPATH,
                    "//div[contains(@class,'big-model')]//button[contains(.,'Update')]",
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
            except Exception:
                self.click_with_retry(self.UPDATE_BUTTON)
        self.wait_seconds(2)
        log.info("Update clicked")

    def cancel(self):
        """Click the Cancel button on the form."""
        log.info("Clicking Cancel button...")
        try:
            btn = self.find_visible_element(self.CANCEL_BUTTON, timeout=5)
            self.driver.execute_script("arguments[0].click();", btn)
        except Exception:
            try:
                btn = self.driver.find_element(
                    By.XPATH,
                    "//div[contains(@class,'big-model')]//button[contains(.,'Cancel')]",
                )
                self.driver.execute_script("arguments[0].click();", btn)
            except Exception:
                self.click_with_retry(self.CANCEL_BUTTON)
        self.wait_seconds(1)

    def close_popup(self):
        """Click the X (close) icon on the form header."""
        log.info("Closing popup via X button...")
        try:
            close_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model button mat-icon, "
                ".edit_pop_up button mat-icon, "
                "mat-dialog-container button mat-icon",
            )
            for icon in close_btns:
                try:
                    if (
                        icon.text.strip().lower() == "close"
                        and icon.is_displayed()
                    ):
                        self.driver.execute_script(
                            "arguments[0].closest('button').click();", icon
                        )
                        self.wait_seconds(0.5)
                        log.info("Popup closed via X button")
                        return
                except Exception:
                    continue
        except Exception:
            pass
        log.warning("X button not found, trying Cancel instead")
        self.cancel()

    # ==============================================================
    #  High-level create / edit / search helpers
    # ==============================================================

    def create_entity_group_definition(self, data):
        """Create an Entity Group Definition with given data.
        Returns the Entity Group Name used for creation.
        """
        name = data.get("entity_group", "")
        log.info(f"Creating Entity Group Definition: {name}, Level: {data.get('level')}")
        self.open_add_form()
        self.wait_seconds(1)
        assert self.is_add_form_open(), "Add form did not open"
        self.fill_form(data)
        self.submit()
        self.wait_seconds(2)
        # BUG-008: No success alert — just check if popup closed
        EGD_SUBMISSIONS.append({"name": name, "level": data.get("level"), "action": "create"})
        return name

    def edit_entity_group_definition(self, existing_name, new_data):
        """Edit an existing Entity Group Definition by name.
        Returns the new Entity Group Name.
        """
        new_name = new_data.get("entity_group", "")
        log.info(f"Editing '{existing_name}' -> '{new_name}'")
        self.click_edit_button(egd_name=existing_name)
        self.wait_seconds(1)
        self.fill_form(new_data)
        self.click_update()
        self.wait_seconds(2)
        EGD_SUBMISSIONS.append({"name": new_name, "level": new_data.get("level"), "action": "edit"})
        return new_name

    def search_entity_group(self, name):
        """Search for an Entity Group Definition by name.
        Uses the table-level Search input and button.
        Returns True if found in the table.
        """
        log.info(f"Searching for: {name}")
        # Clear any previous search
        try:
            search_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "input[placeholder='Search']"
            )
            for si in search_inputs:
                try:
                    if si.is_displayed():
                        self.driver.execute_script(
                            "var s = Object.getOwnPropertyDescriptor("
                            "  window.HTMLInputElement.prototype,'value').set;"
                            "s.call(arguments[0], arguments[1]);"
                            "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
                            si, name,
                        )
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # Click Search button
        try:
            search_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[mattooltip='Search'] button, button[mattooltip='Search']"
            )
            for btn in search_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        break
                except Exception:
                    continue
        except Exception:
            pass

        self.wait_seconds(3)
        found = self.is_entity_group_in_table(name)
        log.info(f"Search result for '{name}': {'Found' if found else 'Not found'}")
        return found

    def clear_search(self):
        """Clear the search input and refresh the table."""
        try:
            search_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "input[placeholder='Search']"
            )
            for si in search_inputs:
                try:
                    if si.is_displayed():
                        self.driver.execute_script(
                            "var s = Object.getOwnPropertyDescriptor("
                            "  window.HTMLInputElement.prototype,'value').set;"
                            "s.call(arguments[0], '');"
                            "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
                            si,
                        )
                        break
                except Exception:
                    continue
        except Exception:
            pass
        self.click_refresh()
        self.wait_seconds(2)

    # ==============================================================
    #  SweetAlert2 handlers
    # ==============================================================

    def handle_success_alert(self, timeout=EXPLICIT_WAIT):
        """Wait for SweetAlert2 success popup.
        NOTE (BUG-008): EGD does NOT show a success SweetAlert after
        create or update. The popup simply closes. Returns '' typically.
        """
        log.info("Waiting for success alert...")
        try:
            wait = WebDriverWait(self.driver, timeout)
            title_el = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            msg = title_el.text.strip()
            try:
                confirm = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".swal2-confirm")
                    )
                )
                try:
                    confirm.click()
                except Exception:
                    self.driver.execute_script(
                        "arguments[0].click();", confirm
                    )
                log.info(f"Success alert handled: {msg}")
            except Exception:
                self.driver.execute_script(
                    "document.querySelectorAll('.swal2-confirm')"
                    ".forEach(function(b){b.click();});"
                )
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, ".swal2-container")
                    )
                )
            except Exception:
                pass
            return msg
        except TimeoutException:
            log.info("No success alert appeared (expected for EGD — BUG-008)")
            return ""

    def handle_validation_warning(self, timeout=10):
        """Handle SweetAlert2 validation warning popup.
        Returns the warning title text, or ''.
        """
        log.info("Checking for validation warning...")
        try:
            wait = WebDriverWait(self.driver, timeout)
            title_el = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            msg = title_el.text.strip()
            html_msg = ""
            try:
                html_el = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-html-container"
                )
                html_msg = html_el.text.strip()
            except Exception:
                pass
            try:
                confirm = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-confirm"
                )
                self.driver.execute_script(
                    "arguments[0].click();", confirm
                )
            except Exception:
                pass
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, ".swal2-container")
                    )
                )
            except Exception:
                pass
            log.info(f"Validation warning handled: {msg} — {html_msg}")
            return msg
        except TimeoutException:
            return ""

    def is_validation_alert_present(self, timeout=5):
        """Check if any SweetAlert2 popup is currently visible."""
        return self.is_displayed(self.SWAL_TITLE, timeout=timeout)

    def get_swal_title(self):
        """Read the SweetAlert2 title text if visible."""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            if el.is_displayed():
                return el.text.strip()
        except Exception:
            pass
        return ""

    def get_swal_html_message(self):
        """Read the SweetAlert2 HTML container message if visible."""
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR, ".swal2-html-container"
            )
            if el.is_displayed():
                return el.text.strip()
        except Exception:
            pass
        return ""

    # ==============================================================
    #  Field-level error checking
    # ==============================================================

    def get_mat_error_text(self):
        """Get all visible mat-error texts from the form."""
        errors = self.driver.find_elements(
            By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
        )
        texts = []
        for e in errors:
            try:
                t = e.text.strip()
                if t:
                    texts.append(t)
            except StaleElementReferenceException:
                continue
        if texts:
            log.warning(f"Validation errors found: {texts}")
        return texts

    def has_field_error(self, field_label):
        """Check if a specific form field has a visible mat-error."""
        try:
            locator = (
                "xpath",
                f"//mat-label[contains(.,'{field_label}')]"
                "/ancestor::mat-form-field//mat-error",
            )
            return self.is_displayed(locator, timeout=3)
        except Exception:
            return False

    # ==============================================================
    #  Verification helpers
    # ==============================================================

    def is_add_form_open(self):
        """Check if the Add form popup is currently visible."""
        popup_visible = self._is_form_popup_open()
        name_input_visible = self.is_displayed(self.ENTITY_GROUP_INPUT, timeout=8)
        if name_input_visible:
            return True
        if popup_visible:
            try:
                popup_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.big-model input, "
                    "div.edit_pop_up input, "
                    "mat-dialog-container input"
                )
                for inp in popup_inputs:
                    try:
                        if inp.is_displayed():
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
        return False

    def is_form_closed(self):
        """Check if the form popup is no longer visible."""
        popup_gone = not self._is_form_popup_open()
        if popup_gone:
            return True
        return not self.is_displayed(self.ENTITY_GROUP_INPUT, timeout=3)

    def _debug_popup_info(self):
        """Log debug information about the current popup state."""
        try:
            all_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.big-model input, div.edit_pop_up input, "
                "mat-dialog-container input"
            )
            log.info(f"DEBUG: Found {len(all_inputs)} inputs in popup")
            for i, inp in enumerate(all_inputs):
                try:
                    log.info(
                        f"  Input[{i}]: "
                        f"tag={inp.tag_name}, "
                        f"name={inp.get_attribute('name')}, "
                        f"formcontrolname={inp.get_attribute('formcontrolname')}, "
                        f"type={inp.get_attribute('type')}, "
                        f"visible={inp.is_displayed()}"
                    )
                except Exception:
                    pass
        except Exception as e:
            log.warning(f"Debug popup info failed: {e}")

    def get_form_heading(self):
        """Read the heading text of the current popup."""
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR,
                ".big-model h3, .edit_pop_up h3, "
                "mat-dialog-container h3",
            )
            return el.text.strip()
        except Exception:
            return ""

    def is_view_mode(self):
        """Check if the currently open form is in View (read-only) mode."""
        try:
            entity_input = self.find_visible_element(self.ENTITY_GROUP_INPUT, timeout=5)
            return not entity_input.is_enabled()
        except Exception:
            return False

    def is_edit_mode(self):
        """Check if the currently open form is in Edit mode."""
        return self.is_displayed(self.UPDATE_BUTTON, timeout=5)

    def get_form_field_values(self):
        """Read all form field values from the currently open popup.
        Returns a dict with keys: entity_group, level.
        """
        values = {}

        try:
            entity_input = self.driver.find_element(
                By.CSS_SELECTOR,
                "input[formcontrolname='entity_group']",
            )
            val = entity_input.get_attribute("value") or ""
            if not val:
                try:
                    val = self.driver.execute_script(
                        "return arguments[0].value;", entity_input
                    ) or ""
                except Exception:
                    pass
            values["entity_group"] = val
        except Exception:
            values["entity_group"] = ""

        try:
            level_input = self.driver.find_element(
                By.CSS_SELECTOR,
                "input[formcontrolname='level']",
            )
            val = level_input.get_attribute("value") or ""
            if not val:
                try:
                    val = self.driver.execute_script(
                        "return arguments[0].value;", level_input
                    ) or ""
                except Exception:
                    pass
            values["level"] = val
        except Exception:
            values["level"] = ""

        return values

    # ==============================================================
    #  Table interactions
    # ==============================================================

    def get_table_row_count(self):
        """Return the number of visible data rows in the table."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table.mat-mdc-table tbody tr"
        )
        return len(rows)

    def get_all_entity_group_names(self):
        """Return a list of all Entity Group names in the current table view."""
        cells = self.driver.find_elements(
            By.CSS_SELECTOR,
            "table.mat-mdc-table tbody td.cdk-column-entity_group, "
            "table.mat-mdc-table tbody td.mat-column-entity_group",
        )
        names = []
        for cell in cells:
            try:
                text = cell.text.strip()
                if text:
                    names.append(text)
            except StaleElementReferenceException:
                continue
        return names

    def is_entity_group_in_table(self, name):
        """Check if an Entity Group with the given name appears in the table.
        Checks current page only — may need to search or paginate first.
        """
        names = self.get_all_entity_group_names()
        return any(name.strip().lower() in n.lower() for n in names)

    def verify_record_in_table(self, name, level=None):
        """Verify a record exists in the table by name (and optionally level).
        Returns True if found. Searches current page only.
        """
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table.mat-mdc-table tbody tr"
        )
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                row_texts = [c.text.strip() for c in cells]
                name_match = any(
                    name.strip().lower() in t.lower() for t in row_texts
                )
                if name_match:
                    if level is not None:
                        level_str = str(level)
                        level_match = any(
                            level_str == t for t in row_texts
                        )
                        if level_match:
                            return True
                    else:
                        return True
            except StaleElementReferenceException:
                continue
        return False

    def click_view_button(self, egd_name):
        """Click the View (eye) button for a specific Entity Group row."""
        log.info(f"Clicking View button for: {egd_name}")
        locator = (
            "xpath",
            f"//td[contains(@class,'cdk-column-entity_group') and "
            f"contains(text(),'{egd_name}')]"
            f"/ancestor::tr//td[contains(@class,'cdk-column-actions')]"
            f"//button[.//i-feather[contains(@class,'tbl-fav-eye')]]",
        )
        try:
            btn = self.find_visible_element(locator, timeout=5)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                btn,
            )
            self.wait_seconds(2)
        except Exception:
            # Fallback: find by icon
            try:
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, "table.mat-mdc-table tbody tr"
                )
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        for cell in cells:
                            if egd_name.lower() in cell.text.strip().lower():
                                eye_btn = row.find_element(
                                    By.CSS_SELECTOR,
                                    "button .tbl-fav-eye"
                                )
                                self.driver.execute_script(
                                    "arguments[0].closest('button').click();",
                                    eye_btn,
                                )
                                self.wait_seconds(2)
                                return
                    except Exception:
                        continue
            except Exception:
                pass
            log.warning(f"View button not found for: {egd_name}")

    def click_edit_button(self, egd_name):
        """Click the Edit (pencil) button for a specific Entity Group row."""
        log.info(f"Clicking Edit button for: {egd_name}")
        locator = (
            "xpath",
            f"//td[contains(@class,'cdk-column-entity_group') and "
            f"contains(text(),'{egd_name}')]"
            f"/ancestor::tr//td[contains(@class,'cdk-column-actions')]"
            f"//button[.//i-feather[contains(@class,'tbl-fav-edit')]]",
        )
        try:
            btn = self.find_visible_element(locator, timeout=5)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                btn,
            )
            self.wait_seconds(2)
        except Exception:
            # Fallback: find by icon
            try:
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, "table.mat-mdc-table tbody tr"
                )
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        for cell in cells:
                            if egd_name.lower() in cell.text.strip().lower():
                                edit_btn = row.find_element(
                                    By.CSS_SELECTOR,
                                    "button .tbl-fav-edit"
                                )
                                self.driver.execute_script(
                                    "arguments[0].closest('button').click();",
                                    edit_btn,
                                )
                                self.wait_seconds(2)
                                return
                    except Exception:
                        continue
            except Exception:
                pass
            log.warning(f"Edit button not found for: {egd_name}")

    # ==============================================================
    #  Filter panel
    # ==============================================================

    def open_filter_panel(self):
        """Open the filter panel."""
        log.info("Opening filter panel...")
        try:
            self.click_with_retry(self.FILTER_TOGGLE)
            self.wait_seconds(1)
        except Exception:
            log.warning("Filter toggle button not found")

    def is_filter_panel_open(self):
        """Check if the filter panel is currently visible."""
        return self.is_displayed(self.FILTER_PANEL, timeout=5)

    def close_filter_panel(self):
        """Close the filter panel."""
        log.info("Closing filter panel...")
        try:
            close_btn = self.driver.find_element(
                By.CSS_SELECTOR, ".filter-panel .close-btn"
            )
            self.driver.execute_script("arguments[0].click();", close_btn)
            self.wait_seconds(1)
        except Exception:
            self._force_close_panels()

    # ==============================================================
    #  Pagination
    # ==============================================================

    def go_to_next_page(self):
        """Navigate to the next page of the table."""
        try:
            next_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button[mattooltip='Next page'], "
                "button.mat-paginator-navigation-next",
            )
            for btn in next_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].click();", btn
                        )
                        self.wait_seconds(2)
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def go_to_first_page(self):
        """Navigate to the first page of the table."""
        try:
            first_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button[mattooltip='First page'], "
                "button.mat-paginator-navigation-first",
            )
            for btn in first_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].click();", btn
                        )
                        self.wait_seconds(2)
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False
