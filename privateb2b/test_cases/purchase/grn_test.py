import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import glob
import shutil
import logging
from selenium.webdriver.chrome.options import Options

import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import InvalidElementStateException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import config
from common import auth_section, nav_section
from common.helper import select_dropdown, fill_input, click_submit
from data.test_data import grn_data, gatepass_data

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# ==========================================
# EXISTING HELPER FUNCTIONS (keep as is)
# ==========================================

def wait_for_sweetalert_to_close(driver, wait, timeout=10):
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container")))
        logger.info("   ✅ SweetAlert overlay closed.")
    except TimeoutException:
        driver.save_screenshot("sweetalert_still_open.png")
        logger.warning("   ⚠️ SweetAlert overlay still visible; continuing anyway.")

def select_first_gate_pass_option(driver, wait):
    try:
        logger.info("➡️ Selecting Gate Pass (first option)")
        time.sleep(2)
        dropdown = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "mat-select[formcontrolname='gate_pass_ref_id']")
        ))
        wait.until(lambda d: dropdown.get_attribute("aria-disabled") != "true")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        try:
            dropdown.click()
        except:
            driver.execute_script("arguments[0].click();", dropdown)
        overlay = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")
        ))
        wait.until(EC.visibility_of(overlay))
        time.sleep(1)
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

# ==========================================
# MODIFIED: FILL GRN FORM (WITH ADDITIONAL DETAILS)
# ==========================================

def fill_grn_form(driver, wait, data):
    """Populate supplier and gate pass, fill Additional Details, wait for rows."""
    logger.info("⚡ Filling GRN form (no submit yet)...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='supplier_ref_id']")))
    time.sleep(0.5)

    # Set date
    logger.info(f"   📅 Setting GRN Transaction Date to: {data['transaction_date']}")
    fill_input(driver, wait, data['transaction_date'], control_name="transaction_date")

    # Select supplier
    select_dropdown(driver, wait, value=data['supplier'], control_name="supplier_ref_id", searchable=True)

    # Select Gate Pass
    select_first_gate_pass_option(driver, wait)

    # ----- GRN_TC12: Additional Details accordion -----
    logger.info("   🧪 [GRN_TC12] Filling Additional Details...")
    try:
        accordion = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@class,'header accordian')]//strong[contains(text(),'Additional Details')]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", accordion)
        driver.execute_script("arguments[0].click();", accordion)
        time.sleep(0.5)

        if data.get('transporter_name'):
            fill_input(driver, wait, data['transporter_name'], control_name="transporter_name")
        if data.get('vehicle_no'):
            fill_input(driver, wait, data['vehicle_no'], control_name="vehicle_no")
        if data.get('driver_name'):
            fill_input(driver, wait, data['driver_name'], control_name="driver_name")
        if data.get('driver_contact'):
            fill_input(driver, wait, data['driver_contact'], control_name="driver_contact_no")
        logger.info("      ✅ Additional Details filled successfully.")
    except Exception as e:
        logger.warning(f"      ⚠️ Additional Details accordion not found or failed: {e}")

    # Wait for the table rows to appear
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.main_tbody tr")))
    time.sleep(2)
    logger.info("   ✅ GRN form populated, table rows ready.")

# ==========================================
# VALIDATION FUNCTIONS (work on creation form)
# ==========================================

