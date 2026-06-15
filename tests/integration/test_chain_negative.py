import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log


@pytest.mark.integration
class TestChainNegative:
    def test_CHAIN_N01_missing_po_for_grn(self, api_client):
        """GRN without PO ref should fail."""
        log.info("CHAIN-N01: GRN without PO ref")
        from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import (
            build_grn_payload,
        )
        from pages.private_b2b.modules.goods_receipt_note.utils.api_goods_receipt_note_utils import (
            GRNAPIUtils,
        )
        grn_api = GRNAPIUtils(api_client)
        payload = build_grn_payload(po_ref_id_id=None, gate_pass_ref_id_id=505)
        status = grn_api.create_and_expect_failure(payload)
        log.info(f"  Status: {status}")

    def test_CHAIN_N02_missing_grn_for_qc(self, api_client):
        """QC without GRN ref should fail."""
        log.info("CHAIN-N02: QC without GRN ref")
        from pages.private_b2b.modules.quality_check.data.quality_check_data import (
            build_qc_payload,
        )
        from pages.private_b2b.modules.quality_check.utils.api_quality_check_utils import (
            QCAPIUtils,
        )
        qc_api = QCAPIUtils(api_client)
        payload = build_qc_payload(grn_ref_id_id=None, gate_pass_ref_id_id=505)
        status = qc_api.create_and_expect_failure(payload)
        log.info(f"  Status: {status}")

    def test_CHAIN_N03_supplier_mismatch(self, purchase_chain):
        """All docs in chain should use same supplier."""
        log.info("CHAIN-N03: Supplier mismatch")
        result = purchase_chain.run(supplier_ref_id=1)
        qc_data = result["qc"]["data"]
        assert qc_data.get("supplier_ref_id") == 1, \
            f"QC supplier ({qc_data.get('supplier_ref_id')}) should match chain supplier (1)"
        log.info("  Supplier consistent across chain")
