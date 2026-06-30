from pages.common_settings.modules.designation.data.designation_data import (
    generate_valid_designation_data,
)


class TestDesignationUI:

    def test_create_smoke(self, designation_page):
        data = generate_valid_designation_data()
        designation_page.open_add_form()
        designation_page.fill_form(data)
        designation_page.submit()
        designation_page.handle_success_alert()
        designation_page.search_designation(data["name"])
        designation_page.verify_designation_exists(data["name"])

        data2 = generate_valid_designation_data()
        designation_page.open_add_form()
        designation_page.page.fill(designation_page.NAME_INPUT, data2["name"])
        designation_page.submit()
        designation_page.handle_success_alert()
        designation_page.search_designation(data2["name"])
        designation_page.verify_designation_exists(data2["name"])

    def test_form_discard(self, designation_page):
        data = generate_valid_designation_data()
        designation_page.open_add_form()
        designation_page.fill_form(data)
        designation_page.close_popup()
        designation_page.search_designation(data["name"])
        assert not designation_page.is_designation_in_table(data["name"])

    def test_validation_sweep(self, designation_page):
        designation_page.open_add_form()
        designation_page.submit()
        designation_page.handle_validation_alert()
        designation_page.close_popup()

    def test_listing_and_search(self, designation_page):
        assert designation_page.get_table_row_count() > 0
        data = generate_valid_designation_data()
        designation_page.open_add_form()
        designation_page.fill_form(data)
        designation_page.submit()
        designation_page.handle_success_alert()
        designation_page.search_designation(data["name"])
        designation_page.verify_designation_exists(data["name"])

    def test_full_row_actions(self, designation_page):
        data = generate_valid_designation_data()
        designation_page.open_add_form()
        designation_page.fill_form(data)
        designation_page.submit()
        designation_page.handle_success_alert()
        designation_page.search_designation(data["name"])
        designation_page.verify_designation_exists(data["name"])

        designation_page.click_view_button(data["name"])
        designation_page.verify_view_popup_read_only()
        designation_page.close_popup()

        updated_name = data["name"] + "UPD"
        designation_page.click_edit_button(data["name"])
        designation_page.update_name(updated_name)
        designation_page.click_update()
        designation_page.handle_success_alert()

        designation_page.search_designation(updated_name)
        designation_page.click_history_button(updated_name)
        assert designation_page.page.locator(designation_page.CHANGE_LOG).count() > 0
        designation_page.close_popup()
