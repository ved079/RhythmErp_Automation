import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from common.helper import select_dropdown

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

def trigger_angular_change(driver, element):
    """Force Angular to register changes by dispatching input and change events."""
    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element)
    # Also click away to blur
    body = driver.find_element(By.TAG_NAME, "body")
    ActionChains(driver).move_to_element_with_offset(body, 10, 10).click().perform()


# ==========================================
# CORE CREATION FUNCTION (WITH INLINE TESTS)
# ==========================================

def fill_receipt_registration(driver, wait, data, run_validations=True):
    logger.info("⚡ Starting Receipt Registration...")

    # Wait for the page to be fully loaded before starting
    logger.info("   ⏳ Waiting for page to load...")
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loader, .spinner, .cdk-overlay-backdrop")))
        time.sleep(1)
    except:
        pass

    # Transaction Date (if provided)
    if 'transaction_date' in data and data['transaction_date']:
        try:
            date_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[formcontrolname='transaction_date']")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", date_input)
            date_input.send_keys(Keys.CONTROL, 'a')
            date_input.send_keys(Keys.BACKSPACE)
            date_input.send_keys(data['transaction_date'])
            date_input.send_keys(Keys.TAB)
            trigger_angular_change(driver, date_input)  # force Angular update
            logger.info(f"  ✅ Filled Transaction Date: {data['transaction_date']}")
            
            # Force close the calendar overlay
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1) 
        except Exception as e:
            logger.warning(f"  ⚠️ Could not set Transaction Date: {e}")

    # Receipt Type
    select_dropdown(driver, wait, value=data['receipt_type'], control_name="payment_type_ref_id", searchable=False)

    # Department, Division, Location, Type of Sale
    select_dropdown(driver, wait, value=data['department'], label_text="Department", searchable=False)
    select_dropdown(driver, wait, value=data['division'], label_text="Division", searchable=False)
    select_dropdown(driver, wait, value=data['location'], label_text="Location", searchable=False)
    select_dropdown(driver, wait, value=data['type_of_sale'], label_text="Type of Sale", searchable=False)

    # Customer Name
    select_dropdown(driver, wait, value=data['customer_name'], control_name="customer_ref_id", searchable=True)

    # Payment Method
    select_dropdown(driver, wait, value=data['payment_method'], control_name="payment_method_ref_id", searchable=False)

    # Company Account Number (optional)
    try:
        if 'company_account_number' in data and data['company_account_number']:
            if data['company_account_number'] == "First Option":
                acc_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select[formcontrolname='tenant_account_ref_id']")))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", acc_dropdown)
                driver.execute_script("arguments[0].click();", acc_dropdown)
                overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")))
                wait.until(EC.visibility_of(overlay))
                first_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//mat-option[1]//span")))
                driver.execute_script("arguments[0].click();", first_option)
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                logger.info("   Selected first Company Account Number")
            else:
                select_dropdown(driver, wait, value=data['company_account_number'], control_name="tenant_account_ref_id", searchable=False)
        else:
            logger.info("   ℹ️ Company Account Number not provided, skipping")
    except Exception as e:
        logger.warning(f"   ⚠️ Could not set Company Account Number: {e}")

    # Customer Bank Name (optional)
    try:
        if 'customer_bank_name' in data and data['customer_bank_name']:
            if data['customer_bank_name'] == "First Option":
                bank_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select[formcontrolname='bank_detail_ref_id']")))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", bank_dropdown)
                driver.execute_script("arguments[0].click();", bank_dropdown)
                overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")))
                wait.until(EC.visibility_of(overlay))
                first_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//mat-option[1]//span")))
                driver.execute_script("arguments[0].click();", first_option)
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                logger.info("   Selected first Customer Bank Name")
            else:
                select_dropdown(driver, wait, value=data['customer_bank_name'], control_name="bank_detail_ref_id", searchable=False)
        else:
            logger.info("   ℹ️ Customer Bank Name not provided, skipping")
    except Exception as e:
        logger.warning(f"   ⚠️ Could not set Customer Bank Name: {e}")

    # ----- INLINE VALIDATIONS (RCP_TC01, RCP_TC02, RCP_TC03) -----
    if run_validations:
        logger.info("   🧪 Running Receipt inline validations...")
        try:
            time.sleep(1)
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody.main_tbody tr")
            if not rows:
                logger.warning("      ⚠️ No invoice rows found; skipping validations.")
            else:
                row = rows[0]
                
                cells = row.find_elements(By.CSS_SELECTOR, "td.col_input")
                if len(cells) < 4:
                    raise Exception("Could not find invoice amount cell")
                outstanding_text = cells[2].text.strip().replace(',', '')
                outstanding = float(outstanding_text) if outstanding_text else 0.0
                
                if outstanding <= 0:
                    logger.warning("      ⚠️ Outstanding amount is zero; skipping amount validations.")
                else:
                    checkbox = row.find_element(By.CSS_SELECTOR, "mat-checkbox[formcontrolname='is_check']")
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)
                    driver.execute_script("arguments[0].click();", checkbox)
                    trigger_angular_change(driver, checkbox)  # force update after checkbox
                    time.sleep(0.5)
                    
                    amount_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_amount']")
                    
                    # RCP_TC01
                    populated_val = float(driver.execute_script("return arguments[0].value;", amount_input).replace(',', '') or 0)
                    if abs(populated_val - outstanding) < 0.01:
                        logger.info(f"      ✅ [RCP_TC01] Receipt amount auto-populated: {populated_val}")
                    else:
                        logger.warning(f"      ⚠️ Auto-population mismatch! Expected {outstanding}, got {populated_val}")
                    
                    # RCP_TC02 - use JavaScript for reliability
                    driver.execute_script("arguments[0].value = '';", amount_input)
                    partial_amt = round(outstanding / 2, 2)
                    driver.execute_script(f"arguments[0].value = '{partial_amt}';", amount_input)
                    trigger_angular_change(driver, amount_input)
                    time.sleep(0.5)
                    if not has_validation_error(driver):
                        logger.info(f"      ✅ [RCP_TC02] Partial receipt amount accepted: {partial_amt}")
                    else:
                        logger.warning("      ⚠️ Validation error on partial amount!")
                    
                    # RCP_TC03
                    driver.execute_script("arguments[0].value = '';", amount_input)
                    over_amt = round(outstanding + 1000.0, 2)
                    driver.execute_script(f"arguments[0].value = '{over_amt}';", amount_input)
                    trigger_angular_change(driver, amount_input)
                    time.sleep(1)
                    try:
                        alert = WebDriverWait(driver, 2).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-container"))
                        )
                        logger.info("      ✅ [RCP_TC03] Over-receipt alert triggered.")
                        confirm_btn = alert.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                        driver.execute_script("arguments[0].click();", confirm_btn)
                        time.sleep(0.5)
                    except TimeoutException:
                        logger.warning("      ⚠️ No over-receipt alert shown!")
                    
                    # Reset to full amount
                    driver.execute_script(f"arguments[0].value = '{outstanding}';", amount_input)
                    trigger_angular_change(driver, amount_input)
                    logger.info(f"      ✅ Receipt amount reset to {outstanding}")
        except Exception as e:
            logger.warning(f"      ⚠️ Inline validation block failed: {e}")

    # Submit
    logger.info("📤 Submitting Receipt...")
    submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.footer button.submit")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    driver.execute_script("arguments[0].click();", submit_btn)
    logger.info("   ✅ Submit button clicked")

    # Wait for redirect
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
        logger.info("🚀 Receipt Registration Completed Successfully!")
    except TimeoutException:
        errors = driver.find_elements(By.CSS_SELECTOR, "mat-error")
        error_msgs = [e.text for e in errors if e.text.strip()]
        if error_msgs:
            logger.error(f"❌ Validation errors: {error_msgs}")
            driver.save_screenshot("receipt_validation_errors.png")
            raise Exception(f"Form validation failed: {error_msgs}")
        else:
            logger.warning("⚠️ No redirect and no errors. Retrying submit...")
            driver.execute_script("arguments[0].click();", submit_btn)
            time.sleep(2)
            if driver.find_elements(By.CSS_SELECTOR, "table.mat-mdc-table"):
                logger.info("🚀 Receipt Registration Completed Successfully!")
            else:
                driver.save_screenshot("receipt_submit_failed.png")
                raise Exception("Submission failed: page did not redirect and no validation errors.")


# ==========================================
# SUITE EXECUTOR
# ==========================================

def execute_receipt_suite(driver, wait, data):
    logger.info("\n--- ⚡ STARTING RECEIPT SUITE ---")
    fill_receipt_registration(driver, wait, data, run_validations=True)
    logger.info("--- ✅ RECEIPT SUITE COMPLETED ---\n")