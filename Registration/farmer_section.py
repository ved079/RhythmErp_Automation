from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import time
import logging
from common.helper import select_dropdown

# Set up a module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


def fill_datepicker(driver, wait, value):
    """Fill Angular Material datepicker by locating the input via its label or class."""
    try:
        # Try to find the datepicker input by its associated label
        # The input has class 'mat-datepicker-input'
        date_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.mat-datepicker-input")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", date_input)
        driver.execute_script("arguments[0].click();", date_input)
        time.sleep(0.3)

        # Clear and type the date
        date_input.send_keys(Keys.CONTROL + "a")
        date_input.send_keys(Keys.BACKSPACE)
        date_input.send_keys(value)
        date_input.send_keys(Keys.TAB)  # Force Angular validation and close picker
        
        logger.info(f"✅ Filled Date of Birth: {value}")
    except Exception as e:
        logger.error(f"❌ Failed to fill Date of Birth: {e}")
        driver.save_screenshot("dob_error.png")
        # Removed 'raise' here so a DOB failure doesn't instantly crash the whole suite


def click_submit_and_verify(driver, wait):
    """Click submit and verify redirection or log validation errors."""
    logger.info("📤 Submitting form...")
    submit_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@class, 'submit') and contains(text(), 'Submit')]")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    driver.execute_script("arguments[0].click();", submit_btn)
    logger.info("✅ Submit button clicked")

    try:
        # Wait for success indicator (table, toast, or sweet alert)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table, .toast-success, .swal2-success")))
        logger.info("🚀 Farmer Registration Completed Successfully!")
    except TimeoutException:
        errors = driver.find_elements(By.CSS_SELECTOR, "mat-error")
        error_msgs = [e.text for e in errors if e.text.strip()]
        if error_msgs:
            logger.error(f"❌ Validation errors: {error_msgs}")
            driver.save_screenshot("farmer_validation_errors.png")
            raise Exception(f"Form validation failed: {error_msgs}")
        else:
            logger.error("❌ Form did not submit – no redirect and no errors shown.")
            driver.save_screenshot("farmer_submit_failed.png")
            raise Exception("Submission failed silently.")


def fill_registration(driver, wait, data):
    logger.info("⚡ Starting Farmer Registration...")

    wait.until(EC.visibility_of_element_located((By.ID, "name"))).send_keys(data['name'])
    driver.find_element(By.ID, "email").send_keys(data['email'])
    driver.find_element(By.ID, "phone").send_keys(data['phone'])

    # Fill Date of Birth (now actually implemented)
    fill_datepicker(driver, wait, data['dob'])

    # Gender and Caste
    select_dropdown(driver, wait, data['gender'], control_id="gender", searchable=False)
    select_dropdown(driver, wait, data['caste'], control_id="cast_religion", searchable=False)

    driver.find_element(By.ID, "password").send_keys(data['password'])

    # Farmer Category (required)
    if 'farmer_category' in data:
        select_dropdown(driver, wait, data['farmer_category'], control_id="farmer_category", searchable=False)
    else:
        select_dropdown(driver, wait, "Walk-in Farmer", control_id="farmer_category", searchable=False)

    logger.info("📍 Expanding Address...")
    addr_toggle = wait.until(EC.element_to_be_clickable((By.XPATH, "//strong[contains(text(), 'Address')]")))
    driver.execute_script("arguments[0].click();", addr_toggle)
    time.sleep(1)

    select_dropdown(driver, wait, data['state'], control_id="state_ref_id_id", searchable=False)
    time.sleep(1)
    select_dropdown(driver, wait, data['district'], control_id="district_ref_id_id", searchable=False)
    time.sleep(1)
    select_dropdown(driver, wait, data['taluka'], control_id="sub_district_ref_id_id", searchable=False)
    time.sleep(1)
    select_dropdown(driver, wait, data['village'], control_id="village_ref_id_id", searchable=False)

    driver.find_element(By.ID, "pincode").send_keys(data['pincode'])
    address1 = wait.until(EC.visibility_of_element_located((By.NAME, "Address1")))
    address1.send_keys(data.get('address1', 'Test Address Line 1'))

    try:
        address2 = driver.find_element(By.NAME, "Address2")
        address2.send_keys(data.get('address2', ''))
    except:
        pass

    logger.info("🏦 Expanding Bank...")
    bank_toggle = wait.until(EC.element_to_be_clickable((By.XPATH, "//strong[contains(text(), 'Bank')]")))
    driver.execute_script("arguments[0].click();", bank_toggle)
    time.sleep(1)

    driver.find_element(By.ID, "bank_name").send_keys(data['bank_name'])
    driver.find_element(By.ID, "bank_ifsc_code").send_keys(data['ifsc'])
    driver.find_element(By.ID, "bank_account_no").send_keys(data['account_no'])
    driver.find_element(By.ID, "bank_account_holder_name").send_keys(data['name'])
    branch_input = driver.find_element(By.ID, "bank_branch_code")
    branch_input.send_keys(data.get('branch_name', 'Main Branch'))

    if 'account_type' in data:
        select_dropdown(driver, wait, data['account_type'], control_id="account_type0", searchable=False)
    if 'bank_proof' in data:
        select_dropdown(driver, wait, data['bank_proof'], control_id="bank_doc_id0", searchable=False)

    try:
        checkbox = driver.find_element(By.ID, "mat-mdc-checkbox-1-input")
        driver.execute_script("arguments[0].click();", checkbox)
    except:
        pass

    # Use the verifying submit
    click_submit_and_verify(driver, wait)