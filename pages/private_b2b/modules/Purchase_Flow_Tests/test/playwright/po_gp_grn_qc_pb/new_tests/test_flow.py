import pytest


@pytest.mark.smoke
class TestCreatePO:
    def test_create_and_verify(self, po_page):
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
        po_page.click_save()

        po_page.fill_rate("3000")
        po_page.select_gst_type("IGST")
        po_page.select_tax_rate("5")

        po_page.submit()

        ref_no = po_page.get_ref_no_of_first_row()
        assert ref_no, "PO ref_no should not be empty after submit"

        po_page.search(ref_no)
        po_page.open_view(ref_no)

        assert po_page.get_total_po_amount() == "47250"
        assert po_page.get_item_name() == "CONNECTOR WAGO"
        assert po_page.get_transaction_currency() == "INR"

        po_page.close_view()
