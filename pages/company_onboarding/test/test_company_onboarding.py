"""
test_company_onboarding.py
---------------------------
Test cases for Company Onboarding screen.

Categories:
  1. SINGLE CREATION  â€” Create one company (happy path)
  2. BULK CREATION    â€” Create N companies in one go (data-driven)

Run single creation:
    python -m pytest tests/test_company_onboarding.py::TestSingleCompanyCreation -v

Run bulk creation (10 companies):
    python -m pytest tests/test_company_onboarding.py::TestBulkCompanyCreation -v

Run with HTML report:
    python -m pytest tests/test_company_onboarding.py -v --html=reports/company_onboarding_report.html

Run only bulk with custom count (via env variable):
    BULK_COUNT=50 python -m pytest tests/test_company_onboarding.py::TestBulkCompanyCreation -v
"""

import os
import time
from datetime import datetime

import pytest

from ..data.company_onboarding_data import SINGLE_COMPANY, generate_bulk_companies, save_bulk_data_to_excel
from common.logger import log
from pages.company_onboarding.Company_Onboarding.company_onboarding_page import CompanyOnboardingPage


# ================================================================
# BULK COUNT â€” configurable via environment variable
# ================================================================
BULK_COUNT = int(os.getenv("BULK_COUNT", "10"))  # Default: 10 (safe for quick testing)


# ================================================================
# TEST CLASS 1: SINGLE COMPANY CREATION
# ================================================================

class TestSingleCompanyCreation:
    """Tests for creating a single company via the Company Onboarding screen."""

    def test_create_single_company(self, logged_in_driver):
        """
        Happy path — create one company using SINGLE_COMPANY template.
        Opens ADD form, fills Step 1, goes to Step 2, fills address, submits.
        """
        driver = logged_in_driver
        page = CompanyOnboardingPage(driver)

        log.test_start("Create Single Company")

        # Step 0: Navigate to Company Onboarding page
        log.step(0, "Navigate to Company Onboarding page")
        page.navigate_to_page()
        assert page.is_page_loaded(), "Company Onboarding page did not load"

        # Step 1: Open the ADD form
        log.step(1, "Open ADD form")
        page.open_add_form()
        assert page.is_add_form_open(), "ADD dialog did not open"

        # Step 2: Fill Company Details
        log.step(2, "Fill Company Details (Step 1)")
        page.fill_company_details(SINGLE_COMPANY)

        # Step 3: Navigate to Promoters (Step 2) then to Address Details (Step 3)
        log.step(3, "Navigate to Promoters Details (Step 2)")
        page.go_to_step2()          # Step 1 → Step 2 (Promoters)
        log.step(4, "Navigate to Address Details (Step 3)")
        page._click_next()          # Step 2 → Step 3 (Address)
        page.wait_seconds(1)

        # Step 4 (renumbered): Fill Address Details
        log.step(5, "Fill Address Details (Step 3)")
        assert page.is_step2_visible(), "Step 3 (Address Details) is not visible"
        page.fill_address_details(SINGLE_COMPANY)

        # Step 5: Submit
        log.step(6, "Submit company form")
        page.submit()

        # Step 6: Verify — dialog should close after successful submission
        log.step(7, "Verify submission")
        page.wait_seconds(2)
        msg = page.get_success_message(timeout=8)
        if msg:
            log.info(f"Server message: {msg}")

        # Check dialog is closed (company name input gone)
        dialog_closed = page.is_dialog_closed()
        assert dialog_closed, f"Dialog did not close after submit. Message: {msg}"

        log.passed("Single company created successfully!")
        log.test_end("Create Single Company", "PASSED")

    def test_create_single_company_one_call(self, logged_in_driver):
        """
        Test the one-call convenience method: create_company(data).
        Does everything in a single method call.
        """
        driver = logged_in_driver
        page = CompanyOnboardingPage(driver)

        log.test_start("Create Company (One-Call Method)")

        # Navigate and create in one call
        page.navigate_to_page()
        assert page.is_page_loaded(), "Company Onboarding page did not load"

        page.create_company(SINGLE_COMPANY)

        # Verify via table search (server takes 30-40s to save)
        company_name = SINGLE_COMPANY['company_name']
        # Poll table until company appears (up to 90s)
        found = False
        for attempt in range(18):
            log.info(f"Table check attempt {attempt + 1}/18 (every 5s)...")
            try:
                page.click(("css", "button[mattooltip='REFRESH'], div[mattooltip='REFRESH'] button"))
                page.wait_seconds(3)
            except Exception:
                pass
            found = page.verify_company_exists(company_name)
            if found:
                break
            page.wait_seconds(5)
        assert found, f"Company not found in table after 90s: {company_name}"

        log.passed(f"One-call company creation successful! Verified: {company_name}")
        log.test_end("Create Company (One-Call Method)", "PASSED")


