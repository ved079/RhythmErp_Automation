from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import logging

# Adjust these imports based on your actual folder structure
from common import nav_section, auth_section 
from privateb2b.purchase import purchase_booking_section
from data.test_data import SHARED_SUPPLIER
import config 

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


def test_run_export():
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)

    try:
        # 1. Login using your framework's auth section
        logger.info("Step 1: Logging in...")
        auth_section.perform_login(driver, wait, config)
        
        # 2. Navigate straight to Purchase Booking
        logger.info("\nStep 2: Navigating to Purchase Booking page...")
        nav_section.go_to_purchase_booking_page(driver, wait)
        
        # 3. Run the Search & Export
        logger.info("\nStep 3: Searching and Exporting...")
        purchase_booking_section.search_and_export_latest_pb(driver, wait, SHARED_SUPPLIER)

        logger.info("\n🎉 Test Case Completed Successfully!")

    except Exception as e:
        logger.error(f"\n❌ Test Failed: {e}")
        raise  # <--- ADD THIS LINE! This forces Pytest to mark it RED if it fails.
    finally:
        logger.info("\nClosing browser...")
        driver.quit()

if __name__ == "__main__":
    test_run_export()