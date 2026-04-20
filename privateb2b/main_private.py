import sys
import os

# THE FIX: This must happen before ANY custom imports so Python knows where the root folder is.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from privateb2b.test_cases import stock_transfer_recon
from privateb2b import stock_transfer_section
from privateb2b.purchase import gatepass_section, grn_section, purchase_booking_section, qc_section
from privateb2b.sales import dispatch_note_section, invoice_section, lot_creation_section, receipt_section, sales_order_section
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import config
from common import auth_section, nav_section
from reports.all_reports import inventory_report1
from data.test_data import (
    gatepass_data, 
    grn_data, 
    qc_data, 
    purchase_booking_data,
    sales_order_data,
    dispatch_note_data,
    invoice_data,
    receipt_data,
    stock_transfer_data
    
)
import time

driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 60)

try:
    auth_section.perform_login(driver, wait, config)
    
    # --- Execute the Stock Transfer Reconciliation Test ---
    # stock_transfer_recon.run_stock_transfer_reconciliation(driver, wait)

    
    # nav_section.go_to_stock_transfer_page(driver, wait)
    # stock_transfer_section.fill_stock_transfer(driver, wait, stock_transfer_data)
    
    nav_section.go_to_gatepass_page(driver, wait)
    gatepass_section.fill_gatepass_registration(driver, wait, gatepass_data)

    nav_section.go_to_grn_page(driver, wait)
    grn_section.fill_grn_registration(driver, wait, grn_data)
    grn_section.approve_latest_grn(driver, wait)

    nav_section.go_to_qc_page(driver, wait)
    qc_section.fill_qc_registration(driver, wait, qc_data)

    nav_section.go_to_purchase_booking_page(driver, wait)
    purchase_booking_section.fill_purchase_booking_registration(driver, wait, purchase_booking_data)

    # # # -------------------------------------------------------------------------
    # # # INVENTORY VERIFICATION (Multi-Item Upgraded)
    # # # We pass purchase_booking_data directly because it contains the 'items' list
    # # # -------------------------------------------------------------------------
    # # # inventory_report.go_to_inventory_summary(driver, wait)
    # # # inventory_report.verify_inventory_after_purchase(driver, wait, purchase_booking_data)

    # # # print("✅ SUCCESS: All Purchase and Inventory verification completed")
    # # # time.sleep(20)



    # nav_section.go_to_sales_order_page(driver, wait)
    # sales_order_section.fill_sales_order_registration(driver, wait, sales_order_data)

    # nav_section.go_to_lot_creation_page(driver, wait)
    # # Pass the entire 'items' array over to the lot creation script
    # lot_creation_section.fill_lot_creation(driver, wait, {
    #     "customer_name": sales_order_data['customer_name'],
    #     "items": sales_order_data['items'] 
    # })
    
    # nav_section.go_to_dispatch_note_page(driver, wait)
    # dispatch_note_section.fill_dispatch_note_registration(driver, wait, dispatch_note_data)

    # nav_section.go_to_invoice_page(driver, wait)
    # invoice_section.fill_invoice_registration(driver, wait, invoice_data)

    # nav_section.go_to_receipt_page(driver, wait)
    # receipt_section.fill_receipt_registration(driver, wait, receipt_data)


finally:
    driver.quit()