# ================================================================
# TEST CLASS 2: BULK COMPANY CREATION
# ================================================================

class TestBulkCompanyCreation:
    """Tests for creating multiple companies in a loop."""

    def test_create_10_companies_bulk(self, logged_in_driver):
        """
        Create 10 companies using the bulk creation method.
        Uses generate_bulk_companies() for test data.
        All 10 must pass for the test to pass.
        """
        driver = logged_in_driver
        page = CompanyOnboardingPage(driver)

        count = 10
        log.test_start(f"Bulk Create {count} Companies")

        # Navigate to page
        page.navigate_to_page()
        assert page.is_page_loaded(), "Company Onboarding page did not load"

        # Generate data
        companies = generate_bulk_companies(count)
        log.info(f"Generated {len(companies)} unique companies")

        # Run bulk creation
        results = page.create_bulk_companies(companies)

        # Verify results
        passed = sum(1 for r in results if r["status"] == "passed")
        failed = sum(1 for r in results if r["status"] == "failed")

        log.info(f"Bulk Results: Passed={passed}, Failed={failed}")

        # Print summary of failures
        if failed > 0:
            for r in results:
                if r["status"] == "failed":
                    log.failed(f"  [{r['index']}] {r['company_name']}: {r['error']}")

        assert passed == count, f"Only {passed}/{count} companies created. {failed} failed."

        log.passed(f"All {count} companies created successfully!")
        log.test_end(f"Bulk Create {count} Companies", "PASSED")

    def test_create_n_companies_configurable(self, logged_in_driver):
        """
        Create N companies where N is set via BULK_COUNT env variable.
        Default is 10. Override with: BULK_COUNT=50 python -m pytest ...

        This test also generates an Excel file with the created data.
        """
        driver = logged_in_driver
        page = CompanyOnboardingPage(driver)

        count = BULK_COUNT
        log.test_start(f"Bulk Create {count} Companies (Configurable)")

        # Navigate to page
        page.navigate_to_page()
        assert page.is_page_loaded(), "Company Onboarding page did not load"

        # Generate data
        companies = generate_bulk_companies(count)
        log.info(f"Generated {len(companies)} unique companies for bulk creation")

        # Save generated data to Excel for reference
        from config import DATA_DIR
        excel_path = os.path.join(DATA_DIR, f"bulk_companies_{count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        save_bulk_data_to_excel(companies, excel_path)
        log.info(f"Generated data saved to: {excel_path}")

        # Progress callback â€” logs every 50 companies
        def progress_callback(current, total, name):
            if current % 50 == 0 or current == total:
                log.info(f"  Progress: {current}/{total} completed")

        # Run bulk creation
        results = page.create_bulk_companies(companies, on_progress=progress_callback)

        # Save results to Excel
        from config import REPORT_DIR
        results_path = os.path.join(REPORT_DIR, f"bulk_results_{count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        try:
            import pandas as pd
            df = pd.DataFrame(results)
            df.to_excel(results_path, index=False, engine="openpyxl")
            log.info(f"Results saved to: {results_path}")
        except Exception as e:
            log.warning(f"Could not save results Excel: {e}")

        # Verify
        passed = sum(1 for r in results if r["status"] == "passed")
        failed = sum(1 for r in results if r["status"] == "failed")

        log.separator()
        log.info(f" FINAL RESULTS")
        log.info(f" Total  : {count}")
        log.info(f" Passed : {passed}")
        log.info(f" Failed : {failed}")
        log.info(f" Time   : see pytest duration")
        log.separator()

        # Print failures
        if failed > 0:
            for r in results:
                if r["status"] == "failed":
                    log.failed(f"  [{r['index']}] {r['company_name']}: {r['error']}")

        # Assert all passed
        assert passed == count, f"Only {passed}/{count} companies created. {failed} failed."

        log.passed(f"All {count} companies created successfully!")
        log.test_end(f"Bulk Create {count} Companies", "PASSED")

    def test_create_1000_companies(self, logged_in_driver):
        """
        Full load test â€” create 1000 companies in one run.
        Takes ~2-3 hours. Run only when needed:

            python -m pytest tests/test_company_onboarding.py::TestBulkCompanyCreation::test_create_1000_companies -v
        """
        driver = logged_in_driver
        page = CompanyOnboardingPage(driver)

        count = 1000
        log.test_start(f"BULK LOAD TEST â€” {count} Companies")

        # Navigate to page
        page.navigate_to_page()
        assert page.is_page_loaded(), "Company Onboarding page did not load"

        # Generate 1000 unique companies
        log.info("Generating 1000 unique companies...")
        start_time = time.time()
        companies = generate_bulk_companies(count)
        gen_time = time.time() - start_time
        log.info(f"Data generated in {gen_time:.1f}s")

        # Save generated data
        from config import DATA_DIR
        excel_path = os.path.join(DATA_DIR, f"bulk_1000_companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        save_bulk_data_to_excel(companies, excel_path)

        # Progress callback
        def progress_callback(current, total, name):
            if current % 100 == 0 or current == 1 or current == total:
                elapsed = time.time() - start_time
                rate = current / elapsed if elapsed > 0 else 0
                remaining = (total - current) / rate if rate > 0 else 0
                log.info(
                    f"  [{current}/{total}] {name} | "
                    f"{rate:.1f} comp/min | ~{remaining:.0f} min remaining"
                )

        start_time = time.time()

        # Run bulk creation
        results = page.create_bulk_companies(companies, on_progress=progress_callback)

        total_time = time.time() - start_time

        # Save results
        from config import REPORT_DIR
        results_path = os.path.join(REPORT_DIR, f"bulk_1000_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        try:
            import pandas as pd
            df = pd.DataFrame(results)
            df.to_excel(results_path, index=False, engine="openpyxl")
        except Exception:
            pass

        # Final summary
        passed = sum(1 for r in results if r["status"] == "passed")
        failed = sum(1 for r in results if r["status"] == "failed")

        log.separator("=")
        log.info(f" 1000 COMPANY BULK TEST COMPLETE")
        log.info(f" Passed : {passed}")
        log.info(f" Failed : {failed}")
        log.info(f" Total time: {total_time / 60:.1f} minutes")
        if total_time > 0:
            log.info(f" Avg per company: {total_time / count:.1f} seconds")
        log.info(f" Data Excel : {excel_path}")
        log.info(f" Results Excel: {results_path}")
        log.separator("=")

        assert passed == count, f"Only {passed}/{count} companies created."

# ================================================================
# TEST CLASS 3: PARALLEL COMPANY CREATION (pytest-xdist)
# ================================================================

class TestParallelCompanyCreation:
    """
    Parallel company creation using pytest-xdist.
    Each company runs as a separate test with its own browser instance.

    Run with 5 parallel workers (20 companies):
        $env:BULK_COUNT = "20"
        python -m pytest pages/company_onboarding/test/test_company_onboarding.py::TestParallelCompanyCreation -n 5 -v

    Each worker gets its own browser + login session.
    20 companies / 5 workers = ~4 batches x 68s = ~4.5 min (vs ~23 min sequential)
    """

    @pytest.mark.parametrize("idx", range(BULK_COUNT))
    def test_create_company_parallel(self, logged_in_driver, idx):
        """Create a single company with unique data. Use -n N to run N in parallel."""
        import time
        driver = logged_in_driver
        page = CompanyOnboardingPage(driver)

        company = generate_bulk_companies(1)[0]
        company_name = company.get("company_name", f"Company_{idx}")

        page.navigate_to_page()
        assert page.is_page_loaded(), "Company Onboarding page did not load"

        start = time.time()
        try:
            page.create_company(company)
            elapsed = time.time() - start
            log.info(f"[Worker-{idx}] {company_name} -> PASSED ({elapsed:.1f}s)")
        except Exception as e:
            elapsed = time.time() - start
            log.failed(f"[Worker-{idx}] {company_name} -> FAILED ({elapsed:.1f}s): {e}")
            raise