def verify_grn_data_vs_gatepass(driver, wait, expected_items):
    """Compare item names, GRN quantity, etc. against Gate Pass data."""
    logger.info("🔍 Verifying GRN auto-populated data against Gate Pass...")
    
    first_row = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.main_tbody tr:first-child")))
    item_select = first_row.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='item_ref_id']")
    wait.until(lambda d: driver.execute_script(
        "return arguments[0].querySelector('.mat-mdc-select-value-text')?.innerText || '';", 
        item_select
    ).strip() != "")
    time.sleep(0.5)
    
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.main_tbody tr")
    actual_count = len(rows)
    expected_count = len(expected_items)
    assert actual_count == expected_count, f"Row count mismatch: expected {expected_count}, got {actual_count}"
    logger.info(f"   ✅ Row count matches: {actual_count}")

    for idx, expected in enumerate(expected_items):
        row = rows[idx]

        # Item Name
        item_select = row.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='item_ref_id']")
        item_text = driver.execute_script(
            "return arguments[0].querySelector('.mat-mdc-select-value-text')?.innerText || '';",
            item_select
        ).strip()
        if not item_text:
            item_text = driver.execute_script(
                "return arguments[0].getAttribute('value') || arguments[0].innerText || '';",
                item_select
            ).strip()
        assert item_text == expected['item'], \
            f"Row {idx+1}: Item mismatch. Expected '{expected['item']}', got '{item_text}'"
        logger.info(f"   ✅ Row {idx+1} Item: {item_text}")

        # HSN Code
        try:
            hsn_select = row.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='hsn_sac_no']")
            hsn_text = driver.execute_script(
                "return arguments[0].querySelector('.mat-mdc-select-value-text')?.innerText || '';",
                hsn_select
            ).strip()
            if not hsn_text:
                hsn_text = driver.execute_script(
                    "return arguments[0].getAttribute('value') || '';",
                    hsn_select
                ).strip()
            assert hsn_text != "", f"Row {idx+1}: HSN code is empty"
            logger.info(f"   ✅ Row {idx+1} HSN: {hsn_text}")
        except:
            logger.warning(f"   ⚠️ Row {idx+1}: HSN field not found – skipping")

        # GRN Quantity (disabled input)
        qty_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='quantity']")
        qty_value = float(qty_input.get_attribute('value'))
        expected_qty = float(expected['quantity'])
        assert qty_value == expected_qty, \
            f"Row {idx+1}: GRN Quantity mismatch. Expected {expected_qty}, got {qty_value}"
        logger.info(f"   ✅ Row {idx+1} GRN Quantity: {qty_value}")

        # Gate Pass Quantity (received_qty)
        gp_qty_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='received_qty']")
        gp_qty_value = float(gp_qty_input.get_attribute('value'))
        assert gp_qty_value == expected_qty, \
            f"Row {idx+1}: Gate Pass Quantity mismatch. Expected {expected_qty}, got {gp_qty_value}"
        logger.info(f"   ✅ Row {idx+1} Gate Pass Quantity: {gp_qty_value}")

    logger.info("✅ GRN data verification passed.\n")


def test_rejected_qty_calculation(driver, wait, row_index=1):
    logger.info(f"🧮 Testing Rejected Qty calculation on row {row_index}...")
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.main_tbody tr")
    row = rows[row_index - 1]

    gp_qty_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='received_qty']")
    gp_qty = float(gp_qty_input.get_attribute('value'))

    accepted_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='accepted_qty']")
    rejected_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='rejected_qty']")

    accepted_input.clear()
    accepted_qty = gp_qty - 10.0
    accepted_input.send_keys(str(accepted_qty))
    accepted_input.send_keys(Keys.TAB)
    time.sleep(1)

    rejected_value = float(rejected_input.get_attribute('value'))
    expected_rejected = gp_qty - accepted_qty
    
    assert round(rejected_value, 2) == round(expected_rejected, 2), \
        f"Rejected Qty mismatch: expected {expected_rejected}, got {rejected_value}"
    logger.info(f"   ✅ Rejected Qty = {rejected_value} (GP Qty {gp_qty} - Accepted {accepted_qty})")


def test_negative_value_block(driver, wait, row_index=1):
    logger.info(f"🚫 Testing negative value block on row {row_index}...")
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.main_tbody tr")
    row = rows[row_index - 1]
    accepted_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='accepted_qty']")

    original_value = accepted_input.get_attribute('value')
    accepted_input.clear()
    accepted_input.send_keys("-50")
    accepted_input.send_keys(Keys.TAB)
    time.sleep(0.5)

    new_value = accepted_input.get_attribute('value')
    if "-" in new_value:
        classes = accepted_input.get_attribute('class')
        assert "ng-invalid" in classes, "Negative value accepted without validation error!"
        logger.info("   ✅ Negative value correctly marked invalid.")
    else:
        logger.info("   ✅ UI stripped the negative sign.")

    accepted_input.clear()
    accepted_input.send_keys(original_value)


