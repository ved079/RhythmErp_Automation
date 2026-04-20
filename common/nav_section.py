from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# ----------------------------------------------------------------------
# Helper: Wait for SweetAlert overlay to close
# ----------------------------------------------------------------------
def wait_for_sweetalert_to_close(driver, wait, timeout=10):
    """Wait for any SweetAlert2 overlay to disappear."""
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container")))
        logger.info("✅ SweetAlert overlay closed.")
    except TimeoutException:
        # If overlay doesn't disappear, take a screenshot but continue
        driver.save_screenshot("sweetalert_still_open.png")
        logger.warning("⚠️ SweetAlert overlay still visible; continuing anyway.")

# ----------------------------------------------------------------------
# Navigation functions (with smart menu handling)
# ----------------------------------------------------------------------
def go_to_farmer_page(driver, wait):
    logger.info("Navigating to Farmer Page...")
    farmer_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Farmer")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", farmer_link)
    driver.execute_script("arguments[0].click();", farmer_link)
    time.sleep(1)

    add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".new_employee")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(1)

def go_to_supplier_page(driver, wait):
    logger.info("Farmer submitted! Waiting 15 seconds before moving to Supplier...")
    time.sleep(17)

    logger.info("Navigating to Supplier Page...")
    supplier_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Supplier")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", supplier_link)
    driver.execute_script("arguments[0].click();", supplier_link)
    time.sleep(4)

    add_btn_xpath = "//button[contains(., 'Add New Supplier')]"
    time.sleep(3)
    add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, add_btn_xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(1)

def go_to_agent_page(driver, wait):
    logger.info("Navigating to Agent Page...")
    agent_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'agent-registration')]")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", agent_link)
    driver.execute_script("arguments[0].click();", agent_link)
    time.sleep(1)

    add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.new_employee")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(1)

def go_to_customer_page(driver, wait):
    logger.info("Navigating to Customer Page...")
    
    # 1. Click the Customer menu link (JavaScript to avoid interception)
    customer_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'customer-registration')]")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", customer_link)
    driver.execute_script("arguments[0].click();", customer_link)
    time.sleep(2)
    logger.info("   ✅ Clicked Customer menu link.")

    # 2. Click the ADD button (JavaScript to avoid overlay issues)
    add_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.new_employee")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn)
    logger.info("   ✅ Add button clicked (JavaScript).")
    
    # 3. Wait for the form to appear (company_name input)
    time.sleep(2)
    try:
        wait.until(EC.visibility_of_element_located((By.ID, "company_name")))
        logger.info("   ✅ Customer form loaded.")
    except Exception as e:
        driver.save_screenshot("customer_form_not_loaded.png")
        logger.error("❌ Customer form did not load. Screenshot saved.")
        raise

def go_to_employee_page(driver, wait):
    logger.info("Navigating to Employee Page...")
    employee_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'user')]")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", employee_link)
    driver.execute_script("arguments[0].click();", employee_link)
    time.sleep(2)

    add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.new_employee")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(2)

    wait.until(EC.presence_of_element_located((By.XPATH, "//input[@formcontrolname='emp_name']")))
    logger.info("✅ Employee form loaded.")

def go_to_gatepass_page(driver, wait):
    logger.info("Navigating to Gate Pass page...")
    
    # Wait for any SweetAlert overlay to disappear
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container, .cdk-overlay-backdrop")))
    except:
        pass

    # Scroll to top to ensure menus are visible
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # Open Private (B2B) menu
    try:
        b2b = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ng-star-inserted:nth-child(11) .hide-menu")))
    except:
        b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Private (B2B)')]")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b2b)
    driver.execute_script("arguments[0].click();", b2b)
    time.sleep(1)

    # Click Purchase
    purchase = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", purchase)
    driver.execute_script("arguments[0].click();", purchase)
    time.sleep(1)

    # Click Gate Pass
    gatepass_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Gate Pass")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", gatepass_link)
    driver.execute_script("arguments[0].click();", gatepass_link)
    time.sleep(2)

    # Click "Add New Gate Pass" button
    add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".mat-mdc-tooltip-trigger, button.new_employee")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(2)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='supplier_ref_id']")))
    logger.info("✅ Gate Pass form loaded.")

