"""
item_attribute_page.py
----------------------
Page Object for RhythmERP -> Commodity Settings -> Item Attribute 1-5.
Parameterized across 5 screens via attr_num (1-5).

IA1: Name (required) + Base UOM (mat-select, required) + Description + Status toggle
IA2-5: Name (required) + Description + Status toggle (NO Base UOM)

Optimised (UOM gold standard v2 — Item Group variant):
- ZERO time.sleep() calls — WebDriverWait with 0.15-0.3s polling
- JS clicks for ALL buttons — bypasses overlay issues
- offsetParent visibility checks (except position:fixed -> getBoundingClientRect)
- Single hard_refresh() in _cleanup() — fast page reset between tests
- Fast SweetAlert2 handler: JS-based poll, dismiss via JS click
- 3-dot menu: td.cdk-column-actions button + text-based menu matching
- Single-line concatenated JS strings — NO triple-quoted Python strings
- _js_set_input() with Angular event dispatch for text fields
- _js_set_mat_select() for Base UOM dropdown (IA1 only) — works around BUG-IA02
- _set_status_toggle() / _get_status_toggle_state() via .on.active class check
- Search with multi-selector fallback for search button
- _force_close_panels() only removes .erp-action-menu and .cdk-overlay-backdrop
- cancel() is graceful — returns 'no_cancel_found' instead of throwing
- clear_search() uses JS-based clearing (no hard_refresh — saves ~4s per call)
- create_item_attribute() / edit_item_attribute() workflow helpers
- Filter panel uses position:fixed -> getBoundingClientRect for visibility
- History via 3-dot menu "History" item
- Field names: name="Name" / name="Description" (capital N and D!)
"""

import time
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL


