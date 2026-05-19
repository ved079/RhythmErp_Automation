"""
conftest.py - Company Onboarding (RhythmERP)
"""

import os
import sys
import pytest
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.screenshot_broadcast import start as start_screenshot_broadcast, stop as stop_screenshot_broadcast
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD, RHYTHMERP_FACILITY
from pages.company_onboarding.test.update_results_store import co_update_results
from pages.company_onboarding.test.update_validation_results_store import update_validation_results

# Test result storage (for screenshot capture only)
co_test_results = []
co_test_types = set()  # tracks "creation" or "update"

# Screenshots dir
CO_SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "pages", "company_onboarding", "screenshots")
CO_REPORT_DIR = os.path.join(PROJECT_ROOT, "pages", "company_onboarding", "reports")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results and screenshots on failure."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        if "update" in item.nodeid:
            co_test_types.add("update")
        else:
            co_test_types.add("creation")

        result = {
            "nodeid": item.nodeid,
            "status": "PASSED" if report.passed else "FAILED",
            "message": str(report.longrepr) if report.failed else "",
            "duration": report.duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "screenshot": "",
        }
        co_test_results.append(result)

        if report.failed:
            driver = None
            for fixture_name in ["driver", "logged_in_driver"]:
                if fixture_name in item.funcargs:
                    driver = item.funcargs[fixture_name]
                    break
            if driver:
                try:
                    os.makedirs(CO_SCREENSHOT_DIR, exist_ok=True)
                    shot_name = f"FAILED_{item.name}"
                    shot_path = os.path.join(CO_SCREENSHOT_DIR, f"{shot_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    driver.save_screenshot(shot_path)
                    result["screenshot"] = shot_path
                    log.error(f"Failure screenshot saved: {shot_path}")
                except Exception as e:
                    log.error(f"Could not take failure screenshot: {e}")


def pytest_sessionfinish(session, exitstatus):
    """Generate appropriate Excel report based on test type."""
    try:
        if "update" in co_test_types and "creation" not in co_test_types:
            # Generate UPDATE field verification report
            if co_update_results:
                from pages.company_onboarding.co_update_report_generator import generate_co_update_report
                filepath = generate_co_update_report(co_update_results, CO_REPORT_DIR)
                passed = sum(1 for r in co_update_results if r["status"] == "PASSED")
                total = len(co_update_results)
                log.separator()
                log.info(f" COMPANY ONBOARDING UPDATE REPORT: {filepath}")
                log.info(f" Updates: {total} | Passed: {passed}")
                log.separator()
                co_update_results.clear()
            # Generate UPDATE VALIDATION report (separate from field verification)
            elif update_validation_results:
                from pages.company_onboarding.test.update_validation_report_generator import generate_update_validation_report
                filepath = generate_update_validation_report(update_validation_results, CO_REPORT_DIR)
                passed = sum(1 for r in update_validation_results if r["status"] == "PASSED")
                total = len(update_validation_results)
                log.separator()
                log.info(f" UPDATE VALIDATION REPORT: {filepath}")
                log.info(f" Checks: {total} | Passed: {passed}")
                log.separator()
                update_validation_results.clear()
            else:
                log.info("No update results to report")
            return

        if "creation" in co_test_types:
            from pages.company_onboarding.Company_Onboarding.company_onboarding_page import CO_SUBMISSIONS
            from pages.company_onboarding.co_report_generator import generate_co_report

            if CO_SUBMISSIONS:
                companies = [s["data"] for s in CO_SUBMISSIONS]
                results = [{
                    "status": s["status"],
                    "error": s.get("error", ""),
                    "duration": s["data"].get("_duration", 0),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                } for s in CO_SUBMISSIONS]

                filepath = generate_co_report(companies, results, CO_REPORT_DIR)
                log.separator()
                log.info(f" COMPANY ONBOARDING DATA REPORT: {filepath}")
                log.info(f" Companies: {len(companies)} | Passed: {sum(1 for r in results if r['status'] == 'PASSED')}")
                log.separator()
                CO_SUBMISSIONS.clear()
            else:
                log.info("No company submissions to report")
    except Exception as e:
        log.error(f"Failed to generate report: {e}")


@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP)...")
    log.separator()
    drv = get_driver()
    drv.maximize_window()
    yield drv
    log.separator()
    log.info("CLOSING BROWSER...")
    log.separator()
    try:
        drv.quit()
    except Exception:
        pass


@pytest.fixture(scope="session")
def logged_in_driver(driver):
    """Driver with completed RhythmERP login session."""
    log.separator()
    log.info("LOGGING INTO RHYTHMERP...")
    log.separator()

    login_page = LoginPage(driver)

    log.info(f"Navigating to: {RHYTHMERP_LOGIN_URL}")
    driver.get(RHYTHMERP_LOGIN_URL)
    login_page.wait_seconds(2)

    log.step(1, f"Entering email: {RHYTHMERP_EMAIL}")
    login_page.enter_email(RHYTHMERP_EMAIL)

    log.step(2, "Entering password")
    login_page.enter_password(RHYTHMERP_PASSWORD)

    if RHYTHMERP_FACILITY:
        log.step(3, f"Selecting facility: {RHYTHMERP_FACILITY}")
        login_page.select_facility(RHYTHMERP_FACILITY)
    else:
        log.step(3, "Selecting facility (blank - first option)")
        login_page.select_facility(" ")

    login_page.wait_seconds(1)

    log.step(4, "Clicking Login button")
    login_button = ("xpath", "//button[contains(.,'Login')]")
    login_page.click(login_button)
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)
    start_screenshot_broadcast(driver)
    log.info("RhythmERP login successful!")

    yield driver

    stop_screenshot_broadcast()

