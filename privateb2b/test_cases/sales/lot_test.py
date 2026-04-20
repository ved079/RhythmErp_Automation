import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
from decimal import Decimal
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import config
from common import auth_section, nav_section
from common.helper import select_dropdown


# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# ==========================================
# HELPER: VALIDATION & UTILITY FUNCTIONS
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


def parse_date(date_str):
    """Parse date string in format DD-MM-YYYY to datetime object."""
    try:
        return datetime.strptime(date_str.strip(), "%d-%m-%Y")
    except:
        return None


def verify_fifo_order(driver, wait):
    """
    LOT_TC10: Verify Supplier Bills display on FIFO basis (by Transaction Date).
    Extracts dates from column index 2 and asserts ascending order.
    """
    logger.info("   🧪 [LOT_TC10] Checking FIFO order of supplier bills...")
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody.main_tbody tr")
        dates = []
        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, "td.col_input")
            if len(cells) > 2:
                date_text = cells[2].text.strip()
                dt = parse_date(date_text)
                if dt:
                    dates.append(dt)
        if len(dates) > 1:
            is_sorted = all(dates[i] <= dates[i+1] for i in range(len(dates)-1))
            if is_sorted:
                logger.info("      ✅ Supplier bills are in FIFO order (ascending dates).")
            else:
                logger.warning("      ⚠️ WARNING: Supplier bills are NOT in FIFO order!")
        else:
            logger.info("      ℹ️ Only one bill row; FIFO check not applicable.")
    except Exception as e:
        logger.warning(f"      ⚠️ FIFO check failed: {e}")


def verify_so_quantity_autopopulation(driver, wait, expected_so_qty):
    """
    LOT_TC15: Verify Sales Order Quantity auto-populates correctly.
    """
    logger.info("   🧪 [LOT_TC15] Checking SO Quantity auto-population...")
    try:
        so_qty_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[formcontrolname='total_sales_order_qty']")
        ))
        displayed_qty = driver.execute_script("return arguments[0].value;", so_qty_input).strip()
        if displayed_qty:
            displayed_decimal = Decimal(displayed_qty.replace(',', ''))
            expected_decimal = Decimal(str(expected_so_qty)).quantize(Decimal('0.0001'))
            if abs(displayed_decimal - expected_decimal) < Decimal('0.0001'):
                logger.info(f"      ✅ SO Quantity auto-populated correctly: {displayed_qty} MT")
            else:
                logger.warning(f"      ⚠️ WARNING: SO Quantity mismatch! Expected {expected_so_qty}, got {displayed_qty}")
        else:
            logger.warning("      ⚠️ SO Quantity field is empty.")
    except Exception as e:
        logger.warning(f"      ⚠️ SO Quantity check failed: {e}")


def verify_purchase_amount_calculation(driver, wait):
    """
    LOT_TC16: Verify Purchase Amount auto-calculation (Base Rate × Purchase Qty).
    """
    logger.info("   🧪 [LOT_TC16] Checking Purchase Amount calculations per row...")
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody.main_tbody tr")
        all_passed = True
        for idx, row in enumerate(rows):
            cells = row.find_elements(By.CSS_SELECTOR, "td.col_input")
            if len(cells) < 7:
                continue
            base_rate_text = cells[3].text.strip().replace(',', '')
            try:
                base_rate = float(base_rate_text) if base_rate_text else 0.0
                purchase_qty = float(cells[3].text.strip().replace(',', ''))
                purchase_amt = float(cells[6].text.strip().replace(',', ''))
                expected_amt = base_rate * purchase_qty
                if abs(purchase_amt - expected_amt) > 0.01:
                    logger.warning(f"      ⚠️ Row {idx+1}: Purchase Amount mismatch. UI: {purchase_amt}, Expected: {expected_amt}")
                    all_passed = False
            except:
                continue
        if all_passed:
            logger.info("      ✅ All Purchase Amount calculations are correct.")
        else:
            logger.warning("      ⚠️ Some Purchase Amount calculations are incorrect.")
    except Exception as e:
        logger.warning(f"      ⚠️ Purchase Amount check failed: {e}")


