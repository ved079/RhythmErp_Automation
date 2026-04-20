import sys
import os
import shutil
import logging
from selenium.webdriver.chrome.options import Options

# Go up two levels to reach the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from common import auth_section, nav_section
import config
from data.test_data import (gatepass_data, grn_data, qc_data, purchase_booking_data, sales_order_data, 
                            dispatch_note_data, invoice_data, receipt_data)

# Import the test files
from privateb2b.test_cases.purchase import gate_pass_test
from privateb2b.test_cases.purchase import grn_test
from privateb2b.test_cases.purchase import qc_test           
from privateb2b.test_cases.purchase import purchase_booking_test
from privateb2b.test_cases.sales import sales_order_test
from privateb2b.test_cases.sales import lot_test
from privateb2b.test_cases.sales import dispatch_test
from privateb2b.test_cases.sales import invoice_test
from privateb2b.test_cases.sales import receipt_test

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

if __name__ == "__main__":
    # Setup download directory for Excel test
    download_dir = os.path.abspath("downloads")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    chrome_options = Options()
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)

    try:
        logger.info("🚀 LOGGING INTO FPC PORTAL...")
        auth_section.perform_login(driver, wait, config)

        ## ---------------------------------------------------------
        # # 1. GATE PASS MODULE
        # # ---------------------------------------------------------
        # nav_section.go_to_gatepass_page(driver, wait)
        # gate_pass_test.execute_gate_pass_suite(driver, wait, gatepass_data, download_dir)

        # # # ---------------------------------------------------------
        # # # 2. GRN MODULE
        # # # ---------------------------------------------------------
        # nav_section.go_to_grn_page(driver, wait)
        # grn_test.execute_grn_suite(driver, wait, grn_data, gatepass_data['items'], download_dir)

        # # # ---------------------------------------------------------
        # # # 3. QC MODULE
        # # # ---------------------------------------------------------
        # nav_section.go_to_qc_page(driver, wait) 
        # qc_test.execute_qc_suite(driver, wait, qc_data, gatepass_data['items'], download_dir)

        # # # ---------------------------------------------------------
        # # # 4. PURCHASE BOOKING MODULE
        # # # ---------------------------------------------------------
        # nav_section.go_to_purchase_booking_page(driver, wait)
        # purchase_booking_test.execute_purchase_suite(driver, wait, purchase_booking_data, download_dir)


        # # ---------------------------------------------------------
        # # 5. SALES ORDER MODULE
        # # ---------------------------------------------------------


        nav_section.go_to_sales_order_page(driver, wait)
        sales_order_test.execute_sales_order_suite(driver, wait, sales_order_data)
        
        nav_section.go_to_lot_creation_page(driver, wait)
        lot_test.execute_lot_suite(driver, wait, sales_order_data)

        nav_section.go_to_dispatch_note_page(driver,wait)
        dispatch_test.execute_dispatch_suite(driver, wait, dispatch_note_data)

        nav_section.go_to_invoice_page(driver, wait) 
        invoice_test.execute_invoice_suite(driver, wait, invoice_data)

        nav_section.go_to_receipt_page(driver,wait)
        receipt_test.execute_receipt_suite(driver, wait, receipt_data)


        # ... ADD MORE MODULES HERE AS YOU BUILD THEM ...

        logger.info("\n🏆 ALL TEST SUITES EXECUTED SUCCESSFULLY!")

    finally:
        driver.quit()
        # Optional: cleanup download directory
        shutil.rmtree(download_dir, ignore_errors=True)