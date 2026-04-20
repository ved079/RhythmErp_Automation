from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


def _get_fresh_overlay(driver):
    """Always fetches a fresh overlay element to avoid stale references after Angular re-renders."""
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".cdk-overlay-pane")
        if el.is_displayed():
            return el
    except Exception:
        pass
    return None


def _wait_for_overlay_open(wait, driver):
    """Waits until the overlay pane is present and visible, returns fresh element."""
    return wait.until(lambda d: _get_fresh_overlay(driver))


def _wait_for_overlay_close(wait, driver, timeout=10):
    """Waits until the overlay pane disappears or is hidden."""
    end = time.time() + timeout
    while time.time() < end:
        try:
            el = driver.find_element(By.CSS_SELECTOR, ".cdk-overlay-pane")
            if not el.is_displayed():
                return True
        except Exception:
            return True  # Element gone from DOM
        time.sleep(0.2)
    raise TimeoutError("Overlay did not close in time")


def select_dropdown(driver, wait, value=None, control_name=None, label_text=None,
                    control_id=None, searchable=False, post_open_wait=0.5):
    """
    Selects a mat-select dropdown option by value.

    Args:
        driver:         Selenium WebDriver instance.
        wait:           WebDriverWait instance.
        value:          The visible text of the option to select.
        control_name:   formcontrolname attribute of the mat-select.
        label_text:     mat-label text to locate the mat-select via XPath.
        control_id:     HTML id of the mat-select.
        searchable:     If True, types value into the search input before selecting.
        post_open_wait: Seconds to wait after opening the dropdown before interacting
                        (useful for dropdowns that load options dynamically).
    """
    # --- Locate the dropdown trigger ---
    if control_name:
        selector = f"mat-select[formcontrolname='{control_name}']"
        dropdown = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
    elif label_text:
        selector = f"//mat-label[contains(text(), '{label_text}')]/ancestor::mat-form-field//mat-select"
        dropdown = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
    elif control_id:
        dropdown = wait.until(EC.presence_of_element_located((By.ID, control_id)))
    else:
        raise ValueError("One of control_name, label_text, or control_id must be provided.")

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", dropdown)

    # Wait for the overlay to open
    _wait_for_overlay_open(wait, driver)
    time.sleep(post_open_wait)  # Let Angular populate options (critical for dynamic lists)

    # --- Optional: type into search box to filter results ---
    if searchable:
        search_xpath = (
            ".//input["
            "@type='text' and ("
            "contains(@placeholder,'Search') or "
            "contains(@placeholder,'search') or "
            "contains(@placeholder,'Filter') or "
            "contains(@class,'mat-select-search') or "
            "contains(@class,'search')"
            ")]"
        )
        overlay = _get_fresh_overlay(driver)
        if overlay:
            try:
                search_input = overlay.find_element(By.XPATH, search_xpath)
                search_input.clear()
                search_input.send_keys(value)
                time.sleep(0.8)  # Wait for Angular to filter the list
                logger.info(f"   🔍 Searched for '{value}' in dropdown")
            except Exception:
                # No search box found — log and proceed without filtering
                logger.warning(
                    f"   ⚠️  No search input found in overlay for '{control_name or label_text}'. "
                    f"Proceeding without filtering."
                )

    # --- Log what options are visible (helps debug mismatches) ---
    try:
        overlay = _get_fresh_overlay(driver)
        options_found = overlay.find_elements(By.XPATH, ".//mat-option") if overlay else []
        logger.info(f"   📋 {len(options_found)} option(s) visible in overlay")
        if not options_found:
            logger.warning("   ⚠️  Overlay is empty — the dropdown may still be loading. "
                           "Consider increasing post_open_wait.")
        for opt in options_found[:5]:
            logger.debug(f"      Option: '{opt.text.strip()}'")
    except Exception:
        pass

    # --- Click the matching option using a fresh overlay reference ---
    def find_option(d):
        fresh = _get_fresh_overlay(driver)
        if not fresh:
            return None
        
        # 1. Try EXACT match first
        try:
            exact_options = fresh.find_elements(By.XPATH, f".//mat-option[normalize-space(.)='{value}']")
            if exact_options:
                return exact_options[0]
        except Exception:
            pass
            
        # 2. Fallback to PARTIAL match
        try:
            partial_options = fresh.find_elements(By.XPATH, f".//mat-option[contains(normalize-space(.), '{value}')]")
            if partial_options:
                return partial_options[0]
        except Exception:
            pass
            
        return None

    option = wait.until(find_option)
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
    driver.execute_script("arguments[0].click();", option)
    logger.info(f"   ✅ Selected '{value}' from '{control_name or label_text or control_id}'")

    # Wait for the overlay to fully close before proceeding
    _wait_for_overlay_close(wait, driver)


def fill_input(driver, wait, value, control_name=None, control_id=None):
    """
    Fills a plain <input> or Angular Material Datepicker field.

    Uses keyboard-based clear + type + TAB to ensure Angular's change
    detection and validators fire correctly.
    """
    try:
        if control_name:
            element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"input[formcontrolname='{control_name}']"))
            )
        elif control_id:
            element = wait.until(EC.presence_of_element_located((By.ID, control_id)))
        else:
            raise ValueError("Either control_name or control_id must be provided.")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.2)

        # JS click avoids floating mat-label intercepting the click
        driver.execute_script("arguments[0].click();", element)
        time.sleep(0.2)

        # CTRL+A → BACKSPACE clears correctly for Angular-managed inputs
        # (element.clear() does NOT reliably trigger Angular's value accessor)
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.BACKSPACE)
        time.sleep(0.2)

        element.send_keys(str(value))
        time.sleep(0.2)

        # TAB forces Angular to register the new value and run validators
        element.send_keys(Keys.TAB)
        time.sleep(0.2)

        logger.info(f"   ✅ Filled '{control_name or control_id}': {value}")

    except Exception as e:
        logger.error(f"   ❌ Failed to fill '{control_name or control_id}': {e}")
        driver.save_screenshot(f"fill_error_{control_name or control_id}.png")
        raise


def click_submit(driver, wait):
    """
    Clicks the form submit button.

    Uses JS click to avoid ElementClickInterceptedException from
    overlapping elements (e.g. sticky headers, tooltips).
    """
    try:
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.submit")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        driver.execute_script("arguments[0].click();", submit_btn)
        logger.info("   ✅ Submit button clicked")
    except Exception as e:
        logger.error(f"   ❌ Failed to click submit: {e}")
        driver.save_screenshot("submit_button_error.png")
        raise