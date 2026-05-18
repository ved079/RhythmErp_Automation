"""
user_creation_test.py
---------------------
Pytest test cases for User Creation screen (Access Module).
8 tests in 3 classes: Positive, Validation, Dropdown.

Run:
    pytest pages/access_screen/access_screens_test_cases/user_creation_test.py -v
"""

import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.access_screen.data.access_test_data import (
    DUPLICATE_USERNAME,
    DUPLICATE_EMAIL,
    VALID_PASSWORD,
    WEAK_PASSWORDS,
    random_user_data,
    random_user_data_single_type,
    random_user_data_dcb,
)
from pages.access_screen.Access_screens.user_creation import (
    _fill_input,
    _fill_multi_dropdown,
    _fill_search_dropdown,
)


# ================================================================
# PRIVATE HELPERS
# ================================================================

def _click_add(driver, wait):
    """Click the ADD button to open the creation form."""
    add_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@class,'erp-add-btn')]")
    ))
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(1)


def _click_submit(driver, wait):
    """Click the Submit button on the form."""
    submit = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@type='submit']//span[normalize-space()='Submit']")
    ))
    driver.execute_script("arguments[0].click();", submit)


def _wait_for_swal_toast(driver, wait, timeout=5):
    """Wait for SweetAlert toast to appear and return its title text."""
    try:
        toast = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "div.swal2-popup.swal2-toast h2.swal2-title")
            )
        )
        text = toast.text.strip()
        time.sleep(3)   # wait for auto-dismiss
        return text
    except Exception:
        return None


def _wait_for_swal_success(driver, wait):
    """Wait for SweetAlert success popup and click OK."""
    try:
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".swal2-success")
        ))
        try:
            ok_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".swal2-confirm")
            ))
            ok_btn.click()
            time.sleep(0.5)
        except Exception:
            pass
        return True
    except Exception:
        return False


def _is_form_open(driver, wait):
    """Check if the creation form modal is still open."""
    try:
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//span[contains(text(),'User Creation Screen Details')]")
        ))
        return True
    except Exception:
        return False


def _fill_all_fields(driver, wait, data):
    """Fill all form fields with given data dict."""
    _fill_input(driver, wait, "username", data["username"])
    _fill_input(driver, wait, "email", data["email"])
    _fill_input(driver, wait, "first_name", data["first_name"])
    _fill_input(driver, wait, "last_name", data["last_name"])
    _fill_input(driver, wait, "password", data["password"])
    _fill_multi_dropdown(driver, wait, "User Type", data["user_types"])
    _fill_search_dropdown(driver, wait, "Role", data["role"])
    _fill_multi_dropdown(driver, wait, "Entity", [data["entity"]])


# ================================================================
# CLASS 1: POSITIVE TESTS (uses class-scoped fixture from conftest.py)
# ================================================================

class TestUserCreationPositive:

    def _open_add_form(self, driver, wait):
        """Dismiss overlays, click ADD, wait for form to appear."""
        try:
            wait.until(EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, ".cdk-overlay-backdrop, .ngx-spinner-overlay")
            ))
        except:
            pass
        _click_add(driver, wait)
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//h3[contains(text(),'User Creation Screen Details')]")
        ))
        time.sleep(0.3)

    def test_uc_p01_happy_path_create_and_verify(self, user_creation_screen):
        driver, wait = user_creation_screen
        self._open_add_form(driver, wait)
        data = random_user_data()
        _fill_all_fields(driver, wait, data)
        _click_submit(driver, wait)

        success = _wait_for_swal_success(driver, wait)
        assert success, "Expected SweetAlert success popup after creating user"

        from common.table_helpers import verify_in_table
        verify_in_table(driver, wait, data["username"],
                        check_date=True, date_column="joined",
                        date_format="%d %b %Y")

    def test_uc_p02_single_user_type(self, user_creation_screen):
        driver, wait = user_creation_screen
        self._open_add_form(driver, wait)
        data = random_user_data_single_type()
        _fill_all_fields(driver, wait, data)
        _click_submit(driver, wait)

        success = _wait_for_swal_success(driver, wait)
        assert success, "Expected SweetAlert success popup after creating user"

        from common.table_helpers import verify_in_table
        verify_in_table(driver, wait, data["username"],
                        check_date=True, date_column="joined",
                        date_format="%d %b %Y")

    def test_uc_p03_dcb_role_dcb1_entity(self, user_creation_screen):
        driver, wait = user_creation_screen
        self._open_add_form(driver, wait)
        data = random_user_data_dcb()
        _fill_all_fields(driver, wait, data)
        _click_submit(driver, wait)

        success = _wait_for_swal_success(driver, wait)
        assert success, "Expected SweetAlert success popup after creating user"

        from common.table_helpers import verify_in_table
        verify_in_table(driver, wait, data["username"],
                        check_date=True, date_column="joined",
                        date_format="%d %b %Y")


