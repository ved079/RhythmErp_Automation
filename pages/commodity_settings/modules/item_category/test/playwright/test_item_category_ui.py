import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)

_IC_MAIN = [
    # Foodgrains
    "Foodgrains", "Cereals", "Millets", "Pulses", "Oilseeds",
    # Commercial crops
    "Cotton", "Sugarcane", "Jute", "Tobacco", "Rubber",
    # Horticulture
    "Horticulture", "Vegetables", "Fruits", "Flowers", "Spices",
    # Plantation
    "Plantation Crops", "Medicinal Plants", "Aromatic Plants", "Forest Produce",
    # Animal & aqua
    "Livestock", "Poultry", "Fisheries", "Dairy", "Apiculture",
    # Processed
    "Processed Foods", "Milled Products", "Edible Oils", "Feed & Fodder",
    "Agro Chemicals", "Bio Inputs", "Farm Machinery",
]

_IC_SUB = [
    "Kharif", "Rabi", "Summer", "Annual", "Perennial",
    "Irrigated", "Rainfed", "Hybrid", "Traditional", "Organic",
    "Export", "Domestic", "Commercial", "Subsistence", "Certified",
]


def _unique_data():
    global _counter
    _counter += 1
    main = _rng.choice(_IC_MAIN)
    sub  = _rng.choice(_IC_SUB)
    name = f"{main} {sub} {_counter}"
    return {
        "item_category":   name,
        "item_description": f"Automated category entry {_counter}",
        "level":           1,
    }


class TestICUIGroup1:
    def test_create_smoke(self, ic_page):
        data = _unique_data()
        ic_page.create_record(data)
        ic_page.search_category(data["item_category"])
        ic_page.verify_category_exists(data["item_category"])


class TestICUIGroup2:
    def test_form_discard(self, ic_page):
        data = _unique_data()
        ic_page.open_add_form()
        ic_page.page.locator(ic_page.ITEM_CATEGORY).first.click(force=True)
        ic_page.page.locator(ic_page.ITEM_CATEGORY).first.fill(data["item_category"])
        ic_page.close_popup()
        assert not ic_page.is_category_in_table(data["item_category"])

    def test_validation_sweep(self, ic_page):
        ic_page.open_add_form()
        ic_page.submit()
        ic_page.handle_validation_alert()
        ic_page.close_popup()


class TestICUIGroup3:
    def test_listing_and_search(self, ic_page):
        assert ic_page.get_table_row_count() > 0


class TestICUIGroup4:
    def test_full_row_actions(self, ic_page):
        data = _unique_data()
        ic_page.create_record(data)
        ic_page.search_category(data["item_category"])
        ic_page.verify_category_exists(data["item_category"])
        ic_page.click_view_button(data["item_category"])
        ic_page.verify_view_popup_read_only()
        ic_page.close_popup()
        ic_page.search_category(data["item_category"])
        ic_page.click_history_button(data["item_category"])
        assert ic_page.page.locator(".popup-footer").count() > 0
        ic_page.close_popup()
