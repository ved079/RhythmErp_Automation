"""
common/nav_section.py
---------------------
Reusable navigation helper for PACS application.
Uses PrimeNG Tree Navigator to navigate to any module page.

Usage:
    from common.nav_section import navigate_to
    navigate_to(driver, wait, "Access", "Entity Group Definition")
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'
    ))
    logger.addHandler(console)


# ================================================================
# PRIVATE HELPERS
# ================================================================

def _dismiss_overlays(driver, wait):
    """Kill SweetAlert, CDK overlays, spinners."""
    try:
        wait.until(EC.invisibility_of_element_located(
            (By.CSS_SELECTOR, ".swal2-container, .cdk-overlay-backdrop, .ngx-spinner-overlay")
        ))
    except Exception:
        pass


def _js_click(driver, element):
    """scrollIntoView + JS click."""
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", element)


def _is_module_expanded(driver, module_name):
    """
    Returns True if the module node already has visible children.
    Checks the aria-expanded attribute on the tree node.
    """
    try:
        node = driver.find_element(
            By.XPATH,
            f"//li[@aria-label='{module_name}']"
        )
        return node.get_attribute("aria-expanded") == "true"
    except NoSuchElementException:
        return False


# ================================================================
# TREE NAVIGATION
# ================================================================

def open_tree(driver, wait):
    """Open the PrimeNG tree navigator overlay."""
    _dismiss_overlays(driver, wait)
    time.sleep(1)

    logger.info("Opening tree navigator...")
    pill = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@class,'global-search-pill')]")
    ))

    _js_click(driver, pill)
    time.sleep(1.5)

    # Wait for tree to actually render
    try:
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".p-tree-node-label")
        ))
    except TimeoutException:
        logger.info("  Tree not found after first click, retrying...")
        _js_click(driver, pill)
        time.sleep(1.5)
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".p-tree-node-label")
        ))

    logger.info("  Tree opened.")


def expand_module(driver, wait, module_name):
    """
    Expand a module branch in the tree.
    Skips the toggle click if the module is already expanded,
    preventing accidental collapse on re-navigation.
    """
    logger.info(f"Expanding: {module_name}...")

    if _is_module_expanded(driver, module_name):
        logger.info(f"  '{module_name}' already expanded, skipping toggle.")
        return

    btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH,
         f"//span[text()='{module_name}']"
         f"/ancestor::div[contains(@class,'p-tree-node-content')]//button")
    ))
    _js_click(driver, btn)
    time.sleep(1)

    # Confirm children appeared
    try:
        wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//li[@aria-label='{module_name}']//li")
        ))
    except TimeoutException:
        # If children still not visible, the node may have collapsed — retry once
        logger.warning(f"  Children not found after expanding '{module_name}', retrying...")
        _js_click(driver, btn)
        time.sleep(1)
        wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//li[@aria-label='{module_name}']//li")
        ))

    logger.info(f"  '{module_name}' expanded.")


def click_page(driver, wait, page_name):
    """Click a page label in the tree to navigate."""
    logger.info(f"Clicking: {page_name}...")

    label = wait.until(EC.element_to_be_clickable(
        (By.XPATH,
         f"//li[@aria-label='{page_name}']"
         f"//span[contains(@class,'p-tree-node-label')]")
    ))
    _js_click(driver, label)
    time.sleep(2)
    logger.info(f"  '{page_name}' opened.")


# ================================================================
# MAIN FUNCTION
# ================================================================

def navigate_to(driver, wait, module_name, page_name):
    """
    Full navigation: open tree → expand module (if needed) → click page.

    Example:
        navigate_to(driver, wait, "Access", "Entity Group Definition")
        navigate_to(driver, wait, "Common Settings", "Country Master")
    """
    logger.info(f">> {module_name} > {page_name}")
    open_tree(driver, wait)
    expand_module(driver, wait, module_name)
    click_page(driver, wait, page_name)
    logger.info(f">> Done: {module_name} > {page_name}")