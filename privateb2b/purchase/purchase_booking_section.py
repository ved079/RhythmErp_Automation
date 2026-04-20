from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import os
import pandas as pd
from datetime import datetime
import logging
from common.helper import select_dropdown, fill_input, click_submit
from decimal import Decimal

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


def wait_for_backdrop_to_clear(wait):
    """Utility to ensure Angular overlay backdrops are fully gone before the next action."""
    try:
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "cdk-overlay-backdrop")))
    except:
        pass


def add_quantity_details(driver, wait, no_of_bags, quantity, row_index):
    """Click the 'Add' button for a specific row, fill modal, and submit."""
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
        bags_input.send_keys(str(no_of_bags))

        qty_input = modal.find_element(By.CSS_SELECTOR, "input[formcontrolname='quantity']")
        driver.execute_script("arguments[0].click();", qty_input)
        qty_input.send_keys(Keys.CONTROL + "a")
        qty_input.send_keys(Keys.BACKSPACE)
        qty_input.send_keys(str(quantity))

        submit_modal_btn = modal.find_element(By.XPATH, ".//button[contains(text(), 'Submit') or contains(text(), 'Save')]")
        driver.execute_script("arguments[0].click();", submit_modal_btn)
        logger.info("   ✅ Modal submitted")

        wait_for_backdrop_to_clear(wait)
        time.sleep(1)
    except Exception as e:
        logger.error(f"❌ Failed to add quantity details for row {row_index + 1}: {e}")
        driver.save_screenshot(f"add_quantity_error_row_{row_index + 1}.png")
        raise


def _read_total_from_open_modal(driver, wait):
    """
    Read txn_currency_total_amount from the PB view modal that is already open.
    Called immediately after fill_purchase_booking_registration (which opens the modal
    via search_and_export_latest_pb). Does NOT re-search or re-click View.
    """
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tableExport1 tbody tr")))
        time.sleep(1)
        total_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[formcontrolname='txn_currency_total_amount']")
            )
        )
        total_text = total_element.get_attribute('value')
        total = float(total_text.replace(',', ''))
        logger.info(f"   ✅ Read PB total from open modal: {total}")
        return total
    except Exception as e:
        driver.save_screenshot("read_pb_total_error.png")
        raise Exception(f"❌ Could not read PB total from open modal: {e}")


def fill_purchase_booking_and_return_total(driver, wait, data):
    """
    Executes the full purchase booking registration and returns the
    final transaction total amount as a Decimal.

    Flow:
      1. fill_purchase_booking_registration  → submits form, navigates to list,
                                               calls search_and_export_latest_pb
                                               which opens the View modal.
      2. _read_total_from_open_modal         → reads the total from the
                                               already-open modal (no re-search).
    """
    fill_purchase_booking_registration(driver, wait, data)
    # Modal is already open here — just read the value directly
    total = _read_total_from_open_modal(driver, wait)
    return Decimal(str(total))


def select_first_qc_option(driver, wait):
    """Select the first available and enabled QC option."""
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


def upload_grn_attachment(driver, wait, file_path):
    """Expand GRN details accordion and upload a file."""
    try:
        try:
            accordion = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='header accordian']//strong[contains(text(), 'GRN details')]")
            ))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", accordion)
            driver.execute_script("arguments[0].click();", accordion)
            logger.info("   ✅ GRN details accordion expanded")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"   ⚠️ Could not expand GRN details accordion: {e}")

        file_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='file'][id^='bank_upload_']")
        ))
        abs_path = os.path.abspath(file_path)
        file_input.send_keys(abs_path)
        logger.info(f"   ✅ File uploaded: {abs_path}")
        time.sleep(1)
    except Exception as e:
        logger.error(f"❌ Failed to upload GRN attachment: {e}")
        driver.save_screenshot("grn_attachment_error.png")
        raise


