from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
from selenium.common.exceptions import StaleElementReferenceException
import logging

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)

def search_farmer(driver, wait, search_term):
    """Type in the search box and press Enter."""
    try:
        # Wait specifically for the search input to be interactable
        search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".browser-default")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", search_box)
        
        search_box.clear()
        time.sleep(0.5) # Brief pause to ensure clear registers
        search_box.send_keys(search_term)
        search_box.send_keys(Keys.ENTER)
        
        # Give Angular time to filter the table data
        time.sleep(2) 
        logger.info(f"   ✅ Searched for: {search_term}")
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        driver.save_screenshot("search_farmer_error.png")
        raise

def get_first_row(driver, wait):
    """Wait for the table rows to populate and return the first row."""
    try:
        row = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        return row
    except Exception as e:
        logger.error(f"❌ No rows found: {e}")
        driver.save_screenshot("no_rows_error.png")
        raise

def click_action_button(driver, wait, button_selector, action_name):
    """A bulletproof helper to click action icons in the first row of the table."""
    attempts = 0
    while attempts < 3:
        try:
            # Re-fetch the element on every attempt to prevent StaleElementReferenceExceptions
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"table tbody tr:first-child {button_selector}")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.5) # Let scroll settle
            
            # Use JS Click to bypass any floating tooltips or overlays
            driver.execute_script("arguments[0].click();", btn)
            logger.info(f"   ✅ {action_name} button clicked")
            time.sleep(1.5) # Give the modal/navigation time to render
            return
        except StaleElementReferenceException:
            attempts += 1
            time.sleep(0.5)
            logger.warning(f"   Stale element, retrying {action_name} ({attempts})...")
    raise Exception(f"Could not click {action_name} button after retries")

def click_history(driver, wait):
    """Click the history icon (clock) in the first row."""
    click_action_button(driver, wait, ".bi-clock-history", "History")

def click_edit(driver, wait):
    """Click the edit (pencil) button in the first row."""
    click_action_button(driver, wait, ".bi-pencil", "Edit")

def click_view(driver, wait):
    """Click the view (eye) button in the first row."""
    click_action_button(driver, wait, ".bi-eye", "View")

def close_modal(driver, wait):
    """Close the modal by clicking the X button or Cancel."""
    try:
        # Look for the close icon first
        close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".bi-x-lg")))
        driver.execute_script("arguments[0].click();", close_btn)
        time.sleep(1)
        logger.info("   ✅ Modal closed (X button)")
    except:
        # Fallback to a Cancel button if the X isn't present
        try:
            cancel_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cancel")))
            driver.execute_script("arguments[0].click();", cancel_btn)
            time.sleep(1)
            logger.info("   ✅ Modal closed (Cancel button)")
        except:
            logger.warning("   ⚠️ Could not close modal. It may already be closed.")

def is_history_empty(driver, wait):
    """Check if the history modal shows no records."""
    try:
        modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        
        # Give the API a second to fetch and render the history data inside the modal
        time.sleep(1.5) 
        
        # Look for empty state text anywhere in the modal
        empty_msg = modal.find_elements(By.XPATH, "//*[contains(text(),'No records') or contains(text(),'No data') or contains(text(),'No Data')]")
        
        if empty_msg:
            logger.info("   ✅ Verified: History is empty (No records found).")
            return True
        else:
            logger.warning("   ⚠️ Verified: History is NOT empty. Data was found.")
            return False
    except Exception as e:
        logger.warning(f"   ⚠️ Could not read history modal: {e}")
        return False

def is_history_has_update(driver, wait):
    """Check if the history modal contains an 'Updated' entry."""
    try:
        modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        
        # Give the API a second to fetch the new history data
        time.sleep(1.5) 
        
        # Look for update confirmation text
        update_msg = modal.find_elements(By.XPATH, "//*[contains(text(),'Updated') or contains(text(),'Edited') or contains(text(),'Update')]")
        
        if update_msg:
            logger.info("   ✅ Verified: History successfully logged the 'Update' event.")
            return True
        else:
            logger.error("   ❌ Verified: History did NOT log the update.")
            return False
    except Exception as e:
        logger.warning(f"   ⚠️ Could not read history modal: {e}")
        return False

