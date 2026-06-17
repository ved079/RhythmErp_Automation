"""Run pytest tests via subprocess and stream results as SSE events.

In v3.0, this module also sends a callback to Next.js when a run completes,
so that run results are always persisted even if the user navigates away
from the page during the SSE stream.
"""

import subprocess
import os
import re
import ast
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

from api.database import create_run, update_run_started, update_run_completed, update_run_status
from api.models import (
    RunStatus, TestStatus, TestResult, LogEvent, CreateRunRequest, RunCompletionPayload
)


PROJECT_ROOT = Path(__file__).parent.parent

# Active subprocess tracking: run_id -> subprocess.Popen
_active_processes: dict[str, subprocess.Popen] = {}

# Callback configuration
NEXTJS_CALLBACK_URL = os.getenv("NEXTJS_CALLBACK_URL", "http://localhost:3000")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "rhythmerp-proxy-key-change-in-production")
CALLBACK_ENABLED = os.getenv("RUN_CALLBACK_ENABLED", "true").lower() == "true"

logger = logging.getLogger(__name__)


# --- Input Validation ---

ALLOWED_MODULES = {
    "login_screens", "access", "company_onboarding",
    "common_settings", "commodity_settings", "registration",
}

ALLOWED_SUB_MODULES = {
    # access
    "entity_group_definition", "user_creation_screen", "role_creation_screen",
    # common_settings
    "bank", "designation", "error_code_mst", "hsn_sac", "season",
    "tax_authority", "tax_rate", "uom", "uom_conversion", "vehicle_master",
    # commodity_settings
    "crop_master", "item_master", "quality_parameter_master", "services_master",
    "item_category", "item_group", "commodity_quality_parameter",
    "commodity_base_rate", "item_attribute",
    # registration
    "agent", "supplier", "customer", "farmer",
}


def validate_module_path(module: str, sub_module: str = None) -> None:
    """Validate module and sub_module against whitelist to prevent path traversal."""
    if not module or not re.match(r'^[a-zA-Z0-9_]+$', module):
        raise ValueError(f"Invalid module name: {module}")
    if sub_module:
        if not re.match(r'^[a-zA-Z0-9_]+$', sub_module):
            raise ValueError(f"Invalid sub_module name: {sub_module}")
    # Verify the path actually exists
    test_path = build_pytest_path(module, sub_module)
    if not test_path:
        raise ValueError(f"Test path not found for module={module}, sub_module={sub_module}")


def build_pytest_path(module: str, sub_module: str = None) -> str:
    """Build the filesystem path to run pytest on."""
    if sub_module:
        test_dir = PROJECT_ROOT / "pages" / module / "modules" / sub_module / "test"
        if test_dir.exists():
            return str(test_dir)
        # Fallback: check for test files directly in sub_module dir
        test_dir = PROJECT_ROOT / "pages" / module / "modules" / sub_module
        if test_dir.exists():
            return str(test_dir)
    else:
        test_dir = PROJECT_ROOT / "pages" / module / "test"
        if test_dir.exists():
            return str(test_dir)
        # Some modules like login_screens have tests in subdirectories
        test_dir = PROJECT_ROOT / "pages" / module / "Test_cases_login"
        if test_dir.exists():
            return str(test_dir)
    return ""


def _collect_test_ids(test_path: str) -> list:
    """Run pytest --collect-only to get all test node IDs."""
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", test_path, "--collect-only", "-q"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
            timeout=30
        )
        ids = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if "::" in line and not line.startswith("<") and not line.startswith("no tests") and "collected" not in line:
                node_id = line.split(" ")[0] if " " in line else line
                ids.append(node_id)
        return ids
    except Exception:
        return []


