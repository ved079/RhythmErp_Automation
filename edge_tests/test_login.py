import pytest
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import config

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console)


class TestLogin:

    def safe_type(self, wait, css_selectors, text):
        """Helper to reliably clear and type into fields sequentially, char by char."""
        element = None
        for selector in css_selectors:
            try:
                driver = wait._driver 
                short_wait = WebDriverWait(driver, 2)
                element = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                break  
            except TimeoutException:
                continue

        if not element:
            pytest.fail(f"Could not find or click any element with selectors: {css_selectors}")

        # Clear the field reliably (Avoids the .clear() Angular trap)
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.BACKSPACE)
        time.sleep(0.5) 

        # Type character by character for visual verification
        if text:
            for char in text:
                element.send_keys(char)
                time.sleep(0.1) 
            
        time.sleep(0.5) 
        return element

    # =========================================================================
    # THE PASSWORD VISIBILITY TOGGLE (YOUR INSANITY SAVER)
    # =========================================================================
    def click_password_visibility(self, wait):
        """Clicks the exact mat-icon to unmask the password."""
        try:
            # Targets the exact icon using the HTML you provided, handling the weird spacing
            visibility_icon = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//mat-icon[contains(text(), 'visibility_off')]")
            ))
            visibility_icon.click()
            
            # 🛑 FORCING A 1.5 SECOND PAUSE SO YOU CAN SEE THE UNMASKED PASSWORD 🛑
            time.sleep(1.5)  
        except TimeoutException:
            logger.warning("WARNING: Password eye icon not found. Is the field empty?")
    # =========================================================================

    def fill_login_initial(self, wait, username, password):
        """Fill username and password sequentially, toggle visibility, then click login."""
        username_selectors = ["[formcontrolname='username']", "#mat-input-0"]
        password_selectors = ["[formcontrolname='password']", "#mat-input-1"]
        
        self.safe_type(wait, username_selectors, username)
        self.safe_type(wait, password_selectors, password)
        
        # =====================================================================
        # FIRING THE VISIBILITY TOGGLE IF A PASSWORD WAS TYPED
        # =====================================================================
        if password:
            self.click_password_visibility(wait)
        # =====================================================================
        
        # Click login button
        try:
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], .mat-mdc-button, button.login-btn")))
            btn.click()
        except TimeoutException:
            driver = wait._driver
            btn = driver.find_element(By.XPATH, "//button[contains(translate(., 'LOGIN', 'login'), 'login')]")
            btn.click()

    def select_tenant(self, wait, tenant_name):
        """After successful login, select tenant from Angular dropdown."""
        tenant_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select[formcontrolname='tenant_name']")))
        tenant_dropdown.click()
        time.sleep(1) 
        
        option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//mat-option//span[contains(text(), '{tenant_name}')]")))
        option.click()
        time.sleep(1) 
        
        try:
            driver = wait._driver
            final_login = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
            final_login.click()
        except TimeoutException:
            pass 

    @pytest.mark.parametrize("username, password, reason", [
        ("invalid_user@example.com", config.PASS, "Invalid Username"),
        (config.USER, "wrong_password", "Invalid Password"),
        ("", config.PASS, "Empty Username"),
        (config.USER, "", "Empty Password"),
        (f"   {config.USER}   ", config.PASS, "Username With Whitespace")
    ])
    def test_invalid_login(self, driver, wait, username, password, reason):
        """Test invalid login attempts."""
        driver.get(config.URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # This calls fill_login_initial, which triggers the typing AND the eye icon
        self.fill_login_initial(wait, username, password)
        
        try:
            error = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "mat-error, .toast, .error, .alert, [role='alert']")))
            assert len(error.text) > 0
            time.sleep(1.5) 
        except TimeoutException:
            driver.save_screenshot(f"invalid_login_fail_{reason.replace(' ', '_')}.png")
            pytest.fail(f"Failed on {reason}: No error message UI appeared. Screenshot saved.")

    def test_valid_login(self, driver, wait):
        """Test successful login with tenant selection."""
        driver.get(config.URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # This calls fill_login_initial, which triggers the typing AND the eye icon
        self.fill_login_initial(wait, config.USER, config.PASS)
        
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-select[formcontrolname='tenant_name']")))
        except TimeoutException:
            driver.save_screenshot("tenant_not_appeared.png")
            pytest.fail("Tenant dropdown did not appear after login.")
        
        self.select_tenant(wait, config.TENANT_NAME)
        
        try:
            success_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".profile-icon, .logout-btn, #user-menu, nav")))
            assert success_element.is_displayed()
        except TimeoutException:
            driver.save_screenshot("dashboard_not_found.png")
            pytest.fail("Dashboard not found after tenant selection.")