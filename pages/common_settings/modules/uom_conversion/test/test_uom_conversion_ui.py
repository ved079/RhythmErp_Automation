from pages.common_settings.modules.uom_conversion.data.uom_conversion_data import (
    generate_uom_conversion_data,
)


class TestUOMConversionUI:

    def test_create_smoke(self, uom_conv_page):
        data = generate_uom_conversion_data()
        actual_src, actual_tgt = uom_conv_page.create_record(data["conversion_factor"])
        uom_conv_page.handle_success_alert()
        uom_conv_page.verify_record_exists(actual_src, actual_tgt)

        data2 = generate_uom_conversion_data()
        actual_src2, actual_tgt2 = uom_conv_page.create_record(data2["conversion_factor"])
        uom_conv_page.handle_success_alert()
        uom_conv_page.verify_record_exists(actual_src2, actual_tgt2)

    def test_form_discard(self, uom_conv_page):
        before = uom_conv_page.get_table_row_count()
        data = generate_uom_conversion_data()
        uom_conv_page.open_add_form()
        uom_conv_page.select_source_uom(data["source_uom"])
        uom_conv_page.select_target_uom(data["target_uom"])
        uom_conv_page.fill_conversion_factor(data["conversion_factor"])
        uom_conv_page.close_popup()
        uom_conv_page.page.wait_for_timeout(500)
        after = uom_conv_page.get_table_row_count()
        assert after == before

    def test_validation_sweep(self, uom_conv_page):
        uom_conv_page.open_add_form()
        uom_conv_page.submit()
        uom_conv_page.handle_validation_alert()
        uom_conv_page.close_popup()

    def test_listing_and_search(self, uom_conv_page):
        assert uom_conv_page.get_table_row_count() > 0
        data = generate_uom_conversion_data()
        actual_src, actual_tgt = uom_conv_page.create_record(data["conversion_factor"])
        uom_conv_page.handle_success_alert()
        uom_conv_page.search_conversion(actual_src)
        uom_conv_page.verify_record_exists(actual_src, actual_tgt)

    def test_full_row_actions(self, uom_conv_page):
        data = generate_uom_conversion_data()
        actual_src, actual_tgt = uom_conv_page.create_record(data["conversion_factor"])
        uom_conv_page.handle_success_alert()
        uom_conv_page.search_conversion(actual_src)
        uom_conv_page.verify_record_exists(actual_src, actual_tgt)

        uom_conv_page.click_view_button(actual_src, actual_tgt)
        uom_conv_page.verify_view_popup_read_only()
        uom_conv_page.close_popup()

        uom_conv_page.click_edit_button(actual_src, actual_tgt)
        uom_conv_page.fill_conversion_factor("99")
        uom_conv_page.click_update()
        uom_conv_page.handle_success_alert()

        uom_conv_page.search_conversion(actual_src)
        uom_conv_page.click_history_button(actual_src, actual_tgt)
        assert uom_conv_page.page.locator(uom_conv_page.CHANGE_LOG).count() > 0
        uom_conv_page.close_popup()
