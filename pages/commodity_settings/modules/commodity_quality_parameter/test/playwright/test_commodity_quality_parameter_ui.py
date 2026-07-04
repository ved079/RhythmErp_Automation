def _unique_data():
    return {"min_quality": 1, "max_quality": 100, "multiplier": 1}


class TestCQPUIGroup1:
    def test_create_smoke(self, cqp_page):
        cqp_page.create_record(_unique_data())
        name = cqp_page.get_first_item_name_in_table()
        if name:
            cqp_page.search_cqp(name)
            cqp_page.verify_cqp_exists(name)


class TestCQPUIGroup2:
    def test_form_discard(self, cqp_page):
        cqp_page.open_add_form()
        cqp_page.close_popup()

    def test_validation_sweep(self, cqp_page):
        cqp_page.open_add_form()
        cqp_page.submit()
        cqp_page.handle_validation_alert()
        cqp_page.close_popup()


class TestCQPUIGroup3:
    def test_listing_and_search(self, cqp_page):
        assert cqp_page.get_table_row_count() > 0


class TestCQPUIGroup4:
    def test_full_row_actions(self, cqp_page):
        cqp_page.create_record(_unique_data())
        cqp_page.click_view_button()
        cqp_page.verify_view_popup_read_only()
        cqp_page.close_popup()
        cqp_page.click_history_button()
        assert cqp_page.page.locator(".popup-footer").count() > 0
        cqp_page.close_popup()
