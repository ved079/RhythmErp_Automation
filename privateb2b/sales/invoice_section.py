from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import time
import os
import logging
from common.helper import select_dropdown, click_submit

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

def fill_invoice_registration(driver, wait, data):
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
        time.sleep(0.5)
    except Exception as e:
        logger.error(f"❌ Failed to select Dispatch Note: {e}")
        driver.save_screenshot("invoice_dn_error.png")
        raise

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
    except TimeoutException:
        # If still on the form, check for validation errors
        errors = driver.find_elements(By.CSS_SELECTOR, "mat-error")
        error_msgs = [e.text for e in errors if e.text.strip()]
        if error_msgs:
            logger.error(f"❌ Validation errors: {error_msgs}")
            driver.save_screenshot("invoice_validation_errors.png")
            raise Exception(f"Form validation failed: {error_msgs}")
        else:
            # No errors but didn't redirect – maybe the click didn't work? Try again.
            logger.warning("⚠️ No redirect and no errors. Retrying submit...")
            driver.execute_script("arguments[0].click();", submit_btn)
            time.sleep(2)
            if driver.find_elements(By.CSS_SELECTOR, "table.mat-mdc-table"):
                logger.info("🚀 Invoice Registration Completed Successfully!")
            else:
                driver.save_screenshot("invoice_submit_failed.png")
                raise Exception("Submission failed: page did not redirect and no validation errors.")