"""
common/table_helpers.py
-----------------------
Reusable table search + verify for any app-table in the PACS app.

Usage:
    from common.table_helpers import verify_in_table
    verify_in_table(driver, wait, "Admin Role", "name")
    verify_in_table(driver, wait, "testuser123", "username")
"""

from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import logging

logger = logging.getLogger(__name__)


def verify_in_table(driver, wait, search_value, column_class=None,
                    check_date=False, date_column="created_date_time",
                    date_format="%d-%b-%Y"):
    """..."""
    logger.info(f"  Verifying '{search_value}' in table...")

    # ── 0. Dismiss any open overlays / popups ─────────────────────
    try:
        overlays = driver.find_elements(By.CSS_SELECTOR,
            ".swal2-container, .cdk-overlay-backdrop, .ngx-spinner-overlay")
        for ov in overlays:
            try:
                driver.execute_script("arguments[0].remove();", ov)
            except Exception:
                pass
        time.sleep(0.3)
    except Exception:
        pass

    # ── 1. Click search button ────────────────────────────────────
    try:
        search_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.search-btn, button[aria-label='Search']")
        ))
        driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(0.5)
    except Exception:
        logger.warning("  Could not click search button, trying input directly.")

    # ── 2. Type into search input ─────────────────────────────────
    search_input = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR,
         "#erpSearchInput, "
         "input.erp-search-input, "
         ".erp-search-container input, "
         "input.search-input")
    ))
    search_input.clear()
    search_input.send_keys(search_value)
    search_input.send_keys("\n")  # press Enter to trigger search
    time.sleep(2)  # extra wait for table filter

    # ── 3. Check for "No results" row ────────────────────────────
    try:
        no_data = driver.find_element(
            By.XPATH,
            "//*[contains(@class,'mat-mdc-no-data-row') or "
            "contains(text(),'No results found') or "
            "contains(text(),'No data found')]"
        )
        if no_data.is_displayed():
            raise Exception(
                f"Verification FAILED: '{search_value}' not found in table "
                f"(table shows: '{no_data.text.strip()}')"
            )
    except NoSuchElementException:
        pass

    # ── 4. Find value: specific column first, then any cell ───────
    found = False

    if column_class:
        try:
            wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 f"//td[contains(@class,'cdk-column-{column_class}')]"
                 f"//span[normalize-space()='{search_value}']")
            ))
            logger.info(f"  Found '{search_value}' in 'cdk-column-{column_class}'.")
            found = True
        except TimeoutException:
            logger.warning(
                f"  '{search_value}' not found in 'cdk-column-{column_class}'. "
                f"Falling back to any-cell search..."
            )

    if not found:
        try:
            wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 f"//tbody//td[normalize-space()='{search_value}' or "
                 f".//span[normalize-space()='{search_value}']]")
            ))
            logger.info(f"  Found '{search_value}' in table (any-cell match).")
            found = True
        except TimeoutException:
            raise Exception(
                f"Verification FAILED: '{search_value}' not found anywhere in table."
            )

    # ── 5. Optionally check date matches today ────────────────────
    if check_date:
        today_str = datetime.now().strftime(date_format)
        try:
            date_cell = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 f"//td[contains(@class,'cdk-column-{date_column}')]//span")
            ))
            date_text = date_cell.text.strip()
            if date_text.startswith(today_str):
                logger.info(f"  Date verified: '{date_text}' matches today ({today_str}).")
            else:
                raise Exception(
                    f"Date mismatch: expected '{today_str}', got '{date_text}'."
                )
        except TimeoutException:
            logger.warning(f"  '{date_column}' column not found — skipping date check.")

    # ── 6. Clear search ───────────────────────────────────────────
    try:
        search_input.clear()
        search_input.send_keys("\n")
        time.sleep(0.5)
    except Exception:
        pass

    logger.info(f"  Verification PASSED for '{search_value}'.")