from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import logging
from common.helper import select_dropdown, click_submit, fill_input
from selenium.common.exceptions import StaleElementReferenceException

def click_with_retry(driver, wait, xpath, retries=3, delay=1.5):
    """Find and click an element by XPath, retrying on stale element errors."""
    for attempt in range(1, retries + 1):
        try:
            # Always re-locate inside the loop — never reuse a reference across iterations
            element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            driver.execute_script("arguments[0].click();", element)
            return  # success
        except StaleElementReferenceException:
            logger.warning(f"   ⚠️ Stale element on attempt {attempt}/{retries}, retrying...")
            time.sleep(delay)
    raise RuntimeError(f"Element still stale after {retries} attempts: {xpath}")

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

def wait_for_sweetalert_to_close(driver, wait, timeout=10):
    """Wait for any SweetAlert2 overlay to disappear."""
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container")))
        logger.info("   ✅ SweetAlert overlay closed.")
    except TimeoutException:
        driver.save_screenshot("sweetalert_still_open.png")
        logger.warning("   ⚠️ SweetAlert overlay still visible; continuing anyway.")

def select_first_gate_pass_option(driver, wait):
    """For Gate Pass dropdown – select the first option (latest GP) since we don't know its exact value."""
    try:
        logger.info("➡️ Selecting Gate Pass (first option)")
        time.sleep(2)   # wait for supplier API to load gate passes
        
        dropdown = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "mat-select[formcontrolname='gate_pass_ref_id']")
        ))
        wait.until(lambda d: dropdown.get_attribute("aria-disabled") != "true")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        
        try:
            dropdown.click()
        except:
            driver.execute_script("arguments[0].click();", dropdown)

        overlay = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")
        ))
        wait.until(EC.visibility_of(overlay))
        time.sleep(1)

        first_option = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//mat-option[1]//span")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", first_option)
        driver.execute_script("arguments[0].click();", first_option)
        logger.info("   ✅ Selected first Gate Pass option")
        time.sleep(0.5)
        
    except Exception as e:
        logger.error(f"❌ Failed to select Gate Pass: {e}")
        driver.save_screenshot("gate_pass_error.png")
        raise

def fill_grn_registration(driver, wait, data):
    logger.info("⚡ Starting GRN Registration...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='supplier_ref_id']")))
    time.sleep(0.5)

    # --- 1. SET THE DATE ---
    logger.info(f"   📅 Setting GRN Transaction Date to: {data['transaction_date']}")
    fill_input(driver, wait, data['transaction_date'], control_name="transaction_date")

    # --- 2. SELECT SUPPLIER ---
    select_dropdown(driver, wait, value=data['supplier'], control_name="supplier_ref_id", searchable=True)

    # --- 3. SELECT GATE PASS (This auto-populates all the multiple items!) ---
    select_first_gate_pass_option(driver, wait)
    
    # Wait for the backend API to fetch and render all the item rows
    time.sleep(3)

    # --- 4. SUBMIT ---
    logger.info("📤 Submitting the form...")
    click_submit(driver, wait)

    time.sleep(3)
    logger.info("🚀 GRN Registration Completed Successfully!")

def approve_latest_grn(driver, wait):
    logger.info("⚡ Approving latest GRN...")

    # Step 1: Close any lingering SweetAlerts
    wait_for_sweetalert_to_close(driver, wait)
    time.sleep(1)

    # Step 2: If we're still on the form, close it to go back to the list
    try:
        cancel_btn = driver.find_element(By.XPATH, "//button[contains(@class, 'cancel') or contains(text(), 'Cancel')]")
        if cancel_btn.is_displayed():
            cancel_btn.click()
            logger.info("   ✅ Closed GRN form to return to list")
            time.sleep(2)
    except:
        pass  # Already on list page

    # Step 3: Wait for the GRN list table with actual data rows
    try:
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "table.mat-mdc-table tbody tr")
        ))
        time.sleep(1)
    except TimeoutException:
        logger.warning("   ⚠️ GRN table rows not loaded, refreshing page...")
        driver.refresh()
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "table.mat-mdc-table tbody tr")
        ))
        time.sleep(1)

    EDIT_BTN_XPATH = (
        "//tbody/tr[1]//button[contains(@class, 'tblActnBtn')]"
        "//i[contains(@class, 'bi-pencil')]/parent::button"
    )
    APPROVE_BTN_XPATH = "//button[contains(text(), 'Approve')]"

    try:
        click_with_retry(driver, wait, EDIT_BTN_XPATH)
        logger.info("   ✅ Clicked edit button for latest GRN")
        time.sleep(2)
    except Exception as e:
        logger.error(f"❌ Failed to find edit button: {e}")
        driver.save_screenshot("edit_button_not_found.png")
        raise

    wait_for_sweetalert_to_close(driver, wait)

    try:
        click_with_retry(driver, wait, APPROVE_BTN_XPATH)
        logger.info("   ✅ Clicked Approve button")
        time.sleep(2)
    except Exception as e:
        logger.error(f"❌ Failed to click Approve: {e}")
        driver.save_screenshot("approve_button_not_found.png")
        raise

    wait_for_sweetalert_to_close(driver, wait)
    logger.info("🚀 GRN approved successfully!")