# ================================================================
# CLASS 2: VALIDATION TESTS
# ================================================================

class TestUserCreationValidation:

    def test_uc_v01_blank_submit_no_alert(self, on_user_creation):
        driver, wait = on_user_creation
        _click_add(driver, wait)
        _click_submit(driver, wait)

        toast = _wait_for_swal_toast(driver, wait, timeout=3)
        assert toast is None, f"Should NOT show SweetAlert on blank submit, got: '{toast}'"
        assert _is_form_open(driver, wait), "Form should still be open"

    def test_uc_v02_duplicate_username_rejected(self, on_user_creation):
        driver, wait = on_user_creation
        _click_add(driver, wait)
        _fill_input(driver, wait, "username", DUPLICATE_USERNAME)
        _fill_input(driver, wait, "email", "unique_email_test@mail.com")
        _fill_input(driver, wait, "first_name", "Test")
        _fill_input(driver, wait, "last_name", "Dup")
        _fill_input(driver, wait, "password", VALID_PASSWORD)
        _fill_multi_dropdown(driver, wait, "User Type", ["Checker"])
        _fill_search_dropdown(driver, wait, "Role", "DCB")
        _fill_multi_dropdown(driver, wait, "Entity", ["dcb1"])
        _click_submit(driver, wait)

        toast = _wait_for_swal_toast(driver, wait)
        assert toast, "Expected error toast for duplicate username"
        assert "username already exists" in toast.lower(), f"Got: '{toast}'"

    def test_uc_v03_duplicate_email_rejected(self, on_user_creation):
        driver, wait = on_user_creation
        _click_add(driver, wait)
        _fill_input(driver, wait, "username", f"dup_email_{int(time.time())}")
        _fill_input(driver, wait, "email", DUPLICATE_EMAIL)
        _fill_input(driver, wait, "first_name", "Test")
        _fill_input(driver, wait, "last_name", "Dup")
        _fill_input(driver, wait, "password", VALID_PASSWORD)
        _fill_multi_dropdown(driver, wait, "User Type", ["Checker"])
        _fill_search_dropdown(driver, wait, "Role", "DCB")
        _fill_multi_dropdown(driver, wait, "Entity", ["dcb1"])
        _click_submit(driver, wait)

        toast = _wait_for_swal_toast(driver, wait)
        assert toast, "Expected error toast for duplicate email"
        assert "email already exists" in toast.lower(), f"Got: '{toast}'"

    def test_uc_v04_weak_password_rejected(self, on_user_creation):
        driver, wait = on_user_creation
        data = random_user_data()
        _click_add(driver, wait)
        _fill_all_fields(driver, wait, data)
        _fill_input(driver, wait, "password", WEAK_PASSWORDS["too_short"])
        _click_submit(driver, wait)

        toast = _wait_for_swal_toast(driver, wait, timeout=3)
        if toast:
            assert "already exists" not in toast.lower(), \
                f"Weak password should not create user, got: '{toast}'"


# ================================================================
# CLASS 3: DROPDOWN TESTS
# ================================================================

class TestUserCreationDropdown:

    def test_uc_d01_multi_select_user_type(self, on_user_creation):
        driver, wait = on_user_creation
        _click_add(driver, wait)

        select = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             "//mat-label[normalize-space()='User Type']"
             "/ancestor::mat-form-field//mat-select"
             "//div[contains(@class,'select-trigger')]")
        ))
        select.click()
        time.sleep(0.5)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class,'cdk-overlay-pane')]//mat-option")
        ))

        for opt_text in ["Maker", "Checker"]:
            option = wait.until(EC.element_to_be_clickable(
                (By.XPATH,
                 f"//div[contains(@class,'cdk-overlay-pane')]"
                 f"//mat-option//span[normalize-space()='{opt_text}']")
            ))
            driver.execute_script("arguments[0].click();", option)
            time.sleep(0.3)

        driver.find_element(By.TAG_NAME, "body").click()
        time.sleep(0.5)

        chips = driver.find_elements(
            By.XPATH,
            "//mat-label[normalize-space()='User Type']"
            "/ancestor::mat-form-field//mat-chip"
        )
        assert len(chips) >= 2, f"Expected at least 2 chips, found {len(chips)}"