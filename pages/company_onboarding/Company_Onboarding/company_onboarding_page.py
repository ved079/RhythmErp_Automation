"""
company_onboarding_page.py
---------------------
Page Object Model for RhythmERP Company Onboarding screen.

KEY DESIGN DECISION:
  Never send Keys.ESCAPE anywhere except click_cancel_or_dismiss_dialog.
  Use backdrop click + JS removal for overlay panels.
"""

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL


CO_SUBMISSIONS = []


class CompanyOnboardingPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Company%20Onboarding"

    # ---- Toolbar ----
    ADD_BUTTON = ("css", "button.erp-add-btn")
    REFRESH_BUTTON = ("css", "button[mattooltip='REFRESH'], div[mattooltip='REFRESH'] button")

    # ---- Header fields (outside stepper) ----
    COMPANY_NAME_INPUT = ("css", "input[name='Company Name']")
    ENTITY_GROUP_SELECT = ("xpath", "//mat-label[contains(.,'Entity Group')]/ancestor::mat-form-field//mat-select")
    PARENT_NAME_SELECT = ("xpath", "//mat-label[contains(.,'Parent Name')]/ancestor::mat-form-field//mat-select")
    COMPANY_LINKED_SELECT = ("xpath", "//mat-label[contains(.,'Company Linked')]/ancestor::mat-form-field//mat-select")

    # ---- Step 1 fields ----
    COMPANY_SHORT_NAME_INPUT = ("css", "input[name='Company Short Name']")
    CONTACT_NAME_INPUT = ("css", "input[name='Contact Name']")
    COMPANY_BACKGROUND_INPUT = ("css", "textarea[name='Company Background']")
    EMAIL_INPUT = ("css", "input[name='Email ']")
    MOBILE_NUMBER_INPUT = ("css", "input[name='Mobile Number']")
    PAN_INPUT = ("css", "input[name='PAN']")
    GSTIN_INPUT = ("css", "input[name='GSTIN']")
    CIN_INPUT = ("css", "input[name='CIN']")
    PASSWORD_INPUT = ("css", "input[name='Password']")

    PLAN_TYPE_SELECT = ("xpath", "//mat-label[contains(.,'Plan Type')]/ancestor::mat-form-field//mat-select")
    AUTH_TYPE_SELECT = ("xpath", "//mat-label[contains(.,'Authentication Type')]/ancestor::mat-form-field//mat-select")
    TWO_FA_TOGGLE = ("css", "app-slide-toggle-v2:not(.readonly) .slider")

    # ---- Next / Back ----
    NEXT_BUTTON_XPATH = (
        "//mat-dialog-container//button[@matsteppernext or @matStepperNext]"
        " | //mat-stepper//button[@matsteppernext or @matStepperNext]"
        " | //mat-dialog-container//button[normalize-space(.)='Next']"
    )
    STEP1_NEXT_BUTTON = ("xpath", NEXT_BUTTON_XPATH)
    STEP2_BACK_BUTTON = ("css", "form.step-form button[matstepperprevious]")

    # ---- Step 3: Address details ----
    ADDRESS_TYPE_SELECT = ("xpath", "//app-dynamic-details//mat-label[contains(.,'Address Type')]/ancestor::mat-form-field//mat-select")
    COUNTRY_SELECT = ("xpath", "//app-dynamic-details//mat-label[contains(.,'Country')]/ancestor::mat-form-field//mat-select")
    STATE_SELECT = ("xpath", "//app-dynamic-details//mat-label[contains(.,'State')]/ancestor::mat-form-field//mat-select")
    DISTRICT_SELECT = ("xpath", "//app-dynamic-details//mat-label[contains(.,'District')]/ancestor::mat-form-field//mat-select")
    TALUKA_SELECT = ("xpath", "//app-dynamic-details//mat-label[contains(.,'Taluka')]/ancestor::mat-form-field//mat-select")
    ADDRESS_INPUT = ("xpath", "//app-dynamic-details//input[@name='Address']")
    PIN_CODE_INPUT = ("xpath", "//app-dynamic-details//input[@name='Pin Code']")

    # ---- Step 2: Promoters ----
    PROMOTER_NAME_INPUT = ("xpath", "//app-dynamic-details//input[@name='Name']")
    STEP_REMARK_INPUT = ("xpath", "//app-dynamic-details//textarea[@name='Remark']")
    ADD_ROW_BUTTON = ("css", "button[mat-icon-button][color='primary']")

    # ---- Step 3: Business Details ----
    BUSINESS_MODEL_INPUT = ("xpath", "//app-dynamic-details//mat-label[normalize-space(.)='Business Model']/ancestor::mat-form-field//input")
    MARKET_LINKAGES_INPUT = ("xpath", "//app-dynamic-details//mat-label[normalize-space(.)='Market Linkages']/ancestor::mat-form-field//input")
    LINE_OF_BUSINESS_INPUT = ("xpath", "//app-dynamic-details//mat-label[normalize-space(.)='Line of Business']/ancestor::mat-form-field//input")
    ADDITIONAL_BUSINESS_INPUT = ("xpath", "//app-dynamic-details//mat-label[contains(.,'Additional Business Activities')]/ancestor::mat-form-field//input")

    # ---- Step 4: Infrastructure ----
    INFRA_TYPE_SELECT = ("xpath", "//app-dynamic-details//mat-label[normalize-space(.)='Infrastructure Type']/ancestor::mat-form-field//mat-select")
    INFRA_LOCATION_INPUT = ("xpath", "//app-dynamic-details//input[@name='Infrastructure Location']")
    INFRA_OWNERSHIP_SELECT = ("xpath", "//app-dynamic-details//mat-label[normalize-space(.)='Ownership Type']/ancestor::mat-form-field//mat-select")


    # ---- Table & Search ----
    SEARCH_BUTTON = ('css', 'button.search-btn')
    SEARCH_INPUT = ('css', '.erp-search-wrapper input')
    TABLE_COMPANY_NAMES = ('css', 'td.cdk-column-name')
    PAGINATOR_LABEL = ('css', '.mat-mdc-paginator-range-label')
    REFRESH_BUTTON_HEADER = ('xpath', "//button[*[contains(@class,'material-icons') and text()='refresh']]")
    # ---- Dialog footer ----
    CANCEL_BUTTON = ("xpath", "//div[@class='popup-footer']//button[contains(.,'Cancel')]")
    SUBMIT_BUTTON = ("xpath", "//div[@class='popup-footer']//button[contains(.,'Submit')]")

    # ================================================================
    # Navigation & toolbar
    # ================================================================
    def navigate_to_page(self):
        log.info("Navigating to Company Onboarding page...")
        self.navigate_to(self.PAGE_URL)
        self.wait_seconds(2)

    def is_page_loaded(self):
        return self.is_displayed(self.ADD_BUTTON, timeout=10)

    def open_add_form(self):
        log.info("Clicking ADD button...")
        self.click(self.ADD_BUTTON)
        self.wait_seconds(1.5)

    def click_refresh(self):
        self.click(self.REFRESH_BUTTON)
        self.wait_seconds(2)

    # ================================================================
    # Overlay cleanup
    # ================================================================
    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS. Keeps dialog backdrop."""
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

        # Quick check if anything remains
        remaining = self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop), "
            "div.cdk-overlay-pane mat-option",
        )
        if remaining:
            self._force_close_panels()

    # ================================================================
    # Row management
    # ================================================================
    def add_row(self):
        """Click the + button to add a new row in the current step."""
        btns = self.driver.find_elements("css selector", "button[mat-icon-button][color='primary']")
        clicked = False
        for btn in btns:
            try:
                if btn.is_displayed() and btn.is_enabled():
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
                        btn
                    )
                    clicked = True
                    break
            except Exception:
                continue
        if not clicked:
            raise Exception("+ (add) button not found or not clickable")
        self.wait_seconds(0.5)
        log.info("Added new row via + button")

    # ================================================================
    # Fill Step 1 (Company Details)
    # ================================================================

    def _idx(self, locator, index):
        """Wrap locator with 1-based XPath index."""
        strategy, path = locator
        return (strategy, f"({path})[{index}]")
    def fill_company_details(self, data):
        log.info("Filling Company Details...")

        field_map = {
            "company_name": self.COMPANY_NAME_INPUT,
            "company_short_name": self.COMPANY_SHORT_NAME_INPUT,
            "contact_name": self.CONTACT_NAME_INPUT,
            "company_background": self.COMPANY_BACKGROUND_INPUT,
            "email": self.EMAIL_INPUT,
            "mobile_number": self.MOBILE_NUMBER_INPUT,
            "pan": self.PAN_INPUT,
            "gstin": self.GSTIN_INPUT,
            "cin": self.CIN_INPUT,
        }
        for key, locator in field_map.items():
            if data.get(key):
                self.type_text(locator, str(data[key]), clear_first=True)

        select_map = {
            "entity_group": self.ENTITY_GROUP_SELECT,
            "parent_name": self.PARENT_NAME_SELECT,
            "plan_type": self.PLAN_TYPE_SELECT,
        }
        for key, locator in select_map.items():
            if data.get(key):
                self._select_mat_option(locator, str(data[key]))

        if data.get("company_linked"):
            values = (
                data["company_linked"]
                if isinstance(data["company_linked"], list)
                else [data["company_linked"]]
            )
            self._select_mat_options_multi(self.COMPANY_LINKED_SELECT, values)

        if data.get("is_2fa"):
            self._enable_2fa_toggle()

        if data.get("is_2fa") and data.get("auth_type"):
            self.wait_seconds(0.3)
            self._select_mat_option(self.AUTH_TYPE_SELECT, str(data["auth_type"]))

        # Clean up any open panels
        self._force_close_panels()

        log.info("Company Details filled")

        errors = self.driver.find_elements(
            By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
        )
        if errors:
            texts = [e.text for e in errors if e.text.strip()]
            if texts:
                log.warning(f"Validation errors after fill: {texts}")

    # ================================================================
    # Step navigation â€” OPTIMIZED: JS click directly, no fallback chain
    # ================================================================
    def _click_next(self):
        """
        Find Next button and click it via JS directly.
        No normal click attempt (always gets intercepted by overlay).
        No 10s wait on primary locator (always times out).
        """
        self._force_close_panels()

        btn_element = None
        # Short 5s timeout instead of 10s
        try:
            btn_element = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.XPATH, self.NEXT_BUTTON_XPATH))
            )
        except Exception:
            pass

        # Quick DOM fallback scan
        if btn_element is None:
            candidates = self.driver.find_elements(
                By.XPATH,
                "//button[@matsteppernext or @matStepperNext]"
                " | //button[normalize-space(.)='Next']",
            )
            for c in candidates:
                try:
                    if c.is_displayed() and c.is_enabled():
                        btn_element = c
                        break
                except Exception:
                    continue

        if btn_element is None:
            raise Exception("Next button not found")

        # JS click directly â€” skip normal click entirely
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
            btn_element,
        )
        log.info("Clicked Next button")

    def go_to_step2(self):
        """Step 1 -> Step 2 (Promoters)."""
        if not self.is_add_form_open():
            raise Exception("Dialog closed before clicking Next")
        log.info("  Next: Step 1 -> Step 2 (Promoters)")
        self._click_next()
        self.wait_seconds(0.8)

    def go_to_step3(self):
        """Step 2 (Promoters) -> Step 3 (Business Details)."""
        log.info("  Next: Step 2 -> Step 3 (Business Details)")
        self._click_next()
        self.wait_seconds(0.8)

    def go_to_step4(self):
        """Step 3 (Business) -> Step 4 (Infrastructure)."""
        log.info("  Next: Step 3 -> Step 4 (Infrastructure)")
        self._click_next()
        self.wait_seconds(0.8)

    def go_to_address_step(self, company_data):
        """Navigate: Promoters -> Address -> Business -> Infrastructure."""
        self.click_next_button("2", "3", "Address")
        self.fill_address_details(company_data)
        self.click_next_button("3", "4", "Business Activities")
        self.fill_business_details(company_data)
        self.click_next_button("4", "5", "Infrastructure Details")
        self.fill_infrastructure(company_data)
        self.click_next_button("5", "6", "Submit")

    def go_back_to_step1(self):
        self.click(self.STEP2_BACK_BUTTON)
        self.wait_seconds(1)

    # ================================================================
    # Fill Address Details
    # ================================================================

    def _select_random_from_dropdown(self, select_locator, label_name, exclude=None):
        """
        Open a mat-select dropdown, read ALL options from the UI,
        pick one randomly, click it, and return the selected text.
        Bulletproof against case mismatches and missing options.
        """
        # Open dropdown
        try:
            self.click(select_locator)
        except Exception:
            trigger = (
                "xpath",
                f"{select_locator[1]}//div[contains(@class,'mat-mdc-select-trigger')]",
            )
            self.click(trigger)
        self.wait_seconds(0.5)

        # Wait for options to appear
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='listbox'] mat-option"))
        )

        # Read all available options from UI
        options = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
        option_texts = [t for t in [opt.text.strip() for opt in options] if t and not t.startswith("Select") and t != "No results found"]

        # Fallback for newer Angular Material
        if not option_texts:
            options = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] [role='option']")
            option_texts = [opt.text.strip() for opt in options if opt.text.strip() and opt.text.strip() != "No results found"]

        if not option_texts:
            raise Exception(f"No options found in '{label_name}' dropdown")

        # Exclude already-used options
        if exclude:
            option_texts = [t for t in option_texts if t not in exclude]
            if not option_texts:
                raise Exception(f"No remaining options in {label_name} after excluding {exclude}")

        # Pick random
        selected = random.choice(option_texts)

        # Click using JS (avoids interception issues)
        for opt in options:
            if opt.text.strip() == selected:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
                    opt
                )
                break

        self.wait_seconds(0.3)
        log.info(f"Random '{label_name}' selected: '{selected}'")
        return selected


    def _fill_address_location_with_retry(self, row_index=1, max_attempts=15):
        """
        Select State -> District -> Taluka with retry logic.
        If Taluka has no options, retry with different random selections.
        """
        for attempt in range(1, max_attempts + 1):
            log.info(f"Address location attempt {attempt}/{max_attempts}")
            try:
                self._force_close_panels()
                self._select_random_from_dropdown(self._idx(self.STATE_SELECT, row_index), "State")
                self.wait_seconds(0.5)
                self._select_random_from_dropdown(self._idx(self.DISTRICT_SELECT, row_index), "District")
                self.wait_seconds(0.5)
                taluka = self._select_random_from_dropdown(self._idx(self.TALUKA_SELECT, row_index), "Taluka")
                if taluka:
                    return taluka
            except Exception as e:
                log.warning(f"Attempt {attempt} failed: {e}")
                self._force_close_panels()
        raise Exception(f"Could not find valid State/District/Taluka after {max_attempts} attempts")

    def fill_address_details(self, data, row_index=1):
        self._force_close_panels()
        log.info(f"Filling Address Details row {row_index}...")
        # Random address type: Registered or Corporate
        addr_types = ["Registered Address", "Corporate Address"]
        if data.get("address_type"):
            # Use data-provided type but swap if it conflicts with row 1
            chosen_type = data["address_type"]
        else:
            chosen_type = random.choice(addr_types)
        self._select_mat_option(self._idx(self.ADDRESS_TYPE_SELECT, row_index), chosen_type)
        if data.get("country"):
            self._select_mat_option(self._idx(self.COUNTRY_SELECT, row_index), data["country"])
            self.wait_seconds(0.5)
        selected_taluka = self._fill_address_location_with_retry(row_index=row_index)
        log.info(f"Address location resolved: Taluka = {selected_taluka}")
        uid = data.get("address", "").split(",")[0].strip() or str(row_index)
        address_text = f"{uid}, Test Street, {selected_taluka}"
        self.type_text(self._idx(self.ADDRESS_INPUT, row_index), address_text, clear_first=True)
        pin = str(random.randint(110000, 899999))
        self.type_text(self._idx(self.PIN_CODE_INPUT, row_index), pin, clear_first=True)
        # Store address record
        if "addresses" not in data:
            data["addresses"] = []
        while len(data["addresses"]) < row_index:
            data["addresses"].append({})
        data["addresses"][row_index - 1] = {
            "address_type": data.get("address_type", ""),
            "country": data.get("country", ""),
            "taluka": selected_taluka,
            "address": address_text,
            "pin_code": pin,
        }
        log.info(f"Address Details row {row_index} filled")

    def fill_promoters(self, promoter, row_index=1):
        log.info(f"Filling Promoters row {row_index}...")
        self._force_close_panels()
        name_loc = ("xpath", f"(//app-dynamic-details//input[@name=\'Name\'])[{row_index}]")
        remark_loc = ("xpath", f"(//app-dynamic-details//textarea[@name=\'Remark\'])[{row_index}]")
        self.type_text(name_loc, promoter.get("name", "Mr Test Promoter"), clear_first=True)
        self.type_text(remark_loc, promoter.get("remark", "Test remark."), clear_first=True)
        self.wait_seconds(0.3)
        log.info(f"Promoters row {row_index} filled")

    # ================================================================
    # Fill Step 3: Business Details
    # ================================================================
    def fill_business_details(self, data, row_index=1):
        log.info(f"Filling Business Details row {row_index}...")
        self._force_close_panels()
        self.type_text(self._idx(self.BUSINESS_MODEL_INPUT, row_index), data.get("business_model", ""), clear_first=True)
        self.wait_seconds(0.3)
        self.type_text(self._idx(self.MARKET_LINKAGES_INPUT, row_index), data.get("market_linkages", ""), clear_first=True)
        self.wait_seconds(0.3)
        self.type_text(self._idx(self.LINE_OF_BUSINESS_INPUT, row_index), data.get("line_of_business", ""), clear_first=True)
        self.wait_seconds(0.3)
        self.type_text(self._idx(self.ADDITIONAL_BUSINESS_INPUT, row_index), data.get("additional_business_activities", ""), clear_first=True)
        self.wait_seconds(0.5)
        log.info(f"Business Details row {row_index} filled")

    def fill_infrastructure(self, data, row_index=1):
        log.info(f"Filling Infrastructure row {row_index}...")
        self._force_close_panels()
        used_types = data.get("_used_infra_types", [])
        infra_type = self._select_random_from_dropdown(
            self._idx(self.INFRA_TYPE_SELECT, row_index),
            "Infrastructure Type", exclude=used_types
        )
        data["_used_infra_types"] = used_types + [infra_type]
        self.wait_seconds(0.5)
        self.type_text(self._idx(self.INFRA_LOCATION_INPUT, row_index), data.get("infra_location", "Test Location"), clear_first=True)
        self.wait_seconds(0.3)
        ownership = self._select_random_from_dropdown(self._idx(self.INFRA_OWNERSHIP_SELECT, row_index), "Ownership Type")
        self.wait_seconds(0.5)
        # Store infrastructure record
        if "infrastructure" not in data:
            data["infrastructure"] = []
        while len(data["infrastructure"]) < row_index:
            data["infrastructure"].append({})
        data["infrastructure"][row_index - 1] = {
            "infra_type": infra_type,
            "infra_location": data.get("infra_location", "Test Location"),
            "ownership_type": ownership,
        }
        log.info(f"Infrastructure row {row_index} filled")


    def search_company(self, company_name):
        """Search for a company in the table. Uses pure JS to avoid stale elements."""
        try:
            self._force_close_panels()
            self.wait_seconds(1)
            self.driver.execute_script(
                "var b=document.querySelector('button.search-btn');if(b)b.click();")
            self.wait_seconds(1)
            self.driver.execute_script(
                "var i=document.querySelector('.erp-search-wrapper input');"
                "if(i){var s=Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype,'value').set;"
                "s.call(i,arguments[0]);"
                "i.dispatchEvent(new Event('input',{bubbles:true}));"
                "i.dispatchEvent(new KeyboardEvent('keydown',"
                "{key:'Enter',keyCode:13,bubbles:true}));}",
                company_name)
            self.wait_seconds(2)
            rows = self.driver.find_elements(By.CSS_SELECTOR, 'td.cdk-column-name')
            for row in rows:
                if company_name.strip().lower() in row.text.strip().lower():
                    log.info(f"Company found in table: {row.text.strip()}")
                    return True
            log.warning(f"Company not found in table: {company_name}")
            return False
        except Exception as e:
            log.error(f"Search failed: {e}")
            return False

    def clear_search(self):
        """Clear search and restore full table."""
        try:
            if self.is_displayed(self.SEARCH_INPUT, timeout=3):
                self.type_text(self.SEARCH_INPUT, '', clear_first=True)
                self.wait_seconds(0.5)
                # Press Escape to close search
                from selenium.webdriver.common.keys import Keys
                self.driver.find_element(By.CSS_SELECTOR, '.erp-search-wrapper input').send_keys(Keys.ESCAPE)
                self.wait_seconds(0.5)
        except Exception:
            pass

    def verify_company_exists(self, company_name):
        """Full verification: search table for company name."""
        self.navigate_to_page()
        self.wait_seconds(2)
        found = self.search_company(company_name)
        self.clear_search()
        return found

    def submit(self):
        log.info("Submitting form...")
        self._force_close_panels()
        self.scroll_to_element(self.SUBMIT_BUTTON)
        self.wait_seconds(0.3)
        self.click(self.SUBMIT_BUTTON)
        self.wait_seconds(2)

    def cancel(self):
        self.click(self.CANCEL_BUTTON)
        self.wait_seconds(1)

    # ================================================================
    # One-call creation
    # ================================================================
    def create_company(self, company_data):
        log.info(f"Creating company: {company_data.get('company_name', 'N/A')}")
        self.open_add_form()
        self.fill_company_details(company_data)
        # Step 2: Promoters (random 1-4 rows)
        self.go_to_step2()
        promoters = company_data.get("promoters", [])
        for idx, promoter in enumerate(promoters, 1):
            if idx > 1:
                self.add_row()
            self.fill_promoters(promoter, row_index=idx)
        # Step 3: Address (fixed 2 rows)
        self.go_to_step3()
        num_addr = company_data.get("num_addresses", 1)
        addr_types = random.sample(["Registered Address", "Corporate Address"], min(num_addr, 2))
        for idx in range(1, num_addr + 1):
            if idx > 1:
                self.add_row()
            company_data["address_type"] = addr_types[(idx - 1) % len(addr_types)]
            self.fill_address_details(company_data, row_index=idx)
        # Step 4: Business Activities (random 1-4 rows)
        self.go_to_step4()
        num_biz = company_data.get("num_business_rows", 1)
        for idx in range(1, num_biz + 1):
            if idx > 1:
                self.add_row()
            self.fill_business_details(company_data, row_index=idx)
        # Step 5: Infrastructure (random 1-4 rows)
        self._click_next()
        num_infra = company_data.get("num_infra_rows", 1)
        for idx in range(1, num_infra + 1):
            if idx > 1:
                self.add_row()
            self.fill_infrastructure(company_data, row_index=idx)
        success = True
        error_msg = ""
        try:
            self.submit()
            msg = self.get_success_message(timeout=60)
            if msg:
                log.info(f"Server message: {msg}")
            else:
                log.warning("No success message detected")
            self.wait_seconds(3)
            if not msg:
                dialog_closed = self.is_dialog_closed()
                if not dialog_closed:
                    success = False
                    error_msg = "No success message and dialog did not close"
        except Exception as e:
            success = False
            error_msg = str(e)
        # Store submission record
        import copy
        CO_SUBMISSIONS.append({
            "data": copy.deepcopy(company_data),
            "status": "PASSED" if success else "FAILED",
            "error": error_msg,
        })
        log.info(f"Company submission recorded: {'PASSED' if success else 'FAILED'}")

    def create_bulk_companies(self, companies_list, on_progress=None):
        import time as _time
        total = len(companies_list)
        results = []
        for i, comp in enumerate(companies_list, 1):
            name = comp.get("company_name", f"Company_{i}")
            log.info(f"[{i}/{total}] Creating: {name}")
            result = {"index": i, "company_name": name, "status": "passed", "error": ""}
            start_time = _time.time()
            try:
                self.create_company(comp)
                result["status"] = "passed"
            except Exception as e:
                result["status"] = "failed"
                result["error"] = str(e)
                log.failed(f"Failed: {name} - {e}")
            elapsed = _time.time() - start_time
            result["duration"] = round(elapsed, 1)
            log.info(f"  [{i}/{total}] {name} -> {result['status'].upper()} ({elapsed:.1f}s)")
            try:
                self.click_cancel_or_dismiss_dialog()
                self.click_refresh()
                self.wait_seconds(2)
            except Exception:
                try:
                    self.navigate_to_page()
                    self.wait_seconds(2)
                except Exception:
                    pass
            results.append(result)
            if on_progress:
                on_progress(i, total, name)
        passed = sum(1 for r in results if r["status"] == "passed")
        failed = sum(1 for r in results if r["status"] == "failed")
        log.separator()
        log.info(f" BULK COMPLETE: {passed}/{total} passed, {failed} failed")
        log.separator()
        return results

    # ================================================================
    # Verification helpers
    # ================================================================
    def is_add_form_open(self):
        return self.is_displayed(self.COMPANY_NAME_INPUT, timeout=5)

    def is_step2_visible(self):
        """Check if Address Details step is visible."""
        return self.is_displayed(self.ADDRESS_INPUT, timeout=5)

    def is_dialog_closed(self):
        return not self.is_displayed(self.COMPANY_NAME_INPUT, timeout=60)

    def get_success_message(self, timeout=30):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        try:
            wait = WebDriverWait(self.driver, timeout)
            title_el = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#swal2-title"))
            )
            msg = title_el.text
            if msg:
                log.info(f"SweetAlert appeared: {msg}")
                try:
                    confirm_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".swal2-confirm"))
                    )
                    confirm_btn.click()
                    log.info("SweetAlert confirm button clicked")
                except Exception:
                    log.warning("Could not click SweetAlert confirm, waiting for auto-dismiss")
                    try:
                        WebDriverWait(self.driver, 5).until(
                            EC.invisibility_of_element_located((By.CSS_SELECTOR, "#swal2-title"))
                        )
                    except Exception:
                        pass
                return msg
        except Exception:
            pass
        toast = ("css", "snack-bar-container .mat-mdc-snack-bar-label, [role='alert']")
        if self.is_displayed(toast, timeout=5):
            return self.get_text(toast)
        return ""

    # ================================================================
    # Internal mat-select helpers
    # ================================================================
    def _select_mat_option(self, select_locator, option_text):
        try:
            self.click(select_locator)
        except Exception:
            trigger = (
                "xpath",
                f"{select_locator[1]}//div[contains(@class,'mat-mdc-select-trigger')]",
            )
            self.click(trigger)
        self.wait_seconds(0.3)
        opt_loc = (
            "xpath",
            f"//div[@role='listbox']//mat-option[contains(.,'{option_text}')]"
            f" | //div[@role='listbox']//div[@role='option'][contains(.,'{option_text}')]",
        )
        self.wait_for_visible(opt_loc, timeout=5)
        self.click(opt_loc)
        self.wait_seconds(0.3)
        log.info(f"Selected '{option_text}'")

    def _select_mat_options_multi(self, select_locator, option_texts):
        try:
            self.click(select_locator)
        except Exception:
            trigger = (
                "xpath",
                f"{select_locator[1]}//div[contains(@class,'mat-mdc-select-trigger')]",
            )
            self.click(trigger)
        self.wait_seconds(0.3)

        for opt in option_texts:
            opt_loc = (
                "xpath",
                f"//div[@role='listbox']//mat-option[contains(.,'{opt}')]"
                f" | //div[@role='listbox']//div[@role='option'][contains(.,'{opt}')]",
            )
            self.wait_for_visible(opt_loc, timeout=5)
            self.click(opt_loc)
            self.wait_seconds(0.2)
            log.info(f"Multi-select: '{opt}'")

        self._close_select_panel()

    def _enable_2fa_toggle(self):
        off = ("css", "app-slide-toggle-v2 .state-label.off.active")
        if self.is_displayed(off, timeout=3):
            log.info("Enabling 2FA toggle")
            self.click(self.TWO_FA_TOGGLE)
            self.wait_seconds(0.3)

    def click_cancel_or_dismiss_dialog(self):
        try:
            if self.is_displayed(self.CANCEL_BUTTON, timeout=2):
                self.click(self.CANCEL_BUTTON)
                return
        except Exception:
            pass
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        self.wait_seconds(0.5)
