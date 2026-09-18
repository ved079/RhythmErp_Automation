import pytest
from pages.private_b2b.modules.Purchase_Flow_Tests.test.playwright.po_gp_grn_qc_pb.new_tests.pages.qc_page import compute_actual_values


@pytest.mark.smoke
class TestPOGPGRNQCFlow:
    def test_create_po(self, po_page, flow_state, chain_config):
        flow_state["chain_config"] = chain_config
        item = chain_config["item_name"]
        qty  = chain_config["quantity"]
        rate = chain_config["rate"]

        po_page.open_add_form()

        po_page.select_supplier("Urban Harvest Ltd")
        po_page.select_item_category("Raw material")
        po_page.select_location("Pune")
        po_page.select_department("Soyabean")
        po_page.select_division("Trading")
        po_page.select_type_of_sale("B2B")
        po_page.select_delivery_terms("Delivery")

        po_page.select_item_name(item)
        po_page.fill_quantity(str(qty))
        po_page.fill_rate(str(rate))

        po_page.select_gst_type("IGST")
        po_page.select_random_tax_rate()

        po_page.submit()

        ref_no = po_page.get_ref_no_of_first_row()
        assert ref_no, "PO ref_no should not be empty"
        flow_state["po_ref_no"] = ref_no

    def test_verify_po(self, po_page, flow_state):
        cfg    = flow_state["chain_config"]
        ref_no = flow_state["po_ref_no"]
        po_page.search(ref_no)
        po_page.open_view(ref_no)

        assert po_page.get_supplier_name() == "Urban Harvest Ltd"
        assert po_page.get_total_po_amount(), "Total PO Amount should not be empty"

        po_page.close_view()

    def test_create_gp(self, gp_page, flow_state):
        cfg  = flow_state["chain_config"]
        item = cfg["item_name"]
        qty  = cfg["quantity"]

        gp_page.open_add_form()

        gp_page.select_supplier("Urban Harvest Ltd")
        gp_page.select_purchase_order(flow_state["po_ref_no"])
        gp_page.select_item_name(item)
        gp_page.fill_no_of_bags(str(qty))
        gp_page.fill_quantity(str(qty))

        gp_page.submit()

        ref_no = gp_page.get_ref_no_of_first_row()
        assert ref_no, "GP ref_no should not be empty"
        flow_state["gp_ref_no"] = ref_no

    def test_verify_gp(self, gp_page, flow_state):
        cfg    = flow_state["chain_config"]
        ref_no = flow_state["gp_ref_no"]
        gp_page.search(ref_no)
        gp_page.open_view(ref_no)

        assert gp_page.get_quantity() == str(cfg["quantity"])
        assert gp_page.get_item_name() == cfg["item_name"]

        gp_page.close_view()

    def test_create_grn(self, grn_page, flow_state):
        cfg = flow_state["chain_config"]

        grn_page.open_add_form()

        grn_page.select_supplier("Urban Harvest Ltd")
        grn_page.select_gate_pass(flow_state["gp_ref_no"])

        grn_page.fill_received_quantity(str(cfg["quantity"]))

        grn_page.submit()

        ref_no = grn_page.get_ref_no_of_first_row()
        assert ref_no, "GRN ref_no should not be empty"
        flow_state["grn_ref_no"] = ref_no

    def test_verify_grn(self, grn_page, flow_state):
        cfg    = flow_state["chain_config"]
        ref_no = flow_state["grn_ref_no"]
        grn_page.search(ref_no)
        grn_page.open_view(ref_no)

        assert grn_page.get_grn_ref_no() == ref_no
        assert grn_page.get_gate_pass_no() == flow_state["gp_ref_no"]
        assert grn_page.get_received_quantity() == str(cfg["quantity"])

        grn_page.close_view()

    def test_create_qc(self, qc_page, flow_state):
        cfg            = flow_state["chain_config"]
        cqp_params     = cfg["cqp_params"]
        per_bag_weight = cfg["per_bag_weight"]

        actual_values = compute_actual_values(cqp_params)

        qc_page.open_add_form()

        qc_page.select_supplier("Urban Harvest Ltd")
        qc_page.select_gate_pass(flow_state["gp_ref_no"])

        # ── Bags detail ─────────────────────────────────────────────────
        # Total Weight = 1 × per_bag_weight = qty × 0.04 < qty ✓
        qc_page.open_bags_detail()
        qc_page.select_type_of_bag("test")
        qc_page.fill_no_of_bags("1")
        qc_page.fill_per_bag_weight(str(per_bag_weight))
        qc_page.done_bags()

        # ── Quality parameters ───────────────────────────────────────────
        # actual_values computed from CQP slab data via compute_actual_values()
        qc_page.open_quality_params()
        for i, actual_val in enumerate(actual_values):
            qc_page.fill_actual_value(i, str(actual_val))
        qc_page.done_quality_params()
        qc_page.close_quality_params_popup()

        qc_page.submit()

        ref_no = qc_page.get_ref_no_of_first_row()
        assert ref_no, "QC ref_no should not be empty"
        flow_state["qc_ref_no"] = ref_no

    def test_verify_qc(self, qc_page, flow_state):
        ref_no = flow_state["qc_ref_no"]
        qc_page.search(ref_no)
        qc_page.open_view(ref_no)

        assert qc_page.get_qc_deduction_pct(), "QC Deduction % should not be empty"

        qc_page.close_view()
