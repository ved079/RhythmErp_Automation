import sys
import os

# Go up 3 levels from this file to reach the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

import time
import logging
from decimal import Decimal
from datetime import datetime
import pandas as pd

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config
from common import auth_section, nav_section
from privateb2b import stock_transfer_section
from reports.all_reports import inventory_report1
# --- INTEGRATED: Using the dedicated recon data dictionary ---
from data.test_data import st_recon_inventory_data, stock_transfer_data

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# ----------------------------------------------------------------------------------
# 1. INVENTORY SCRAPER UTILITY
# ----------------------------------------------------------------------------------
def get_inventory_closing_qty(driver, wait):
    """
    Scrapes the Closing Qty from the Inventory Report.
    Opens Full View modal to ensure Angular has fully rendered all cell values,
    reads the 9th column (index 8), then closes the Full View.
    """
    logger.info("   🔍 Extracting Closing Qty from table...")
    
    try:
        # Wait for report card table to appear
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        time.sleep(1)
        
        # Click the Full View button to force full render
        full_view_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@title, 'Full View')]")
        ))
        full_view_btn.click()
        logger.info("      ✅ Opened Full View")
        time.sleep(2)
        
        # Read from the Full View modal's table
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.card.card-body table tbody tr")))
        time.sleep(1)
        
        first_row = driver.find_element(By.CSS_SELECTOR, "div.card.card-body table tbody tr")
        cells = first_row.find_elements(By.TAG_NAME, "td")
        
        if not cells or "No Data" in first_row.text:
            logger.info("      ⚠️ No stock records found. Assuming 0.00.")
            _close_full_view(driver)
            return Decimal('0.00')

        if len(cells) < 9:
            _close_full_view(driver)
            raise Exception(f"Row has only {len(cells)} cells, expected at least 9.")
            
        closing_qty_text = cells[8].text.strip()
        logger.info(f"      Raw Closing Qty Text: '{closing_qty_text}'")
        
        cleaned = closing_qty_text.replace(',', '').strip()
        if not cleaned or cleaned == '-':
            value = Decimal('0.00')
        else:
            value = Decimal(cleaned)
            
        _close_full_view(driver)
        logger.info(f"      ✅ Parsed Closing Qty: {value}")
        return value

    except Exception as e:
        logger.error(f"❌ Failed to extract Closing Qty: {e}")
        _close_full_view(driver)
        driver.save_screenshot("inventory_qty_extract_error.png")
        raise Exception("Could not find or parse the Closing Qty in the Inventory Report.")


def _close_full_view(driver):
    """Closes the Full View modal if it's open."""
    try:
        cancel_btn = driver.find_element(By.CSS_SELECTOR, "button.cancel-btn-fullscreen")
        cancel_btn.click()
        time.sleep(0.5)
    except:
        pass


def fetch_stock_for_location(driver, wait, base_data, location_name):
    """Overrides the location in the base data, runs the report, and returns the qty."""
    logger.info(f"📊 Fetching stock for Location: {location_name}")
    
    report_filter = base_data.copy()
    report_filter['location'] = location_name
    
    # --- INTEGRATED: Using the fast, minimalist report loader ---
    inventory_report1.load_recon_report_data(driver, wait, report_filter)
    
    return get_inventory_closing_qty(driver, wait)

# ----------------------------------------------------------------------------------
# 2. EXCEL RECONCILIATION GENERATOR
# ----------------------------------------------------------------------------------
def generate_st_reconciliation_report(
    item_name, from_loc, to_loc, transfer_qty,
    from_initial, from_final, to_initial, to_final,
    output_dir="download_files"
):
    logger.info("📄 Generating Stock Transfer Reconciliation Report...")
    os.makedirs(output_dir, exist_ok=True)

    # Reconciliation Math
    transfer_qty_dec = Decimal(str(transfer_qty))
    expected_from_final = from_initial - transfer_qty_dec
    expected_to_final = to_initial + transfer_qty_dec
    
    diff_from = from_final - expected_from_final
    diff_to = to_final - expected_to_final
    
    status_from = "✅ PASS" if abs(diff_from) < Decimal('0.01') else "❌ FAIL"
    status_to = "✅ PASS" if abs(diff_to) < Decimal('0.01') else "❌ FAIL"

    data = {
        "Location Role": ["From Location", "To Location"],
        "Location Name": [from_loc, to_loc],
        "Initial Qty": [float(from_initial), float(to_initial)],
        "Transfer Impact": [float(-transfer_qty_dec), float(transfer_qty_dec)],
        "Expected Qty": [float(expected_from_final), float(expected_to_final)],
        "Actual Qty": [float(from_final), float(to_final)],
        "Difference": [float(diff_from), float(diff_to)],
        "Status": [status_from, status_to]
    }
    
    df = pd.DataFrame(data)

    metadata = pd.DataFrame({
        "Location Role": ["Report Generated", "Item Transferred"],
        "Location Name": [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item_name],
        "Initial Qty": ["", ""], "Transfer Impact": ["", ""], "Expected Qty": ["", ""],
        "Actual Qty": ["", ""], "Difference": ["", ""], "Status": ["", ""]
    })
    
    df = pd.concat([metadata, df], ignore_index=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.abspath(os.path.join(output_dir, f"Stock_Transfer_Recon_{timestamp}.xlsx"))

    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='ST_Recon', index=False)
        workbook = writer.book
        worksheet = writer.sheets['ST_Recon']

        header_format = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
        cell_format   = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        pass_format   = workbook.add_format({'bold': True, 'font_color': 'green', 'border': 1})
        fail_format   = workbook.add_format({'bold': True, 'font_color': 'red', 'border': 1})

        for col_num, col_name in enumerate(df.columns):
            worksheet.write(0, col_num, col_name, header_format)

        for row_num in range(1, len(df) + 1):
            for col_num in range(len(df.columns)):
                val = df.iloc[row_num - 1, col_num]
                
                if df.columns[col_num] == "Status" and "PASS" in str(val):
                    worksheet.write(row_num, col_num, val, pass_format)
                elif df.columns[col_num] == "Status" and "FAIL" in str(val):
                    worksheet.write(row_num, col_num, val, fail_format)
                else:
                    fmt = cell_format if row_num > 2 and isinstance(val, (int, float)) else workbook.add_format({'border': 1})
                    worksheet.write(row_num, col_num, val, fmt)

        worksheet.set_column('A:B', 20)
        worksheet.set_column('C:G', 15)
        worksheet.set_column('H:H', 12)

    logger.info(f"✅ Reconciliation report saved: {file_path}")
    return status_from == "✅ PASS" and status_to == "✅ PASS"

