"""
pages/access_screen/role_creation.py
-------------------------------------
Role Creation screen — create + verify.

Usage:
    from pages.access_screen.role_creation import create_role
    create_role(driver, wait, "Admin Role", "BRANCH")
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import logging

from common.table_helpers import verify_in_table

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'
    ))
    logger.addHandler(console)


# ================================================================
# PRIVATE HELPERS
# ================================================================

def _fill_dropdown(driver, wait, formcontrol_name, option_text):
    """Click a mat-select dropdown and pick an option by visible text."""
    logger.info(f"  Selecting '{option_text}' from dropdown (formcontrol: {formcontrol_name})")

    # 1. Click the trigger div (not mat-select itself — Angular needs native click)
    trigger = wait.until(EC.element_to_be_clickable(
        (By.XPATH,
         f"//mat-select[@formcontrolname='{formcontrol_name}']"
         f"//div[contains(@class,'select-trigger')]")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", trigger)
    time.sleep(0.3)
    trigger.click()  # native click — JS click doesn't fire Angular event
    time.sleep(0.5)

    # 2. Wait for option panel — use role='listbox' (more reliable than .mat-select-panel)
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//div[@role='listbox']//mat-option")
    ))

    # 3. Click the matching option
    option = wait.until(EC.element_to_be_clickable(
        (By.XPATH,
         f"//div[@role='listbox']//mat-option"
         f"//span[normalize-space()='{option_text}']")
    ))
    driver.execute_script("arguments[0].click();", option)
    time.sleep(0.3)
    logger.info(f"  Selected '{option_text}'.")
    


def _check_result(driver, wait):
    """Check submit response — SweetAlert success, toast, or error."""
    time.sleep(2)

    # Check for error first
    try:
        error = driver.find_element(
            By.CSS_SELECTOR, ".alert-danger, .toast-error, .snack-bar-error"
        )
        if error.is_displayed():
            raise Exception(f"Submit failed: {error.text.strip()}")
    except NoSuchElementException:
        pass

    # SweetAlert success
    try:
        driver.find_element(By.CSS_SELECTOR, ".swal2-success")
        logger.info("  Submit succeeded (SweetAlert confirmed).")
        try:
            ok_btn = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
            driver.execute_script("arguments[0].click();", ok_btn)
            time.sleep(0.5)
        except Exception:
            pass
        return
    except NoSuchElementException:
        pass

    # Inline toast fallback
    try:
        toast = driver.find_element(By.CSS_SELECTOR, ".toast-success, .snack-bar-success")
        if toast.is_displayed():
            logger.info(f"  Success toast: {toast.text.strip()}")
    except NoSuchElementException:
        pass


# ================================================================
# MAIN FUNCTION
# ================================================================

def create_role(driver, wait, role_name, entity_group):
    """
    Create a role on the Role Creation Screen and verify in table.

    Args:
        driver:       Selenium WebDriver (already logged in, on page)
        wait:         WebDriverWait instance
        role_name:    Role name (str)
        entity_group: Entity type from dropdown (str) — BRANCH, DCB, or PACS

    Raises:
        Exception: if submit fails or role not found in table.
    """
    logger.info(f"Creating Role: '{role_name}' | Entity: '{entity_group}'")

    # 1. Click Add button
    logger.info("  Clicking Add...")
    add_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@class,'erp-add-btn')]")
    ))
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(1)

    # 2. Fill Role Name (text input — uses formcontrolname, not mat-label)
    logger.info(f"  Filling Role Name = '{role_name}'")
    role_input = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@formcontrolname='role_name']")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", role_input)
    time.sleep(0.3)
    role_input.click()
    role_input.clear()
    role_input.send_keys(role_name)

    # 3. Select Entity Type (mat-select dropdown)
    _fill_dropdown(driver, wait, "entity_type", entity_group)

    # 4. Submit
    logger.info("  Submitting...")
    submit = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@type='submit']//span[normalize-space()='Submit']")
    ))
    driver.execute_script("arguments[0].click();", submit)

    # 5. Check server response
    _check_result(driver, wait)

    # 6. Search + verify in table
    verify_in_table(driver, wait, role_name, "name")

    logger.info(f"Done: Role '{role_name}' created and verified.")