def go_to_grn_page(driver, wait):
    logger.info("Navigating to GRN page...")
    time.sleep(2)

    # ---------- 1. Navigate to GRN (smart menu) ----------
    try:
        grn = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "GRN")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", grn)
        driver.execute_script("arguments[0].click();", grn)
        logger.info("   Menu was already open. Clicked GRN directly.")
    except (TimeoutException, NoSuchElementException):
        logger.info("   Menu was closed. Opening B2B -> Purchase...")
        try:
            b2b = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ng-star-inserted:nth-child(11) .hide-menu")))
        except:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b2b)
        b2b.click()
        time.sleep(1)

        purchase = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", purchase)
        purchase.click()
        time.sleep(1)

        grn = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "GRN")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", grn)
        driver.execute_script("arguments[0].click();", grn)

    time.sleep(2)

    # ---------- 2. AGGRESSIVELY REMOVE OVERLAYS ----------
    # Wait for the side menu to disappear (or force it)
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "a.ml-sub-menu")))
        logger.info("   Sidebar menu collapsed.")
    except TimeoutException:
        # Force hide all sub-menus with JavaScript
        driver.execute_script("""
            var subMenus = document.querySelectorAll('a.ml-sub-menu');
            subMenus.forEach(function(el) { el.style.display = 'none'; });
        """)
        logger.info("   Sidebar force-hidden with JS.")
    time.sleep(1)

    # Also dismiss any CDK overlays / SweetAlert
    try:
        driver.execute_script("""
            var overlays = document.querySelectorAll('.cdk-overlay-backdrop, .swal2-container');
            overlays.forEach(function(el) { el.style.display = 'none'; });
        """)
    except:
        pass

    # ---------- 3. CLICK THE "ADD" BUTTON (multiple strategies) ----------
    add_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.new_employee")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    time.sleep(0.5)

    # Strategy A: ActionChains hover + native click (handles overlays better)
    try:
        actions = ActionChains(driver)
        actions.move_to_element(add_btn).pause(0.3).click().perform()
        logger.info("   ✅ Add button clicked via ActionChains.")
    except Exception as e:
        logger.warning(f"   ActionChains click failed: {e}. Falling back to JS click.")
        driver.execute_script("arguments[0].click();", add_btn)
        logger.info("   ✅ Add button clicked via JavaScript.")

    time.sleep(2)

    # ---------- 4. CONFIRM FORM LOADED ----------
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='supplier_ref_id']")))
    logger.info("✅ GRN form loaded.")
    

def go_to_qc_page(driver, wait):
    logger.info("Navigating to QC page...")
    
    # 👻 Rule 2: Overlay Assassination (Wait for GRN success toast to clear)
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container, .cdk-overlay-backdrop")))
    except:
        pass
        
    time.sleep(2)

    try:
        # Try to click QC link directly (menu already open)
        qc_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "QC")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", qc_link)
        driver.execute_script("arguments[0].click();", qc_link)
        logger.info("   Menu was already open. Clicked QC directly.")
    except (TimeoutException, NoSuchElementException):
        # Menu collapsed – open B2B -> Purchase
        logger.info("   Menu was closed. Opening B2B -> Purchase...")
        try:
            b2b = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ng-star-inserted:nth-child(11) .hide-menu")))
        except:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b2b)
        b2b.click()
        time.sleep(1)

        purchase = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", purchase)
        purchase.click()
        time.sleep(1)

        qc_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "QC")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", qc_link)
        driver.execute_script("arguments[0].click();", qc_link)

    time.sleep(5)

    # Click "Add New QC" button
    try:
        add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.new_employee")))
    except:
        add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Add New QC')]")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    
    # ⚠️ Rule 1: The JavaScript Click is King
    driver.execute_script("arguments[0].click();", add_btn) 
    time.sleep(2)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='supplier_ref_id']")))
    logger.info("✅ QC form loaded.")

