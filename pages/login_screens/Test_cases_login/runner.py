"""
runner.py
---------
Pytest runner for PACS Automation test suite.
Run this to execute all tests with Excel report.

Usage:
    python runner.py                          → runs all tests
    python runner.py --auto-only               → runs only automatic tests (skips OTP tests)
    python runner.py --otp-only                → runs only tests that need manual OTP
    python runner.py --login                   → runs only login tests
    python runner.py --forgot-password         → runs only forgot password tests
    python runner.py --screen1                 → runs only Screen 1 tests
    python runner.py --screen2                 → runs only Screen 2 tests
    python runner.py --full-flow               → runs only full flow tests
    python runner.py --page-load               → runs only page load tests
    python runner.py --negative                → runs only negative/validation tests
    python runner.py --positive                → runs only positive tests
"""

import sys
import os

# Add project root to Python path so pytest finds all modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest


def run_tests(extra_args=None):
    """Execute pytest with Excel report generation via conftest.py hooks."""

    # Base arguments
    args = [
        "pages/login_screens/Test_cases_login/",
        "-v",
        "--tb=short",
        "-s",
    ]

    # Add any extra arguments passed in
    if extra_args:
        args.extend(extra_args)

    # Run pytest
    exit_code = pytest.main(args)

    return exit_code


if __name__ == "__main__":

    cli_args = sys.argv[1:]  # grab everything after the script name

    if not cli_args:
        # No arguments → run everything
        print("\n  Running ALL tests...")
        print("  Tests requiring OTP will pause for your input.\n")
        exit_code = run_tests()

    elif "--auto-only" in cli_args:
        # Skip manual OTP tests
        print("\n  Running AUTO tests only (skipping OTP tests)...\n")
        exit_code = run_tests(["-m", "not manual_otp"])

    elif "--otp-only" in cli_args:
        # Only run manual OTP tests
        print("\n  Running OTP tests only (have your email ready)...\n")
        exit_code = run_tests(["-m", "manual_otp"])

    elif "--login" in cli_args:
        print("\n  Running LOGIN tests only...\n")
        exit_code = run_tests(["-k", "test_l_01 or test_lp_ or test_ln_"])

    elif "--forgot-password" in cli_args:
        print("\n  Running FORGOT PASSWORD tests only...\n")
        exit_code = run_tests(["-k", "test_fp_"])

    elif "--page-load" in cli_args:
        print("\n  Running PAGE LOAD tests only...\n")
        exit_code = run_tests(["-k", "TestLoginPageLoad"])

    elif "--negative" in cli_args:
        print("\n  Running NEGATIVE / VALIDATION tests only...\n")
        exit_code = run_tests(["-k", "TestLoginNegative"])

    elif "--positive" in cli_args:
        print("\n  Running POSITIVE tests only...\n")
        exit_code = run_tests(["-k", "TestLoginPositive"])

    elif "--screen1" in cli_args:
        print("\n  Running Screen 1 tests only...\n")
        exit_code = run_tests(["-k", "Screen1"])

    elif "--screen2" in cli_args:
        print("\n  Running Screen 2 tests only...\n")
        exit_code = run_tests(["-k", "Screen2"])

    elif "--full-flow" in cli_args:
        print("\n  Running Full Flow tests only (have your email ready)...\n")
        exit_code = run_tests(["-k", "FullFlow"])

    else:
        # Unknown args → pass them directly to pytest
        print(f"\n  Running with custom args: {cli_args}\n")
        exit_code = run_tests(cli_args)

    sys.exit(exit_code)