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


class TestAgentEdgeCases:

    @pytest.fixture(autouse=True)
    def setup_and_navigate(self, driver, wait):
        """Automatically log in and navigate to the Agent Registration page."""
        driver.get(config.URL)
        auth_section.perform_login(driver, wait, config)
        
        # Navigate to Agent page
        nav_section.go_to_agent_page(driver, wait)
        time.sleep(2) # Give Angular a moment to settle

    def test_agent_empty_form_errors(self, driver, wait):
        """Verify clicking Submit on an empty Agent form triggers mandatory validations."""
        
        # 1. Force click the Submit button 
        # FIX: Updated selector specifically for the Agent page footer
        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.right button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        
        time.sleep(1) 
        
        # 3. Grab all visible error texts using our JavaScript trick
        errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
        error_texts = [driver.execute_script("return arguments[0].textContent;", err).strip().lower() for err in errors if err != ""]
        
        logger.info(f"\n[DEBUG] Empty Agent Form Errors Found: {error_texts}")
        
        # 4. Assert actual core agent fields are caught
        error_string_block = " ".join(error_texts)
        assert "name" in error_string_block, "Validation missing for Agent Name!"
        assert "phone" in error_string_block or "mobile" in error_string_block, "Validation missing for Phone!"
        assert "basis" in error_string_block, "Validation missing for Basis Type!"
        assert "bank" in error_string_block, "Validation missing for Bank Name!"

    def test_agent_commission_numeric_only_validation(self, driver, wait):
        """Verify the Commission field strictly rejects alphabetical letters."""
        
        # 1. Wait for presence (not visibility), scroll to it, and enter letters
        commission_input = wait.until(EC.presence_of_element_located((By.ID, "commission")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", commission_input)
        time.sleep(0.5) # Give Angular a split second after scrolling
        
        commission_input.clear()
        commission_input.send_keys("ABC")
        
        # 2. Force click Submit (Using the FIXED selector for the Agent page footer)
        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.right button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        
        time.sleep(1)
        
        # 3. Grab all visible error texts
        errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
        error_texts = [driver.execute_script("return arguments[0].textContent;", err).strip().lower() for err in errors if err != ""]
        
        logger.info(f"\n[DEBUG] Invalid Commission Errors Found: {error_texts}")
        
        # 4. Assert the system rejected the letters
        error_string_block = " ".join(error_texts)
        assert "commission" in error_string_block, "BUG: The system accepted letters (ABC) in the Commission field!"