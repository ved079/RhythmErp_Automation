import time
from pages.common_settings.modules.tax_rate.tax_rate_page import TaxRatePage

_ts = int(time.time())
_counter = 0


def _unique_name():
    global _counter
    _counter += 1
    return f"TaxRate {_ts} {_counter:04d}"


def _valid_data():
    return {
        "tax_rate_name": _unique_name(),
        "from_date": "01/04/2024",
    }


class TestTaxRateUIGroup1:

    def test_create_smoke(self, tr_page):
        data = _valid_data()
        tr_page.create_record(data)
        tr_page.search_tax_rate(data["tax_rate_name"])
        tr_page.verify_tax_rate_exists(data["tax_rate_name"])


class TestTaxRateUIGroup2:

    def test_form_discard(self, tr_page):
        data = _valid_data()
        tr_page.open_add_form()
        tr_page.page.fill(tr_page.NAME_INPUT, data["tax_rate_name"])
        tr_page.close_popup()
        tr_page.search_tax_rate(data["tax_rate_name"])
        assert not tr_page.is_tax_rate_in_table(data["tax_rate_name"])

    def test_validation_sweep(self, tr_page):
        tr_page.open_add_form()
        tr_page.submit()
        tr_page.handle_validation_alert()
        tr_page.close_popup()


class TestTaxRateUIGroup3:

    def test_listing_and_search(self, tr_page):
        assert tr_page.get_table_row_count() > 0
        data = _valid_data()
        tr_page.create_record(data)
        tr_page.search_tax_rate(data["tax_rate_name"])
        tr_page.verify_tax_rate_exists(data["tax_rate_name"])


class TestTaxRateUIGroup4:

    def test_full_row_actions(self, tr_page):
        data = _valid_data()
        tr_page.create_record(data)
        tr_page.search_tax_rate(data["tax_rate_name"])
        tr_page.verify_tax_rate_exists(data["tax_rate_name"])

        tr_page.click_view_button(data["tax_rate_name"])
        tr_page.verify_view_popup_read_only()
        tr_page.close_popup()

        tr_page.search_tax_rate(data["tax_rate_name"])
        tr_page.click_history_button(data["tax_rate_name"])
        assert tr_page.page.locator(".popup-footer").count() > 0
        tr_page.close_popup()