def go_to_purchase_booking_page(driver, wait):
    start = time.time()
    logger.info("Navigating to Purchase Booking page...")
    # Wait for any SweetAlert to disappear, but use a short timeout to avoid long waits
    try:
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "swal2-container")))
        logger.info("   SweetAlert overlay closed.")
    except:
        pass

    # Try to click the link directly (if menu is already open)
    try:
        # THE FIX: Create a temporary 5-second wait object instead of passing timeout to .until()
        from selenium.webdriver.support.ui import WebDriverWait
        short_wait = WebDriverWait(driver, 5)
        pb_link = short_wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase Booking")))
        
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", pb_link)
        driver.execute_script("arguments[0].click();", pb_link)
        logger.info("   Menu was already open. Clicked Purchase Booking directly.")
    except:
        # Menu collapsed – open B2B -> Purchase -> Purchase Booking
        logger.info("   Menu was closed. Opening B2B -> Purchase -> Purchase Booking...")
        b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Private (B2B)')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b2b)
        driver.execute_script("arguments[0].click();", b2b)
        time.sleep(0.5)

        purchase = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", purchase)
        driver.execute_script("arguments[0].click();", purchase)
        time.sleep(0.5)

        pb_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Purchase Booking")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", pb_link)
        driver.execute_script("arguments[0].click();", pb_link)

    # Wait for the search input (or table header) to appear
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.search-field[placeholder='Search in table']")))
    logger.info(f"   Page loaded in {time.time() - start:.1f} seconds.")

def go_to_farmer_list(driver, wait):
    logger.info("Navigating to Farmer List...")
    # Wait for any overlay to disappear (e.g., success toast)
    try:
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "cdk-overlay-container")))
    except:
        pass
    # Click Farmer link
    farmer_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Farmer")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", farmer_link)
    driver.execute_script("arguments[0].click();", farmer_link)
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("✅ Farmer list loaded.")

def go_to_supplier_list(driver, wait):
    logger.info("Navigating to Supplier List...")
    try:
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "cdk-overlay-container")))
    except:
        pass
    supplier_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Supplier")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", supplier_link)
    driver.execute_script("arguments[0].click();", supplier_link)
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("✅ Supplier list loaded.")

def go_to_agent_list(driver, wait):
    logger.info("Navigating to Agent List...")
    try:
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "cdk-overlay-container")))
    except:
        pass
    agent_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'agent-registration')]")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", agent_link)
    driver.execute_script("arguments[0].click();", agent_link)
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("✅ Agent list loaded.")

def go_to_customer_page(driver, wait):
    logger.info("Navigating to Customer Page...")
    
    # 1. Locate and click the Customer menu link
    customer_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'customer-registration')]")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", customer_link)
    
    # Use ActionChains to hover, then native click (mimicking your IDE)
    actions = ActionChains(driver)
    actions.move_to_element(customer_link).perform()
    time.sleep(0.5)
    customer_link.click()
    logger.info("   ✅ Clicked Customer menu link.")
    
    time.sleep(2) # Wait for the table/list to load

    # 2. Locate and click the Add button
    add_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.new_employee")))
    driver.execute_script("arguments[0].click();", add_btn) # JS Click doesn't even need scrollIntoView!
    
    # Use ActionChains to hover, then native click (NO JS CLICK HERE)
    actions.move_to_element(add_btn).perform()
    time.sleep(0.5)
    add_btn.click() 
    logger.info("   ✅ Add button clicked (Native click).")

    time.sleep(2)
    
    # 3. Wait for the form to open using the highly specific CSS selector
    try:
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input#company_name[name='Company Name']")))
        logger.info("✅ Customer form loaded (company_name found).")
    except Exception as e:
        driver.save_screenshot("customer_form_not_loaded.png")
        logger.error(f"❌ Form did not load. Screenshot saved as customer_form_not_loaded.png")
        raise

def go_to_customer_page(driver, wait):
    logger.info("Navigating to Customer Page...")

    # 1. Click the Customer menu link
    customer_link = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//a[contains(@href, 'customer-registration')]")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", customer_link)
    driver.execute_script("arguments[0].click();", customer_link)
    logger.info("   ✅ Clicked Customer menu link.")

    time.sleep(2)  # Let the list/table render

    # 2. ✅ PERMANENT FIX: Wait for any Angular CDK overlay/backdrop to fully clear
    #    (same pattern used in go_to_agent_list — this is what was missing)
    try:
        wait.until(EC.invisibility_of_element_located(
            (By.CLASS_NAME, "cdk-overlay-container")
        ))
    except:
        pass  # If no overlay present, that's fine too

    # 3. Click the ADD button — JS click only (no double-click)
    add_btn = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "button.new_employee")
    ))
    driver.execute_script("arguments[0].click();", add_btn)
    logger.info("   ✅ Add button clicked.")

    time.sleep(2)

    # 4. Confirm the form loaded
    try:
        wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input#company_name[name='Company Name']")
        ))
        logger.info("✅ Customer form loaded (company_name found).")
    except Exception:
        driver.save_screenshot("customer_form_not_loaded.png")
        logger.error("❌ Form did not load. Screenshot saved as customer_form_not_loaded.png")
        raise

    

