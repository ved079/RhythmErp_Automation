import pytest
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import config
from common import auth_section, nav_section

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


class TestEmployeeEdgeCases:

    @pytest.fixture(autouse=True)
    def setup_and_navigate(self, driver, wait):
        """Automatically log in and navigate to the Employee Registration page."""
        driver.get(config.URL)
        auth_section.perform_login(driver, wait, config)
        
        # Navigate to Employee page
        nav_section.go_to_employee_page(driver, wait)
        time.sleep(2) # Give Angular a moment to settle

    def test_employee_empty_form_errors(self, driver, wait):
        """Verify clicking Submit on an empty Employee form triggers mandatory validations."""
        
        # 1. Force click the Submit button
        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        
        # 2. Give Angular a second to render the red texts
        time.sleep(1) 
        
        # 3. Grab all visible error texts using our JavaScript trick
        errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
        error_texts = [driver.execute_script("return arguments[0].textContent;", err).strip().lower() for err in errors if err != ""]
        
        logger.info(f"\n[DEBUG] Empty Employee Form Errors Found: {error_texts}")
        
        # 4. Assert core employee fields are caught
        error_string_block = " ".join(error_texts)
        assert "name" in error_string_block, "Validation missing for Employee Name!"
        assert "email" in error_string_block, "Validation missing for Email!"
        assert "phone" in error_string_block or "mobile" in error_string_block, "Validation missing for Phone!"
        
        # THIS IS THE FIX: Checking for maker/checker instead of designation
        assert "maker" in error_string_block or "checker" in error_string_block, "Validation missing for Maker/Checker!"

    def test_employee_name_alphabet_only_validation(self, driver, wait):
        """Verify the Employee Name field strictly rejects numbers and special characters."""
        
        # 1. Enter an explicitly invalid name containing numbers and symbols
        name_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@formcontrolname='emp_name']")))
        name_input.clear()
        name_input.send_keys("John123!@#")
        
        # 2. Force click Submit
        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        
        time.sleep(1)
        
        # 3. Grab all visible error texts
        errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
        error_texts = [driver.execute_script("return arguments[0].textContent;", err).strip().lower() for err in errors if err != ""]
        
        logger.info(f"\n[DEBUG] Invalid Employee Name Errors Found: {error_texts}")
        
        # 4. Assert the system rejected the non-alphabetical characters
        error_string_block = " ".join(error_texts)
        assert "name" in error_string_block or "character" in error_string_block or "invalid" in error_string_block, "BUG: The system accepted numbers/symbols in the Employee Name field!"