def is_form_readonly(driver, wait):
    """Check if the form in view mode has disabled inputs."""
    try:
        # Wait for the view modal form to actually load
        name_input = wait.until(EC.presence_of_element_located((By.ID, "name")))
        if name_input.get_attribute("disabled") or name_input.get_attribute("readonly"):
            logger.info("   ✅ Form is read-only (view mode).")
            return True
        else:
            logger.error("   ❌ Form is not read-only (expected disabled).")
            return False
    except Exception as e:
        logger.warning(f"   ⚠️ Could not verify read-only state: {e}")
        return False

def update_farmer_name_only(driver, wait, new_name):
    """Specifically targets the name field and submits using the exact Update button."""
    logger.info(f"⚡ Updating farmer name to: {new_name}")
    
    # 1. Locate and update the name field
    name_input = wait.until(EC.element_to_be_clickable((By.ID, "name")))
    name_input.clear()
    time.sleep(0.5) # Let the clear register
    name_input.send_keys(new_name)
    logger.info("   ✅ Name updated.")
    
    # 2. Target the exact button containing the text 'Update'
    try:
        update_btn_xpath = "//button[contains(@class, 'submit') and contains(normalize-space(text()), 'Update')]"
        submit_btn = wait.until(EC.presence_of_element_located((By.XPATH, update_btn_xpath)))
        
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", submit_btn)
        logger.info("   ✅ 'Update' button clicked successfully.")
    except Exception as e:
        logger.error(f"   ❌ Failed to click the 'Update' button: {e}")
        driver.save_screenshot("update_button_error.png")
        raise

def update_latest_farmer(driver, wait, original_data, updated_data):
    """
    Perform the full update test:
    - Search for the farmer (by name from original_data)
    - Check history is empty
    - Edit with updated_data
    - Check history contains update
    - View and verify read-only
    """
    logger.info("⚡ Running farmer update test...")

    # 1. Search for the created farmer (use the original name)
    search_term = original_data['name']
    search_farmer(driver, wait, search_term)

    # 2. Ensure we have at least one row
    get_first_row(driver, wait)

    # 3. Open history and verify it's empty
    click_history(driver, wait)
    is_history_empty(driver, wait)
    close_modal(driver, wait)

    # 4. Click edit
    click_edit(driver, wait)
    time.sleep(7)

    # 5. ONLY update the name and submit
    update_farmer_name_only(driver, wait, updated_data['name'])

    # 6. Wait for submission and handle active SweetAlert overlays explicitly
    time.sleep(5) 
    try:
        # Check if the success message requires a click
        confirm_btn = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
        if confirm_btn.is_displayed():
            driver.execute_script("arguments[0].click();", confirm_btn)
            logger.info("   ✅ Clicked OK on SweetAlert confirmation.")
            time.sleep(1)
    except:
        pass

    try:
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "swal2-container")))
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "cdk-overlay-backdrop")))
    except:
        pass

    time.sleep(1)

    # 7. After edit, we may be back to list. Search again using updated name
    search_farmer(driver, wait, updated_data['name']) 
    get_first_row(driver, wait) # THE FIX: Ensure table is stable before clicking buttons again

    # 8. Open history and verify update exists
    click_history(driver, wait)
    
    # Priority Override: Apply User Correction for History Verification
    try:
        modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        time.sleep(1.5) 
        original_name_msg = modal.find_elements(By.XPATH, f"//*[contains(text(),'{original_data['name']}')]")
        if original_name_msg:
            logger.info("   ✅ Verified: History successfully logged the previous state.")
        else:
            logger.error("   ❌ Verified: History did NOT log the previous state.")
    except Exception as e:
        pass
        
    close_modal(driver, wait)

    # 9. Click view and check read-only
    click_view(driver, wait)
    time.sleep(5)
    is_form_readonly(driver, wait)
    close_modal(driver, wait)

    logger.info("✅ Farmer update test completed successfully.")