"""Batch create Gate Pass entries via dedicated API endpoint."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")))

from common.logger import log
from pages.private_b2b.modules.gate_pass.data.gate_pass_data import (
    generate_gp_payloads,
)
from pages.private_b2b.modules.gate_pass.utils.api_gate_pass_utils import (
    GPAPIUtils,
)


def main():
    log.info("=== Batch Creating Gate Pass Entries ===")
    utils = GPAPIUtils()
    utils.client.login()

    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    payloads = generate_gp_payloads(count, fk_overrides={
        "supplier_ref_id": 1, "item_type_ref_id": 113,
        "parameter1": 1,
    })

    successes = 0
    for i, payload in enumerate(payloads, 1):
        result = utils.create_gp(payload)
        if result:
            successes += 1
            entry_id = result.get("id")
            ref_no = result.get("transaction_ref_no", "N/A")
            log.info(f"  [{i}/{count}] Created GP #{entry_id} (ref: {ref_no})")
        else:
            log.warning(f"  [{i}/{count}] Failed (status {utils._last_status})")
            if utils._last_response is not None:
                log.warning(f"  Body: {utils._last_response.text[:300]}")

    log.info(f"Done: {successes}/{count} created")


if __name__ == "__main__":
    main()
