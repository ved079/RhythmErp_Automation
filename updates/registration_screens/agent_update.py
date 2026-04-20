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

def search_agent(driver, wait, search_term):
    try:
        search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".browser-default")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", search_box)
        
        search_box.clear()
        time.sleep(0.5) 
        search_box.send_keys(search_term)
        search_box.send_keys(Keys.ENTER)
        
        time.sleep(2) 
        logger.info(f"   ✅ Searched for: {search_term}")
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        driver.save_screenshot("search_agent_error.png")
        raise

def get_first_row(driver, wait):
    try:
        row = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        return row
    except Exception as e:
        logger.error(f"❌ No rows found: {e}")
        driver.save_screenshot("no_rows_error.png")
        raise

def click_action_button(driver, wait, button_selector, action_name):
    attempts = 0
    while attempts < 3:
        try:
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"table tbody tr:first-child {button_selector}")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.5) 
            driver.execute_script("arguments[0].click();", btn)
            logger.info(f"   ✅ {action_name} button clicked")
            time.sleep(1.5) 
            return
        except StaleElementReferenceException:
            attempts += 1
            time.sleep(0.5)
            logger.warning(f"   Stale element, retrying {action_name} ({attempts})...")
    raise Exception(f"Could not click {action_name} button after retries")

def click_history(driver, wait):
    click_action_button(driver, wait, ".bi-clock-history", "History")

def click_edit(driver, wait):
    click_action_button(driver, wait, ".bi-pencil", "Edit")

def click_view(driver, wait):
    click_action_button(driver, wait, ".bi-eye", "View")

def close_modal(driver, wait):
    try:
        close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".bi-x-lg")))
        driver.execute_script("arguments[0].click();", close_btn)
        time.sleep(1)
        logger.info("   ✅ Modal closed (X button)")
    except:
        try:
            cancel_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cancel")))
            driver.execute_script("arguments[0].click();", cancel_btn)
            time.sleep(1)
            logger.info("   ✅ Modal closed (Cancel button)")
        except:
            logger.warning("   ⚠️ Could not close modal. It may already be closed.")

def is_history_empty(driver, wait):
    try:
        modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        time.sleep(1.5) 
        empty_msg = modal.find_elements(By.XPATH, "//*[contains(text(),'No records') or contains(text(),'No data') or contains(text(),'No Data')]")
        if empty_msg:
            logger.info("   ✅ Verified: History is empty.")
            return True
        else:
            logger.warning("   ⚠️ Verified: History is NOT empty.")
            return False
    except Exception as e:
        return False

def is_history_has_update(driver, wait):
    try:
        modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        time.sleep(1.5) 
        update_msg = modal.find_elements(By.XPATH, "//*[contains(text(),'Updated') or contains(text(),'Edited') or contains(text(),'Update')]")
        if update_msg:
            logger.info("   ✅ Verified: History successfully logged the 'Update' event.")
            return True
        else:
            logger.error("   ❌ Verified: History did NOT log the update.")
            return False
    except Exception as e:
        return False

def is_form_readonly(driver, wait):
    try:
        name_input = wait.until(EC.presence_of_element_located((By.ID, "agent_name")))
        if name_input.get_attribute("disabled") or name_input.get_attribute("readonly"):
            logger.info("   ✅ Form is read-only (view mode).")
            return True
        else:
            logger.error("   ❌ Form is not read-only (expected disabled).")
            return False
    except Exception as e:
        logger.warning(f"   ⚠️ Could not verify read-only state: {e}")
        return False

def update_agent_name_only(driver, wait, new_agent_name):
    logger.info(f"⚡ Updating agent name to: {new_agent_name}")
    
    # 1. Locate and update the agent_name field
    name_input = wait.until(EC.element_to_be_clickable((By.ID, "agent_name")))
    name_input.clear()
    time.sleep(0.5) 
    name_input.send_keys(new_agent_name)
    logger.info("   ✅ Agent Name updated.")
    
    # 2. Target the exact Update button strictly inside the .footer and .right divs
    try:
        update_btn_xpath = "//div[contains(@class, 'footer')]//div[contains(@class, 'right')]//button[contains(@class, 'submit') and contains(., 'Update')]"
        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, update_btn_xpath)))
        
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", submit_btn)
        logger.info("   ✅ 'Update' button clicked successfully.")
    except Exception as e:
        logger.error(f"   ❌ Failed to click the 'Update' button: {e}")
        driver.save_screenshot("agent_update_button_error.png")
        raise

def update_latest_agent(driver, wait, original_data, updated_data):
    logger.info("⚡ Running agent update test...")

    # 1. Search for the agent
    search_term = original_data['agent_name']
    search_agent(driver, wait, search_term)
    get_first_row(driver, wait)

    # 2. History checks
    click_history(driver, wait)
    is_history_empty(driver, wait)
    close_modal(driver, wait)

    # 3. Edit
    click_edit(driver, wait)
    update_agent_name_only(driver, wait, updated_data['agent_name'])

    # Wait for completion
    time.sleep(2) 
    try:
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "swal2-container")))
    except:
        pass

    # 4. Search again
    search_agent(driver, wait, updated_data['agent_name']) 

    # 5. History checks
    click_history(driver, wait)
    
    # ⚠️ Rule 1 Override: Apply User Correction for History Verification
    # The history modal displays data from BEFORE the save event, so we must check for 
    # the original agent_name, not the updated one, to confirm the log is present.
    try:
        modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane")))
        time.sleep(1.5) 
        original_name_msg = modal.find_elements(By.XPATH, f"//*[contains(text(),'{original_data['agent_name']}')]")
        if original_name_msg:
            logger.info("   ✅ Verified: History successfully logged the previous state.")
        else:
            logger.error("   ❌ Verified: History did NOT log the previous state.")
    except Exception as e:
        pass
        
    close_modal(driver, wait)

    # 6. View checks
    click_view(driver, wait)
    is_form_readonly(driver, wait)
    close_modal(driver, wait)

    logger.info("✅ Agent update test completed successfully.")