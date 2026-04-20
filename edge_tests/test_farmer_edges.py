import pytest
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

import config
from common import auth_section, nav_section
from Registration import farmer_section
from data.test_data import farmer_data

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


class TestRegistrationEdgeCases:

    @pytest.fixture(autouse=True)
    def setup_and_navigate(self, driver, wait):
        driver.get(config.URL)
        auth_section.perform_login(driver, wait, config)
        nav_section.go_to_farmer_page(driver, wait)
        time.sleep(2)

    def test_prevent_double_submission_on_save(self, driver, wait):
        logger.info("\n[DEBUG] Filling mandatory fields to enable valid submission...")

        try:
            wait.until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".cdk-overlay-container, .ngx-spinner-overlay, .swal2-container")
                )
            )
        except TimeoutException:
            pass

        name_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[formcontrolname='name'], input#name"))
        )
        name_input.clear()
        name_input.send_keys("Robust Test Farmer")

        driver.find_element(By.ID, "email").send_keys(farmer_data["email"])
        driver.find_element(By.ID, "phone").send_keys("9876543210")
        driver.find_element(By.ID, "password").send_keys(farmer_data["password"])

        farmer_section.fill_datepicker(driver, wait, farmer_data["dob"])
        farmer_section.select_with_filter(driver, wait, "gender", farmer_data["gender"])
        farmer_section.select_with_filter(driver, wait, "cast_religion", farmer_data["caste"])

        addr_toggle = wait.until(EC.element_to_be_clickable((By.XPATH, "//strong[contains(text(), 'Address')]")))
        driver.execute_script("arguments[0].click();", addr_toggle)
        time.sleep(1)

        farmer_section.select_with_filter(driver, wait, "state_ref_id_id", farmer_data["state"])
        time.sleep(1)
        farmer_section.select_with_filter(driver, wait, "district_ref_id_id", farmer_data["district"])
        time.sleep(1)
        farmer_section.select_with_filter(driver, wait, "sub_district_ref_id_id", farmer_data["taluka"])
        time.sleep(1)
        farmer_section.select_with_filter(driver, wait, "village_ref_id_id", farmer_data["village"])

        driver.find_element(By.ID, "pincode").send_keys(farmer_data["pincode"])

        try:
            address1 = wait.until(EC.visibility_of_element_located((By.NAME, "Address1")))
            address1.send_keys("123 Test Street")
        except TimeoutException:
            pass

        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)

        logger.info("[DEBUG] Form valid. Clicking Submit Button...")
        submit_btn.click()

        def ui_locked(d):
            try:
                btn = d.find_element(By.CSS_SELECTOR, "button.submit")
                disabled = btn.get_attribute("disabled") is not None or "disabled" in (btn.get_attribute("class") or "")
            except StaleElementReferenceException:
                disabled = True

            overlay_present = len(
                d.find_elements(By.CSS_SELECTOR, ".cdk-overlay-backdrop-showing, .swal2-container, .ngx-spinner-overlay")
            ) > 0

            return disabled or overlay_present

        try:
            WebDriverWait(driver, 5).until(ui_locked)
            logger.info("[DEBUG] ✅ UI successfully locked down after click.")
        except TimeoutException:
            logger.info("[DEBUG] ❌ UI remained unlocked after click.")
            assert False, "BUG: Submit button remained clickable during save! UI did not lock down."

    # def test_required_field_errors_on_submit(self, driver, wait):
    #     """Verify clicking a clickable submit button on an empty form shows red errors."""
    #     
    #     # 1. Click the submit button
    #     submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.submit")))
    #     driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    #     driver.execute_script("arguments[0].click();", submit_btn)
    #     
    #     # 2. Wait a split second for the Angular animations to display the red text
    #     time.sleep(1) 
    #     
    #     # 3. Find the errors. We use presence, not visibility, just in case.
    #     errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
    #     
    #     # 4. Extract text using JavaScript to bypass visibility issues
    #     error_texts = [driver.execute_script("return arguments[0].textContent;", err).strip() for err in errors]
    #     error_texts = [text for text in error_texts if text != ""] # Filter out empty ones
    #     
    #     print(f"\n[DEBUG] Visible Error Texts Found: {error_texts}")
    #     
    #     # 5. Check if the expected errors appeared based on your app's actual output!
    #     assert "Farmer Name Is Required" in error_texts, "Validation missing for Farmer Name!"
    #     assert "Phone Number Is Required" in error_texts, "Validation missing for Phone Number!"
    #     assert "Date Of Birth Is Required" in error_texts, "Validation missing for DOB!"
    #     assert "State Is Required" in error_texts, "Validation missing for State!"
    #     assert "District Is Required" in error_texts, "Validation missing for District!"

    # def test_invalid_phone_number_length(self, driver, wait):
    #     """Verify entering a phone number with less than 10 digits triggers a validation error."""
    #     
    #     # 1. Enter the 5-digit bad phone number
    #     phone_input = wait.until(EC.visibility_of_element_located((By.ID, "phone")))
    #     phone_input.clear()
    #     phone_input.send_keys("12345")
    #     
    #     # 2. Force click the Submit button using JavaScript (just like in your working script!)
    #     # This guarantees the form tries to submit and forces all red errors to appear.
    #     submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
    #     driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    #     driver.execute_script("arguments[0].click();", submit_btn)
    #     
    #     # 3. Give Angular a full second to render the error texts
    #     time.sleep(1)
    #     
    #     # 4. Grab all visible error texts
    #     errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
    #     error_texts = [driver.execute_script("return arguments[0].textContent;", err).strip() for err in errors]
    #     error_texts = [text for text in error_texts if text != ""]
    #     
    #     print(f"\n[DEBUG] Errors after entering bad phone number: {error_texts}")
    #     
    #     # 5. Check if the app generated an error about the phone/mobile number
    #     # We convert everything to lowercase to make matching easier
    #     error_string_block = " ".join(error_texts).lower()
    #     
    #     assert "phone" in error_string_block or "mobile" in error_string_block or "valid" in error_string_block, "BUG: The form accepted a 5-digit phone number!"

    # def test_invalid_email_format(self, driver, wait):
    #     """Verify the system rejects an email address missing the @ symbol and domain."""
    #     
    #     # 1. Enter an invalid email format
    #     email_input = wait.until(EC.visibility_of_element_located((By.ID, "email")))
    #     email_input.clear()
    #     email_input.send_keys("nilesh.tidake_at_godafarm") # Intentionally missing @ and .com
    #     
    #     # 2. Force click Submit using our reliable JavaScript method
    #     submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
    #     driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    #     driver.execute_script("arguments[0].click();", submit_btn)
    #     
    #     # 3. Give Angular a second to render
    #     time.sleep(1)
    #     
    #     # 4. Grab all visible error texts and convert to lowercase for easy matching
    #     errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
    #     error_texts = [driver.execute_script("return arguments[0].textContent;", err).strip().lower() for err in errors if err != ""]
    #     
    #     print(f"\n[DEBUG] Email Test Errors: {error_texts}")
    #     
    #     # 5. Assert the system caught the bad email
    #     error_string_block = " ".join(error_texts)
    #     assert "email" in error_string_block or "valid" in error_string_block, "BUG: The form accepted an invalid email format!"

    # def test_pincode_rejects_letters(self, driver, wait):
    #     """Verify the pincode field strictly enforces numeric input by rejecting letters."""
    #     
    #     # 1. Expand the Address section first (since Pincode is hidden inside it)
    #     addr_toggle = wait.until(EC.element_to_be_clickable((By.XPATH, "//strong[contains(text(), 'Address')]")))
    #     driver.execute_script("arguments[0].scrollIntoView({block:'center'});", addr_toggle)
    #     driver.execute_script("arguments[0].click();", addr_toggle)
    #     time.sleep(1) # Wait for the accordion animation to open

    #     # 2. Enter letters into the Pincode field
    #     pincode_input = wait.until(EC.visibility_of_element_located((By.ID, "pincode")))
    #     pincode_input.clear()
    #     pincode_input.send_keys("ABCDEF")
    #     
    #     # 3. Force click Submit
    #     submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit")))
    #     driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    #     driver.execute_script("arguments[0].click();", submit_btn)
    #     
    #     # 4. Grab all visible error texts
    #     time.sleep(1)
    #     errors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "mat-error")))
    #     error_texts = [driver.execute_script("return arguments[0].textContent;", err).strip().lower() for err in errors if err != ""]
    #     
    #     print(f"\n[DEBUG] Pincode Test Errors: {error_texts}")
    #     
    #     # 5. Assert the system caught the alphabetical characters
    #     error_string_block = " ".join(error_texts)
    #     assert "pincode" in error_string_block or "number" in error_string_block or "invalid" in error_string_block, "BUG: The form accepted letters in the Pincode field!"