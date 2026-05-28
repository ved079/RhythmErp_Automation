"""
conftest.py
-----------
pytest configuration for Login Screens test cases.
Handles fixtures and report generation specific to login/forgot-password tests.
"""

import pytest
from datetime import datetime

from common.logger import log
from common.report_generator import generate_report
from config import REPORT_DIR


# ================================================================
# TEST RESULT STORAGE (for Excel report)
# ================================================================
login_test_results = []


# ================================================================
# LOGIN TEST DESCRIPTIONS
# ================================================================
LOGIN_DESCRIPTIONS = {
    "test_lp_01": {
        "name": "All UI Elements Visible",
        "question": "Does the login page load correctly with all fields — email, password, facility dropdown, and login button?",
    },
    "test_lp_02": {
        "name": "Facility Dropdown Opens",
        "question": "Does the facility dropdown open and show available options when clicked?",
    },
    "test_lp_03": {
        "name": "Password Field Masks Input",
        "question": "Is the password field masked (dots) so the password isn't visible while typing?",
    },
    "test_lp_04": {
        "name": "Forgot Password Link Works",
        "question": "Does clicking 'Forgot Password' navigate to the correct forgot password page?",
    },
    "test_lp_05": {
        "name": "Empty Form Submission Blocked",
        "question": "Does the app show validation errors when you click Login without filling any fields?",
    },
    "test_ln_01": {
        "name": "Wrong Password Rejected",
        "question": "Does the app block login with a correct email but wrong password and show an error?",
    },
    "test_ln_02": {
        "name": "Wrong Email Rejected",
        "question": "Does the app block login with a non-existent email and show an error?",
    },
    "test_ln_03": {
        "name": "Both Credentials Wrong Rejected",
        "question": "Does the app block login when both email and password are completely wrong?",
    },
    "test_ln_04": {
        "name": "Blank Email Validation",
        "question": "Does the app show a field-level error when trying to login without entering an email?",
    },
    "test_ln_05": {
        "name": "Blank Password Validation",
        "question": "Does the app show a field-level error when trying to login without entering a password?",
    },
    "test_ln_06": {
        "name": "Invalid Email Format Caught",
        "question": "Does the app catch invalid email formats like 'invalidemail' (no @, no domain)?",
    },
    "test_ln_07": {
        "name": "Email with Spaces Handled",
        "question": "Does the app handle emails with leading/trailing spaces (e.g. '  test@gmail.com  ') correctly — trim or validate?",
    },
    "test_ln_08": {
        "name": "Space in Email Middle Caught",
        "question": "Does the app catch malformed emails with spaces in the middle like 'test @gmail.com'?",
    },
    "test_ln_09": {
        "name": "No Facility Selected Blocked",
        "question": "Does the app prevent login when no facility/tenant is selected from the dropdown?",
    },
    "test_ln_10": {
        "name": "Double-Click Login Safe",
        "question": "Does rapid double-clicking the Login button cause any issues like duplicate requests or crashes?",
    },
    "test_l_01": {
        "name": "Valid Credentials → Dashboard",
        "question": "THE BIG ONE: Does the full login flow work — enter valid credentials, select facility, and reach the dashboard?",
    },
}

LOGIN_CATEGORIES = {
    "TestLoginPageLoad": "Page Load / UI",
    "TestLoginNegative": "Negative / Validation",
    "TestLoginPositive": "Positive",
}


# ================================================================
# FORGOT PASSWORD TEST DESCRIPTIONS
# ================================================================
FP_DESCRIPTIONS = {
    "test_fp_s1_01": {
        "name": "Unregistered Email Proceeds",
        "question": "Does the app proceed to OTP screen even for an email that doesn't exist in the system?",
    },
    "test_fp_s1_02": {
        "name": "Valid Email Sends OTP",
        "question": "Does a valid registered email trigger OTP delivery and navigate to the OTP screen?",
    },
    "test_fp_s1_03": {
        "name": "Blank Email Submission",
        "question": "Does clicking Send OTP without entering an email show a validation error or alert?",
    },
    "test_fp_s1_04": {
        "name": "Email with Spaces Trimmed",
        "question": "Does the app handle emails with leading/trailing spaces — trim them and proceed?",
    },
    "test_fp_s1_05": {
        "name": "Email Case Insensitive",
        "question": "Does the app treat uppercase and lowercase emails the same way?",
    },
    "test_fp_s1_06": {
        "name": "Double-Click Send OTP Safe",
        "question": "Does rapid double-clicking Send OTP cause issues like duplicate OTPs or crashes?",
    },
    "test_fp_s2_01": {
        "name": "Invalid OTP Shows Alert",
        "question": "Does entering a wrong OTP code show an error alert?",
    },
    "test_fp_s2_02": {
        "name": "Password Mismatch Shows Alert",
        "question": "Does entering different passwords in New Password and Confirm Password show an error?",
    },
    "test_fp_s2_03": {
        "name": "Password Policy Hints Visible",
        "question": "Do password policy hints (min 12 chars, uppercase, etc.) appear when typing a weak password?",
    },
    "test_fp_s2_04": {
        "name": "Recently Used Password Alert",
        "question": "Does the app show an error when trying to reset to a recently used password?",
    },
    "test_fp_ff_01": {
        "name": "Browser Back from OTP Screen",
        "question": "Does pressing browser back on the OTP screen return to email entry or login?",
    },
    "test_fp_ff_02": {
        "name": "Back to Login from Screen 1",
        "question": "Does clicking 'Back to Login' on Screen 1 return to the login page?",
    },
    "test_fp_ff_03": {
        "name": "Grand Finale: Reset → Login → Dashboard",
        "question": "THE BIG ONE: Full forgot password flow — reset password, login with new password, reach dashboard?",
    },
    "test_fp_ff_04": {
        "name": "Recently Used Password Rejected",
        "question": "Does the app reject a password that was just used in the previous reset?",
    },
    "test_fp_ff_05": {
        "name": "Current Password Rejected",
        "question": "Does the app reject setting the same password as the current one?",
    },
    "test_fp_ff_06": {
        "name": "Cleanup: Reset to Default Password",
        "question": "Does the cleanup reset the password back to the default so next test run starts clean?",
    },
}