def _extract_docstring(file_path: str, func_name: str) -> str:
    """Extract docstring from a specific test function in a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                doc = ast.get_docstring(node) or ""
                return doc
    except Exception:
        pass
    return ""


def _match_score(description: str, docstring: str, node_id: str) -> float:
    """Calculate match score between description and test docstring/name."""
    desc_lower = description.lower()
    doc_lower = (docstring + " " + node_id).lower()

    skip_words = {"the", "and", "for", "with", "from", "that", "this", "should",
                  "field", "fields", "are", "not", "was", "has", "been", "into"}
    desc_words = set(w for w in desc_lower.split() if len(w) > 2 and w not in skip_words)

    if not desc_words:
        return 0

    matches = sum(1 for w in desc_words if w in doc_lower)
    return matches / len(desc_words)


def _load_test_cases_for_path(test_path: str) -> dict:
    """Load test_cases.json and find the matching module key."""
    tc_path = PROJECT_ROOT / "api" / "test_cases.json"
    if not tc_path.exists():
        return {}

    try:
        with open(tc_path, "r", encoding="utf-8") as f:
            all_tc = json.load(f)
    except Exception:
        return {}

    # Find matching key by checking path parts
    path_parts = Path(test_path).parts
    for key in all_tc:
        # Normalize the key for comparison
        normalized = key.lower().replace("-", "_").replace(" ", "_")
        for part in path_parts:
            if normalized == part.lower():
                return all_tc[key]
    return {}


def _resolve_tests(test_path: str, requested: list) -> list:
    """Resolve frontend test IDs to actual pytest node IDs by matching descriptions to docstrings."""
    # Step 1: Load test_cases.json to get descriptions
    tc_module = _load_test_cases_for_path(test_path)
    tc_tests = tc_module.get("tests", []) if tc_module else []

    if not tc_tests:
        # No test_cases data — fall back to index-based
        all_ids = _collect_test_ids(test_path)
        resolved = []
        for t in requested:
            try:
                idx = int(t) - 1
                if 0 <= idx < len(all_ids):
                    resolved.append(all_ids[idx])
            except ValueError:
                for nid in all_ids:
                    if t.lower() in nid.lower():
                        resolved.append(nid)
                        break
        return resolved

    # Build ID -> description mapping
    id_to_desc = {}
    for t in tc_tests:
        id_to_desc[str(t.get("id", ""))] = t.get("description", "")

    # Step 2: Collect all pytest node IDs
    all_ids = _collect_test_ids(test_path)

    # Step 3: Parse docstrings for each test file
    node_id_to_doc = {}
    for nid in all_ids:
        parts = nid.split("::")
        if len(parts) < 3:
            node_id_to_doc[nid] = ""
            continue
        file_rel = parts[0]
        file_abs = PROJECT_ROOT / file_rel
        func_name = parts[-1]
        doc = _extract_docstring(str(file_abs), func_name)
        node_id_to_doc[nid] = doc

    # Step 4: Match each requested ID to best matching node ID
    resolved = []
    used = set()
    for t in requested:
        desc = id_to_desc.get(str(t), "")
        if not desc:
            continue

        best_match = None
        best_score = 0

        for nid, doc in node_id_to_doc.items():
            if nid in used:
                continue
            score = _match_score(desc, doc, nid)
            if score > best_score:
                best_score = score
                best_match = nid

        if best_match and best_score > 0.3:
            resolved.append(best_match)
            used.add(best_match)

    return resolved


def stop_run(run_id: str) -> bool:
    """Stop a running test subprocess. Returns True if process was killed."""
    process = _active_processes.get(run_id)
    if not process or process.poll() is not None:
        return False

    try:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)

        update_run_status(run_id, RunStatus.STOPPED)
        return True
    except Exception:
        return False
    finally:
        _active_processes.pop(run_id, None)


def _send_run_callback(run_id: str, module: str, sub_module: str | None,
                       passed: int, failed: int, skipped: int, total: int,
                       duration: float, status: str, results: list[TestResult],
                       started_at: str | None, completed_at: str | None) -> None:
    """Send run completion callback to Next.js.

    This ensures run results are persisted even if the user navigated away
    from the SSE stream. The callback is fire-and-forget — failures are logged
    but don't affect the test run.
    """
    if not CALLBACK_ENABLED:
        return

    callback_url = f"{NEXTJS_CALLBACK_URL}/api/runs/callback"

    payload = RunCompletionPayload(
        run_id=run_id,
        module=module,
        sub_module=sub_module,
        passed=passed,
        failed=failed,
        skipped=skipped,
        total=total,
        duration_seconds=round(duration, 2),
        status=status,
        results=[r.model_dump() for r in results],
        started_at=started_at,
        completed_at=completed_at,
    )

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                callback_url,
                json=payload.model_dump(),
                headers={
                    "Content-Type": "application/json",
                    "X-Proxy-API-Key": PROXY_API_KEY,
                },
            )
            if resp.status_code >= 300:
                logger.warning(f"[Callback] Next.js returned {resp.status_code}: {resp.text[:200]}")
            else:
                logger.info(f"[Callback] Run {run_id} results synced to Next.js ({status})")
    except httpx.ConnectError:
        logger.warning(f"[Callback] Could not reach Next.js at {NEXTJS_CALLBACK_URL} — run results saved locally only")
    except Exception as e:
        logger.warning(f"[Callback] Failed to sync run {run_id}: {e}")


def run_tests_stream(request: CreateRunRequest):
    """Run pytest and yield SSE events. This is a generator for Server-Sent Events."""

    # 1. Validate inputs
    try:
        validate_module_path(request.module, request.sub_module)
    except ValueError as e:
        yield _sse_event(LogEvent(
            type="error",
            message=str(e),
            timestamp=datetime.now(timezone.utc),
        ))
        return

    # 2. Create run record
    run_id = create_run(request.module, request.sub_module)

    # 3. Build pytest path
    test_path = build_pytest_path(request.module, request.sub_module)
    if not test_path:
        yield _sse_event(LogEvent(
            type="error",
            message=f"Test path not found for module={request.module}, sub_module={request.sub_module}",
            timestamp=datetime.now(timezone.utc),
        ))
        return

    # 4. Build command
    cmd = ["python", "-m", "pytest", "-v", "--tb=short"]

    # Add specific tests if provided - resolve IDs to actual pytest node IDs
    if request.tests:
        resolved = _resolve_tests(test_path, request.tests)
        if resolved:
            cmd.extend(resolved)
        else:
            cmd.append(test_path)
    else:
        cmd.append(test_path)

    # 5. Mark run as started
    update_run_started(run_id)
    started_at_iso = datetime.now(timezone.utc).isoformat()

    yield _sse_event(LogEvent(
        type="log",
        message=f"Starting run {run_id}: {' '.join(cmd)}",
        timestamp=datetime.now(timezone.utc),
    ))

    # 6. Run pytest
    results = []
    total = passed = failed = skipped = 0
    start_time = time.time()

    env = os.environ.copy()
    if request.env_url:
        env["RHYTHMERP_BASE_URL"] = request.env_url
    if request.erp_token:
        env["ERP_TOKEN"] = request.erp_token
    if request.erp_tenant_id:
        env["ERP_TENANT_ID"] = request.erp_tenant_id

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
        # Track the process for stop functionality
        _active_processes[run_id] = process

        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            yield _sse_event(LogEvent(
                type="log",
                message=line,
                timestamp=datetime.now(timezone.utc),
            ))

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
                    message=f"{test_name} -> {status}",
                    test_name=test_name,
                    status=status,
                    timestamp=datetime.now(timezone.utc),
                ))

        process.wait()
        duration = time.time() - start_time

    except Exception as e:
        duration = time.time() - start_time
        yield _sse_event(LogEvent(
            type="error",
            message=f"Run failed with error: {str(e)}",
            timestamp=datetime.now(timezone.utc),
        ))
    finally:
        # Clean up process tracking
        _active_processes.pop(run_id, None)

    # 7. Check if the run was stopped
    current_run = None
    from api.database import get_run
    current_run = get_run(run_id)

    if current_run and current_run.get("status") == RunStatus.STOPPED.value:
        completed_at_iso = datetime.now(timezone.utc).isoformat()
        # Send callback for stopped runs too
        _send_run_callback(
            run_id=run_id, module=request.module, sub_module=request.sub_module,
            passed=passed, failed=failed, skipped=skipped, total=total,
            duration=duration, status="stopped", results=results,
            started_at=started_at_iso, completed_at=completed_at_iso,
        )
        yield _sse_event(LogEvent(
            type="run_end",
            message=f"Run {run_id} was stopped by user after {duration:.1f}s",
            timestamp=datetime.now(timezone.utc),
        ))
        return

    # 8. Save results locally
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

    completed_at_iso = datetime.now(timezone.utc).isoformat()

    # 9. Send callback to Next.js so results are persisted server-side
    _send_run_callback(
        run_id=run_id, module=request.module, sub_module=request.sub_module,
        passed=passed, failed=failed, skipped=skipped, total=total,
        duration=duration,
        status=final_status.value,  # "completed" or "failed"
        results=results,
        started_at=started_at_iso, completed_at=completed_at_iso,
    )

    yield _sse_event(LogEvent(
        type="run_end",
        message=f"Run {run_id} finished: {passed} passed, {failed} failed, {skipped} skipped in {duration:.1f}s",
        timestamp=datetime.now(timezone.utc),
    ))


def _parse_pytest_line(line: str) -> tuple:
    """Parse a pytest -v output line for PASSED/FAILED/SKIPPED."""
    match = re.match(r".+::(.+?)\s+(PASSED|FAILED|SKIPPED|ERROR)", line)
    if match:
        return match.group(1), match.group(2).lower()
    return None


def _sse_event(event: LogEvent) -> str:
    """Convert a LogEvent to Server-Sent Event format."""
    return f"data: {event.model_dump_json()}\n\n"