def generate_pb_excel_report(scraped_items, global_total_ui):
    """Generates a formatted Excel Audit showing Weight Reduction and Math Reconciliation."""
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

    total_gross   = df['Gross Quantity'].sum().round(2)
    total_net     = df['Net Quantity'].sum().round(2)
    total_reduced = df['Weight Reduced'].sum().round(2)
    total_labour  = df['Labour Charges'].sum().round(2)
    total_igst    = df['IGST Amount'].sum().round(2)
    sum_of_table_totals = df['Total Amount'].sum().round(2)
    global_total_ui = round(global_total_ui, 2)

    sum_row = pd.DataFrame({
        'PB Number': ['GRAND TOTALS'], 'Item Name': [''], 'Rate': [''],
        'Gross Quantity': [total_gross], 'Net Quantity': [total_net],
        'Empty Bag Weight (KG)': [''], 'Labour Charges': [total_labour],
        'IGST Amount': [total_igst], 'Total Amount': [sum_of_table_totals],
        'Weight Reduced': [total_reduced]
    })

    expected_ui_total = round(sum_of_table_totals - total_labour, 2)
    diff   = round(global_total_ui - expected_ui_total, 2)
    status = "✅ MATCHED" if abs(diff) < 0.01 else f"❌ DISCREPANCY: {diff:.2f}"

    recon_row = pd.DataFrame({
        'PB Number': ['MATH AUDIT'],
        'Item Name': [f'Global UI Total: {global_total_ui}'],
        'Rate': [f'Total Labour: {total_labour}'],
        'Gross Quantity': [f'Actual Table Sum: {sum_of_table_totals}'],
        'Net Quantity': [f'Calculated UI (Table - Labour): {expected_ui_total}'],
        'Empty Bag Weight (KG)': [status],
        'Labour Charges': [''], 'IGST Amount': [''],
        'Total Amount': [''], 'Weight Reduced': ['']
    })

    df = pd.concat([df, sum_row, recon_row], ignore_index=True)
    df = df[column_order]

    folder = "download_files"
    if not os.path.exists(folder):
        os.makedirs(folder)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = os.path.abspath(os.path.join(folder, f"PB_Audit_{timestamp}.xlsx"))

    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Audit', index=False)
        workbook  = writer.book
        worksheet = writer.sheets['Audit']

        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'vcenter',
            'align': 'center', 'bg_color': '#D9E1F2', 'border': 1
        })
        cell_format = workbook.add_format({
            'text_wrap': True, 'valign': 'vcenter', 'align': 'center', 'border': 1
        })

        for col_num, col_name in enumerate(df.columns):
            worksheet.write(0, col_num, col_name, header_format)
        for row_num in range(1, len(df) + 1):
            worksheet.set_row(row_num, None, cell_format)

        column_widths = {
            'A': 20, 'B': 30, 'C': 12, 'D': 15, 'E': 15,
            'F': 20, 'G': 15, 'H': 15, 'I': 18, 'J': 18
        }
        for col, width in column_widths.items():
            worksheet.set_column(f'{col}:{col}', width)

    logger.info(f"✅ Formatted Audit Report saved: {file_path}")


