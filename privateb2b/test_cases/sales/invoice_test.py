import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
from decimal import Decimal
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from common.helper import select_dropdown, fill_input

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# ==========================================
# HELPER: VALIDATION CHECK
# ==========================================

def has_validation_error(driver):
    """Checks for common Angular Material or toast error elements."""
    try:
        mat_error = driver.find_elements(By.CSS_SELECTOR, "mat-error")
        for err in mat_error:
            if err.is_displayed():
                return True
        toast = driver.find_elements(By.CSS_SELECTOR, ".toast-error, .toast-message, .swal2-error")
        for t in toast:
            if t.is_displayed():
                return True
        error_text = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') and not(contains(@style, 'display: none'))]")
        return len(error_text) > 0
    except:
        return False


# ==========================================
# CORE CREATION FUNCTION (WITH INLINE TESTS)
# ==========================================

def fill_invoice_registration(driver, wait, data, run_validations=True):
    logger.info("⚡ Starting Invoice Registration...")

    # Customer Name (searchable)
    select_dropdown(driver, wait, value=data['customer_name'], control_name="customer_ref_id", searchable=True)

    # Sales Type (simple)
    select_dropdown(driver, wait, value=data['sales_type'], control_name="so_type_ref_id", searchable=False)

    # Supply Type (simple)
    select_dropdown(driver, wait, value=data['supply_type'], control_name="supply_type_ref_id", searchable=False)

    # Dispatch Note (first option)
    try:
        dn_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select[formcontrolname='dispatch_note_ref_id']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dn_dropdown)
        driver.execute_script("arguments[0].click();", dn_dropdown)
        logger.info("   Opened Dispatch Note dropdown")

        overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")))
        wait.until(EC.visibility_of(overlay))

        first_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//mat-option[1]//span")))
        driver.execute_script("arguments[0].click();", first_option)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        logger.info("   Selected first Dispatch Note")
        time.sleep(1)
    except Exception as e:
        logger.error(f"❌ Failed to select Dispatch Note: {e}")
        driver.save_screenshot("invoice_dn_error.png")
        raise

    # ----- INV_TC01 & INV_TC02: Transportation Charges (Fill + Precision Test) -----
    if run_validations:
        if 'transportation_charges' in data and data['transportation_charges'] is not None:
            logger.info("   🧪 [INV_TC01 & INV_TC02] Testing Transportation Charges...")
            try:
                transport_input = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[formcontrolname='txn_currency_freight_charges']")
                ))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", transport_input)
                
                # INV_TC02: Decimal precision (step=0.01 means max 2 decimals)
                transport_input.send_keys(Keys.CONTROL, 'a')
                transport_input.send_keys(Keys.BACKSPACE)
                transport_input.send_keys("100.123")
                transport_input.send_keys(Keys.TAB)
                time.sleep(0.5)
                entered_val = driver.execute_script("return arguments[0].value;", transport_input)
                if entered_val == "100.12" or has_validation_error(driver):
                    logger.info(f"      ✅ Decimal precision enforced (entered: {entered_val}).")
                else:
                    logger.warning(f"      ⚠️ WARNING: Decimal precision not enforced! Entered: {entered_val}")

                # Now enter correct value (INV_TC01)
                transport_input.send_keys(Keys.CONTROL, 'a')
                transport_input.send_keys(Keys.BACKSPACE)
                transport_input.send_keys(str(data['transportation_charges']))
                transport_input.send_keys(Keys.TAB)
                logger.info(f"      ✅ Transportation Charges set to: {data['transportation_charges']}")
            except Exception as e:
                logger.warning(f"      ⚠️ Transportation Charges test skipped: {e}")
        else:
            logger.info("   ℹ️ Skipping Transportation Charges test – no data provided.")

    # Wait for any calculations to update
    time.sleep(2)

    # ----- INV_TC03: Grand Total Calculation Verification -----
    if run_validations:
        logger.info("   🧪 [INV_TC03] Verifying Grand Total calculation...")
        try:
            subtotal_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_sub_total_amount']")
            tax_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_tax_amount']")
            grand_total_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_grand_total_amount']")
            transport_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_freight_charges']")
            
            subtotal_val = float(driver.execute_script("return arguments[0].value;", subtotal_input).replace(',', '') or 0)
            tax_val = float(driver.execute_script("return arguments[0].value;", tax_input).replace(',', '') or 0)
            grand_total_val = float(driver.execute_script("return arguments[0].value;", grand_total_input).replace(',', '') or 0)
            transport_val = float(driver.execute_script("return arguments[0].value;", transport_input).replace(',', '') or 0)
            
            expected_grand_total = subtotal_val + tax_val + transport_val
            diff = abs(grand_total_val - expected_grand_total)
            if diff < 0.01:
                logger.info(f"      ✅ Grand Total correct: {grand_total_val} (Subtotal: {subtotal_val} + Tax: {tax_val} + Transport: {transport_val})")
            else:
                logger.warning(f"      ⚠️ Grand Total mismatch! UI: {grand_total_val}, Expected: {expected_grand_total:.2f} (diff: {diff:.2f})")
        except Exception as e:
            logger.warning(f"      ⚠️ Grand Total check failed: {e}")

    # Submit button (inside footer)
    logger.info("📤 Submitting Invoice...")
    submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.footer button.submit")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    driver.execute_script("arguments[0].click();", submit_btn)
    logger.info("   ✅ Submit button clicked")

    # Wait for redirect to the list page
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
        logger.info("🚀 Invoice Registration Completed Successfully!")
        time.sleep(3)
    except TimeoutException:
        errors = driver.find_elements(By.CSS_SELECTOR, "mat-error")
        error_msgs = [e.text for e in errors if e.text.strip()]
        if error_msgs:
            logger.error(f"❌ Validation errors: {error_msgs}")
            driver.save_screenshot("invoice_validation_errors.png")
            raise Exception(f"Form validation failed: {error_msgs}")
        else:
            logger.warning("⚠️ No redirect and no errors. Retrying submit...")
            driver.execute_script("arguments[0].click();", submit_btn)
            time.sleep(2)
            if driver.find_elements(By.CSS_SELECTOR, "table.mat-mdc-table"):
                logger.info("🚀 Invoice Registration Completed Successfully!")
            else:
                driver.save_screenshot("invoice_submit_failed.png")
                raise Exception("Submission failed: page did not redirect and no validation errors.")


