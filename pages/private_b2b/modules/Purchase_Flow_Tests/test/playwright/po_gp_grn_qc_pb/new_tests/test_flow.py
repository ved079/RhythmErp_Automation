import pytest


@pytest.mark.smoke
class TestPOGPGRNFlow:
    def test_create_po(self, po_page, flow_state, po_rate):
        po_page.open_add_form()

        po_page.select_supplier("Urban Harvest Ltd")
        po_page.select_item_category("Raw material")
        po_page.select_location("Pune")
        po_page.select_department("Soyabean")
        po_page.select_division("Trading")
        po_page.select_type_of_sale("B2B")
        po_page.select_delivery_terms("Delivery")

        po_page.select_item_name("CONNECTOR WAGO")
        po_page.fill_quantity("15")
        po_page.fill_rate(str(po_rate))

        po_page.select_gst_type("IGST")
        po_page.select_tax_rate("5")

        po_page.submit()

        ref_no = po_page.get_ref_no_of_first_row()
        assert ref_no, "PO ref_no should not be empty"
        flow_state["po_ref_no"] = ref_no
        flow_state["po_rate"] = po_rate

    def test_verify_po(self, po_page, flow_state):
        ref_no = flow_state["po_ref_no"]
        po_page.search(ref_no)
        po_page.open_view(ref_no)

        assert po_page.get_supplier_name() == "Urban Harvest Ltd"

        rate = flow_state["po_rate"]
        qty = 15
        expected_total = str(round(rate * qty * 1.05, 2))  # qty * rate + 5% GST
        actual_total = po_page.get_total_po_amount()
        assert actual_total == expected_total, f"Total PO Amount: expected {expected_total}, got {actual_total}"

        po_page.close_view()

    def test_create_gp(self, gp_page, flow_state):
        gp_page.open_add_form()

        gp_page.select_supplier("Urban Harvest Ltd")
        gp_page.select_purchase_order(flow_state["po_ref_no"])
        gp_page.select_item_name("CONNECTOR WAGO")
        gp_page.fill_no_of_bags("10")
        gp_page.fill_quantity("15")

        gp_page.submit()

        ref_no = gp_page.get_ref_no_of_first_row()
        assert ref_no, "GP ref_no should not be empty"
        flow_state["gp_ref_no"] = ref_no

    def test_verify_gp(self, gp_page, flow_state):
        ref_no = flow_state["gp_ref_no"]
        gp_page.search(ref_no)
        gp_page.open_view(ref_no)

        assert gp_page.get_quantity() == "15"
        assert gp_page.get_item_name() == "CONNECTOR WAGO"

        gp_page.close_view()

    def test_create_grn(self, grn_page, flow_state):
        grn_page.open_add_form()

        grn_page.select_supplier("Urban Harvest Ltd")
        grn_page.select_gate_pass(flow_state["gp_ref_no"])

        grn_page.fill_received_quantity("15")

        grn_page.submit()

        ref_no = grn_page.get_ref_no_of_first_row()
        assert ref_no, "GRN ref_no should not be empty"
        flow_state["grn_ref_no"] = ref_no

    def test_verify_grn(self, grn_page, flow_state):
        ref_no = flow_state["grn_ref_no"]
        grn_page.search(ref_no)
        grn_page.open_view(ref_no)

        assert grn_page.get_grn_ref_no() == ref_no
        assert grn_page.get_gate_pass_no() == flow_state["gp_ref_no"]
        assert grn_page.get_received_quantity() == "15"

        grn_page.close_view()
