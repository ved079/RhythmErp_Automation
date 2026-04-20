from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
from decimal import Decimal, ROUND_HALF_UP
import logging
from common.helper import select_dropdown

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

def fill_lot_creation(driver, wait, data):
    logger.info("⚡ Starting Lot Creation Process...")

    # Grab the array of items, fallback to a single item if array isn't provided
    items = data.get('items', [])
    if not items:
        items = [{'item_name': data.get('item_name'), 'quantity': data.get('so_quantity')}]

    for idx, item in enumerate(items):
        item_name = item.get('item_name', 'Unknown Item')
        logger.info(f"\n📦 --- Processing Lot for Item {idx + 1}: {item_name} ---")

        # If it's not the first item, we are on the List Page and need to open the Form again
        if idx > 0:
            logger.info("   🔄 Navigating back to the Create Lot form...")
            try:
                # ⚠️ IMPORTANT: Adjust this XPATH to match the "Add" or "Create" button on your Lot List page
                add_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(translate(., 'ADD', 'add'), 'add') or contains(translate(., 'CREATE', 'create'), 'create')]")
                ))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
                driver.execute_script("arguments[0].click();", add_btn)
                time.sleep(2) # Wait for the form to render
            except Exception as e:
                logger.error(f"   ❌ Could not find the button to start the next lot: {e}")
                driver.save_screenshot(f"lot_add_button_error_{idx}.png")
                raise

        # ----- 1. CUSTOMER (searchable) -----
        select_dropdown(driver, wait, value=data['customer_name'], control_name="customer_ref_id", searchable=True)
        time.sleep(1)

        # ----- 2. SALES ORDER NUMBER (pick the first/latest) -----
        try:
            so_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select[formcontrolname='so_ref_id']")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", so_dropdown)
            driver.execute_script("arguments[0].click();", so_dropdown)
            logger.info("   Opened Sales Order Number dropdown")

            overlay = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
            first_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//mat-option[1]//span")))
            driver.execute_script("arguments[0].click();", first_option)
            logger.info("   Selected first Sales Order Number")
            wait.until(EC.invisibility_of_element(overlay))
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"❌ Failed to select Sales Order Number: {e}")
            driver.save_screenshot("so_number_error.png")
            raise

        # ----- 3. COMMODITY NAME (Select the specific item) -----
        try:
            commodity_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select[formcontrolname='item_ref_id']")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", commodity_dropdown)
            driver.execute_script("arguments[0].click();", commodity_dropdown)
            logger.info("   Opened Commodity Name dropdown")

            overlay = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))

            if 'item_name' in item and item['item_name']:
                # Target the exact commodity from our array
                target_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-option[contains(normalize-space(.), '{item['item_name']}')]")))
            else:
                target_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//mat-option[1]//span")))
                
            driver.execute_script("arguments[0].click();", target_option)
            logger.info(f"   ✅ Selected Commodity Name: {item.get('item_name', 'First Option')}")
            wait.until(EC.invisibility_of_element(overlay))
            
            # Crucial: Wait a moment for the table to fetch the lots for this specific commodity
            time.sleep(1.5) 
        except Exception as e:
            logger.error(f"❌ Failed to select Commodity Name: {e}")
            driver.save_screenshot("commodity_error.png")
            raise

        # ----- 4. WAIT FOR TABLE TO LOAD -----
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody.main_tbody tr")))

        # Get quantity specifically from the current item in the loop
        raw_qty = item.get('quantity', item.get('so_quantity', 0))
        required_qty = Decimal(str(raw_qty)).quantize(Decimal('0.001'))
        logger.info(f"   Required Sales Order Quantity: {required_qty} MT")

        # ----- 5. COLLECT ALL ROWS WITH THEIR AVAILABLE QUANTITIES -----
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody.main_tbody tr")
        logger.info(f"   Found {len(rows)} rows in the lot table.")
        rows_data = []  

        for r_idx, row in enumerate(rows):
            try:
                qty_cell = row.find_elements(By.TAG_NAME, "td")[3]
                qty_text = driver.execute_script("return arguments[0].textContent;", qty_cell).strip().replace(',', '')
                available_qty = Decimal(qty_text).quantize(Decimal('0.001'))
                rows_data.append((r_idx, available_qty))
            except Exception as e:
                continue

        if not rows_data:
            raise Exception("No rows with valid quantity found.")

        # ----- 6. DECIDE WHICH ROWS TO USE -----
        allocations = []  

        single_row_found = None
        for r_idx, available in rows_data:
            if available >= required_qty:
                single_row_found = (r_idx, required_qty)
                logger.info(f"   ✅ Found a single row (Row {r_idx+1}) with {available} MT >= required {required_qty} MT")
                break

        if single_row_found:
            allocations.append(single_row_found)
        else:
            accumulated = Decimal('0')
            for r_idx, available in rows_data:
                if accumulated >= required_qty:
                    break
                if available > 0:
                    remaining = required_qty - accumulated
                    take_qty = min(available, remaining)
                    allocations.append((r_idx, take_qty))
                    accumulated += take_qty
                    logger.info(f"      Taking {take_qty} MT from Row {r_idx+1}. Total accumulated: {accumulated} MT")

            if accumulated < required_qty - Decimal('0.001'):
                driver.save_screenshot("lot_insufficient_quantity.png")
                raise Exception(f"Insufficient total purchase quantity. Required: {required_qty} MT, Available: {accumulated} MT")

        time.sleep(1)
        
        # ----- 7. PROCESS SELECTED ROWS (checkboxes + allocation) -----
        for row_idx, alloc_qty in allocations:
            current_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody.main_tbody tr")
            if row_idx >= len(current_rows):
                raise Exception(f"Row index {row_idx} out of range after DOM refresh")
                
            row = current_rows[row_idx]

            checkbox = row.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)
            driver.execute_script("arguments[0].click();", checkbox)
            logger.info(f"   ✅ Checkbox selected for Row {row_idx+1}")

            try:
                confirm_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".swal2-confirm")))
                driver.execute_script("arguments[0].click();", confirm_btn)
                time.sleep(0.5)
            except: pass  
            
            time.sleep(1.5)
            
            alloc_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='allocated_qty']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", alloc_input)
            driver.execute_script("arguments[0].click();", alloc_input)
            
            alloc_input.send_keys(Keys.CONTROL + "a", Keys.BACKSPACE)
            alloc_str = f"{alloc_qty:.3f}".rstrip('0').rstrip('.') if '.' in f"{alloc_qty:.3f}" else f"{alloc_qty:.0f}"
            alloc_input.send_keys(alloc_str)
            time.sleep(1) 
            
            body = driver.find_element(By.TAG_NAME, "body")
            ActionChains(driver).move_to_element_with_offset(body, 10, 10).click().perform()
            logger.info(f"   ✅ Allocation Quantity set to {alloc_str} MT")
            time.sleep(1)

        # ----- 8. SUBMIT -----
        logger.info("📤 Submitting Lot Creation...")
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.footer button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)

        # Wait for redirect to the list page before looping back
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
        logger.info(f"🚀 Lot Creation for {item_name} Completed Successfully!")
        time.sleep(2)

    logger.info("🏁 All Lot Creations completed successfully!")