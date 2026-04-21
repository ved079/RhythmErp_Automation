import pytest
import time
import logging
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

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
DROPDOWN_LOAD = 1.5
ACCORDION_ANIM = 1
OVERLAY_WAIT = 5

# ─────────────────────────────────────────────
#  SCREENSHOT DIRECTORY
# ─────────────────────────────────────────────
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "farmer")
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
    """Navigate to farmer page. Used by runner.py AND the pytest fixture below."""
    driver.get(config.URL)
    auth_section.perform_login(driver, wait, config)
    nav_section.go_to_farmer_page(driver, wait)
    time.sleep(ANGULAR_SETTLE)


def do_reset_between_tests(driver, wait):
    """Reset form between tests. Used by runner.py AND the pytest fixture below."""
    reset_form(driver, wait)


# ═══════════════════════════════════════════════
#  TEST CLASS
# ═══════════════════════════════════════════════
class TestFarmerEdgeCases:

    @pytest.fixture(scope="class", autouse=True)
    def setup_and_navigate(self, driver, wait):
        do_setup_and_navigate(driver, wait)
        yield

    @pytest.fixture(autouse=True)
    def reset_between_tests(self, driver, wait):
        yield
        do_reset_between_tests(driver, wait)

    # ═══════════════════════════════════════════
    #  GROUP 1: Pure Validation (no side effects)
    #  These DO NOT submit the form — just check errors
    # ═══════════════════════════════════════════

    def test_empty_form_required_field_errors(self, driver, wait):
        """Clicking Submit on an empty form should show validation errors for all mandatory fields."""

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] Empty form errors found: {error_texts}")

        assert "name" in error_block, \
            f"Missing validation for Farmer Name! Errors found: [{error_block}]"
        assert "phone" in error_block or "mobile" in error_block, \
            f"Missing validation for Phone! Errors found: [{error_block}]"

    def test_phone_9_digits_rejected(self, driver, wait):
        """Phone with 9 digits should be rejected."""
        phone_input = wait.until(EC.visibility_of_element_located((By.ID, "phone")))
        phone_input.clear()
        phone_input.send_keys("987654321")

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] 9-digit phone errors: {error_texts}")

        assert "phone" in error_block or "mobile" in error_block or "valid" in error_block or "digit" in error_block, \
            f"BUG: 9-digit phone accepted! Errors found: [{error_block}]"

    def test_phone_10_digits_accepted(self, driver, wait):
        """Phone with exactly 10 digits should NOT show a phone-length validation error."""
        phone_input = wait.until(EC.visibility_of_element_located((By.ID, "phone")))
        phone_input.clear()
        phone_input.send_keys("9876543210")

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] 10-digit phone errors: {error_texts}")

        phone_length_errors = [e for e in error_texts if "phone" in e or "mobile" in e or "10" in e or "digit" in e]
        assert len(phone_length_errors) == 0, \
            f"BUG: 10-digit phone was rejected! Phone errors found: {phone_length_errors}"

    def test_phone_11_digits_rejected(self, driver, wait):
        """Phone with 11 digits should be rejected."""
        phone_input = wait.until(EC.visibility_of_element_located((By.ID, "phone")))
        phone_input.clear()
        phone_input.send_keys("98765432101")

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] 11-digit phone errors: {error_texts}")

        assert "phone" in error_block or "mobile" in error_block or "valid" in error_block or "digit" in error_block, \
            f"BUG: 11-digit phone accepted! Errors found: [{error_block}]"

    def test_invalid_email_format_rejected(self, driver, wait):
        """Email missing @ and domain should be rejected."""
        email_input = wait.until(EC.visibility_of_element_located((By.ID, "email")))
        email_input.clear()
        email_input.send_keys("nilesh.tidake_at_godafarm")

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] Invalid email errors: {error_texts}")

        assert "email" in error_block or "valid" in error_block, \
            f"BUG: Invalid email format accepted! Errors found: [{error_block}]"

    def test_pincode_rejects_letters(self, driver, wait):
        """Pincode field should reject alphabetical characters."""
        addr_toggle = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//strong[contains(text(), 'Address')]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", addr_toggle)
        driver.execute_script("arguments[0].click();", addr_toggle)
        time.sleep(ACCORDION_ANIM)

        pincode_input = wait.until(EC.visibility_of_element_located((By.ID, "pincode")))
        pincode_input.clear()
        pincode_input.send_keys("ABCDEF")

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] Pincode errors: {error_texts}")

        assert "pincode" in error_block or "number" in error_block or "invalid" in error_block or "numeric" in error_block, \
            f"BUG: Letters accepted in Pincode! Errors found: [{error_block}]"

    def test_name_rejects_numbers(self, driver, wait):
        """Farmer Name field should reject numbers and special characters."""
        name_input = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[formcontrolname='name'], input#name")
        ))
        name_input.clear()
        name_input.send_keys("John123!@#")

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] Invalid name errors: {error_texts}")

        assert "name" in error_block or "character" in error_block or "invalid" in error_block or "alphabet" in error_block, \
            f"BUG: Numbers/symbols accepted in Name! Errors found: [{error_block}]"

    def test_phone_rejects_letters(self, driver, wait):
        """Phone field should reject non-numeric characters like letters."""
        phone_input = wait.until(EC.visibility_of_element_located((By.ID, "phone")))
        phone_input.clear()
        phone_input.send_keys("abcdefghij")

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(ANGULAR_SETTLE)

        error_texts = grab_error_texts(driver, wait)
        error_block = " ".join(error_texts)

        logger.info(f"[DEBUG] Phone letters errors: {error_texts}")

        assert "phone" in error_block or "mobile" in error_block or "number" in error_block or "digit" in error_block or "numeric" in error_block, \
            f"BUG: Letters accepted in Phone! Errors found: [{error_block}]"

    def test_reset_button_clears_form(self, driver, wait):
        """Clicking the Reset button should clear all filled fields back to empty."""

        # Fill a couple of fields
        name_input = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[formcontrolname='name'], input#name")
        ))
        name_input.clear()
        name_input.send_keys("Temporary Test Name")

        phone_input = wait.until(EC.visibility_of_element_located((By.ID, "phone")))
        phone_input.clear()
        phone_input.send_keys("9876543210")

        email_input = wait.until(EC.visibility_of_element_located((By.ID, "email")))
        email_input.clear()
        email_input.send_keys("temp@test.com")

        logger.info("[DEBUG] Filled 3 fields. Clicking Reset...")

        # Click Reset
        reset_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.send")))
        driver.execute_script("arguments[0].click();", reset_btn)
        time.sleep(ANGULAR_SETTLE)

        # Verify fields are cleared
        name_val = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[formcontrolname='name'], input#name")
        )).get_attribute("value")
        phone_val = driver.find_element(By.ID, "phone").get_attribute("value")
        email_val = driver.find_element(By.ID, "email").get_attribute("value")

        logger.info(f"[DEBUG] After reset — name='{name_val}', phone='{phone_val}', email='{email_val}'")

        assert name_val == "", f"BUG: Reset did not clear Name! Value: '{name_val}'"
        assert phone_val == "", f"BUG: Reset did not clear Phone! Value: '{phone_val}'"
        assert email_val == "", f"BUG: Reset did not clear Email! Value: '{email_val}'"
