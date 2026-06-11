"""
probe_get_none_type.py
----------------------
Create one Agent per API validation test case, then try GET on each.
Reports which records can be opened vs which crash with NoneType 500.

Run:
    cd C:\Users\vedantd\Desktop\Pacs_Automation
    python -m scripts.probe_get_none_type
"""

import os
import sys
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from pages.registration.modules.agent.utils.api_agent_utils import AgentAPIUtils
from pages.registration.modules.agent.data.agent_data import (
    generate_spaces_only,
    generate_string_255,
    generate_string_256,
    generate_special_char_name,
    generate_sql_injection,
    generate_xss_payload,
    generate_invalid_email,
    generate_invalid_phone,
    generate_invalid_ifsc,
)
from common.logger import log


def main():
    # ── Login ──────────────────────────────────────
    log.info("Logging in...")
    client = RhythmERPAPIClient()
    client.login()
    api = AgentAPIUtils(api_client=client)
    log.info("Login OK")

    # ── Define test cases ──────────────────────────
    # Each entry: (label, payload_override_func)
    test_cases = [
        (
            "AC01 - Empty submit",
            lambda: {
                "attribute_name": "Agent",
                "name": "",
                "mobile_no": "",
                "email_id": "",
            },
        ),
        (
            "AC02 - Spaces-only name",
            lambda: api.generate_unique_payload(
                agent_data={"name": generate_spaces_only()},
                name_prefix="SpacesAGT",
            ),
        ),
        (
            "AC03 - Special chars name",
            lambda: api.generate_unique_payload(
                agent_data={"name": generate_special_char_name()},
                name_prefix="SpecialAGT",
            ),
        ),
        (
            "AC04 - SQL injection",
            lambda: api.generate_unique_payload(
                agent_data={"name": generate_sql_injection()},
                name_prefix="SQLAGT",
            ),
        ),
        (
            "AC05 - XSS payload",
            lambda: api.generate_unique_payload(
                agent_data={"name": generate_xss_payload()},
                name_prefix="XSSAGT",
            ),
        ),
        (
            "AC06 - 255-char name",
            lambda: api.generate_unique_payload(
                agent_data={"name": generate_string_255()},
                name_prefix="255AGT",
            ),
        ),
        (
            "AC07 - 256-char name",
            lambda: api.generate_unique_payload(
                agent_data={"name": generate_string_256()},
                name_prefix="256AGT",
            ),
        ),
        (
            "AC08 - Invalid email",
            lambda: api.generate_unique_payload(
                agent_data={"email_id": generate_invalid_email()},
                name_prefix="InvEmailAGT",
            ),
        ),
        (
            "AC09 - Invalid phone",
            lambda: api.generate_unique_payload(
                agent_data={"mobile_no": generate_invalid_phone()},
                name_prefix="InvPhoneAGT",
            ),
        ),
        (
            "AC10 - Invalid IFSC",
            lambda: _make_invalid_ifsc_payload(api),
        ),
        (
            "VALID - Full valid data (control)",
            lambda: api.generate_unique_payload(name_prefix="ValidCtrl"),
        ),
    ]

    # ── Run each test case ─────────────────────────
    results = []

    for label, payload_func in test_cases:
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")

        payload = payload_func()

        # CREATE
        log.info(f"[PROBE] Creating: {label}")
        create_result = api.create_and_expect_failure(payload, name_prefix="PROBE")

        if create_result is None:
            # Server rejected — nothing to GET
            print(f"  CREATE: REJECTED by server (no record created)")
            print(f"  GET:    N/A — no ID to fetch")
            results.append({
                "label": label,
                "create_status": "REJECTED",
                "created_id": None,
                "get_status": "N/A",
                "get_error": None,
            })
            continue

        created_id = create_result.get("id", "unknown")
        created_name = create_result.get("name", payload.get("name", "?"))
        print(f"  CREATE: ACCEPTED — id={created_id}  name='{created_name}'")

        # GET
        time.sleep(0.5)  # small delay before fetching
        log.info(f"[PROBE] GETting id={created_id}")
        get_result = api.get_agent(created_id)
        raw = client._last_raw_response

        if get_result is not None:
            print(f"  GET:    OK (200) — record can be opened")
            results.append({
                "label": label,
                "create_status": "ACCEPTED",
                "created_id": created_id,
                "get_status": "200 OK",
                "get_error": None,
            })
        else:
            status_code = raw.status_code if raw else "?"
            error_snippet = ""
            if raw and raw.text:
                # Grab first 150 chars of error
                error_snippet = raw.text[:150].replace("\n", " ").strip()
            print(f"  GET:    FAILED ({status_code}) — {error_snippet}")
            results.append({
                "label": label,
                "create_status": "ACCEPTED",
                "created_id": created_id,
                "get_status": f"{status_code} FAIL",
                "get_error": error_snippet,
            })

        time.sleep(0.3)  # rate limit courtesy

    # ── Summary ────────────────────────────────────
    print(f"\n\n{'#'*60}")
    print(f"  PROBE RESULTS SUMMARY")
    print(f"{'#'*60}")
    print()
    print(f"  {'Test Case':<30} {'CREATE':<10} {'GET':<12} {'ID':<10}")
    print(f"  {'-'*30} {'-'*10} {'-'*12} {'-'*10}")

    opens_ok = 0
    crashes = 0

    for r in results:
        id_str = str(r["created_id"]) if r["created_id"] else "—"
        print(
            f"  {r['label']:<30} {r['create_status']:<10} "
            f"{r['get_status']:<12} {id_str:<10}"
        )
        if r["get_status"] == "200 OK":
            opens_ok += 1
        elif r["get_status"] != "N/A":
            crashes += 1

    print()
    print(f"  Records that OPEN fine:  {opens_ok}")
    print(f"  Records that CRASH 500:  {crashes}")
    print(f"  Records not created:     {len(results) - opens_ok - crashes}")

    # Show crash details
    crash_records = [r for r in results if r["get_error"]]
    if crash_records:
        print(f"\n  CRASH DETAILS:")
        for r in crash_records:
            print(f"    id={r['created_id']}  {r['label']}")
            print(f"      Error: {r['get_error'][:120]}")

    # Cleanup report
    try:
        api.tracker.generate_reports()
    except Exception:
        pass

    client.close()
    log.info("Probe complete.")


def _make_invalid_ifsc_payload(api: AgentAPIUtils) -> dict:
    """Build a payload with invalid IFSC in the Bank Details stepper."""
    payload = api.generate_unique_payload(name_prefix="InvIFSAGT")
    for child in payload.get("children", []):
        if child.get("stepper_name") == "Bank Details":
            for detail in child.get("details", []):
                detail["bank_ifsc_code"] = generate_invalid_ifsc()
    return payload


if __name__ == "__main__":
    main()