def search_and_export_latest_pb(driver, wait, supplier_raw_name):
    name = supplier_raw_name.split('-')[0].strip()
    logger.info(f"🔍 Auditing finalized data for: {name}")

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

    view_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//table/tbody/tr[1]//button[.//i[contains(@class, 'bi-eye')]]")
    ))
    driver.execute_script("arguments[0].click();", view_btn)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tableExport1 tbody tr")))
    logger.info("   ⏳ Loading PB Details & Calculations...")
    time.sleep(5)

    scraped_data = []

    def safe_f(v):
        try:
            return float(v) if v else 0.0
        except:
            return 0.0

    try:
        global_total_ui = safe_f(driver.find_element(
            By.CSS_SELECTOR, "input[formcontrolname='txn_currency_total_amount']"
        ).get_attribute("value"))
        pb_num = driver.find_element(
            By.CSS_SELECTOR, "input[formcontrolname='transaction_ref_no']"
        ).get_attribute("value")
        logger.info(f"   📊 UI Global Total: {global_total_ui} | PB: {pb_num}")
    except:
        global_total_ui, pb_num = 0.0, "N/A"

    rows = driver.find_elements(
        By.XPATH, "//table[@id='tableExport1']//tbody[contains(@class, 'main_tbody')]/tr"
    )
    logger.info(f"   Found {len(rows)} rows in the table.")
    for row in rows:
        try:
            item = row.find_element(By.CSS_SELECTOR, ".mat-mdc-select-min-line").text.strip()
            if not item:
                continue

            def get_val(selector):
                try:
                    return safe_f(row.find_element(By.CSS_SELECTOR, selector).get_attribute("value"))
                except:
                    return 0.0

            scraped_data.append({
                'PB Number':            pb_num,
                'Item Name':            item,
                'Rate':                 get_val("input[formcontrolname='rate']"),
                'Gross Quantity':       get_val("input[formcontrolname='alternate_qty']"),
                'Net Quantity':         get_val("input[formcontrolname='alternate_net_qty']"),
                'Empty Bag Weight (KG)':get_val("input[formcontrolname='empty_bag_weight']"),
                'Labour Charges':       get_val("input[formcontrolname='labour_charges']"),
                'IGST Amount':          get_val("input[formcontrolname='txn_currency_igst_amount']"),
                'Total Amount':         get_val("input[formcontrolname='txn_currency_total_txn_amount']")
            })
            logger.info(f"      Scraped: {item}")
        except Exception as e:
            logger.warning(f"      ⚠️ Skipped row: {e}")

    if scraped_data:
        generate_pb_excel_report(scraped_data, global_total_ui)
    else:
        driver.save_screenshot("scrape_failed.png")
        raise Exception("Failed to scrape table data! No rows found.")


