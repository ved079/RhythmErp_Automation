import time
from pages.common_settings.modules.vehicle_master.data.vehicle_master_data import (
    generate_valid_vehicle_data,
)


# ERP rejects digits/special chars in name — encode timestamp as base-26 letters A-Z
_ts = int(time.time())


def _encode_ts(ts):
    result = ""
    while ts > 0:
        result = chr(ord('A') + (ts % 26)) + result
        ts //= 26
    return result


_ts_letters = _encode_ts(_ts)


def _unique_name(name):
    return f"{name} {_ts_letters}"


class TestVehicleMasterUI:

    def test_create_smoke(self, vm_page):
        data = generate_valid_vehicle_data()
        data["name"] = _unique_name(data["name"])
        vm_page.open_add_form()
        vm_page.fill_form(data)
        vm_page.submit()
        vm_page.handle_success_alert()
        vm_page.search_vehicle(data["name"])
        vm_page.verify_vehicle_exists(data["name"])

        data2 = generate_valid_vehicle_data()
        data2["name"] = _unique_name(data2["name"] + "B")
        vm_page.open_add_form()
        vm_page.fill_form(data2)
        vm_page.submit()
        vm_page.handle_success_alert()
        vm_page.search_vehicle(data2["name"])
        vm_page.verify_vehicle_exists(data2["name"])

    def test_form_discard(self, vm_page):
        data = generate_valid_vehicle_data()
        data["name"] = _unique_name(data["name"])
        vm_page.open_add_form()
        vm_page.page.fill(vm_page.NAME_INPUT, data["name"])
        vm_page.close_popup()
        vm_page.search_vehicle(data["name"])
        assert not vm_page.is_vehicle_in_table(data["name"])

    def test_validation_sweep(self, vm_page):
        vm_page.open_add_form()
        vm_page.submit()
        vm_page.handle_validation_alert()
        vm_page.close_popup()

    def test_listing_and_search(self, vm_page):
        assert vm_page.get_table_row_count() > 0
        data = generate_valid_vehicle_data()
        data["name"] = _unique_name(data["name"])
        vm_page.open_add_form()
        vm_page.fill_form(data)
        vm_page.submit()
        vm_page.handle_success_alert()
        vm_page.search_vehicle(data["name"])
        vm_page.verify_vehicle_exists(data["name"])

    def test_duplicate_name_rejected(self, vm_page):
        existing_name = vm_page.page.locator("td.cdk-column-name").first.inner_text().strip()
        data = generate_valid_vehicle_data()
        data["name"] = existing_name
        vm_page.open_add_form()
        vm_page.fill_form(data)
        vm_page.submit()
        vm_page.page.wait_for_selector(".swal2-container", timeout=5000)
        title = (vm_page.page.locator("#swal2-title").text_content() or "").strip().lower()
        assert any(w in title for w in ("validation", "already", "exists", "duplicate", "error")), \
            f"Expected duplicate rejection alert, got: '{title}'"
        vm_page.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        vm_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        vm_page.close_popup()

    def test_search_nonexistent(self, vm_page):
        vm_page.search_vehicle("searchNonexitingName")
        assert not vm_page.is_vehicle_in_table("searchNonexitingName")

    def test_full_row_actions(self, vm_page):
        data = generate_valid_vehicle_data()
        data["name"] = _unique_name(data["name"])
        vm_page.open_add_form()
        vm_page.fill_form(data)
        vm_page.submit()
        vm_page.handle_success_alert()
        vm_page.search_vehicle(data["name"])
        vm_page.verify_vehicle_exists(data["name"])

        vm_page.click_view_button(data["name"])
        vm_page.verify_view_popup_read_only()
        vm_page.close_popup()

        updated_name = _unique_name(data["name"] + "U")
        vm_page.click_edit_button(data["name"])
        vm_page.update_name(updated_name)
        vm_page.click_update()
        vm_page.handle_success_alert()

        vm_page.search_vehicle(updated_name)
        vm_page.click_history_button(updated_name)
        assert vm_page.page.locator(vm_page.CHANGE_LOG).count() > 0
        vm_page.close_popup()
