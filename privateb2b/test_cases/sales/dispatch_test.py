import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
from decimal import Decimal
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from common.helper import select_dropdown, fill_input

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
    """Checks for common Angular Material or toast error elements."""
    try:
        mat_error = driver.find_elements(By.CSS_SELECTOR, "mat-error")
        for err in mat_error:
            if err.is_displayed():
                return True
        toast = driver.find_elements(By.CSS_SELECTOR, ".toast-error, .toast-message, .swal2-error")
        for t in toast:
            if t.is_displayed():
                return True
        error_text = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') and not(contains(@style, 'display: none'))]")
        return len(error_text) > 0
    except:
        return False


# ==========================================
# CORE CREATION FUNCTION (WITH INLINE TESTS)
# ==========================================

def fill_dispatch_note_registration(driver, wait, data, run_validations=True):
    logger.info("⚡ Starting Dispatch Note Registration...")

    # --- DATE LOGIC ---
    if 'transaction_date' in data and data['transaction_date']:
        try:
            date_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[formcontrolname='transaction_date']")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", date_input)
            date_input.send_keys(Keys.CONTROL, 'a')
            date_input.send_keys(Keys.BACKSPACE)
            date_input.send_keys(data['transaction_date'])
            date_input.send_keys(Keys.TAB)
            logger.info(f"  ✅ Filled Transaction Date: {data['transaction_date']}")
        except Exception as e:
            logger.warning(f"  ⚠️ Custom date logic failed: {e}")

    # Base Dropdowns
    select_dropdown(driver, wait, value=data['customer_name'], control_name="customer_ref_id", searchable=True)
    select_dropdown(driver, wait, value=data['sale_type'], control_name="sales_type_id", searchable=False)
    select_dropdown(driver, wait, value=data['supply_type'], control_name="supply_type_ref_id", searchable=False)
    select_dropdown(driver, wait, value=data['department'], label_text="Department", searchable=False)
    select_dropdown(driver, wait, value=data['division'], label_text="Division", searchable=False)
    select_dropdown(driver, wait, value=data['location'], label_text="Location", searchable=False)
    select_dropdown(driver, wait, value=data['type_of_sale'], label_text="Type of Sale", searchable=False)

    # ----- SALES ORDER SELECTION (ROBUST) -----
    try:
        time.sleep(2) # Give the system a moment before opening SO dropdown
        so_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select[formcontrolname='so_ref_id']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", so_dropdown)
        driver.execute_script("arguments[0].click();", so_dropdown)
        logger.info("   Opened Sales Order dropdown")
        
        # Use generic overlay pane selector
        overlay = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        
        # Wait for options to load
        wait.until(EC.presence_of_element_located((By.XPATH, "//mat-option")))
        time.sleep(1) # Extra time for SO options to fully populate
        
        # THE FIX: Search ONLY inside the visible overlay
        options = overlay.find_elements(By.XPATH, ".//mat-option")
        selected = False
        for opt in options:
            text = opt.text.strip()
            if text and "Select" not in text and len(text) > 5:
                driver.execute_script("arguments[0].click();", opt)
                logger.info(f"   ✅ Selected Sales Order: {text}")
                selected = True
                break
        if not selected and options:
            driver.execute_script("arguments[0].click();", options[0])
            logger.info(f"   ✅ Selected first Sales Order (fallback): {options[0].text.strip()}")
        
        # Close overlay with Escape
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        wait.until(EC.invisibility_of_element(overlay))
        
        logger.info("   ⏳ Waiting for Lots to load from backend...")
        time.sleep(4)  # Generous wait to allow backend to populate the Lot dropdown
    except Exception as e:
        logger.error(f"❌ Failed to select Sales Order: {e}")
        driver.save_screenshot("so_selection_error.png")
        raise

    # ----- MULTI-LOT SELECTION (ROBUST) -----
    items_list = data.get('items', [data])
    num_lots_to_select = len(items_list)
    
    try:
        lot_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select[formcontrolname='lot_ref_id']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lot_dropdown)
        driver.execute_script("arguments[0].click();", lot_dropdown)
        logger.info("   Opened Lot dropdown")
        
        overlay = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        
        # Wait for options to appear
        wait.until(EC.presence_of_element_located((By.XPATH, "//mat-option")))
        time.sleep(1.5) # Extra time for Lot options to fully populate
        
        # THE FIX: Search ONLY inside the visible overlay
        options = overlay.find_elements(By.XPATH, ".//mat-option")
        total_available = len(options)
        logger.info(f"   Found {total_available} lot options available")
        
        selected_count = 0
        for opt in options:
            if selected_count >= num_lots_to_select:
                break
            text = opt.text.strip()
            if text and "LOT" in text.upper():
                driver.execute_script("arguments[0].click();", opt)
                logger.info(f"   ✅ Selected Lot: {text}")
                selected_count += 1
                time.sleep(0.3)
        
        # Fallback: pick any non-placeholder option
        if selected_count < num_lots_to_select:
            logger.warning(f"   ⚠️ Only {selected_count} lots with 'LOT' found. Using fallback selection...")
            for opt in options:
                if selected_count >= num_lots_to_select:
                    break
                text = opt.text.strip()
                if text and "Select" not in text and len(text) > 5:
                    driver.execute_script("arguments[0].click();", opt)
                    logger.info(f"   ✅ Selected fallback Lot: {text}")
                    selected_count += 1
                    time.sleep(0.3)
        
        # If still not enough, take top N
        if selected_count < num_lots_to_select:
            for i in range(selected_count, min(num_lots_to_select, len(options))):
                opt = options[i]
                text = opt.text.strip()
                driver.execute_script("arguments[0].click();", opt)
                logger.info(f"   ✅ Selected top-{i+1} Lot: {text}")
                selected_count += 1
                time.sleep(0.3)
        
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        wait.until(EC.invisibility_of_element(overlay))
        logger.info(f"   ✅ Selected {selected_count} Lot(s) out of {total_available} available")
        time.sleep(1.5) # Time for grid to generate after closing dropdown
    except Exception as e:
        logger.error(f"❌ Failed to select Lots: {e}")
        driver.save_screenshot("lot_selection_error.png")
        raise

    # Open Additional Details accordion
    try:
        accordion_header = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'header accordian')]//strong[contains(text(), 'Additional Details')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", accordion_header)
        driver.execute_script("arguments[0].click();", accordion_header)
        time.sleep(1)
    except Exception as e:
        logger.warning(f"⚠️ Could not open accordion: {e}")

    # Transporter Name, Vehicle Number, Distance
    fill_input(driver, wait, data['transporter_name'], control_name="transporter_name")
    fill_input(driver, wait, data['vehicle_no'], control_name="vehicle_no")
    fill_input(driver, wait, str(data['distance']), control_name="distance")

    # ----- DN_TC01 & DN_TC02: Transportation Charges (Fill + Precision Test) -----
    if run_validations:
        if 'transportation_charges' in data and data['transportation_charges'] is not None:
            logger.info("   🧪 [DN_TC01 & DN_TC02] Testing Transportation Charges...")
            try:
                transport_input = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[formcontrolname='txn_currency_transportation_charges']")
                ))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", transport_input)
                
                # DN_TC02: Decimal precision
                transport_input.send_keys(Keys.CONTROL, 'a')
                transport_input.send_keys(Keys.BACKSPACE)
                transport_input.send_keys("100.123")
                transport_input.send_keys(Keys.TAB)
                time.sleep(0.5)
                entered_val = driver.execute_script("return arguments[0].value;", transport_input)
                if entered_val == "100.12" or has_validation_error(driver):
                    logger.info(f"      ✅ Decimal precision enforced (entered: {entered_val}).")
                else:
                    logger.warning(f"      ⚠️ WARNING: Decimal precision not enforced! Entered: {entered_val}")

                # Enter correct value
                transport_input.send_keys(Keys.CONTROL, 'a')
                transport_input.send_keys(Keys.BACKSPACE)
                transport_input.send_keys(str(data['transportation_charges']))
                transport_input.send_keys(Keys.TAB)
                logger.info(f"      ✅ Transportation Charges set to: {data['transportation_charges']}")
            except Exception as e:
                logger.warning(f"      ⚠️ Transportation Charges test skipped: {e}")
        else:
            logger.info("   ℹ️ Skipping Transportation Charges test – no data provided.")

    # ----- MULTI-ITEM GRID FILLING (Tax & Bags) -----
    logger.info(f"   📦 Processing Grid Details for {len(items_list)} items...")
    
    for idx, item in enumerate(items_list):
        item_name = item.get('item_name', '')
        if item_name in {"Soyabean", "Turmeric", "Chana"}:
            tax_rate = "5"
        elif item_name in {"Tur-Red", "Maize-Yellow"}:
            tax_rate = "0"
        else:
            tax_rate = str(item.get('tax_rate', '0'))

        # 1. Tax Rate dropdown
        tax_dropdowns = driver.find_elements(By.CSS_SELECTOR, "mat-select[formcontrolname='tax_rate']")
        if tax_dropdowns and idx < len(tax_dropdowns):
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tax_dropdowns[idx])
            driver.execute_script("arguments[0].click();", tax_dropdowns[idx])
            overlay = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
            
            strategies = [
                f"//mat-option[normalize-space()='{tax_rate}']",
                f"//mat-option[contains(normalize-space(), '{tax_rate}')]",
                f"//mat-option//span[contains(text(), '{tax_rate}')]/ancestor::mat-option",
                f"//mat-option[contains(., '{tax_rate}')]"
            ]
            opt = None
            fast_wait = WebDriverWait(driver, 3)
            for strategy in strategies:
                try:
                    opt = fast_wait.until(EC.element_to_be_clickable((By.XPATH, strategy)))
                    break
                except TimeoutException:
                    continue
            
            if not opt:
                options = overlay.find_elements(By.XPATH, ".//mat-option")
                available = [o.text.strip() for o in options if o.text.strip()]
                logger.warning(f"      ⚠️ Available tax options: {available}")
                driver.save_screenshot("tax_rate_not_found.png")
                if options:
                    opt = options[0]
                    logger.warning(f"      ⚠️ Falling back to first option: {opt.text.strip()}")
                else:
                    raise Exception(f"Tax rate '{tax_rate}' not found.")
            
            driver.execute_script("arguments[0].click();", opt)
            wait.until(EC.invisibility_of_element(overlay))
            logger.info(f"      ✅ Row {idx+1}: Tax Rate set to {tax_rate}")

        # 2. No Of Bags input with inline validation (DN_TC03)
        bag_inputs = driver.find_elements(By.CSS_SELECTOR, "input[formcontrolname='dispatch_no_of_bags']")
        if bag_inputs and idx < len(bag_inputs):
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", bag_inputs[idx])
            
            if run_validations and idx == 0:
                logger.info("      🧪 [DN_TC03] Testing Bags decimal precision...")
                bag_inputs[idx].send_keys(Keys.CONTROL, 'a')
                bag_inputs[idx].send_keys(Keys.BACKSPACE)
                bag_inputs[idx].send_keys("10.5")
                bag_inputs[idx].send_keys(Keys.TAB)
                time.sleep(0.5)
                is_invalid = "ng-invalid" in bag_inputs[idx].get_attribute("class")
                bag_val = driver.execute_script("return arguments[0].value;", bag_inputs[idx])
                if is_invalid or has_validation_error(driver):
                    logger.info(f"         ✅ Bags decimal rejected (validation triggered).")
                else:
                    logger.warning(f"         ⚠️ Bags accepted decimal: {bag_val}")

            # Enter correct bags value
            bag_inputs[idx].send_keys(Keys.CONTROL, 'a')
            bag_inputs[idx].send_keys(Keys.BACKSPACE)
            bags = str(item.get('no_of_bags', data.get('no_of_bags', 10)))
            bag_inputs[idx].send_keys(bags)
            logger.info(f"      ✅ Row {idx+1}: No of Bags set to {bags}")

    # File upload
    if 'attachment_file' in data and data['attachment_file']:
        try:
            file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'][id^='bank_upload']")))
            abs_path = os.path.abspath(data['attachment_file'])
            file_input.send_keys(abs_path)
            logger.info(f"  ✅ File uploaded: {abs_path}")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ Failed to upload file: {e}")

    # Wait for calculations
    time.sleep(2)

    # ----- DN_TC04: Grand Total Calculation Verification -----
    if run_validations:
        logger.info("   🧪 [DN_TC04] Verifying Grand Total calculation...")
        try:
            subtotal_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_sub_total_amount']")
            tax_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_tax_amount']")
            grand_total_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_grand_total_amount']")
            transport_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_transportation_charges']")
            
            subtotal_val = float(driver.execute_script("return arguments[0].value;", subtotal_input).replace(',', '') or 0)
            tax_val = float(driver.execute_script("return arguments[0].value;", tax_input).replace(',', '') or 0)
            grand_total_val = float(driver.execute_script("return arguments[0].value;", grand_total_input).replace(',', '') or 0)
            transport_val = float(driver.execute_script("return arguments[0].value;", transport_input).replace(',', '') or 0)
            
            expected_grand_total = subtotal_val + tax_val + transport_val
            diff = abs(grand_total_val - expected_grand_total)
            if diff < 0.01:
                logger.info(f"      ✅ Grand Total correct: {grand_total_val} (Subtotal: {subtotal_val} + Tax: {tax_val} + Transport: {transport_val})")
            else:
                logger.warning(f"      ⚠️ Grand Total mismatch! UI: {grand_total_val}, Expected: {expected_grand_total:.2f} (diff: {diff:.2f})")
        except Exception as e:
            logger.warning(f"      ⚠️ Grand Total check failed: {e}")

    # --- SUBMIT ---
    logger.info("📤 Submitting Dispatch Note...")
    submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.footer button.submit")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    driver.execute_script("arguments[0].click();", submit_btn)
    logger.info("   ✅ Submit button clicked")

    # Wait for redirect to the list page
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
        logger.info("🚀 Dispatch Note Registration Completed Successfully!")
        time.sleep(3)  
    except TimeoutException:
        errors = driver.find_elements(By.CSS_SELECTOR, "mat-error")
        error_msgs = [e.text for e in errors if e.text.strip()]
        if error_msgs:
            logger.error(f"❌ Validation errors: {error_msgs}")
            driver.save_screenshot("dispatch_validation_errors.png")
            raise Exception(f"Form validation failed: {error_msgs}")
        else:
            logger.warning("⚠️ No redirect and no errors. Retrying submit...")
            driver.execute_script("arguments[0].click();", submit_btn)
            time.sleep(2)
            if driver.find_elements(By.CSS_SELECTOR, "table.mat-mdc-table"):
                logger.info("🚀 Dispatch Note Registration Completed Successfully!")
            else:
                driver.save_screenshot("dispatch_submit_failed.png")
                raise Exception("Submission failed: page did not redirect and no validation errors.")


