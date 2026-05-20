"""
test_company_onboarding_update.py
----------------------------------
Test cases for Company Onboarding UPDATE functionality.

6 Steps:
  Step 1 = Company Details
  Step 2 = Promoters
  Step 3 = Address
  Step 4 = Business Details
  Step 5 = Infrastructure
  Step 6 = Configuration (Base Currency)
"""

import pytest
from datetime import datetime
from pages.company_onboarding.Company_Onboarding.company_onboarding_page_update import CompanyOnboardingUpdatePage
from pages.company_onboarding.data.company_onboarding_update_data import (
    UPDATE_COMPANY_NAME,
    ALL_UPDATES,
)
from common.logger import log
from pages.company_onboarding.test.update_results_store import co_update_results


class TestCompanyOnboardingUpdate:

    def test_update_using_one_call(self, logged_in_driver):
        update_page = CompanyOnboardingUpdatePage(logged_in_driver)
        company_name = UPDATE_COMPANY_NAME

        log.info("=" * 60)
        log.info(f"UPDATE TEST (ONE-CALL): {company_name}")
        log.info("=" * 60)

        update_page.navigate_to_page()
        update_page.wait_seconds(2)

        result = update_page.update_company(company_name, ALL_UPDATES)

        # Store result for update report
        co_update_results.append({
            "company_name": company_name,
            "status": "PASSED" if result["success"] else "FAILED",
            "duration": 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": result.get("message", ""),
            "before": result.get("before", {}),
            "after": result.get("after", {}),
            "updates_applied": ALL_UPDATES,
        })

        assert result["success"], f"Update failed: {result.get('error', 'Unknown error')}"

        # Verify before-values were captured (used in report)
        before = result.get("before", {})
        assert "step1" in before, "Step 1 before-values not captured for report"
        assert "step6" in before, "Step 6 (Configuration) before-values not captured for report"

        log.info(f"Before values captured for report:")
        for step_key, step_val in before.items():
            log.info(f"  {step_key}: {step_val}")

        log.info(f"Company '{company_name}' updated successfully!")
