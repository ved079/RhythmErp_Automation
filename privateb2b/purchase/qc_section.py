from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
import time
import logging
from common.helper import select_dropdown, click_submit, fill_input

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


# ─────────────────────────────────────────────
#  PERMANENT STALE-ELEMENT FIX
#  Always re-locates inside the loop — never
#  reuses a reference across iterations.
# ─────────────────────────────────────────────
def click_with_retry(driver, wait, xpath, retries=5, delay=1.5):
    """Find and JS-click an element by XPath, retrying on StaleElementReferenceException."""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            # Re-locate right before clicking — presence_of_element_located
            # might itself return a stale ref if the page re-rendered during the wait
            element = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            driver.execute_script("arguments[0].click();", element)
            return  # success
        except StaleElementReferenceException as e:
            last_exc = e
            logger.warning(f"   ⚠️ Stale element (attempt {attempt}/{retries}), retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError(f"Element still stale after {retries} attempts [{xpath}]: {last_exc}")


def wait_for_sweetalert_to_close(driver, wait, timeout=10):
    """Wait for any SweetAlert2 overlay to disappear."""
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container")))
        logger.info("   ✅ SweetAlert overlay closed.")
    except TimeoutException:
        driver.save_screenshot("sweetalert_still_open.png")
        logger.warning("   ⚠️ SweetAlert overlay still visible; continuing anyway.")


def select_first_gate_pass_option(driver, wait):
    """Select the first (latest) Gate Pass from the dropdown."""
    try:
        logger.info("➡️ Selecting Gate Pass (first option)")
        dropdown = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "mat-select[formcontrolname='gate_pass_ref_id']")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        driver.execute_script("arguments[0].click();", dropdown)

        overlay = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")
        ))
        wait.until(EC.visibility_of(overlay))

        first_option = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//mat-option[1]//span")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", first_option)
        driver.execute_script("arguments[0].click();", first_option)
        logger.info("   ✅ Selected first Gate Pass option")
        time.sleep(0.5)
    except Exception as e:
        logger.error(f"❌ Failed to select Gate Pass: {e}")
        driver.save_screenshot("gate_pass_error.png")
        raise


