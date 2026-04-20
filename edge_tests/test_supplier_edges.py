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

class TestSupplierEdgeCases:

    @pytest.fixture(autouse=True)
    def setup_and_navigate(self, driver, wait):
        """Automatically log in and navigate to the Supplier Registration page."""
        driver.get(config.URL)
        auth_section.perform_login(driver, wait, config)
        
        # Navigate to Supplier instead of Farmer
        nav_section.go_to_supplier_page(driver, wait)
        time.sleep(2) # Give Angular a moment to settle

    def test_supplier_empty_form_errors(self, driver, wait):
        """Verify clicking Submit on an empty Supplier form triggers mandatory validations."""
        
        # 1. Force click the Submit button
        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.right button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        
        # 2. Give Angular a second to render the red texts
        time.sleep(1) 
        
        # 3. Grab all visible error texts using our JavaScript trick
        errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
        error_texts = [driver.execute_script("return arguments[0].textContent;", err).strip().lower() for err in errors if err != ""]
        
        logger.info(f"\n[DEBUG] Empty Supplier Form Errors Found: {error_texts}")
        
        # 4. Assert core supplier fields are caught based on actual app behavior
        error_string_block = " ".join(error_texts)
        assert "company" in error_string_block, "Validation missing for Company Name!"
        assert "phone" in error_string_block, "Validation missing for Phone Number!"
        assert "pan" in error_string_block, "Validation missing for PAN Number!"

        
    def test_supplier_invalid_pan_format(self, driver, wait):
        """Verify the system strictly enforces Indian PAN Card formatting (e.g., ABCDE1234F)."""
        
        # 1. Enter an explicitly bad PAN format (just numbers)
        pan_input = wait.until(EC.visibility_of_element_located((By.ID, "pan_no")))
        pan_input.clear()
        pan_input.send_keys("1234567890")
        
        # 2. Force click Submit
        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.right button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        
        time.sleep(1)
        
        # 3. Grab all visible error texts
        errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
        error_texts = [driver.execute_script("return arguments[0].textContent;", err).strip().lower() for err in errors if err != ""]
        
        logger.info(f"\n[DEBUG] Invalid PAN Errors Found: {error_texts}")
        
        # 4. Assert the system rejected the bad PAN format
        error_string_block = " ".join(error_texts)
        assert "pan" in error_string_block or "valid" in error_string_block or "format" in error_string_block, "BUG: The system accepted an invalid PAN format!"