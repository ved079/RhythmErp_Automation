from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import time
import logging
from common.helper import select_dropdown, fill_input

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


# ─────────────────────────────────────────────
#  PERMANENT STALE-ELEMENT FIX
#  Re-locates the element fresh on every retry.
#  Never reuses a reference across iterations.
# ─────────────────────────────────────────────
def click_with_retry(driver, wait, xpath, retries=5, delay=1.5):
    """Find and JS-click an element by XPath, retrying on StaleElementReferenceException."""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            # Re-locate right before clicking — critical to do this as the last step
            element = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            driver.execute_script("arguments[0].click();", element)
            return  # success
        except StaleElementReferenceException as e:
            last_exc = e
            logger.warning(f"   ⚠️ Stale element (attempt {attempt}/{retries}), retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError(f"Element still stale after {retries} attempts [{xpath}]: {last_exc}")


def add_item_row(driver, wait, row_index):
    """Click the '+' button to create a new row for items."""
    try:
        add_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'apply-button') and .//i[contains(@class, 'fa-plus')]]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
        driver.execute_script("arguments[0].click();", add_btn)

        new_row_xpath = f"//tbody[contains(@class, 'main_tbody')]/tr[{row_index + 1}]"
        wait.until(EC.presence_of_element_located((By.XPATH, new_row_xpath)))

        logger.info(f"   ✅ Added new row for item {row_index + 1}")
        time.sleep(0.5)
        return True
    except Exception as e:
        logger.warning(f"   ⚠️ Could not add row {row_index + 1}: {e}")
        return False


def fill_item_row(driver, wait, row_index, item_data):
    """Fill a specific row isolated from the rest of the table."""
    row_xpath = f"//tbody[contains(@class, 'main_tbody')]/tr[{row_index + 1}]"
    row = wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))

    # --- 1. Item Dropdown ---
    item_dropdown = row.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='item_ref_id']")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", item_dropdown)
    time.sleep(0.2)
    driver.execute_script("arguments[0].click();", item_dropdown)

    overlay = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))

    search_inputs = overlay.find_elements(
        By.XPATH, ".//input[contains(@placeholder, 'Search') or contains(@class, 'mat-filter-input')]"
    )
    if search_inputs:
        search_inputs[0].clear()
        search_inputs[0].send_keys(item_data['item_name'])
        time.sleep(1)

    option = wait.until(EC.presence_of_element_located(
        (By.XPATH, f"//mat-option[contains(normalize-space(.), '{item_data['item_name']}')]")
    ))
    driver.execute_script("arguments[0].click();", option)
    wait.until(EC.invisibility_of_element(overlay))
    logger.info(f"      ✅ Selected item: {item_data['item_name']}")

    # --- 2. Quantity ---
    qty_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='quantity']")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", qty_input)
    driver.execute_script("arguments[0].click();", qty_input)
    qty_input.send_keys(Keys.CONTROL, 'a')
    qty_input.send_keys(Keys.BACKSPACE)
    qty_input.send_keys(str(item_data['quantity']))
    qty_input.send_keys(Keys.TAB)
    logger.info(f"      ✅ Quantity: {item_data['quantity']}")

    # --- 3. Rate ---
    rate_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='rate']")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", rate_input)
    driver.execute_script("arguments[0].click();", rate_input)
    rate_input.send_keys(Keys.CONTROL, 'a')
    rate_input.send_keys(Keys.BACKSPACE)
    rate_input.send_keys(str(item_data['rate']))
    rate_input.send_keys(Keys.TAB)
    logger.info(f"      ✅ Rate: {item_data['rate']}")

    # --- 4. Tax Rate ---
    tax_dropdown = row.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='tax_rate']")
    if item_data['item_name'] in {"Soyabean", "Turmeric", "Chana"}:
        tax_rate = "5"
    elif item_data['item_name'] == "Tur-Red":
        tax_rate = "0"
    else:
        tax_rate = str(item_data.get('tax_rate', '0'))

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tax_dropdown)
    time.sleep(0.2)
    driver.execute_script("arguments[0].click();", tax_dropdown)

    overlay = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
    opt = wait.until(EC.presence_of_element_located(
        (By.XPATH, f"//mat-option[contains(normalize-space(.), '{tax_rate}')]")
    ))
    driver.execute_script("arguments[0].click();", opt)
    wait.until(EC.invisibility_of_element(overlay))
    logger.info(f"      ✅ Tax Rate set to {tax_rate}")

    # --- 5. Expected Delivery Date ---
    if 'expected_delivery_date' in item_data:
        date_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='expected_delivery_date']")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", date_input)
        driver.execute_script("arguments[0].click();", date_input)
        driver.execute_script("arguments[0].value = '';", date_input)
        date_input.send_keys(Keys.CONTROL, 'a')
        date_input.send_keys(Keys.BACKSPACE)
        date_input.send_keys(item_data['expected_delivery_date'])
        date_input.send_keys(Keys.TAB)
        logger.info(f"      ✅ Expected delivery date: {item_data['expected_delivery_date']}")


