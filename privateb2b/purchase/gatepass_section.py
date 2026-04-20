from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from common.helper import select_dropdown, fill_input, click_submit

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

def fill_gatepass_registration(driver, wait, data):
    logger.info("⚡ Starting Gate Pass Registration...")

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='supplier_ref_id']")))
    time.sleep(0.5)

    # --- 1. FILL THE CONSTANT DATE FIRST ---
    logger.info(f"   📅 Setting Transaction Date to: {data['transaction_date']}")
    fill_input(driver, wait, data['transaction_date'], control_name="transaction_date")

    # --- 2. STANDARD DROPDOWNS ---
    select_dropdown(driver, wait, data['supplier'], control_name="supplier_ref_id")
    select_dropdown(driver, wait, data['item_type'], control_name="item_type_ref_id")
    time.sleep(1)

    select_dropdown(driver, wait, data['department'], label_text="Department", searchable=False)
    select_dropdown(driver, wait, data['division'], label_text="Division", searchable=False)
    select_dropdown(driver, wait, data['location'], label_text="Location", searchable=False)
    select_dropdown(driver, wait, data['sale_type'], label_text="Type of Sale", searchable=False)
    select_dropdown(driver, wait, data['delivery_terms'], label_text="Delivery Terms", searchable=False)

    # --- 3. STANDARD INPUTS ---
    fill_input(driver, wait, data['vehicle_no'], control_name="vehicle_no")
    fill_input(driver, wait, data['driver_name'], control_name="driver_name")
    fill_input(driver, wait, data['driver_contact'], control_name="driver_contact_no")
    fill_input(driver, wait, data['in_time'], control_name="in_time")

    # --- 4. MULTI-ITEM LOOP ---
    logger.info(f"   📦 Adding {len(data['items'])} items to Gate Pass...")
    
    for index, item_data in enumerate(data['items']):
        # If it's not the first item, we need to click the '+' button to add a new row
        if index > 0:
            add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.apply-button i.fa-plus")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
            driver.execute_script("arguments[0].click();", add_btn)
            time.sleep(1) # Let Angular render the new row

        # Locate the specific row for this iteration (XPath is 1-indexed)
        row_xpath = f"//tbody[contains(@class, 'main_tbody')]/tr[{index + 1}]"
        row = wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))
        logger.info(f"      ➡️ Filling Row {index + 1}: {item_data['item']}")

        # A. Select Item Dropdown INSIDE this specific row
        item_dropdown = row.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='item_ref_id']")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", item_dropdown)
        driver.execute_script("arguments[0].click();", item_dropdown)
        
        # Wait for the standard overlay, then click the option
        overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")))
        wait.until(EC.visibility_of(overlay))
        
        option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-option//span[normalize-space()='{item_data['item']}']")))
        driver.execute_script("arguments[0].click();", option)
        time.sleep(0.5)

        # B. Fill Bags INSIDE this specific row
        bags_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='no_of_bags']")
        bags_input.clear()
        bags_input.send_keys(str(item_data['no_of_bags']))

        # C. Fill Quantity INSIDE this specific row
        qty_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='quantity']")
        qty_input.clear()
        qty_input.send_keys(str(item_data['quantity']))

    # --- 5. SUBMIT ---
    logger.info("📤 Submitting the form...")
    click_submit(driver, wait)

    time.sleep(3)
    logger.info("🚀 Gate Pass Registration Completed Successfully!")