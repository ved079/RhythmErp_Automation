r"""
debug_xpass.py
--------------
Debug the 4 XPASS tests to see what the server actually returns.
Tests AC03, AC05, AD01, AE01 one at a time with full response logging.

Run:
    python -m scripts.debug_xpass
"""

import os
import sys
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from pages.registration.modules.agent.utils.api_agent_utils import AgentAPIUtils
from pages.registration.modules.agent.data.agent_data import (
    generate_special_char_name,
    generate_xss_payload,
    generate_invalid_email,
)


def main():
    log_info = print

    log_info("Logging in...")
    client = RhythmERPAPIClient()
    client.login()
    api = AgentAPIUtils(api_client=client)
    log_info("Login OK\n")

    # ── AC03: Special chars name ──────────────────
    log_info("=" * 60)
    log_info("  AC03 - Special chars name")
    log_info("=" * 60)
    payload = api.generate_unique_payload(
        agent_data={"name": generate_special_char_name()},
        name_prefix="SpecialAGT",
    )
    result = client.create_entry(payload)
    raw = client._last_raw_response
    log_info(f"  Status: {raw.status_code if raw else 'NO RESPONSE'}")
    log_info(f"  Result: {result}")
    if raw and raw.text:
        log_info(f"  Body:   {raw.text[:300]}")
    log_info("")

    time.sleep(0.5)

    # ── AC05: XSS payload ─────────────────────────
    log_info("=" * 60)
    log_info("  AC05 - XSS payload")
    log_info("=" * 60)
    payload = api.generate_unique_payload(
        agent_data={"name": generate_xss_payload()},
        name_prefix="XSSAGT",
    )
    result = client.create_entry(payload)
    raw = client._last_raw_response
    log_info(f"  Status: {raw.status_code if raw else 'NO RESPONSE'}")
    log_info(f"  Result: {result}")
    if raw and raw.text:
        log_info(f"  Body:   {raw.text[:300]}")
    log_info("")

    time.sleep(0.5)

    # ── AD01: Duplicate name ──────────────────────
    log_info("=" * 60)
    log_info("  AD01 - Duplicate name")
    log_info("=" * 60)
    result1 = api.create_agent(name_prefix="DupAGT")
    name1 = result1.get("name", "") if result1 else "FAILED"
    log_info(f"  First create:  id={result1.get('id') if result1 else 'N/A'}  name='{name1}'")

    payload2 = api.generate_unique_payload(
        agent_data={"name": name1},
        name_prefix="DupAGT2",
    )
    result2 = client.create_entry(payload2)
    raw2 = client._last_raw_response
    log_info(f"  Second create: status={raw2.status_code if raw2 else 'NO RESPONSE'}")
    log_info(f"  Result: {result2}")
    if raw2 and raw2.text:
        log_info(f"  Body:   {raw2.text[:300]}")
    log_info("")

    time.sleep(0.5)

    # ── AE01: Edit with invalid email ─────────────
    log_info("=" * 60)
    log_info("  AE01 - Edit with invalid email")
    log_info("=" * 60)
    created = api.create_agent(name_prefix="EditInvEmail")
    if created:
        agent_id = created.get("id")
        log_info(f"  Created agent id={agent_id}")

        detail = api.get_agent(agent_id)
        if detail:
            log_info(f"  GET OK, current email: {detail.get('email_id')}")
            detail["email_id"] = generate_invalid_email()
            log_info(f"  Setting email to: {detail['email_id']}")

            update_result = client.create_entry(detail)  # Update uses same POST
            raw3 = client._last_raw_response
            log_info(f"  Update status: {raw3.status_code if raw3 else 'NO RESPONSE'}")
            log_info(f"  Update result: {update_result}")
            if raw3 and raw3.text:
                log_info(f"  Body:   {raw3.text[:300]}")
        else:
            log_info("  GET FAILED — can't test edit")
    else:
        log_info("  CREATE FAILED — can't test edit")

    client.close()
    log_info("\nDebug complete.")


if __name__ == "__main__":
    main()
