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
    try:
        identifier = control_name or label_text or control_id or "unknown"
        logger.info(f"➡️ Selecting {identifier}: {value}")
        dropdown = None
        if control_name: dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"mat-select[formcontrolname='{control_name}']")))
        elif label_text: dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-label[contains(text(), '{label_text}')]/ancestor::mat-form-field//mat-select")))
        elif control_id: dropdown = wait.until(EC.element_to_be_clickable((By.ID, control_id)))
        if not dropdown: raise ValueError("No locator provided")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        driver.execute_script("arguments[0].click();", dropdown)

        overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")))
        wait.until(EC.visibility_of(overlay))

        if searchable:
            search_input = wait.until(EC.presence_of_element_located((By.XPATH, ".//input[@placeholder='Search' or contains(@class,'mat-filter-input')]")))
            search_input.clear()
            search_input.send_keys(value)
            logger.info(f"   🔍 Filtered with '{value}'")
            time.sleep(1)

        try: option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-option//span[normalize-space()='{value}']")))
        except: option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-option//span[contains(text(), '{value}')]")))

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
    except: pass 
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

def select_report_name(driver, wait, report_name="Supplier Balance"):
    logger.info(f"   🔽 Selecting Report Name: {report_name}...")
    try:
        dropdown = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-select[formcontrolname='report_name']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        time.sleep(0.5)
        if report_name in dropdown.text:
            logger.info(f"      ✅ Report Name is already set to '{report_name}'")
            return True
        driver.execute_script("arguments[0].click();", dropdown)
        overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")))
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

def fill_supplier_balance_form(driver, wait, data):
    logger.info("📝 Filling Supplier Balance form...")
    if not select_report_name(driver, wait, "Supplier Balance"): raise Exception("Failed")
    time.sleep(1.5)
    try:
        wait.until(EC.presence_of_element_located((By.ID, "supplier_ref_id")))
        logger.info("   ✅ Base form rendered.")
    except Exception:
        logger.error("   ❌ Form never appeared")
        driver.save_screenshot("form_not_appeared.png")
        raise
        
    field_map = [
        ('supplier_name', 'supplier_ref_id', 'dropdown', 'Supplier Name', data.get('supplier_name')),
        ('file_format', 'file_format', 'dropdown', 'File Format', data.get('file_format'))
    ]
    
    for key, elem_locator, field_type, fallback_label, val in field_map:
        if val: 
            try: select_dropdown(driver, wait, value=val, control_id=elem_locator, searchable=True)
            except:
                try: select_dropdown(driver, wait, value=val, control_name=elem_locator, searchable=True)
                except:
                    try: select_dropdown(driver, wait, value=val, label_text=fallback_label, searchable=True)
                    except: select_dropdown(driver, wait, value=val, control_id=elem_locator, searchable=False)
    logger.info("✅ Form filling complete.")

def click_view(driver, wait):
    try:
        try: wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "mat-spinner, .ngx-spinner-overlay, .cdk-overlay-backdrop")))
        except: pass
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
    go_to_reports_page(driver, wait)
    fill_supplier_balance_form(driver, wait, data)
    click_view(driver, wait)
    click_download(driver, wait)