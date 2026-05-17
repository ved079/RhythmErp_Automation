"""Run pytest tests via subprocess and stream results as SSE events."""

import subprocess
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from api.database import create_run, update_run_started, update_run_completed
from api.models import (
    RunStatus, TestStatus, TestResult, LogEvent, CreateRunRequest
)


PROJECT_ROOT = Path(__file__).parent.parent


def build_pytest_path(module: str, sub_module: str = None) -> str:
    """Build the filesystem path to run pytest on."""
    if sub_module:
        # e.g. pages/common_settings/modules/bank/test/
        test_dir = PROJECT_ROOT / "pages" / module / "modules" / sub_module / "test"
        if test_dir.exists():
            return str(test_dir)
    else:
        # e.g. pages/company_onboarding/test/
        test_dir = PROJECT_ROOT / "pages" / module / "test"
        if test_dir.exists():
            return str(test_dir)
    return ""


def build_test_filter(tests: list[str] = None) -> str:
    """Build pytest -k filter string from test names."""
    if not tests:
        return ""
    # Join with " or " for pytest -k flag
    return " or ".join(tests)


def run_tests_stream(request: CreateRunRequest):
    """Run pytest and yield SSE events. This is a generator for Server-Sent Events."""
    
    # 1. Create run record
    run_id = create_run(request.module, request.sub_module)
    
    # 2. Build pytest path
    test_path = build_pytest_path(request.module, request.sub_module)
    if not test_path:
        yield _sse_event(LogEvent(
            type="error",
            message=f"Test path not found for module={request.module}, sub_module={request.sub_module}",
            timestamp=datetime.now(timezone.utc),
        ))
        return run_id
    
    # 3. Build command
    cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=short"]
    
    # Add test filter if specific tests
    test_filter = build_test_filter(request.tests)
    if test_filter:
        cmd.extend(["-k", test_filter])
    
    # 4. Mark run as started
    update_run_started(run_id)
    yield _sse_event(LogEvent(
        type="log",
        message=f"Starting run {run_id}: {' '.join(cmd)}",
        timestamp=datetime.now(timezone.utc),
    ))
    
    # 5. Run pytest
    results = []
    total = passed = failed = skipped = 0
    start_time = time.time()
    
    env = os.environ.copy()
    if request.env_url:
        env["PACS_BASE_URL"] = request.env_url
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            bufsize=1,
        )
        
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            
            yield _sse_event(LogEvent(
                type="log",
                message=line,
                timestamp=datetime.now(timezone.utc),
            ))
            
            # Parse pytest output for test results
            parsed = _parse_pytest_line(line)
            if parsed:
                test_name, status = parsed
                if status == "passed":
                    passed += 1
                elif status == "failed":
                    failed += 1
                elif status == "skipped":
                    skipped += 1
                total += 1
                results.append(TestResult(
                    name=test_name,
                    status=status,
                    duration=0,
                ))
                
                yield _sse_event(LogEvent(
                    type="test_end",
                    message=f"{test_name} → {status}",
                    test_name=test_name,
                    status=status,
                    timestamp=datetime.now(timezone.utc),
                ))
        
        process.wait()
        duration = time.time() - start_time
        
        # Parse summary line for totals
        # e.g. "12 passed, 2 failed, 1 skipped in 15.3s"
        
    except Exception as e:
        duration = time.time() - start_time
        yield _sse_event(LogEvent(
            type="error",
            message=f"Run failed with error: {str(e)}",
            timestamp=datetime.now(timezone.utc),
        ))
    
    # 6. Save results
    final_status = RunStatus.COMPLETED if failed == 0 else RunStatus.FAILED
    update_run_completed(
        run_id=run_id,
        status=final_status,
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        duration=round(duration, 2),
        results=results,
    )
    
    yield _sse_event(LogEvent(
        type="run_end",
        message=f"Run {run_id} finished: {passed} passed, {failed} failed, {skipped} skipped in {duration:.1f}s",
        timestamp=datetime.now(timezone.utc),
    ))
    
    return run_id


def _parse_pytest_line(line: str) -> tuple:
    """Parse a pytest -v output line for PASSED/FAILED/SKIPPED.
    Returns (test_name, status) or None."""
    # Matches: pages/.../test_file.py::TestClass::test_name PASSED/FAILED/SKIPPED
    match = re.match(r".+::(.+?)\s+(PASSED|FAILED|SKIPPED|ERROR)", line)
    if match:
        return match.group(1), match.group(2).lower()
    return None


def _sse_event(event: LogEvent) -> str:
    """Convert a LogEvent to Server-Sent Event format."""
    return f"data: {event.model_dump_json()}\n\n"