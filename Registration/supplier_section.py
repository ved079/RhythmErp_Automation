from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import logging
from common.helper import select_dropdown, click_submit

# Set up module-level logger (same format as helper)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

# ---------------- HELPER TO EXPAND ACCORDION SECTION ---------------- #
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

# ---------------- ADDRESS HELPER (uses select_dropdown) ---------------- #
def fill_address(driver, wait, index, address_data):
    logger.info(f"   📍 Filling Address Block {index}...")
    select_dropdown(driver, wait, address_data['address_type'], control_id=f"address_type{index}", searchable=True)

    address_inputs = driver.find_elements(By.NAME, "Address")
    if len(address_inputs) > index:
        address_input = address_inputs[index]
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", address_input)
        address_input.clear()
        address_input.send_keys(address_data['address'])
    else:
        logger.warning(f"⚠️ Address textarea with index {index} not found")

    select_dropdown(driver, wait, address_data['state'], control_id=f"state_ref_id_id{index}", searchable=True)
    time.sleep(1)
    select_dropdown(driver, wait, address_data['district'], control_id=f"district_ref_id_id{index}", searchable=True)
    time.sleep(1)
    select_dropdown(driver, wait, address_data['taluka'], control_id=f"sub_district_ref_id_id{index}", searchable=True)
    time.sleep(1)
    select_dropdown(driver, wait, address_data['village'], control_id=f"village_ref_id{index}", searchable=True)

    pin_inputs = driver.find_elements(By.ID, "pin_code")
    if len(pin_inputs) > index:
        pin_input = pin_inputs[index]
        pin_input.clear()
        pin_input.send_keys(address_data['pin_code'])
    else:
        logger.warning(f"⚠️ Pincode input with index {index} not found")

    if 'country' in address_data:
        select_dropdown(driver, wait, address_data['country'], control_id=f"country_ref_id_id{index}", searchable=True)

    logger.info(f"   ✅ Address Block {index} filled.")

# ---------------- BANK DETAILS HELPER (with file upload) ---------------- #
def fill_bank_details(driver, wait, bank_data):
    logger.info("🏦 Filling Bank Details...")
    driver.find_element(By.ID, "bank_name").send_keys(bank_data['bank_name'])
    driver.find_element(By.ID, "bank_branch_code").send_keys(bank_data.get('branch_name', ''))
    driver.find_element(By.ID, "bank_ifsc_code").send_keys(bank_data['ifsc'])
    select_dropdown(driver, wait, bank_data['account_type'], control_id="account_type0", searchable=False)
    driver.find_element(By.ID, "bank_account_holder_name").send_keys(bank_data['account_holder_name'])
    driver.find_element(By.ID, "bank_account_no").send_keys(bank_data['account_number'])
    select_dropdown(driver, wait, bank_data['bank_proof'], control_id="bank_doc_id0", searchable=False)

    # ---- Upload bank proof file ----
    if 'bank_proof_file' in bank_data and bank_data['bank_proof_file']:
        logger.info("📂 Uploading bank proof file...")
        try:
            # Try multiple possible selectors to find the file input
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

            # Scroll to and send the file
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
    logger.info("🏦 Bank details filled.")

# ---------------- MAIN SUPPLIER FORM FUNCTION ---------------- #
def fill_supplier_registration(driver, wait, data):
    logger.info("⚡ Starting Supplier Registration...")

    # --- Basic Info (already visible) ---
    select_dropdown(driver, wait, data['supplier_status'], control_id="supplier_status", searchable=True)
    driver.find_element(By.ID, "company_name").send_keys(data['company_name'])
    select_dropdown(driver, wait, data['po_type_ref_id'], control_id="po_type_ref_id", searchable=True)
    driver.find_element(By.ID, "email_id").send_keys(data['email_id'])
    driver.find_element(By.ID, "mobile_no").send_keys(data['mobile_no'])
    driver.find_element(By.ID, "pan_no").send_keys(data['pan_no'])
    select_dropdown(driver, wait, data['ownership_status_ref_id'], control_id="ownership_status_ref_id", searchable=True)
    time.sleep(4)
    # --- Expand Additional Details ---
    expand_section(driver, wait, "Additional Details")

    contact_name = wait.until(EC.visibility_of_element_located((By.ID, "display_name_as")))
    contact_name.send_keys(data.get('contact_person_name', ''))

    office = wait.until(EC.visibility_of_element_located((By.ID, "office_no")))
    office.send_keys(data.get('office_number', ''))

    if 'payment_terms' in data:
        select_dropdown(driver, wait, data['payment_terms'], control_id="payment_terms_ref_id", searchable=False)
    if 'delivery_terms' in data:
        select_dropdown(driver, wait, data['delivery_terms'], control_id="delivery_terms_ref_id", searchable=False)
    if 'mode_of_delivery' in data:
        select_dropdown(driver, wait, data['mode_of_delivery'], control_id="mode_of_delivery_ref_id", searchable=False)

    # --- Expand Supplier Details (addresses) ---
    expand_section(driver, wait, "Supplier Details")
    time.sleep(4)

    logger.info("📍 Handling Addresses...")
    fill_address(driver, wait, 0, data['billing_address'])

    add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.apply-button")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    add_btn.click()
    time.sleep(2)

    fill_address(driver, wait, 1, data['shipping_address'])

    if 'gstin' in data:
        gstin_input = driver.find_element(By.ID, "gstin")
        gstin_input.clear()
        gstin_input.send_keys(data['gstin'])

    # --- Expand Supplier Bank Details ---
    expand_section(driver, wait, "Supplier Bank Details")
    time.sleep(4)

    if 'bank' in data:
        fill_bank_details(driver, wait, data['bank'])

    # --- Submit Button ---
    logger.info("📤 Submitting the form...")
    time.sleep(1)
    click_submit(driver, wait)

    time.sleep(2)
    logger.info("🚀 Supplier Registration Completed Successfully!")