def fill_qc_parameters_modal(driver, wait, parameter_dict, item_index):
    """
    Open the QC parameter modal for a specific row, fill actual values,
    and submit the modal.
    """
    logger.info(f"⚡ Filling QC parameters for Item {item_index + 1} (via modal)...")

    row_xpath = f"//tbody[contains(@class, 'main_tbody')]/tr[{item_index + 1}]"
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))
    except TimeoutException:
        logger.error(f"❌ Row {item_index + 1} not found")
        driver.save_screenshot(f"qc_row_{item_index+1}_not_found.png")
        raise

    # 1. Click the "Enter Parameter" button — use retry in case row re-renders
    button_xpath = f"{row_xpath}//button[contains(text(), 'Enter Parameter')]"
    try:
        click_with_retry(driver, wait, button_xpath)
        logger.info(f"   ✅ 'Enter Parameter' button {item_index + 1} clicked")
    except Exception as e:
        logger.error(f"❌ Could not click 'Enter Parameter' for row {item_index + 1}: {e}")
        driver.save_screenshot(f"enter_parameter_button_error_row_{item_index + 1}.png")
        raise

    # 2. Wait for the modal to appear
    time.sleep(2)
    try:
        modal = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")
        ))
    except TimeoutException:
        logger.error("❌ Modal did not appear")
        driver.save_screenshot("modal_not_appeared.png")
        raise

    # 3. Fill each parameter row inside the modal
    rows = modal.find_elements(By.XPATH, ".//tr[.//input[@formcontrolname='actual_value']]")
    if not rows:
        logger.warning("   ⚠️ No parameter rows found inside modal.")
    else:
        for row in rows:
            try:
                param_el = row.find_element(By.CSS_SELECTOR, ".mat-mdc-select-min-line")
                param_name = param_el.get_attribute("textContent").strip()
                logger.info(f"   Found parameter UI text: '{param_name}'")

                matched_val = None
                for dict_key, dict_val in parameter_dict.items():
                    if dict_key.lower() in param_name.lower():
                        matched_val = str(dict_val)
                        break

                if matched_val:
                    input_field = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='actual_value']")
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_field)
                    driver.execute_script("arguments[0].click();", input_field)
                    input_field.clear()
                    time.sleep(0.2)
                    input_field.send_keys(matched_val)
                    logger.info(f"   ✅ Set {param_name} = {matched_val}")
                    time.sleep(0.5)
                else:
                    logger.warning(f"   ⚠️ No match in dictionary for '{param_name}' – skipped")
            except StaleElementReferenceException:
                logger.warning("   ⚠️ Stale row inside modal — skipping row")
            except Exception as e:
                logger.error(f"   ❌ Error filling row: {e}")
                driver.save_screenshot("qc_param_modal_fill_error.png")

    # 4. Click "Ok" inside the modal
    try:
        ok_btn = modal.find_element(By.XPATH, ".//button[contains(text(), 'Ok')]")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", ok_btn)
        driver.execute_script("arguments[0].click();", ok_btn)
        logger.info("   ✅ Modal submitted (Ok clicked)")
    except Exception as e:
        logger.error(f"❌ Could not click Ok button in modal: {e}")
        driver.save_screenshot("modal_ok_button_error.png")
        raise

    # 5. Wait for the modal to close
    try:
        wait.until(EC.invisibility_of_element_located(
            (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane")
        ))
        logger.info("   ✅ Modal closed")
        time.sleep(1)
    except TimeoutException:
        logger.warning("⚠️ Modal did not close; continuing anyway.")


def approve_latest_qc(driver, wait):
    """Find the latest QC in the list, click its edit button, and approve it."""
    logger.info("⚡ Approving the latest QC...")

    # Wait for the table and let Angular finish rendering
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
    time.sleep(2)

    rows = driver.find_elements(By.CSS_SELECTOR, "table.mat-mdc-table tbody tr")
    logger.info(f"   Number of rows in QC list: {len(rows)}")
    if not rows:
        driver.save_screenshot("qc_list_empty.png")
        raise Exception("QC list is empty after submission")

    # Try each XPath selector with the retry-click utility
    EDIT_XPATHS = [
        "//table/tbody/tr[1]//button[contains(@class, 'tblActnBtn')]//i[contains(@class, 'bi-pencil')]/..",
        "//table/tbody/tr[1]//button[.//i[contains(@class, 'bi-pencil')]]",
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
            continue  # try next selector

    if not clicked:
        driver.save_screenshot("qc_edit_button_not_found.png")
        raise Exception("Could not locate or click the edit button on QC list page")

    wait_for_sweetalert_to_close(driver, wait)
    time.sleep(2)

    # Approve — also wrapped in retry
    APPROVE_XPATH = "//button[contains(text(), 'Approve')]"
    try:
        click_with_retry(driver, wait, APPROVE_XPATH)
        logger.info("   ✅ Approve button clicked")
    except Exception as e:
        logger.error(f"❌ Failed to click Approve button: {e}")
        driver.save_screenshot("qc_approve_button_error.png")
        raise

    wait_for_sweetalert_to_close(driver, wait)
    time.sleep(2)
    logger.info("🚀 QC approved successfully!")


def fill_qc_registration(driver, wait, data):
    logger.info("⚡ Starting QC Registration...")

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='supplier_ref_id']")))
    time.sleep(0.5)

    # 1. Set the Date
    logger.info(f"   📅 Setting QC Transaction Date to: {data.get('transaction_date', 'Not Provided')}")
    if 'transaction_date' in data:
        fill_input(driver, wait, data['transaction_date'], control_name="transaction_date")

    # 2. Supplier selection
    logger.info(f"   ➡️ Forcing Supplier Selection for: {data['supplier']}")
    try:
        supplier_drop = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "mat-select[formcontrolname='supplier_ref_id']")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", supplier_drop)
        driver.execute_script("arguments[0].click();", supplier_drop)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        time.sleep(1)

        supplier_name_only = data['supplier'].split('-')[0].strip()

        try:
            search_box = driver.find_element(By.CSS_SELECTOR, ".cdk-overlay-pane input")
            search_box.send_keys(supplier_name_only)
            time.sleep(1)
        except Exception:
            pass

        options = driver.find_elements(By.CSS_SELECTOR, "mat-option")
        clicked = False
        for opt in options:
            if supplier_name_only.lower() in opt.get_attribute("textContent").lower():
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opt)
                driver.execute_script("arguments[0].click();", opt)
                clicked = True
                logger.info(f"      ✅ Supplier clicked: {supplier_name_only}")
                break

        if not clicked:
            raise Exception(f"Could not find '{supplier_name_only}' in the dropdown list.")

        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        except Exception:
            pass
    except Exception as e:
        logger.error(f"❌ CRITICAL: Failed to set Supplier: {e}")
        driver.save_screenshot("qc_supplier_fail.png")
        raise

    # 3. Item type
    select_dropdown(driver, wait, value=data['item_type'], control_name="item_type_ref_id", searchable=False)

    # 4. Gate Pass (auto-populates items table)
    select_first_gate_pass_option(driver, wait)
    time.sleep(3)

    # 5. Transaction Currency
    select_dropdown(driver, wait, value="INR", control_name="txn_currency", searchable=False)

    # 6. Expand QC Details accordion
    try:
        accordion = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='header accordian']//strong[contains(text(), 'QC Details')]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", accordion)
        driver.execute_script("arguments[0].click();", accordion)
        logger.info("   ✅ QC Details accordion expanded")
        time.sleep(1)
    except Exception:
        logger.info("   QC Details accordion may already be expanded")

    # 7. Multi-item QC loop
    logger.info(f"   🔬 Processing QC Parameters for {len(data['items'])} items...")
    for index, item_data in enumerate(data['items']):
        logger.info(f"      ➡️ Doing QC for: {item_data['item']}")
        fill_qc_parameters_modal(driver, wait, item_data['qc_parameters'], index)

    # 8. Submit
    logger.info("📤 Submitting the QC form...")
    click_submit(driver, wait)

    try:
        wait.until(EC.invisibility_of_element_located(
            (By.CSS_SELECTOR, ".swal2-container, .cdk-overlay-backdrop, .ngx-spinner-overlay")
        ))
    except Exception:
        pass

    logger.info("   ⏳ Waiting to return to QC List page...")
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
        logger.info("   ✅ Returned to QC List page.")
    except Exception as e:
        logger.error("❌ CRITICAL: Did not return to the QC list page. Cannot approve QC.")
        driver.save_screenshot("qc_submit_stuck.png")
        raise

    time.sleep(2)
    logger.info("🚀 QC Registration Completed Successfully!")

    # 9. Approve the newly created QC
    approve_latest_qc(driver, wait)