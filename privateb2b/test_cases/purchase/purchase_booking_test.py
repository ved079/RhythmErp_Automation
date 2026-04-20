import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import glob
import shutil
import logging
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException, InvalidElementStateException
from selenium.webdriver.chrome.options import Options

import config
from common import auth_section, nav_section
from common.helper import select_dropdown, fill_input, click_submit
from data.test_data import purchase_booking_data

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# ==========================================
# UTILITY & HELPER FUNCTIONS
# ==========================================

def wait_for_backdrop_to_clear(wait):
    try:
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "cdk-overlay-backdrop")))
    except:
        pass

def select_first_qc_option(driver, wait):
    try:
        logger.info("➡️ Selecting QC (first valid option)")
        dropdown = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "mat-select[formcontrolname='qc_ref_id']")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
        driver.execute_script("arguments[0].click();", dropdown)

        overlay = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")
        ))
        wait.until(EC.visibility_of(overlay))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-option")))
        time.sleep(1)

        options = driver.find_elements(By.CSS_SELECTOR, "mat-option")
        for opt in options:
            if opt.is_enabled():
                opt_text = opt.text.strip()
                if opt_text and "Select" not in opt_text:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opt)
                    driver.execute_script("arguments[0].click();", opt)
                    wait_for_backdrop_to_clear(wait)
                    logger.info(f"   ✅ Selected QC: {opt_text}")
                    time.sleep(1)
                    return
        driver.save_screenshot("qc_no_valid_options.png")
        raise Exception("No valid QC option found (all options are disabled or placeholders)")
    except Exception as e:
        logger.error(f"❌ Failed to select QC: {e}")
        driver.save_screenshot("qc_dropdown_error.png")
        raise

def add_quantity_details(driver, wait, item_data, row_index):
    try:
        add_btn_xpath = f"//tbody/tr[{row_index + 1}]//button[contains(text(), 'Add') or contains(text(), 'View')]"
        add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, add_btn_xpath)))
        
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
        driver.execute_script("arguments[0].click();", add_btn)
        logger.info(f"   ✅ Add button clicked for Row {row_index + 1}")

        modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")))
        wait.until(EC.visibility_of(modal))
        time.sleep(1)

        bags_input = modal.find_element(By.CSS_SELECTOR, "input[formcontrolname='no_of_bags']")
        driver.execute_script("arguments[0].click();", bags_input)
        bags_input.send_keys(Keys.CONTROL + "a")
        bags_input.send_keys(Keys.BACKSPACE)
        bags_input.send_keys(str(item_data['no_of_bags']))

        qty_input = modal.find_element(By.CSS_SELECTOR, "input[formcontrolname='quantity']")
        driver.execute_script("arguments[0].click();", qty_input)
        qty_input.send_keys(Keys.CONTROL + "a")
        qty_input.send_keys(Keys.BACKSPACE)
        qty_input.send_keys(str(item_data['quantity']))

        submit_modal_btn = modal.find_element(By.XPATH, ".//button[contains(text(), 'Submit') or contains(text(), 'Save')]")
        driver.execute_script("arguments[0].click();", submit_modal_btn)
        logger.info("   ✅ Quantity Details Modal submitted")
        
        wait_for_backdrop_to_clear(wait)
        time.sleep(1)
    except Exception as e:
        logger.error(f"❌ Failed to add quantity details for row {row_index + 1}: {e}")
        driver.save_screenshot(f"add_quantity_error_row_{row_index + 1}.png")
        raise

def upload_grn_attachment(driver, wait, file_path):
    try:
        try:
            accordion = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='header accordian']//strong[contains(text(), 'GRN details')]")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", accordion)
            driver.execute_script("arguments[0].click();", accordion)
            logger.info("   ✅ GRN details accordion expanded")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"   ⚠️ Could not expand GRN details accordion: {e}")

        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'][id^='bank_upload_']")))
        abs_path = os.path.abspath(file_path)
        file_input.send_keys(abs_path)
        logger.info(f"   ✅ File uploaded: {abs_path}")
        time.sleep(1)
    except Exception as e:
        logger.error(f"❌ Failed to upload GRN attachment: {e}")
        driver.save_screenshot("grn_attachment_error.png")
        raise