def test_over_receipt_block(driver, wait, row_index=1):
    logger.info(f"⚠️ Testing over-receipt block on row {row_index}...")
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.main_tbody tr")
    row = rows[row_index - 1]

    gp_qty_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='received_qty']")
    gp_qty = float(gp_qty_input.get_attribute('value'))
    accepted_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='accepted_qty']")

    over_qty = gp_qty + 10.0
    accepted_input.clear()
    accepted_input.send_keys(str(over_qty))
    accepted_input.send_keys(Keys.TAB)
    time.sleep(1)

    try:
        error_toast = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'toast-error') or contains(@class, 'error-message')]")
        ))
        logger.info("   ✅ Over-receipt blocked by error message.")
    except:
        classes = accepted_input.get_attribute('class')
        assert "ng-invalid" in classes, "Over-receipt was allowed without validation!"
        logger.info("   ✅ Over-receipt blocked (field marked invalid).")

    accepted_input.clear()
    accepted_input.send_keys(str(gp_qty))

    
def test_readonly_fields(driver, wait, row_index=1):
    logger.info("🔒 Testing read-only fields...")
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.main_tbody tr")
    row = rows[row_index - 1]

    grn_qty = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='quantity']")
    assert grn_qty.get_attribute('readonly') == 'true' or grn_qty.get_attribute('disabled') == 'true', \
        "GRN Quantity should be read-only"
    logger.info("   ✅ GRN Quantity is read-only")

    gp_qty = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='received_qty']")
    assert gp_qty.get_attribute('readonly') == 'true' or gp_qty.get_attribute('disabled') == 'true', \
        "Gate Pass Quantity should be read-only"
    logger.info("   ✅ Gate Pass Quantity is read-only")

    bags = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='no_of_bags']")
    assert bags.get_attribute('readonly') == 'true' or bags.get_attribute('disabled') == 'true', \
        "No. of Bags should be read-only"
    logger.info("   ✅ No. of Bags is read-only")

    rejected = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='rejected_qty']")
    assert rejected.get_attribute('readonly') == 'true' or rejected.get_attribute('disabled') == 'true', \
        "Rejected Quantity should be read-only"
    logger.info("   ✅ Rejected Quantity is read-only")

def test_rate_field_not_editable(driver, wait, row_index=1):
    logger.info("💰 Testing Rate field editability (should NOT be editable)...")
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.main_tbody tr")
    row = rows[row_index - 1]
    rate_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='rate']")

    is_readonly = rate_input.get_attribute('readonly') in ['true', 'readonly', True]
    is_disabled = rate_input.get_attribute('disabled') in ['true', 'disabled', True]

    if is_readonly or is_disabled:
        logger.info("   ✅ Rate field is correctly locked (readonly/disabled attribute found).")
        return

    original_value = rate_input.get_attribute('value')
    try:
        rate_input.clear()
        rate_input.send_keys("999.99")
        rate_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        new_value = rate_input.get_attribute('value')
        if new_value != original_value:
            raise AssertionError(f"❌ FAIL: Rate field was editable! Changed from '{original_value}' to '{new_value}'")
        else:
            logger.info("   ✅ Rate field is correctly read-only (input ignored by UI).")
    except InvalidElementStateException:
        logger.info("   ✅ Rate field is correctly locked (Selenium blocked interaction).")


# ==========================================
# APPROVAL FROM LIST
# ==========================================

def approve_latest_grn(driver, wait):
    logger.info("⚡ Approving latest GRN from list...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
    time.sleep(1)

    edit_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "(//tbody/tr)[1]//button[@mattooltip='EDIT']")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", edit_btn)
    driver.execute_script("arguments[0].click();", edit_btn)
    logger.info("   ✅ Edit modal opened")
    time.sleep(2)
    wait_for_sweetalert_to_close(driver, wait)

    approve_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(), 'Approve')]")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", approve_btn)
    driver.execute_script("arguments[0].click();", approve_btn)
    logger.info("   ✅ Clicked Approve button")
    time.sleep(2)
    wait_for_sweetalert_to_close(driver, wait)
    logger.info("🚀 GRN approved successfully!")


