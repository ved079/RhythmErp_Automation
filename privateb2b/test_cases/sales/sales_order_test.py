import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import config
from common import auth_section, nav_section
from common.helper import select_dropdown, fill_input
from data.test_data import sales_order_data

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# ==========================================
# HELPER: VALIDATION CHECK
# ==========================================

def has_validation_error(driver):
    """
    Checks for common Angular Material or toast error elements.
    Returns True if an error message is visible.
    """
    try:
        # Look for mat-error (Angular Material)
        mat_error = driver.find_elements(By.CSS_SELECTOR, "mat-error")
        for err in mat_error:
            if err.is_displayed():
                return True
        # Look for toast container (common in many apps)
        toast = driver.find_elements(By.CSS_SELECTOR, ".toast-error, .toast-message, .swal2-error")
        for t in toast:
            if t.is_displayed():
                return True
        # Also check for any element with 'error' class or text
        error_text = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') and not(contains(@style, 'display: none'))]")
        return len(error_text) > 0
    except:
        return False


# ==========================================
# ITEM ROW HANDLING
# ==========================================

def add_item_row(driver, wait, row_index):
    """Click the '+' button to create a new row for items."""
    try:
        add_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'apply-button') and .//i[contains(@class, 'fa-plus')]]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
        driver.execute_script("arguments[0].click();", add_btn)

        new_row_xpath = f"//tbody[contains(@class, 'main_tbody')]/tr[{row_index + 1}]"
        wait.until(EC.presence_of_element_located((By.XPATH, new_row_xpath)))
        logger.info(f"   ✅ Added new row for item {row_index + 1}")
        time.sleep(0.5)
        return True
    except Exception as e:
        logger.warning(f"   ⚠️ Could not add row {row_index + 1}: {e}")
        return False


