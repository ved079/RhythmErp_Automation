import sys
import os
import shutil
import logging
from selenium.webdriver.chrome.options import Options

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# Go up two levels to reach the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

# Import utilities, config, and data
from common import auth_section
import config
from data.test_data import payable_data, receivable_data

# Import the specific report test function
from reports.test_cases.payable_recouncliation_test import run_payable_reconciliation
from reports.test_cases.receivable_reconciliation_test import run_receivable_reconciliation

if __name__ == "__main__":
    # Setup isolated download directory for these tests
    download_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "downloads"))
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # Configure Chrome to download files silently to our target directory
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

        logger.info("\n▶️ [RUNNING TEST 1]: Payable Deep-Dive Reconciliation")
        
        # CORRECTED: Calling the imported function directly with all 3 arguments
        run_payable_reconciliation(driver, wait, payable_data)
        run_receivable_reconciliation(driver, wait, receivable_data)

        logger.info("✅ [PAYABLE RECONCILIATION COMPLETED]")
        logger.info("\n🏆 ALL REPORT TEST SUITES EXECUTED SUCCESSFULLY!")

    except Exception as e:
        logger.error(f"\n❌ A CRITICAL ERROR OCCURRED: {e}")
        driver.save_screenshot("reports_runner_fatal_error.png")

    finally:
        logger.info("\n🧹 Cleaning up and closing browser...")
        driver.quit()