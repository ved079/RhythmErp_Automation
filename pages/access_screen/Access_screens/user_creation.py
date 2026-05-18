"""
pages/access_screen/user_creation.py
-------------------------------------
User Creation screen — create + verify.

Usage:
    from pages.access_screen.user_creation import create_user
    create_user(driver, wait, **user_creation_data)
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
def _fill_input(driver, wait, field_name, text):
    
    """Fill an input field by its formcontrolname."""
    logger.info(f"  Filling '{field_name}' = '{text}'")
    input_el = wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//input[@formcontrolname='{field_name}']")
    ))
    try:
        input_el.clear()
        input_el.send_keys(text)
    except Exception:
        logger.warning(f"  send_keys failed for '{field_name}', using JS fallback.")
        driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
            input_el, text
        )



def _fill_multi_dropdown(driver, wait, label_text, options_list):
    """Click a multi-select mat-select and pick multiple options by label.

    Flow:
        1. Find mat-select by mat-label text
        2. Click trigger (native click)
        3. Loop: click each option from cdk-overlay-pane
        4. Click body to close the panel
    """
    logger.info(f"  Multi-select '{label_text}': {options_list}")

    # 1. Find and click the select trigger
    select = wait.until(EC.element_to_be_clickable(
        (By.XPATH,
         f"//mat-label[normalize-space()='{label_text}']"
         f"/ancestor::mat-form-field//mat-select"
         f"//div[contains(@class,'select-trigger')]")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select)
    time.sleep(0.3)
    select.click()
    time.sleep(0.5)

    # 2. Wait for options panel
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//div[contains(@class,'cdk-overlay-pane')]//mat-option")
    ))

    # 3. Click each option
    for opt_text in options_list:
        option = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             f"//div[contains(@class,'cdk-overlay-pane')]"
             f"//mat-option//span[normalize-space()='{opt_text}']")
        ))
        driver.execute_script("arguments[0].click();", option)
        time.sleep(0.3)
        logger.info(f"    Selected '{opt_text}'")

    # 4. Click body to close the panel
    driver.find_element(By.TAG_NAME, "body").click()
    time.sleep(0.3)


def _fill_search_dropdown(driver, wait, label_text, search_text):
    """Click a mat-select, type in its search box, then click filtered option.

    Flow:
        1. Find mat-select by mat-label text
        2. Click trigger (native click)
        3. Wait for search input inside cdk-overlay-pane
        4. Type search_text to filter
        5. Click the matching option
    """
    logger.info(f"  Search-select '{label_text}': '{search_text}'")

    # 1. Find and click the select trigger
    select = wait.until(EC.element_to_be_clickable(
        (By.XPATH,
         f"//mat-label[normalize-space()='{label_text}']"
         f"/ancestor::mat-form-field//mat-select"
         f"//div[contains(@class,'select-trigger')]")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select)
    time.sleep(0.3)
    select.click()
    time.sleep(0.5)

    # 2. Wait for search input inside the panel
    search_input = wait.until(EC.element_to_be_clickable(
        (By.XPATH,
         "//div[contains(@class,'cdk-overlay-pane')]"
         "//input[contains(@placeholder,'Search')]")
    ))
    search_input.clear()
    search_input.send_keys(search_text)
    time.sleep(1)

    # 3. Click the filtered option
    option = wait.until(EC.element_to_be_clickable(
        (By.XPATH,
         f"//div[contains(@class,'cdk-overlay-pane')]"
         f"//mat-option//span[normalize-space()='{search_text}']")
    ))
    driver.execute_script("arguments[0].click();", option)
    time.sleep(0.3)
    logger.info(f"    Selected '{search_text}'")


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

def create_user(driver, wait, username, email, first_name, last_name,
                password, user_types, role, entity):
    """
    Create a user on the User Creation Screen and verify in table.

    Args:
        driver:     Selenium WebDriver (already logged in, on page)
        wait:       WebDriverWait instance
        username:   Username (str)
        email:      Email (str)
        first_name: First name (str)
        last_name:  Last name (str)
        password:   Password (str)
        user_types: List of user types to select (list[str])
        role:       Role to select from dropdown (str)
        entity:     Entity to select from dropdown (str)

    Raises:
        Exception: if submit fails or user not found in table.
    """
    logger.info(f"Creating User: '{username}' | Email: '{email}'")

    # 1. Click Add button
    logger.info("  Clicking Add...")
    add_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@class,'erp-add-btn')]")
    ))
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(1)

    # 2. Fill text inputs
    _fill_input(driver, wait, "username", username)
    _fill_input(driver, wait, "email", email)
    _fill_input(driver, wait, "first_name", first_name)
    _fill_input(driver, wait, "last_name", last_name)
    _fill_input(driver, wait, "password", password)

    # 3. User Type (multi-select dropdown)
    _fill_multi_dropdown(driver, wait, "User Type", user_types)

    # 4. Role (single-select with search)
    _fill_search_dropdown(driver, wait, "Role", role)

    # 5. Entity (multi-select dropdown)
    _fill_multi_dropdown(driver, wait, "Entity", [entity])

    # 6. Submit
    logger.info("  Submitting...")
    submit = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@type='submit']//span[normalize-space()='Submit']")
    ))
    driver.execute_script("arguments[0].click();", submit)

    # 7. Check server response
    _check_result(driver, wait)

    # 8. Search + verify in table
    verify_in_table(driver, wait, username,
                    check_date=True, date_column="joined",
                    date_format="%d %b %Y") 

    logger.info(f"Done: User '{username}' created and verified.")