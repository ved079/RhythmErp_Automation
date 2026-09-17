from pages.private_b2b.modules.purchase_booking.pb_playwright_page import PBPlaywrightPage


class PBPage(PBPlaywrightPage):
    """PB page for po_gp_grn_qc_pb flow."""

    def create_pb(self, supplier_name, qc_ref_no):
        """
        Selects supplier → QC ref → submits.
        Returns ref_no of the created PB record.
        """
        self.open_add_form()
        self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
        self.page.wait_for_timeout(500)
        self._select_mat_by_partial_text(self.QC_SELECT, qc_ref_no)
        self.page.wait_for_timeout(800)

        conv = self.page.locator(self.CONVERSION_RATE)
        if conv.count() > 0:
            conv.first.click(force=True)
            conv.first.fill("1")
            conv.first.press("Tab")
            self.page.wait_for_timeout(300)

        self.page.locator(self.SUBMIT_BTN).click()
        self.page.wait_for_timeout(5000)
        self.handle_success_alert()
        self.navigate_to_page()

        return self.get_ref_no_of_first_row()