def fill_purchase_booking_registration(driver, wait, data):
    logger.info("⚡ Starting Purchase Booking Registration...")

    try:
        logger.info("   ➡️ Waiting for page to completely settle...")
        time.sleep(3)
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ngx-spinner-overlay")))
        except:
            pass

        logger.info("   ➡️ Forcing click on '+ Add New Purchase Booking'...")
        add_btn = driver.find_element(By.CSS_SELECTOR, "button.new_employee")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", add_btn)
        logger.info("   ✅ Clicked 'Add New Purchase Booking' successfully!")
    except Exception as e:
        logger.error(f"❌ CRITICAL: Failed to click Add button: {e}")
        driver.save_screenshot("pb_add_button_error.png")
        raise

    logger.info("   ⏳ Waiting for PB form to load...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='supplier_ref_id']")))
    time.sleep(1)

    if 'transaction_date' in data:
        logger.info(f"   📅 Setting PB Transaction Date to: {data['transaction_date']}")
        fill_input(driver, wait, data['transaction_date'], control_name="transaction_date")

    select_dropdown(driver, wait, data['supplier'], control_name="supplier_ref_id")
    select_first_qc_option(driver, wait)
    time.sleep(3)

    select_dropdown(driver, wait, data['payment_terms'], control_name="supplier_payment_terms_ref_id", searchable=False)

    logger.info(f"   📦 Processing {len(data['items'])} items for Purchase Booking...")
    for index, item_data in enumerate(data['items']):
        item_name = item_data.get('item', '')
        logger.info(f"      ➡️ Setting details for Row {index + 1}: {item_name}")

        add_quantity_details(driver, wait, item_data['no_of_bags'], item_data['quantity'], index)

        row_xpath = f"//tbody/tr[{index + 1}]"
        row = wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))

        if item_name in {"Soyabean", "Turmeric", "Chana"}:
            tax_rate_to_use  = "5"
            igst_rate_to_use = "5"
        elif item_name == "Tur-Red":
            tax_rate_to_use  = "0"
            igst_rate_to_use = "0"
        else:
            tax_rate_to_use  = str(data.get('tax_rate', '0'))
            igst_rate_to_use = str(data.get('igst_rate', '0'))

        try:
            tax_dropdown = row.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='tax_rate']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tax_dropdown)
            driver.execute_script("arguments[0].click();", tax_dropdown)
            overlay = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")
            ))
            wait.until(EC.visibility_of(overlay))
            opt_xpath = f"//mat-option//span[normalize-space()='{tax_rate_to_use}']"
            tax_option = wait.until(EC.element_to_be_clickable((By.XPATH, opt_xpath)))
            driver.execute_script("arguments[0].click();", tax_option)
            time.sleep(0.5)
            logger.info(f"         ✅ Tax Rate set to {tax_rate_to_use}")
        except NoSuchElementException:
            logger.info(f"         ℹ️ Tax Rate dropdown not found for row {index + 1} – skipping")
        except Exception as e:
            logger.warning(f"         ⚠️ Could not set Tax Rate for row {index + 1}: {e}")

        try:
            igst_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_igst_rate']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", igst_input)
            driver.execute_script("arguments[0].click();", igst_input)
            igst_input.send_keys(Keys.CONTROL + "a")
            igst_input.send_keys(Keys.BACKSPACE)
            igst_input.send_keys(igst_rate_to_use)
            igst_input.send_keys(Keys.TAB)
            time.sleep(0.5)
            logger.info(f"         ✅ IGST Rate set to {igst_rate_to_use}")
        except NoSuchElementException:
            logger.info(f"         ℹ️ IGST Rate input not found for row {index + 1} – skipping")
        except Exception as e:
            logger.warning(f"         ⚠️ Could not set IGST Rate for row {index + 1}: {e}")

    upload_grn_attachment(driver, wait, data['attachment_file'])

    logger.info("📤 Submitting the Final Purchase Booking form...")
    final_submit_xpath = "//div[contains(@class, 'footer')]//button[@type='submit']"
    submit_button = wait.until(EC.presence_of_element_located((By.XPATH, final_submit_xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_button)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", submit_button)
    logger.info("✅ Final Submit button clicked")

    logger.info("   ⏳ Waiting to redirect to the PB List page...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
    time.sleep(3)
    logger.info("🚀 Purchase Booking Saved Successfully!")

    logger.info("\n🔍 Opening the newly saved PB to extract the finalized report...")
    # This opens the view modal — it stays open when this function returns
    search_and_export_latest_pb(driver, wait, data['supplier'])


def fill_purchase_booking_with_extra_fields(driver, wait, data):
    """
    Same as fill_purchase_booking_registration, but also fills
    empty_bag_weight and labour_charges if present in item_data.
    """
    logger.info("⚡ Starting Purchase Booking Registration (with extra fields)...")

    try:
        logger.info("   ➡️ Waiting for page to completely settle...")
        time.sleep(3)
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ngx-spinner-overlay")))
        except:
            pass

        logger.info("   ➡️ Forcing click on '+ Add New Purchase Booking'...")
        add_btn = driver.find_element(By.CSS_SELECTOR, "button.new_employee")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", add_btn)
        logger.info("   ✅ Clicked 'Add New Purchase Booking' successfully!")
    except Exception as e:
        logger.error(f"❌ CRITICAL: Failed to click Add button: {e}")
        driver.save_screenshot("pb_add_button_error.png")
        raise

    logger.info("   ⏳ Waiting for PB form to load...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[formcontrolname='supplier_ref_id']")))
    time.sleep(1)

    if 'transaction_date' in data:
        logger.info(f"   📅 Setting PB Transaction Date to: {data['transaction_date']}")
        fill_input(driver, wait, data['transaction_date'], control_name="transaction_date")

    select_dropdown(driver, wait, data['supplier'], control_name="supplier_ref_id")
    select_first_qc_option(driver, wait)
    time.sleep(3)

    select_dropdown(driver, wait, data['payment_terms'], control_name="supplier_payment_terms_ref_id", searchable=False)

    logger.info(f"   📦 Processing {len(data['items'])} items for Purchase Booking...")
    for index, item_data in enumerate(data['items']):
        item_name = item_data.get('item', '')
        logger.info(f"      ➡️ Setting details for Row {index + 1}: {item_name}")

        add_quantity_details(driver, wait, item_data['no_of_bags'], item_data['quantity'], index)

        row_xpath = f"//tbody/tr[{index + 1}]"
        row = wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))

        if item_name in {"Soyabean", "Turmeric", "Chana"}:
            tax_rate_to_use  = "5"
            igst_rate_to_use = "5"
        elif item_name == "Tur-Red":
            tax_rate_to_use  = "0"
            igst_rate_to_use = "0"
        else:
            tax_rate_to_use  = str(data.get('tax_rate', '0'))
            igst_rate_to_use = str(data.get('igst_rate', '0'))

        try:
            tax_dropdown = row.find_element(By.CSS_SELECTOR, "mat-select[formcontrolname='tax_rate']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tax_dropdown)
            driver.execute_script("arguments[0].click();", tax_dropdown)
            overlay = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "body > .cdk-overlay-container .cdk-overlay-pane:last-child")
            ))
            wait.until(EC.visibility_of(overlay))
            opt_xpath = f"//mat-option//span[normalize-space()='{tax_rate_to_use}']"
            tax_option = wait.until(EC.element_to_be_clickable((By.XPATH, opt_xpath)))
            driver.execute_script("arguments[0].click();", tax_option)
            time.sleep(0.5)
            logger.info(f"         ✅ Tax Rate set to {tax_rate_to_use}")
        except Exception as e:
            logger.warning(f"         ⚠️ Could not set Tax Rate for row {index + 1}: {e}")

        try:
            igst_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='txn_currency_igst_rate']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", igst_input)
            driver.execute_script("arguments[0].click();", igst_input)
            igst_input.send_keys(Keys.CONTROL + "a")
            igst_input.send_keys(Keys.BACKSPACE)
            igst_input.send_keys(igst_rate_to_use)
            igst_input.send_keys(Keys.TAB)
            time.sleep(0.5)
            logger.info(f"         ✅ IGST Rate set to {igst_rate_to_use}")
        except Exception as e:
            logger.warning(f"         ⚠️ Could not set IGST Rate for row {index + 1}: {e}")

        if 'empty_bag_weight' in item_data:
            try:
                ebw_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='empty_bag_weight']")
                ebw_input.clear()
                ebw_input.send_keys(str(item_data['empty_bag_weight']))
                logger.info(f"         ✅ Empty Bag Weight set to {item_data['empty_bag_weight']}")
            except Exception as e:
                logger.warning(f"         ⚠️ Could not set Empty Bag Weight: {e}")

        if 'labour_charges' in item_data:
            try:
                labour_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='labour_charges']")
                labour_input.clear()
                labour_input.send_keys(str(item_data['labour_charges']))
                logger.info(f"         ✅ Labour Charges set to {item_data['labour_charges']}")
            except Exception as e:
                logger.warning(f"         ⚠️ Could not set Labour Charges: {e}")

    upload_grn_attachment(driver, wait, data['attachment_file'])

    logger.info("📤 Submitting the Final Purchase Booking form...")
    final_submit_xpath = "//div[contains(@class, 'footer')]//button[@type='submit']"
    submit_button = wait.until(EC.presence_of_element_located((By.XPATH, final_submit_xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_button)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", submit_button)
    logger.info("✅ Final Submit button clicked")

    logger.info("   ⏳ Waiting to redirect to the PB List page...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-mdc-table")))
    time.sleep(3)
    logger.info("🚀 Purchase Booking Saved Successfully!")

    logger.info("\n🔍 Opening the newly saved PB to extract the finalized report...")
    search_and_export_latest_pb(driver, wait, data['supplier'])