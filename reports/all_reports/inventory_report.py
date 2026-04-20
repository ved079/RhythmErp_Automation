from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

def go_to_inventory_summary(driver, wait):
    """Navigate to Reports → Inventory Summary."""
    print("Navigating to Inventory Summary...")
    
    # 1. KILL THE OVERLAY: Wait for the Purchase Booking success message/shield to disappear
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-container, .swal2-container, .ngx-spinner-overlay")))
        print("   ✅ Success overlays cleared.")
    except:
        pass # If it times out, we will force the click anyway

    # 2. SCROLL TO TOP: Ensure the sidebar isn't cut off at the bottom of the page
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # 3. FORCE CLICK: Use the exact HTML locators you found, powered by a JavaScript click
    try:
        # Looking for your exact href or the "All Reports" span
        xpath = "//a[contains(@href, 'rhythm-report/reports')] | //span[contains(text(), 'All Reports')]/ancestor::a"
        reports_menu = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", reports_menu)
        driver.execute_script("arguments[0].click();", reports_menu) # JS Click ignores all overlays!
        print("   ✅ Clicked All Reports menu")
        
    except Exception as e:
        driver.save_screenshot("reports_menu_not_found.png")
        print(f"❌ Could not find Reports menu: {e}")
        raise

    time.sleep(2)
    
    # 4. CONFIRM ARRIVAL: Wait for the report name dropdown you identified
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-select[formcontrolname='report_name']")))
    print("✅ Inventory Summary page loaded.")


def select_report_name(driver, wait, report_name="Inventory Report"):
    """Select the report name from the first dropdown."""
    try:
        dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select[formcontrolname='report_name']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        driver.execute_script("arguments[0].click();", dropdown)
        print("   ✅ Opened report name dropdown")

        overlay = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")
        ))
        wait.until(EC.visibility_of(overlay))

        option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-option//span[contains(text(), '{report_name}')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
        driver.execute_script("arguments[0].click();", option)
        print(f"   ✅ Selected report: {report_name}")
        time.sleep(0.5)
    except Exception as e:
        print(f"❌ Failed to select report name: {e}")
        driver.save_screenshot("report_name_error.png")
        raise

def select_filter_by_id(driver, wait, element_id, value):
    """Select a dropdown by its ID (e.g., item_ref_id)."""
    try:
        dropdown = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        driver.execute_script("arguments[0].click();", dropdown)
        print(f"   ✅ Opened {element_id}")

        overlay = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")
        ))
        wait.until(EC.visibility_of(overlay))

        option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-option//span[contains(text(), '{value}')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
        driver.execute_script("arguments[0].click();", option)
        print(f"   ✅ Selected {element_id}: {value}")
        time.sleep(0.5)
    except Exception as e:
        print(f"❌ Failed to select {element_id}: {e}")
        driver.save_screenshot(f"filter_{element_id}_error.png")
        raise

def click_view_button(driver, wait):
    """Click the View button."""
    try:
        view_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'View')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", view_btn)
        driver.execute_script("arguments[0].click();", view_btn)
        print("   ✅ View button clicked")
        time.sleep(3)  # Wait for the table to load
    except Exception as e:
        print(f"❌ Failed to click View: {e}")
        driver.save_screenshot("view_button_error.png")
        raise

def expand_first_row(driver, wait):
    """Click the expand icon of the first row using JS to bypass overlays."""
    try:
        # Look for the span, the italic icon, or the IDE exact selector in the first row
        xpath = "//tbody/tr[1]/td[contains(@class, 'td_col')][1]//span | //tbody/tr[1]/td[contains(@class, 'td_col')][1]//i"
        
        try:
            expand_element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        except:
            print("   ⚠️ Primary locator failed, falling back to IDE locator...")
            expand_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr:nth-child(1) > .td_col:nth-child(2) span, tr:nth-child(1) > .td_col:nth-child(2) i")))

        # Scroll to ensure it is in the viewport
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", expand_element)
        time.sleep(1)
        
        # Force the click using Javascript to bypass any invisible barriers
        driver.execute_script("arguments[0].click();", expand_element)
        print("   ✅ Expanded first row (via JS)")
        
        # Give the child table 3 full seconds to fetch its data and render
        time.sleep(3) 
        
    except Exception as e:
        print(f"❌ Failed to expand row: {e}")
        driver.save_screenshot("expand_row_error.png")
        raise

def get_last_purchase_row(driver, wait):
    """Return the last row in the nested child table."""
    try:
        child_table = wait.until(EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'table-sm')]//tbody")))
        rows = child_table.find_elements(By.XPATH, "./tr")
        
        purchase_rows = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            # Verify it's a valid data row and Transaction Type (Index 4) is "Purchase"
            if len(cells) > 4 and "Purchase" in cells[4].text:
                purchase_rows.append(row)
                
        if not purchase_rows:
            raise Exception("No purchase rows found in the nested table.")
            
        last_row = purchase_rows[-1]  
        print("   ✅ Found last purchase row.")
        return last_row
        
    except Exception as e:
        print(f"❌ Failed to get last purchase row: {e}")
        driver.save_screenshot("last_purchase_row_error.png")
        raise

