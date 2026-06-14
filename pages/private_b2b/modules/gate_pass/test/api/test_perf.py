import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import time
import pytest

from common.logger import log
from pages.private_b2b.modules.gate_pass.data.gate_pass_data import (
    generate_gp_payload,
    generate_gp_payloads,
)


class TestPerformance:
    @pytest.mark.performance
    def test_GP_PERF01_create_response_time(self, gp_api):
        log.info("GP-PERF01: Create GP response time")
        payload = generate_gp_payload()
        start = time.time()
        data = gp_api.create_gp(payload)
        elapsed = time.time() - start
        assert data is not None, "Create should succeed"
        assert elapsed < 10.0, f"Create took {elapsed:.2f}s (expected < 10s)"
        log.info(f"Create time: {elapsed:.2f}s")

    @pytest.mark.performance
    def test_GP_PERF02_list_response_time(self, gp_api):
        log.info("GP-PERF02: List GP response time")
        start = time.time()
        result = gp_api.list_gps(page=1, page_size=5)
        elapsed = time.time() - start
        assert result is not None, "List should succeed"
        assert elapsed < 10.0, f"List took {elapsed:.2f}s (expected < 10s)"
        log.info(f"List time: {elapsed:.2f}s")

    @pytest.mark.performance
    def test_GP_PERF03_get_response_time(self, gp_api):
        log.info("GP-PERF03: Get GP response time")
        payload = generate_gp_payload()
        data = gp_api.create_gp(payload)
        entry_id = data["id"]
        start = time.time()
        fetched = gp_api.get_gp(entry_id)
        elapsed = time.time() - start
        assert fetched is not None, "Get should succeed"
        assert elapsed < 10.0, f"Get took {elapsed:.2f}s (expected < 10s)"
        log.info(f"Get time: {elapsed:.2f}s")
