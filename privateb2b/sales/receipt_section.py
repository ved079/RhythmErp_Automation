from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import time
import logging
from common.helper import select_dropdown, fill_input

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

def fill_receipt_registration(driver, wait, data):
    logger.info("⚡ Starting Receipt Registration...")

    # Transaction Date (if provided)
    if 'transaction_date' in data and data['transaction_date']:
        try:
            date_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[formcontrolname='transaction_date']")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", date_input)
            date_input.send_keys(Keys.CONTROL, 'a')
            date_input.send_keys(Keys.BACKSPACE)
            date_input.send_keys(data['transaction_date'])
            
            # 1. Hit ENTER to confirm the date in the calendar UI
            date_input.send_keys(Keys.ENTER)
            time.sleep(0.5)
            
            # 2. Hit TAB to move focus
            date_input.send_keys(Keys.TAB)
            
            # 3. THE FIX: Force Angular to close the overlay by hitting ESCAPE on the body
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            
            logger.info(f"✅ Filled Transaction Date: {data['transaction_date']}")
            
            # 4. Wait for the invisible calendar backdrop to definitely be gone
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-backdrop, .mat-datepicker-content")))
            time.sleep(1)
            
        except Exception as e:
            logger.warning(f"⚠️ Could not set Transaction Date: {e}")

            
    # Receipt Type
    select_dropdown(driver, wait, value=data['receipt_type'], control_name="payment_type_ref_id", searchable=False)
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
    time.sleep(1)

    # Department, Division, Location, Type of Sale
    select_dropdown(driver, wait, value=data['department'], label_text="Department", searchable=False)
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
    time.sleep(1)
    
    select_dropdown(driver, wait, value=data['division'], label_text="Division", searchable=False)
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
    time.sleep(1)
    
    select_dropdown(driver, wait, value=data['location'], label_text="Location", searchable=False)
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
    time.sleep(1)
    
    select_dropdown(driver, wait, value=data['type_of_sale'], label_text="Type of Sale", searchable=False)
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
    time.sleep(1)

    # Customer Name
    select_dropdown(driver, wait, value=data['customer_name'], control_name="customer_ref_id", searchable=True)
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
    time.sleep(1)

    # Payment Method
    select_dropdown(driver, wait, value=data['payment_method'], control_name="payment_method_ref_id", searchable=False)
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
    time.sleep(1)


    # Company Account Number (optional)
    try:
        if 'company_account_number' in data and data['company_account_number']:
            if data['company_account_number'] == "First Option":
                # Pick the first option
                acc_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select[formcontrolname='tenant_account_ref_id']")))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", acc_dropdown)
                driver.execute_script("arguments[0].click();", acc_dropdown)
                
                overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")))
                wait.until(EC.visibility_of(overlay))
                
                # THE FIX: Bulletproof Array Indexing
                options = wait.until(lambda d: overlay.find_elements(By.TAG_NAME, "mat-option"))
                if options:
                    first_option = options[0]
                    driver.execute_script("arguments[0].click();", first_option)
                
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                logger.info("   Selected first Company Account Number")
            else:
                # Use provided value
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
                
                # THE FIX: Bulletproof Array Indexing
                options = wait.until(lambda d: overlay.find_elements(By.TAG_NAME, "mat-option"))
                if options:
                    first_option = options[0]
                    driver.execute_script("arguments[0].click();", first_option)
                
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                logger.info("   Selected first Customer Bank Name")
            else:
                select_dropdown(driver, wait, value=data['customer_bank_name'], control_name="bank_detail_ref_id", searchable=False)
        else:
            logger.info("   ℹ️ Customer Bank Name not provided, skipping")
    except Exception as e:
        logger.warning(f"   ⚠️ Could not set Customer Bank Name: {e}")

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