from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
import os
import logging
from common.helper import select_dropdown, fill_input

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


# ─────────────────────────────────────────────
#  PERMANENT STALE-ELEMENT FIX
# ─────────────────────────────────────────────
def click_with_retry(driver, wait, xpath, retries=5, delay=1.5):
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            element = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            driver.execute_script("arguments[0].click();", element)
            return
        except StaleElementReferenceException as e:
            last_exc = e
            logger.warning(f"   ⚠️ Stale element (attempt {attempt}/{retries}), retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError(f"Element still stale after {retries} attempts [{xpath}]: {last_exc}")


def get_active_overlay(driver, wait, timeout=15):
    """
    Wait for a CDK overlay pane to appear AND contain at least one mat-option.
    Returns the overlay element.
    This scopes all option lookups to the correct pane, avoiding global DOM mismatches.
    """
    # Wait until at least one mat-option is visible inside any overlay pane
    wait_with_timeout = type(wait)(driver, timeout)
    try:
        wait_with_timeout.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane mat-option"))
        )
    except TimeoutException:
        raise TimeoutException("Dropdown opened but no mat-option appeared within the overlay pane.")

    # Return the last (topmost) overlay pane — Angular always appends the active one last
    panes = driver.find_elements(By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane")
    if not panes:
        raise Exception("No overlay pane found in DOM.")
    return panes[-1]


def select_first_so_option(driver, wait):
    """Open the Sales Order dropdown and select the first option."""
    try:
        so_dropdown = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "mat-select[formcontrolname='so_ref_id']")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", so_dropdown)
        driver.execute_script("arguments[0].click();", so_dropdown)

        overlay = get_active_overlay(driver, wait)

        # ---------------------------------------------------------
        # THE FIX: Never use :first-child in Angular. 
        # Grab all options and pick index [0].
        # ---------------------------------------------------------
        options = wait.until(lambda d: overlay.find_elements(By.TAG_NAME, "mat-option"))
        
        if not options:
            raise Exception("Sales Order dropdown opened, but the backend returned 0 options.")
            
        first_option = options[0]
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", first_option)
        driver.execute_script("arguments[0].click();", first_option)
        # ---------------------------------------------------------

        # Close overlay cleanly
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        logger.info("   ✅ Selected first Sales Order")

        # Wait longer for the lots API to respond — this was the real cause of the timeout
        logger.info("   ⏳ Waiting for Lots to load from backend...")
        time.sleep(4)

    except Exception as e:
        logger.error(f"❌ Failed to select Sales Order: {e}")
        driver.save_screenshot("so_selection_error.png")
        raise

    

def select_lots(driver, wait, num_lots):
    """
    Open the Lot dropdown and select the top N lots.
    Options are scoped to the active overlay to avoid global DOM mismatches.
    """
    try:
        lot_dropdown = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "mat-select[formcontrolname='lot_ref_id']")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lot_dropdown)
        driver.execute_script("arguments[0].click();", lot_dropdown)

        # Wait for overlay AND options to actually be present
        overlay = get_active_overlay(driver, wait, timeout=20)
        logger.info(f"   ✅ Lot dropdown opened, selecting top {num_lots} lot(s)...")

        for i in range(num_lots):
            # Re-fetch options every iteration — overlay content can shift after each click
            options = overlay.find_elements(By.CSS_SELECTOR, "mat-option")
            if i >= len(options):
                logger.warning(f"   ⚠️ Only {len(options)} lot(s) available, requested {num_lots}. Selecting all available.")
                break
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", options[i])
            driver.execute_script("arguments[0].click();", options[i])
            logger.info(f"      ✅ Selected Lot {i + 1}")
            time.sleep(0.3)

        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        logger.info(f"   ✅ Finished selecting {num_lots} lot(s)")

        # Let the table rows generate
        time.sleep(2)

    except Exception as e:
        logger.error(f"❌ Failed to select Lots: {e}")
        driver.save_screenshot("lot_selection_error.png")
        raise