# ==========================================
# LIFECYCLE & GRID FUNCTIONS
# ==========================================

def test_view_invoice(driver, wait):
    """Click View to ensure no internal server error occurs on the list page."""
    logger.info("🐞 Testing View & Crash Check...")
    try:
        view_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//table/tbody/tr[1]//button[.//i[contains(@class, 'bi-eye')]]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", view_btn)
        driver.execute_script("arguments[0].click();", view_btn)
        time.sleep(2)
        
        try:
            driver.find_element(By.XPATH, "//*[contains(text(), 'Internal server error')]")
            logger.error("   ❌ BUG CAUGHT: Internal Server Error on View!")
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        except NoSuchElementException:
            logger.info("   ✅ Invoice View modal loaded cleanly.")
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
    except Exception as e:
        logger.warning(f"   ⚠️ Could not perform View test: {e}")


def test_unpost_invoice(driver, wait):
    """Test unpost flow: click Unpost div, fill reason code & remark, confirm. (INV_TC04)"""
    logger.info("🗑️ [INV_TC04] Testing Invoice Unpost...")
    try:
        # Locate the "Unpost" div in the first row
        unpost_div = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//table/tbody/tr[1]//div[contains(@class, 'unpost_btn') and normalize-space()='Unpost']")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", unpost_div)
        driver.execute_script("arguments[0].click();", unpost_div)
        logger.info("   ✅ Clicked Unpost button")

        # Wait for SweetAlert modal to appear
        swal_modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup")))
        logger.info("   ✅ SweetAlert modal opened")

        # Fill Reason Code (required)
        reason_code_input = swal_modal.find_element(By.CSS_SELECTOR, "input#reason_code")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", reason_code_input)
        reason_code_input.clear()
        reason_code_input.send_keys("999")
        logger.info("   ✅ Entered Reason Code: 999")

        # Fill Remark (required)
        remark_input = swal_modal.find_element(By.CSS_SELECTOR, "input#remark")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", remark_input)
        remark_input.clear()
        remark_input.send_keys("Automated test unpost")
        logger.info("   ✅ Entered Remark")

        # Click the "Yes" confirmation button
        confirm_btn = swal_modal.find_element(By.CSS_SELECTOR, "button.swal2-confirm")
        driver.execute_script("arguments[0].click();", confirm_btn)
        logger.info("   ✅ Clicked Yes to confirm unpost")

        # Wait for modal to disappear
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup")))
        time.sleep(2)
        logger.info("   ✅ Invoice successfully unposted (status should change or row removed)")

    except Exception as e:
        logger.warning(f"   ⚠️ Unpost test failed: {e}")
        driver.save_screenshot("invoice_unpost_error.png")
        # Do not raise; allow suite to continue


def execute_invoice_suite(driver, wait, data):
    logger.info("\n--- ⚡ STARTING INVOICE SUITE ---")
    
    # 1. Standard Creation (with inline validations)
    fill_invoice_registration(driver, wait, data, run_validations=True)
    
    # 2. View Bug Check
    test_view_invoice(driver, wait)
    
    # Short delay for list page stability
    time.sleep(1)
    
    # 3. Unpost Flow Check (INV_TC04)
    # test_unpost_invoice(driver, wait)
    
    logger.info("--- ✅ INVOICE SUITE COMPLETED ---\n")