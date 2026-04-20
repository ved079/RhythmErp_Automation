from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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

def select_report_name(driver, wait, report_name="Payable"):
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

def fill_payable_form(driver, wait, data):
    logger.info("📝 Filling Payable form (Fast-Track)...")
    
    if not select_report_name(driver, wait, "Payable"):
        raise Exception("Could not select Report Name")
    
    time.sleep(1.5) 
    logger.info("   ⏳ Waiting for form to initialize...")
    
    # Wait for the file format dropdown to physically appear
    try:
        wait.until(EC.presence_of_element_located((By.ID, "file_format")))
        logger.info("   ✅ Base form rendered.")
    except Exception:
        logger.error("   ❌ Form never appeared")
        driver.save_screenshot("form_not_appeared.png")
        raise
    
    # Skip all other fields and only interact with file format
    if data.get('file_format'):
        try:
            select_dropdown(driver, wait, value=data['file_format'], control_id='file_format', searchable=False)
        except Exception:
            # Fallback to formcontrolname if ID fails
            logger.warning("   ⚠️ Search by ID failed, trying formcontrolname...")
            select_dropdown(driver, wait, value=data['file_format'], control_name='file_format', searchable=False)
    
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

def run_payable(driver, wait, data):
    """Complete Payable report flow."""
    go_to_reports_page(driver, wait)
    fill_payable_form(driver, wait, data)
    click_view(driver, wait)
    click_download(driver, wait)