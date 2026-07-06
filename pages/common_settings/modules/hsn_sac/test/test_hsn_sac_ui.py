from pages.common_settings.modules.hsn_sac.data.hsn_sac_data import generate_valid_hsn_sac_data


class TestHsnSacUI:

    def test_create_smoke(self, hsn_page):
        data = generate_valid_hsn_sac_data()
        hsn_page.open_add_form()
        hsn_page.fill_form(data)
        hsn_page.submit()
        hsn_page.handle_success_alert()
        found = hsn_page.is_hsn_in_table(data["hsn_sac_number"])
        assert found, f"HSN SAC '{data['hsn_sac_number']}' not found in table after create"

    def test_validation_sweep(self, hsn_page):
        hsn_page.open_add_form()
        hsn_page.submit()
        hsn_page.handle_validation_alert()
        hsn_page.close_popup()

    def test_listing_and_search(self, hsn_page):
        assert hsn_page.get_table_row_count() > 0
        data = generate_valid_hsn_sac_data()
        hsn_page.open_add_form()
        hsn_page.fill_form(data)
        hsn_page.submit()
        hsn_page.handle_success_alert()
        hsn_page.search_hsn_sac(data["hsn_sac_number"])
        hsn_page.verify_hsn_exists(data["hsn_sac_number"])

    def test_full_row_actions(self, hsn_page):
        data = generate_valid_hsn_sac_data()
        hsn_page.open_add_form()
        hsn_page.fill_form(data)
        hsn_page.submit()
        hsn_page.handle_success_alert()
        hsn_page.search_hsn_sac(data["hsn_sac_number"])
        hsn_page.verify_hsn_exists(data["hsn_sac_number"])

        hsn_page.click_view_button(data["hsn_sac_number"])
        hsn_page.verify_view_popup_read_only()
        hsn_page.close_popup()

        hsn_page.click_edit_button(data["hsn_sac_number"])
        hsn_page.update_description("Updated description by automation")
        hsn_page.click_update()
        hsn_page.handle_success_alert()

        hsn_page.search_hsn_sac(data["hsn_sac_number"])
        hsn_page.click_history_button(data["hsn_sac_number"])
        assert hsn_page.page.locator(hsn_page.CHANGE_LOG).count() > 0
        hsn_page.close_popup()
