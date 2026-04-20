from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import logging
import config
from common import auth_section, nav_section
from Registration import farmer_section, supplier_section, agent_section, customer_section, employee_section
from privateb2b.purchase import qc_section       
from data.test_data import (
    farmer_data,
    supplier_data,
    agent_data,
    customer_data,
    employee_data,
    gatepass_data,
    grn_data,
    qc_data,
    purchase_booking_data,
    farmer_update_data
)
from privateb2b.purchase import gatepass_section, grn_section, purchase_booking_section
from updates.registration_screens import farmer_update
import time

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 60)

try:
    auth_section.perform_login(driver, wait, config)

    nav_section.go_to_farmer_page(driver, wait)
    farmer_section.fill_registration(driver, wait, farmer_data)

    # nav_section.go_to_supplier_page(driver, wait)
    # supplier_section.fill_supplier_registration(driver, wait, supplier_data)

    # nav_section.go_to_agent_page(driver, wait)
    # agent_section.fill_agent_registration(driver, wait, agent_data)

    # nav_section.go_to_customer_page(driver, wait)
    # customer_section.fill_customer_registration(driver, wait, customer_data)

    # nav_section.go_to_employee_page(driver, wait)
    # employee_section.fill_employee_registration(driver, wait, employee_data)


    logger.info("✅ SUCCESS: All forms filled!")
    time.sleep(20)

finally:
    driver.quit()