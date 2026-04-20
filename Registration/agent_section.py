from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import logging
from common.helper import select_dropdown, fill_input, click_submit

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

def expand_section(driver, wait, section_text):
    """Expands an accordion section by clicking the header containing the given text."""
    try:
        header = wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//div[@class='header accordian']//strong[contains(text(), '{section_text}')]")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", header)
        header.click()
        time.sleep(1)
        logger.info(f"   ✅ Expanded '{section_text}' section")
    except Exception as e:
        logger.warning(f"⚠️ Could not expand section '{section_text}': {e}")

def fill_bank_details_agent(driver, wait, bank_data):
    logger.info("🏦 Filling Agent Bank Details...")
    fill_input(driver, wait, bank_data['bank_name'], control_id="bank_name")
    fill_input(driver, wait, bank_data.get('branch_name', ''), control_id="bank_branch_code")
    fill_input(driver, wait, bank_data['ifsc'], control_id="bank_ifsc_code")
    select_dropdown(driver, wait, bank_data['account_type'], control_id="account_type0", searchable=False)
    fill_input(driver, wait, bank_data['account_holder_name'], control_id="bank_account_holder_name")
    fill_input(driver, wait, bank_data['account_number'], control_id="bank_account_no")
    select_dropdown(driver, wait, bank_data['bank_proof'], control_id="bank_doc_id0", searchable=False)

    if 'bank_proof_file' in bank_data and bank_data['bank_proof_file']:
        logger.info("📂 Uploading bank proof file...")
        try:
            file_input = None
            selectors = [
                "input[type='file']",
                "input#bank_proof_file",
                "input[name='bank_proof']",
                "//input[@type='file' and contains(@id,'bank')]",
                "//div[contains(@class,'bank')]//input[@type='file']"
            ]
            for selector in selectors:
                try:
                    if selector.startswith("//"):
                        file_input = driver.find_element(By.XPATH, selector)
                    else:
                        file_input = driver.find_element(By.CSS_SELECTOR, selector)
                    if file_input:
                        logger.info(f"   Found file input using: {selector}")
                        break
                except:
                    continue

            if not file_input:
                raise Exception("File input not found with any selector")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", file_input)
            time.sleep(0.5)
            abs_path = os.path.abspath(bank_data['bank_proof_file'])
            file_input.send_keys(abs_path)
            logger.info(f"   ✅ Uploaded: {abs_path}")
            time.sleep(2)
        except Exception as e:
            logger.warning(f"⚠️ Failed to upload bank proof: {e}")
    else:
        logger.warning("⚠️ No bank proof file path provided. Skipping upload.")
    logger.info("🏦 Agent Bank details filled.")

def fill_agent_registration(driver, wait, data):
    logger.info("⚡ Starting Agent Registration...")

    # --- Basic Info ---
    fill_input(driver, wait, data['agent_name'], control_id="agent_name")
    fill_input(driver, wait, data['phone'], control_id="phone")
    fill_input(driver, wait, data['email'], control_id="email")
    select_dropdown(driver, wait, data['basis_type'], control_id="basis_type_id", searchable=True)
    fill_input(driver, wait, str(data['commission']), control_id="commission")

    expand_section(driver, wait, "Address Details") 
    
    # --- Address / Location fields (already visible) ---
    select_dropdown(driver, wait, data['state'], control_id="state_ref_id_id", searchable=True)
    time.sleep(1)
    select_dropdown(driver, wait, data['district'], control_id="district_ref_id_id", searchable=True)
    time.sleep(1)
    select_dropdown(driver, wait, data['taluka'], control_id="sub_district_ref_id_id", searchable=True)
    time.sleep(1)
    select_dropdown(driver, wait, data['village'], control_id="village_ref_id", searchable=True)

    # Address textarea (using NAME since ID is dynamic)
    address_input = wait.until(EC.visibility_of_element_located((By.NAME, "Address")))
    address_input.clear()
    address_input.send_keys(data['address'])

    fill_input(driver, wait, data['pincode'], control_id="pincode")

    # --- Expand Payment Details ---
    expand_section(driver, wait, "Payment Details")
    if 'payment_terms' in data:
        select_dropdown(driver, wait, data['payment_terms'], control_id="payment_terms", searchable=False)
    if 'preferred_payment_method' in data:
        select_dropdown(driver, wait, data['preferred_payment_method'], control_id="preferred_payment_method", searchable=False)

    # --- Expand Agent Bank Details ---
    expand_section(driver, wait, "Agent Bank Details")
    if 'bank' in data:
        fill_bank_details_agent(driver, wait, data['bank'])

    # --- Submit Button ---
    logger.info("📤 Submitting the form...")
    time.sleep(1)
    click_submit(driver, wait)

    time.sleep(3)
    logger.info("🚀 Agent Registration Completed Successfully!")