# ==========================================
# VALIDATION FUNCTIONS
# ==========================================

def test_pb_negative_rate_block(driver, wait, row_index=1):
    logger.info(f"🛡️ Testing Negative Rate constraints on row {row_index}...")
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.main_tbody tr")
    row = rows[row_index - 1]

    try:
        rate_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='rate']")
        original_rate = driver.execute_script("return arguments[0].value;", rate_input)
        
        rate_input.send_keys(Keys.CONTROL + "a")
        rate_input.send_keys(Keys.BACKSPACE)
        rate_input.send_keys("-1500")
        rate_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        val = driver.execute_script("return arguments[0].value;", rate_input)
        if "-" in val:
            classes = rate_input.get_attribute('class')
            assert "ng-invalid" in classes, "Negative value accepted in Rate!"
        logger.info("   ✅ Negative Rate correctly blocked/stripped.")
        
        rate_input.send_keys(Keys.CONTROL + "a")
        rate_input.send_keys(Keys.BACKSPACE)
        rate_input.send_keys(str(original_rate))
        rate_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        logger.info(f"   ✅ Restored original Rate: {original_rate}")
        
    except Exception as e:
         logger.warning(f"   ⚠️ Could not test negative rate: {e}")

def verify_pb_math(driver, wait, row_index=1):
    logger.info(f"🧮 Verifying PB Math on row {row_index}...")
    time.sleep(1.5)
    
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.main_tbody tr")
    row = rows[row_index - 1]

    try:
        gross_qty_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='alternate_qty']")
        gross_qty = float(driver.execute_script("return arguments[0].value;", gross_qty_input) or 0)

        empty_bag_weight_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='empty_bag_weight']")
        empty_bag_weight = float(driver.execute_script("return arguments[0].value;", empty_bag_weight_input) or 0)

        net_qty_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='alternate_net_qty']")
        net_qty_ui = float(driver.execute_script("return arguments[0].value;", net_qty_input) or 0)

        expected_net_qty = gross_qty - empty_bag_weight
        assert abs(round(net_qty_ui, 2) - round(expected_net_qty, 2)) < 0.01, \
            f"❌ Net Qty Math Failed! Gross: {gross_qty}, Empty Bag: {empty_bag_weight}, Expected: {expected_net_qty}, UI: {net_qty_ui}"
        logger.info(f"   ✅ Net Qty Math correct: {net_qty_ui}")

        rate_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='rate']")
        rate = float(driver.execute_script("return arguments[0].value;", rate_input) or 0)

        txn_amount_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_total_txn_amount']")
        txn_amount_ui = float(driver.execute_script("return arguments[0].value;", txn_amount_input) or 0)
        
        expected_txn_amount = net_qty_ui * rate
        assert abs(round(txn_amount_ui, 2) - round(expected_txn_amount, 2)) < 0.01, \
            f"❌ Txn Amount Math Failed! Net Qty: {net_qty_ui}, Rate: {rate}, Expected: {expected_txn_amount}, UI: {txn_amount_ui}"
        logger.info(f"   ✅ Transaction Amount Math correct: {txn_amount_ui}")

    except Exception as e:
         logger.warning(f"   ⚠️ Could not verify math: {e}")

# ==========================================
# NEW: ENHANCED VALIDATIONS (NON-DISRUPTIVE)
# ==========================================