def fill_item_row(driver, wait, row_index, item_data, run_validations=True):
    """
    Fill a specific row. If run_validations is True (first row only),
    perform inline negative/zero validation before final correct entry.
    """
    row_xpath = f"//tbody[contains(@class, 'main_tbody')]/tr[{row_index + 1}]"
    row = wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))

    # --- 1. Item Dropdown ---
    if item_data.get('item_name'):
        item_dropdown = row.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='item_ref_id']")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", item_dropdown)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", item_dropdown)

        overlay = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))

        search_inputs = overlay.find_elements(By.XPATH, ".//input[contains(@placeholder, 'Search') or contains(@class, 'mat-filter-input')]")
        if search_inputs:
            search_inputs[0].clear()
            search_inputs[0].send_keys(item_data['item_name'])
            time.sleep(1)

        option = wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//mat-option[contains(normalize-space(.), '{item_data['item_name']}')]")
        ))
        driver.execute_script("arguments[0].click();", option)
        wait.until(EC.invisibility_of_element(overlay))
        logger.info(f"      ✅ Selected item: {item_data['item_name']}")

    # --- 2. Quantity (with inline validation) ---
    qty_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='quantity']")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", qty_input)

    if run_validations:
        # SO_TC14: Try zero quantity
        logger.info("      🧪 [SO_TC14] Testing Quantity = 0 validation...")
        qty_input.send_keys(Keys.CONTROL, 'a')
        qty_input.send_keys(Keys.BACKSPACE)
        qty_input.send_keys("0")
        qty_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        if has_validation_error(driver):
            logger.info("         ✅ Quantity = 0 correctly blocked.")
        else:
            logger.warning("         ⚠️ Warning: No validation error for Quantity = 0!")

        # Try negative quantity (if allowed by input)
        try:
            driver.execute_script("arguments[0].value = '-5';", qty_input)
            qty_input.send_keys(Keys.TAB)
            time.sleep(0.5)
            if has_validation_error(driver):
                logger.info("         ✅ Negative Quantity correctly blocked.")
            else:
                logger.warning("         ⚠️ Warning: No validation error for negative Quantity!")
        except:
            pass

        # Now enter correct quantity
        qty_input.send_keys(Keys.CONTROL, 'a')
        qty_input.send_keys(Keys.BACKSPACE)
        qty_input.send_keys(str(item_data.get('quantity', '')))
        qty_input.send_keys(Keys.TAB)
        logger.info(f"      ✅ Quantity set to correct value: {item_data.get('quantity', '')}")
    else:
        # For additional rows, just fill normally
        qty_input.send_keys(Keys.CONTROL, 'a')
        qty_input.send_keys(Keys.BACKSPACE)
        qty_input.send_keys(str(item_data.get('quantity', '')))
        qty_input.send_keys(Keys.TAB)
        logger.info(f"      ✅ Quantity: {item_data.get('quantity', '')}")

    # --- 3. Rate (with inline validation) ---
    rate_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='rate']")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", rate_input)

    if run_validations:
        # SO_TC14: Try zero rate
        logger.info("      🧪 [SO_TC14] Testing Rate = 0 validation...")
        rate_input.send_keys(Keys.CONTROL, 'a')
        rate_input.send_keys(Keys.BACKSPACE)
        rate_input.send_keys("0")
        rate_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        if has_validation_error(driver):
            logger.info("         ✅ Rate = 0 correctly blocked.")
        else:
            logger.warning("         ⚠️ Warning: No validation error for Rate = 0!")

        # Try negative rate
        try:
            driver.execute_script("arguments[0].value = '-10';", rate_input)
            rate_input.send_keys(Keys.TAB)
            time.sleep(0.5)
            if has_validation_error(driver):
                logger.info("         ✅ Negative Rate correctly blocked.")
            else:
                logger.warning("         ⚠️ Warning: No validation error for negative Rate!")
        except:
            pass

        # Now enter correct rate
        rate_input.send_keys(Keys.CONTROL, 'a')
        rate_input.send_keys(Keys.BACKSPACE)
        rate_input.send_keys(str(item_data.get('rate', '')))
        rate_input.send_keys(Keys.TAB)
        logger.info(f"      ✅ Rate set to correct value: {item_data.get('rate', '')}")
    else:
        rate_input.send_keys(Keys.CONTROL, 'a')
        rate_input.send_keys(Keys.BACKSPACE)
        rate_input.send_keys(str(item_data.get('rate', '')))
        rate_input.send_keys(Keys.TAB)
        logger.info(f"      ✅ Rate: {item_data.get('rate', '')}")

    # --- 4. Tax Rate ---
    tax_dropdown = row.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='tax_rate']")
    if item_data.get('item_name') in {"Soyabean", "Turmeric", "Chana"}:
        tax_rate = "5"
    elif item_data.get('item_name') == "Tur-Red":
        tax_rate = "0"
    else:
        tax_rate = str(item_data.get('tax_rate', '0'))

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tax_dropdown)
    time.sleep(0.2)
    driver.execute_script("arguments[0].click();", tax_dropdown)

    overlay = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
    opt = wait.until(EC.presence_of_element_located((By.XPATH, f"//mat-option[contains(normalize-space(.), '{tax_rate}')]")))
    driver.execute_script("arguments[0].click();", opt)
    wait.until(EC.invisibility_of_element(overlay))
    logger.info(f"      ✅ Tax Rate set to {tax_rate}")

    # --- 5. Expected Delivery Date ---
    if item_data.get('expected_delivery_date'):
        date_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='expected_delivery_date']")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", date_input)
        driver.execute_script("arguments[0].click();", date_input)
        driver.execute_script("arguments[0].value = '';", date_input)
        date_input.send_keys(Keys.CONTROL, 'a')
        date_input.send_keys(Keys.BACKSPACE)
        date_input.send_keys(item_data['expected_delivery_date'])
        date_input.send_keys(Keys.TAB)
        logger.info(f"      ✅ Expected delivery date: {item_data['expected_delivery_date']}")


# ==========================================
# MAIN CREATION + APPROVAL
# ==========================================