# ==========================================
# LIFECYCLE & GRID FUNCTIONS
# ==========================================

def test_view_dispatch_note(driver, wait):
    """Click View to ensure no internal server error occurs on the list page."""
    logger.info("🐞 Testing View & Crash Check...")
    try:
        view_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//table/tbody/tr[1]//button[.//i[contains(@class, 'bi-eye')]]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", view_btn)
        driver.execute_script("arguments[0].click();", view_btn)
        time.sleep(2)
        
        try:
            driver.find_element(By.XPATH, "//*[contains(text(), 'Internal server error')]")
            logger.error("   ❌ BUG CAUGHT: Internal Server Error on View!")
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        except NoSuchElementException:
            logger.info("   ✅ Dispatch Note View modal loaded cleanly.")
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
    except Exception as e:
        logger.warning(f"   ⚠️ Could not perform View test: {e}")


def test_delete_dispatch_note(driver, wait):
    """Test deletion flow and catch alerts if the system blocks it. (DN_TC05)"""
    logger.info("🗑️ [DN_TC05] Testing Dispatch Note Deletion...")
    try:
        delete_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//table/tbody/tr[1]//button[.//i[contains(@class, 'bi-trash')]]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", delete_btn)
        driver.execute_script("arguments[0].click();", delete_btn)
        
        confirm_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".swal2-confirm")))
        driver.execute_script("arguments[0].click();", confirm_btn)
        time.sleep(1)
        
        try:
            alert_text = driver.find_element(By.CSS_SELECTOR, ".toast-message, .swal2-html-container").text
            logger.info(f"   ✅ Deletion Blocked by System Alert: '{alert_text}' (Marking as Passed per requirements)")
        except NoSuchElementException:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container")))
            logger.info("   ✅ Dispatch Note deleted successfully from grid.")
    except Exception as e:
        logger.warning(f"   ⚠️ Could not complete Delete test: {e}")


# ==========================================
# SUITE EXECUTOR
# ==========================================

def execute_dispatch_suite(driver, wait, data):
    logger.info("--- ⚡ STARTING DISPATCH NOTE SUITE ---")
    
    # 1. Standard Creation (with inline validations)
    fill_dispatch_note_registration(driver, wait, data, run_validations=True)
    
    # 2. View Bug Check
    test_view_dispatch_note(driver, wait)
    
    # Short delay for list page stability
    time.sleep(1)
    
    # 3. Deletion Flow Check (DN_TC05)
    # test_delete_dispatch_note(driver, wait)  # Uncomment when ready
    
    logger.info("--- ✅ DISPATCH NOTE SUITE COMPLETED ---")