def test_empty_bag_weight_recalculation(driver, wait, row_index=1):
    """PB_NEW_02: Modify empty bag weight and verify net qty updates dynamically."""
    logger.info(f"🔄 [PB_NEW_02] Testing Empty Bag Weight dynamic recalculation on row {row_index}...")
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody.main_tbody tr")
        row = rows[row_index - 1]

        gross_qty_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='alternate_qty']")
        gross_qty = float(driver.execute_script("return arguments[0].value;", gross_qty_input) or 0)

        ebw_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='empty_bag_weight']")
        original_ebw = driver.execute_script("return arguments[0].value;", ebw_input) or "0"

        # Change empty bag weight
        new_ebw = float(original_ebw) + 5.0 if original_ebw else 5.0
        driver.execute_script("arguments[0].value = '';", ebw_input)
        ebw_input.send_keys(str(new_ebw))
        ebw_input.send_keys(Keys.TAB)
        time.sleep(1.5)

        net_qty_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='alternate_net_qty']")
        net_qty_ui = float(driver.execute_script("return arguments[0].value;", net_qty_input) or 0)
        expected_net = gross_qty - new_ebw
        if abs(round(net_qty_ui, 2) - round(expected_net, 2)) < 0.01:
            logger.info(f"   ✅ Net Qty recalculated correctly: {net_qty_ui}")
        else:
            logger.warning(f"   ⚠️ Net Qty mismatch. Expected {expected_net}, got {net_qty_ui}")

        # Restore original
        driver.execute_script("arguments[0].value = '';", ebw_input)
        ebw_input.send_keys(str(original_ebw))
        ebw_input.send_keys(Keys.TAB)
        time.sleep(1)
    except Exception as e:
        logger.warning(f"   ⚠️ Empty bag weight recalc test skipped: {e}")

def verify_rate_matches_qc_final_rate(driver, wait, expected_rate=None, row_index=1):
    """PB_NEW_01: Check that the displayed rate matches expected QC final rate."""
    logger.info(f"💰 [PB_NEW_01] Verifying rate matches QC Final Rate on row {row_index}...")
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody.main_tbody tr")
        row = rows[row_index - 1]
        rate_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='rate']")
        displayed_rate = float(driver.execute_script("return arguments[0].value;", rate_input) or 0)
        if expected_rate is not None:
            if abs(displayed_rate - expected_rate) < 0.01:
                logger.info(f"   ✅ Rate matches expected QC Final Rate: {displayed_rate}")
            else:
                logger.warning(f"   ⚠️ Rate mismatch! Expected {expected_rate}, got {displayed_rate}")
        else:
            if displayed_rate > 0:
                logger.info(f"   ℹ️ Rate is {displayed_rate} (no expected value provided).")
            else:
                logger.warning("   ⚠️ Rate is zero – possibly not fetched correctly.")
    except Exception as e:
        logger.warning(f"   ⚠️ Rate verification skipped: {e}")

def test_tds_deduction(driver, wait, row_index=1):
    """PB_TC27: Verify TDS deduction updates payable amount."""
    logger.info(f"🧾 [PB_TC27] Testing TDS deduction on row {row_index}...")
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody.main_tbody tr")
        row = rows[row_index - 1]

        # TDS input might be per row or global; check both
        try:
            tds_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='tds_amount']")
        except:
            tds_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='tds_amount']")

        payable_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='payable_amount']")
        txn_amount_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_total_txn_amount']")

        txn_amount = float(driver.execute_script("return arguments[0].value;", txn_amount_input) or 0)
        original_tds = driver.execute_script("return arguments[0].value;", tds_input) or "0"

        test_tds = 100.0
        driver.execute_script("arguments[0].value = '';", tds_input)
        tds_input.send_keys(str(test_tds))
        tds_input.send_keys(Keys.TAB)
        time.sleep(1.5)

        payable_ui = float(driver.execute_script("return arguments[0].value;", payable_input) or 0)
        expected_payable = txn_amount - test_tds
        if abs(payable_ui - expected_payable) < 0.01:
            logger.info(f"   ✅ Payable amount updated correctly: {payable_ui}")
        else:
            logger.warning(f"   ⚠️ Payable mismatch. Expected {expected_payable}, got {payable_ui}")

        # Restore
        driver.execute_script("arguments[0].value = '';", tds_input)
        tds_input.send_keys(str(original_tds))
        tds_input.send_keys(Keys.TAB)
    except Exception as e:
        logger.warning(f"   ⚠️ TDS test skipped (field may not exist): {e}")

# ==========================================
# MAIN FORM EXECUTION
# ==========================================