def go_to_employee_list(driver, wait):
    logger.info("Navigating to Employee List...")
    employee_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'user')]")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", employee_link)
    driver.execute_script("arguments[0].click();", employee_link)
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    logger.info("✅ Employee list loaded.")

def go_to_inventory_summary(driver, wait):
    logger.info("Navigating to Inventory Summary...")
    time.sleep(2) # Let Purchase Booking success toast fade
    
    try:
        # Try to click Inventory Summary directly
        inv_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Inventory Summary")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inv_link)
        driver.execute_script("arguments[0].click();", inv_link)
    except:
        # If it's hidden inside a 'Reports' or 'Inventory' menu, open that first
        logger.info("   Menu closed. Opening Reports/Inventory menu...")
        # (Adjust this text if your main menu category is named differently)
        reports_menu = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Inventory') or contains(text(),'Reports')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", reports_menu)
        reports_menu.click()
        time.sleep(1)
        
        inv_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Inventory Summary")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inv_link)
        driver.execute_script("arguments[0].click();", inv_link)

    # Wait for the filter button/dropdowns to load to confirm page is ready
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.apply, .apply-button")))
    logger.info("✅ Inventory Summary page loaded.")

def go_to_trial_balance(driver, wait):
    logger.info("Navigating to trial_balance...")
    time.sleep(2) # Let Purchase Booking success toast fade
    
    try:
        # Try to click trial_balance directly
        inv_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Trial Balance")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inv_link)
        driver.execute_script("arguments[0].click();", inv_link)
    except:
        # If it's hidden inside a 'Reports' or 'Inventory' menu, open that first
        logger.info("   Menu closed. Opening Reports/Inventory menu...")
        # (Adjust this text if your main menu category is named differently)
        reports_menu = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Inventory') or contains(text(),'Reports')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", reports_menu)
        reports_menu.click()
        time.sleep(1)
        
        inv_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Trial Balance")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inv_link)
        driver.execute_script("arguments[0].click();", inv_link)

    # Wait for the filter button/dropdowns to load to confirm page is ready
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.apply, .apply-button")))
    logger.info("✅ Trial Balance page loaded.")



def go_to_sales_order_page(driver, wait):
    logger.info("Navigating to Sales Order page...")
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container, .cdk-overlay-backdrop, .ngx-spinner-overlay")))
    except:
        pass
        
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # --- SMART MENU NAVIGATION ---
    # 1. Check if 'Sales' is visible. If not, B2B is closed, so click it.
    sales_links = driver.find_elements(By.LINK_TEXT, "Sales")
    if not sales_links or not sales_links[0].is_displayed():
        try:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Private (B2B)')]")))
        except:
            b2b = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ng-star-inserted:nth-child(11) .hide-menu")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b2b)
        driver.execute_script("arguments[0].click();", b2b)
        time.sleep(1)

    # 2. Check if 'Sales Order' is visible. If not, Sales is closed, so click it.
    so_links = driver.find_elements(By.LINK_TEXT, "Sales Order")
    if not so_links or not so_links[0].is_displayed():
        sales = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sales")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sales)
        driver.execute_script("arguments[0].click();", sales)
        time.sleep(1)
    # -----------------------------

    # Click Sales Order
    sales_order = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sales Order")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sales_order)
    driver.execute_script("arguments[0].click();", sales_order)
    time.sleep(2)

    # Click "Generate Conversion Rate" button if present
    try:
        conv_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Generate Conversion Rate')]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", conv_btn)
        driver.execute_script("arguments[0].click();", conv_btn)
        logger.info("   ✅ Clicked 'Generate Conversion Rate' button")
        time.sleep(1)
    except Exception as e:
        logger.warning(f"   ⚠️ 'Generate Conversion Rate' button not found or not clickable: {e}")
    time.sleep(5)

    # Click "Add New Sales Order" button
    add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.new_employee")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(2)

    # Wait for the form to load – look for Customer Name dropdown
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='customer_ref_id']")))
    logger.info("✅ Sales Order form loaded.")

