# Registration/customer_section.py
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

# ---------------- HELPER TO EXPAND ACCORDION SECTION ---------------- #
def expand_section(driver, wait, section_text):
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

# ---------------- ADDRESS HELPER (with index) ---------------- #
def fill_address_customer(driver, wait, index, address_data):
    logger.info(f"   📍 Filling Customer Address Block {index}...")

    if 'address_type' in address_data:
        select_dropdown(driver, wait, address_data['address_type'], control_id=f"address_type{index}", searchable=True)

    address_inputs = driver.find_elements(By.ID, "address")
    if len(address_inputs) > index:
        address_input = address_inputs[index]
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", address_input)
        address_input.clear()
        address_input.send_keys(address_data['address'])
    else:
        logger.warning(f"⚠️ Address input with index {index} not found")

    select_dropdown(driver, wait, address_data['state'], control_id=f"state_ref_id_id{index}", searchable=True)
    time.sleep(1)
    select_dropdown(driver, wait, address_data['district'], control_id=f"district_ref_id_id{index}", searchable=True)
    time.sleep(1)
    select_dropdown(driver, wait, address_data['taluka'], control_id=f"sub_district_ref_id_id{index}", searchable=True)
    time.sleep(1)
    select_dropdown(driver, wait, address_data['village'], control_id=f"village_ref_id{index}", searchable=True)
    time.sleep(1)

    pin_inputs = driver.find_elements(By.ID, "pin_code")
    if len(pin_inputs) > index:
        pin_input = pin_inputs[index]
        pin_input.clear()
        pin_input.send_keys(address_data['pin_code'])
    else:
        logger.warning(f"⚠️ Pincode input with index {index} not found")

    logger.info(f"   ✅ Customer Address Block {index} filled.")

# ---------------- BANK DETAILS HELPER (with file upload) ---------------- #
def fill_bank_details_customer(driver, wait, bank_data):
    logger.info("🏦 Filling Customer Bank Details...")
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
    logger.info("🏦 Customer Bank details filled.")

# ---------------- MAIN CUSTOMER FORM FUNCTION ---------------- #
def fill_customer_registration(driver, wait, data):
    logger.info("⚡ Starting Customer Registration...")

    company_name_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#company_name[name='Company Name']")))
    time.sleep(0.5)
    company_name_input.send_keys(data['company_name'])

    select_dropdown(driver, wait, data['supply_type'], control_id="supply_type_ref_id", searchable=True)
    select_dropdown(driver, wait, data['customer_type'], control_id="customer_type_ref_id", searchable=True)
    select_dropdown(driver, wait, data['sale_type'], control_id="sale_type_ref_id", searchable=True)

    # Give the page a moment to update after sale type selection
    time.sleep(1)

    # Use control_id for fields that have an id but no formcontrolname
    fill_input(driver, wait, data['email'], control_id="email_id")
    fill_input(driver, wait, data['mobile'], control_id="mobile_no")
    fill_input(driver, wait, data['pan'], control_id="pan_no")

    select_dropdown(driver, wait, data['ownership_status'], control_id="ownership_status_ref_id", searchable=True)

    # --- Expand Additional Details ---
    expand_section(driver, wait, "Additional Details")

    fill_input(driver, wait, data.get('contact_person', ''), control_id="display_name_as")
    fill_input(driver, wait, data.get('office_number', ''), control_id="office_no")

    if 'preferred_payment_method' in data:
        select_dropdown(driver, wait, data['preferred_payment_method'], control_id="preferred_payment_method_ref_id", searchable=False)
    if 'gst_registration_type' in data:
        select_dropdown(driver, wait, data['gst_registration_type'], control_id="gst_registration_type", searchable=False)
    if 'payment_terms' in data:
        select_dropdown(driver, wait, data['payment_terms'], control_id="payment_terms_ref_id", searchable=False)
    if 'delivery_terms' in data:
        select_dropdown(driver, wait, data['delivery_terms'], control_id="delivery_terms_ref_id", searchable=False)
    if 'mode_of_delivery' in data:
        select_dropdown(driver, wait, data['mode_of_delivery'], control_id="mode_of_delivery_ref_id", searchable=False)
    if 'courier_terms' in data:
        select_dropdown(driver, wait, data['courier_terms'], control_id="courier_terms_ref_id", searchable=False)

    # Deposit, Quantity Tolerance, Rate Tolerance
    fill_input(driver, wait, str(data.get('deposit', '0')), control_id="deposit")
    fill_input(driver, wait, str(data.get('quantity_tolerance', '0')), control_id="quantity_tolerance")
    fill_input(driver, wait, str(data.get('rate_tolerance', '0')), control_id="rate_tolerance")

    # --- Expand Customer Details (addresses) ---
    expand_section(driver, wait, "Customer Details")

    if 'billing_address' in data:
        fill_address_customer(driver, wait, 0, data['billing_address'])

    add_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.apply-button")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    driver.execute_script("arguments[0].click();", add_btn) # <--- JAVASCRIPT CLICK
    time.sleep(2)

    if 'shipping_address' in data:
        fill_address_customer(driver, wait, 1, data['shipping_address'])

    # --- Expand Customer Bank Details ---
    expand_section(driver, wait, "Customer Bank Details")
    if 'bank' in data:
        fill_bank_details_customer(driver, wait, data['bank'])

    # --- Submit Button ---
    logger.info("📤 Submitting the form...")
    time.sleep(1)
    click_submit(driver, wait)

    time.sleep(3)
    logger.info("🚀 Customer Registration Completed Successfully!")