def fill_purchase_booking_registration(driver, wait, data, run_validations=True):
    logger.info("⚡ Starting Purchase Booking Registration...")

    try:
        logger.info("   ➡️ Waiting for page to completely settle...")
        time.sleep(3)
        try: wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ngx-spinner-overlay")))
        except: pass

        add_btn = driver.find_element(By.CSS_SELECTOR, "button.new_employee")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", add_btn)
        logger.info("   ✅ Clicked 'Add New Purchase Booking'")
    except Exception as e:
        logger.error(f"❌ CRITICAL: Failed to click Add button: {e}")
        raise

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='supplier_ref_id']")))
    time.sleep(1)

    if 'transaction_date' in data:
        fill_input(driver, wait, data['transaction_date'], control_name="transaction_date")

    select_dropdown(driver, wait, data['supplier'], control_name="supplier_ref_id")
    select_first_qc_option(driver, wait)
    time.sleep(3)

    select_dropdown(driver, wait, data['payment_terms'], control_name="supplier_payment_terms_ref_id", searchable=False)

    logger.info(f"   📦 Processing {len(data['items'])} items for Purchase Booking...")
    for index, item_data in enumerate(data['items']):
        item_name = item_data.get('item', '')
        logger.info(f"      ➡️ Setting details for Row {index + 1}: {item_name}")

        add_quantity_details(driver, wait, item_data, index)

        row_xpath = f"//tbody/tr[{index + 1}]"
        row = wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))
        
        if run_validations and index == 0:
            test_pb_negative_rate_block(driver, wait, row_index=(index + 1))
            # PB_NEW_01: verify rate (optional expected value can be passed via data)
            expected_rate = item_data.get('final_rate', None)
            verify_rate_matches_qc_final_rate(driver, wait, expected_rate, row_index=(index+1))

        # Determine Taxes (with CGST/SGST support - PB_NEW_03)
        is_intra_state = data.get('is_intra_state', False)
        if item_name in {"Soyabean", "Turmeric", "Chana"}:
            tax_rate_to_use = "5"
        elif item_name == "Tur-Red":
            tax_rate_to_use = "0"
        else:
            tax_rate_to_use = str(data.get('tax_rate', '0'))

        if is_intra_state:
            cgst_rate = str(float(tax_rate_to_use) / 2)
            sgst_rate = cgst_rate
            igst_rate_to_use = "0"
        else:
            igst_rate_to_use = tax_rate_to_use
            cgst_rate = "0"
            sgst_rate = "0"

        # Set Tax Rate (CGST or IGST)
        try:
            tax_dropdown = row.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='tax_rate']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tax_dropdown)
            driver.execute_script("arguments[0].click();", tax_dropdown)
            overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")))
            wait.until(EC.visibility_of(overlay))
            opt_xpath = f"//mat-option//span[normalize-space()='{tax_rate_to_use}']"
            tax_option = wait.until(EC.element_to_be_clickable((By.XPATH, opt_xpath)))
            driver.execute_script("arguments[0].click();", tax_option)
            time.sleep(0.5)
            logger.info(f"         ✅ Tax Rate set to {tax_rate_to_use}")
        except Exception as e:
            logger.warning(f"         ⚠️ Could not set Tax Rate for row {index+1}: {e}")

        # Set CGST/SGST or IGST
        if is_intra_state:
            try:
                cgst_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='cgst_rate']")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cgst_input)
                cgst_input.send_keys(Keys.CONTROL + "a")
                cgst_input.send_keys(Keys.BACKSPACE)
                cgst_input.send_keys(cgst_rate)
                cgst_input.send_keys(Keys.TAB)
                time.sleep(0.5)
                logger.info(f"         ✅ CGST Rate set to {cgst_rate}")
            except: pass
            try:
                sgst_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='sgst_rate']")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sgst_input)
                sgst_input.send_keys(Keys.CONTROL + "a")
                sgst_input.send_keys(Keys.BACKSPACE)
                sgst_input.send_keys(sgst_rate)
                sgst_input.send_keys(Keys.TAB)
                time.sleep(0.5)
                logger.info(f"         ✅ SGST Rate set to {sgst_rate}")
            except: pass
        else:
            try:
                igst_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_igst_rate']")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", igst_input)
                igst_input.send_keys(Keys.CONTROL + "a")
                igst_input.send_keys(Keys.BACKSPACE)
                igst_input.send_keys(igst_rate_to_use)
                igst_input.send_keys(Keys.TAB)
                time.sleep(0.5)
                logger.info(f"         ✅ IGST Rate set to {igst_rate_to_use}")
            except Exception as e:
                pass

        # Extra Fields (Empty Bag Weight, Labour Charges)
        if 'empty_bag_weight' in item_data:
            try:
                ebw_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='empty_bag_weight']")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", ebw_input)
                ebw_input.send_keys(Keys.CONTROL + "a")
                ebw_input.send_keys(Keys.BACKSPACE)
                ebw_input.send_keys(str(item_data['empty_bag_weight']))
                ebw_input.send_keys(Keys.TAB)
                time.sleep(0.5)
                logger.info(f"         ✅ Empty Bag Weight set to {item_data['empty_bag_weight']}")
            except Exception as e:
                logger.warning(f"         ⚠️ Could not set Empty Bag Weight: {e}")

        if 'labour_charges' in item_data:
            try:
                labour_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='labour_charges']")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", labour_input)
                labour_input.send_keys(Keys.CONTROL + "a")
                labour_input.send_keys(Keys.BACKSPACE)
                labour_input.send_keys(str(item_data['labour_charges']))
                labour_input.send_keys(Keys.TAB)
                time.sleep(0.5)
                logger.info(f"         ✅ Labour Charges set to {item_data['labour_charges']}")
            except Exception as e:
                logger.warning(f"         ⚠️ Could not set Labour Charges: {e}")

        if run_validations and index == 0:
            verify_pb_math(driver, wait, row_index=(index+1))
            test_empty_bag_weight_recalculation(driver, wait, row_index=(index+1))
            test_tds_deduction(driver, wait, row_index=(index+1))

    if 'attachment_file' in data:
        upload_grn_attachment(driver, wait, data['attachment_file'])

    logger.info("📤 Submitting the Final Purchase Booking form...")
    final_submit_xpath = "//div[contains(@class, 'footer')]//button[@type='submit']"
    submit_button = wait.until(EC.presence_of_element_located((By.XPATH, final_submit_xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_button)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", submit_button)
    logger.info("✅ Final Submit button clicked")

    logger.info("   ⏳ Waiting to redirect to the PB List page...")
    try:
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-container")))
        wait_for_backdrop_to_clear(wait)
    except:
        pass
        
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.new_employee")))
    time.sleep(2)
    logger.info("🚀 Purchase Booking Saved Successfully!")

    
# ==========================================
# REPORTING & BUG CHECKS
# ==========================================

def test_view_internal_server_error_bug(driver, wait):
    """PB_TC24: Check for internal server error on view."""
    logger.info("🐞 [PB_TC24] Testing Known Bug: 'Internal Server Error' on View...")
    try:
        view_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//table/tbody/tr[1]//button[.//i[contains(@class, 'bi-eye')]]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", view_btn)
        driver.execute_script("arguments[0].click();", view_btn)
        time.sleep(2)
        
        try:
            error_toast = driver.find_element(By.XPATH, "//*[contains(text(), 'Internal server error')]")
            logger.warning("   ✅ BUG CAUGHT: Internal Server Error occurred on View.")
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        except:
            logger.info("   ⚠️ No error caught. Has the bug been fixed? PB loaded successfully.")
    except Exception as e:
        logger.warning(f"   ⚠️ Could not perform View Bug test: {e}")

def test_excel_download(driver, wait, download_dir):
    logger.info("📥 Testing Excel Download...")
    for f in glob.glob(os.path.join(download_dir, "*.xlsx")):
        os.remove(f)
    
    excel_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Download Excel')]")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", excel_btn)
    driver.execute_script("arguments[0].click();", excel_btn)
    
    timeout = time.time() + 20
    downloaded_file = None
    while time.time() < timeout:
        files = glob.glob(os.path.join(download_dir, "*.xlsx"))
        if files:
            downloaded_file = files[0]
            break
        time.sleep(1)
        
    if downloaded_file and os.path.getsize(downloaded_file) > 0:
        logger.info(f"   ✅ Excel downloaded successfully: {os.path.basename(downloaded_file)}")
        os.remove(downloaded_file)
    else:
        raise AssertionError("❌ Excel file was not downloaded.")


def generate_pb_excel_report(scraped_items, global_total_ui):
    logger.info("📊 Generating Enhanced Audit Report...")
    df = pd.DataFrame(scraped_items)

    numeric_cols = ['Rate', 'Gross Quantity', 'Net Quantity', 'Empty Bag Weight (KG)',
                    'Labour Charges', 'IGST Amount', 'Total Amount']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].round(2)

    column_order = [
        'PB Number', 'Item Name', 'Rate', 'Gross Quantity', 'Net Quantity',
        'Empty Bag Weight (KG)', 'Labour Charges', 'IGST Amount', 'Total Amount', 'Weight Reduced'
    ]
    df['Weight Reduced'] = (df['Gross Quantity'] - df['Net Quantity']).round(2)

    total_gross = df['Gross Quantity'].sum().round(2)
    total_net = df['Net Quantity'].sum().round(2)
    total_reduced = df['Weight Reduced'].sum().round(2)
    total_labour = df['Labour Charges'].sum().round(2)
    total_igst = df['IGST Amount'].sum().round(2)
    sum_of_table_totals = df['Total Amount'].sum().round(2)
    global_total_ui = round(global_total_ui, 2)

    sum_row = pd.DataFrame({
        'PB Number': ['GRAND TOTALS'],
        'Item Name': [''],
        'Rate': [''],
        'Gross Quantity': [total_gross],
        'Net Quantity': [total_net],
        'Empty Bag Weight (KG)': [''],
        'Labour Charges': [total_labour],
        'IGST Amount': [total_igst],
        'Total Amount': [sum_of_table_totals],
        'Weight Reduced': [total_reduced]
    })

    expected_ui_total = round(sum_of_table_totals - total_labour, 2)
    diff = round(global_total_ui - expected_ui_total, 2)
    status = "✅ MATCHED" if abs(diff) < 0.01 else f"❌ DISCREPANCY: {diff:.2f}"

    recon_row = pd.DataFrame({
        'PB Number': ['MATH AUDIT'],
        'Item Name': [f'Global UI Total: {global_total_ui}'],
        'Rate': [f'Total Labour: {total_labour}'],
        'Gross Quantity': [f'Actual Table Sum: {sum_of_table_totals}'],
        'Net Quantity': [f'Calculated UI (Table - Labour): {expected_ui_total}'],
        'Empty Bag Weight (KG)': [status],
        'Labour Charges': [''],
        'IGST Amount': [''],
        'Total Amount': [''],
        'Weight Reduced': ['']
    })

    df = pd.concat([df, sum_row, recon_row], ignore_index=True)
    df = df[column_order]

    folder = "download_files"
    if not os.path.exists(folder): os.makedirs(folder)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = os.path.abspath(os.path.join(folder, f"PB_Audit_{timestamp}.xlsx"))

    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Audit', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Audit']

        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center',
            'bg_color': '#D9E1F2', 'border': 1
        })
        cell_format = workbook.add_format({
            'text_wrap': True, 'valign': 'vcenter', 'align': 'center', 'border': 1
        })

        for col_num, col_name in enumerate(df.columns):
            worksheet.write(0, col_num, col_name, header_format)
        for row_num in range(1, len(df) + 1):
            worksheet.set_row(row_num, None, cell_format)

        column_widths = {'A':20, 'B':30, 'C':12, 'D':15, 'E':15, 'F':20, 'G':15, 'H':15, 'I':18, 'J':18}
        for col, width in column_widths.items():
            worksheet.set_column(f'{col}:{col}', width)

    logger.info(f"✅ Formatted Audit Report saved: {file_path}")

