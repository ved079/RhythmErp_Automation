from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException
import time
import os
import logging

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
from selenium.webdriver.common.action_chains import ActionChains

def select_dropdown(driver, wait, value, control_name=None, label_text=None, control_id=None):
    try:
        identifier = control_name or label_text or control_id or "unknown"
        logger.info(f"➡️ Selecting {identifier}: {value}")
        dropdown = None
        
        # 1. Locate the dropdown
        if control_name:
            dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"mat-select[formcontrolname='{control_name}']")))
        elif label_text:
            dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-label[contains(text(), '{label_text}')]/ancestor::mat-form-field//mat-select")))
        elif control_id:
            dropdown = wait.until(EC.element_to_be_clickable((By.ID, control_id)))
            
        if not dropdown:
            raise ValueError("No locator provided")

        # 2. Open the dropdown using JS (avoids click interception)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", dropdown)

        # 3. Wait for the specific Angular overlay pane to appear
        overlay_pane = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        time.sleep(0.5) # Let the opening animation finish

        # 4. DYNAMIC SEARCH DETECTION: If a search box exists, use it!
        search_inputs = overlay_pane.find_elements(By.XPATH, ".//input[contains(@placeholder, 'Search') or contains(@class, 'mat-filter-input')]")
        if search_inputs:
            logger.info(f"   🔍 Search box detected. Filtering by: '{value}'")
            search_input = search_inputs[0]
            search_input.clear()
            search_input.send_keys(value)
            time.sleep(1) # Wait for the list to filter

        # 5. Locate the Option (using normalize-space to ignore weird HTML formatting)
        option_xpath = f"//mat-option[contains(normalize-space(.), '{value}')]"
        
        # We use presence_of_element_located because Angular sometimes hides elements behind invisible backdrops
        option = wait.until(EC.presence_of_element_located((By.XPATH, option_xpath)))

        # 6. Force the click with JavaScript
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", option)
            
        logger.info(f"   ✅ Selected: {value}")
        
        # 7. Wait for the pane to close
        wait.until(EC.invisibility_of_element(overlay_pane))
        time.sleep(0.3)
        
    except Exception as e:
        logger.error(f"❌ Dropdown failed for {identifier}: {e}")
        # Send ESCAPE key to close the stuck dropdown so the script can try the next field
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
        raise

def fill_input(driver, wait, value, control_name=None, control_id=None):
    try:
        identifier = control_name or control_id
        logger.info(f"➡️ Typing in {identifier}: {value}")
        
        if control_name:
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"input[formcontrolname='{control_name}']")))
        elif control_id:
            element = wait.until(EC.presence_of_element_located((By.ID, control_id)))
            
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.2)
        
        driver.execute_script("arguments[0].click();", element)
        time.sleep(0.2)
        
        # Angular specific clear for dates
        driver.execute_script("arguments[0].value = '';", element) 
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.BACKSPACE)
        time.sleep(0.2)
        
        element.send_keys(str(value))
        time.sleep(0.2)
        element.send_keys(Keys.TAB) # Tab out to trigger Angular's form validation
        logger.info(f"   ✅ Filled {identifier}: {value}")
        
    except Exception as e:
        logger.error(f"❌ Failed to fill {identifier}: {e}")
        raise

def go_to_reports_page(driver, wait):
    logger.info("Navigating to Reports page...")
    try:
        # Check for multiple blocking overlays
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-container, .swal2-container, .ngx-spinner-overlay")))
        logger.info("   ✅ Success overlays cleared.")
    except:
        pass
        
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    
    try:
        xpath = "//a[contains(@href, 'rhythm-report/reports')] | //span[contains(text(), 'All Reports')]/ancestor::a"
        reports_menu = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", reports_menu)
        try:
            reports_menu.click()
        except:
            driver.execute_script("arguments[0].click();", reports_menu)
            
        logger.info("   ✅ Clicked All Reports menu")
    except Exception as e:
        driver.save_screenshot("reports_menu_not_found.png")
        logger.error(f"❌ Could not find Reports menu: {e}")
        raise
        
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-select[formcontrolname='report_name']")))
    logger.info("✅ Reports page loaded.")

