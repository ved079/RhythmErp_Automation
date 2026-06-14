import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import time
import pytest
from common.logger import log
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    generate_po_payloads,
)


class TestPerformance:
    @pytest.mark.performance
    def test_payload_generation_speed(self):
        start = time.time()
        count = 100
        payloads = generate_po_payloads(count)
        elapsed = time.time() - start
        rate = count / elapsed
        log.info(f"Generated {count} payloads in {elapsed:.2f}s ({rate:.0f}/s)")
        assert len(payloads) == count
        assert rate > 10, f"Generation rate too slow: {rate:.0f}/s"

    @pytest.mark.performance
    def test_single_payload_structure(self):
        payloads = generate_po_payloads(1)
        p = payloads[0]
        assert "additional_details" in p
        assert "supplier_details" in p
        assert "purchasing_order_items_details" in p

    @pytest.mark.performance
    def test_batch_payload_uniqueness(self):
        payloads = generate_po_payloads(10)
        param4_values = [p["parameter4"] for p in payloads]
        item_values = [p["purchasing_order_items_details"][0]["item_ref_id"] for p in payloads]
        assert len(set(param4_values)) > 1 or len(set(item_values)) > 1, \
            "All payloads have same FK values — randomness appears broken"


class TestLivePerformance:
    @pytest.mark.performance
    @pytest.mark.api
    def test_api_create_response_time(self, po_api):
        from pages.private_b2b.modules.purchase_order.data.purchase_order_data import build_po_payload
        payload = build_po_payload(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
        )
        start = time.time()
        result = po_api.create_po(payload)
        elapsed = time.time() - start
        assert result is not None, "PO creation failed"
        log.info(f"Create PO response time: {elapsed:.2f}s")
        assert elapsed < 10, f"Create PO too slow: {elapsed:.2f}s"

    @pytest.mark.performance
    @pytest.mark.api
    def test_list_po_response_time(self, po_api):
        start = time.time()
        listing = po_api.list_pos(page=1, page_size=25)
        elapsed = time.time() - start
        assert listing is not None, "List PO failed"
        log.info(f"List PO response time: {elapsed:.2f}s")
        assert elapsed < 10, f"List PO too slow: {elapsed:.2f}s"

    @pytest.mark.performance
    @pytest.mark.api
    def test_batch_create_ref_no_uniqueness(self, po_api):
        ids = []
        for i in range(5):
            from pages.private_b2b.modules.purchase_order.data.purchase_order_data import build_po_payload
            payload = build_po_payload(
                supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            )
            result = po_api.create_po(payload)
            assert result is not None
            eid = result.get("id") or result.get("entry_id")
            ids.append(eid)
        refs = set()
        for eid in ids:
            entry = po_api.get_po(eid)
            ref = entry.get("transaction_ref_no", "")
            refs.add(ref)
        assert len(refs) == len(ids), f"Duplicate ref nos among {ids}"
