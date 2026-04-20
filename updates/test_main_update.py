import sys
import os
import time
import pytest
import logging

# THE FIX: This must happen before ANY custom imports so Python knows where the root folder is.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

import config
from common import auth_section, nav_section
from Registration import farmer_section, supplier_section, agent_section, customer_section, employee_section
from updates.registration_screens import farmer_update, supplier_update, agent_update, customer_update, employee_update
from data.test_data import (farmer_data, farmer_update_data, supplier_data, updated_supplier_data, 
                            agent_data, updated_agent_data, customer_data, updated_customer_data, 
                            employee_data, updated_employee_data)

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


# ==========================================
# TEST 1: FARMER UPDATE
# ==========================================
# def test_farmer_update():
#     driver = webdriver.Chrome()
#     driver.maximize_window()
#     wait = WebDriverWait(driver, 60)

#     try:
#         # 1. Login
#         auth_section.perform_login(driver, wait, config)

#         # 2. Create a new farmer
#         nav_section.go_to_farmer_page(driver, wait)
#         farmer_section.fill_registration(driver, wait, farmer_data)
        
#         # 3. Navigate to the Farmer List
#         nav_section.go_to_farmer_list(driver, wait)
        
#         # 4. Run the update test
#         farmer_update.update_latest_farmer(driver, wait, farmer_data, farmer_update_data)

#         logger.info("✅ Farmer update test completed successfully!")
#         time.sleep(2)

#     finally:
#         driver.quit()

# ==========================================
# TEST 2: SUPPLIER UPDATE
# ==========================================
def test_supplier_update():
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)

    try:
        # 1. Login
        auth_section.perform_login(driver, wait, config)

        # 2. Create a new supplier
        nav_section.go_to_supplier_page(driver, wait)
        
        # FIX: Call the correctly named function
        supplier_section.fill_supplier_registration(driver, wait, supplier_data)
        
        # 3. Navigate to the Supplier List
        nav_section.go_to_supplier_list(driver, wait)
        
        # 4. Run the update test
        supplier_update.update_latest_supplier(driver, wait, supplier_data, updated_supplier_data)

        logger.info("✅ Supplier update test completed successfully!")
        time.sleep(2)

    finally:
        driver.quit()

# # ==========================================
# # TEST 3: AGENT UPDATE
# # ==========================================
# def test_agent_update():
#     driver = webdriver.Chrome()
#     driver.maximize_window()
#     wait = WebDriverWait(driver, 60)

#     try:
#         # 1. Login
#         auth_section.perform_login(driver, wait, config)

#         # 2. Create a new agent
#         nav_section.go_to_agent_page(driver, wait)
        
#         # Ensure you call whatever function creates an agent inside Registration/agent_section.py
#         agent_section.fill_agent_registration(driver, wait, agent_data) 
        
#         # 3. Navigate to the Agent List
#         nav_section.go_to_agent_list(driver, wait)
        
#         # 4. Run the update test
#         agent_update.update_latest_agent(driver, wait, agent_data, updated_agent_data)

#         logger.info("✅ Agent update test completed successfully!")
#         time.sleep(2)

#     finally:
#         driver.quit()

# # # ==========================================
# # # TEST 4: CUSTOMER UPDATE
# # # ==========================================
# def test_customer_update():
#     driver = webdriver.Chrome()
#     driver.maximize_window()
#     wait = WebDriverWait(driver, 60)

#     try:
#         # 1. Login
#         auth_section.perform_login(driver, wait, config)

#         # 2. Create a new customer
#         nav_section.go_to_customer_page(driver, wait)
        
#         # Ensure you call whatever function creates a customer inside Registration/customer_section.py
#         customer_section.fill_customer_registration(driver, wait, customer_data) 
        
#         # 3. Navigate to the Customer List
#         nav_section.go_to_customer_list(driver, wait)
        
#         # 4. Run the update test
#         customer_update.update_latest_customer(driver, wait, customer_data, updated_customer_data)

#         logger.info("✅ Customer update test completed successfully!")
#         time.sleep(2)

#     finally:
#         driver.quit()

# # ==========================================
# # TEST 5: EMPLOYEE UPDATE
# # ==========================================
# def test_employee_update():
#     driver = webdriver.Chrome()
#     driver.maximize_window()
#     wait = WebDriverWait(driver, 60)

#     try:
#         auth_section.perform_login(driver, wait, config)

#         nav_section.go_to_employee_page(driver, wait)
#         employee_section.fill_employee_registration(driver, wait, employee_data)

#         nav_section.go_to_employee_list(driver, wait)
#         employee_update.update_latest_employee(driver, wait, employee_data, updated_employee_data)

#         logger.info("✅ Employee update test completed successfully!")
#         time.sleep(2)

    # finally:
    #     driver.quit()