def fill_dispatch_note_registration(driver, wait, data):
    logger.info("⚡ Starting Dispatch Note Registration...")

    # --- DATE ---
    if data.get('transaction_date'):
        try:
            date_input = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[formcontrolname='transaction_date']")
            ))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", date_input)
            date_input.send_keys(Keys.CONTROL, 'a')
            date_input.send_keys(Keys.BACKSPACE)
            date_input.send_keys(data['transaction_date'])
            date_input.send_keys(Keys.TAB)
            logger.info(f"  ✅ Filled Transaction Date: {data['transaction_date']}")
        except Exception as e:
            logger.warning(f"  ⚠️ Custom date logic failed: {e}")

    # --- BASE DROPDOWNS ---
    select_dropdown(driver, wait, value=data['customer_name'], control_name="customer_ref_id", searchable=True)
    select_dropdown(driver, wait, value=data['sale_type'], control_name="sales_type_id", searchable=False)
    select_dropdown(driver, wait, value=data['supply_type'], control_name="supply_type_ref_id", searchable=False)
    select_dropdown(driver, wait, value=data['department'], label_text="Department", searchable=False)
    select_dropdown(driver, wait, value=data['division'], label_text="Division", searchable=False)
    select_dropdown(driver, wait, value=data['location'], label_text="Location", searchable=False)
    select_dropdown(driver, wait, value=data['type_of_sale'], label_text="Type of Sale", searchable=False)

    # --- SALES ORDER ---
    select_first_so_option(driver, wait)

    # --- LOTS ---
    items_list = data.get('items', [data])
    select_lots(driver, wait, num_lots=len(items_list))

    # --- ADDITIONAL DETAILS ACCORDION ---
    try:
        click_with_retry(
            driver, wait,
            "//div[contains(@class, 'header accordian')]//strong[contains(text(), 'Additional Details')]"
        )
        logger.info("   ✅ Additional Details accordion expanded")
        time.sleep(1)
    except Exception as e:
        logger.warning(f"⚠️ Could not open accordion: {e}")

    # --- TRANSPORTER / VEHICLE / DISTANCE ---
    fill_input(driver, wait, data['transporter_name'], control_name="transporter_name")
    fill_input(driver, wait, data['vehicle_no'], control_name="vehicle_no")
    fill_input(driver, wait, str(data['distance']), control_name="distance")

    # --- MULTI-ITEM GRID (Tax & Bags) ---
    logger.info(f"   📦 Processing Grid Details for {len(items_list)} items...")

    for idx, item in enumerate(items_list):
        item_name = item.get('item_name', '')

        if item_name in {"Soyabean", "Turmeric", "Chana"}:
            tax_rate = "5"
        elif item_name in {"Tur-Red", "Maize-Yellow"}:
            tax_rate = "0"
        else:
            tax_rate = str(item.get('tax_rate', '0'))

        # Tax Rate — re-fetch list every row (avoids stale refs after prior row interactions)
        try:
            tax_dropdowns = driver.find_elements(By.CSS_SELECTOR, "mat-select[formcontrolname='tax_rate']")
            if idx < len(tax_dropdowns):
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tax_dropdowns[idx])
                driver.execute_script("arguments[0].click();", tax_dropdowns[idx])
                overlay = get_active_overlay(driver, wait)
                opt = overlay.find_element(
                    By.XPATH, f".//mat-option[contains(normalize-space(.), '{tax_rate}')]"
                )
                driver.execute_script("arguments[0].click();", opt)
                # Wait for overlay to close before next interaction
                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane mat-option")))
                logger.info(f"      ✅ Row {idx+1}: Tax Rate = {tax_rate}")
        except Exception as e:
            logger.warning(f"      ⚠️ Row {idx+1}: Tax Rate failed: {e}")

        # Bags — re-fetch list every row
        try:
            bag_inputs = driver.find_elements(By.CSS_SELECTOR, "input[formcontrolname='dispatch_no_of_bags']")
            if idx < len(bag_inputs):
                bags = str(item.get('no_of_bags', data.get('no_of_bags', 10)))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", bag_inputs[idx])
                bag_inputs[idx].send_keys(Keys.CONTROL, 'a')
                bag_inputs[idx].send_keys(Keys.BACKSPACE)
                bag_inputs[idx].send_keys(bags)
                logger.info(f"      ✅ Row {idx+1}: No of Bags = {bags}")
        except Exception as e:
            logger.warning(f"      ⚠️ Row {idx+1}: Bags failed: {e}")

    # --- FILE UPLOAD ---
    if data.get('attachment_file'):
        try:
            file_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='file'][id^='bank_upload']")
            ))
            abs_path = os.path.abspath(data['attachment_file'])
            file_input.send_keys(abs_path)
            logger.info(f"   ✅ File uploaded: {abs_path}")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ Failed to upload file: {e}")

    time.sleep(2)

    # --- SUBMIT ---
    logger.info("📤 Submitting Dispatch Note...")
    SUBMIT_XPATH = "//div[contains(@class, 'footer')]//button[contains(@class, 'submit')]"
    click_with_retry(driver, wait, SUBMIT_XPATH)
    logger.info("   ✅ Submit button clicked")

    # Wait for redirect to list page
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
        logger.info("🚀 Dispatch Note Registration Completed Successfully!")
        time.sleep(3)
    except TimeoutException:
        errors = driver.find_elements(By.CSS_SELECTOR, "mat-error")
        error_msgs = [e.text for e in errors if e.text.strip()]
        if error_msgs:
            logger.error(f"❌ Validation errors: {error_msgs}")
            driver.save_screenshot("dispatch_validation_errors.png")
            raise Exception(f"Form validation failed: {error_msgs}")
        else:
            logger.warning("⚠️ No redirect and no errors. Retrying submit...")
            click_with_retry(driver, wait, SUBMIT_XPATH)
            time.sleep(3)
            if driver.find_elements(By.CSS_SELECTOR, "table.mat-mdc-table"):
                logger.info("🚀 Dispatch Note Registration Completed Successfully!")
            else:
                driver.save_screenshot("dispatch_submit_failed.png")
                raise Exception("Submission failed: page did not redirect and no validation errors.")