def go_to_lot_creation_page(driver, wait):
    logger.info("Navigating to Lot Creation page...")
    
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container, .cdk-overlay-backdrop, .ngx-spinner-overlay")))
    except:
        pass

    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # --- THE FIX: SMART MENU NAVIGATION ---
    # 1. Check if 'Sales' is visible. If not, B2B is closed, so we click it.
    sales_links = driver.find_elements(By.LINK_TEXT, "Sales")
    if not sales_links or not sales_links[0].is_displayed():
        try:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Private (B2B)')]")))
        except:
            b2b = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ng-star-inserted:nth-child(11) .hide-menu")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b2b)
        driver.execute_script("arguments[0].click();", b2b)
        time.sleep(1)

    # 2. Check if 'Lot Creation' is visible. If not, Sales is closed, so we click it.
    lot_links = driver.find_elements(By.LINK_TEXT, "Lot Creation")
    if not lot_links or not lot_links[0].is_displayed():
        sales = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sales")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sales)
        driver.execute_script("arguments[0].click();", sales)
        time.sleep(1)
    # ---------------------------------------
    
    # Click Lot Creation
    lot_creation = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Lot Creation")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lot_creation)
    driver.execute_script("arguments[0].click();", lot_creation)
    time.sleep(2)


    try:
        conv_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Generate Conversion Rate')]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", conv_btn)
        driver.execute_script("arguments[0].click();", conv_btn)
        logger.info("   ✅ Clicked 'Generate Conversion Rate' button")
        time.sleep(1)
    except Exception as e:
        logger.warning(f"   ⚠️ 'Generate Conversion Rate' button not found or not clickable: {e}")



    time.sleep(5)

    # Click "Add New Lot" button
    add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.new_employee")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(2)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    logger.info("✅ Lot Creation form loaded.")

def go_to_dispatch_note_page(driver, wait):
    logger.info("Navigating to Dispatch Note page...")
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container, .cdk-overlay-backdrop, .ngx-spinner-overlay")))
    except:
        pass
        
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # --- SMART MENU NAVIGATION ---
    # 1. Check if 'Sales' is visible. If not, B2B is closed, so click it.
    sales_links = driver.find_elements(By.LINK_TEXT, "Sales")
    if not sales_links or not sales_links[0].is_displayed():
        try:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Private (B2B)')]")))
        except:
            b2b = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ng-star-inserted:nth-child(11) .hide-menu")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b2b)
        driver.execute_script("arguments[0].click();", b2b)
        time.sleep(1)

    # 2. Check if 'Dispatch Note' is visible. If not, Sales is closed, so click it.
    dispatch_links = driver.find_elements(By.LINK_TEXT, "Dispatch Note")
    if not dispatch_links or not dispatch_links[0].is_displayed():
        sales = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sales")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sales)
        driver.execute_script("arguments[0].click();", sales)
        time.sleep(1)
    # -----------------------------

    # Click Dispatch Note
    dispatch = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Dispatch Note")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dispatch)
    driver.execute_script("arguments[0].click();", dispatch)
    time.sleep(2)

    
    
    # Click Add New Dispatch Note button
    add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.new_employee")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(2)
    
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='customer_ref_id']")))
    logger.info("✅ Dispatch Note form loaded.")

def go_to_invoice_page(driver, wait):
    logger.info("Navigating to Invoice page...")
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container, .cdk-overlay-backdrop, .ngx-spinner-overlay")))
    except:
        pass
        
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # --- SMART MENU NAVIGATION ---
    # 1. Check if 'Sales' is visible. If not, B2B is closed, so click it.
    sales_links = driver.find_elements(By.LINK_TEXT, "Sales")
    if not sales_links or not sales_links[0].is_displayed():
        try:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Private (B2B)')]")))
        except:
            b2b = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ng-star-inserted:nth-child(11) .hide-menu")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b2b)
        driver.execute_script("arguments[0].click();", b2b)
        time.sleep(1)

    # 2. Check if 'Invoice' is visible. If not, Sales is closed, so click it.
    invoice_links = driver.find_elements(By.LINK_TEXT, "Invoice")
    if not invoice_links or not invoice_links[0].is_displayed():
        sales = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sales")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sales)
        driver.execute_script("arguments[0].click();", sales)
        time.sleep(1)
    # -----------------------------

    # Click Invoice
    invoice = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Invoice")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", invoice)
    driver.execute_script("arguments[0].click();", invoice)
    time.sleep(2)

    # Click "Add New Invoice" button
    add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.new_employee")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(2)

    # Wait for the customer dropdown to be present
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='customer_ref_id']")))
    logger.info("✅ Invoice form loaded.")