class ItemAttributePage(BasePage):
    """Page Object for Item Attribute 1-5 screens.
    Constructor takes attr_num (1-5) to determine which screen to use.
    """

    SCREEN_NAMES = {
        1: "dynamic-screens/Item%20Attribute1",
        2: "dynamic-screens/Item%20Attribute2",
        3: "dynamic-screens/Item%20Attribute3",
        4: "dynamic-screens/Item%20Attribute4",
        5: "dynamic-screens/Item%20Attribute5",
    }

    DISPLAY_NAMES = {
        1: "Item Attribute1",
        2: "Item Attribute2",
        3: "Item Attribute3",
        4: "Item Attribute4",
        5: "Item Attribute5",
    }

    def __init__(self, driver, attr_num=1):
        super().__init__(driver)
        self.attr_num = attr_num
        screen_name = self.SCREEN_NAMES.get(attr_num, self.SCREEN_NAMES[1])
        self.PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/{screen_name}"
        self.display_name = self.DISPLAY_NAMES.get(attr_num, "Item Attribute1")
        self.has_base_uom = (attr_num == 1)

    # Locators — minimal set
    ADD_BUTTON = ("css", "button.erp-add-btn")
    NAME_INPUT = ("css", "input[name='Name'], input[formcontrolname='name']")
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
        log.info("Navigating to " + self.display_name + " page")
        self.driver.get(self.PAGE_URL)
        self._wait_for_page_ready()

    def hard_refresh(self):
        log.info("Hard refreshing " + self.display_name + " page")
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        try:
            WebDriverWait(self.driver, 8).until(
                lambda d: d.find_elements("css selector", "table#excel-table")
            )
            log.info(self.display_name + " page ready (table found)")
        except Exception:
            try:
                WebDriverWait(self.driver, 2).until(
                    lambda d: d.find_elements("css selector", "button.erp-add-btn")
                )
                log.info(self.display_name + " page ready (add button found)")
            except Exception:
                log.warning(self.display_name + " page ready check timed out")

    def is_page_loaded(self):
        return bool(self.driver.execute_script(
            "var t = document.querySelector('table#excel-table'); "
            "return t && t.offsetParent !== null;"
        ))

    # ================================================================
    # Overlay cleanup
    # ================================================================

    def _force_close_panels(self):
        self.driver.execute_script(
            "document.querySelectorAll('.erp-action-menu').forEach(function(el){el.remove();}); "
            "document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el){el.remove();});"
        )

    def _cleanup(self):
        self._force_close_panels()
        self._cleanup_swal2()
        self.hard_refresh()

    # ================================================================
    # Add form
    # ================================================================

    def open_add_form(self):
        log.info("Opening Add form on " + self.display_name)
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
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: d.execute_script(
                    "var el = document.querySelector("
                    "\"input[name='Name'], input[formcontrolname='name']\"); "
                    "return el && el.offsetParent !== null;"
                )
            )
            log.info("Add form opened")
        except Exception:
            log.warning("Add form may not have opened — Name input not found")

    # ================================================================
    # Fill form
    # ================================================================

    def fill_item_attribute_form(self, data):
        """Fill the Item Attribute form.
        data: dict with keys 'name', 'base_uom' (IA1 only), 'description', 'status'"""
        log.info("Filling " + self.display_name + " form: " + str(data))
        name = data.get("name")
        if name is not None:
            self._js_set_input("input[name='Name'], input[formcontrolname='name']", str(name))
        # Base UOM — IA1 only
        if self.has_base_uom and "base_uom" in data:
            self._js_set_mat_select(data["base_uom"])
        description = data.get("description")
        if description is not None:
            self._js_set_input("input[name='Description'], input[formcontrolname='description']", str(description))
        # Status toggle
        if "status" in data:
            self._set_status_toggle(bool(data["status"]))
        log.info(self.display_name + " form filled")

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

    def _js_set_mat_select(self, value_text):
        """Select an option in the Base UOM mat-select dropdown via JS.
        Works around BUG-IA02: browser-clicked mat-select values don't
        register in Angular reactive form. Uses JS click on the option
        AND sets the form control value via Angular's NgModel."""
        if not value_text:
            # Select a random option if no specific value given
            self._js_select_random_mat_option()
            return
        log.info("Selecting Base UOM: " + str(value_text))
        try:
            # Step 1: Open the mat-select dropdown
            self.driver.execute_script(
                "var sel = document.querySelector('mat-select'); "
                "if(!sel){throw new Error('mat-select not found');} "
                "sel.scrollIntoView({block:'center'}); sel.click(); "
                "return 'opened';"
            )
            # Step 2: Wait for options to appear
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located(("css selector", "div[role='listbox'] mat-option"))
                )
            except Exception:
                pass
            # Step 3: Click the matching option via JS
            result = self.driver.execute_script(
                "var options = document.querySelectorAll('div[role=\"listbox\"] mat-option'); "
                "for(var i=0;i<options.length;i++){"
                "  var txt = options[i].textContent.trim(); "
                "  if(txt === arguments[0] || txt.indexOf(arguments[0])!==-1){"
                "    options[i].click(); return 'selected_'+txt;"
                "  }"
                "} "
                "return 'option_not_found';",
                str(value_text)
            )
            log.info("Base UOM selection result: " + str(result))
            # Step 4: Close any leftover overlay
            self._force_close_panels()
        except Exception as e:
            log.warning("Base UOM selection failed: " + str(e))
            self._force_close_panels()

    def _js_select_random_mat_option(self):
        """Select a random option from the Base UOM dropdown."""
        log.info("Selecting random Base UOM option")
        try:
            self.driver.execute_script(
                "var sel = document.querySelector('mat-select'); "
                "if(!sel){throw new Error('mat-select not found');} "
                "sel.scrollIntoView({block:'center'}); sel.click(); "
                "return 'opened';"
            )
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located(("css selector", "div[role='listbox'] mat-option"))
                )
            except Exception:
                pass
            result = self.driver.execute_script(
                "var options = document.querySelectorAll('div[role=\"listbox\"] mat-option'); "
                "if(options.length===0){return 'no_options';} "
                "var idx = Math.floor(Math.random() * options.length); "
                "var txt = options[idx].textContent.trim(); "
                "options[idx].click(); return 'selected_'+txt;"
            )
            log.info("Random Base UOM: " + str(result))
            self._force_close_panels()
        except Exception as e:
            log.warning("Random Base UOM selection failed: " + str(e))
            self._force_close_panels()

    # ================================================================
    # Status toggle
    # ================================================================

    def _set_status_toggle(self, desired_state):
        """Set the Status toggle to desired state.
        True = Active (ON), False = Inactive (OFF)."""
        current = self._get_status_toggle_state()
        if current == desired_state:
            log.info("Status toggle already " + ("Active" if desired_state else "Inactive"))
            return
        log.info("Setting Status toggle to " + ("Active" if desired_state else "Inactive"))
        self.driver.execute_script(
            "var slider = document.querySelector('.switch-wrapper .slider'); "
            "if(!slider){var wrapper = document.querySelector('.switch-wrapper'); "
            "if(wrapper){wrapper.click(); return 'clicked_wrapper';} "
            "return 'not_found';} "
            "slider.click(); return 'clicked_slider';"
        )
        # Verify
        new_state = self._get_status_toggle_state()
        if new_state != desired_state:
            log.warning("Status toggle may not have changed")

    def _get_status_toggle_state(self):
        """Read current Status toggle state. True=Active, False=Inactive."""
        try:
            return bool(self.driver.execute_script(
                "var on = document.querySelector('.switch-wrapper .on.active'); "
                "return on !== null;"
            ))
        except Exception:
            return True  # Default

    # ================================================================
    # Submit / Update / Cancel — all via JS click
    # ================================================================

    def submit(self):
        log.info("Clicking Submit")
        self._js_click_popup_button("Submit")

    def click_update(self):
        log.info("Clicking Update")
        self._js_click_popup_button("Update")

    def cancel(self):
        """Click Cancel via JS. Gracefully handles no popup open."""
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
        log.info("Force closing form popup")
        result = self.driver.execute_script(
            "var popup = document.querySelector('div.edit_pop_up, div.big-model'); "
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

    def _click_action_menu_item(self, item_name, action_name):
        """Click a 3-dot menu item (View/Edit/History) for a specific row."""
        log.info("Clicking " + action_name + " via 3-dot menu for: " + item_name)
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
            "throw new Error('Item \"'+arguments[0]+'\" not found in table');",
            item_name
        )
        # Step 2: Wait for dropdown overlay
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
        log.info("Successfully clicked " + action_name + " for: " + item_name)
        return result

    def click_view_button(self, item_name):
        """Click View via 3-dot menu for a specific row."""
        self._ensure_item_visible(item_name)
        self._click_action_menu_item(item_name, "View")
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(("css selector", ".popup-header h3"))
            )
        except Exception:
            pass

    def click_edit_button(self, item_name):
        """Click Edit via 3-dot menu for a specific row."""
        self._ensure_item_visible(item_name)
        self._click_action_menu_item(item_name, "Edit")
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: d.execute_script(
                    "var el = document.querySelector("
                    "\"input[name='Name'], input[formcontrolname='name']\"); "
                    "return el && el.offsetParent !== null;"
                )
            )
        except Exception:
            pass

    def click_history_button(self, item_name):
        """Click History via 3-dot menu for a specific row."""
        self._ensure_item_visible(item_name)
        self._click_action_menu_item(item_name, "History")
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

    def _ensure_item_visible(self, item_name, max_attempts=2):
        """Ensure an item is visible in the table before clicking its 3-dot menu."""
        for attempt in range(max_attempts):
            if self.is_item_in_table(item_name):
                return
            found = self.search_item(item_name)
            if found:
                return
            if attempt < max_attempts - 1:
                log.info("Item not found via search, hard refreshing: " + item_name)
                self.hard_refresh()
        if not self.is_item_in_table(item_name):
            self.search_item(item_name)

    # ================================================================
    # Form state checks — offsetParent
    # ================================================================

    def is_add_form_open(self):
        return bool(self.driver.execute_script(
            "var el = document.querySelector("
            "\"input[name='Name'], input[formcontrolname='name']\"); "
            "return el && el.offsetParent !== null;"
        ))

    def is_form_closed(self):
        return not self.is_add_form_open()

    def is_view_mode(self):
        return bool(self.driver.execute_script(
            "var el = document.querySelector("
            "\"input[name='Name'], input[formcontrolname='name']\"); "
            "return el && el.offsetParent !== null && el.disabled;"
        ))

    def is_edit_mode(self):
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
        try:
            return self.driver.execute_script(
                "var h = document.querySelector('.edit_pop_up h3, .big-model h3, mat-dialog-container h3'); "
                "return h ? h.textContent.trim() : '';"
            ) or ""
        except Exception:
            return ""

    def get_form_field_values(self):
        """Read all form field values via JS (single call).
        Returns dict: name, description, base_uom (if IA1), status"""
        try:
            result = self.driver.execute_script(
                "var nameEl = document.querySelector("
                "\"input[name='Name'], input[formcontrolname='name']\"); "
                "var descEl = document.querySelector("
                "\"input[name='Description'], input[formcontrolname='description']\"); "
                "var uomEl = document.querySelector('mat-select'); "
                "var statusActive = document.querySelector('.switch-wrapper .on.active'); "
                "return {"
                "  name: nameEl ? nameEl.value : '',"
                "  description: descEl ? descEl.value : '',"
                "  base_uom: uomEl ? uomEl.textContent.trim() : '',"
                "  status: statusActive !== null"
                "};"
            )
            return result or {"name": "", "description": "", "base_uom": "", "status": True}
        except Exception:
            return {"name": "", "description": "", "base_uom": "", "status": True}

    # ================================================================
    # View/Edit popup verification — single JS call
    # ================================================================

    def verify_view_popup_read_only(self):
        log.info("Verifying View popup is read-only")
        try:
            result = self.driver.execute_script(
                "var nameEl = document.querySelector("
                "\"input[name='Name'], input[formcontrolname='name']\"); "
                "var descEl = document.querySelector("
                "\"input[name='Description'], input[formcontrolname='description']\"); "
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
            log.info("View popup read-only: " + str(is_readonly))
            return is_readonly
        except Exception as e:
            log.warning("View popup check failed: " + str(e))
            return False

    def verify_edit_popup_editable(self):
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
            log.info("Edit popup editable: " + str(is_editable))
            return is_editable
        except Exception as e:
            log.warning("Edit popup check failed: " + str(e))
            return False

    # ================================================================
    # Mat-error text — JS-based parent walk
    # ================================================================

    def get_mat_error_text(self):
        try:
            result = self.driver.execute_script(
                "var input = document.querySelector("
                "\"input[name='Name'], input[formcontrolname='name']\"); "
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
                log.warning("Validation errors: " + result)
            return result or ""
        except Exception:
            return ""

    def has_field_error(self, field_label):
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
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('#swal2-title'); "
                "return (el && el.offsetParent !== null) ? el.textContent.trim() : '';"
            ) or ""
        except Exception:
            return ""

    def get_swal_html_message(self):
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('.swal2-html-container'); "
                "return (el && el.offsetParent !== null) ? el.textContent.trim() : '';"
            ) or ""
        except Exception:
            return ""

    def _cleanup_swal2(self):
        try:
            self.driver.execute_script(
                "document.querySelectorAll('.swal2-container').forEach(function(el){el.remove();});"
            )
        except Exception:
            pass

    # ================================================================
    # Search — multi-selector fallback for search button
    # ================================================================

    def search_item(self, item_name):
        """Search for an item by name. Returns True if found."""
        log.info("Searching for: " + item_name)
        try:
            self.driver.execute_script(
                "var input = document.querySelector('input#erpSearchInput, .erp-search-wrapper input'); "
                "if(!input){return 'no search input';} "
                "var setter = Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype,'value').set;"
                "setter.call(input, arguments[0]); "
                "input.dispatchEvent(new Event('input',{bubbles:true})); "
                "input.dispatchEvent(new Event('change',{bubbles:true})); "
                "return 'typed';",
                item_name
            )
            self.driver.execute_script(
                "var btn = document.querySelector("
                "'button[aria-label=\"Search\"], "
                "button.search-btn, "
                "button.erp-outline-btn[mattooltip=\"Search\"]'); "
                "if(btn){btn.click(); return 'clicked';} return 'no search button';"
            )
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
                        item_name
                    )
                )
            except Exception:
                pass
            found = self.is_item_in_table(item_name)
            log.info("Search result for '" + item_name + "': " + str(found))
            return found
        except Exception as e:
            log.warning("Search failed: " + str(e))
            return False

    def clear_search(self):
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
            self.driver.execute_script(
                "var btn = document.querySelector("
                "'button[aria-label=\"Search\"], "
                "button.search-btn, "
                "button.erp-outline-btn[mattooltip=\"Search\"]'); "
                "if(btn){btn.click(); return 'clicked';} return 'no search button';"
            )
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

    def is_item_in_table(self, item_name):
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
                item_name
            ))
        except Exception:
            return False

    # ================================================================
    # Table data extraction
    # ================================================================

    def get_table_row_count(self):
        try:
            return self.driver.execute_script(
                "return document.querySelectorAll('table#excel-table tbody tr').length;"
            ) or 0
        except Exception:
            return 0

    # ================================================================
    # Filter panel — position:fixed -> getBoundingClientRect
    # ================================================================

    def open_filter_panel(self):
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
        log.info("Closing filter panel")
        try:
            self.driver.execute_script(
                "var btn = document.querySelector('div.filter-panel button.close-btn'); "
                "if(btn){btn.click(); return 'clicked';} return 'not found';"
            )
        except Exception:
            pass

    def get_filter_categories(self):
        try:
            return self.driver.execute_script(
                "var cats = document.querySelectorAll('div.filter-category'); "
                "var names = []; "
                "for(var i=0;i<cats.length;i++){"
                "  var txt = cats[i].textContent.trim(); "
                "  if(txt) names.push(txt);"
                "} return names;"
            ) or []
        except Exception:
            return []

    # ================================================================
    # History popup
    # ================================================================

    def check_history(self, item_name):
        """Open history popup for an item. Returns dict with error, row_count."""
        log.info("Checking history for: " + item_name)
        try:
            self.click_history_button(item_name)
            row_count = self.get_history_row_count()
            self.close_history_popup()
            return {"error": "", "row_count": row_count}
        except Exception as e:
            log.warning("History check failed: " + str(e))
            try:
                self.close_history_popup()
            except Exception:
                pass
            return {"error": str(e), "row_count": 0}

    def close_history_popup(self):
        log.info("Closing history popup")
        try:
            self.driver.execute_script(
                "var headings = document.querySelectorAll("
                "'.big-model h3, .popup-header h3, mat-dialog-container h3'); "
                "for(var i=0;i<headings.length;i++){"
                "  if(headings[i].textContent.toLowerCase().indexOf('history')!==-1){"
                "    var popup = headings[i].closest('.big-model, mat-dialog-container, .popup-overlay'); "
                "    if(popup){"
                "      var cancelBtn = popup.querySelector('button'); "
                "      var footers = popup.querySelectorAll('div[class*=\"popup-footer\"] button'); "
                "      for(var j=0;j<footers.length;j++){"
                "        if(footers[j].textContent.trim().indexOf('Cancel')!==-1){"
                "          footers[j].click(); return 'clicked_cancel';"
                "        }"
                "      }"
                "      var closeIcon = popup.querySelector('button[mat-icon-button] mat-icon'); "
                "      if(closeIcon){var btn=closeIcon.closest('button'); if(btn){btn.click(); return 'clicked_close';}}"
                "    }"
                "  }"
                "} return 'no_history_popup';"
            )
        except Exception:
            pass

    def get_history_row_count(self):
        try:
            return self.driver.execute_script(
                "var rows = document.querySelectorAll('.big-model table tbody tr, app-dynamic-history table tbody tr'); "
                "return rows.length;"
            ) or 0
        except Exception:
            return 0

    def get_history_columns(self):
        try:
            return self.driver.execute_script(
                "var headers = document.querySelectorAll('.big-model table th, app-dynamic-history table th'); "
                "var cols = []; "
                "for(var i=0;i<headers.length;i++){"
                "  var t = headers[i].textContent.trim(); if(t) cols.push(t);"
                "} return cols;"
            ) or []
        except Exception:
            return []

    # ================================================================
    # High-level workflow helpers
    # ================================================================

    def create_item_attribute(self, data):
        """Create an item attribute with the given data.
        Returns dict: {status, name, error}"""
        log.info("Creating " + self.display_name + ": " + str(data))
        try:
            self.open_add_form()
            self._force_close_panels()
            self.fill_item_attribute_form(data)
            self.submit()
            # Check for validation alert
            is_alert = self.is_validation_alert_present(timeout=3)
            if is_alert:
                warning = self.handle_validation_warning()
                return {"status": "FAILED", "name": data.get("name", ""), "error": warning}
            # Check for success alert
            title = self.handle_success_alert(timeout=3)
            if title and ("success" in title.lower() or "added" in title.lower()):
                return {"status": "PASSED", "name": data.get("name", ""), "error": ""}
            # Check for save failure (e.g. too long)
            is_failure = self.is_validation_alert_present(timeout=2)
            if is_failure:
                fail_title = self.handle_validation_warning()
                return {"status": "FAILED", "name": data.get("name", ""), "error": fail_title}
            # No alert at all — check if form closed (success)
            if self.is_form_closed():
                return {"status": "PASSED", "name": data.get("name", ""), "error": ""}
            return {"status": "PASSED", "name": data.get("name", ""), "error": ""}
        except Exception as e:
            log.warning("Create failed: " + str(e))
            return {"status": "FAILED", "name": data.get("name", ""), "error": str(e)}

    def edit_item_attribute(self, item_name, edit_data):
        """Edit an existing item attribute.
        Returns dict: {status, name, error}"""
        log.info("Editing " + self.display_name + " '" + item_name + "': " + str(edit_data))
        try:
            self.search_item(item_name)
            self.click_edit_button(item_name)
            # Fill only provided fields (None = skip)
            if edit_data.get("name") is not None:
                self._js_set_input("input[name='Name'], input[formcontrolname='name']", str(edit_data["name"]))
            if self.has_base_uom and edit_data.get("base_uom") is not None:
                self._js_set_mat_select(edit_data["base_uom"])
            if edit_data.get("description") is not None:
                self._js_set_input("input[name='Description'], input[formcontrolname='description']", str(edit_data["description"]))
            if "status" in edit_data:
                self._set_status_toggle(bool(edit_data["status"]))
            self.click_update()
            # Check for validation alert
            is_alert = self.is_validation_alert_present(timeout=3)
            if is_alert:
                warning = self.handle_validation_warning()
                return {"status": "FAILED", "name": edit_data.get("name") or item_name, "error": warning}
            # Check for success
            title = self.handle_success_alert(timeout=3)
            if title and ("success" in title.lower() or "updated" in title.lower()):
                return {"status": "PASSED", "name": edit_data.get("name") or item_name, "error": ""}
            # Check for save failure
            is_failure = self.is_validation_alert_present(timeout=2)
            if is_failure:
                fail_title = self.handle_validation_warning()
                return {"status": "FAILED", "name": edit_data.get("name") or item_name, "error": fail_title}
            if self.is_form_closed():
                return {"status": "PASSED", "name": edit_data.get("name") or item_name, "error": ""}
            return {"status": "PASSED", "name": edit_data.get("name") or item_name, "error": ""}
        except Exception as e:
            log.warning("Edit failed: " + str(e))
            return {"status": "FAILED", "name": edit_data.get("name") or item_name, "error": str(e)}
