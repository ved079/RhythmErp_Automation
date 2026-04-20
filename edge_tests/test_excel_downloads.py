import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from common import auth_section
import config

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def set_download_preferences(driver, download_dir):
    driver.execute_cdp_cmd('Page.setDownloadBehavior', {
        'behavior': 'allow',
        'downloadPath': download_dir
    })

def wait_for_download(download_dir, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        files = [f for f in os.listdir(download_dir) if f.endswith(('.xlsx', '.xls'))]
        if files:
            latest = max([os.path.join(download_dir, f) for f in files], key=os.path.getmtime)
            time.sleep(5)
            return latest
        time.sleep(0.5)
    raise Exception("Download timed out")

def close_overlays(driver, wait):
    """Close any open dropdown overlays or SweetAlert."""
    try:
        driver.find_element(By.TAG_NAME, "body").click()
        time.sleep(0.3)
    except:
        pass
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-backdrop")))
    except:
        pass

def smart_click(driver, wait, element):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    driver.execute_script("arguments[0].click();", element)

def is_element_visible(driver, by, value):
    try:
        el = driver.find_element(by, value)
        return el.is_displayed()
    except:
        return False

# ------------------------------------------------------------
# Navigation functions (each goes to list page, not add form)
# ------------------------------------------------------------
def go_to_farmer_list(driver, wait):
    logger.info("   Navigating to Farmer list...")
    close_overlays(driver, wait)
    farmer_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Farmer")))
    smart_click(driver, wait, farmer_link)
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Farmer list loaded.")

def go_to_supplier_list(driver, wait):
    logger.info("   Navigating to Supplier list...")
    close_overlays(driver, wait)
    supplier_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Supplier")))
    smart_click(driver, wait, supplier_link)
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Supplier list loaded.")

def go_to_agent_list(driver, wait):
    logger.info("   Navigating to Agent list...")
    close_overlays(driver, wait)
    agent_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'agent-registration')]")))
    smart_click(driver, wait, agent_link)
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Agent list loaded.")

def go_to_customer_list(driver, wait):
    logger.info("   Navigating to Customer list...")
    close_overlays(driver, wait)
    customer_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'customer-registration')]")))
    smart_click(driver, wait, customer_link)
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Customer list loaded.")

def go_to_employee_list(driver, wait):
    logger.info("   Navigating to Employee list...")
    close_overlays(driver, wait)
    employee_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'user')]")))
    smart_click(driver, wait, employee_link)
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Employee list loaded.")

def go_to_purchase_order_list(driver, wait):
    logger.info("   Navigating to Purchase Order list...")
    close_overlays(driver, wait)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)
    
    # If already visible, click directly
    if is_element_visible(driver, By.LINK_TEXT, "Purchase Order"):
        po = driver.find_element(By.LINK_TEXT, "Purchase Order")
        smart_click(driver, wait, po)
    else:
        # Open B2B -> Purchase
        b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
        smart_click(driver, wait, b2b)
        time.sleep(1)
        purchase = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase")))
        smart_click(driver, wait, purchase)
        time.sleep(1)
        po = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase Order")))
        smart_click(driver, wait, po)
    
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Purchase Order list loaded.")

def go_to_gatepass_list(driver, wait):
    logger.info("   Navigating to Gate Pass list...")
    close_overlays(driver, wait)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)
    
    if is_element_visible(driver, By.LINK_TEXT, "Gate Pass"):
        gp = driver.find_element(By.LINK_TEXT, "Gate Pass")
        smart_click(driver, wait, gp)
    else:
        b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
        smart_click(driver, wait, b2b)
        time.sleep(1)
        purchase = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase")))
        smart_click(driver, wait, purchase)
        time.sleep(1)
        gp = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Gate Pass")))
        smart_click(driver, wait, gp)
    
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Gate Pass list loaded.")

