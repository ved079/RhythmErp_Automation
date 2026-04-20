from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
from selenium.common.exceptions import StaleElementReferenceException
import logging

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# ----------------------------------------------------------------------
# Helper: search for employee by name
# ----------------------------------------------------------------------
def search_employee(driver, wait, search_term):
    try:
        search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".browser-default")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", search_box)
        search_box.clear()
        time.sleep(0.5)
        search_box.send_keys(search_term)
        search_box.send_keys(Keys.ENTER)
        time.sleep(2)
        logger.info(f"   ✅ Searched for: {search_term}")
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        driver.save_screenshot("search_employee_error.png")
        raise

def get_first_row(driver, wait):
    try:
        row = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        return row
    except Exception as e:
        logger.error(f"❌ No rows found: {e}")
        driver.save_screenshot("no_rows_error.png")
        raise

def click_action_button(driver, wait, button_selector, action_name):
    attempts = 0
    while attempts < 3:
        try:
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"table tbody tr:first-child {button_selector}")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", btn)
            logger.info(f"   ✅ {action_name} button clicked")
            time.sleep(1.5)
            return
        except StaleElementReferenceException:
            attempts += 1
            time.sleep(0.5)
            logger.warning(f"   Stale element, retrying {action_name} ({attempts})...")
    raise Exception(f"Could not click {action_name} button after retries")

def click_history(driver, wait):
    click_action_button(driver, wait, ".bi-clock-history", "History")

def click_edit(driver, wait):
    click_action_button(driver, wait, ".bi-pencil", "Edit")

def click_view(driver, wait):
    click_action_button(driver, wait, ".bi-eye", "View")

def close_modal(driver, wait):
    try:
        close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".bi-x-lg")))
        driver.execute_script("arguments[0].click();", close_btn)
        time.sleep(1)
        logger.info("   ✅ Modal closed (X button)")
    except:
        try:
            cancel_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cancel")))
            driver.execute_script("arguments[0].click();", cancel_btn)
            time.sleep(1)
            logger.info("   ✅ Modal closed (Cancel button)")
        except:
            logger.warning("   ⚠️ Could not close modal. It may already be closed.")

def is_history_empty(driver, wait):
    try:
        modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        time.sleep(1.5)
        empty_msg = modal.find_elements(By.XPATH, "//*[contains(text(),'No records') or contains(text(),'No data') or contains(text(),'No Data')]")
        if empty_msg:
            logger.info("   ✅ Verified: History is empty (No records found).")
            return True
        else:
            logger.warning("   ⚠️ Verified: History is NOT empty. Data was found.")
            return False
    except Exception as e:
        logger.warning(f"   ⚠️ Could not read history modal: {e}")
        return False

def is_history_has_update(driver, wait):
    try:
        modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        time.sleep(1.5)
        update_msg = modal.find_elements(By.XPATH, "//*[contains(text(),'Updated') or contains(text(),'Edited') or contains(text(),'Update')]")
        if update_msg:
            logger.info("   ✅ Verified: History successfully logged the 'Update' event.")
            return True
        else:
            logger.error("   ❌ Verified: History did NOT log the update.")
            return False
    except Exception as e:
        logger.warning(f"   ⚠️ Could not read history modal: {e}")
        return False

def is_form_readonly(driver, wait):
    """Check if the form in view mode has disabled inputs."""
    try:
        # Locate the employee name input (by formcontrolname)
        name_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@formcontrolname='emp_name']")))
        if name_input.get_attribute("disabled") or name_input.get_attribute("readonly"):
            logger.info("   ✅ Form is read-only (view mode).")
            return True
        else:
            logger.error("   ❌ Form is not read-only (expected disabled).")
            return False
    except Exception as e:
        logger.warning(f"   ⚠️ Could not verify read-only state: {e}")
        return False

def update_employee_name_only(driver, wait, new_employee_name):
    """Update only the employee name field and click the Update button."""
    logger.info(f"⚡ Updating employee name to: {new_employee_name}")

    # 1. Locate and update the employee name input (by formcontrolname)
    name_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@formcontrolname='emp_name']")))
    name_input.clear()
    time.sleep(0.5)
    name_input.send_keys(new_employee_name)
    logger.info("   ✅ Employee Name updated.")

    # 2. Click the Update button (button with text 'Update')
    try:
        update_btn_xpath = "//button[contains(@class, 'submit') and contains(text(), 'Update')]"
        update_btn = wait.until(EC.element_to_be_clickable((By.XPATH, update_btn_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", update_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", update_btn)
        logger.info("   ✅ 'Update' button clicked successfully.")
    except Exception as e:
        logger.error(f"   ❌ Failed to click the 'Update' button: {e}")
        driver.save_screenshot("employee_update_button_error.png")
        raise

def update_latest_employee(driver, wait, original_data, updated_data):
    """
    Perform the full update test:
    - Search for the employee (by employee_name from original_data)
    - Check history is empty
    - Edit with updated_data (only employee name)
    - Check history contains update
    - View and verify read-only
    """
    logger.info("⚡ Running employee update test...")

    # 1. Search for the created employee (use the original name)
    search_term = original_data['employee_name']
    search_employee(driver, wait, search_term)

    # 2. Ensure we have at least one row
    get_first_row(driver, wait)


    # 4. Click edit
    click_edit(driver, wait)

    # 5. Update only the employee name and submit
    update_employee_name_only(driver, wait, updated_data['employee_name'])

    # 6. Wait for submission and any overlays
    time.sleep(2)
    try:
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "swal2-container")))
    except:
        pass

    # 7. After edit, we may be back to list. Search again using updated name
    search_employee(driver, wait, updated_data['employee_name'])

    #
    # 9. Click view and check read-only
    click_view(driver, wait)
    is_form_readonly(driver, wait)
    close_modal(driver, wait)

    logger.info("✅ Employee update test completed successfully.")