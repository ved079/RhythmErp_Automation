import sys
import os

# This points to the folder ABOVE 'reports', which is your project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.chrome.options import Options

chrome_options = Options()
prefs = {
    "download.default_directory": r"C:\Users\vedantd\Downloads",  # change to your folder
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--safebrowsing-disable-download-protection")

driver = webdriver.Chrome(options=chrome_options)
from common import auth_section  # Now this will work!s
# ... rest of your imports
from reports.all_reports.trial_balance import run as run_trial_balance
from reports.all_reports.balance_sheet import run as run_balance_sheet
from reports.all_reports.profit_loss import run as run_profit_loss
from reports.all_reports.payable import run_payable
from reports.all_reports.receivable import run_rec
from reports.all_reports.inventory_report1 import run as ir
from reports.all_reports.inventory_summary import run as ir1
from reports.all_reports.ageing_report import run as ir2
from reports.all_reports.ledger_enquiry import run as ir3
from reports.all_reports.day_book import run as ir4
from reports.all_reports.sales_order_status import run as ir5
from reports.all_reports.supplier_balance import run as ir6
from reports.all_reports.customer_balance import run as ir7
from reports.all_reports.statistics import run as ir8
from reports.all_reports.weighted_average_rate import run as ir9
from data.test_data import (trial_balance_data, balance_sheet_data, 
profit_loss_data, payable_data, receivable_data, inventory_report_data, 
inventory_summary_data, ageing_report_data, ledger_enquiry_data, day_book_data, sales_order_data
, supplier_balance_data, customer_balance_data, statistics_data, weighted_average_rate_data)
import config
import time

def set_download_preferences(driver, download_dir):
    driver.execute_cdp_cmd('Page.setDownloadBehavior', {
        'behavior': 'allow',
        'downloadPath': download_dir
    })

def main():
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)

    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)
    set_download_preferences(driver, download_dir)

    try:
        print("\n🔐 Logging in...")
        auth_section.perform_login(driver, wait, config)

        # run_trial_balance(driver, wait, trial_balance_data)
        # run_balance_sheet(driver, wait, balance_sheet_data)
        # ir2(driver, wait, ageing_report_data)
        run_profit_loss(driver, wait, profit_loss_data)
        run_payable(driver, wait, payable_data)
        run_rec(driver, wait, receivable_data)
        ir(driver, wait, inventory_report_data)
        ir1(driver, wait, inventory_summary_data)
        ir3(driver, wait, ledger_enquiry_data)
        ir4(driver, wait, day_book_data)
        ir5(driver, wait, sales_order_data)
        ir6(driver, wait, supplier_balance_data)
        ir7(driver, wait, customer_balance_data)
        ir8(driver, wait, statistics_data)
        ir9(driver, wait, weighted_average_rate_data)




    except Exception as e:
        print(f"\n❌ Error: {e}")
        driver.save_screenshot("trial_balance_error.png")
        raise
    finally:
        time.sleep(3)
        driver.quit()

if __name__ == "__main__":
    main()