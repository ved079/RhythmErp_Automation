from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from common.helper import select_dropdown, fill_input, click_submit

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

def fill_employee_registration(driver, wait, data):
    logger.info("⚡ Starting Employee Registration...")

    # Wait for the form to load – first field 'emp_name'
    wait.until(EC.presence_of_element_located((By.XPATH, "//input[@formcontrolname='emp_name']")))
    time.sleep(0.5)

    # Employee Name (control_name)
    fill_input(driver, wait, data['employee_name'], control_name="emp_name")

    # Email (control_name)
    fill_input(driver, wait, data['email'], control_name="email")

    # Phone (control_name)
    fill_input(driver, wait, data['phone'], control_name="phone")

    # Designation (dropdown)
    select_dropdown(driver, wait, data['designation'], control_name="designation", searchable=True)

    # Maker/Checker (dropdown)
    select_dropdown(driver, wait, data['maker_checker'], control_name="maker_checker", searchable=True)

    # --- Submit Button ---
    logger.info("📤 Submitting the form...")
    time.sleep(1)
    click_submit(driver, wait)

    time.sleep(3)
    logger.info("🚀 Employee Registration Completed Successfully!")