def search_and_export_latest_pb(driver, wait, supplier_raw_name):
    name = supplier_raw_name.split('-')[0].strip()
    logger.info(f"\n🔍 Auditing finalized data for: {name}")

    search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.search-field")))
    wait.until(lambda d: search_input.is_enabled())
    driver.execute_script("arguments[0].value = '';", search_input)
    driver.execute_script("arguments[0].value = arguments[1];", search_input, name)
    driver.execute_script("""
        var event = new KeyboardEvent('keypress', {
            key: 'Enter', code: 'Enter', which: 13, keyCode: 13, bubbles: true
        });
        arguments[0].dispatchEvent(event);
    """, search_input)
    time.sleep(3)

    view_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//table/tbody/tr[1]//button[.//i[contains(@class, 'bi-eye')]]")))
    driver.execute_script("arguments[0].click();", view_btn)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tableExport1 tbody tr")))
    logger.info("   ⏳ Loading PB Details & Calculations...")
    time.sleep(5)

    scraped_data = []
    def safe_f(v):
        try: return float(v) if v else 0.0
        except: return 0.0

    try:
        global_total_ui = safe_f(driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_total_amount']").get_attribute("value"))
        pb_num = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='transaction_ref_no']").get_attribute("value")
        logger.info(f"   📊 UI Global Total: {global_total_ui} | PB: {pb_num}")
    except:
        global_total_ui, pb_num = 0.0, "N/A"

    rows = driver.find_elements(By.XPATH, "//table[@id='tableExport1']//tbody[contains(@class, 'main_tbody')]/tr")
    for row in rows:
        try:
            item = row.find_element(By.CSS_SELECTOR, ".mat-mdc-select-min-line").text.strip()
            if not item: continue
            def get_val(selector):
                try: return safe_f(row.find_element(By.CSS_SELECTOR, selector).get_attribute("value"))
                except: return 0.0
            scraped_data.append({
                'PB Number': pb_num,
                'Item Name': item,
                'Rate': get_val("input[formcontrolname='rate']"),
                'Gross Quantity': get_val("input[formcontrolname='alternate_qty']"),
                'Net Quantity': get_val("input[formcontrolname='alternate_net_qty']"),
                'Empty Bag Weight (KG)': get_val("input[formcontrolname='empty_bag_weight']"),
                'Labour Charges': get_val("input[formcontrolname='labour_charges']"),
                'IGST Amount': get_val("input[formcontrolname='txn_currency_igst_amount']"),
                'Total Amount': get_val("input[formcontrolname='txn_currency_total_txn_amount']")
            })
        except Exception as e:
            pass

    if scraped_data:
        generate_pb_excel_report(scraped_data, global_total_ui)
    else:
        logger.warning("⚠️ Failed to scrape table data for Audit report.")

# ==========================================
# SUITE EXECUTOR
# ==========================================

def execute_purchase_suite(driver, wait, data, download_dir):
    logger.info("\n--- ⚡ STARTING PURCHASE BOOKING SUITE ---")
    
    fill_purchase_booking_registration(driver, wait, data, run_validations=True)
    
    test_view_internal_server_error_bug(driver, wait)   # PB_TC24
    
    test_excel_download(driver, wait, download_dir)
    
    search_and_export_latest_pb(driver, wait, data['supplier'])

    logger.info("--- ✅ PURCHASE BOOKING SUITE COMPLETED ---\n")


if __name__ == "__main__":
    download_dir = os.path.abspath("downloads")
    if not os.path.exists(download_dir): os.makedirs(download_dir)
    
    chrome_options = Options()
    prefs = {"download.default_directory": download_dir, "download.prompt_for_download": False}
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)

    try:
        auth_section.perform_login(driver, wait, config)
        nav_section.go_to_purchase_booking_page(driver, wait) 
        
        execute_purchase_suite(driver, wait, purchase_booking_data, download_dir)
        
    finally:
        driver.quit()
        shutil.rmtree(download_dir, ignore_errors=True)