def approve_latest_sales_order(driver, wait):
    """Find the latest Sales Order in the list, open it, and approve it."""
    logger.info("⚡ Approving the newly created Sales Order...")

    # Wait for table and let Angular finish rendering
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
    time.sleep(2)

    # Try each edit-button XPath with retry
    EDIT_XPATHS = [
        "//table/tbody/tr[1]//button[.//i[contains(@class, 'bi-pencil')]]",
        "//table/tbody/tr[1]//button[contains(@class, 'tblActnBtn')]//i[contains(@class, 'bi-pencil')]/..",
        "//table/tbody/tr[1]//button[contains(@class, 'tblActnBtn')]",
        "//table/tbody/tr[1]//i[contains(@class, 'bi-pencil')]/parent::button",
    ]

    clicked = False
    for xpath in EDIT_XPATHS:
        try:
            click_with_retry(driver, wait, xpath)
            logger.info(f"   ✅ Edit button clicked via: {xpath}")
            clicked = True
            break
        except Exception:
            continue

    if not clicked:
        driver.save_screenshot("so_edit_button_not_found.png")
        raise Exception("Could not locate or click the edit button on Sales Order list page")

    # Wait for the detail/edit view to load
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.footer")))
    time.sleep(2)

    # Approve — also wrapped in retry
    APPROVE_XPATH = "//div[contains(@class, 'footer')]//button[contains(normalize-space(), 'Approve')]"
    try:
        click_with_retry(driver, wait, APPROVE_XPATH)
        logger.info("   ✅ Approve button clicked")
    except Exception as e:
        logger.error(f"❌ Failed to click Approve button: {e}")
        driver.save_screenshot("so_approve_button_error.png")
        raise

    # Wait for SweetAlert and redirect back to list
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container")))
    except TimeoutException:
        pass

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
    time.sleep(2)
    logger.info("🚀 Sales Order Approved Successfully!")


def fill_sales_order_registration(driver, wait, data):
    logger.info("⚡ Starting Sales Order Registration...")

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-select[formcontrolname='customer_ref_id']")))
    time.sleep(1)

    # Base Info Section
    logger.info(f"   Selecting Customer: {data['customer_name']}")
    select_dropdown(driver, wait, value=data['customer_name'], control_name="customer_ref_id", searchable=True)

    try: select_dropdown(driver, wait, value=data['department'], label_text="Department", searchable=False)
    except: select_dropdown(driver, wait, value=data['department'], control_name="department", searchable=False)

    try: select_dropdown(driver, wait, value=data['division'], label_text="Division", searchable=False)
    except: select_dropdown(driver, wait, value=data['division'], control_name="division", searchable=False)

    try: select_dropdown(driver, wait, value=data['location'], label_text="Location", searchable=False)
    except: select_dropdown(driver, wait, value=data['location'], control_name="location", searchable=False)

    try: select_dropdown(driver, wait, value=data['sale_type'], label_text="Type of Sale", searchable=False)
    except: select_dropdown(driver, wait, value=data['sale_type'], control_name="sale_type", searchable=False)

    if 'transaction_date' in data:
        fill_input(driver, wait, data['transaction_date'], control_name="transaction_date")

    fill_input(driver, wait, data['customer_po_number'], control_name="customer_po_number")
    fill_input(driver, wait, data['customer_po_date'], control_name="customer_po_date")
    fill_input(driver, wait, str(data['transportation_charges']), control_name="transportation_charges")

    # Multi-item section
    items = data.get('items', [])
    if not items:
        items = [{
            'item_name': data.get('item_name', ''),
            'quantity': data.get('quantity', 0),
            'rate': data.get('rate', 0),
            'tax_rate': data.get('tax_rate', '0'),
            'expected_delivery_date': data.get('expected_delivery_date', '')
        }]

    logger.info(f"   📦 Processing {len(items)} items...")
    for idx, item in enumerate(items):
        logger.info(f"      ➡️ Setting details for Row {idx + 1}: {item['item_name']}")
        if idx > 0:
            add_item_row(driver, wait, idx)
        fill_item_row(driver, wait, idx, item)

    logger.info("   ⏳ Waiting for ERP to generate conversion rate and totals...")
    time.sleep(3)

    # Submit
    logger.info("📤 Submitting Sales Order form...")
    click_with_retry(driver, wait, "//div[contains(@class, 'footer')]//button[contains(@class, 'submit')]")
    logger.info("   ✅ Submit button clicked")

    # Wait for redirect to list page
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
    time.sleep(3)
    logger.info("🚀 Sales Order Registration Completed Successfully!")

    # Approve
    approve_latest_sales_order(driver, wait)