def select_report_name(driver, wait, report_name="Sales Order Status"):
    logger.info(f"   🔽 Selecting Report Name: {report_name}...")
    try:
        dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select[formcontrolname='report_name']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        time.sleep(0.5)
        
        if report_name in dropdown.text:
            logger.info(f"      ✅ Report Name is already set to '{report_name}'")
            return True
            
        dropdown.click()
        overlay_pane = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        
        option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-option[contains(., '{report_name}')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
        time.sleep(0.2)
        option.click()
        
        logger.info(f"      ✅ Selected report: {report_name}")
        wait.until(EC.invisibility_of_element(overlay_pane))
        time.sleep(1)
        return True
    except Exception as e:
        logger.error(f"      ❌ Failed to select report name: {e}")
        driver.save_screenshot("select_report_name_error.png")
        return False

def fill_sales_order_status_form(driver, wait, data):
    logger.info("📝 Filling Sales Order Status form...")
    if not select_report_name(driver, wait, "Sales Order Status"):
        raise Exception("Failed to select report")

    time.sleep(2)

    fields = [
        ('customer_name', 'customer_id', 'dropdown', 'Customer Name', data.get('customer_name')),
        ('division', 'division_ref_id', 'dropdown', 'Division', data.get('division')),
        ('department', 'department_ref_id', 'dropdown', 'Department', data.get('department')),
        ('type_of_sale', 'sale_type_ref_id', 'dropdown', 'Type Of Sale', data.get('type_of_sale')),
        ('location', 'location_ref_id', 'dropdown', 'Location', data.get('location')),
        ('lot_status', 'lot_status', 'dropdown', 'Lot Status', data.get('lot_status')),
        ('dispatch_status', 'dispatch_status', 'dropdown', 'Dispatch Status', data.get('dispatch_status')),
        ('invoice_status', 'invoice_status', 'dropdown', 'Invoice Status', data.get('invoice_status')),
        ('receipt_status', 'receipt_status', 'dropdown', 'Receipt Status', data.get('receipt_status')),
        ('file_format', 'file_format', 'dropdown', 'File Format', data.get('file_format')),
        ('from_date', 'from_date', 'input', 'From Date', data.get('from_date')),
        ('to_date', 'to_date', 'input', 'To Date', data.get('to_date'))
    ]

    for key, elem_id, field_type, fallback_label, val in fields:
        if val:
            try:
                if field_type == 'dropdown':
                    # Notice we removed the searchable=False argument! 
                    # The function now handles it automatically.
                    try:
                        select_dropdown(driver, wait, value=val, control_id=elem_id)
                    except:
                        select_dropdown(driver, wait, value=val, label_text=fallback_label)
                        
                elif field_type == 'input':
                    fill_input(driver, wait, value=val, control_id=elem_id)
                    
            except Exception as e:
                # CRITICAL: This ensures if one field fails, it moves to the next one!
                logger.warning(f"   ⚠️ WARNING: Could not set field '{key}'. Skipping to next.")
                
            time.sleep(0.5)

    logger.info("✅ Form filling complete.")

    
def click_view(driver, wait):
    try:
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "mat-spinner, .ngx-spinner-overlay, .cdk-overlay-backdrop")))
        except:
            pass
        view_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'View')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", view_btn)
        driver.execute_script("arguments[0].click();", view_btn)
        logger.info("   ✅ View button clicked")
        logger.info("⏳ Waiting for report table to load...")
        time.sleep(5)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table, .report-container")))
        logger.info("✅ Report table loaded.")
    except Exception as e:
        logger.warning(f"⚠️ View clicked but table check failed: {e}")
        driver.save_screenshot("view_button_error.png")

def click_download(driver, wait):
    try:
        # 1. Set file format to Excel (if not already)
        try:
            file_format_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "file_format")))
            current_value = file_format_dropdown.text.strip()
            if "Excel" not in current_value:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", file_format_dropdown)
                driver.execute_script("arguments[0].click();", file_format_dropdown)
                overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")))
                wait.until(EC.visibility_of(overlay))
                excel_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//mat-option//span[contains(text(), 'Excel')]")))
                driver.execute_script("arguments[0].click();", excel_option)
                logger.info("   ✅ Selected Excel format")
                time.sleep(1)
            else:
                logger.info("   ✅ File format already set to Excel")
        except Exception as e:
            logger.warning(f"   ⚠️ Could not set file format: {e}")

        # 2. Click Download button
        download_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(normalize-space(), 'Download')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", download_btn)
        driver.execute_script("arguments[0].click();", download_btn)
        logger.info("   ✅ Download button clicked")
        time.sleep(5)
        logger.info("✅ Download triggered successfully.")
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        driver.save_screenshot("download_button_error.png")
        raise

def run(driver, wait, data):
    go_to_reports_page(driver, wait)
    fill_sales_order_status_form(driver, wait, data)
    click_view(driver, wait)
    click_download(driver, wait)