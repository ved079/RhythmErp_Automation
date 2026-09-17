from pages.private_b2b.modules.gate_pass.gp_playwright_page import GPPlaywrightPage


class GPPage(GPPlaywrightPage):
    """GP page for po_gp_grn_qc_pb flow — Raw Materia item category with PO linkage."""

    ITEM_TYPE      = "xpath=//mat-form-field[.//mat-label[contains(.,'Item category')]]//mat-select"
    PURCHASE_ORDER = "xpath=//mat-form-field[.//mat-label[contains(.,'Purchase Order')]]//mat-select"

    def fill_header_with_supplier(self, supplier_name, location=None, type_of_sale=None, po_ref_no=None):
        self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
        self.page.wait_for_timeout(500)
        if po_ref_no:
            self._select_mat_by_text(self.PURCHASE_ORDER, po_ref_no)
        self._select_mat_by_text(self.ITEM_TYPE, "Raw Materia")
        self._select_mat_by_text(self.DELIVERY_TERMS, "Spot")
        self.fill_in_time(10, 0)
        if location:
            self._select_mat_by_text(self.LOCATION, location)
        else:
            self._select_random_mat_option(self.LOCATION)
        self._select_random_mat_option(self.DEPARTMENT)
        self._select_random_mat_option(self.DIVISION)
        if type_of_sale:
            self._select_mat_by_text(self.TYPE_OF_SALE, type_of_sale)
        else:
            self._select_random_mat_option(self.TYPE_OF_SALE)
        self._fill_text_field(self.DISTANCE, "1")
        self._fill_text_field(self.VEHICLE_NUMBER, "MH14KK2354")
        self._fill_text_field(self.DRIVER_NAME, "TestDriver")
        self._fill_number_nth(self.DRIVER_NUMBER, 0, 9999988888)

    def create_gp(self, supplier_name, items, location=None, type_of_sale="B2B", po_ref_no=None):
        """
        items: list of (item_name, bags, qty) tuples.
        Returns ref_no.
        """
        self.open_add_form()
        self.fill_header_with_supplier(supplier_name, location=location, type_of_sale=type_of_sale, po_ref_no=po_ref_no)

        row0_item = items[0][0] if items else None
        for i, (item_name, bags, qty) in enumerate(items):
            if i > 0:
                self.page.locator(self.ADD_ROW_BTN).click()
                self.page.wait_for_timeout(1000)
            self._select_item_by_name_nth(i, item_name)
            self.page.wait_for_timeout(800)
            if i > 0 and row0_item and row0_item != item_name:
                hsn_text = self.page.locator(self.HSN_SAC_NO).nth(i).inner_text().strip()
                if not hsn_text:
                    self._select_item_by_name_nth(i, row0_item)
                    self.page.wait_for_timeout(600)
                    self._select_item_by_name_nth(i, item_name)
                    self.page.wait_for_timeout(600)
            self._fill_number_nth(self.NO_OF_BAGS, i, bags)
            self._fill_number_nth(self.QUANTITY, i, qty)
            self.page.wait_for_timeout(400)

        ref_no, _ = self.submit_items_form(items)
        return ref_no
