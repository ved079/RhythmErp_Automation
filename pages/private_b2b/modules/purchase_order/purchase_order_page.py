import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT


class PurchaseOrderPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/purchase/purchase-order"

    ADD_BUTTON = ("xpath", "//button[contains(normalize-space(.), 'Add Purchase Order')]")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[mattooltip='Search'], button.search-icon")
    SEARCH_INPUT = ("css", "#erpSearchInput, input.erp-search-input")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")

    TABLE = ("css", "table#excel-table, table.mat-mdc-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr, table.mat-mdc-table tbody tr.mat-mdc-row")

    ROW_MENU_TRIGGER = ("xpath", "//table/tbody/tr[1]/td[1]//button")
    ROW_MENU_VIEW = ("xpath", "//span[contains(@class,'erp-menu-title') and contains(.,'View')]")
    ROW_MENU_EDIT = ("xpath", "//span[contains(@class,'erp-menu-title') and contains(.,'Edit')]")

    FORM_POPUP = ("xpath", "//mat-dialog-container")
    FORM_HEADING = ("css", "div.popup-title h4, .modal-header h4")

    SUBMIT_BUTTON = ("xpath", "//div[contains(@class,'form-footer')]//button[contains(.,'Submit')]")
    UPDATE_BUTTON = ("xpath", "//div[contains(@class,'form-footer')]//button[contains(.,'Update')]")
    CANCEL_BUTTON = ("xpath", "//div[contains(@class,'form-footer')]//button[contains(.,'Cancel')]")
    CLOSE_BUTTON = ("xpath", "//div[contains(@class,'form-footer')]//button[contains(.,'Close')]")

    TABLE_FIRST_DATA_CELL = ("css", "table#excel-table tbody tr.mat-mdc-row td:nth-child(4), table.mat-mdc-table tbody tr.mat-mdc-row td:nth-child(4)")

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    def navigate_to_page(self):
        log.info("Navigating to Purchase Order page...")
        self.navigate_to(self.PAGE_URL)
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        for attempt in range(3):
            try:
                if "purchase-order" not in self.driver.current_url:
                    self.navigate_to(self.PAGE_URL)
                    time.sleep(2)
                WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table"))
                )
                return
            except TimeoutException:
                log.warning(f"PO table not found (attempt {attempt+1}), refreshing...")
                self.driver.refresh()
                time.sleep(4)
        log.warning("PO table not found within timeout")

    def open_add_form(self):
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.element_to_be_clickable(self.ADD_BUTTON))
        try:
            self.click(self.ADD_BUTTON)
        except Exception:
            self.click_with_retry(self.ADD_BUTTON)
        time.sleep(2)
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "form.ng-pristine")) > 0
            )
        except TimeoutException:
            log.warning("Add form did not open within timeout")

    def _is_form_popup_open(self):
        try:
            return len(self.driver.find_elements(By.CSS_SELECTOR, "form.ng-pristine")) > 0
        except Exception:
            return False

    def force_close_form_popup(self):
        try:
            cancel_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.CANCEL_BUTTON)
            )
            cancel_btn.click()
        except Exception:
            pass
        self.navigate_to_page()
        self._force_close_panels()

    def click_refresh(self, retry_on_empty=False):
        try:
            self.click(self.REFRESH_BUTTON)
        except Exception:
            self.click_with_retry(self.REFRESH_BUTTON)
        time.sleep(2)
        if not self._wait_for_table_rows(timeout=15) and retry_on_empty:
            log.warning("No rows after refresh, retrying...")
            try:
                self.click(self.REFRESH_BUTTON)
            except Exception:
                pass
            time.sleep(3)
            self._wait_for_table_rows(timeout=15)

    def _wait_for_table_rows(self, timeout=15):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table tbody tr.mat-mdc-row"))
            )
            return True
        except TimeoutException:
            return False

    def get_table_row_count(self) -> int:
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table.mat-mdc-table tbody tr.mat-mdc-row")
            return len(rows)
        except Exception:
            return 0

    def search_po(self, search_term: str) -> bool:
        try:
            toggle = self.driver.find_element(By.CSS_SELECTOR, 'button[mattooltip="Search"]')
            self.driver.execute_script("arguments[0].click();", toggle)
            time.sleep(1)
        except Exception:
            pass
        try:
            self.find_visible_element(self.SEARCH_INPUT, timeout=5)
            self.type_text(self.SEARCH_INPUT, search_term)
            time.sleep(1.5)
            self._wait_for_table_rows(timeout=10)
            return self.get_table_row_count() >= 1
        except Exception:
            return False

    def search_po_verify_row(self, search_term: str) -> bool:
        if not self.search_po(search_term):
            return False
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: any(
                    search_term in c.text
                    for c in d.find_elements(By.CSS_SELECTOR,
                        "table.mat-mdc-table tbody tr.mat-mdc-row td:nth-child(4)")
                )
            )
            return True
        except (TimeoutException, Exception):
            return False

    def click_view_first_row(self):
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.element_to_be_clickable(self.ROW_MENU_TRIGGER))
        try:
            self.click(self.ROW_MENU_TRIGGER)
        except Exception:
            self.click_with_retry(self.ROW_MENU_TRIGGER)
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.ROW_MENU_VIEW)
            )
        except Exception:
            pass
        try:
            self.click(self.ROW_MENU_VIEW)
        except Exception:
            self.click_with_retry(self.ROW_MENU_VIEW)

    def edit_first_row(self):
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.element_to_be_clickable(self.ROW_MENU_TRIGGER))
        try:
            self.click(self.ROW_MENU_TRIGGER)
        except Exception:
            self.click_with_retry(self.ROW_MENU_TRIGGER)
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.ROW_MENU_EDIT)
            )
        except Exception:
            pass
        try:
            self.click(self.ROW_MENU_EDIT)
        except Exception:
            self.click_with_retry(self.ROW_MENU_EDIT)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.FORM_POPUP)
            )
        except Exception:
            pass

    def has_update_button(self) -> bool:
        try:
            btn = self.find_clickable_element(self.UPDATE_BUTTON, timeout=5)
            return btn is not None and btn.is_displayed()
        except Exception:
            return False

    def verify_view_popup_read_only(self) -> bool:
        try:
            has_submit = self.is_displayed(self.SUBMIT_BUTTON, timeout=2)
            has_update = self.is_displayed(self.UPDATE_BUTTON, timeout=2)
            if has_submit or has_update:
                return False
            return True
        except Exception:
            return True

    def close_popup(self):
        try:
            self.click(self.CLOSE_BUTTON)
        except Exception:
            try:
                self.click(self.CANCEL_BUTTON)
            except Exception:
                pass
        try:
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located(self.FORM_POPUP)
            )
        except Exception:
            pass

    def get_form_field_value(self, label: str) -> str:
        locator = ("xpath", f"//mat-label[contains(.,'{label}')]/ancestor::mat-form-field//input")
        try:
            return self.get_value(locator)
        except Exception:
            return ""

    def _force_close_panels(self):
        try:
            self.driver.execute_script("""
                document.querySelectorAll('div.cdk-overlay-pane').forEach(el => el.remove());
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove());
            """)
        except Exception:
            pass
