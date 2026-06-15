import os
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log


class TestGRNPerformance:
    @pytest.mark.performance
    @pytest.mark.api
    def test_create_completes_under_3_seconds(self, grn_api, build_payload):
        log.info("GRN-PERF-01: Create completes in under 3 seconds")
        payload = build_payload()
        start = time.time()
        data = grn_api.create_grn(payload)
        elapsed = time.time() - start
        assert data is not None, "Create failed"
        assert elapsed < 3.0, (
            f"GRN create took {elapsed:.2f}s (threshold: 3.0s)"
        )
        log.info(f"  Create completed in {elapsed:.2f}s")

    @pytest.mark.performance
    @pytest.mark.api
    def test_get_completes_under_2_seconds(self, grn_api, build_payload):
        log.info("GRN-PERF-02: GET completes in under 2 seconds")
        payload = build_payload()
        data = grn_api.create_grn(payload)
        entry_id = data["id"]

        start = time.time()
        entry = grn_api.get_grn(entry_id)
        elapsed = time.time() - start
        assert entry is not None, "GET failed"
        assert elapsed < 2.0, (
            f"GRN GET took {elapsed:.2f}s (threshold: 2.0s)"
        )
        log.info(f"  GET completed in {elapsed:.2f}s")

    @pytest.mark.performance
    @pytest.mark.api
    def test_list_completes_under_2_seconds(self, grn_api):
        log.info("GRN-PERF-03: LIST completes in under 2 seconds")
        start = time.time()
        result = grn_api.list_grns(page=1, page_size=20)
        elapsed = time.time() - start
        assert result is not None, "LIST failed"
        assert elapsed < 2.0, (
            f"GRN LIST took {elapsed:.2f}s (threshold: 2.0s)"
        )
        log.info(f"  LIST completed in {elapsed:.2f}s")

    @pytest.mark.performance
    @pytest.mark.api
    def test_create_and_verify_calculations_under_5_seconds(self, grn_api):
        log.info("GRN-PERF-04: Create + calc verification under 5 seconds")
        start = time.time()
        result = grn_api.create_and_verify_calculations()
        elapsed = time.time() - start
        assert result is not None
        assert elapsed < 5.0, (
            f"GRN create+verify took {elapsed:.2f}s (threshold: 5.0s)"
        )
        log.info(f"  Create+verify completed in {elapsed:.2f}s")
