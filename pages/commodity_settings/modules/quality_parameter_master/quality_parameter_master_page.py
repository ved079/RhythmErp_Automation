"""
quality_parameter_master_page.py
--------------------------------
Page Object for RhythmERP -> Commodity Settings -> Quality Parameter Master.
Single-field screen: Name (text input, required).

URL: /#/dynamic-screens/Quality%20Parameter%20Master
3-dot menu per row: View and Edit only (BUG-005/006: no Delete, no History)
No success SweetAlert after create/update (BUG-004): form just closes silently.
Validation SweetAlert on empty submit: "Validation Failed" / "Please correct the highlighted fields"

Optimised (UOM gold standard v2):
- ZERO wait_seconds() calls — WebDriverWait with 0.1-0.3s polling
- JS clicks for ALL buttons — bypasses overlay issues
- offsetParent visibility checks instead of is_displayed()
- Single hard_refresh() instead of click_refresh + wait_seconds
- Fast SweetAlert2 handler: JS-based poll, dismiss via JS click
- 3-dot menu: td.cdk-column-actions button + text-based matching
- Single-line concatenated JS strings — NO triple-quoted Python strings
- Search with multi-selector fallback
- _force_close_panels() only removes .erp-action-menu and .cdk-overlay-backdrop
- SUBMIT_BUTTON xpath uses contains(@class,'popup-footer') NOT exact match
"""

import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL


class QualityParameterMasterPage(BasePage):
    """Page Object for Quality Parameter Master (1-field screen)."""

    PAGE_URL = RHYTHMERP_BASE_URL + "/#/dynamic-screens/Quality%20Parameter%20Master"

    # Locators — kept minimal for a 1-field screen
    ADD_BUTTON = ("css", "button.erp-add-btn")
    NAME_INPUT = ("css", "input[name='Name'], input[name='name'], input[formcontrolname='name']")
    SUBMIT_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]")
    UPDATE_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]")
    CANCEL_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    SEARCH_INPUT = ("css", "input#erpSearchInput")

    # ================================================================
    # Navigation
    # ================================================================

    def navigate_to_page(self):
        """Navigate to QPM page and wait for table ready."""
        log.info("Navigating to Quality Parameter Master page")
        self.driver.get(self.PAGE_URL)
        self._wait_for_page_ready()

    def hard_refresh(self):
        """Hard refresh and wait for table to appear."""
        log.info("Hard refreshing page")
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait for the main table to render (proves page is loaded)."""
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: d.find_elements("css selector", "table#excel-table")
            )
            log.info("Page ready (table found)")
        except Exception:
            try:
                WebDriverWait(self.driver, 3).until(
                    lambda d: d.find_elements("css selector", "button.erp-add-btn")
                )
                log.info("Page ready (add button found, no table)")
            except Exception:
                log.warning("Page ready check timed out")

    def is_page_loaded(self):
        """Check if the listing page has loaded via JS offsetParent."""
        return bool(self.driver.execute_script(
            "var t = document.querySelector('table#excel-table'); "
            "return t && t.offsetParent !== null;"
        ))

    # ================================================================
    # Overlay cleanup
    # ================================================================

    def _force_close_panels(self):
        """Remove only .erp-action-menu and .cdk-overlay-backdrop — NOT all .cdk-overlay-pane."""
        self.driver.execute_script(
            "document.querySelectorAll('.erp-action-menu').forEach(function(el){el.remove();}); "
            "document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el){el.remove();});"
        )

    # ================================================================
    # Add form
    # ================================================================

    def open_add_form(self):
        """Click the Add button via JS click, wait for popup to appear."""
        log.info("Opening Add form")
        try:
            result = self.driver.execute_script(
                "var btn = document.querySelector('button.erp-add-btn'); "
                "if(!btn){throw new Error('Add button not found');} "
                "btn.scrollIntoView({block:'center'}); btn.click(); return 'clicked';"
            )
            log.info("Add button clicked via JS: " + str(result))
        except Exception as e:
            log.warning("JS click failed, falling back to Selenium click: " + str(e))
            self.click_with_retry(self.ADD_BUTTON)
        # Wait for Name input to appear
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: d.execute_script(
                    "var el = document.querySelector("
                    "\"input[name='Name'], input[name='name'], input[formcontrolname='name']\"); "
                    "return el && el.offsetParent !== null;"
                )
            )
            log.info("Add form opened")
        except Exception:
            log.warning("Add form may not have opened — Name input not found")

    # ================================================================
    # Fill form
    # ================================================================

    def fill_form(self, data):
        """Fill the QPM form. Only field: name."""
        log.info("Filling QPM form: " + str(data))
        name = data.get("name")
        if name is not None:
            self._js_set_input("input[name='Name'], input[name='name'], input[formcontrolname='name']", str(name))
        log.info("QPM form filled")

    def _js_set_input(self, selector, value):
        """Set an input value via JS and dispatch Angular events."""
        self.driver.execute_script(
            "var el = document.querySelector(arguments[0]); "
            "if(!el){throw new Error('Input not found: '+arguments[0]);} "
            "el.value = arguments[1]; "
            "el.dispatchEvent(new Event('input',{bubbles:true})); "
            "el.dispatchEvent(new Event('change',{bubbles:true})); "
            "el.dispatchEvent(new Event('blur',{bubbles:true}));",
            selector, value
        )

    # ================================================================
    # Submit / Update / Cancel — all via JS click
    # ================================================================

    def submit(self):
        """Click Submit via JS click on popup-footer button."""
        log.info("Clicking Submit")
        self._js_click_popup_button("Submit")

    def click_update(self):
        """Click Update via JS click on popup-footer button."""
        log.info("Clicking Update")
        self._js_click_popup_button("Update")

    def cancel(self):
        """Click Cancel via JS click on popup-footer button.
        Gracefully handles case where no popup is open (no error thrown)."""
        log.info("Clicking Cancel")
        try:
            result = self.driver.execute_script(
                "var footers = document.querySelectorAll('div[class*=\"popup-footer\"]'); "
                "for(var i=0;i<footers.length;i++){"
                "  var buttons = footers[i].querySelectorAll('button'); "
                "  for(var j=0;j<buttons.length;j++){"
                "    if(buttons[j].textContent.trim().indexOf('Cancel')!==-1){"
                "      buttons[j].click(); return 'clicked_Cancel';"
                "    }"
                "  }"
                "} "
                "return 'no_cancel_found';"
            )
            log.info("Cancel result: " + str(result))
        except Exception as e:
            log.warning("Cancel click failed: " + str(e))

    def _js_click_popup_button(self, button_text):
        """Click a popup footer button (Submit/Update/Cancel) via JS — bypasses overlay issues."""
        try:
            result = self.driver.execute_script(
                "var footers = document.querySelectorAll('div[class*=\"popup-footer\"]'); "
                "for(var i=0;i<footers.length;i++){"
                "  var buttons = footers[i].querySelectorAll('button'); "
                "  for(var j=0;j<buttons.length;j++){"
                "    if(buttons[j].textContent.trim().indexOf(arguments[0])!==-1){"
                "      buttons[j].click(); return 'clicked_'+arguments[0];"
                "    }"
                "  }"
                "} "
                "throw new Error('Button \"'+arguments[0]+'\" not found in popup footer');",
                button_text
            )
            log.info("JS click " + button_text + ": " + str(result))
        except Exception as e:
            log.warning("JS click failed for " + button_text + ", falling back: " + str(e))
            if button_text == "Submit":
                self.click_with_retry(self.SUBMIT_BUTTON)
            elif button_text == "Update":
                self.click_with_retry(self.UPDATE_BUTTON)
            elif button_text == "Cancel":
                self.click_with_retry(self.CANCEL_BUTTON)

    def close_popup(self):
        """Close popup via X button (JS click) or Cancel fallback."""
        log.info("Closing popup")
        result = self.driver.execute_script(
            "var popup = document.querySelector('div.edit_pop_up, div.big-model, mat-dialog-container'); "
            "if(!popup){return 'no popup found';} "
            "var closeIcon = popup.querySelector('button[mat-icon-button] mat-icon'); "
            "if(closeIcon){var btn=closeIcon.closest('button'); if(btn){btn.click(); return 'clicked close';}} "
            "var footers = popup.querySelectorAll('div[class*=\"popup-footer\"] button'); "
            "for(var i=0;i<footers.length;i++){"
            "  if(footers[i].textContent.trim().indexOf('Cancel')!==-1){"
            "    footers[i].click(); return 'clicked Cancel';"
            "  }"
            "} "
            "return 'no close button found';"
        )
        log.info("Close popup result: " + str(result))

    # ================================================================
    # 3-dot menu: View / Edit (text-based matching, NOT icon-based)
    # ================================================================

    def _click_action_menu_item(self, qp_name, action_name):
        """Click a 3-dot menu item (View/Edit) for a specific row.
        Uses td.cdk-column-actions button trigger + text-based menu matching."""
        log.info("Clicking " + action_name + " via 3-dot menu for QP: " + qp_name)
        # Step 1: Find the row and click its 3-dot menu button
        self.driver.execute_script(
            "var table = document.querySelector('table#excel-table'); "
            "if(!table){throw new Error('Table not found');} "
            "var rows = table.querySelectorAll('tbody tr'); "
            "for(var i=0;i<rows.length;i++){"
            "  var cells = rows[i].querySelectorAll('td'); "
            "  for(var j=0;j<cells.length;j++){"
            "    if(cells[j].textContent.trim().indexOf(arguments[0])!==-1){"
            "      var menuBtn = rows[i].querySelector('td.cdk-column-actions button'); "
            "      if(!menuBtn){throw new Error('3-dot menu button not found');} "
            "      menuBtn.scrollIntoView({block:'center'}); menuBtn.click(); "
            "      return 'menu_opened';"
            "    }"
            "  }"
            "} "
            "throw new Error('QP \"'+arguments[0]+'\" not found in table');",
            qp_name
        )
        # Step 2: Wait for dropdown overlay to render
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(("css selector", ".cdk-overlay-container .cdk-overlay-pane"))
            )
        except Exception:
            pass
        # Step 3: Click the specific menu item by text
        result = self.driver.execute_script(
            "var overlay = document.querySelector('.cdk-overlay-container'); "
            "if(!overlay){throw new Error('CDK overlay not found after menu click');} "
            "var items = overlay.querySelectorAll('button, span, div'); "
            "for(var i=0;i<items.length;i++){"
            "  if(items[i].textContent.trim()===arguments[0]){"
            "    items[i].click(); return 'clicked_'+arguments[0];"
            "  }"
            "} "
            "for(var i=0;i<items.length;i++){"
            "  if(items[i].textContent.trim().toLowerCase().indexOf(arguments[0].toLowerCase())!==-1){"
            "    items[i].click(); return 'clicked_partial_'+arguments[0];"
            "  }"
            "} "
            "throw new Error('Menu item \"'+arguments[0]+'\" not found in dropdown');",
            action_name
        )
        log.info("Successfully clicked " + action_name + " for QP: " + qp_name)
        return result

    def click_view_button(self, qp_name):
        """Click View via 3-dot menu for a specific QP row.
        Searches first to ensure the QP is on the current page."""
        if not self.is_qp_in_table(qp_name):
            self.search_qp(qp_name)
        self._click_action_menu_item(qp_name, "View")
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(("css selector", ".popup-header h3"))
            )
        except Exception:
            pass

    def click_edit_button(self, qp_name):
        """Click Edit via 3-dot menu for a specific QP row.
        Searches first to ensure the QP is on the current page."""
        if not self.is_qp_in_table(qp_name):
            self.search_qp(qp_name)
        self._click_action_menu_item(qp_name, "Edit")
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: d.execute_script(
                    "var el = document.querySelector("
                    "\"input[name='Name'], input[name='name'], input[formcontrolname='name']\"); "
                    "return el && el.offsetParent !== null;"
                )
            )
        except Exception:
            pass

    # ================================================================
    # Form state checks — offsetParent instead of is_displayed()
    # ================================================================

    def is_add_form_open(self):
        """Check if the Name input is visible via offsetParent."""
        return bool(self.driver.execute_script(
            "var el = document.querySelector("
            "\"input[name='Name'], input[name='name'], input[formcontrolname='name']\"); "
            "return el && el.offsetParent !== null;"
        ))

    def is_form_closed(self):
        """Check if the form popup is no longer visible."""
        return not self.is_add_form_open()

    def is_view_mode(self):
        """Check if the Name input is disabled (view/read-only mode)."""
        return bool(self.driver.execute_script(
            "var el = document.querySelector("
            "\"input[name='Name'], input[name='name'], input[formcontrolname='name']\"); "
            "return el && el.offsetParent !== null && el.disabled;"
        ))

    def is_edit_mode(self):
        """Check if Update button is visible (edit mode)."""
        return bool(self.driver.execute_script(
            "var footers = document.querySelectorAll('div[class*=\"popup-footer\"]'); "
            "for(var i=0;i<footers.length;i++){"
            "  var buttons = footers[i].querySelectorAll('button'); "
            "  for(var j=0;j<buttons.length;j++){"
            "    if(buttons[j].textContent.trim().indexOf('Update')!==-1 && buttons[j].offsetParent !== null){"
            "      return true;"
            "    }"
            "  }"
            "} return false;"
        ))

    def get_form_field_values(self):
        """Read form field values. QPM has only one field: name."""
        name = self.driver.execute_script(
            "var el = document.querySelector("
            "\"input[name='Name'], input[name='name'], input[formcontrolname='name']\"); "
            "return el ? el.value : '';"
        ) or ""
        return {"name": name}

    def get_form_heading(self):
        """Read the heading text of the current popup."""
        try:
            return self.driver.execute_script(
                "var h = document.querySelector('.edit_pop_up h3, .big-model h3, mat-dialog-container h3'); "
                "return h ? h.textContent.trim() : '';"
            ) or ""
        except Exception:
            return ""

    # ================================================================
    # Mat-error text — JS-based parent walk
    # ================================================================

    def get_mat_error_text(self):
        """Get mat-error text below the Name input via JS parent walk."""
        try:
            result = self.driver.execute_script(
                "var input = document.querySelector("
                "\"input[name='Name'], input[name='name'], input[formcontrolname='name']\"); "
                "if(!input){return '';} "
                "var current = input; "
                "for(var steps=0;steps<20;steps++){"
                "  var errors = current.querySelectorAll('mat-error'); "
                "  if(errors.length>0){"
                "    var texts = []; "
                "    for(var i=0;i<errors.length;i++){"
                "      var t = errors[i].textContent.trim(); if(t) texts.push(t);"
                "    } "
                "    return texts.join(' | ');"
                "  } "
                "  current = current.parentElement; "
                "  if(!current || current===document.body) break;"
                "} return '';"
            )
            if result:
                log.warning("Validation errors found: " + result)
            return result or ""
        except Exception:
            return ""

    # ================================================================
    # SweetAlert2 — fast JS-based poll + JS dismiss
    # ================================================================

    def is_validation_alert_present(self, timeout=2):
        """Check if any SweetAlert validation popup is visible. Fast JS poll (0.15s)."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector("
                    "'.swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error'); "
                    "return el && el.offsetParent !== null;"
                )
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.15)
        return False

    def handle_validation_warning(self, timeout=3):
        """Dismiss validation SweetAlert via JS click on .swal2-confirm.
        Returns the alert title text, or ''."""
        log.info("Handling validation warning")
        if not self.is_validation_alert_present(timeout=timeout):
            return ""
        title = self.get_swal_title()
        # Dismiss via JS click
        self.driver.execute_script(
            "var btn = document.querySelector('.swal2-confirm'); "
            "if(btn){btn.click(); return 'clicked';} return 'not found';"
        )
        # Wait for SweetAlert to disappear
        try:
            WebDriverWait(self.driver, 2).until(
                EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
            )
        except Exception:
            pass
        log.info("Validation warning handled: " + title)
        return title

    def get_swal_title(self):
        """Read the SweetAlert2 title text if visible."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('#swal2-title'); "
                "return (el && el.offsetParent !== null) ? el.textContent.trim() : '';"
            ) or ""
        except Exception:
            return ""

    def get_swal_html_message(self):
        """Read the SweetAlert2 HTML container message if visible."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('.swal2-html-container'); "
                "return (el && el.offsetParent !== null) ? el.textContent.trim() : '';"
            ) or ""
        except Exception:
            return ""

    # ================================================================
    # Search — multi-selector fallback for search button
    # ================================================================

    def search_qp(self, qp_name):
        """Search for a QP by name. Returns True if found in results, False otherwise.
        Multi-selector fallback for search button."""
        log.info("Searching for QP: " + qp_name)
        # Step 1: Check if search input is already visible
        search_input = None
        try:
            el = self.driver.find_element("css selector", "input#erpSearchInput")
            rect = self.driver.execute_script(
                "var r = arguments[0].getBoundingClientRect(); "
                "return r.width > 0 && r.height > 0;", el
            )
            if rect:
                search_input = el
        except Exception:
            pass

        # Step 2: If not visible, click search button via JS (multi-selector fallback)
        if search_input is None:
            try:
                self.driver.execute_script(
                    "var btn = document.querySelector('button.search-btn') "
                    "|| document.querySelector('button[mattooltip=\"Search\"]') "
                    "|| document.querySelector('button[mattooltip=\"search\"]') "
                    "|| document.querySelector('.search-btn'); "
                    "if(!btn){return 'not_found';} "
                    "btn.scrollIntoView({block:'center'}); btn.click(); return 'clicked';"
                )
            except Exception as e:
                log.warning("Search button click failed: " + str(e))
                return False
            try:
                search_input = WebDriverWait(self.driver, 2).until(
                    EC.visibility_of_element_located(("css selector", "input#erpSearchInput"))
                )
            except Exception:
                log.warning("Search input did not become visible")
                return False

        # Step 3: Clear and set value via JS — single call
        self.driver.execute_script(
            "var el = arguments[0]; el.value = ''; "
            "el.dispatchEvent(new Event('input',{bubbles:true})); "
            "el.value = arguments[1]; "
            "el.dispatchEvent(new Event('input',{bubbles:true})); "
            "el.dispatchEvent(new Event('keyup',{bubbles:true})); "
            "el.dispatchEvent(new Event('change',{bubbles:true}));",
            search_input, qp_name
        )

        # Step 4: Click search button again to submit filter
        self.driver.execute_script(
            "var btn = document.querySelector('button.search-btn') "
            "|| document.querySelector('button[mattooltip=\"Search\"]'); "
            "if(btn){btn.click();}"
        )

        # Step 5: Wait for table to refresh, then check name via JS (no sleep)
        try:
            WebDriverWait(self.driver, 2).until(
                lambda d: d.find_elements("css selector", "table#excel-table tbody tr")
            )
        except Exception:
            pass

        # Step 6: Check if the searched name is actually in the filtered results
        found = self.is_qp_in_table(qp_name)
        log.info("Search completed for: " + qp_name + " found=" + str(found))
        return found

    # ================================================================
    # Table data helpers
    # ================================================================

    def verify_qp_exists(self, qp_name):
        """Verify QP name appears in table. Polls up to 8s via JS for slow renders."""
        log.info("Verifying QP '" + qp_name + "' exists in table")
        end_time = time.monotonic() + 8
        last_seen = []
        while time.monotonic() < end_time:
            try:
                result = self.driver.execute_script(
                    "var table = document.querySelector('table#excel-table'); "
                    "if(!table){return {found:false, rows:[]};} "
                    "var rows = table.querySelectorAll('tbody tr'); "
                    "var found = false; var rowTexts = []; "
                    "for(var i=0;i<rows.length;i++){"
                    "  var cells = rows[i].querySelectorAll('td'); "
                    "  var texts = []; "
                    "  for(var j=0;j<cells.length;j++){"
                    "    var t = cells[j].textContent.trim(); "
                    "    if(t){texts.push(t); if(t.indexOf(arguments[0])!==-1){found=true;}} "
                    "  } "
                    "  rowTexts.push(texts.join(' | ')); "
                    "} "
                    "return {found:found, rows:rowTexts};",
                    qp_name
                )
                if result and result.get('found'):
                    log.info("QP '" + qp_name + "' found in table")
                    return True
                last_seen = result.get('rows', []) if result else []
            except Exception:
                pass
            time.sleep(0.3)
        log.error("QP '" + qp_name + "' NOT found. Table: " + str(last_seen))
        raise AssertionError(
            "QP '" + qp_name + "' NOT found in table after search. Last rows: " + str(last_seen)
        )

    def is_qp_in_table(self, qp_name):
        """Check if a QP name exists in the current table view. Returns True/False.
        Pure JS — avoids slow Selenium round-trips per cell."""
        try:
            return bool(self.driver.execute_script(
                "var table = document.querySelector('table#excel-table'); "
                "if(!table){return false;} "
                "var rows = table.querySelectorAll('tbody tr'); "
                "for(var i=0;i<rows.length;i++){"
                "  var cells = rows[i].querySelectorAll('td'); "
                "  for(var j=0;j<cells.length;j++){"
                "    if(cells[j].textContent.trim().indexOf(arguments[0])!==-1){return true;} "
                "  }"
                "} return false;",
                qp_name
            ))
        except Exception:
            return False

    def get_all_qp_names(self):
        """Return all QP names from the current table view."""
        names = self.driver.execute_script(
            "var cells = document.querySelectorAll("
            "'table#excel-table tbody td.cdk-column-name, "
            "table#excel-table tbody td.mat-column-name, "
            "table#excel-table tbody td:nth-child(3)'); "
            "var result = []; "
            "for(var i=0;i<cells.length;i++){"
            "  var t = cells[i].textContent.trim(); if(t) result.push(t);"
            "} return result;"
        )
        return names or []

    def get_table_row_count(self):
        """Return the number of visible data rows in the table. Pure JS."""
        try:
            count = self.driver.execute_script(
                "var rows = document.querySelectorAll('table#excel-table tbody tr'); "
                "return rows ? rows.length : 0;"
            )
            return int(count) if count else 0
        except Exception:
            return 0

    # ================================================================
    # Search cleanup — needed by test C02, E02, S01-S03, S05
    # ================================================================

    def clear_search(self):
        """Clear the search input via JS and trigger table reload.
        Much faster than hard_refresh — no full page reload needed."""
        log.info("Clearing search via JS")
        try:
            self.driver.execute_script(
                "var el = document.querySelector('input#erpSearchInput'); "
                "if(!el){return 'no input';} "
                "el.value = ''; "
                "el.dispatchEvent(new Event('input',{bubbles:true})); "
                "el.dispatchEvent(new Event('change',{bubbles:true}));"
            )
            # Click search button to apply empty filter (shows all rows)
            self.driver.execute_script(
                "var btn = document.querySelector('button.search-btn') "
                "|| document.querySelector('button[mattooltip=\"Search\"]'); "
                "if(btn){btn.click();}"
            )
            # Wait briefly for table to reload
            try:
                WebDriverWait(self.driver, 2).until(
                    lambda d: d.find_elements("css selector", "table#excel-table tbody tr")
                )
            except Exception:
                pass
            log.info("Search cleared via JS")
        except Exception as e:
            log.warning("JS clear_search failed, falling back to hard_refresh: " + str(e))
            self.hard_refresh()

    # ================================================================
    # Filter panel — needed by test S04
    # ================================================================

    def open_filter_panel(self):
        """Open the filter panel via JS click on the filter button."""
        log.info("Opening filter panel")
        try:
            result = self.driver.execute_script(
                "var btn = document.querySelector('button.filter-btn') "
                "|| document.querySelector('button[mattooltip=\"Filter\"]') "
                "|| document.querySelector('button[mattooltip=\"filter\"]'); "
                "if(!btn){return 'not found';} "
                "btn.scrollIntoView({block:'center'}); btn.click(); return 'clicked';"
            )
            log.info("Filter panel result: " + str(result))
        except Exception as e:
            log.warning("Filter panel open failed: " + str(e))

    def close_filter_panel(self):
        """Close the filter panel via JS click on close/cancel."""
        log.info("Closing filter panel")
        try:
            result = self.driver.execute_script(
                "var btn = document.querySelector('button.filter-btn') "
                "|| document.querySelector('button[mattooltip=\"Filter\"]') "
                "|| document.querySelector('button[mattooltip=\"filter\"]'); "
                "if(btn){btn.click(); return 'clicked toggle';} "
                "var cancel = document.querySelector('.filter-panel button.cancel-btn'); "
                "if(cancel){cancel.click(); return 'clicked cancel';} "
                "return 'not found';"
            )
            log.info("Filter close result: " + str(result))
        except Exception as e:
            log.warning("Filter panel close failed: " + str(e))

    def is_filter_panel_open(self):
        """Check if the filter panel is currently visible."""
        try:
            return bool(self.driver.execute_script(
                "var panel = document.querySelector('.filter-panel, .erp-filter-panel'); "
                "return panel && panel.offsetParent !== null;"
            ))
        except Exception:
            return False

    # ================================================================
    # Column sort — needed by test S05
    # ================================================================

    def click_name_column_header(self):
        """Click the Name column header to toggle sort order via JS."""
        log.info("Clicking Name column header for sort")
        try:
            result = self.driver.execute_script(
                "var header = document.querySelector('table#excel-table th.cdk-column-name') "
                "|| document.querySelector('table#excel-table th.mat-column-name'); "
                "if(!header){return 'not found';} "
                "header.click(); return 'clicked';"
            )
            log.info("Name column header result: " + str(result))
        except Exception as e:
            log.warning("Name column header click failed: " + str(e))

    # ================================================================
    # View/Edit popup verification — needed by tests P03, P04
    # ================================================================

    def verify_view_popup_read_only(self):
        """Verify the View popup shows Name field as read-only.
        Returns True if read-only, False if editable.
        Single JS call — 4x faster than 4 separate execute_script calls."""
        log.info("Verifying View popup is read-only")
        try:
            result = self.driver.execute_script(
                "var el = document.querySelector("
                "\"input[name='Name'], input[name='name'], input[formcontrolname='name']\"); "
                "var disabled = el && el.disabled; "
                "var hasSubmit = false, hasUpdate = false, hasCancel = false; "
                "var footers = document.querySelectorAll('div[class*=\"popup-footer\"]'); "
                "for(var i=0;i<footers.length;i++){"
                "  var buttons = footers[i].querySelectorAll('button'); "
                "  for(var j=0;j<buttons.length;j++){"
                "    var txt = buttons[j].textContent.trim(); "
                "    if(txt.indexOf('Submit')!==-1){hasSubmit=true;} "
                "    if(txt.indexOf('Update')!==-1){hasUpdate=true;} "
                "    if(txt.indexOf('Cancel')!==-1){hasCancel=true;} "
                "  }"
                "} "
                "return {disabled:disabled, hasSubmit:hasSubmit, hasUpdate:hasUpdate, hasCancel:hasCancel};"
            )
            name_disabled = bool(result.get('disabled'))
            no_submit = not result.get('hasSubmit')
            no_update = not result.get('hasUpdate')
            has_cancel = result.get('hasCancel')
            is_readonly = name_disabled and no_submit and no_update and has_cancel
            log.info("View popup read-only check: disabled=" + str(name_disabled)
                     + " no_submit=" + str(no_submit) + " no_update=" + str(no_update)
                     + " has_cancel=" + str(has_cancel) + " => readonly=" + str(is_readonly))
            return is_readonly
        except Exception as e:
            log.warning("View popup read-only check failed: " + str(e))
            return False

    def verify_edit_popup_editable(self):
        """Verify the Edit popup shows Name field as editable with Update button.
        Returns True if editable, False if not.
        Single JS call — 2x faster than 2 separate execute_script calls."""
        log.info("Verifying Edit popup is editable")
        try:
            result = self.driver.execute_script(
                "var hasUpdate = false, hasCancel = false; "
                "var footers = document.querySelectorAll('div[class*=\"popup-footer\"]'); "
                "for(var i=0;i<footers.length;i++){"
                "  var buttons = footers[i].querySelectorAll('button'); "
                "  for(var j=0;j<buttons.length;j++){"
                "    var txt = buttons[j].textContent.trim(); "
                "    if(txt.indexOf('Update')!==-1){hasUpdate=true;} "
                "    if(txt.indexOf('Cancel')!==-1){hasCancel=true;} "
                "  }"
                "} "
                "return {hasUpdate:hasUpdate, hasCancel:hasCancel};"
            )
            has_update = result.get('hasUpdate')
            has_cancel = result.get('hasCancel')
            is_editable = has_update and has_cancel
            log.info("Edit popup editable check: has_update=" + str(has_update)
                     + " has_cancel=" + str(has_cancel) + " => editable=" + str(is_editable))
            return is_editable
        except Exception as e:
            log.warning("Edit popup editable check failed: " + str(e))
            return False

    # ================================================================
    # High-level CRUD workflows
    # ================================================================

    def create_quality_parameter(self, data):
        """Full create workflow: open form → fill → submit → handle response.
        Returns the name that was submitted.
        Optimised: checks form-closed FIRST (BUG-004 fast path), then alert."""
        name = data.get("name", "")
        log.info("Creating Quality Parameter: " + name)

        self.open_add_form()
        assert self.is_add_form_open(), "Add form did not open"

        self.fill_form(data)
        self.submit()

        # BUG-004: No success SweetAlert — form just closes silently
        # Check form-closed first (fast path), then alert (slow path)
        end_time = time.monotonic() + 3
        while time.monotonic() < end_time:
            if not self.is_add_form_open():
                break  # Form closed — valid create
            # Quick single-check for validation alert
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector("
                    "'.swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error'); "
                    "return el && el.offsetParent !== null;"
                )
                if visible:
                    warning = self.get_swal_title()
                    log.warning("Validation alert after submit: " + warning)
                    self.handle_validation_warning(timeout=1)
                    return name
            except Exception:
                pass
            time.sleep(0.15)

        log.info("Quality Parameter created: " + name)
        return name

    def edit_quality_parameter(self, qp_name, new_data):
        """Full edit workflow: navigate → search → click edit → fill → update.
        Returns the new name.
        Optimised: checks form-closed FIRST (BUG-004 fast path), then alert."""
        new_name = new_data.get("name", "")
        log.info("Editing QP '" + qp_name + "' -> '" + new_name + "'")

        self.navigate_to_page()
        self.search_qp(qp_name)
        self.click_edit_button(qp_name)
        assert self.is_edit_mode(), "Edit mode not activated"

        self.fill_form(new_data)
        self.click_update()

        # BUG-004: No success SweetAlert — form just closes silently
        # Check form-closed first (fast path), then alert
        end_time = time.monotonic() + 3
        while time.monotonic() < end_time:
            if not self.is_add_form_open():
                break  # Form closed — valid update
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector("
                    "'.swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error'); "
                    "return el && el.offsetParent !== null;"
                )
                if visible:
                    warning = self.get_swal_title()
                    log.warning("Validation alert after update: " + warning)
                    self.handle_validation_warning(timeout=1)
                    return new_name
            except Exception:
                pass
            time.sleep(0.15)

        log.info("Quality Parameter updated: " + new_name)
        return new_name