def go_to_receipt_page(driver, wait):
    logger.info("Navigating to Receipt page...")
    # Wait for any SweetAlert overlay to disappear
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container, .cdk-overlay-backdrop, .ngx-spinner-overlay")))
    except:
        pass
        
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # --- SMART MENU NAVIGATION ---
    sales_links = driver.find_elements(By.LINK_TEXT, "Sales")
    if not sales_links or not sales_links[0].is_displayed():
        try:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Private (B2B)')]")))
        except:
            b2b = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ng-star-inserted:nth-child(11) .hide-menu")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b2b)
        driver.execute_script("arguments[0].click();", b2b)
        time.sleep(1)

    receipt_links = driver.find_elements(By.LINK_TEXT, "Receipt")
    if not receipt_links or not receipt_links[0].is_displayed():
        sales = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sales")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sales)
        driver.execute_script("arguments[0].click();", sales)
        time.sleep(1)

    receipt = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Receipt")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", receipt)
    driver.execute_script("arguments[0].click();", receipt)
    time.sleep(2)

    # Click "Generate Conversion Rates" button if present
    try:
        conv_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Generate Conversion Rates')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", conv_btn)
        driver.execute_script("arguments[0].click();", conv_btn)
        logger.info("   ✅ Clicked 'Generate Conversion Rates' button")
        time.sleep(1)
    except Exception as e:
        logger.warning(f"   ⚠️ 'Generate Conversion Rates' button not found or not clickable: {e}")

    time.sleep(5)
    # Click "Add New Receipt" button
    add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.new_employee")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(2)

    # Wait for the form to load (customer dropdown)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='customer_ref_id']")))
    logger.info("✅ Receipt form loaded.")

def go_to_reports_page(driver, wait):
    logger.info("Navigating to Reports page...")
    
    # Wait for any overlays/spinners to disappear
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-backdrop, .swal2-container, .ngx-spinner-overlay")))
    except:
        pass
    
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # Smart menu: try direct click first
    try:
        reports_link = driver.find_element(By.XPATH, "//a[contains(@href, 'rhythm-report/reports')] | //span[contains(text(), 'All Reports')]/ancestor::a")
        if reports_link.is_displayed():
            driver.execute_script("arguments[0].click();", reports_link)
            logger.info("   ✅ Clicked All Reports menu directly.")
        else:
            raise Exception("Not visible")
    except:
        logger.info("   Menu collapsed – attempting to expand...")
        # Try to expand a top-level "Reports" menu if present
        try:
            reports_toggle = driver.find_element(By.XPATH, "//span[contains(text(), 'Reports')]/ancestor::a")
            driver.execute_script("arguments[0].click();", reports_toggle)
            time.sleep(1)
        except:
            pass
        # Now click the "All Reports" link
        reports_link = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(@href, 'rhythm-report/reports')] | //span[contains(text(), 'All Reports')]/ancestor::a")
        ))
        driver.execute_script("arguments[0].click();", reports_link)
        logger.info("   ✅ Clicked All Reports menu after expansion.")

    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-select[formcontrolname='report_name']")))
    logger.info("✅ Reports page loaded.")


def go_to_stock_transfer_page(driver, wait):
    logger.info("Navigating to Stock Transfer page...")
    # Wait for any overlays to disappear
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container, .cdk-overlay-backdrop, .ngx-spinner-overlay")))
    except:
        pass
        
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # --- SMART MENU NAVIGATION ---
    # Check if 'Stock Transfer' is directly visible (menu may already be expanded)
    stock_transfer_links = driver.find_elements(By.LINK_TEXT, "Stock Transfer")
    if not stock_transfer_links or not stock_transfer_links[0].is_displayed():
        # Need to expand B2B menu first
        try:
            b2b = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Private (B2B)')]")))
        except:
            b2b = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ng-star-inserted:nth-child(11) .hide-menu")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b2b)
        driver.execute_script("arguments[0].click();", b2b)
        time.sleep(1)

    # Now Stock Transfer should be visible (it's a direct child under B2B, not nested under Purchase/Sales)
    stock_transfer = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Stock Transfer")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", stock_transfer)
    driver.execute_script("arguments[0].click();", stock_transfer)
    time.sleep(2)

    # Click "+ Add New Stock Transfer" button
    add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add New Stock Transfer')]")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(2)

    # Wait for the form to load – adjust the selector based on actual form fields
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='transaction_date'], [formcontrolname='item_ref_id']")))
    logger.info("✅ Stock Transfer form loaded.")