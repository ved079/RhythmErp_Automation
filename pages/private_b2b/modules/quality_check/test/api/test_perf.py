import os
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.private_b2b.modules.quality_check.data.quality_check_data import (
    build_qc_payload,
)


PERF_THRESHOLD = 5.0


@pytest.mark.api
@pytest.mark.performance
class TestQCPerformance:
    def test_QC_PERF01_create_response_time(self, qc_api):
        log.info("QC-PERF01: Create response time")
        payload = build_qc_payload()
        start = time.time()
        data = qc_api.create_qc(payload)
        elapsed = time.time() - start
        assert data is not None, "Create should succeed"
        assert elapsed < PERF_THRESHOLD, f"Create took {elapsed:.2f}s (threshold {PERF_THRESHOLD}s)"
        log.info(f"  Create: {elapsed:.2f}s")

    def test_QC_PERF02_get_response_time(self, qc_api):
        log.info("QC-PERF02: GET response time")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None
        entry_id = data["id"]
        start = time.time()
        fetched = qc_api.get_qc(entry_id)
        elapsed = time.time() - start
        assert fetched is not None, "GET should succeed"
        assert elapsed < PERF_THRESHOLD, f"GET took {elapsed:.2f}s"
        log.info(f"  GET: {elapsed:.2f}s")

    def test_QC_PERF03_list_response_time(self, qc_api):
        log.info("QC-PERF03: LIST response time")
        start = time.time()
        listing = qc_api.list_qcs()
        elapsed = time.time() - start
        assert listing is not None, "LIST should succeed"
        assert elapsed < PERF_THRESHOLD, f"LIST took {elapsed:.2f}s"
        log.info(f"  LIST: {elapsed:.2f}s")

    @pytest.mark.xfail(reason="QC PUT endpoint has server-side IntegrityError", strict=False)
    def test_QC_PERF04_update_response_time(self, qc_api):
        log.info("QC-PERF04: Update response time")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None
        entry_id = data["id"]
        updated = build_qc_payload()
        start = time.time()
        result = qc_api.update_qc(entry_id, updated)
        elapsed = time.time() - start
        assert result is not None, "Update should succeed"
        assert elapsed < PERF_THRESHOLD, f"Update took {elapsed:.2f}s"
        log.info(f"  Update: {elapsed:.2f}s")
