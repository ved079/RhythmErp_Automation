import subprocess
import threading
import os
import glob
import time
from datetime import datetime
import database

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CREATION_TEST_FILE = os.path.join(PROJECT_ROOT, "pages", "company_onboarding", "test", "test_company_onboarding.py")
UPDATE_TEST_FILE = os.path.join(PROJECT_ROOT, "pages", "company_onboarding", "test", "test_company_onboarding_update.py")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "pages", "company_onboarding", "reports")

def _find_latest_report(pattern="*UpdateReport*"):
    if not os.path.exists(REPORTS_DIR):
        return None
    files = glob.glob(os.path.join(REPORTS_DIR, pattern))
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def run_test(test_type, run_id, company_count=1):
    start_time = time.time()
    log_lines = []
    status = "PASSED"
    error_msg = None
    report_path = None
    try:
        if test_type == "creation":
            cmd = ["python", "-m", "pytest", CREATION_TEST_FILE + "::TestSingleCompanyCreation::test_create_single_company_one_call", "-v", "-s"]
            test_name = "Company Creation"
        elif test_type == "update":
            cmd = ["python", "-m", "pytest", UPDATE_TEST_FILE + "::TestCompanyOnboardingUpdate::test_update_using_one_call", "-v", "--tb=short"]
            test_name = "Company Update"
        elif test_type == "full":
            cmd = ["python", "-m", "pytest", CREATION_TEST_FILE + "::TestSingleCompanyCreation::test_create_single_company_one_call", "-v", "-s", "--", UPDATE_TEST_FILE + "::TestCompanyOnboardingUpdate::test_update_using_one_call", "-v", "--tb=short"]
            test_name = "Full Suite"
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        log_lines.append(f"Starting {test_name} test...")
        log_lines.append(f"Command: {' '.join(cmd)}")
        log_lines.append(f"Working directory: {PROJECT_ROOT}")
        log_lines.append("")
        process = subprocess.Popen(cmd, cwd=PROJECT_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            line = line.rstrip()
            log_lines.append(line)
        process.wait(timeout=600)
        if process.returncode != 0:
            status = "FAILED"
            error_msg = f"Exit code: {process.returncode}"
            log_lines.append(f"\nTest FAILED with exit code {process.returncode}")
        else:
            log_lines.append(f"\nTest PASSED successfully")
        if test_type == "update":
            report = _find_latest_report("*UpdateReport*")
        else:
            report = _find_latest_report("*DataReport*")
        if report:
            report_path = report
            log_lines.append(f"Report generated: {report}")
    except subprocess.TimeoutExpired:
        status = "FAILED"
        error_msg = "Test timed out after 10 minutes"
        log_lines.append(error_msg)
    except Exception as e:
        status = "FAILED"
        error_msg = str(e)
        log_lines.append(f"Error: {e}")
    finally:
        duration = round(time.time() - start_time, 1)
        database.update_test_run(run_id=run_id, status=status, duration=duration, error_message=error_msg, report_path=report_path, log_output="\n".join(log_lines))
        print(f"[Run {run_id}] {status} in {duration}s")

def start_test(test_type, company_count=1):
    run_id = database.create_test_run(test_type)
    thread = threading.Thread(target=run_test, args=(test_type, run_id, company_count), daemon=True)
    thread.start()
    return run_id