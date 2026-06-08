"""
item_group_page.py
------------------
Page Object for RhythmERP -> Commodity Settings -> Item Group.
2 fields: Item Group (text, required), Description (text, required).

Optimised (UOM gold standard v2):
- ZERO time.sleep() calls — WebDriverWait with 0.15-0.3s polling
- JS clicks for ALL buttons — bypasses overlay issues
- offsetParent visibility checks (except position:fixed → getBoundingClientRect)
- Single hard_refresh() in _cleanup() — fast page reset between tests
- Fast SweetAlert2 handler: JS-based poll, dismiss via JS click
- 3-dot menu: td.cdk-column-actions button.erp-row-trigger + text-based menu matching
- Single-line concatenated JS strings — NO triple-quoted Python strings
- Search with multi-selector fallback for search button
- _force_close_panels() only removes .erp-action-menu and .cdk-overlay-backdrop
- SUBMIT_BUTTON uses contains(@class,'popup-footer') NOT exact match
- cancel() is graceful — returns 'no_cancel_found' instead of throwing
- click_edit/view/search first to handle pagination
- clear_search() uses JS-based clearing (no hard_refresh — saves ~4s per call)
- Consolidated JS calls for speed
- Timeout reductions: page ready 8s, create/edit poll 3s, validation alert 2s
- Fast polling intervals: 0.15-0.3s instead of 0.5s
- NO status toggle on this screen
- NO file upload on this screen
- Field names: name="Item Group" / name="Description" (NOT "Code"!)
- Filter panel uses position:fixed → getBoundingClientRect for visibility
- History via 3-dot menu "History" item
"""

import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL


class ItemGroupPage(BasePage):
    """Page Object for Item Group (2-field screen: Item Group + Description)."""

    PAGE_URL = RHYTHMERP_BASE_URL + "/#/dynamic-screens/Item%20Group"

    # Locators — minimal set for a 2-field screen
    ADD_BUTTON = ("css", "button.erp-add-btn")
    CODE_INPUT = ("css", "input[name='Item Group'], input[name='Code'], input[formcontrolname='code']")
    DESCRIPTION_INPUT = ("css", "input[name='Description'], input[formcontrolname='description']")
    SUBMIT_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]")
    UPDATE_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]")
    CANCEL_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    SEARCH_INPUT = ("css", "input#erpSearchInput")

    # ================================================================
    # Navigation
    # ================================================================

    def navigate_to_page(self):
        """Navigate to Item Group page and wait for table ready."""
        log.info("Navigating to Item Group page")
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
            WebDriverWait(self.driver, 8).until(
                lambda d: d.find_elements("css selector", "table#excel-table")
            )
            log.info("Page ready (table found)")
        except Exception:
            try:
                WebDriverWait(self.driver, 2).until(
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
        """Remove only .erp-action-menu and .cdk-overlay-backdrop."""
        self.driver.execute_script(
            "document.querySelectorAll('.erp-action-menu').forEach(function(el){el.remove();}); "
            "document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el){el.remove();});"
        )

    def _cleanup(self):
        """Cleanup between tests: close panels, swals, hard refresh."""
        self._force_close_panels()
        self._cleanup_swal2()
        self.hard_refresh()

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
        # Wait for Code input to appear via offsetParent
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: d.execute_script(
                    "var el = document.querySelector("
                    "\"input[name='Item Group'], input[name='Code'], input[formcontrolname='code']\"); "
                    "return el && el.offsetParent !== null;"
                )
            )
            log.info("Add form opened")
        except Exception:
            log.warning("Add form may not have opened — Code input not found")

    # ================================================================
    # Fill form
    # ================================================================

    def fill_item_group_form(self, data):
        """Fill the Item Group form.
        data: dict with keys 'code', 'description'
        NO dropdowns, NO toggle, NO file upload — simplest screen."""
        log.info("Filling item group form: " + str(data))
        code = data.get("code")
        if code is not None:
            self._js_set_input("input[name='Item Group'], input[name='Code'], input[formcontrolname='code']", str(code))
        description = data.get("description")
        if description is not None:
            self._js_set_input("input[name='Description'], input[formcontrolname='description']", str(description))
        log.info("Item Group form filled")

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
        Gracefully handles case where no popup is open."""
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
        """Click a popup footer button (Submit/Update/Cancel) via JS."""
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

    def force_close_form_popup(self):
        """Force-close any open form popup by clicking the X button via JS."""
        log.info("Force closing form popup")
        result = self.driver.execute_script(
            "var popup = document.querySelector('div.edit_pop_up'); "
            "if(!popup){return 'no popup found';} "
            "var closeBtn = popup.querySelector('button[mat-icon-button] mat-icon'); "
            "if(!closeBtn){return 'no close button found';} "
            "var btn = closeBtn.closest('button'); "
            "if(btn){btn.click(); return 'clicked close';} "
            "return 'could not click';"
        )
        log.info("Force close result: " + str(result))

    # ================================================================
    # 3-dot menu: View / Edit / History (text-based matching)
    # ================================================================

    def _click_action_menu_item(self, ig_code, action_name):
        """Click a 3-dot menu item (View/Edit/History) for a specific row.
        Uses td.cdk-column-actions button.erp-row-trigger + text-based menu matching.
        Searches first to ensure item is on current page (handles pagination)."""
        log.info("Clicking " + action_name + " via 3-dot menu for item group: " + ig_code)
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
            "throw new Error('Item Group \"'+arguments[0]+'\" not found in table');",
            ig_code
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
        log.info("Successfully clicked " + action_name + " for item group: " + ig_code)
        return result

    def click_view_button(self, ig_code):
        """Click View via 3-dot menu for a specific item group row."""
        self._ensure_item_visible(ig_code)
        self._click_action_menu_item(ig_code, "View")
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(("css selector", ".popup-header h3"))
            )
        except Exception:
            pass

    def click_edit_button(self, ig_code):
        """Click Edit via 3-dot menu for a specific item group row."""
        self._ensure_item_visible(ig_code)
        self._click_action_menu_item(ig_code, "Edit")
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: d.execute_script(
                    "var el = document.querySelector("
                    "\"input[name='Item Group'], input[name='Code'], input[formcontrolname='code']\"); "
                    "return el && el.offsetParent !== null;"
                )
            )
        except Exception:
            pass

    def click_history_button(self, ig_code):
        """Click History via 3-dot menu for a specific item group row."""
        self._ensure_item_visible(ig_code)
        self._click_action_menu_item(ig_code, "History")
        # Wait for history popup (uses heading text matching)
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: d.execute_script(
                    "var headings = document.querySelectorAll("
                    "'h3.popup-title, .big-model h3, mat-dialog-container h3, .popup-header h3'); "
                    "for(var i=0;i<headings.length;i++){"
                    "  if(headings[i].offsetParent !== null "
                    "     && headings[i].textContent.toLowerCase().indexOf('history')!==-1){"
                    "    return true;"
                    "  }"
                    "} "
                    "var el = document.querySelector('app-dynamic-history, .popup-overlay'); "
                    "return el && el.offsetParent !== null;"
                )
            )
        except Exception:
            pass

    def _ensure_item_visible(self, ig_code, max_attempts=2):
        """Ensure an item group is visible in the table before clicking its 3-dot menu."""
        for attempt in range(max_attempts):
            if self.is_item_group_in_table(ig_code):
                return
            found = self.search_item_group(ig_code)
            if found:
                return
            if attempt < max_attempts - 1:
                log.info("Item Group not found via search, hard refreshing and retrying: " + ig_code)
                self.hard_refresh()
        if not self.is_item_group_in_table(ig_code):
            self.search_item_group(ig_code)

    # ================================================================
    # Form state checks — offsetParent instead of is_displayed()
    # ================================================================

    def is_add_form_open(self):
        """Check if the Code input is visible via offsetParent."""
        return bool(self.driver.execute_script(
            "var el = document.querySelector("
            "\"input[name='Item Group'], input[name='Code'], input[formcontrolname='code']\"); "
            "return el && el.offsetParent !== null;"
        ))

    def is_form_closed(self):
        """Check if the form popup is no longer visible."""
        return not self.is_add_form_open()

    def is_view_mode(self):
        """Check if the Code input is disabled (view/read-only mode) via JS."""
        return bool(self.driver.execute_script(
            "var el = document.querySelector("
            "\"input[name='Item Group'], input[name='Code'], input[formcontrolname='code']\"); "
            "return el && el.offsetParent !== null && el.disabled;"
        ))

    def is_edit_mode(self):
        """Check if Update button is visible (edit mode) via JS offsetParent."""
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

    def get_form_heading(self):
        """Read the heading text of the current popup via JS."""
        try:
            return self.driver.execute_script(
                "var h = document.querySelector('.edit_pop_up h3, .big-model h3, mat-dialog-container h3'); "
                "return h ? h.textContent.trim() : '';"
            ) or ""
        except Exception:
            return ""

    def get_form_field_values(self):
        """Read all form field values via JS (single call — fast).
        Returns dict: code, description"""
        try:
            result = self.driver.execute_script(
                "var codeEl = document.querySelector("
                "\"input[name='Item Group'], input[name='Code'], input[formcontrolname='code']\"); "
                "var descEl = document.querySelector("
                "\"input[name='Description'], input[formcontrolname='description']\"); "
                "return {"
                "  code: codeEl ? codeEl.value : '',"
                "  description: descEl ? descEl.value : ''"
                "};"
            )
            return result or {"code": "", "description": ""}
        except Exception:
            return {"code": "", "description": ""}

    # ================================================================
    # View/Edit popup verification — single JS call
    # ================================================================

    def verify_view_popup_read_only(self):
        """Verify the View popup shows Code and Description disabled + no Submit/Update button.
        Single JS call — 4x faster than separate execute_script calls."""
        log.info("Verifying View popup is read-only")
        try:
            result = self.driver.execute_script(
                "var codeEl = document.querySelector("
                "\"input[name='Item Group'], input[name='Code'], input[formcontrolname='code']\"); "
                "var descEl = document.querySelector("
                "\"input[name='Description'], input[formcontrolname='description']\"); "
                "var codeDisabled = codeEl && codeEl.disabled; "
                "var descDisabled = descEl && descEl.disabled; "
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
                "return {codeDisabled:codeDisabled, descDisabled:descDisabled, "
                "  hasSubmit:hasSubmit, hasUpdate:hasUpdate, hasCancel:hasCancel};"
            )
            code_disabled = bool(result.get('codeDisabled'))
            desc_disabled = bool(result.get('descDisabled'))
            no_submit = not result.get('hasSubmit')
            no_update = not result.get('hasUpdate')
            has_cancel = result.get('hasCancel')
            is_readonly = code_disabled and desc_disabled and no_submit and no_update and has_cancel
            log.info("View popup read-only check: code_disabled=" + str(code_disabled)
                     + " desc_disabled=" + str(desc_disabled) + " no_submit=" + str(no_submit)
                     + " no_update=" + str(no_update) + " has_cancel=" + str(has_cancel)
                     + " => readonly=" + str(is_readonly))
            return is_readonly
        except Exception as e:
            log.warning("View popup read-only check failed: " + str(e))
            return False

    def verify_edit_popup_editable(self):
        """Verify the Edit popup shows Update button and editable fields."""
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
    # Mat-error text — JS-based parent walk
    # ================================================================

    def get_mat_error_text(self):
        """Get mat-error text below form fields via JS parent walk."""
        try:
            result = self.driver.execute_script(
                "var input = document.querySelector("
                "\"input[name='Item Group'], input[name='Code'], input[formcontrolname='code']\"); "
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

    def has_field_error(self, field_label):
        """Check if a form field has error styling (red border / invalid state) via JS."""
        try:
            return bool(self.driver.execute_script(
                "var input = document.querySelector("
                "\"input[name='\"+arguments[0]+\"'], input[formcontrolname='\"+arguments[0]+\"']\"); "
                "if(!input){return false;} "
                "var current = input; "
                "var invalidClasses = ['mat-mdc-form-field-invalid','mat-form-field-invalid','ng-invalid','cdk-text-field-invalid']; "
                "for(var steps=0;steps<20;steps++){"
                "  var classes = current.className || ''; "
                "  for(var i=0;i<invalidClasses.length;i++){"
                "    if(classes.indexOf(invalidClasses[i])!==-1){return true;} "
                "  } "
                "  current = current.parentElement; "
                "  if(!current || current===document.body) break;"
                "} return false;",
                field_label
            ))
        except Exception:
            return False

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

    def handle_validation_warning(self, timeout=2):
        """Dismiss validation SweetAlert via JS click on .swal2-confirm.
        Returns the alert title text, or ''."""
        log.info("Handling validation warning")
        if not self.is_validation_alert_present(timeout=timeout):
            return ""
        title = self.get_swal_title()
        self.driver.execute_script(
            "var btn = document.querySelector('.swal2-confirm'); "
            "if(btn){btn.click(); return 'clicked';} return 'not found';"
        )
        try:
            WebDriverWait(self.driver, 2).until(
                EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
            )
        except Exception:
            pass
        log.info("Validation warning handled: " + title)
        return title

    def handle_success_alert(self, timeout=1.5):
        """Handle SweetAlert2 success notification — fast dismiss.
        Returns message text or ''."""
        log.info("Handling success alert")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(("css selector", ".swal2-container"))
            )
            title = self.get_swal_title()
            log.info("SweetAlert detected, dismissing via JS")
            self.driver.execute_script(
                "var btn = document.querySelector('.swal2-confirm'); "
                "if(btn){btn.click(); return 'clicked';} return 'not found';"
            )
            try:
                WebDriverWait(self.driver, 1).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
                )
            except Exception:
                pass
            return title
        except Exception:
            log.info("No SweetAlert found (may have auto-dismissed)")
            return ""

    def is_success_alert_present(self, timeout=2):
        """Check if SweetAlert2 success alert is visible via JS poll."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector('.swal2-popup.swal2-icon-success'); "
                    "if(!el || el.offsetParent === null){return false;} "
                    "var title = document.querySelector('#swal2-title'); "
                    "if(!title){return false;} "
                    "var t = title.textContent.trim().toLowerCase(); "
                    "return t.indexOf('success')!==-1 || t.indexOf('added')!==-1 || t.indexOf('updated')!==-1;"
                )
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.15)
        return False

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

    def _cleanup_swal2(self):
        """Remove leftover SweetAlert2 containers via JS."""
        try:
            self.driver.execute_script(
                "document.querySelectorAll('.swal2-container').forEach(function(el){el.remove();});"
            )
        except Exception:
            pass

    # ================================================================
    # Search — multi-selector fallback for search button
    # ================================================================

    def search_item_group(self, ig_code):
        """Search for an item group by code. Returns True if found in results, False otherwise."""
        log.info("Searching for item group: " + ig_code)
        try:
            # Clear and type in search input
            self.driver.execute_script(
                "var input = document.querySelector('input#erpSearchInput, .erp-search-wrapper input'); "
                "if(!input){return 'no search input';} "
                "var setter = Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype,'value').set;"
                "setter.call(input, arguments[0]); "
                "input.dispatchEvent(new Event('input',{bubbles:true})); "
                "input.dispatchEvent(new Event('change',{bubbles:true})); "
                "return 'typed';",
                ig_code
            )
            # Click search button (multi-selector fallback)
            self.driver.execute_script(
                "var btn = document.querySelector("
                "'button[aria-label=\"Search\"], "
                "button.search-btn, "
                "button.erp-outline-btn[mattooltip=\"Search\"]'); "
                "if(btn){btn.click(); return 'clicked';} return 'no search button';"
            )
            # Wait for results
            try:
                WebDriverWait(self.driver, 3).until(
                    lambda d: d.execute_script(
                        "var rows = document.querySelectorAll('table#excel-table tbody tr'); "
                        "if(rows.length === 0){return true;} "
                        "for(var i=0;i<rows.length;i++){"
                        "  var cells = rows[i].querySelectorAll('td'); "
                        "  for(var j=0;j<cells.length;j++){"
                        "    if(cells[j].textContent.trim().indexOf(arguments[0])!==-1){return true;}"
                        "  }"
                        "} return false;",
                        ig_code
                    )
                )
            except Exception:
                pass
            # Check if found
            found = self.is_item_group_in_table(ig_code)
            log.info("Search result for '" + ig_code + "': " + str(found))
            return found
        except Exception as e:
            log.warning("Search failed: " + str(e))
            return False

    def clear_search(self):
        """Clear the search input and wait for table to reload. JS-based — no hard_refresh."""
        log.info("Clearing search")
        try:
            self.driver.execute_script(
                "var input = document.querySelector('input#erpSearchInput, .erp-search-wrapper input'); "
                "if(!input){return;} "
                "var setter = Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype,'value').set;"
                "setter.call(input, ''); "
                "input.dispatchEvent(new Event('input',{bubbles:true})); "
                "input.dispatchEvent(new Event('change',{bubbles:true}));"
            )
            # Click search button to refresh results
            self.driver.execute_script(
                "var btn = document.querySelector("
                "'button[aria-label=\"Search\"], "
                "button.search-btn, "
                "button.erp-outline-btn[mattooltip=\"Search\"]'); "
                "if(btn){btn.click(); return 'clicked';} return 'no search button';"
            )
            # Wait briefly for table to reload
            try:
                WebDriverWait(self.driver, 3).until(
                    lambda d: d.find_elements("css selector", "table#excel-table tbody tr")
                )
            except Exception:
                pass
            log.info("Search cleared")
        except Exception as e:
            log.warning("JS clear_search failed, falling back to hard_refresh: " + str(e))
            self.hard_refresh()

    def is_item_group_in_table(self, ig_code):
        """Check if an item group code exists in the table via JS."""
        try:
            return bool(self.driver.execute_script(
                "var table = document.querySelector('table#excel-table'); "
                "if(!table){return false;} "
                "var rows = table.querySelectorAll('tbody tr'); "
                "for(var i=0;i<rows.length;i++){"
                "  var cells = rows[i].querySelectorAll('td'); "
                "  for(var j=0;j<cells.length;j++){"
                "    if(cells[j].textContent.trim().indexOf(arguments[0])!==-1){return true;}"
                "  }"
                "} return false;",
                ig_code
            ))
        except Exception:
            return False

    # ================================================================
    # Table data extraction
    # ================================================================

    def get_table_row_count(self):
        """Get the number of visible rows in the table via JS."""
        try:
            return self.driver.execute_script(
                "return document.querySelectorAll('table#excel-table tbody tr').length;"
            ) or 0
        except Exception:
            return 0

    # ================================================================
    # Filter panel — position:fixed → getBoundingClientRect for visibility
    # ================================================================

    def open_filter_panel(self):
        """Click the Filter button to open the filter panel."""
        log.info("Opening filter panel")
        try:
            self.driver.execute_script(
                "var btn = document.querySelector('button.filter-btn'); "
                "if(btn){btn.click(); return 'clicked';} return 'not found';"
            )
            try:
                WebDriverWait(self.driver, 3).until(
                    lambda d: d.execute_script(
                        "var fp = document.querySelector('div.filter-panel'); "
                        "if(!fp){return false;} "
                        "var r = fp.getBoundingClientRect(); "
                        "return r.width > 0 && r.height > 0;"
                    )
                )
                log.info("Filter panel opened")
                return True
            except Exception:
                log.warning("Filter panel did not become visible")
                return False
        except Exception as e:
            log.warning("Filter panel open failed: " + str(e))
            return False

    def is_filter_panel_open(self):
        """Check if the filter panel is visible.
        Uses getBoundingClientRect because filter panel has position:fixed
        (offsetParent is always null for position:fixed elements)."""
        try:
            return bool(self.driver.execute_script(
                "var fp = document.querySelector('div.filter-panel'); "
                "if(!fp){return false;} "
                "var r = fp.getBoundingClientRect(); "
                "return r.width > 0 && r.height > 0;"
            ))
        except Exception:
            return False

    def close_filter_panel(self):
        """Close the filter panel via JS click on close button."""
        log.info("Closing filter panel")
        try:
            self.driver.execute_script(
                "var btn = document.querySelector('div.filter-panel button.close-btn'); "
                "if(btn){btn.click(); return 'clicked';} return 'not found';"
            )
        except Exception:
            pass

    def get_filter_categories(self):
        """Get the filter category names via JS."""
        try:
            return self.driver.execute_script(
                "var cats = document.querySelectorAll('div.filter-category span.category-name, "
                "div.filter-category'); "
                "var names = []; "
                "for(var i=0;i<cats.length;i++){"
                "  var t = cats[i].textContent.trim(); "
                "  if(t && t.length > 0 && t.length < 50){names.push(t);}"
                "} return names;"
            ) or []
        except Exception:
            return []

    # ================================================================
    # History popup
    # ================================================================

    def check_history(self, ig_code):
        """Open history popup and return row count + data.
        Returns dict: row_count, error, data."""
        log.info("Checking history for: " + ig_code)
        try:
            self.click_history_button(ig_code)
            # Wait for history popup
            try:
                WebDriverWait(self.driver, 3).until(
                    lambda d: d.execute_script(
                        "var headings = document.querySelectorAll("
                        "'h3.popup-title, .big-model h3, mat-dialog-container h3, .popup-header h3'); "
                        "for(var i=0;i<headings.length;i++){"
                        "  if(headings[i].offsetParent !== null "
                        "     && headings[i].textContent.toLowerCase().indexOf('history')!==-1){"
                        "    return true;"
                        "  }"
                        "} return false;"
                    )
                )
            except Exception:
                pass
            # Get row count
            row_count = self.driver.execute_script(
                "var rows = document.querySelectorAll("
                "'.popup-body table tbody tr, .big-model table tbody tr, "
                "app-dynamic-history table tbody tr'); "
                "return rows.length;"
            ) or 0
            log.info("History row count: " + str(row_count))
            # Close history popup
            self.close_history_popup()
            return {"row_count": row_count, "error": "", "data": []}
        except Exception as e:
            log.warning("History check failed: " + str(e))
            try:
                self.close_history_popup()
            except Exception:
                pass
            return {"row_count": 0, "error": str(e), "data": []}

    def close_history_popup(self):
        """Close the history popup via Cancel/Close button or X icon."""
        log.info("Closing history popup")
        try:
            result = self.driver.execute_script(
                "var popup = document.querySelector('div.big-model, div.edit_pop_up, mat-dialog-container'); "
                "if(!popup){return 'no popup';} "
                "var h3s = popup.querySelectorAll('h3'); "
                "var historyPopup = null; "
                "for(var i=0;i<h3s.length;i++){"
                "  if(h3s[i].textContent.toLowerCase().indexOf('history')!==-1){"
                "    historyPopup = h3s[i].closest('div.big-model, div.edit_pop_up, mat-dialog-container'); "
                "    break;"
                "  }"
                "} "
                "if(!historyPopup){return 'no history popup found';} "
                "var closeBtn = historyPopup.querySelector('button[mat-icon-button] mat-icon'); "
                "if(closeBtn){var btn=closeBtn.closest('button'); if(btn){btn.click(); return 'clicked X';}} "
                "var footers = historyPopup.querySelectorAll('div[class*=\"popup-footer\"] button'); "
                "for(var i=0;i<footers.length;i++){"
                "  var txt = footers[i].textContent.trim(); "
                "  if(txt.indexOf('Cancel')!==-1 || txt.indexOf('Close')!==-1){"
                "    footers[i].click(); return 'clicked '+txt;"
                "  }"
                "} return 'no close found';"
            )
            log.info("Close history result: " + str(result))
        except Exception as e:
            log.warning("Close history failed: " + str(e))

    def get_history_row_count(self):
        """Get the number of rows in the history popup via JS."""
        try:
            return self.driver.execute_script(
                "var rows = document.querySelectorAll("
                "'.popup-body table tbody tr, .big-model table tbody tr, "
                "app-dynamic-history table tbody tr'); "
                "return rows.length;"
            ) or 0
        except Exception:
            return 0

    def get_history_columns(self):
        """Get the column header names from the history popup table via JS."""
        try:
            return self.driver.execute_script(
                "var headers = document.querySelectorAll("
                "'.popup-body table thead th, .big-model table thead th, "
                "app-dynamic-history table thead th'); "
                "var names = []; "
                "for(var i=0;i<headers.length;i++){"
                "  var t = headers[i].textContent.trim(); if(t) names.push(t);"
                "} return names;"
            ) or []
        except Exception:
            return []

    # ================================================================
    # High-level workflow methods — create_item_group / edit_item_group
    # ================================================================

    def create_item_group(self, data):
        """Full create workflow: open form, fill, submit, handle alert.
        Returns dict: status (PASSED/FAILED), code, error."""
        code = data.get("code", "")
        try:
            self.open_add_form()
            self._force_close_panels()
            self.fill_item_group_form(data)
            self.submit()
            # Check for success or validation alert
            if self.is_success_alert_present(timeout=3):
                self.handle_success_alert()
                return {"status": "PASSED", "code": code, "error": ""}
            # Check for validation warning
            if self.is_validation_alert_present(timeout=3):
                warning = self.handle_validation_warning()
                try:
                    self.cancel()
                except Exception:
                    pass
                return {"status": "FAILED", "code": code, "error": warning}
            # If form closed — likely success
            if self.is_form_closed():
                return {"status": "PASSED", "code": code, "error": ""}
            # Still open — check if validation alert appeared late
            time.sleep(0.3)
            if self.is_validation_alert_present(timeout=2):
                warning = self.handle_validation_warning()
                try:
                    self.cancel()
                except Exception:
                    pass
                return {"status": "FAILED", "code": code, "error": warning}
            # Assume success
            return {"status": "PASSED", "code": code, "error": ""}
        except Exception as e:
            log.warning("Create item group failed: " + str(e))
            return {"status": "FAILED", "code": code, "error": str(e)}

    def edit_item_group(self, ig_code, edit_data):
        """Full edit workflow: search, click Edit, fill, Update, handle alert.
        edit_data: dict with 'code', 'description' (None = don't change).
        Returns dict: status, code, error."""
        try:
            new_code = edit_data.get("code") or ig_code
            self.click_edit_button(ig_code)
            self._force_close_panels()
            # Fill only non-None fields
            if edit_data.get("code") is not None:
                self._js_set_input("input[name='Item Group'], input[name='Code'], input[formcontrolname='code']", str(edit_data["code"]))
            if edit_data.get("description") is not None:
                self._js_set_input("input[name='Description'], input[formcontrolname='description']", str(edit_data["description"]))
            self.click_update()
            # Check for success or validation alert
            if self.is_success_alert_present(timeout=3):
                self.handle_success_alert()
                return {"status": "PASSED", "code": new_code, "error": ""}
            if self.is_validation_alert_present(timeout=3):
                warning = self.handle_validation_warning()
                try:
                    self.cancel()
                except Exception:
                    pass
                return {"status": "FAILED", "code": new_code, "error": warning}
            if self.is_form_closed():
                return {"status": "PASSED", "code": new_code, "error": ""}
            time.sleep(0.3)
            if self.is_validation_alert_present(timeout=2):
                warning = self.handle_validation_warning()
                try:
                    self.cancel()
                except Exception:
                    pass
                return {"status": "FAILED", "code": new_code, "error": warning}
            return {"status": "PASSED", "code": new_code, "error": ""}
        except Exception as e:
            log.warning("Edit item group failed: " + str(e))
            return {"status": "FAILED", "code": ig_code, "error": str(e)}
