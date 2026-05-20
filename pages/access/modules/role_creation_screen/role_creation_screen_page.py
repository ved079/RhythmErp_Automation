"""
Role Creation Screen – Page Object
RhythmERP  https://rhythmerp.algorhythms.in/#/master-setup/Rolecreationscreen

Form fields:
  - role_name    (input, required)
  - entity_type  (mat-select, required – dropdown of Entity Group names)

Create button: Submit
Edit button:   Update
Row actions:   eye (view) | edit (edit) | clock (history)
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

from common.base_page import BasePage
from config import EXPLICIT_WAIT


class RoleCreationScreenPage(BasePage):
    # ── URL ────────────────────────────────────────────────────────────
    PAGE_URL = "/#/master-setup/Rolecreationscreen"

    # ── Locators – Toolbar / Buttons ───────────────────────────────────
    BTN_ADD = (By.XPATH, "//button[contains(@class,'erp-add-btn') or contains(.,'Add Role')]")
    BTN_SUBMIT = (By.XPATH, "//button[contains(.,'Submit') or contains(.,'submit')]")
    BTN_CANCEL = (By.XPATH, "//button[contains(.,'Cancel') or contains(.,'cancel')]")
    BTN_UPDATE = (By.XPATH, "//button[contains(.,'Update') or contains(.,'update') and contains(@class,'mat-primary')]")
    BTN_CLOSE_ICON = (By.XPATH, "//button[contains(@class,'mat-mdc-icon-button')]//mat-icon[text()='close']/ancestor::button")
    BTN_YES_CONFIRM = (By.XPATH,
                       "//button[contains(@class,'swal2-confirm') or contains(.,'Yes')]")
    BTN_NO_CANCEL = (By.XPATH,
                     "//button[contains(@class,'swal2-cancel') or contains(.,'No')]")
    BTN_OK_SWEET = (By.XPATH,
                    "//button[contains(@class,'swal2-confirm') or contains(.,'OK')]")

    # ── Locators – Form Fields ─────────────────────────────────────────
    INPUT_ROLE_NAME = (By.CSS_SELECTOR, "input[formcontrolname='role_name']")
    SELECT_ENTITY_TYPE = (By.CSS_SELECTOR, "mat-select[formcontrolname='entity_type']")
    MAT_OPTION = (By.CSS_SELECTOR, "mat-option")

    # ── Locators – Validation Messages ─────────────────────────────────
    MSG_REQUIRED = (By.XPATH,
                    "//*[contains(@class,'mat-error') or contains(@class,'error')]")
    MSG_DUPLICATE = (By.XPATH,
                     "//*[contains(text(),'already exist') or contains(text(),'Already Exist') "
                     "or contains(text(),'duplicate') or contains(text(),'Duplicate') "
                     "or contains(text(),'already') or contains(text(),'Already')]")
    MSG_SUCCESS = (By.XPATH,
                   "//*[contains(@class,'swal2-title') and "
                   "(contains(text(),'Success') or contains(text(),'success'))]")
    MSG_SWEET_TITLE = (By.XPATH, "//h2[contains(@class,'swal2-title')]")

    # ── Locators – Table ───────────────────────────────────────────────
    TABLE_ROWS = (By.XPATH,
                  "//table//tbody/tr[not(contains(@class,'example-detail-row'))]")
    TABLE_NO_DATA = (By.XPATH,
                     "//table//tbody//td[contains(@class,'no-data') or "
                     "contains(text(),'No data') or contains(text(),'No record')]")
    SEARCH_INPUT = (By.XPATH,
                    "//input[@placeholder='Search' or contains(@class,'search') or "
                    "(@matinput and contains(@placeholder,'search'))]")

    # ── Locators – Row Action Buttons (feather icons) ──────────────────
    #   eye  = view,  edit = edit,  clock = history
    ROW_VIEW_BTN = (By.XPATH, "//app-feather-icons[@icon='eye']/ancestor::button")
    ROW_EDIT_BTN = (By.XPATH, "//app-feather-icons[@icon='edit']/ancestor::button")
    ROW_HISTORY_BTN = (By.XPATH, "//app-feather-icons[@icon='clock']/ancestor::button")

    # ── Locators – Edit Popup ──────────────────────────────────────────
    EDIT_POPUP = (By.XPATH, "//div[contains(@class,'edit_pop_up')]")
    VIEW_DIALOG = (By.XPATH, "//mat-dialog-container")
    HISTORY_DIALOG = (By.XPATH,
                      "//mat-dialog-container[contains(.,'History') or "
                      "contains(.,'history') or contains(.,'Audit')]")
    HISTORY_TABLE_ROWS = (By.XPATH,
                          "//mat-dialog-container//table//tbody/tr")

    # ── Locators – Backdrop / Overlay ──────────────────────────────────
    CDK_OVERLAY = (By.XPATH, "//div[contains(@class,'cdk-overlay-backdrop')]")

    # ==================================================================
    #  CONSTRUCTOR
    # ==================================================================
    def __init__(self, driver):
        super().__init__(driver)
        self.wait = WebDriverWait(driver, EXPLICIT_WAIT)
        self.actions = ActionChains(driver)

    # ==================================================================
    #  NAVIGATION
    # ==================================================================
    def navigate_to_role_creation_screen(self):
        base = self.driver.current_url.split("#")[0]
        self.driver.get(f"{base}{self.PAGE_URL}")
        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//table | //button[contains(@class,'erp-add-btn')]")))
        self._force_close_panels()

    # ==================================================================
    #  FORCE-CLOSE  (never Keys.ESCAPE)
    # ==================================================================
    def _force_close_panels(self):
        try:
            backdrops = self.driver.find_elements(*self.CDK_OVERLAY)
            for bd in backdrops:
                if bd.is_displayed():
                    bd.click()
                    break
        except Exception:
            pass
        self.driver.execute_script(
            "document.querySelectorAll('.cdk-overlay-backdrop.show').forEach(e=>e.click());"
            "document.querySelectorAll('.cdk-overlay-connected-position-bounding-flex').forEach(e=>e.remove());"
        )

    # ==================================================================
    #  CREATE  –  form interaction
    # ==================================================================
    def click_add_button(self):
        self._force_close_panels()
        add_btn = self.wait.until(EC.element_to_be_clickable(self.BTN_ADD))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", add_btn)
        add_btn.click()
        self.wait.until(EC.visibility_of_element_located(self.INPUT_ROLE_NAME))

    def fill_role_name(self, name: str):
        field = self.wait.until(EC.visibility_of_element_located(self.INPUT_ROLE_NAME))
        field.clear()
        field.send_keys(name)

    def select_entity_type_by_index(self, index: int = 0):
        select = self.wait.until(EC.element_to_be_clickable(self.SELECT_ENTITY_TYPE))
        select.click()
        options = self.wait.until(
            EC.presence_of_all_elements_located(self.MAT_OPTION))
        if index < len(options):
            options[index].click()
        else:
            options[0].click()
        self.wait_seconds(0.5)

    def select_entity_type_by_text(self, text: str):
        select = self.wait.until(EC.element_to_be_clickable(self.SELECT_ENTITY_TYPE))
        select.click()
        self.wait.until(EC.presence_of_all_elements_located(self.MAT_OPTION))
        matching = self.driver.find_elements(
            By.XPATH, f"//mat-option[contains(.,'{text}')]")
        if matching:
            matching[0].click()
        else:
            options = self.driver.find_elements(*self.MAT_OPTION)
            if options:
                options[0].click()
        self.wait_seconds(0.5)

    def click_submit_button(self):
        submit_btn = self.wait.until(EC.element_to_be_clickable(self.BTN_SUBMIT))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
        submit_btn.click()

    def click_update_button(self):
        update_btn = self.wait.until(EC.element_to_be_clickable(self.BTN_UPDATE))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", update_btn)
        update_btn.click()

    def click_cancel_button(self):
        cancel_btn = self.wait.until(EC.element_to_be_clickable(self.BTN_CANCEL))
        cancel_btn.click()

    def create_role(self, name: str, entity_type_index: int = 0):
        """Full flow: Add → fill name → select entity type → Submit."""
        self.click_add_button()
        self.fill_role_name(name)
        self.select_entity_type_by_index(entity_type_index)
        self.click_submit_button()

    # ==================================================================
    #  SWEET ALERT HELPERS
    # ==================================================================
    def confirm_sweet_alert_yes(self):
        yes_btn = self.wait.until(EC.element_to_be_clickable(self.BTN_YES_CONFIRM))
        yes_btn.click()

    def dismiss_sweet_alert_no(self):
        no_btn = self.wait.until(EC.element_to_be_clickable(self.BTN_NO_CANCEL))
        no_btn.click()

    def click_sweet_alert_ok(self):
        ok_btn = self.wait.until(EC.element_to_be_clickable(self.BTN_OK_SWEET))
        ok_btn.click()

    # ==================================================================
    #  READ MESSAGES
    # ==================================================================
    def get_sweet_alert_title(self) -> str:
        el = self.wait.until(EC.visibility_of_element_located(self.MSG_SWEET_TITLE))
        return el.text.strip()

    def get_required_field_error(self) -> str:
        el = self.wait.until(EC.visibility_of_element_located(self.MSG_REQUIRED))
        return el.text.strip()

    def get_all_required_errors(self) -> list:
        els = self.wait.until(
            EC.presence_of_all_elements_located(self.MSG_REQUIRED))
        return [e.text.strip() for e in els if e.is_displayed() and e.text.strip()]

    def is_duplicate_error_visible(self) -> bool:
        try:
            el = self.wait.until(
                EC.visibility_of_element_located(self.MSG_DUPLICATE))
            return el.is_displayed()
        except Exception:
            return False

    def is_success_message_visible(self) -> bool:
        try:
            el = self.wait.until(
                EC.visibility_of_element_located(self.MSG_SUCCESS))
            return el.is_displayed()
        except Exception:
            return False

    # ==================================================================
    #  TABLE  HELPERS
    # ==================================================================
    def get_table_row_count(self) -> int:
        try:
            rows = self.driver.find_elements(*self.TABLE_ROWS)
            return len(rows)
        except Exception:
            return 0

    def is_role_in_table(self, role_name: str) -> bool:
        try:
            rows = self.driver.find_elements(*self.TABLE_ROWS)
            for row in rows:
                if role_name.lower() in row.text.lower():
                    return True
            return False
        except Exception:
            return False

    def get_row_index_by_role_name(self, role_name: str) -> int:
        """Return 1-based row index, or -1 if not found.
        Name is in column 1 (0-indexed)."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        for idx, row in enumerate(rows, start=1):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2 and role_name.lower() in cells[1].text.lower():
                return idx
        return -1

    def get_cell_text_by_row_and_col(self, row_idx: int, col_idx: int) -> str:
        cell = self.driver.find_element(
            By.XPATH, f"//table//tbody/tr[{row_idx}]/td[{col_idx}]")
        return cell.text.strip()

    # ==================================================================
    #  ROW  ACTION  BUTTONS  (eye / edit / clock)
    # ==================================================================
    def _get_row_action_btns(self, row_idx: int):
        """Return list of action button elements for a specific row."""
        row = self.driver.find_element(
            By.XPATH, f"//table//tbody/tr[{row_idx}]")
        return row.find_elements(By.CSS_SELECTOR, "button.tblActnBtn")

    def click_view_button(self, row_idx: int):
        self._force_close_panels()
        btns = self._get_row_action_btns(row_idx)
        assert len(btns) >= 1, f"No action buttons found in row {row_idx}"
        # 1st button = eye (view)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", btns[0])
        btns[0].click()
        self.wait.until(EC.visibility_of_element_located(self.VIEW_DIALOG))

    def click_edit_button(self, row_idx: int):
        self._force_close_panels()
        btns = self._get_row_action_btns(row_idx)
        assert len(btns) >= 2, f"No edit button found in row {row_idx}"
        # 2nd button = edit
        self.driver.execute_script("arguments[0].scrollIntoView(true);", btns[1])
        btns[1].click()
        self.wait.until(EC.visibility_of_element_located(self.EDIT_POPUP))

    def click_history_button(self, row_idx: int):
        self._force_close_panels()
        btns = self._get_row_action_btns(row_idx)
        assert len(btns) >= 3, f"No history button found in row {row_idx}"
        # 3rd button = clock (history)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", btns[2])
        btns[2].click()
        self.wait.until(EC.visibility_of_element_located(self.HISTORY_DIALOG))

    # ==================================================================
    #  VIEW  DIALOG
    # ==================================================================
    def is_view_dialog_open(self) -> bool:
        try:
            el = self.wait.until(
                EC.visibility_of_element_located(self.VIEW_DIALOG))
            return el.is_displayed()
        except Exception:
            return False

    def get_view_dialog_text(self) -> str:
        el = self.wait.until(
            EC.visibility_of_element_located(self.VIEW_DIALOG))
        return el.text.strip()

    def close_view_dialog(self):
        # Try Close text button first
        try:
            close_btn = self.driver.find_element(
                By.XPATH, "//mat-dialog-container//button[contains(.,'Close')]")
            close_btn.click()
        except Exception:
            # Try X icon button
            try:
                close_btn = self.driver.find_element(
                    By.XPATH, "//mat-dialog-container//button[mat-icon[text()='close']]")
                close_btn.click()
            except Exception:
                pass
        self._force_close_panels()

    # ==================================================================
    #  EDIT  POPUP
    # ==================================================================
    def get_role_name_field_value(self) -> str:
        field = self.wait.until(
            EC.visibility_of_element_located(self.INPUT_ROLE_NAME))
        return field.get_attribute("value").strip()

    def get_selected_entity_type(self) -> str:
        try:
            select = self.wait.until(
                EC.visibility_of_element_located(self.SELECT_ENTITY_TYPE))
            value_text = select.find_element(
                By.CSS_SELECTOR, ".mat-mdc-select-value-text"
            ).text.strip()
            return value_text
        except Exception:
            return ""

    def is_role_name_field_readonly(self) -> bool:
        field = self.wait.until(
            EC.visibility_of_element_located(self.INPUT_ROLE_NAME))
        return field.get_attribute("readonly") is not None or \
               field.get_attribute("disabled") is not None

    def is_edit_popup_open(self) -> bool:
        try:
            el = self.wait.until(
                EC.visibility_of_element_located(self.EDIT_POPUP))
            return el.is_displayed()
        except Exception:
            return False

    def close_edit_popup(self):
        """Close the edit popup via Cancel or X button."""
        try:
            cancel_btn = self.driver.find_element(*self.BTN_CANCEL)
            cancel_btn.click()
        except Exception:
            try:
                close_btn = self.driver.find_element(*self.BTN_CLOSE_ICON)
                close_btn.click()
            except Exception:
                pass
        self._force_close_panels()

    # ==================================================================
    #  HISTORY  DIALOG
    # ==================================================================
    def get_history_row_count(self) -> int:
        rows = self.wait.until(
            EC.presence_of_all_elements_located(self.HISTORY_TABLE_ROWS))
        return len(rows)

    def is_history_dialog_open(self) -> bool:
        try:
            el = self.wait.until(
                EC.visibility_of_element_located(self.HISTORY_DIALOG))
            return el.is_displayed()
        except Exception:
            return False

    def close_history_dialog(self):
        self.close_view_dialog()  # Same close approach

    # ==================================================================
    #  SEARCH
    # ==================================================================
    def search_role(self, search_text: str):
        self._force_close_panels()
        search_field = self.wait.until(
            EC.visibility_of_element_located(self.SEARCH_INPUT))
        search_field.clear()
        search_field.send_keys(search_text)

    def clear_search(self):
        search_field = self.wait.until(
            EC.visibility_of_element_located(self.SEARCH_INPUT))
        search_field.clear()

    # ==================================================================
    #  SORT
    # ==================================================================
    def click_sort_header(self, col_index: int):
        header = self.driver.find_element(
            By.XPATH, f"//thead/tr/th[{col_index}]")
        self.driver.execute_script("arguments[0].scrollIntoView(true);", header)
        header.click()

    # ==================================================================
    #  FORM  STATE
    # ==================================================================
    def is_save_button_enabled(self) -> bool:
        try:
            btn = self.driver.find_element(*self.BTN_SUBMIT)
            return btn.is_enabled()
        except Exception:
            return False

    def is_add_button_visible(self) -> bool:
        try:
            btn = self.driver.find_element(*self.BTN_ADD)
            return btn.is_displayed()
        except Exception:
            return False

    def is_form_open(self) -> bool:
        try:
            el = self.driver.find_element(*self.INPUT_ROLE_NAME)
            return el.is_displayed()
        except Exception:
            return False

    # ==================================================================
    #  TABLE  EMPTY  STATE
    # ==================================================================
    def is_no_data_displayed(self) -> bool:
        try:
            el = self.driver.find_element(*self.TABLE_NO_DATA)
            return el.is_displayed()
        except Exception:
            return False

    # ==================================================================
    #  GENERIC  WAIT  FOR  TABLE  UPDATE
    # ==================================================================
    def wait_for_table_to_load(self, min_rows: int = 1):
        self.wait.until(
            lambda d: len(d.find_elements(*self.TABLE_ROWS)) >= min_rows)

    def wait_for_success_and_dismiss(self) -> str:
        title = self.get_sweet_alert_title()
        self.click_sweet_alert_ok()
        return title