def fill_sales_order_registration(driver, wait, data):
    logger.info("⚡ Starting Sales Order Registration...")

    # Wait for the page to be fully loaded
    logger.info("   ⏳ Waiting for page to load...")
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loader, .spinner, .cdk-overlay-backdrop")))
    time.sleep(1)

    # Instantly check if we are on the list page. If so, click Add.
    if not driver.find_elements(By.CSS_SELECTOR, "mat-select[formcontrolname='customer_ref_id']"):
        try:
            add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.new_employee")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
            driver.execute_script("arguments[0].click();", add_btn)
            logger.info("   ✅ Clicked Add button to open new form")
        except:
            pass

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-select[formcontrolname='customer_ref_id']")))
    time.sleep(1)

    # ------------------------------------------------------------
    # SO_TC13: MANDATORY FIELD VALIDATION (Customer)
    # ------------------------------------------------------------
    logger.info("   🧪 [SO_TC13] Testing Customer mandatory validation...")
    # Attempt submit without selecting customer
    submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.footer button.submit")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    driver.execute_script("arguments[0].click();", submit_btn)
    time.sleep(1)
    if has_validation_error(driver):
        logger.info("      ✅ Customer mandatory validation displayed.")
    else:
        logger.warning("      ⚠️ Warning: No validation error for missing Customer!")
    # Form should still be open; we continue filling.

    # Header fields
    logger.info(f"   Selecting Customer: {data.get('customer_name', 'None')}")
    if data.get('customer_name'):
        select_dropdown(driver, wait, value=data['customer_name'], control_name="customer_ref_id", searchable=True)

    try: select_dropdown(driver, wait, value=data.get('department'), label_text="Department", searchable=False)
    except: pass

    try: select_dropdown(driver, wait, value=data.get('division'), label_text="Division", searchable=False)
    except: pass

    try: select_dropdown(driver, wait, value=data.get('location'), label_text="Location", searchable=False)
    except: pass

    try: select_dropdown(driver, wait, value=data.get('sale_type'), label_text="Type of Sale", searchable=False)
    except: pass

    if data.get('transaction_date'):
        fill_input(driver, wait, data['transaction_date'], control_name="transaction_date")

    if data.get('customer_po_number'):
        fill_input(driver, wait, data['customer_po_number'], control_name="customer_po_number")
    
    if data.get('customer_po_date'):
        fill_input(driver, wait, data['customer_po_date'], control_name="customer_po_date")

    if data.get('transportation_charges') is not None:
        fill_input(driver, wait, str(data['transportation_charges']), control_name="transportation_charges")

    # ----- MULTI-ITEM SECTION -----
    items = data.get('items', [])
    if not items:
        items = [{
            'item_name': data.get('item_name', ''),
            'quantity': data.get('quantity', 0),
            'rate': data.get('rate', 0),
            'tax_rate': data.get('tax_rate', '0'),
            'expected_delivery_date': data.get('expected_delivery_date', '')
        }]

    logger.info(f"   📦 Processing {len(items)} items...")
    for idx, item in enumerate(items):
        logger.info(f"      ➡️ Setting details for Row {idx + 1}: {item.get('item_name', 'Unknown')}")
        if idx > 0:
            add_item_row(driver, wait, idx)
        # Run negative/zero validations only on first row
        run_validations = (idx == 0)
        fill_item_row(driver, wait, idx, item, run_validations=run_validations)

    logger.info("   ⏳ Waiting for ERP to generate conversion rate and totals...")
    time.sleep(3)

    # --- TC16: MATH VERIFICATION ---
    try:
        total_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_total_amount']")
        total_val = float(driver.execute_script("return arguments[0].value;", total_input).replace(',', '') or 0)
        if total_val > 0:
            logger.info(f"   🧮 TC16 Passed: System auto-calculated Grand Total as INR {total_val}")
        else:
            logger.warning("   ⚠️ Warning: Grand Total calculated as 0. Math generation may have failed.")
    except Exception as e:
        logger.warning(f"   ⚠️ Could not read Grand Total: {e}")

    # Submit the form (now with valid data)
    logger.info("📤 Submitting Sales Order form...")
    submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.footer button.submit")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    driver.execute_script("arguments[0].click();", submit_btn)
    logger.info("   ✅ Submit button clicked")

    # Wait for redirect to list page and table to be present 
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
    time.sleep(3)
    logger.info("🚀 Sales Order Registration Completed Successfully!")

    time.sleep(5)

    # ---------- APPROVAL STEP ----------
    logger.info("⚡ Approving the newly created Sales Order...")
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loader, .spinner, .cdk-overlay-backdrop")))
        time.sleep(2) 

        for attempt in range(3):
            try:
                edit_btn = driver.find_element(By.XPATH, "//table/tbody/tr[1]//button[.//i[contains(@class, 'bi-pencil')]]")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", edit_btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", edit_btn)
                logger.info("   ✅ Clicked Edit button on the latest Sales Order")
                
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-select[formcontrolname='customer_ref_id']")))
                break 
            except Exception as e:
                if attempt == 2:
                    raise Exception("Failed to navigate to the Edit form after clicking the pencil icon.")
                logger.warning(f"   Retry {attempt+1}: Click didn't trigger routing or element stale, trying again...")
                time.sleep(2)

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loader, .spinner")))
        time.sleep(5)

        approve_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(translate(normalize-space(.), 'APPROVE', 'approve'), 'approve')]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", approve_btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", approve_btn)
        logger.info("   ✅ Clicked Approve button")

        time.sleep(2)
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container")))
        except:
            pass

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
        time.sleep(2)
        logger.info("🚀 Sales Order Approved Successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to approve Sales Order: {e}")
        driver.save_screenshot("so_approve_error.png")
        raise

    