# ----------------------------------------------------------------------------------
# 3. MAIN ORCHESTRATOR
# ----------------------------------------------------------------------------------
def run_stock_transfer_reconciliation(driver, wait):
    logger.info("=" * 60)
    logger.info("🚀 Starting Stock Transfer Reconciliation Test")
    logger.info("=" * 60)
    
    # Extract dynamic data from the imported dictionary
    item_name = stock_transfer_data["item_name"]
    from_loc = stock_transfer_data["from_location"]
    to_loc = stock_transfer_data["to_location"]
    transfer_qty = stock_transfer_data["transfer_quantity"]
    
    # --- INTEGRATED: Target the recon-specific dictionary ---
    st_recon_inventory_data["item"] = item_name
    
    # Step 1: Get Initial Stocks
    logger.info("--- PHASE 1: Fetching Initial Stocks ---")
    initial_from_qty = fetch_stock_for_location(driver, wait, st_recon_inventory_data, from_loc)
    initial_to_qty = fetch_stock_for_location(driver, wait, st_recon_inventory_data, to_loc)
    
    logger.info(f"📦 BEFORE -> {from_loc}: {initial_from_qty} | {to_loc}: {initial_to_qty}")

    # Prevent submitting a transfer if we don't have enough stock
    if Decimal(str(transfer_qty)) > initial_from_qty:
        logger.error(f"❌ Cannot transfer {transfer_qty} units. {from_loc} only has {initial_from_qty} units available.")
        raise AssertionError("Insufficient stock in 'From Location' to perform transfer.")

    # Step 2: Execute Stock Transfer
    logger.info("--- PHASE 2: Executing Stock Transfer ---")
    nav_section.go_to_stock_transfer_page(driver, wait)
    stock_transfer_section.fill_stock_transfer(driver, wait, stock_transfer_data)
    
    logger.info(f"🚚 Transferred {transfer_qty} units of {item_name} from {from_loc} to {to_loc}")
    
    # Wait for backend to sync the inventory ledgers
    logger.info("⏳ Waiting for backend inventory sync...")
    time.sleep(5)

    # Step 3: Get Final Stocks (reads from Full View modal)
    logger.info("--- PHASE 3: Fetching Final Stocks ---")
    final_from_qty = fetch_stock_for_location(driver, wait, st_recon_inventory_data, from_loc)
    final_to_qty = fetch_stock_for_location(driver, wait, st_recon_inventory_data, to_loc)
    
    logger.info(f"📦 AFTER  -> {from_loc}: {final_from_qty} | {to_loc}: {final_to_qty}")

    # Step 4: Generate Excel & Assert
    logger.info("--- PHASE 4: Verification & Reporting ---")
    passed = generate_st_reconciliation_report(
        item_name, from_loc, to_loc, transfer_qty,
        initial_from_qty, final_from_qty, initial_to_qty, final_to_qty
    )
    
    if passed:
        logger.info("🎉 STOCK TRANSFER RECONCILIATION PASSED!")
    else:
        logger.error("💥 STOCK TRANSFER RECONCILIATION FAILED! Check Excel report.")
        raise AssertionError("Stock transfer did not correctly update both locations.")

    logger.info("=" * 60)

if __name__ == "__main__":
    from selenium import webdriver
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)

    try:
        auth_section.perform_login(driver, wait, config)
        run_stock_transfer_reconciliation(driver, wait)
    finally:
        driver.quit()