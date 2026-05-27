"""
conftest.py - Company Onboarding (RhythmERP)

6 Steps:
  Step 1 = Company Details  (including Company Code)
  Step 2 = Promoters
  Step 3 = Address
  Step 4 = Business Details
  Step 5 = Infrastructure
  Step 6 = Configuration (Base Currency)
"""

import os
import sys
import logging
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD

# Optional: cs_report_generator for Excel reports (not required for tests to run)
try:
    from pages.common_settings.cs_report_generator import (
        CSReportStore,
        generate_cs_report,
    )
    _HAS_REPORT_GENERATOR = True
except ImportError:
    _HAS_REPORT_GENERATOR = False
    CSReportStore = None
    generate_cs_report = None


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Company Onboarding Tests)...")
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

    log.info("Navigating to: " + str(RHYTHMERP_LOGIN_URL))
    driver.get(RHYTHMERP_LOGIN_URL)
    login_page.wait_seconds(2)

    log.step(1, "Entering email: " + str(RHYTHMERP_EMAIL))
    login_page.enter_email(RHYTHMERP_EMAIL)

    log.step(2, "Entering password")
    login_page.enter_password(RHYTHMERP_PASSWORD)

#     log.step(3, "Selecting facility (blank - first option)")
#     login_page.select_facility_by_index(index=0)

    login_page.wait_seconds(1)

    log.step(4, "Clicking Login button")
    login_page.click_login()
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")

    yield driver


@pytest.fixture
def co_page(logged_in_driver):
    """Company Onboarding page object -- fresh navigation for each test."""
    from pages.company_onboarding.Company_Onboarding.company_onboarding_page import (
        CompanyOnboardingPage,
    )
    page = CompanyOnboardingPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS (only if cs_report_generator is available)
# ================================================================

if _HAS_REPORT_GENERATOR:
    _co_store = CSReportStore()

    # ---- Company Onboarding Known Issues ----

    # BUG-001 (HIGH): Duplicate Company Name silently rejected
    _co_store.record_issue(
        severity="High",
        module="Company Onboarding",
        category="Data Integrity",
        description="Duplicate Company Names may be accepted silently without "
                    "showing any validation error. The form may close without "
                    "any error or success message.",
        expected="System should show a validation error like 'Company Name already exists' "
                 "and keep the form open for correction.",
        actual="To be confirmed during test execution.",
        test_ref="CO-D01",
        status="Suspected",
    )

    # BUG-002 (HIGH): Company Code maxlength not enforced server-side
    _co_store.record_issue(
        severity="High",
        module="Company Onboarding",
        category="Validation",
        description="Company Code field has maxlength=4 on the HTML input, but "
                    "server-side validation may not enforce this. Names longer than "
                    "4 characters may be accepted if submitted via other means.",
        expected="Server should reject Company Codes longer than 4 characters.",
        actual="HTML maxlength=4 prevents typing more, but server validation unknown.",
        test_ref="CO-C06",
        status="Suspected",
    )

    # BUG-003 (MEDIUM): Inconsistent SweetAlert after submission
    _co_store.record_issue(
        severity="Medium",
        module="Company Onboarding",
        category="UX",
        description="SweetAlert confirmation after successful company creation is "
                    "inconsistent. Sometimes shows success, sometimes no confirmation.",
        expected="System should consistently show a success SweetAlert after every "
                 "successful company creation.",
        actual="Success SweetAlert is shown inconsistently.",
        test_ref="CO-P01",
        status="Suspected",
    )

    # BUG-004 (LOW): No Delete option
    _co_store.record_issue(
        severity="Low",
        module="Company Onboarding",
        category="Functionality",
        description="No Delete option exists anywhere on the Company Onboarding "
                    "screen - no Delete button per row, no Delete in More menu.",
        expected="Users should be able to delete a Company record via a Delete button.",
        actual="No Delete functionality available. Records cannot be removed.",
        test_ref="CO-P04",
        status="Suspected",
    )

    # ================================================================
    # LOG CAPTURE + PYTEST HOOKS
    # ================================================================

    class _LogCapture(logging.Handler):
        """Captures log messages during each test for step-level reporting."""

        def __init__(self, store):
            super().__init__()
            self.store = store

        def emit(self, record):
            try:
                msg = record.getMessage()
            except Exception:
                msg = str(record.msg)
            self.store.add_log_message(msg)


    _capture_handler = None


    def pytest_runtest_setup(item):
        """Start log capture before each test."""
        global _capture_handler
        _co_store.start_test(item.name, item.nodeid)

        _capture_handler = _LogCapture(_co_store)
        _capture_handler.setLevel(logging.INFO)
        try:
            if hasattr(log, "logger") and log.logger:
                log.logger.addHandler(_capture_handler)
            elif hasattr(log, "handlers"):
                log.handlers.append(_capture_handler)
        except Exception:
            logging.getLogger().addHandler(_capture_handler)


    def pytest_runtest_teardown(item, nextitem):
        """Detach log handler after each test."""
        global _capture_handler
        if _capture_handler is None:
            return
        try:
            if hasattr(log, "logger") and log.logger:
                log.logger.removeHandler(_capture_handler)
            elif hasattr(log, "handlers") and _capture_handler in log.handlers:
                log.handlers.remove(_capture_handler)
        except Exception:
            pass
        _capture_handler = None


    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_runtest_makereport(item, call):
        """Capture test result (pass/fail) and finalize for report."""
        outcome = yield
        report = outcome.get_result()
        if call.when == "call":
            if report.passed:
                status = "PASSED"
                error = ""
            elif report.failed:
                status = "FAILED"
                error = str(report.longrepr) if report.longrepr else ""
            else:
                status = "SKIPPED"
                error = ""
            _co_store.finish_test(status, error)


    def pytest_sessionfinish(session, exitstatus):
        """Generate Excel report at end of test session."""
        if not _co_store.has_results():
            return
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "reports"
        )
        try:
            filepath = generate_cs_report(
                _co_store.results, output_dir, issues=_co_store.known_issues
            )
            print("")
            print("=" * 60)
            print("  REPORT GENERATED: " + filepath)
            print("=" * 60)
        except Exception:
            import traceback as tb
            tb.print_exc()
            print("")
            print("  [WARNING] Report generation failed (see traceback above)")

else:
    # cs_report_generator not available -- tests will run without reporting
    print("[INFO] cs_report_generator not found -- Excel report generation disabled")
