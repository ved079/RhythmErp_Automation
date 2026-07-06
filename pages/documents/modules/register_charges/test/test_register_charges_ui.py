import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)


def _unique_data():
    global _counter
    _counter += 1
    charge_id = str(_rng.randint(10000000, 99999999))
    return {
        "charge_id":        charge_id,
        "date_of_creation": "09/09/2024",
        "date_of_modification": "28/08/2025",
        "description":      f"Machinery and equipment {_counter}",
        "amount_secured":   str(_rng.randint(100000, 99999999)),
        "charge_holder":    f"HDFC Bank Branch {_counter}",
    }


class TestRegisterChargesUIGroup1:
    def test_create_smoke(self, rc_page):
        data = _unique_data()
        rc_page.create_record(data)
        rc_page.search_charge(data["charge_id"])
        rc_page.verify_charge_exists(data["charge_id"])


class TestRegisterChargesUIGroup2:
    def test_form_discard(self, rc_page):
        data = _unique_data()
        rc_page.open_add_form()
        rc_page.page.locator(rc_page.CHARGE_ID_ROC).first.click(force=True)
        rc_page.page.locator(rc_page.CHARGE_ID_ROC).first.fill(data["charge_id"])
        rc_page.close_popup()
        assert not rc_page.is_charge_in_table(data["charge_id"])

    def test_validation_sweep(self, rc_page):
        rc_page.open_add_form()
        rc_page.submit()
        rc_page.handle_validation_alert()
        rc_page.close_popup()


class TestRegisterChargesUIGroup3:
    def test_listing_and_search(self, rc_page):
        assert rc_page.get_table_row_count() > 0


class TestRegisterChargesUIGroup4:
    def test_full_row_actions(self, rc_page):
        data = _unique_data()
        rc_page.create_record(data)
        rc_page.search_charge(data["charge_id"])
        rc_page.verify_charge_exists(data["charge_id"])
        rc_page.click_view_button(data["charge_id"])
        rc_page.verify_view_popup_read_only()
        rc_page.close_popup()

        updated_desc = data["description"] + " U"
        rc_page.search_charge(data["charge_id"])
        rc_page.click_edit_button(data["charge_id"])
        rc_page.update_description(updated_desc)
        rc_page.click_update()
        rc_page.handle_success_alert()

        rc_page.search_charge(data["charge_id"])
        rc_page.click_history_button(data["charge_id"])
        assert rc_page.page.locator(".popup-footer").count() > 0
        rc_page.close_popup()
