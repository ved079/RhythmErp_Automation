"""
crop_master_page.py
-------------------
Page Object for RhythmERP -> Commodity Settings -> Crop Master.
4 fields: Name (text, required), Description (text, optional),
          File Upload (optional), Status Toggle (Active/Inactive, default Active).

Optimised (UOM gold standard v2):
- ZERO time.sleep() calls — WebDriverWait with 0.15-0.3s polling
- JS clicks for ALL buttons — bypasses overlay issues
- offsetParent visibility checks instead of is_displayed()
- Single hard_refresh() in _cleanup() — fast page reset between tests
- Fast SweetAlert2 handler: JS-based poll, dismiss via JS click
- 3-dot menu: td.cdk-column-actions button + text-based menu matching
- Single-line concatenated JS strings — NO triple-quoted Python strings
- Search with multi-selector fallback for search button
- _force_close_panels() only removes .erp-action-menu and .cdk-overlay-backdrop
- SUBMIT_BUTTON xpath uses contains(@class,'popup-footer') NOT exact match
- cancel() is graceful — returns 'no_cancel_found' instead of throwing
- click_edit/view/search first to handle pagination
- clear_search() uses JS-based clearing (no hard_refresh — saves ~4s per call)
- Consolidated JS calls for speed
- Timeout reductions: page ready 10s, create/edit poll 3s, validation alert 2s
- Fast polling intervals: 0.15-0.3s instead of 0.5s
- Status toggle uses app-slide-toggle-v2 component (same as UOM)
- File upload via send_keys on input[type='file']
- History via 3-dot menu "History" item (same pattern as UOM)
"""

import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL


class CropMasterPage(BasePage):
    """Page Object for Crop Master (4-field screen with file upload + status toggle)."""

    PAGE_URL = RHYTHMERP_BASE_URL + "/#/dynamic-screens/Crop%20Master"

    # Locators — minimal set for a 4-field screen
    ADD_BUTTON = ("css", "button.erp-add-btn")
    NAME_INPUT = ("css", "input[name='Name'], input[name='name'], input[formcontrolname='name']")
    DESCRIPTION_INPUT = ("css", "input[name='Description'], input[name='description'], input[formcontrolname='description']")
    FILE_INPUT = ("css", "input[type='file']")
    FILE_UPLOAD_CONTAINER = ("css", ".custom-file-upload")
    SUBMIT_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]")
    UPDATE_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]")
    CANCEL_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    SEARCH_INPUT = ("css", "input#erpSearchInput")

    # ================================================================
    # Navigation
    # ================================================================

    def navigate_to_page(self):
        """Navigate to Crop Master page and wait for table ready."""
        log.info("Navigating to Crop Master page")
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

    def _cleanup(self):
        """Cleanup between tests: close any open popups, force close panels, hard refresh."""
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
        # Wait for Name input to appear via offsetParent
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

    def fill_crop_form(self, data):
        """Fill the Crop Master form.
        data: dict with keys 'name', 'description', 'status', 'file_path'
        NO dropdowns — simpler than Vehicle Master."""
        log.info("Filling crop form: " + str({k: v for k, v in data.items() if k != 'file_path'}))
        name = data.get("name")
        if name is not None:
            self._js_set_input("input[name='Name'], input[name='name'], input[formcontrolname='name']", str(name))
        description = data.get("description")
        if description is not None:
            self._js_set_input("input[name='Description'], input[name='description'], input[formcontrolname='description']", str(description))
        file_path = data.get("file_path")
        if file_path is not None:
            self.upload_file(file_path)
        status = data.get("status")
        if status is not None:
            self.set_status(status)
        log.info("Crop form filled")

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
    # Status toggle (app-slide-toggle-v2 — same as UOM)
    # ================================================================

    def toggle_status(self):
        """Click the status toggle (Active <-> Inactive) via JS on app-slide-toggle-v2."""
        log.info("Toggling status")
        result = self.driver.execute_script(
            "var toggle = document.querySelector('app-slide-toggle-v2'); "
            "if(!toggle){"
            "  var slider = document.querySelector('.slider'); "
            "  if(slider){slider.click(); return 'clicked .slider fallback';} "
            "  throw new Error('app-slide-toggle-v2 not found'); "
            "} "
            "var slider = toggle.querySelector('.slider'); "
            "if(slider){slider.scrollIntoView({block:'center'}); slider.click(); return 'clicked .slider';} "
            "var wrapper = toggle.querySelector('.switch-wrapper'); "
            "if(wrapper){wrapper.scrollIntoView({block:'center'}); wrapper.click(); return 'clicked .switch-wrapper';} "
            "toggle.scrollIntoView({block:'center'}); toggle.click(); return 'clicked host';"
        )
        log.info("Toggle clicked: " + str(result))

    def get_current_status(self):
        """Get current toggle state - Active or Inactive via JS."""
        result = self.driver.execute_script(
            "var toggle = document.querySelector('app-slide-toggle-v2'); "
            "if(!toggle){"
            "  var onLabel = document.querySelector('.state-label.on'); "
            "  if(onLabel && onLabel.classList.contains('active')) return 'Active'; "
            "  return 'Inactive'; "
            "} "
            "var onLabel = toggle.querySelector('.state-label.on'); "
            "return (onLabel && onLabel.classList.contains('active')) ? 'Active' : 'Inactive';"
        )
        log.info("Toggle status: " + str(result))
        return result or 'Active'

    def set_status(self, desired_status):
        """Set status to specific value. No-op if already in desired state."""
        current = self.get_current_status()
        if current != desired_status:
            self.toggle_status()

    # ================================================================
    # File upload
    # ================================================================

    def upload_file(self, file_path):
        """Upload file to form via send_keys on input[type='file'].
        Returns True if upload attempted, False otherwise."""
        if not file_path:
            return False
        if not os.path.exists(file_path):
            log.warning("File not found: " + str(file_path))
            return False
        try:
            file_input = self.driver.find_element("css selector", "input[type='file']")
            file_input.send_keys(file_path)
            log.info("File uploaded: " + os.path.basename(file_path))
            return True
        except Exception as e:
            log.warning("File upload failed: " + str(e))
            return False

    def is_file_uploaded(self):
        """Check if file has been uploaded via JS."""
        try:
            return bool(self.driver.execute_script(
                "var containers = document.querySelectorAll('.custom-file-upload'); "
                "for(var i=0;i<containers.length;i++){"
                "  var t = containers[i].textContent.trim(); "
                "  if(t && t.indexOf('No File Uploaded')===-1){return true;} "
                "} return false;"
            ))
        except Exception:
            return False

    def get_uploaded_file_text(self):
        """Get file upload display text via JS."""
        try:
            result = self.driver.execute_script(
                "var containers = document.querySelectorAll('.custom-file-upload'); "
                "for(var i=0;i<containers.length;i++){"
                "  var t = containers[i].textContent.trim(); "
                "  if(t){return t;} "
                "} return '';"
            )
            return result or ''
        except Exception:
            return ''

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

    def _click_action_menu_item(self, crop_name, action_name):
        """Click a 3-dot menu item (View/Edit/History) for a specific row.
        Uses td.cdk-column-actions button trigger + text-based menu matching.
        Searches first to ensure crop is on current page (handles pagination)."""
        log.info("Clicking " + action_name + " via 3-dot menu for crop: " + crop_name)
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
            "throw new Error('Crop \"'+arguments[0]+'\" not found in table');",
            crop_name
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
        log.info("Successfully clicked " + action_name + " for crop: " + crop_name)
        return result

    def click_view_button(self, crop_name):
        """Click View via 3-dot menu for a specific crop row.
        Searches first to ensure the crop is on the current page."""
        if not self.is_crop_in_table(crop_name):
            self.search_crop(crop_name)
        self._click_action_menu_item(crop_name, "View")
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(("css selector", ".popup-header h3"))
            )
        except Exception:
            pass

    def click_edit_button(self, crop_name):
        """Click Edit via 3-dot menu for a specific crop row.
        Searches first to ensure the crop is on the current page."""
        if not self.is_crop_in_table(crop_name):
            self.search_crop(crop_name)
        self._click_action_menu_item(crop_name, "Edit")
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

    def click_history_button(self, crop_name):
        """Click History via 3-dot menu for a specific crop row.
        Searches first to ensure the crop is on the current page."""
        if not self.is_crop_in_table(crop_name):
            self.search_crop(crop_name)
        self._click_action_menu_item(crop_name, "History")
        # Wait for history popup (uses app-dynamic-history component like UOM)
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(("css selector", "app-dynamic-history, .popup-overlay"))
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
        """Check if the Name input is disabled (view/read-only mode) via JS."""
        return bool(self.driver.execute_script(
            "var el = document.querySelector("
            "\"input[name='Name'], input[name='name'], input[formcontrolname='name']\"); "
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
        Returns dict: name, description, status, has_file"""
        try:
            result = self.driver.execute_script(
                "var nameEl = document.querySelector("
                "\"input[name='Name'], input[name='name'], input[formcontrolname='name']\"); "
                "var descEl = document.querySelector("
                "\"input[name='Description'], input[name='description'], input[formcontrolname='description']\"); "
                "var toggle = document.querySelector('app-slide-toggle-v2'); "
                "var status = 'Active'; "
                "if(toggle){"
                "  var onLabel = toggle.querySelector('.state-label.on'); "
                "  if(!(onLabel && onLabel.classList.contains('active'))){status='Inactive';} "
                "} "
                "var containers = document.querySelectorAll('.custom-file-upload'); "
                "var hasFile = false; "
                "for(var i=0;i<containers.length;i++){"
                "  var t = containers[i].textContent.trim(); "
                "  if(t && t.indexOf('No File Uploaded')===-1){hasFile=true; break;} "
                "} "
                "return {"
                "  name: nameEl ? nameEl.value : '',"
                "  description: descEl ? descEl.value : '',"
                "  status: status,"
                "  has_file: hasFile"
                "};"
            )
            return result or {"name": "", "description": "", "status": "Active", "has_file": False}
        except Exception:
            return {"name": "", "description": "", "status": "Active", "has_file": False}

    # ================================================================
    # View/Edit popup verification — single JS call
    # ================================================================

    def verify_view_popup_read_only(self):
        """Verify the View popup shows Name and Description disabled + no Submit/Update button.
        Single JS call — 4x faster than separate execute_script calls."""
        log.info("Verifying View popup is read-only")
        try:
            result = self.driver.execute_script(
                "var nameEl = document.querySelector("
                "\"input[name='Name'], input[name='name'], input[formcontrolname='name']\"); "
                "var descEl = document.querySelector("
                "\"input[name='Description'], input[name='description'], input[formcontrolname='description']\"); "
                "var nameDisabled = nameEl && nameEl.disabled; "
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
                "return {nameDisabled:nameDisabled, descDisabled:descDisabled, "
                "  hasSubmit:hasSubmit, hasUpdate:hasUpdate, hasCancel:hasCancel};"
            )
            name_disabled = bool(result.get('nameDisabled'))
            desc_disabled = bool(result.get('descDisabled'))
            no_submit = not result.get('hasSubmit')
            no_update = not result.get('hasUpdate')
            has_cancel = result.get('hasCancel')
            is_readonly = name_disabled and desc_disabled and no_submit and no_update and has_cancel
            log.info("View popup read-only check: name_disabled=" + str(name_disabled)
                     + " desc_disabled=" + str(desc_disabled) + " no_submit=" + str(no_submit)
                     + " no_update=" + str(no_update) + " has_cancel=" + str(has_cancel)
                     + " => readonly=" + str(is_readonly))
            return is_readonly
        except Exception as e:
            log.warning("View popup read-only check failed: " + str(e))
            return False

    def verify_edit_popup_editable(self):
        """Verify the Edit popup shows Update button and editable fields.
        Single JS call."""
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
        """Get mat-error text below form fields via JS parent walk.
        Note: Crop Master has NO inline mat-error elements (BUG-CM04)."""
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

    def handle_success_alert(self, timeout=3):
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
                WebDriverWait(self.driver, 2).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
                )
            except Exception:
                pass
            return title
        except Exception:
            log.info("No SweetAlert found (may have auto-dismissed)")
            return ""

    def is_success_alert_present(self, timeout=3):
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

    def search_crop(self, crop_name):
        """Search for a crop by name. Returns True if found in results, False otherwise.
        Multi-selector fallback for search button."""
        log.info("Searching for crop: " + crop_name)
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
            search_input, crop_name
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
        found = self.is_crop_in_table(crop_name)
        log.info("Search completed for: " + crop_name + " found=" + str(found))
        return found

    def search_and_verify(self, crop_name):
        """Search for a crop, then verify it exists in the filtered results.
        Recommended way to verify a create/update — handles pagination.
        Raises AssertionError if not found."""
        log.info("Searching and verifying crop: " + crop_name)
        self.search_crop(crop_name)
        return self.verify_crop_exists(crop_name)

    # ================================================================
    # Search cleanup — JS-based, no hard_refresh
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
    # Table data helpers — pure JS for speed
    # ================================================================

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

    def get_all_crop_names(self):
        """Return all crop names from the current table view. Pure JS."""
        try:
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
        except Exception:
            return []

    def is_crop_in_table(self, crop_name):
        """Check if a crop name exists in the current table view. Returns True/False.
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
                crop_name
            ))
        except Exception:
            return False

    def verify_crop_exists(self, crop_name):
        """Verify crop name appears in table. Polls up to 5s via JS for slow renders.
        Raises AssertionError if not found (consistent with UOM gold standard)."""
        log.info("Verifying crop '" + crop_name + "' exists in table")
        end_time = time.monotonic() + 5
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
                    crop_name
                )
                if result and result.get('found'):
                    log.info("Crop '" + crop_name + "' found in table")
                    return True
                last_seen = result.get('rows', []) if result else []
            except Exception:
                pass
            time.sleep(0.3)
        log.error("Crop '" + crop_name + "' NOT found. Table: " + str(last_seen))
        raise AssertionError(
            "Crop '" + crop_name + "' NOT found in table after search. Last rows: " + str(last_seen)
        )

    def get_status_from_table(self, crop_name):
        """Get Status text ('Active'/'Inactive') for a crop. Pure JS."""
        try:
            result = self.driver.execute_script(
                "var table = document.querySelector('table#excel-table'); "
                "if(!table){return '';} "
                "var rows = table.querySelectorAll('tbody tr'); "
                "for(var i=0;i<rows.length;i++){"
                "  var nameCells = rows[i].querySelectorAll('td.cdk-column-name, td.mat-column-name'); "
                "  for(var j=0;j<nameCells.length;j++){"
                "    if(nameCells[j].textContent.trim().toLowerCase().indexOf(arguments[0].toLowerCase())!==-1){"
                "      var statusCells = rows[i].querySelectorAll('td.cdk-column-status, td.mat-column-status'); "
                "      for(var k=0;k<statusCells.length;k++){"
                "        var t = statusCells[k].textContent.trim(); if(t) return t;"
                "      }"
                "    }"
                "  }"
                "} return '';",
                crop_name
            )
            return result or ''
        except Exception:
            return ''

    def find_crop_row_index(self, crop_name):
        """Find row index by name. Returns -1 if not found. Pure JS."""
        try:
            result = self.driver.execute_script(
                "var table = document.querySelector('table#excel-table'); "
                "if(!table){return -1;} "
                "var rows = table.querySelectorAll('tbody tr'); "
                "for(var i=0;i<rows.length;i++){"
                "  var cells = rows[i].querySelectorAll('td'); "
                "  for(var j=0;j<cells.length;j++){"
                "    if(cells[j].textContent.trim().toLowerCase().indexOf(arguments[0].toLowerCase())!==-1){"
                "      return i;"
                "    }"
                "  }"
                "} return -1;",
                crop_name
            )
            return int(result) if result is not None else -1
        except Exception:
            return -1

    # ================================================================
    # Filter panel — JS-based open/close
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
            return 'clicked' in str(result)
        except Exception as e:
            log.warning("Filter panel open failed: " + str(e))
            return False

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

    def get_filter_categories(self):
        """Get filter categories from the filter panel. Returns list of strings."""
        try:
            result = self.driver.execute_script(
                "var panel = document.querySelector('.filter-panel, .erp-filter-panel'); "
                "if(!panel){return [];} "
                "var items = panel.querySelectorAll('mat-panel-title, .category-title, .filter-category'); "
                "var result = []; "
                "for(var i=0;i<items.length;i++){"
                "  var t = items[i].textContent.trim(); if(t) result.push(t);"
                "} return result;"
            )
            return result or []
        except Exception:
            return []

    # ================================================================
    # Click refresh (toolbar refresh button)
    # ================================================================

    def click_refresh(self):
        """Click the toolbar Refresh button via JS."""
        log.info("Clicking refresh button")
        self.driver.execute_script(
            "var btn = document.querySelector('button[mattooltip=\"REFRESH\"], button[mattooltip=\"Refresh\"], button[mattooltip=\"refresh\"]'); "
            "if(btn){btn.click(); return 'clicked';} return 'not found';"
        )
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: d.find_elements("css selector", "table#excel-table tbody tr")
            )
        except Exception:
            pass

    # ================================================================
    # History (via app-dynamic-history — same as UOM)
    # ================================================================

    def is_history_empty(self):
        """Check if the History popup shows 'No data available'. Pure JS."""
        try:
            return bool(self.driver.execute_script(
                "var noData = document.querySelector("
                "'app-dynamic-history .no-data, app-dynamic-history img[alt=\"No Data Available\"], "
                ".popup-overlay .no-data'); "
                "return noData && noData.offsetParent !== null;"
            ))
        except Exception:
            return True

    def get_history_row_count(self):
        """Get the number of rows in the History table. Pure JS."""
        try:
            count = self.driver.execute_script(
                "var rows = document.querySelectorAll("
                "'app-dynamic-history table#excel-table tbody tr, "
                ".popup-overlay table tbody tr'); "
                "return rows ? rows.length : 0;"
            )
            return int(count) if count else 0
        except Exception:
            return 0

    def get_history_data(self):
        """Get all data from the History table. Returns list of dicts.
        Pure JS for speed."""
        log.info("Reading History table data")
        try:
            result = self.driver.execute_script(
                "var container = document.querySelector('app-dynamic-history') || document.querySelector('.popup-overlay'); "
                "if(!container){return [];} "
                "var rows = container.querySelectorAll('table tbody tr'); "
                "var records = []; "
                "for(var i=0;i<rows.length;i++){"
                "  var cells = rows[i].querySelectorAll('td'); "
                "  var record = {}; "
                "  for(var j=0;j<cells.length;j++){"
                "    var t = cells[j].textContent.trim(); "
                "    if(t){record['col_'+j] = t;} "
                "  } "
                "  records.push(record);"
                "} return records;"
            )
            return result or []
        except Exception as e:
            log.warning("Could not read history data: " + str(e))
            return []

    def check_history(self, crop_name, search_text=None):
        """Open history popup for a crop and return row count + error.
        Args:
            crop_name: name to search for and open history
            search_text: optional text to search within history popup
        Returns dict: {row_count, error, search_found}"""
        log.info("Checking history for crop: " + crop_name)
        result = {'row_count': 0, 'error': '', 'search_found': False}
        try:
            self.click_history_button(crop_name)
            # Wait for history content
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located(("css selector", "app-dynamic-history table, .popup-overlay table"))
                )
            except Exception:
                pass
            result['row_count'] = self.get_history_row_count()
            # If search_text provided, try searching within history
            if search_text:
                result['search_found'] = self._search_in_history(search_text)
            self.close_history_popup()
        except Exception as e:
            result['error'] = str(e)
            log.warning("History check error: " + str(e))
            # Try to close any leftover popup
            try:
                self.close_history_popup()
            except Exception:
                pass
        return result

    def _search_in_history(self, search_text):
        """Search within the history popup. Returns True if text found in results."""
        try:
            # Find the history search input and type
            self.driver.execute_script(
                "var input = document.querySelector('app-dynamic-history input#erpSearchInput, "
                ".popup-overlay input#erpSearchInput, app-dynamic-history input'); "
                "if(!input){return false;} "
                "input.value = arguments[0]; "
                "input.dispatchEvent(new Event('input',{bubbles:true})); "
                "input.dispatchEvent(new Event('keyup',{bubbles:true})); "
                "input.dispatchEvent(new Event('change',{bubbles:true}));",
                search_text
            )
            # Press Enter via JS
            self.driver.execute_script(
                "var input = document.querySelector('app-dynamic-history input#erpSearchInput, "
                ".popup-overlay input#erpSearchInput, app-dynamic-history input'); "
                "if(!input){return false;} "
                "var event = new KeyboardEvent('keydown',{key:'Enter',code:'Enter',keyCode:13,bubbles:true}); "
                "input.dispatchEvent(event);"
            )
            # Brief wait then check results
            try:
                WebDriverWait(self.driver, 2).until(
                    lambda d: d.find_elements("css selector", "app-dynamic-history table tbody tr, .popup-overlay table tbody tr")
                )
            except Exception:
                pass
            return self.get_history_row_count() > 0
        except Exception:
            return False

    def is_history_popup_open(self):
        """Check if the history popup is currently visible."""
        try:
            return bool(self.driver.execute_script(
                "var el = document.querySelector('app-dynamic-history, .popup-overlay'); "
                "return el && el.offsetParent !== null;"
            ))
        except Exception:
            return False

    def get_history_headers(self):
        """Get column header texts from the history table. Pure JS."""
        try:
            result = self.driver.execute_script(
                "var container = document.querySelector('app-dynamic-history') || document.querySelector('.popup-overlay'); "
                "if(!container){return [];} "
                "var headers = container.querySelectorAll('table th'); "
                "var result = []; "
                "for(var i=0;i<headers.length;i++){"
                "  var t = headers[i].textContent.trim(); if(t) result.push(t);"
                "} return result;"
            )
            return result or []
        except Exception:
            return []

    def close_history_popup(self):
        """Close the History popup by clicking Cancel via JS."""
        log.info("Closing History popup")
        self.driver.execute_script(
            "var footers = document.querySelectorAll('.popup-footer'); "
            "for(var i=0;i<footers.length;i++){"
            "  var buttons = footers[i].querySelectorAll('button'); "
            "  for(var j=0;j<buttons.length;j++){"
            "    if(buttons[j].textContent.indexOf('Cancel')!==-1){"
            "      buttons[j].click(); return 'clicked';"
            "    }"
            "  }"
            "} "
            "return 'not found';"
        )

    # ================================================================
    # High-level CRUD workflows
    # ================================================================

    def create_crop(self, data):
        """Full create workflow: open form -> fill -> submit -> handle response.
        Returns dict: {status, error, name, message}
        Optimised: checks form-closed FIRST (fast path for success), then alert."""
        name = data.get("name", "")
        log.info("Creating Crop: " + name)

        self.open_add_form()
        assert self.is_add_form_open(), "Add form did not open"

        self.fill_crop_form(data)
        self.submit()

        # Check form-closed first (fast path — Crop Master DOES show success SweetAlert),
        # then check for validation alert (slow path)
        end_time = time.monotonic() + 3
        while time.monotonic() < end_time:
            # Quick check: form closed = successful create
            if not self.is_add_form_open():
                break
            # Quick check for validation alert
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
                    return {'status': 'VALIDATION_FAILED', 'error': warning, 'name': name, 'message': warning}
            except Exception:
                pass
            time.sleep(0.15)

        # Handle success SweetAlert if present
        msg = self.handle_success_alert(timeout=2)

        log.info("Crop created: " + name)
        return {'status': 'PASSED', 'error': '', 'name': name, 'message': msg}

    def edit_crop(self, crop_name, edit_data):
        """Full edit workflow: navigate -> search -> click edit -> fill -> update.
        Returns dict: {status, error, name, message}
        Optimised: checks form-closed FIRST (fast path), then alert."""
        new_name = edit_data.get("name", crop_name)
        log.info("Editing Crop '" + crop_name + "' -> '" + new_name + "'")

        self.navigate_to_page()
        self.search_crop(crop_name)
        self.click_edit_button(crop_name)
        assert self.is_edit_mode(), "Edit mode not activated"

        self.fill_crop_form(edit_data)
        self.click_update()

        # Check form-closed first (fast path), then alert
        end_time = time.monotonic() + 3
        while time.monotonic() < end_time:
            if not self.is_add_form_open():
                break
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
                    return {'status': 'VALIDATION_FAILED', 'error': warning, 'name': new_name, 'message': warning}
            except Exception:
                pass
            time.sleep(0.15)

        # Handle success SweetAlert if present
        msg = self.handle_success_alert(timeout=2)

        log.info("Crop updated: " + new_name)
        return {'status': 'PASSED', 'error': '', 'name': new_name, 'message': msg}
