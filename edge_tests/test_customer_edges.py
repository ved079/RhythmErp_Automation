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


class TestCustomerEdgeCases:

    @pytest.fixture(autouse=True)
    def setup_and_navigate(self, driver, wait):
        """Automatically log in and navigate to the Customer Registration page."""
        driver.get(config.URL)
        auth_section.perform_login(driver, wait, config)
        
        # Navigate to Customer page
        nav_section.go_to_customer_page(driver, wait)
        time.sleep(2) # Give Angular a moment to settle

    def test_customer_empty_form_errors(self, driver, wait):
        """Verify clicking Submit on an empty Customer form triggers mandatory validations."""
        
        # 1. Force click the Submit button
        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.right button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        
        time.sleep(1) 
        
        # 3. Grab all visible error texts using our JavaScript trick
        errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
        error_texts = [driver.execute_script("return arguments[0].textContent;", err).strip().lower() for err in errors if err != ""]
        
        logger.info(f"\n[DEBUG] Empty Customer Form Errors Found: {error_texts}")
        
        # 4. Assert core customer fields are caught
        error_string_block = " ".join(error_texts)
        assert "company" in error_string_block, "Validation missing for Company Name!"
        assert "phone" in error_string_block or "mobile" in error_string_block, "Validation missing for Mobile Number!"
        assert "pan" in error_string_block, "Validation missing for PAN Number!"
        # We check for these to see if they are actually mandatory!
        assert "supply" in error_string_block or "type" in error_string_block, "Validation missing for Supply/Customer Type!"

    def test_customer_deposit_numeric_only_validation(self, driver, wait):
        """Verify the Deposit field inside Additional Details strictly rejects alphabetical letters."""
        
        # 1. Expand the "Additional Details" accordion so the Deposit field becomes visible
        accordion_header = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='header accordian']//strong[contains(text(), 'Additional Details')]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", accordion_header)
        accordion_header.click()
        time.sleep(1) # Wait for animation
        
        # 2. Find the Deposit field and enter letters
        deposit_input = wait.until(EC.presence_of_element_located((By.ID, "deposit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", deposit_input)
        time.sleep(0.5)
        
        deposit_input.clear()
        deposit_input.send_keys("ABC")
        
        # 3. Force click Submit
        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.right button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        
        time.sleep(1)
        
        # 4. Grab all visible error texts
        errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
        error_texts = [driver.execute_script("return arguments[0].textContent;", err).strip().lower() for err in errors if err != ""]
        
        logger.info(f"\n[DEBUG] Invalid Deposit Errors Found: {error_texts}")
        
        # 5. Assert the system rejected the letters (STRICT MATCH)
        error_string_block = " ".join(error_texts)
        assert "deposit" in error_string_block, "BUG: The system accepted letters (ABC) in the Deposit field!"