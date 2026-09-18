import pytest
from pages.private_b2b.modules.Purchase_Flow_Tests.test.playwright.po_gp_grn_qc_pb.new_tests.pages.qc_page import compute_actual_values


@pytest.mark.smoke
class TestPOGPGRNQCPBFlow:
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
        visible_count = qc_page.count_actual_value_inputs()
        for i, actual_val in enumerate(actual_values[:visible_count]):
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

    def test_create_pb(self, pb_page, flow_state):
        qc_ref_no = flow_state["qc_ref_no"]

        pb_page.open_add_form()
        pb_page.select_supplier("Urban Harvest Ltd")
        pb_page.select_qc(qc_ref_no)
        pb_page.select_gst_type("IGST")
        pb_page.select_gst_rate_any()

        pb_page.submit()

        ref_no = pb_page.get_ref_no_of_first_row()
        assert ref_no, "PB ref_no should not be empty"
        flow_state["pb_ref_no"] = ref_no

    def test_verify_pb(self, pb_page, flow_state):
        ref_no = flow_state["pb_ref_no"]
        pb_page.search(ref_no)
        pb_page.open_view(ref_no)

        assert pb_page.get_net_payable_amount(), "Net Payable Amount should not be empty"

        pb_page.close_view()


_MAX_RETRIES = 3


def _confirmed_new(page_obj, prev_top):
    """Return new top ref_no if it differs from prev_top, else None."""
    ref_no = page_obj.get_ref_no_of_first_row()
    if ref_no and ref_no != prev_top:
        return ref_no
    return None