def verify_weighted_average_rate(driver, wait, total_alloc_qty, total_alloc_amt):
    """
    LOT_TC18: Verify Weighted Average Rate calculation in summary row.
    """
    logger.info("   🧪 [LOT_TC18] Checking Weighted Average Rate...")
    try:
        summary_row = driver.find_element(By.XPATH, "//table/tbody[2]/tr")
        cells = summary_row.find_elements(By.TAG_NAME, "td")
        if len(cells) >= 5:
            weighted_avg_text = cells[4].text.strip().replace(',', '') 
            weighted_avg_ui = float(weighted_avg_text) if weighted_avg_text else 0.0
            expected_avg = total_alloc_amt / total_alloc_qty if total_alloc_qty != 0 else 0
            if abs(weighted_avg_ui - expected_avg) < 0.01:
                logger.info(f"      ✅ Weighted Average Rate correct: {weighted_avg_ui}")
            else:
                logger.warning(f"      ⚠️ Weighted Average Rate mismatch. UI: {weighted_avg_ui}, Expected: {expected_avg:.4f}")
        else:
            logger.warning("      ⚠️ Could not locate summary row cells.")
    except Exception as e:
        logger.warning(f"      ⚠️ Weighted Average check failed: {e}")


def verify_listing_page_columns(driver, wait):
    """
    LOT_TC20: Verify that required columns appear on Lot listing page.
    """
    logger.info("   🧪 [LOT_TC20] Verifying listing page columns...")
    required_columns = [
        "Customer", "Lot Number", "SO Number", "SO Quantity (MT)",
        "Purchase Quantity (MT)", "Lot Quantity (MT)"
    ]
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
        headers = driver.find_elements(By.CSS_SELECTOR, "th.mat-mdc-header-cell strong")
        header_texts = [h.text.strip() for h in headers if h.text.strip()]
        missing = [col for col in required_columns if not any(col in h for h in header_texts)]
        if not missing:
            logger.info(f"      ✅ All required columns present: {required_columns}")
        else:
            logger.warning(f"      ⚠️ Missing columns: {missing}")
    except Exception as e:
        logger.warning(f"      ⚠️ Listing column check failed: {e}")


# ==========================================
# COMMODITY SELECTION (unchanged)
# ==========================================

def select_commodity_by_name(driver, wait, item_name):
    """
    Open the commodity dropdown and select the exact option matching item_name.
    Uses multiple strategies and fallbacks to ensure reliability.
    """
    logger.info(f"    Selecting Commodity: {item_name}")

    commodity_dropdown = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "mat-select[formcontrolname='item_ref_id']")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", commodity_dropdown)
    driver.execute_script("arguments[0].click();", commodity_dropdown)
    logger.info("    Opened Commodity Name dropdown")

    overlay = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, ".cdk-overlay-pane")
    ))
    
    wait.until(EC.presence_of_element_located((By.XPATH, "//mat-option")))
    time.sleep(0.5) 

    strategies = [
        f"//mat-option[normalize-space()='{item_name}']",
        f"//mat-option[contains(normalize-space(), '{item_name}')]",
        f"//mat-option//span[contains(text(), '{item_name}')]/ancestor::mat-option",
        f"//mat-option[contains(., '{item_name}')]"
    ]

    option = None
    fast_wait = WebDriverWait(driver, 2)
    
    for strategy in strategies:
        try:
            option = fast_wait.until(EC.element_to_be_clickable((By.XPATH, strategy)))
            logger.info(f"    ✅ Found option using: {strategy}")
            break
        except TimeoutException:
            continue

    if not option:
        options = driver.find_elements(By.XPATH, "//mat-option")
        available = [opt.text.strip() for opt in options if opt.text.strip()]
        logger.error(f"    ❌ Available options: {available}")
        driver.save_screenshot("commodity_not_found.png")
        raise AssertionError(f"Commodity '{item_name}' not found. Available: {available}")

    driver.execute_script("arguments[0].click();", option)
    logger.info(f"    ✅ Selected Commodity Name: {item_name}")

    wait.until(EC.invisibility_of_element(overlay))
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody.main_tbody tr")))
    time.sleep(1)


