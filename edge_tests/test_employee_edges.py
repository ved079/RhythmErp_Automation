import pytest
import time
import logging
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import config
from common import auth_section, nav_section

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# ─────────────────────────────────────────────
#  TIMEOUT CONSTANTS (no magic numbers)
# ─────────────────────────────────────────────
ANGULAR_SETTLE = 2

# ─────────────────────────────────────────────
#  SCREENSHOT DIRECTORY
# ─────────────────────────────────────────────
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "employee")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def take_screenshot(driver, test_name):
    """Save a screenshot on failure for debugging."""
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"{test_name}_{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    try:
        driver.save_screenshot(filepath)
        logger.error(f"  📸 Screenshot saved: {filepath}")
    except Exception as e:
        logger.error(f"  📸 Screenshot failed: {e}")
    return filepath


def grab_error_texts(driver, wait):
    """Grab all visible mat-error texts from the page."""
    errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
    return [
        driver.execute_script("return arguments[0].textContent;", err).strip().lower()
        for err in errors
        if driver.execute_script("return arguments[0].textContent;", err).strip() != ""
    ]


def reset_form(driver, wait):
    """Click the Reset button to clear the form between tests."""
    try:
        reset_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.send")))
        driver.execute_script("arguments[0].click();", reset_btn)
        time.sleep(ANGULAR_SETTLE)
    except Exception:
        pass
        try:
            driver.refresh()
            time.sleep(ANGULAR_SETTLE)
        except Exception:
            pass


# ─────────────────────────────────────────────
#  STANDALONE SETUP / RESET  (runner calls these directly)
# ─────────────────────────────────────────────
def do_setup_and_navigate(driver, wait):
    """Navigate to employee page. Used by runner.py AND the pytest fixture below."""
    driver.get(config.URL)
    auth_section.perform_login(driver, wait, config)
    nav_section.go_to_employee_page(driver, wait)
    time.sleep(ANGULAR_SETTLE)


def do_reset_between_tests(driver, wait):
    """Reset form between tests. Used by runner.py AND the pytest fixture below."""
    reset_form(driver, wait)


# ═══════════════════════════════════════════════
#  TEST CLASS
# ═══════════════════════════════════════════════
class TestEmployeeEdgeCases:

    @pytest.fixture(scope="class", autouse=True)
    def setup_and_navigate(self, driver, wait):
        do_setup_and_navigate(driver, wait)
        yield

    @pytest.fixture(autouse=True)
    def reset_between_tests(self, driver, wait):
        yield
        do_reset_between_tests(driver, wait)

    # ═══════════════════════════════════════════
    #  Pure Validation (no side effects)
    #  These DO NOT submit the form — just check errors
    # ═══════════════════════════════════════════

    def test_employee_empty_form_errors(self, driver, wait):
        """Clicking Submit on an empty Employee form should show validation errors for all mandatory fields."""

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] Empty employee form errors: {error_texts}")

        assert "name" in error_block, \
            f"Missing validation for Employee Name! Errors found: [{error_block}]"
        assert "email" in error_block, \
            f"Missing validation for Email! Errors found: [{error_block}]"
        assert "phone" in error_block or "mobile" in error_block, \
            f"Missing validation for Phone! Errors found: [{error_block}]"
        assert "maker" in error_block or "checker" in error_block, \
            f"Missing validation for Maker/Checker! Errors found: [{error_block}]"

    def test_employee_email_rejects_invalid(self, driver, wait):
        """Email missing @ and domain should be rejected."""
        email_input = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[formcontrolname='email']")
        ))
        email_input.clear()
        email_input.send_keys("nilesh_at_godafarm")

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] Invalid email errors: {error_texts}")

        assert "email" in error_block or "valid" in error_block, \
            f"BUG: Invalid email format accepted! Errors found: [{error_block}]"

    def test_employee_email_accepts_valid(self, driver, wait):
        """Email in valid format should NOT show an email-specific validation error."""
        email_input = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[formcontrolname='email']")
        ))
        email_input.clear()
        email_input.send_keys("test@employee.com")

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] Valid email errors: {error_texts}")

        email_errors = [e for e in error_texts if "email" in e]
        assert len(email_errors) == 0, \
            f"BUG: Valid email was rejected! Email errors found: {email_errors}"

    def test_employee_phone_rejects_letters(self, driver, wait):
        """Phone field (type=Number) should reject letters — browser blocks input, required error fires."""
        phone_input = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[formcontrolname='phone']")
        ))
        phone_input.clear()
        phone_input.send_keys("ABC")

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] Letters in phone errors: {error_texts}")

        # type=Number means browser strips ABC, field stays empty -> required error
        assert "phone" in error_block or "mobile" in error_block or "required" in error_block, \
            f"BUG: No error for invalid phone input! Errors found: [{error_block}]"

    def test_employee_phone_accepts_numbers(self, driver, wait):
        """Phone field should accept normal numeric input without errors."""
        phone_input = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[formcontrolname='phone']")
        ))
        phone_input.clear()
        phone_input.send_keys("9876543210")

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] Normal phone input errors: {error_texts}")

        phone_errors = [e for e in error_texts if "phone" in e or "mobile" in e]
        assert len(phone_errors) == 0, \
            f"BUG: Normal phone number was rejected! Phone errors found: {phone_errors}"

    def test_employee_reset_button_clears_form(self, driver, wait):
        """Clicking the Reset button should clear all filled fields back to empty."""

        # Fill a couple of fields using formcontrolname (no static IDs)
        email_input = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[formcontrolname='email']")
        ))
        email_input.clear()
        email_input.send_keys("test@employee.com")

        phone_input = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[formcontrolname='phone']")
        ))
        phone_input.clear()
        phone_input.send_keys("9876543210")

        logger.info("[DEBUG] Filled 2 fields. Clicking Reset...")

        # Click Reset
        reset_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.send")))
        driver.execute_script("arguments[0].click();", reset_btn)
        time.sleep(ANGULAR_SETTLE)

        # Verify fields are cleared
        email_val = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='email']").get_attribute("value")
        phone_val = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='phone']").get_attribute("value")

        logger.info(f"[DEBUG] After reset — email='{email_val}', phone='{phone_val}'")

        assert email_val == "", f"BUG: Reset did not clear Email! Value: '{email_val}'"
        assert phone_val == "", f"BUG: Reset did not clear Phone! Value: '{phone_val}'"