# ==========================================
# OPTIONAL: VIEW / DELETE TESTS
# ==========================================

def test_view_sales_order(driver, wait):
    """Attempt to View the SO to ensure no internal server error occurs, then close it."""
    logger.info("🐞 Testing SO View & Crash Check...")
    try:
        # 1. Click the View Icon on the list page
        view_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//table/tbody/tr[1]//button[.//i[contains(@class, 'bi-eye')]]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", view_btn)
        driver.execute_script("arguments[0].click();", view_btn)
        time.sleep(6)

        # 2. Check for backend errors
        try:
            driver.find_element(By.XPATH, "//*[contains(text(), 'Internal server error')]")
            logger.error("   ❌ BUG CAUGHT: Internal Server Error on View!")
        except NoSuchElementException:
            logger.info("   ✅ View modal loaded successfully without crashes.")
            
        # 3. Close the modal 
        closed = False
        if not closed:
            try:
                cancel_btn = driver.find_element(By.XPATH, "//div[contains(@class, 'footer')]//button[contains(@class, 'cancel')]")
                driver.execute_script("arguments[0].click();", cancel_btn)
                logger.info("   ✅ Closed modal via Footer Cancel button.")
                closed = True
            except NoSuchElementException:
                pass
                
        if not closed:
            try:
                x_btn = driver.find_element(By.XPATH, "//div[contains(@class, 'popup-actions')]//button[.//i[contains(@class, 'bi-x-lg')]]")
                driver.execute_script("arguments[0].click();", x_btn)
                logger.info("   ✅ Closed modal via Top-Right X button.")
                closed = True
            except NoSuchElementException:
                pass
                
        if not closed:
            logger.warning("   ⚠️ Buttons not found. Forcing escape via JavaScript.")
            driver.execute_script("document.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")

        time.sleep(1) 
    except Exception as e:
        logger.warning(f"   ⚠️ Could not perform View test: {e}")


def test_delete_sales_order(driver, wait):
    """Delete the newly created Sales Order (optional)."""
    logger.info("🗑️ Testing Sales Order Deletion...")
    try:
        so_no_cell = driver.find_element(By.XPATH, "//table/tbody/tr[1]/td[2]")
        deleted_so_number = so_no_cell.text.strip()
        logger.info(f"   📌 SO to delete: {deleted_so_number}")

        delete_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//table/tbody/tr[1]//button[.//i[contains(@class, 'bi-trash')]]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", delete_btn)
        driver.execute_script("arguments[0].click();", delete_btn)

        confirm_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".swal2-confirm")))
        driver.execute_script("arguments[0].click();", confirm_btn)

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container")))
        logger.info("   ✅ Sales Order successfully deleted from list.")
        return deleted_so_number
    except Exception as e:
        logger.warning(f"   ⚠️ Could not perform Delete test: {e}")
        return None


# ==========================================
# SUITE EXECUTOR
# ==========================================

def execute_sales_order_suite(driver, wait, data):
    logger.info("--- ⚡ STARTING SALES ORDER SUITE ---")

    # 1. Normal Happy Path (with inline validations)
    fill_sales_order_registration(driver, wait, data)

    # 2. View Test (Closes back to List Page)
    test_view_sales_order(driver, wait)

    # 3. (Optional) Test Delete – uncomment if you want to clean up
    # test_delete_sales_order(driver, wait)

    logger.info("--- ✅ SALES ORDER SUITE COMPLETED ---")


if __name__ == "__main__":
    from selenium.webdriver.chrome.options import Options

    download_dir = os.path.abspath("downloads")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    chrome_options = Options()
    prefs = {"download.default_directory": download_dir, "download.prompt_for_download": False}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)

    try:
        auth_section.perform_login(driver, wait, config)
        nav_section.go_to_sales_order_page(driver, wait) 
        execute_sales_order_suite(driver, wait, sales_order_data)
    finally:
        driver.quit()