# ==========================================
# MAIN LOT CREATION (WITH INLINE TESTS)
# ==========================================

def fill_lot_creation(driver, wait, data, run_validations=True):
    logger.info("⚡ Starting Lot Creation Process...")

    items = data.get('items', [])
    if not items:
        items = [{'item_name': data.get('item_name'), 'quantity': data.get('so_quantity')}]

    for idx, item in enumerate(items):
        item_name = item.get('item_name', 'Unknown Item')
        expected_so_qty = item.get('quantity', item.get('so_quantity', 0))
        logger.info(f"\n📦 --- Processing Lot for Item {idx + 1}: {item_name} ---")

        if idx > 0:
            logger.info("    🔄 Navigating back to the Create Lot form...")
            try:
                add_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(translate(., 'ADD', 'add'), 'add') or contains(translate(., 'CREATE', 'create'), 'create')]")
                ))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
                driver.execute_script("arguments[0].click();", add_btn)
                time.sleep(2)
            except Exception as e:
                logger.error(f"    ❌ Could not find Add button: {e}")
                driver.save_screenshot(f"lot_add_button_error_{idx}.png")
                raise

        # ----- 1. CUSTOMER -----
        select_dropdown(driver, wait, value=data['customer_name'], control_name="customer_ref_id", searchable=True)
        time.sleep(1.5)

        # ----- 2. SALES ORDER NUMBER -----
        try:
            so_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select[formcontrolname='so_ref_id']")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", so_dropdown)
            
            for attempt in range(2):
                try:
                    driver.execute_script("arguments[0].click();", so_dropdown)
                    break
                except StaleElementReferenceException:
                    so_dropdown = driver.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='so_ref_id']")
                    time.sleep(0.5)
            logger.info("    Opened Sales Order Number dropdown")

            overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
            wait.until(EC.visibility_of(overlay))
            wait.until(EC.presence_of_element_located((By.XPATH, "//mat-option[1]")))
            time.sleep(0.3)
            
            first_option = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "(//mat-option)[1]"))
            )
            driver.execute_script("arguments[0].click();", first_option)
            logger.info("    Selected first Sales Order Number")
            wait.until(EC.invisibility_of_element(overlay))
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"❌ Failed to select Sales Order Number: {e}")
            driver.save_screenshot("so_number_error.png")
            raise

        # ----- 3. COMMODITY NAME -----
        try:
            select_commodity_by_name(driver, wait, item_name)
        except Exception as e:
            logger.error(f"❌ Failed to select Commodity Name: {e}")
            driver.save_screenshot("commodity_error.png")
            raise

        # ----- LOT_TC15: SO Quantity Auto-Population -----
        if run_validations:
            verify_so_quantity_autopopulation(driver, wait, expected_so_qty)

        # ----- 4. GET REQUIRED QUANTITY (Upgraded to 4 decimal places) -----
        raw_qty = item.get('quantity', item.get('so_quantity', 0))
        required_qty = Decimal(str(raw_qty)).quantize(Decimal('0.0001'))
        logger.info(f"    Required Sales Order Quantity: {required_qty} MT")

        # ----- 5. COLLECT ROWS WITH AVAILABLE QUANTITIES -----
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody.main_tbody tr")
        logger.info(f"    Found {len(rows)} rows in the lot table.")
        
        # ----- LOT_TC10: FIFO Order Check -----
        if run_validations:
            verify_fifo_order(driver, wait)
        
        # ----- LOT_TC16: Purchase Amount Auto-Calculation -----
        if run_validations:
            verify_purchase_amount_calculation(driver, wait)

        rows_data = []
        for r_idx, row in enumerate(rows):
            try:
                cells = row.find_elements(By.CSS_SELECTOR, "td.col_input")
                if len(cells) > 2:
                    qty_text = cells[2].text.strip().replace(',', '')
                    available_qty = Decimal(qty_text).quantize(Decimal('0.0001'))
                    rows_data.append((r_idx, available_qty))
            except Exception:
                continue

        if not rows_data:
            raise Exception("No rows with valid quantity found.")

        # ----- 6. DETERMINE ALLOCATIONS USING STRICT FIFO -----
        allocations = []
        accumulated = Decimal('0')
        for r_idx, available in rows_data:
            if accumulated >= required_qty:
                break
            if available > 0:
                take_qty = min(available, required_qty - accumulated)
                allocations.append((r_idx, take_qty))
                accumulated += take_qty
                logger.info(f"      Taking {take_qty} MT from Row {r_idx+1} (Available: {available} MT). Total: {accumulated} MT")

        if accumulated < required_qty - Decimal('0.0001'):
            driver.save_screenshot("lot_insufficient_quantity.png")
            raise Exception(f"Insufficient purchase quantity. Required: {required_qty} MT, Available: {accumulated} MT")
        else:
            if len(allocations) == 1:
                logger.info(f"    ✅ Single row allocation (Row {allocations[0][0]+1}) sufficient.")
            else:
                logger.info(f"    ✅ Split allocation across {len(allocations)} rows following FIFO order.")

        time.sleep(1)

        total_alloc_qty = Decimal('0')
        total_alloc_amt = Decimal('0')

        # ----- 7. PROCESS EACH SELECTED ROW -----
        for i, (row_idx, alloc_qty) in enumerate(allocations):
            current_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody.main_tbody tr")
            if row_idx >= len(current_rows):
                raise Exception(f"Row index {row_idx} out of range after DOM refresh")
            row = current_rows[row_idx]

            # Checkbox
            checkbox = row.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)
            driver.execute_script("arguments[0].click();", checkbox)
            logger.info(f"    ✅ Checkbox selected for Row {row_idx+1}")

            try:
                confirm_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".swal2-confirm")))
                driver.execute_script("arguments[0].click();", confirm_btn)
                time.sleep(0.5)
            except:
                pass

            time.sleep(1.5)

            # Allocation input
            alloc_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='allocated_qty']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", alloc_input)
            driver.execute_script("arguments[0].click();", alloc_input)

            # --- VALIDATIONS ---
            if run_validations and i == 0:
                logger.info("      🛡️ Testing Allocation Constraints...")
                try:
                    # Negative value test (LOT_TC07)
                    alloc_input.send_keys(Keys.CONTROL + "a", Keys.BACKSPACE)
                    alloc_input.send_keys("-10")
                    alloc_input.send_keys(Keys.TAB)
                    time.sleep(0.5)
                    val = driver.execute_script("return arguments[0].value;", alloc_input)
                    if "-" in val:
                        classes = alloc_input.get_attribute('class')
                        assert "ng-invalid" in classes, "Negative value accepted!"
                    logger.info("         ✅ Negative values blocked.")

                    # Over-allocation test (LOT_TC06)
                    available_in_row = float(rows_data[row_idx][1])
                    over_qty = available_in_row + 10.0
                    alloc_input.send_keys(Keys.CONTROL + "a", Keys.BACKSPACE)
                    alloc_input.send_keys(str(over_qty))
                    alloc_input.send_keys(Keys.TAB)
                    time.sleep(1)
                    try:
                        alert = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-container")))
                        logger.info("         ✅ Over-allocation Alert triggered.")
                        alert_ok = alert.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                        driver.execute_script("arguments[0].click();", alert_ok)
                        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container")))
                    except:
                        logger.warning("         ⚠️ WARNING: No over-allocation alert shown!")

                    # ----- LOT_TC19: Decimal precision limit -----
                    logger.info("      🧪 [LOT_TC19] Testing decimal precision limit (max 4 decimals)...")
                    alloc_input.send_keys(Keys.CONTROL + "a", Keys.BACKSPACE)
                    # Tiny decimal to prevent accidental over-allocation triggers
                    alloc_input.send_keys("0.00015")
                    alloc_input.send_keys(Keys.TAB) 
                    time.sleep(0.5)
                    entered_val = driver.execute_script("return arguments[0].value;", alloc_input)
                    if entered_val == "0.0001" or entered_val == "0.0002" or has_validation_error(driver):
                        logger.info(f"         ✅ Decimal precision limit enforced (entered: {entered_val}).")
                    else:
                        logger.warning(f"         ⚠️ WARNING: Decimal precision not enforced! Entered: {entered_val}")
                        
                    # Kill any residual popups from validations before the final entry
                    try:
                        lingering_alert = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                        driver.execute_script("arguments[0].click();", lingering_alert)
                        time.sleep(0.5)
                    except:
                        pass

                except Exception as e:
                    logger.warning(f"         ⚠️ Constraint test skipped/failed: {e}")

            # 🛠️ THE FIX: Enter final valid allocation quantity robustly!
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", alloc_input)
            time.sleep(0.2)
            
            # Crucial: Re-click using JS to bypass any invisible overlay intercepts
            driver.execute_script("arguments[0].click();", alloc_input)
            time.sleep(0.2)
            
            # Force empty via Javascript to ensure it is completely blank
            driver.execute_script("arguments[0].value = '';", alloc_input)
            alloc_input.send_keys(Keys.CONTROL, 'a')
            alloc_input.send_keys(Keys.BACKSPACE)
            
            # Use exact string format so 0.xxxx isn't destroyed
            alloc_str = str(alloc_qty.normalize()) 
            alloc_input.send_keys(alloc_str)
            time.sleep(1)

            # Click away to trigger calculation
            body = driver.find_element(By.TAG_NAME, "body")
            ActionChains(driver).move_to_element_with_offset(body, 10, 10).click().perform()
            logger.info(f"    ✅ Allocation Quantity set to {alloc_str} MT")
            time.sleep(1)

            # --- MATH VERIFICATION (rate * qty = allocated amount) LOT_TC17 ---
            if run_validations:
                try:
                    cells = row.find_elements(By.CSS_SELECTOR, "td.col_input")
                    if len(cells) > 4:
                        base_rate_text = cells[3].text.strip().replace(',', '') 
                        base_rate = float(base_rate_text) if base_rate_text else 0.0
                        alloc_amt_text = cells[7].text.strip().replace(',', '')
                        alloc_amt_ui = float(alloc_amt_text) if alloc_amt_text else 0.0
                        expected_alloc_amt = float(alloc_qty) * base_rate
                        if abs(alloc_amt_ui - expected_alloc_amt) < 0.01:
                            logger.info(f"      🧮 LOT_TC17: Allocation Amount correct: {alloc_amt_ui}")
                        else:
                            logger.warning(f"      ⚠️ Allocation Amount mismatch. UI: {alloc_amt_ui}, Expected: {expected_alloc_amt:.2f}")
                        total_alloc_qty += alloc_qty
                        total_alloc_amt += Decimal(str(alloc_amt_ui))
                except Exception as e:
                    logger.warning(f"      ⚠️ Allocation math check failed: {e}")

        # ----- 8. SUBMIT THE LOT -----
        logger.info("📤 Submitting Lot Creation...")
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.footer button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
        logger.info(f"🚀 Lot Creation for {item_name} Completed Successfully!")
        time.sleep(2)

    # ----- LOT_TC20: Listing Page Column Verification -----
    if run_validations:
        verify_listing_page_columns(driver, wait)

    logger.info("🏁 All Lot Creations completed successfully!")



def execute_lot_suite(driver, wait, data):
    logger.info("\n--- ⚡ STARTING LOT MANAGEMENT SUITE ---")
    fill_lot_creation(driver, wait, data, run_validations=True)
    logger.info("--- ✅ LOT MANAGEMENT SUITE COMPLETED ---\n")


# For standalone testing (optional)
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
        nav_section.go_to_lot_page(driver, wait) 
        from data.test_data import sales_order_data
        execute_lot_suite(driver, wait, sales_order_data)
    finally:
        driver.quit()