import pytest


@pytest.mark.smoke
class TestPOGPFlow:
    def test_create_po(self, po_page, flow_state):
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
        po_page.fill_rate("1000")

        assert po_page.get_transaction_amount() == "15000"

        po_page.select_gst_type("IGST")
        po_page.select_tax_rate("5")

        assert po_page.get_total_amount() == "15750"

        po_page.submit()

        ref_no = po_page.get_ref_no_of_first_row()
        assert ref_no, "PO ref_no should not be empty"
        flow_state["po_ref_no"] = ref_no

    def test_verify_po(self, po_page, flow_state):
        ref_no = flow_state["po_ref_no"]
        po_page.search(ref_no)
        po_page.open_view(ref_no)

        assert po_page.get_supplier_name() == "Urban Harvest Ltd"
        assert po_page.get_total_po_amount() == "15750"

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