FP_CATEGORIES = {
    "TestForgotPasswordScreen1": "Screen 1 / Email Entry",
    "TestForgotPasswordScreen2": "Screen 2 / OTP & Password",
    "TestForgotPasswordFullFlow": "Full Flow",
}


# ================================================================
# FIXTURES
# ================================================================
@pytest.fixture
def on_login_page(driver):
    """Navigate to RhythmERP login page fresh."""
    from config import RHYTHMERP_LOGIN_URL
    from pages.login_screens.Login_Screens_.login_page import LoginPage

    driver.delete_all_cookies()
    driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
    
    # Force full reload — SPA hash routing won't reload if we navigate to same URL
    driver.get("about:blank")
    driver.get(RHYTHMERP_LOGIN_URL)
    
    page = LoginPage(driver)
    page.wait_for_page_load()
    return page


# ================================================================
# HELPERS
# ================================================================
def _detect_suite(results):
    """Detect which test suite is running based on test names."""
    has_login = any("test_lp_" in r["nodeid"] or "test_ln_" in r["nodeid"] or "test_l_01" in r["nodeid"] for r in results)
    has_fp = any("test_fp_" in r["nodeid"] for r in results)
    if has_fp and not has_login:
        return "forgot_password"
    return "login"


# ================================================================
# PYTEST HOOKS
# ================================================================
def pytest_configure(config):
    """Runs before test session starts."""
    log.separator("=")
    log.info(" RHYTHMERP LOGIN SCREEN TEST SUITE")
    log.info(f" Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.separator("=")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results for Excel report + failure screenshots."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        result = {
            "nodeid": item.nodeid,
            "status": "PASSED" if report.passed else "FAILED",
            "message": str(report.longrepr) if report.failed else "",
            "duration": report.duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "screenshot": "",
        }

        if report.failed:
            driver = None
            if "driver" in item.funcargs:
                driver = item.funcargs["driver"]
            if driver:
                try:
                    from pages.login_screens.Login_Screens_.login_page import LoginPage
                    from common.screenshot_broadcast import (
                        start as start_screenshot_broadcast,
                        stop as stop_screenshot_broadcast,
                    )
                    import os
                    os.makedirs(REPORT_DIR, exist_ok=True)
                    shot_name = f"FAILED_{item.name}"
                    lp = LoginPage(driver)
                    result["screenshot"] = lp.take_screenshot(shot_name)
                except Exception as e:
                    log.error(f"Could not take screenshot: {e}")

        login_test_results.append(result)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report after all tests complete."""
    if not login_test_results:
        return

    suite = _detect_suite(login_test_results)

    if suite == "forgot_password":
        title = "RhythmERP Forgot Password Tests"
        prefix = "RhythmERPForgotPassword"
        descriptions = FP_DESCRIPTIONS
        categories = FP_CATEGORIES
    else:
        title = "RhythmERP Login Screen Tests"
        prefix = "RhythmERPLogin"
        descriptions = LOGIN_DESCRIPTIONS
        categories = LOGIN_CATEGORIES

    try:
        filepath = generate_report(
            login_test_results,
            output_dir=REPORT_DIR,
            title=title,
            filename_prefix=prefix,
            descriptions=descriptions,
            categories=categories,
        )
        log.separator()
        log.info(f" EXCEL REPORT GENERATED: {filepath}")
        log.separator()
    except Exception as e:
        log.error(f"Failed to generate Excel report: {e}")