def verify_purchase_row(row, expected_qty_kg, expected_amount):
    """Verify the quantity and amount in the purchase row."""
    try:
        cells = row.find_elements(By.TAG_NAME, "td")
        
        # Inward Qty(KG) is index 6, Inward Amount is index 8
        qty_kg_text = cells[6].text.strip().replace(',', '')
        qty_kg = float(qty_kg_text)
        amount_text = cells[8].text.strip().replace(',', '')
        amount = float(amount_text)

        assert abs(qty_kg - expected_qty_kg) < 0.01, f"Quantity mismatch: expected {expected_qty_kg} KG, got {qty_kg}"
        assert abs(amount - expected_amount) < 0.01, f"Amount mismatch: expected {expected_amount}, got {amount}"
        print(f"   🏆 Verified: Quantity = {qty_kg} KG, Amount = {amount}")
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        driver.save_screenshot("verify_purchase_error.png")
        raise

def download_excel(driver, wait):
    """Select the file format and click the Download button to export."""
    try:
        print("   🔍 Looking for File Format dropdown...")
        
        # 1. Open the File Format dropdown using PRESENCE, not CLICKABLE
        try:
            dropdown = wait.until(EC.presence_of_element_located((By.ID, "file_format")))
        except:
            # Fallback: Look for the dropdown right next to the "File Format" label
            xpath = "//mat-label[contains(text(), 'File Format')]/ancestor::div[1]//mat-select | //mat-select[@id='file_format']"
            dropdown = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        time.sleep(1) # Let scroll settle
        driver.execute_script("arguments[0].click();", dropdown) # Force JS Click
        print("   ✅ Opened File Format dropdown")

        # Wait for the dropdown overlay to appear
        overlay = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")
        ))
        wait.until(EC.visibility_of(overlay))

        # 2. Select "Excel" (Using a case-insensitive XPath just to be completely safe)
        option_xpath = "//mat-option//span[contains(translate(text(), 'EXCEL', 'excel'), 'excel')]"
        option = wait.until(EC.presence_of_element_located((By.XPATH, option_xpath)))
        
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
        driver.execute_script("arguments[0].click();", option)
        print("   ✅ Selected format: EXCEL")
        time.sleep(1) # Give Angular a second to register the selection

        # 3. Click the Download button
        download_xpath = "//button[contains(normalize-space(), 'Download')] | //button[contains(@class, 'apply') and contains(text(), 'Download')]"
        download_btn = wait.until(EC.presence_of_element_located((By.XPATH, download_xpath)))
        
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", download_btn)
        driver.execute_script("arguments[0].click();", download_btn)
        print("   ✅ Download button clicked")
        
        # Give the browser time to actually process and download the file
        time.sleep(4) 
        
    except Exception as e:
        print(f"❌ Failed to download Excel: {e}")
        driver.save_screenshot("download_button_error.png")
        raise

def verify_inventory_after_purchase(driver, wait, purchase_data):
    """
    Full flow: go to Inventory Report, loop through ALL purchased items, 
    apply filters, view, expand row, and verify.
    """
    print("⚡ Running Inventory Report verification for multiple items...")

    # 1. Select report name
    select_report_name(driver, wait, "Inventory Report") 

    # 2. LOOP through the upgraded items list!
    for item_data in purchase_data['items']:
        print(f"\n--- Verifying Inventory for: {item_data['item']} ---")
        
        # Apply filters for this specific item
        select_filter_by_id(driver, wait, "item_ref_id", item_data['item'])
        
        # Note: You'll need to pass division/department/etc. into this function 
        # or grab them from your other shared variables, as they aren't in your new item_data dict.
        select_filter_by_id(driver, wait, "division_ref_id", "HR") 
        select_filter_by_id(driver, wait, "department_ref_id", "Businesss Division")
        select_filter_by_id(driver, wait, "sale_type_ref_id", "B2B")
        select_filter_by_id(driver, wait, "location_ref_id", "London")

        # Click View
        click_view_button(driver, wait)

        # Expand the row 
        expand_first_row(driver, wait)

        # Get last purchase row from the nested table
        last_row = get_last_purchase_row(driver, wait)

        # Verify quantity 
        # NOTE: I removed expected_amount because your gen_multiple_items() function 
        # does not generate a 'total_amount' yet! You will need to add that if you want to verify it.
        verify_purchase_row(last_row, item_data['quantity'], expected_amount=0.0) 

    # Download Excel once at the end
    download_excel(driver, wait)

    print("✅ E2E Inventory Report verification and download completed.")