@pytest.mark.smoke
class TestConnectorWagoFlow:
    """PO→GP→GRN→QC→PB with CONNECTOR WAGO — create only, no verify steps.
    Rate/qty resolved from CBR; item and actual_values are hardcoded.

    Each step records the top-of-table ref_no before creating, then verifies
    the table shows a new ref_no after save — proving the record was persisted.
    Retries up to _MAX_RETRIES times if the top hasn't changed."""

    def test_create_po(self, po_page, flow_state, wago_config):
        flow_state["wago_config"] = wago_config
        cfg = wago_config
        prev_top = po_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:PO:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            po_page.open_add_form()
            po_page.select_supplier("Urban Harvest Ltd")
            po_page.select_item_category("Raw material")
            po_page.select_location("Pune")
            po_page.select_department("Soyabean")
            po_page.select_division("Trading")
            po_page.select_type_of_sale("B2B")
            po_page.select_delivery_terms("Delivery")
            po_page.select_item_name(cfg["item_name"])
            po_page.fill_quantity(str(cfg["quantity"]))
            po_page.fill_rate(str(cfg["rate"]))
            po_page.select_gst_type("IGST")
            po_page.select_random_tax_rate()
            po_page.submit()
            ref_no = _confirmed_new(po_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:PO:{attempt}", flush=True)
        assert ref_no, f"PO not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["po_ref_no"] = ref_no
        print(f"DOC_CREATED:PO:{ref_no}", flush=True)

    def test_create_gp(self, gp_page, flow_state):
        cfg = flow_state["wago_config"]
        prev_top = gp_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:GP:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            gp_page.open_add_form()
            gp_page.select_supplier("Urban Harvest Ltd")
            gp_page.select_purchase_order(flow_state["po_ref_no"])
            gp_page.select_item_name(cfg["item_name"])
            gp_page.fill_no_of_bags(str(cfg["quantity"]))
            gp_page.fill_quantity(str(cfg["quantity"]))
            gp_page.submit()
            ref_no = _confirmed_new(gp_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:GP:{attempt}", flush=True)
        assert ref_no, f"GP not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["gp_ref_no"] = ref_no
        print(f"DOC_CREATED:GP:{ref_no}", flush=True)

    def test_create_grn(self, grn_page, flow_state):
        cfg = flow_state["wago_config"]
        prev_top = grn_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:GRN:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            grn_page.open_add_form()
            grn_page.select_supplier("Urban Harvest Ltd")
            grn_page.select_gate_pass(flow_state["gp_ref_no"])
            grn_page.fill_received_quantity(str(cfg["quantity"]))
            grn_page.submit()
            ref_no = _confirmed_new(grn_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:GRN:{attempt}", flush=True)
        assert ref_no, f"GRN not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["grn_ref_no"] = ref_no
        print(f"DOC_CREATED:GRN:{ref_no}", flush=True)

    def test_create_qc(self, qc_page, flow_state):
        cfg = flow_state["wago_config"]
        prev_top = qc_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:QC:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            qc_page.open_add_form()
            qc_page.select_supplier("Urban Harvest Ltd")
            qc_page.select_gate_pass(flow_state["gp_ref_no"])
            qc_page.open_bags_detail()
            qc_page.select_type_of_bag("test")
            qc_page.fill_no_of_bags("1")
            qc_page.fill_per_bag_weight(str(cfg["per_bag_weight"]))
            qc_page.done_bags()
            qc_page.open_quality_params()
            visible_count = qc_page.count_actual_value_inputs()
            vals = cfg["actual_values"]
            padded = (vals + [vals[-1]] * (visible_count - len(vals)))[:visible_count]
            for i, val in enumerate(padded):
                qc_page.fill_actual_value(i, str(val))
            qc_page.done_quality_params()
            qc_page.close_quality_params_popup()
            qc_page.submit()
            ref_no = _confirmed_new(qc_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:QC:{attempt}", flush=True)
        assert ref_no, f"QC not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["qc_ref_no"] = ref_no
        print(f"DOC_CREATED:QC:{ref_no}", flush=True)

    def test_create_pb(self, pb_page, flow_state):
        prev_top = pb_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:PB:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            pb_page.open_add_form()
            pb_page.select_supplier("Urban Harvest Ltd")
            pb_page.select_qc(flow_state["qc_ref_no"])
            pb_page.select_gst_type("IGST")
            pb_page.select_gst_rate_any()
            pb_page.submit()
            ref_no = _confirmed_new(pb_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:PB:{attempt}", flush=True)
        assert ref_no, f"PB not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["pb_ref_no"] = ref_no
        print(f"DOC_CREATED:PB:{ref_no}", flush=True)


@pytest.mark.smoke
class TestConnectorWagoBatchFlow:
    """Batch mode: create all N POs first, then all N GPs, then GRNs, QCs, PBs.

    Configs are pre-generated by the FastAPI backend and passed via WAGO_CONFIGS
    env var — 1 CBR API call for chain 1, rest randomized locally from the rate band.
    Each test method loops over all N chains for that document type.
    """

    def test_batch_po(self, po_page, flow_state, wago_configs):
        flow_state["wago_configs"] = wago_configs
        flow_state["po_refs"] = []
        for i, cfg in enumerate(wago_configs):
            prev_top = po_page.get_ref_no_of_first_row()
            print(f"PRE_TOP:PO:{prev_top}", flush=True)
            ref_no = None
            for attempt in range(1, _MAX_RETRIES + 1):
                po_page.open_add_form()
                po_page.select_supplier("Urban Harvest Ltd")
                po_page.select_item_category("Raw material")
                po_page.select_location("Pune")
                po_page.select_department("Soyabean")
                po_page.select_division("Trading")
                po_page.select_type_of_sale("B2B")
                po_page.select_delivery_terms("Delivery")
                po_page.select_item_name(cfg["item_name"])
                po_page.fill_quantity(str(cfg["quantity"]))
                po_page.fill_rate(str(cfg["rate"]))
                po_page.select_gst_type("IGST")
                po_page.select_random_tax_rate()
                po_page.submit()
                ref_no = _confirmed_new(po_page, prev_top)
                if ref_no:
                    break
                print(f"RETRY:PO:{attempt}", flush=True)
            assert ref_no, f"PO[{i+1}] not confirmed after {_MAX_RETRIES} attempts"
            flow_state["po_refs"].append(ref_no)
            print(f"DOC_CREATED:PO:{ref_no}", flush=True)

    def test_batch_gp(self, gp_page, flow_state):
        flow_state["gp_refs"] = []
        for i, cfg in enumerate(flow_state["wago_configs"]):
            prev_top = gp_page.get_ref_no_of_first_row()
            print(f"PRE_TOP:GP:{prev_top}", flush=True)
            ref_no = None
            for attempt in range(1, _MAX_RETRIES + 1):
                gp_page.open_add_form()
                gp_page.select_supplier("Urban Harvest Ltd")
                gp_page.select_purchase_order(flow_state["po_refs"][i])
                gp_page.select_item_name(cfg["item_name"])
                gp_page.fill_no_of_bags(str(cfg["quantity"]))
                gp_page.fill_quantity(str(cfg["quantity"]))
                gp_page.submit()
                ref_no = _confirmed_new(gp_page, prev_top)
                if ref_no:
                    break
                print(f"RETRY:GP:{attempt}", flush=True)
            assert ref_no, f"GP[{i+1}] not confirmed after {_MAX_RETRIES} attempts"
            flow_state["gp_refs"].append(ref_no)
            print(f"DOC_CREATED:GP:{ref_no}", flush=True)

    def test_batch_grn(self, grn_page, flow_state):
        flow_state["grn_refs"] = []
        for i, cfg in enumerate(flow_state["wago_configs"]):
            prev_top = grn_page.get_ref_no_of_first_row()
            print(f"PRE_TOP:GRN:{prev_top}", flush=True)
            ref_no = None
            for attempt in range(1, _MAX_RETRIES + 1):
                grn_page.open_add_form()
                grn_page.select_supplier("Urban Harvest Ltd")
                grn_page.select_gate_pass(flow_state["gp_refs"][i])
                grn_page.fill_received_quantity(str(cfg["quantity"]))
                grn_page.submit()
                ref_no = _confirmed_new(grn_page, prev_top)
                if ref_no:
                    break
                print(f"RETRY:GRN:{attempt}", flush=True)
            assert ref_no, f"GRN[{i+1}] not confirmed after {_MAX_RETRIES} attempts"
            flow_state["grn_refs"].append(ref_no)
            print(f"DOC_CREATED:GRN:{ref_no}", flush=True)

    def test_batch_qc(self, qc_page, flow_state):
        flow_state["qc_refs"] = []
        for i, cfg in enumerate(flow_state["wago_configs"]):
            prev_top = qc_page.get_ref_no_of_first_row()
            print(f"PRE_TOP:QC:{prev_top}", flush=True)
            ref_no = None
            for attempt in range(1, _MAX_RETRIES + 1):
                qc_page.open_add_form()
                qc_page.select_supplier("Urban Harvest Ltd")
                qc_page.select_gate_pass(flow_state["gp_refs"][i])
                qc_page.open_bags_detail()
                qc_page.select_type_of_bag("test")
                qc_page.fill_no_of_bags("1")
                qc_page.fill_per_bag_weight(str(cfg["per_bag_weight"]))
                qc_page.done_bags()
                qc_page.open_quality_params()
                visible_count = qc_page.count_actual_value_inputs()
                vals = cfg["actual_values"]
                padded = (vals + [vals[-1]] * (visible_count - len(vals)))[:visible_count]
                for j, val in enumerate(padded):
                    qc_page.fill_actual_value(j, str(val))
                qc_page.done_quality_params()
                qc_page.close_quality_params_popup()
                qc_page.submit()
                ref_no = _confirmed_new(qc_page, prev_top)
                if ref_no:
                    break
                print(f"RETRY:QC:{attempt}", flush=True)
            assert ref_no, f"QC[{i+1}] not confirmed after {_MAX_RETRIES} attempts"
            flow_state["qc_refs"].append(ref_no)
            print(f"DOC_CREATED:QC:{ref_no}", flush=True)

    def test_batch_pb(self, pb_page, flow_state):
        for i in range(len(flow_state["wago_configs"])):
            prev_top = pb_page.get_ref_no_of_first_row()
            print(f"PRE_TOP:PB:{prev_top}", flush=True)
            ref_no = None
            for attempt in range(1, _MAX_RETRIES + 1):
                pb_page.open_add_form()
                pb_page.select_supplier("Urban Harvest Ltd")
                pb_page.select_qc(flow_state["qc_refs"][i])
                pb_page.select_gst_type("IGST")
                pb_page.select_gst_rate_any()
                pb_page.submit()
                ref_no = _confirmed_new(pb_page, prev_top)
                if ref_no:
                    break
                print(f"RETRY:PB:{attempt}", flush=True)
            assert ref_no, f"PB[{i+1}] not confirmed after {_MAX_RETRIES} attempts"
            print(f"DOC_CREATED:PB:{ref_no}", flush=True)
