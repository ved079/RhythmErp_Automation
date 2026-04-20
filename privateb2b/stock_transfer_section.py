from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from common.helper import select_dropdown, fill_input, click_submit

logger = logging.getLogger(__name__)


def fill_stock_transfer(driver, wait, data):
    """
    Creates a single stock transfer entry.

    Expected keys in `data`:
        transaction_date   – date string for the header datepicker
        item_type          – header item type dropdown value
        from_department    – source department
        from_division      – source division
        from_sale_type     – source sale type
        from_location      – source location (triggers item list population)
        item_name          – item to transfer (searchable dropdown)
        to_department      – destination department (table row)
        to_division        – destination division (table row)
        to_sale_type       – destination sale type (table row)
        to_location        – destination location (table row)
        transfer_quantity  – numeric quantity to transfer
    """
    logger.info("⚡ Starting Stock Transfer Creation...")

    # ------------------------------------------------------------------ #
    # 1. Header fields                                                     #
    # ------------------------------------------------------------------ #

    fill_input(driver, wait, data['transaction_date'], control_name="transaction_date")

    select_dropdown(driver, wait, data['item_type'],
                    control_name="item_type_ref_id", searchable=False)

    select_dropdown(driver, wait, data['from_department'],
                    control_name="department_ref_id", searchable=False)

    select_dropdown(driver, wait, data['from_division'],
                    control_name="division_ref_id", searchable=False)

    select_dropdown(driver, wait, data['from_sale_type'],
                    control_name="sale_type_ref_id", searchable=False)

    # from_location selection triggers a backend call to populate the item list —
    # post_open_wait gives Angular time to finish loading options after it closes.
    select_dropdown(driver, wait, data['from_location'],
                    control_name="from_location_ref_id", searchable=False)

    logger.info("⏳ Waiting for item list to populate after location selection...")
    time.sleep(1.5)  # Allow backend to respond and Angular to bind the item options

    # Item Name — searchable; post_open_wait gives extra time for dynamic options
    select_dropdown(driver, wait, data['item_name'],
                    control_name="item_ref_id", searchable=True, post_open_wait=1.0)

    logger.info("⏳ Waiting for available stock to load after item selection...")
    time.sleep(1.5)  # Allow the table row to appear with stock data

    # ------------------------------------------------------------------ #
    # 2. First row in the transfer table                                   #
    # ------------------------------------------------------------------ #

    row = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.main_tbody tr")))
    logger.info("   📋 Table row located, filling destination fields...")

    _select_row_dropdown(driver, wait, row, "department_ref_id", data['to_department'])
    _select_row_dropdown(driver, wait, row, "division_ref_id",   data['to_division'])
    _select_row_dropdown(driver, wait, row, "sale_type_ref_id",  data['to_sale_type'])
    _select_row_dropdown(driver, wait, row, "location_ref_id",   data['to_location'])

    # Transfer quantity
    qty_input = row.find_element(By.CSS_SELECTOR, "input[formcontrolname='transfer_quantity']")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", qty_input)
    qty_input.clear()
    qty_input.send_keys(str(data['transfer_quantity']))
    logger.info(f"   ✅ Quantity set: {data['transfer_quantity']} units → {data['to_location']}")

    # ------------------------------------------------------------------ #
    # 3. Submit                                                            #
    # ------------------------------------------------------------------ #

    logger.info("📤 Submitting Stock Transfer...")
    click_submit(driver, wait)
    time.sleep(3)
    logger.info("🚀 Stock Transfer Completed Successfully!")


# ------------------------------------------------------------------ #
# Private helpers                                                      #
# ------------------------------------------------------------------ #

def _get_fresh_overlay(driver):
    """Returns the visible overlay pane or None."""
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".cdk-overlay-pane")
        if el.is_displayed():
            return el
    except Exception:
        pass
    return None


def _wait_overlay_close(driver, timeout=10):
    """Polls until the overlay pane is gone or hidden."""
    end = time.time() + timeout
    while time.time() < end:
        try:
            el = driver.find_element(By.CSS_SELECTOR, ".cdk-overlay-pane")
            if not el.is_displayed():
                return
        except Exception:
            return  # Element removed from DOM
        time.sleep(0.2)
    raise TimeoutError("Overlay did not close after row dropdown selection.")


def _select_row_dropdown(driver, wait, row, control_name, value):
    """
    Opens a mat-select inside a table row and selects the matching option.

    Fetches a fresh overlay reference before every DOM query to avoid
    stale element exceptions after Angular re-renders.
    """
    dropdown = row.find_element(By.CSS_SELECTOR, f"mat-select[formcontrolname='{control_name}']")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
    driver.execute_script("arguments[0].click();", dropdown)

    # Wait for overlay to appear
    wait.until(lambda d: _get_fresh_overlay(driver) is not None)
    time.sleep(0.4)  # Let options render

    option_xpath = f".//mat-option[contains(normalize-space(.), '{value}')]"

    def find_option(d):
        fresh = _get_fresh_overlay(driver)
        if not fresh:
            return None
        try:
            return fresh.find_element(By.XPATH, option_xpath)
        except Exception:
            return None

    option = wait.until(find_option)
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
    driver.execute_script("arguments[0].click();", option)
    logger.info(f"   ✅ Row field '{control_name}' → '{value}'")

    _wait_overlay_close(driver)