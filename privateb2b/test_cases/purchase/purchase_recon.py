import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

import time
import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime
import pandas as pd

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config
from common import auth_section, nav_section
from privateb2b.purchase import gatepass_section, grn_section, qc_section, purchase_booking_section
from data.test_data import gatepass_data, grn_data, qc_data, purchase_booking_data, trial_balance_data
from reports.all_reports import trial_balance

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


def debug_dump_table(driver):
    """
    Dump every row + every cell to the log so you can see
    exactly what text the table contains and which column index to use.
    """
    logger.info("   🔎 DEBUG: Dumping all table rows...")
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    if not rows:
        logger.warning("   ⚠️  DEBUG: No <tbody tr> rows found at all.")
        # Also try without tbody in case the table structure is flat
        rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
        logger.info(f"   🔎 DEBUG: Found {len(rows)} rows using 'table tr' selector.")
    else:
        logger.info(f"   🔎 DEBUG: Found {len(rows)} rows using 'tbody tr' selector.")

    for i, row in enumerate(rows):
        cells = row.find_elements(By.TAG_NAME, "td")
        cell_texts = [f"[{j}]: '{c.text.strip()}'" for j, c in enumerate(cells)]
        logger.info(f"   Row {i:>3}: {' | '.join(cell_texts) if cell_texts else '(no <td> cells)'}")


def wait_for_table_to_load(driver, wait):
    """Wait until at least one data row is present in the report table."""
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr td")))
        time.sleep(1)  # small buffer for all rows to render
        logger.info("   ✅ Table loaded.")
    except Exception as e:
        driver.save_screenshot("table_not_loaded.png")
        raise Exception(f"Report table did not load in time: {e}")


def get_closing_stock_value(driver, wait):
    """
    Locate the 'Closing Stock' row in the report table and
    return its Closing Balance value as a Decimal.
    """
    logger.info("   🔍 Locating Closing Stock row...")

    # Wait for table to be present before reading
    wait_for_table_to_load(driver, wait)

    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")

    # ── If still empty, fall back to table tr ──────────────────────────
    if not rows:
        rows = driver.find_elements(By.CSS_SELECTOR, "table tr")

    closing_stock_row = None
    closing_balance_text = None

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if not cells:
            continue

        # Search ALL cells for the keyword (case-insensitive, stripped)
        # so we don't depend on a hard-coded column index
        for idx, cell in enumerate(cells):
            cell_text = cell.text.strip()
            if "closing stock" in cell_text.lower():
                closing_stock_row = row
                # Closing Balance is the LAST cell; adjust if your table differs
                closing_balance_text = cells[-1].text.strip()
                logger.info(
                    f"      ✅ Found 'Closing Stock' in column [{idx}]: '{cell_text}' "
                    f"| Last cell (balance): '{closing_balance_text}'"
                )
                break

        if closing_stock_row:
            break

    # ── If still not found, dump the table so you can diagnose ─────────
    if closing_stock_row is None:
        logger.error("   ❌ 'Closing Stock' row NOT found. Dumping full table for diagnosis:")
        debug_dump_table(driver)
        driver.save_screenshot("closing_stock_not_found.png")
        raise Exception(
            "Closing Stock row not found in report table. "
            "Check the log dump above and screenshot 'closing_stock_not_found.png' "
            "to find the exact text and correct column index."
        )

    # ── Parse the value ─────────────────────────────────────────────────
    try:
        cleaned = closing_balance_text.replace(',', '').strip()
        if 'Dr' in cleaned:
            value = Decimal(cleaned.replace('Dr', '').strip())
        elif 'Cr' in cleaned:
            value = -Decimal(cleaned.replace('Cr', '').strip())
        elif cleaned == '' or cleaned == '-':
            value = Decimal('0')
        else:
            value = Decimal(cleaned)
    except InvalidOperation:
        logger.error(f"   ❌ Could not parse closing balance text: '{closing_balance_text}'")
        raise Exception(f"Failed to parse Closing Stock value: '{closing_balance_text}'")

    logger.info(f"      Parsed Closing Stock value: {value}")
    return value


def navigate_to_reports_and_get_closing_stock(driver, wait):
    """Use existing trial_balance module to load the report and return Closing Stock value."""
    logger.info("📊 Navigating to Reports and fetching Closing Stock via Trial Balance module...")
    trial_balance.go_to_reports_page(driver, wait)
    trial_balance.fill_trial_balance_form(driver, wait, trial_balance_data)
    trial_balance.click_view(driver, wait)
    return get_closing_stock_value(driver, wait)


