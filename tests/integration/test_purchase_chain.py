import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log


@pytest.mark.integration
@pytest.mark.chain
class TestPurchaseChain:
    @pytest.mark.smoke
    def test_CHAIN01_full_po_gp_grn_qc_chain(self, purchase_chain):
        """Create a full PO -> GP -> GRN -> QC chain, verify all 4 exist and are linked."""
        log.info("CHAIN-01: Full PO->GP->GRN->QC chain")
        result = purchase_chain.run(supplier_ref_id=1)

        po = result["po"]
        gp = result["gp"]
        grn = result["grn"]
        qc = result["qc"]

        assert po["id"] is not None, "PO should have an ID"
        assert gp["id"] is not None, "GP should have an ID"
        assert grn["id"] is not None, "GRN should have an ID"
        assert qc["id"] is not None, "QC should have an ID"

        log.info(f"  PO #{po['id']} -> GP #{gp['id']} -> GRN #{grn['id']} -> QC #{qc['id']}")

        grn_data = grn["data"]
        assert grn_data.get("po_ref_id_id") == po["id"], \
            f"GRN.po_ref_id_id ({grn_data.get('po_ref_id_id')}) should match PO ID ({po['id']})"
        assert grn_data.get("gate_pass_ref_id_id") == gp["id"], \
            f"GRN.gate_pass_ref_id_id should match GP ID"

        qc_data = qc["data"]
        assert qc_data.get("grn_ref_id_id") == grn["id"], \
            f"QC.grn_ref_id_id ({qc_data.get('grn_ref_id_id')}) should match GRN ID ({grn['id']})"
        assert qc_data.get("gate_pass_ref_id_id") == gp["id"], \
            f"QC.gate_pass_ref_id_id should match GP ID"

        log.info("  All FK links verified: PO -> GP -> GRN -> QC")

    def test_CHAIN02_chain_data_consistency(self, purchase_chain):
        """Verify data consistency across the chain."""
        log.info("CHAIN-02: Data consistency across the chain")
        result = purchase_chain.run(supplier_ref_id=1, num_items=2)

        po = result["po"]
        gp = result["gp"]
        grn = result["grn"]
        qc = result["qc"]

        po_data = po["data"]
        gp_data = gp["data"]
        grn_data = grn["data"]
        qc_data = qc["data"]

        assert po_data.get("supplier_ref_id") == 1, "PO supplier should match"
        assert gp_data.get("supplier_ref_id") == 1, "GP supplier should match"
        assert grn_data.get("supplier_ref_id") == 1, "GRN supplier should match"
        assert qc_data.get("supplier_ref_id") == 1, "QC supplier should match"
        log.info("  Supplier consistent across chain")

        po_items = po_data.get("purchasing_order_items_details", [])
        gp_items = gp_data.get("gate_pass_details", [])
        grn_items = grn_data.get("grn_item_details", [])
        qc_items = qc_data.get("qc_details", [])

        assert len(po_items) == len(gp_items) == len(grn_items) == len(qc_items), (
            f"Item count mismatch: PO={len(po_items)}, GP={len(gp_items)}, "
            f"GRN={len(grn_items)}, QC={len(qc_items)}"
        )
        log.info(f"  Item count consistent: {len(po_items)} item(s)")

        for i in range(len(po_items)):
            pi = po_items[i]
            gi = gp_items[i]
            gri = grn_items[i]
            qi = qc_items[i]
            assert pi["item_ref_id"] == gi["item_ref_id"] == gri["item_ref_id"] == qi["item_ref_id"], \
                f"Item[{i}] item_ref_id mismatch"
        log.info("  item_ref_id consistent across chain")

    def test_CHAIN03_chain_missing_gp(self, api_client):
        """Attempt chain with invalid GP reference should fail gracefully."""
        log.info("CHAIN-03: Broken chain — invalid GP reference")
        from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import (
            build_grn_payload,
        )
        from pages.private_b2b.modules.goods_receipt_note.utils.api_goods_receipt_note_utils import (
            GRNAPIUtils,
        )

        grn_api = GRNAPIUtils(api_client)
        payload = build_grn_payload(gate_pass_ref_id_id=9999999, po_ref_id_id=9999999)
        status = grn_api.create_and_expect_failure(payload)
        assert status != 200, "GRN with invalid GP+PO should fail"
        log.info(f"  Invalid references correctly rejected (status {status})")
