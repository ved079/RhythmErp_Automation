"""
test_perf.py
------------
Performance tests for Miscellaneous Documents â€” optional, run manually.
"""

import pytest
import time
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pages.documents.modules.miscellaneous_documents.data.miscellaneous_documents_data import (
    generate_batch_payloads,
)


pytestmark = pytest.mark.skipif(
    not os.environ.get("ERP_TOKEN"),
    reason="ERP_TOKEN not set; skipping perf tests",
)


@pytest.mark.parametrize("batch_size", [5, 10])
class TestMiscellaneousDocumentsPerf:
    def test_batch_payload_generation_time(self, batch_size):
        start = time.time()
        payloads = generate_batch_payloads(batch_size)
        elapsed = time.time() - start
        assert len(payloads) == batch_size
        assert elapsed < 10, f"Payload generation took too long: {elapsed:.2f}s"

    def test_live_batch_create(self, api_client, batch_size):
        payloads = generate_batch_payloads(batch_size)
        start = time.time()
        created = []
        for p in payloads:
            result = api_client.create_entry_with_defaults(endpoint_slug="", payload=p)
            if result and "id" in result:
                created.append(result["id"])
        elapsed = time.time() - start
        assert len(created) == batch_size, f"Only created {len(created)}/{batch_size} entries"
        max_per_entry = 5.0
        assert elapsed < batch_size * max_per_entry, f"Batch took too long: {elapsed:.2f}s for {batch_size}"