def go_to_grn_list(driver, wait):
    logger.info("   Navigating to GRN list...")
    close_overlays(driver, wait)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)
    
    if is_element_visible(driver, By.LINK_TEXT, "GRN"):
        grn = driver.find_element(By.LINK_TEXT, "GRN")
        smart_click(driver, wait, grn)
    else:
        b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
        smart_click(driver, wait, b2b)
        time.sleep(1)
        purchase = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase")))
        smart_click(driver, wait, purchase)
        time.sleep(1)
        grn = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "GRN")))
        smart_click(driver, wait, grn)
    
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ GRN list loaded.")

def go_to_qc_list(driver, wait):
    logger.info("   Navigating to QC list...")
    close_overlays(driver, wait)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)
    
    if is_element_visible(driver, By.LINK_TEXT, "QC"):
        qc = driver.find_element(By.LINK_TEXT, "QC")
        smart_click(driver, wait, qc)
    else:
        b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
        smart_click(driver, wait, b2b)
        time.sleep(1)
        purchase = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase")))
        smart_click(driver, wait, purchase)
        time.sleep(1)
        qc = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "QC")))
        smart_click(driver, wait, qc)
    
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ QC list loaded.")

def go_to_purchase_booking_list(driver, wait):
    logger.info("   Navigating to Purchase Booking list...")
    close_overlays(driver, wait)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)
    
    if is_element_visible(driver, By.LINK_TEXT, "Purchase Booking"):
        pb = driver.find_element(By.LINK_TEXT, "Purchase Booking")
        smart_click(driver, wait, pb)
    else:
        b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
        smart_click(driver, wait, b2b)
        time.sleep(1)
        purchase = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase")))
        smart_click(driver, wait, purchase)
        time.sleep(1)
        pb = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase Booking")))
        smart_click(driver, wait, pb)
    
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Purchase Booking list loaded.")

def go_to_sales_order_list(driver, wait):
    logger.info("   Navigating to Sales Order list...")
    close_overlays(driver, wait)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # Ensure B2B menu is collapsed? Actually we want it open. But if it's stuck, we click body first.
    try:
        driver.find_element(By.TAG_NAME, "body").click()
    except:
        pass

    # Try to click Sales Order directly if visible
    if is_element_visible(driver, By.LINK_TEXT, "Sales Order"):
        so = driver.find_element(By.LINK_TEXT, "Sales Order")
        smart_click(driver, wait, so)
    else:
        # Click B2B – but if it's already open, clicking it again might close it. So we check if Sales is visible.
        # Better: if Sales is not visible, then click B2B.
        sales_visible = is_element_visible(driver, By.LINK_TEXT, "Sales")
        if not sales_visible:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
            smart_click(driver, wait, b2b)
            time.sleep(1)
        # Now Sales should be visible
        sales = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sales")))
        smart_click(driver, wait, sales)
        time.sleep(1)
        so = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sales Order")))
        smart_click(driver, wait, so)

    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Sales Order list loaded.")

def go_to_lot_creation_list(driver, wait):
    logger.info("   Navigating to Lot Creation list...")
    close_overlays(driver, wait)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    if is_element_visible(driver, By.LINK_TEXT, "Lot Creation"):
        lot = driver.find_element(By.LINK_TEXT, "Lot Creation")
        smart_click(driver, wait, lot)
    else:
        sales_visible = is_element_visible(driver, By.LINK_TEXT, "Sales")
        if not sales_visible:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
            smart_click(driver, wait, b2b)
            time.sleep(1)
        sales = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sales")))
        smart_click(driver, wait, sales)
        time.sleep(1)
        lot = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Lot Creation")))
        smart_click(driver, wait, lot)

    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Lot Creation list loaded.")

def go_to_dispatch_note_list(driver, wait):
    logger.info("   Navigating to Dispatch Note list...")
    close_overlays(driver, wait)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    if is_element_visible(driver, By.LINK_TEXT, "Dispatch Note"):
        dn = driver.find_element(By.LINK_TEXT, "Dispatch Note")
        smart_click(driver, wait, dn)
    else:
        sales_visible = is_element_visible(driver, By.LINK_TEXT, "Sales")
        if not sales_visible:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
            smart_click(driver, wait, b2b)
            time.sleep(1)
        sales = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sales")))
        smart_click(driver, wait, sales)
        time.sleep(1)
        dn = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Dispatch Note")))
        smart_click(driver, wait, dn)

    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Dispatch Note list loaded.")

