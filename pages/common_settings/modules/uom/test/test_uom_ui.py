from pages.common_settings.modules.uom.data.uom_data import generate_uom_data


class TestUOMUI:
    def test_create_smoke(self, uom_page):
        data = generate_uom_data()
        uom_page.open_add_form()
        uom_page.fill_uom_form(data)
        uom_page.submit()
        uom_page.handle_success_alert()
        uom_page.search_uom(data["uom_code"])
        uom_page.verify_uom_exists(data["uom_code"])

        data2 = generate_uom_data()
        uom_page.open_add_form()
        uom_page.page.fill(uom_page.UOM_CODE, data2["uom_code"])
        uom_page.submit()
        uom_page.handle_success_alert()
        uom_page.search_uom(data2["uom_code"])
        uom_page.verify_uom_exists(data2["uom_code"])

    def test_form_discard(self, uom_page):
        data_a = generate_uom_data()
        uom_page.open_add_form()
        uom_page.fill_uom_form(data_a)
        uom_page.close_popup()
        uom_page.search_uom(data_a["uom_code"])
        assert not uom_page.is_uom_in_table(data_a["uom_code"])

    def test_validation_sweep(self, uom_page):
        uom_page.open_add_form()
        uom_page.submit()
        uom_page.handle_validation_alert()
        uom_page.close_popup()

    def test_listing_and_search(self, uom_page):
        assert uom_page.get_table_row_count() > 0
        data = generate_uom_data()
        uom_page.open_add_form()
        uom_page.fill_uom_form(data)
        uom_page.submit()
        uom_page.handle_success_alert()
        uom_page.search_uom(data["uom_code"])
        uom_page.verify_uom_exists(data["uom_code"])

    def test_full_row_actions(self, uom_page):
        data = generate_uom_data()
        uom_page.open_add_form()
        uom_page.fill_uom_form(data)
        uom_page.submit()
        uom_page.handle_success_alert()
        uom_page.search_uom(data["uom_code"])
        uom_page.verify_uom_exists(data["uom_code"])

        uom_page.click_view_button(data["uom_code"])
        assert uom_page.page.locator(uom_page.UOM_CODE).is_disabled()
        uom_page.close_popup()

        uom_page.click_edit_button(data["uom_code"])
        uom_page.update_uom_description("Updated by Playwright")
        uom_page.click_update()
        uom_page.handle_success_alert()

        uom_page.search_uom(data["uom_code"])
        uom_page.click_history_button(data["uom_code"])
        assert uom_page.page.locator(uom_page.CHANGE_LOG).count() > 0
        uom_page.close_popup()