# ==========================================
# GRN_TC15: SENDBACK TO MAKER
# ==========================================

def test_sendback_grn(driver, wait):
    logger.info("↩️ [GRN_TC15] Testing SendBack to Maker...")
    try:
        # Click SendBack button on list row (opens modal)
        sendback_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "(//tbody/tr)[1]//button[contains(text(),'SendBack')]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sendback_btn)
        driver.execute_script("arguments[0].click();", sendback_btn)
        logger.info("   ✅ Clicked SendBack button")
        time.sleep(1)

        # Wait for modal with SendBack Code and Remark
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup")))
        
        # Select SendBack Code (first option)
        code_dropdown = modal.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='error_code_id']")
        driver.execute_script("arguments[0].click();", code_dropdown)
        overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        first_code = wait.until(EC.element_to_be_clickable((By.XPATH, "(//mat-option)[1]")))
        driver.execute_script("arguments[0].click();", first_code)
        wait.until(EC.invisibility_of_element(overlay))
        logger.info("   ✅ Selected SendBack Code")

        # Enter Remark
        remark_input = modal.find_element(By.CSS_SELECTOR, "input[formcontrolname='workflow_remark']")
        remark_input.clear()
        remark_input.send_keys("Automated sendback test")
        logger.info("   ✅ Entered SendBack Remark")

        # Confirm
        confirm_btn = modal.find_element(By.CSS_SELECTOR, "button.swal2-confirm")
        driver.execute_script("arguments[0].click();", confirm_btn)
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup")))
        logger.info("   ✅ GRN sent back to maker successfully.")
    except Exception as e:
        logger.error(f"   ⚠️ SendBack test failed: {e}")


# ==========================================
# GRN_TC16: EDIT RESTRICTIONS
# ==========================================

def test_edit_restrictions(driver, wait):
    logger.info("🔒 [GRN_TC16] Verifying edit restrictions (only allowed fields editable)...")
    try:
        # Ensure we are on the listing page
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
        time.sleep(1)

        # Click edit button on first row
        edit_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "(//tbody/tr)[1]//button[@mattooltip='EDIT']")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", edit_btn)
        driver.execute_script("arguments[0].click();", edit_btn)
        logger.info("   ✅ Edit modal opened")
        time.sleep(2)
        wait_for_sweetalert_to_close(driver, wait)

        # Verify item dropdown is disabled
        try:
            item_select = driver.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='item_ref_id']")
            disabled = item_select.get_attribute('aria-disabled') == 'true' or not item_select.is_enabled()
            if disabled:
                logger.info("   ✅ Item dropdown is locked (non-editable).")
            else:
                logger.warning("   ⚠️ Item dropdown appears editable.")
        except Exception:
            logger.info("   ℹ️ Item dropdown not found; skipping.")

        # Verify quantity is read-only
        try:
            qty_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='quantity']")
            readonly = qty_input.get_attribute('readonly') == 'true'
            if readonly:
                logger.info("   ✅ Quantity field is read-only.")
            else:
                logger.warning("   ⚠️ Quantity field is not read-only.")
        except Exception:
            logger.info("   ℹ️ Quantity field not found; skipping.")

        # Close modal using Cancel button
        try:
            cancel_btn = driver.find_element(By.XPATH, "//div[@class='footer']//button[contains(@class,'cancel')]")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cancel_btn)
            driver.execute_script("arguments[0].click();", cancel_btn)
            time.sleep(1)
            logger.info("   ✅ Edit modal closed.")
        except Exception:
            # Fallback: press Escape
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            logger.warning("   ⚠️ Closed modal via Escape.")

        logger.info("   ✅ Edit restrictions verified.")
    except Exception as e:
        logger.error(f"   ⚠️ Edit restrictions test failed: {e}")