def go_to_invoice_list(driver, wait):
    logger.info("   Navigating to Invoice list...")
    close_overlays(driver, wait)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    if is_element_visible(driver, By.LINK_TEXT, "Invoice"):
        inv = driver.find_element(By.LINK_TEXT, "Invoice")
        smart_click(driver, wait, inv)
    else:
        sales_visible = is_element_visible(driver, By.LINK_TEXT, "Sales")
        if not sales_visible:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
            smart_click(driver, wait, b2b)
            time.sleep(1)
        sales = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sales")))
        smart_click(driver, wait, sales)
        time.sleep(1)
        inv = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Invoice")))
        smart_click(driver, wait, inv)

    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Invoice list loaded.")

def go_to_receipt_list(driver, wait):
    logger.info("   Navigating to Receipt list...")
    close_overlays(driver, wait)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    if is_element_visible(driver, By.LINK_TEXT, "Receipt"):
        receipt = driver.find_element(By.LINK_TEXT, "Receipt")
        smart_click(driver, wait, receipt)
    else:
        sales_visible = is_element_visible(driver, By.LINK_TEXT, "Sales")
        if not sales_visible:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
            smart_click(driver, wait, b2b)
            time.sleep(1)
        sales = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sales")))
        smart_click(driver, wait, sales)
        time.sleep(1)
        receipt = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Receipt")))
        smart_click(driver, wait, receipt)

    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("   ✅ Receipt list loaded.")
# ------------------------------------------------------------
# Main test
# ------------------------------------------------------------
def test_download_all_excel_files():
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)
    set_download_preferences(driver, download_dir)

    try:
        logger.info("\n🔐 Logging in...")
        auth_section.perform_login(driver, wait, config)

        screens = [
            # ("Farmer", go_to_farmer_list),
            ("Supplier", go_to_supplier_list),
            ("Agent", go_to_agent_list),
            ("Customer", go_to_customer_list),
            ("Employee", go_to_employee_list),
            ("Purchase Order", go_to_purchase_order_list),
            ("Gate Pass", go_to_gatepass_list),
            ("GRN", go_to_grn_list),
            ("QC", go_to_qc_list),
            ("Purchase Booking", go_to_purchase_booking_list),
            ("Sales Order", go_to_sales_order_list),
            ("Lot Creation", go_to_lot_creation_list),
            ("Dispatch Note", go_to_dispatch_note_list),
            ("Invoice", go_to_invoice_list),
            ("Receipt", go_to_receipt_list),
        ]

        for name, nav_func in screens:
            logger.info(f"\n📁 Testing Excel download for: {name}")
            nav_func(driver, wait)

            # Find Download Excel button
            try:
                download_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[.//span[text()='Download Excel']]")
                    )
                )
            except TimeoutException:
                download_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(.,'Download Excel')]")
                    )
                )

            # Clear previous downloads
            for f in os.listdir(download_dir):
                if f.endswith(('.xlsx', '.xls')):
                    os.remove(os.path.join(download_dir, f))

            smart_click(driver, wait, download_btn)

            downloaded_file = wait_for_download(download_dir, timeout=30)
            assert os.path.getsize(downloaded_file) > 0
            logger.info(f"   ✅ Downloaded: {os.path.basename(downloaded_file)} ({os.path.getsize(downloaded_file)} bytes)")

            os.remove(downloaded_file)

        logger.info("\n🎉 All Excel downloads verified successfully!")

    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        driver.save_screenshot("excel_download_error.png")
        raise
    finally:
        time.sleep(2)
        driver.quit()

if __name__ == "__main__":
    test_download_all_excel_files()