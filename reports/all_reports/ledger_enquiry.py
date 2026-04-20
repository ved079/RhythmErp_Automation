from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import logging

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

def select_dropdown(driver, wait, value, control_name=None, label_text=None, control_id=None, searchable=True):
    """Universal dropdown selection."""
    try:
        identifier = control_name or label_text or control_id or "unknown"
        logger.info(f"➡️ Selecting {identifier}: {value}")

        dropdown = None
        if control_name:
            dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"mat-select[formcontrolname='{control_name}']")))
        elif label_text:
            dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-label[contains(text(), '{label_text}')]/ancestor::mat-form-field//mat-select")))
        elif control_id:
            dropdown = wait.until(EC.element_to_be_clickable((By.ID, control_id)))

        if not dropdown:
            raise ValueError("No locator provided")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        driver.execute_script("arguments[0].click();", dropdown)

        overlay = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")
        ))
        wait.until(EC.visibility_of(overlay))

        if searchable:
            search_input = wait.until(EC.presence_of_element_located(
                (By.XPATH, ".//input[@placeholder='Search' or contains(@class,'mat-filter-input')]")
            ))
            search_input.clear()
            search_input.send_keys(value)
            logger.info(f"   🔍 Filtered with '{value}'")
            time.sleep(1)

        try:
            option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-option//span[normalize-space()='{value}']")))
        except:
            option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-option//span[contains(text(), '{value}')]")))

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
        driver.execute_script("arguments[0].click();", option)
        logger.info(f"   ✅ Selected: {value}")
        
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-backdrop")))
        time.sleep(0.5)
    except Exception as e:
        logger.error(f"❌ Dropdown failed for {identifier}: {e}")
        driver.save_screenshot(f"dropdown_error_{identifier}.png")
        raise

def fill_input(driver, wait, value, control_name=None, control_id=None):
    """Fill a simple input or Datepicker field (Bypasses Angular restrictions)."""
    try:
        identifier = control_name or control_id
        logger.info(f"➡️ Typing in {identifier}: {value}")
        
        if control_name:
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"input[formcontrolname='{control_name}']")))
        elif control_id:
            element = wait.until(EC.presence_of_element_located((By.ID, control_id)))
        else:
            raise ValueError("Either control_name or control_id must be provided")
            
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", element)
        time.sleep(0.2)
        
        element.send_keys(Keys.CONTROL + "a") 
        element.send_keys(Keys.BACKSPACE)
        time.sleep(0.2)
        element.send_keys(str(value))
        time.sleep(0.2)
        element.send_keys(Keys.TAB) 
        
        logger.info(f"   ✅ Filled {identifier}: {value}")
    except Exception as e:
        logger.error(f"❌ Failed to fill {identifier}: {e}")
        driver.save_screenshot(f"fill_error_{identifier}.png")
        raise

def go_to_reports_page(driver, wait):
    logger.info("Navigating to Reports page...")
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-container, .swal2-container, .ngx-spinner-overlay")))
        logger.info("   ✅ Success overlays cleared.")
    except:
        pass 

    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    try:
        xpath = "//a[contains(@href, 'rhythm-report/reports')] | //span[contains(text(), 'All Reports')]/ancestor::a"
        reports_menu = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", reports_menu)
        driver.execute_script("arguments[0].click();", reports_menu) 
        logger.info("   ✅ Clicked All Reports menu")
    except Exception as e:
        driver.save_screenshot("reports_menu_not_found.png")
        logger.error(f"❌ Could not find Reports menu: {e}")
        raise

    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-select[formcontrolname='report_name']")))
    logger.info("✅ Reports page loaded.")

