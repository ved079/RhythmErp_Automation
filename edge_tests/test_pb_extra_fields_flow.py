import sys
import os
import copy
import time
import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common import auth_section, nav_section
from privateb2b.purchase import gatepass_section, grn_section, purchase_booking_section, qc_section
from data.test_data import (
    gatepass_data, grn_data, qc_data, purchase_booking_data,
    get_qc_parameters, gen_empty_bag_weight, gen_labour_charges, SHARED_TRANSACTION_DATE
)
import config

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


def test_full_purchase_with_extra_fields():
    """
    Runs the full purchase flow using data from test_data, but adds random
    empty bag weight and labour charges to the gate pass items, then verifies
    the effect in the exported Excel report.
    """
    # Deep copy the original data so we don't modify the originals globally
    gp_data = copy.deepcopy(gatepass_data)
    grn_data_copy = copy.deepcopy(grn_data)
    qc_data_copy = copy.deepcopy(qc_data)
    pb_data = copy.deepcopy(purchase_booking_data)

    # Add random empty bag weight and labour charges to each item in the gate pass
    for item in gp_data['items']:
        item['empty_bag_weight'] = gen_empty_bag_weight()
        item['labour_charges'] = gen_labour_charges()
        logger.info(f"   🧪 Added to {item['item']}: Empty Bag = {item['empty_bag_weight']}, Labour = {item['labour_charges']}")

    # The purchase booking uses the same items list, so we sync it
    pb_data['items'] = gp_data['items']

    # Map the correct QC parameters to the dynamically copied items
    qc_items = []
    for item in gp_data['items']:
        qc_items.append({
            "item": item['item'],
            "qc_parameters": get_qc_parameters(item['item'])
        })
    qc_data_copy['items'] = qc_items
    qc_data_copy['transaction_date'] = SHARED_TRANSACTION_DATE

    # Ensure the gate pass and purchase booking also have the transaction date
    gp_data['transaction_date'] = SHARED_TRANSACTION_DATE
    pb_data['transaction_date'] = SHARED_TRANSACTION_DATE

    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)

    try:
        logger.info("\n🔐 Logging in...")
        auth_section.perform_login(driver, wait, config)

        logger.info("\n📦 Creating Gate Pass...")
        nav_section.go_to_gatepass_page(driver, wait)
        gatepass_section.fill_gatepass_registration(driver, wait, gp_data)

        # logger.info("\n📄 Creating GRN...")
        # nav_section.go_to_grn_page(driver, wait)
        # grn_section.fill_grn_registration(driver, wait, grn_data_copy)
        # grn_section.approve_latest_grn(driver, wait)

        logger.info("\n🔬 Creating QC...")
        nav_section.go_to_qc_page(driver, wait)
        qc_section.fill_qc_registration(driver, wait, qc_data_copy)

        logger.info("\n📑 Creating Purchase Booking (with AUDIT fields)...")
        nav_section.go_to_purchase_booking_page(driver, wait)
        
        # -------------------------------------------------------------
        # THE FIX: Call the new Audit function, NOT the normal function
        # -------------------------------------------------------------
        purchase_booking_section.fill_purchase_booking_with_extra_fields(driver, wait, pb_data)

        logger.info("\n✅ Full purchase flow with extra fields completed and Excel generated.")
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        raise
    finally:
        time.sleep(2)
        driver.quit()


if __name__ == "__main__":
    test_full_purchase_with_extra_fields()