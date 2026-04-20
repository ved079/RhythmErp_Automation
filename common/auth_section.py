from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

# Set up module-level logger (same format as other modules)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

def perform_login(driver, wait, config):
    logger.info("Step 1: Logging in...")
    driver.get(config.URL)

    # Username
    username = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@formcontrolname='username']")
    ))
    username.clear()
    username.send_keys(config.USER)

    # Password
    password = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@formcontrolname='password']")
    ))
    password.clear()
    password.send_keys(config.PASS)

    # First login click
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

    time.sleep(2)

    # Tenant dropdown
    dropdown = wait.until(EC.element_to_be_clickable((By.TAG_NAME, "mat-select")))
    driver.execute_script("arguments[0].click();", dropdown)

    # Select tenant
    tenant = wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//mat-option//span[contains(text(), '{config.TENANT_NAME}')]")
    ))
    tenant.click()

    time.sleep(1)

    # Final login click
    final_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
    driver.execute_script("arguments[0].click();", final_btn)

    logger.info("✅ Login Successful")