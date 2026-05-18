"""
pages/access_screen/entity_group.py
------------------------------------
Entity Group Definition screen — create + verify.

Usage:
    from pages.access_screen.entity_group import create_entity_group
    create_entity_group(driver, wait, "Admin Role", "2")
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import logging

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

def _fill_field(driver, wait, label_text, value):
    """Fill any mat-form-field input by its visible label text."""
    logger.info(f"  Filling '{label_text}' = '{value}'")

    input_el = wait.until(EC.element_to_be_clickable(
        (By.XPATH,
         f"//mat-label[normalize-space()='{label_text}']"
         f"/ancestor::mat-form-field//input")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_el)
    time.sleep(0.3)

    try:
        input_el.click()
        input_el.clear()
        input_el.send_keys(value)
    except Exception:
        logger.warning(f"  send_keys failed for '{label_text}', using JS fallback.")
        driver.execute_script("arguments[0].value = arguments[1];", input_el, value)


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


def _verify_in_table(driver, wait, group_name):
    """
    Search for group_name using the search button → input flow,
    then confirm the name appears in the entity_group column.

    Raises:
        Exception: if "No results found" is shown or name is absent.
    """
    logger.info(f"  Verifying '{group_name}' in table...")

    # 1. Click the search button to reveal the input
    search_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button.search-btn, button[aria-label='Search']")
    ))
    driver.execute_script("arguments[0].click();", search_btn)
    time.sleep(0.5)

    # 2. Type name into the revealed input
    search_input = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR,
         "input.search-input, "                      # common custom class
         ".erp-search-container input, "             # matches the div in your HTML
         "input[placeholder*='Search'], "
         "input[type='search']")
    ))
    search_input.clear()
    search_input.send_keys(group_name)
    time.sleep(1.5)   # let Angular filter the table

    # 3. Check for "No results" row first
    try:
        no_data = driver.find_element(
            By.XPATH,
            "//*[contains(@class,'mat-mdc-no-data-row') or "
            "contains(text(),'No results found') or "
            "contains(text(),'No data found')]"
        )
        if no_data.is_displayed():
            raise Exception(
                f"Verification FAILED: '{group_name}' not found in table "
                f"(table shows: '{no_data.text.strip()}')"
            )
    except NoSuchElementException:
        pass  # no "empty" row visible — good, continue

    # 4. Confirm name appears in the entity_group column
    try:
        wait.until(EC.presence_of_element_located(
            (By.XPATH,
             f"//td[contains(@class,'mat-column-entity_group')]"
             f"//span[normalize-space()='{group_name}']")
        ))
        logger.info(f"  Verification PASSED: '{group_name}' found in table.")
    except TimeoutException:
        raise Exception(
            f"Verification FAILED: '{group_name}' not found in entity_group column."
        )

    # 5. Clear search to restore full table view
    try:
        search_input.clear()
        time.sleep(0.5)
    except Exception:
        pass


# ================================================================
# MAIN FUNCTION
# ================================================================

def create_entity_group(driver, wait, group_name, level):
    """
    Navigate to Entity Group Definition form, fill, submit, and verify.

    Args:
        driver:     Selenium WebDriver (already logged in, already on page)
        wait:       WebDriverWait instance
        group_name: Entity Group Name (str)
        level:      Level value (str or int)

    Raises:
        Exception: if submit fails OR if name not found in table after creation.
    """
    logger.info(f"Creating Entity Group: '{group_name}' | Level: '{level}'")

    # 1. Click Add button
    logger.info("  Clicking Add...")
    add_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@class,'erp-add-btn')]")   # precise from your HTML
    ))
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(1)

    # 2. Fill form
    _fill_field(driver, wait, "Entity Group Name", group_name)
    _fill_field(driver, wait, "Level", str(level))

    # 3. Submit
    logger.info("  Submitting...")
    submit = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@type='submit']//span[normalize-space()='Submit']")
    ))
    driver.execute_script("arguments[0].click();", submit)

    # 4. Check server response
    _check_result(driver, wait)

    # 5. Search + verify in table
    _verify_in_table(driver, wait, group_name)

    logger.info(f"Done: Entity Group '{group_name}' created and verified.")