def select_report_name(driver, wait, report_name="Ledger Enquiry"):
    logger.info(f"   🔽 Selecting Report Name: {report_name}...")
    try:
        dropdown = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-select[formcontrolname='report_name']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        time.sleep(0.5)
        
        if report_name in dropdown.text:
            logger.info(f"      ✅ Report Name is already set to '{report_name}'")
            return True

        driver.execute_script("arguments[0].click();", dropdown)
        logger.info("      Dropdown opened")

        overlay = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")
        ))
        wait.until(EC.visibility_of(overlay))

        option = wait.until(EC.presence_of_element_located((By.XPATH, f"//mat-option//span[contains(normalize-space(), '{report_name}')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
        driver.execute_script("arguments[0].click();", option)
        logger.info(f"      ✅ Selected report: {report_name}")
        
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-backdrop")))
        time.sleep(1)
        return True
    except Exception as e:
        logger.error(f"      ❌ Failed to select report name: {e}")
        driver.save_screenshot("select_report_name_error.png")
        return False

def fill_ledger_enquiry_form(driver, wait, data):
    logger.info("📝 Filling Ledger Enquiry form...")
    
    if not select_report_name(driver, wait, "Ledger Enquiry"):
        raise Exception("Could not select Report Name")
    
    time.sleep(1.5) 
    logger.info("   ⏳ Waiting for form to initialize...")
    
    # Wait for the first specific field to load (Frequency is usually a safe ID)
    try:
        wait.until(EC.presence_of_element_located((By.ID, "account_ref_id")))
        logger.info("   ✅ Base form rendered.")
    except Exception:
        logger.error("   ❌ Form never appeared")
        driver.save_screenshot("form_not_appeared.png")
        raise
        
    # Smart Field Map for Ledger Enquiry
    field_map = [
        ('account', 'account_ref_id', 'dropdown', 'Account', data.get('account')), # <--- Updated ID here!
        ('frequency', 'frequancy', 'dropdown', 'Frequency', data.get('frequency')),
        ('file_format', 'file_format', 'dropdown', 'File Format', data.get('file_format')),
        ('from_date', 'from_date', 'input', 'From Date', data.get('from_date')),
        ('to_date', 'to_date', 'input', 'To Date', data.get('to_date'))
    ]
    
    # Loop through and route to the correct UI function
    for key, elem_locator, field_type, fallback_label, val in field_map:
        if val: 
            if field_type == 'dropdown':
                try:
                    select_dropdown(driver, wait, value=val, control_id=elem_locator, searchable=True)
                except Exception:
                    try:
                        select_dropdown(driver, wait, value=val, control_name=elem_locator, searchable=True)
                    except Exception:
                        try:
                            logger.warning(f"   ⚠️ ID/Name failed for {elem_locator}, trying Label: '{fallback_label}'...")
                            select_dropdown(driver, wait, value=val, label_text=fallback_label, searchable=True)
                        except Exception:
                            logger.warning(f"   ⚠️ Searchable failed, trying non-searchable click for {elem_locator}...")
                            select_dropdown(driver, wait, value=val, control_id=elem_locator, searchable=False)
            
            elif field_type == 'input':
                time.sleep(1) 
                fill_input(driver, wait, value=val, control_id=elem_locator)
    
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
        time.sleep(3) 
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table, .report-container")))
        logger.info("✅ Report table loaded.")
    except Exception as e:
        logger.warning(f"⚠️ View clicked but table check failed: {e}")
        driver.save_screenshot("view_button_error.png")

def click_download(driver, wait):
    try:
        download_xpath = "//button[contains(normalize-space(), 'Download')] | //button[contains(@class, 'apply') and contains(text(), 'Download')]"
        download_btn = wait.until(EC.presence_of_element_located((By.XPATH, download_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", download_btn)
        driver.execute_script("arguments[0].click();", download_btn)
        time.sleep(4)
        logger.info("✅ Download triggered successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Download failed: {e}")
        driver.save_screenshot("download_button_error.png")

def run(driver, wait, data):
    """Complete Ledger Enquiry flow."""
    go_to_reports_page(driver, wait)
    fill_ledger_enquiry_form(driver, wait, data)
    click_view(driver, wait)
    click_download(driver, wait)