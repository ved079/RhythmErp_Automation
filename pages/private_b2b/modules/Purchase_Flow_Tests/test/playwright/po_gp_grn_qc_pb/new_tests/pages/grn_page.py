from pages.private_b2b.modules.goods_receipt_note.grn_playwright_page import GRNPlaywrightPage


class GRNPage(GRNPlaywrightPage):
    """GRN page for po_gp_grn_qc_pb flow."""

    def create_grn(self, supplier_name, gp_ref_no, po_ref_no=None):
        """
        Selects supplier → GP ref → optional PO ref → submits.
        Returns ref_no of the created GRN.
        """
        self.open_add_form()
        self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
        self.page.wait_for_timeout(500)
        self._select_mat_by_text(self.GATE_PASS_REF, gp_ref_no)
        self.page.wait_for_timeout(800)
        if po_ref_no and self.page.locator(self.PO_REF).count() > 0:
            self._select_mat_by_text(self.PO_REF, po_ref_no)
            self.page.wait_for_timeout(500)

        conv = self.page.locator(self.CONVERSION_RATE_INPUT)
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
