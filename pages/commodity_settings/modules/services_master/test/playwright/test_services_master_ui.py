import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)

_SM_MAIN = [
    # Transport & logistics
    "Road Transport", "Rail Transport", "Air Freight", "Sea Freight",
    "Cold Chain Transport", "Bulk Cargo Transport", "Container Transport",
    "Last Mile Delivery", "Intrastate Transport", "Interstate Transport",
    "Courier Service", "Warehousing", "Cold Storage", "Fumigation Service",
    # Agri services
    "Crop Insurance", "Soil Testing", "Seed Treatment", "Spraying Service",
    "Harvesting Service", "Threshing Service", "Grading Service", "Sorting Service",
    "Milling Service", "Cleaning Service", "Drying Service", "Packing Service",
    # Financial services
    "Loan Processing", "Interest Collection", "Insurance Premium",
    "Commission Charges", "Handling Charges", "Storage Charges",
    # Inspection & certification
    "Quality Inspection", "Weighment Service", "Sampling Service",
    "Certification Service", "Audit Service", "Assaying Service",
]

_SM_QUALIFIER = [
    "Kharif", "Rabi", "Annual", "Seasonal", "Regular",
    "Premium", "Standard", "Bulk", "Express", "Local",
    "Interstate", "Domestic", "Export", "Certified", "Contracted",
]


def _unique_data():
    global _counter
    _counter += 1
    main      = _rng.choice(_SM_MAIN)
    qualifier = _rng.choice(_SM_QUALIFIER)
    name      = f"{main} {qualifier} {_counter}"
    return {
        "name":                name,
        "base_uom_conversion": 1,
    }


class TestSMUIGroup1:
    def test_create_smoke(self, sm_page):
        data = _unique_data()
        sm_page.create_record(data)
        sm_page.search_service(data["name"])
        sm_page.verify_service_exists(data["name"])


class TestSMUIGroup2:
    def test_form_discard(self, sm_page):
        data = _unique_data()
        sm_page.open_add_form()
        sm_page.page.locator(sm_page.NAME).first.click(force=True)
        sm_page.page.locator(sm_page.NAME).first.fill(data["name"])
        sm_page.close_popup()
        assert not sm_page.is_service_in_table(data["name"])

    def test_validation_sweep(self, sm_page):
        sm_page.open_add_form()
        sm_page.submit()
        sm_page.handle_validation_alert()
        sm_page.close_popup()


class TestSMUIGroup3:
    def test_listing_and_search(self, sm_page):
        assert sm_page.get_table_row_count() > 0


class TestSMUIGroup4:
    def test_full_row_actions(self, sm_page):
        data = _unique_data()
        sm_page.create_record(data)
        sm_page.search_service(data["name"])
        sm_page.verify_service_exists(data["name"])
        sm_page.click_view_button(data["name"])
        sm_page.verify_view_popup_read_only()
        sm_page.close_popup()
        sm_page.search_service(data["name"])
        sm_page.click_history_button(data["name"])
        assert sm_page.page.locator(".popup-footer").count() > 0
        sm_page.close_popup()