def run_purchase_flow_and_get_pb_total(driver, wait):
    """
    Execute the full purchase flow (Gate Pass -> GRN -> QC -> Purchase Booking).
    Returns the Purchase Booking total amount as a Decimal.
    """
    logger.info("🛒 Starting Purchase Flow...")

    nav_section.go_to_gatepass_page(driver, wait)
    gatepass_section.fill_gatepass_registration(driver, wait, gatepass_data)

    nav_section.go_to_grn_page(driver, wait)
    grn_section.fill_grn_registration(driver, wait, grn_data)
    grn_section.approve_latest_grn(driver, wait)

    nav_section.go_to_qc_page(driver, wait)
    qc_section.fill_qc_registration(driver, wait, qc_data)

    nav_section.go_to_purchase_booking_page(driver, wait)
    pb_total = purchase_booking_section.fill_purchase_booking_and_return_total(driver, wait, purchase_booking_data)

    logger.info(f"✅ Purchase Flow completed. PB Total: {pb_total}")
    return pb_total


def generate_reconciliation_report(
    closing_stock_before,
    closing_stock_after,
    pb_total_amount,
    pb_number,
    supplier_name,
    output_dir="download_files"
):
    """Generate a formatted Excel reconciliation report."""
    logger.info("📄 Generating Reconciliation Report...")
    os.makedirs(output_dir, exist_ok=True)

    expected_after = closing_stock_before + pb_total_amount
    difference = closing_stock_after - expected_after
    status = "✅ PASS" if abs(difference) < Decimal('0.01') else "❌ FAIL"

    data = {
        "Metric": [
            "Closing Stock (Before)",
            "Purchase Booking Amount",
            "Expected Closing Stock (After)",
            "Actual Closing Stock (After)",
            "Difference",
            "Status"
        ],
        "Value": [
            f"{closing_stock_before:,.2f}",
            f"{pb_total_amount:,.2f}",
            f"{expected_after:,.2f}",
            f"{closing_stock_after:,.2f}",
            f"{difference:,.2f}",
            status
        ]
    }
    df = pd.DataFrame(data)

    metadata = pd.DataFrame({
        "Metric": ["Report Generated", "Supplier", "PB Number"],
        "Value": [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            supplier_name,
            pb_number
        ]
    })
    df = pd.concat([metadata, df], ignore_index=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.abspath(os.path.join(output_dir, f"Purchase_Recon_{timestamp}.xlsx"))

    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Reconciliation', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Reconciliation']

        header_format = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
        cell_format   = workbook.add_format({'border': 1})
        pass_format   = workbook.add_format({'bold': True, 'font_color': 'green'})
        fail_format   = workbook.add_format({'bold': True, 'font_color': 'red'})

        for col_num, col_name in enumerate(df.columns):
            worksheet.write(0, col_num, col_name, header_format)

        for row_num in range(1, len(df) + 1):
            worksheet.write(row_num, 0, df.iloc[row_num - 1, 0], cell_format)
            if df.iloc[row_num - 1, 0] == "Status":
                fmt = pass_format if "PASS" in df.iloc[row_num - 1, 1] else fail_format
                worksheet.write(row_num, 1, df.iloc[row_num - 1, 1], fmt)
            else:
                worksheet.write(row_num, 1, df.iloc[row_num - 1, 1], cell_format)

        worksheet.set_column('A:A', 35)
        worksheet.set_column('B:B', 25)

    logger.info(f"✅ Reconciliation report saved: {file_path}")


def run_purchase_reconciliation_test(driver, wait):
    """Main test orchestrator."""
    logger.info("=" * 60)
    logger.info("🚀 Starting Purchase Reconciliation Test")
    logger.info("=" * 60)

    # Step 1: Closing stock before purchase
    closing_stock_before = navigate_to_reports_and_get_closing_stock(driver, wait)
    logger.info(f"💰 Closing Stock BEFORE purchase: {closing_stock_before:,.2f}")

    # Step 2: Execute purchase flow
    pb_total = run_purchase_flow_and_get_pb_total(driver, wait)

    # Step 3: Closing stock after purchase
    closing_stock_after = navigate_to_reports_and_get_closing_stock(driver, wait)
    logger.info(f"💰 Closing Stock AFTER purchase: {closing_stock_after:,.2f}")

    # Step 4: Generate Excel report
    generate_reconciliation_report(
        closing_stock_before=closing_stock_before,
        closing_stock_after=closing_stock_after,
        pb_total_amount=pb_total,
        pb_number="See PB Audit Report",
        supplier_name=purchase_booking_data['supplier']
    )

    # Step 5: Assert reconciliation
    expected = closing_stock_before + pb_total
    if abs(closing_stock_after - expected) < Decimal('0.01'):
        logger.info("🎉 RECONCILIATION PASSED: Closing Stock updated correctly.")
    else:
        logger.error(f"💥 RECONCILIATION FAILED: Expected {expected:,.2f}, got {closing_stock_after:,.2f}")
        raise AssertionError("Purchase amount not reflected in Closing Stock.")

    logger.info("=" * 60)
    logger.info("✅ Purchase Reconciliation Test Completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    from selenium import webdriver
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)

    try:
        auth_section.perform_login(driver, wait, config)
        run_purchase_reconciliation_test(driver, wait)
    finally:
        driver.quit()