"""
Common runner for edge-case test cases.

Usage standalone:
    python edge_tests/runner.py
    python edge_tests/runner.py --tc "Farmer Registration TC"
    python edge_tests/runner.py --tc "Farmer Registration TC" "Customer Registration TC"
    python edge_tests/runner.py --headless

Usage from api.py:
    from edge_tests.runner import run_test_case, run_all_selected, generate_report
    results = run_all_selected(["Farmer Registration TC", "Customer Registration TC"], driver, wait)
    report_path = generate_report(results)

Usage via pytest (original way):
    pytest edge_tests/test_farmer_edges.py -v
    pytest edge_tests/test_customer_edges.py -v
"""

import logging
import sys
import os
import argparse
import time
from datetime import datetime

# Ensure project root is on path so edge_tests imports work
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from edge_tests.test_farmer_edges import TestFarmerEdgeCases, do_setup_and_navigate as farmer_setup
from edge_tests.test_farmer_edges import do_reset_between_tests as farmer_reset
from edge_tests.test_farmer_edges import take_screenshot as farmer_screenshot
from edge_tests.test_customer_edges import TestCustomerEdgeCases, do_setup_and_navigate as customer_setup
from edge_tests.test_customer_edges import do_reset_between_tests as customer_reset
from edge_tests.test_customer_edges import take_screenshot as customer_screenshot
from edge_tests.test_agent_edges import TestAgentEdgeCases, do_setup_and_navigate as agent_setup
from edge_tests.test_agent_edges import do_reset_between_tests as agent_reset
from edge_tests.test_agent_edges import take_screenshot as agent_screenshot
from edge_tests.test_employee_edges import TestEmployeeEdgeCases, do_setup_and_navigate as employee_setup
from edge_tests.test_employee_edges import do_reset_between_tests as employee_reset
from edge_tests.test_employee_edges import take_screenshot as employee_screenshot
from edge_tests.test_supplier_edges import TestSupplierEdgeCases, do_setup_and_navigate as supplier_setup
from edge_tests.test_supplier_edges import do_reset_between_tests as supplier_reset
from edge_tests.test_supplier_edges import take_screenshot as supplier_screenshot

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  TEST REGISTRY
#  Format: "Display Name" -> {
#      "class": TestClass,
#      "methods": [...],
#      "setup": standalone_setup_function,
#      "reset": standalone_reset_function,
#      "screenshot": screenshot_function
#  }
# ─────────────────────────────────────────────
TEST_REGISTRY = {
    "Farmer Registration TC": {
        "class": TestFarmerEdgeCases,
        "methods": [
            # All pure validation — no side effects, no form submission
            "test_empty_form_required_field_errors",
            "test_phone_9_digits_rejected",
            "test_phone_10_digits_accepted",
            "test_phone_11_digits_rejected",
            "test_phone_rejects_letters",
            "test_invalid_email_format_rejected",
            "test_pincode_rejects_letters",
            "test_name_rejects_numbers",
            "test_reset_button_clears_form",
        ],
        "setup": farmer_setup,
        "reset": farmer_reset,
        "screenshot": farmer_screenshot,
    },
    "Customer Registration TC": {
        "class": TestCustomerEdgeCases,
        "methods": [
            # All pure validation — no side effects, no form submission
            "test_customer_empty_form_errors",
            "test_customer_phone_9_digits_rejected",
            "test_customer_phone_10_digits_accepted",
            "test_customer_phone_11_digits_rejected",
            "test_customer_pan_rejects_invalid_format",
            "test_customer_pan_valid_format_no_error",
            "test_customer_deposit_rejects_letters",
            "test_customer_reset_button_clears_form",
        ],
        "setup": customer_setup,
        "reset": customer_reset,
        "screenshot": customer_screenshot,
    },
    "Agent Registration TC": {
        "class": TestAgentEdgeCases,
        "methods": [
            # All pure validation — no side effects, no form submission
            "test_agent_empty_form_errors",
            "test_agent_phone_rejects_pipe",
            "test_agent_phone_accepts_normal_input",
            "test_agent_commission_rejects_negative",
            "test_agent_commission_accepts_decimal",
            "test_agent_commission_rejects_letters",
            "test_agent_reset_button_clears_form",
        ],
        "setup": agent_setup,
        "reset": agent_reset,
        "screenshot": agent_screenshot,
    },
    "Employee Registration TC": {
        "class": TestEmployeeEdgeCases,
        "methods": [
            # All pure validation — no side effects, no form submission
            "test_employee_empty_form_errors",
            "test_employee_email_rejects_invalid",
            "test_employee_email_accepts_valid",
            "test_employee_phone_rejects_letters",
            "test_employee_phone_accepts_numbers",
            "test_employee_reset_button_clears_form",
        ],
        "setup": employee_setup,
        "reset": employee_reset,
        "screenshot": employee_screenshot,
    },
    "Supplier Registration TC": {
        "class": TestSupplierEdgeCases,
        "methods": [
            # All pure validation — no side effects, no form submission
            "test_supplier_empty_form_errors",
            "test_supplier_phone_9_digits_rejected",
            "test_supplier_phone_10_digits_accepted",
            "test_supplier_phone_11_digits_rejected",
            "test_supplier_pan_rejects_invalid_format",
            "test_supplier_pan_valid_format_no_error",
            "test_supplier_reset_button_clears_form",
        ],
        "setup": supplier_setup,
        "reset": supplier_reset,
        "screenshot": supplier_screenshot,
    },
}