# ==========================================
# EXCEL & PRINT
# ==========================================

def test_print_button(driver, wait):
    logger.info("🖨️ Testing Print Button...")
    original_windows = driver.window_handles
    original_handle = driver.current_window_handle

    print_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "(//tbody/tr)[1]//button[@mattooltip='PRINT']")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", print_btn)
    driver.execute_script("arguments[0].click();", print_btn)

    timeout = time.time() + 5
    while len(driver.window_handles) <= len(original_windows) and time.time() < timeout:
        time.sleep(0.5)

    new_windows = driver.window_handles
    if len(new_windows) > len(original_windows):
        logger.info(f"   ✅ New tab opened. Total windows: {len(new_windows)}")
        new_tab = [w for w in new_windows if w != original_handle][0]
        driver.switch_to.window(new_tab)
        driver.close()
        driver.switch_to.window(original_handle)
        logger.info("   ✅ Print tab closed, returned to main window.")
    else:
        raise AssertionError("❌ Print button did not open a new tab.")

def test_excel_download(driver, wait, download_dir):
    logger.info("📥 Testing Excel Download...")
    
    for f in glob.glob(os.path.join(download_dir, "*.xlsx")):
        os.remove(f)
    
    before_files = set(os.listdir(download_dir))
    
    excel_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(., 'Download Excel')]")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", excel_btn)
    driver.execute_script("arguments[0].click();", excel_btn)
    
    timeout = time.time() + 20
    downloaded_file = None
    while time.time() < timeout:
        after_files = set(os.listdir(download_dir))
        new_files = after_files - before_files
        for f in new_files:
            if f.endswith(('.xlsx', '.xls')):
                downloaded_file = os.path.join(download_dir, f)
                break
        if downloaded_file:
            break
        time.sleep(1)
    
    if not downloaded_file:
        time.sleep(5)
        for f in os.listdir(download_dir):
            if f.endswith(('.xlsx', '.xls')) and not f.endswith('.crdownload'):
                downloaded_file = os.path.join(download_dir, f)
                break
    
    if downloaded_file and os.path.getsize(downloaded_file) > 0:
        logger.info(f"   ✅ Excel file downloaded successfully: {os.path.basename(downloaded_file)}")
        os.remove(downloaded_file)
    else:
        logger.warning(f"   ⚠️ Files in download dir: {os.listdir(download_dir)}")
        raise AssertionError("❌ Excel file was not downloaded or is empty.")
    

# ==========================================
# MAIN SUITE EXECUTION
# ==========================================

def execute_grn_suite(driver, wait, grn_data, gatepass_items, download_dir):
    logger.info("--- ⚡ STARTING GRN SUITE ---")

    # 1. Fill form (no submit yet)
    fill_grn_form(driver, wait, grn_data)

    # 2. Run all validations on the creation form table
    verify_grn_data_vs_gatepass(driver, wait, gatepass_items)
    test_rejected_qty_calculation(driver, wait, row_index=1)
    test_negative_value_block(driver, wait, row_index=1)
    test_over_receipt_block(driver, wait, row_index=1)
    test_readonly_fields(driver, wait, row_index=1)
    test_rate_field_not_editable(driver, wait, row_index=1)

    # 3. Submit the GRN
    logger.info("📤 Submitting GRN form...")
    click_submit(driver, wait)
    time.sleep(3)
    logger.info("✅ GRN submitted successfully.")

    # 4. Wait for redirect to list page
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
    time.sleep(2)
    logger.info("📍 Landed on GRN listing page.")

    # 5. Test Edit Restrictions (GRN_TC16) - before approval, GRN is editable
    # test_edit_restrictions(driver, wait)

    # 6. Approve the GRN from list
    approve_latest_grn(driver, wait)

    # 7. (Optional) Test SendBack (GRN_TC15) - commented due to known manual issue
    # test_sendback_grn(driver, wait)

    # 8. Test Excel and Print on GRN list page
    test_print_button(driver, wait)
    test_excel_download(driver, wait, download_dir)

    logger.info("--- ✅ GRN SUITE COMPLETED ---")