def run_test_case(test_name, driver, wait):
    """
    Run a single test case and return rich results.

    Returns:
        dict with test_case, passed, summary, total, pass_count, fail_count, results[]
    """
    if test_name not in TEST_REGISTRY:
        logger.error(f"Unknown test case: {test_name}")
        return {
            "test_case": test_name, "passed": False, "summary": "Unknown test case",
            "total": 0, "pass_count": 0, "fail_count": 0, "results": []
        }

    tc = TEST_REGISTRY[test_name]
    cls = tc["class"]
    setup_fn = tc["setup"]
    reset_fn = tc["reset"]
    screenshot_fn = tc["screenshot"]
    test_methods = tc["methods"]

    instance = cls()

    total = len(test_methods)
    pass_count = 0
    fail_count = 0
    results = []

    # Run setup ONCE — navigates to the correct page
    try:
        setup_fn(driver, wait)
    except Exception as e:
        logger.error(f"SETUP FAILED for {test_name}: {e}")
        return {
            "test_case": test_name, "passed": False,
            "summary": f"0/{total} passed (setup failed)",
            "total": total, "pass_count": 0, "fail_count": total,
            "results": [{"method": "setup_and_navigate", "status": "ERROR",
                         "error": str(e), "screenshot": None,
                         "timestamp": datetime.now().strftime("%H:%M:%S")}]
        }

    for i, method_name in enumerate(test_methods):
        method = getattr(instance, method_name)
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "PASSED"
        error_msg = None
        screenshot_path = None

        try:
            method(driver, wait)
            logger.info(f"  ✅ {method_name}: PASSED")
            pass_count += 1
        except AssertionError as e:
            error_msg = str(e)
            status = "FAILED"
            fail_count += 1
            logger.error(f"  ❌ {method_name}: FAILED — {e}")
            try:
                screenshot_path = screenshot_fn(driver, method_name)
            except Exception:
                pass
        except Exception as e:
            error_msg = str(e)
            status = "ERROR"
            fail_count += 1
            logger.error(f"  ❌ {method_name}: ERROR — {e}")
            try:
                screenshot_path = screenshot_fn(driver, method_name)
            except Exception:
                pass

        results.append({
            "method": method_name, "status": status,
            "error": error_msg, "screenshot": screenshot_path,
            "timestamp": timestamp
        })

        # Reset form between tests (except after last)
        if i < len(test_methods) - 1:
            try:
                reset_fn(driver, wait)
            except Exception:
                try:
                    driver.refresh()
                    time.sleep(2)
                except Exception:
                    pass

    all_passed = (fail_count == 0)
    summary = f"{pass_count}/{total} passed"

    return {
        "test_case": test_name, "passed": all_passed, "summary": summary,
        "total": total, "pass_count": pass_count, "fail_count": fail_count,
        "results": results
    }


def run_all_selected(test_names, driver, wait):
    """Run multiple test cases and return all results."""
    all_results = []
    for test_name in test_names:
        if test_name in TEST_REGISTRY:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*50}")
            result = run_test_case(test_name, driver, wait)
            all_results.append(result)
            logger.info(f"{test_name}: {result['summary']}")
        else:
            logger.warning(f"Skipped unknown test case: {test_name}")
    return all_results


def generate_report(results):
    """Generate Excel report. Delegates to report_generator."""
    try:
        from edge_tests.report_generator import generate_report as _gen
        return _gen(results)
    except ImportError:
        logger.error("report_generator.py not found — skipping report generation.")
        return None


# ═══════════════════════════════════════════════════════════════
#  STANDALONE MODE — run directly from terminal
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Setup logging for standalone run
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )

    parser = argparse.ArgumentParser(description="Run edge-case tests and generate Excel report")
    parser.add_argument("--tc", nargs="+", default=list(TEST_REGISTRY.keys()),
                        help="Test cases to run (default: all in registry)")
    parser.add_argument("--headless", action="store_true", help="Run Chrome headless")
    args = parser.parse_args()

    # Import Selenium here (only needed in standalone mode)
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager

    import config

    driver = None
    try:
        # 1. Start Chrome
        print("\n" + "=" * 60)
        print("  FPC Edge-Case Test Runner")
        print("=" * 60)
        logging.info("Starting Chrome...")
        options = webdriver.ChromeOptions()
        if args.headless:
            options.add_argument("--headless")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 60)

        # 2. Run tests (each test case's setup handles login + navigation)
        results = run_all_selected(args.tc, driver, wait)

        # 3. Print summary
        total_tests = 0
        total_pass = 0
        total_fail = 0
        print("\n" + "=" * 60)
        print("  RESULTS")
        print("=" * 60)
        for r in results:
            print(f"\n  {r['test_case']}: {r['summary']}")
            for d in r['results']:
                icon = "✅" if d['status'] == "PASSED" else "❌"
                print(f"    {icon} {d['method']}")
                if d['error']:
                    print(f"       → {d['error']}")
            total_tests += r['total']
            total_pass += r['pass_count']
            total_fail += r['fail_count']

        rate = f"{(total_pass / total_tests * 100):.0f}%" if total_tests > 0 else "N/A"
        print(f"\n  OVERALL: {total_pass}/{total_tests} passed ({rate})")
        print("=" * 60)

        # 4. Generate Excel report
        report_path = generate_report(results)
        if report_path:
            print(f"\n  📊 Report saved: {report_path}\n")

    except Exception as e:
        logging.error(f"Run failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            logging.info("Chrome closed.")
