import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)

_QPM_PARAMS = [
    # Physical parameters
    "Moisture Content", "Bulk Density", "Test Weight", "Grain Size", "Grain Length",
    "Grain Width", "Kernel Weight", "Broken Percentage", "Foreign Matter", "Shrivelled Grain",
    "Immature Grain", "Damaged Grain", "Discoloured Grain", "Chalky Grain", "Weevilled Grain",
    # Chemical parameters
    "Protein Content", "Fat Content", "Fibre Content", "Ash Content", "Starch Content",
    "Gluten Content", "Oil Content", "Fatty Acid Value", "Aflatoxin Level", "Pesticide Residue",
    "Heavy Metal Content", "Moisture Absorption", "Water Activity", "pH Level", "Acidity",
    # Sensory parameters
    "Colour Value", "Texture Score", "Aroma Score", "Taste Score", "Hardness",
    "Particle Size", "Viscosity", "Clarity", "Turbidity", "Brightness",
    # Milling parameters
    "Milling Recovery", "Head Rice Recovery", "Hulling Efficiency", "Whiteness Index",
    "Degree of Milling", "Bran Content", "Polish Degree",
    # Purity parameters
    "Purity Percentage", "Admixture Level", "Weed Seed Count", "Germination Rate",
    "Viability Percentage", "Vigour Index",
]

_QPM_QUALIFIERS = [
    "Index", "Score", "Level", "Value", "Rating",
    "Percentage", "Grade", "Parameter", "Measure", "Standard",
]


def _unique_data():
    global _counter
    _counter += 1
    param     = _rng.choice(_QPM_PARAMS)
    qualifier = _rng.choice(_QPM_QUALIFIERS)
    return {"name": f"{param} {qualifier} {_counter}"}


class TestQPMUIGroup1:
    def test_create_smoke(self, qpm_page):
        data = _unique_data()
        qpm_page.create_record(data)
        qpm_page.search_parameter(data["name"])
        qpm_page.verify_parameter_exists(data["name"])


class TestQPMUIGroup2:
    def test_form_discard(self, qpm_page):
        data = _unique_data()
        qpm_page.open_add_form()
        qpm_page.page.locator(qpm_page.NAME).first.click(force=True)
        qpm_page.page.locator(qpm_page.NAME).first.fill(data["name"])
        qpm_page.close_popup()
        assert not qpm_page.is_parameter_in_table(data["name"])

    def test_validation_sweep(self, qpm_page):
        qpm_page.open_add_form()
        qpm_page.submit()
        qpm_page.handle_validation_alert()
        qpm_page.close_popup()


class TestQPMUIGroup3:
    def test_listing_and_search(self, qpm_page):
        assert qpm_page.get_table_row_count() > 0

    def test_search_nonexistent(self, qpm_page):
        qpm_page.search_parameter("searchNonexitingCode")
        assert not qpm_page.is_parameter_in_table("searchNonexitingCode")


class TestQPMUIGroup4:
    def test_full_row_actions(self, qpm_page):
        data = _unique_data()
        qpm_page.create_record(data)
        qpm_page.search_parameter(data["name"])
        qpm_page.verify_parameter_exists(data["name"])

        # View
        qpm_page.click_view_button(data["name"])
        qpm_page.verify_view_popup_read_only()
        qpm_page.close_popup()

        # Edit — update name
        qpm_page.search_parameter(data["name"])
        updated_name = data["name"] + " Edited"
        qpm_page.click_edit_button(data["name"])
        qpm_page.update_name(updated_name)
        qpm_page.click_update()
        qpm_page.handle_success_alert()
        qpm_page.navigate_to_page()

        # History
        qpm_page.search_parameter(updated_name)
        qpm_page.click_history_button(updated_name)
        assert qpm_page.page.locator(".popup-footer").count() > 0
        qpm_page.close_popup()


class TestQPMUIGroup5:
    def test_duplicate_name_rejected(self, qpm_page):
        existing_name = qpm_page.page.locator("td.cdk-column-name").first.inner_text().strip()
        qpm_page.open_add_form()
        qpm_page.fill_form({"name": existing_name})
        qpm_page.submit()
        qpm_page.page.wait_for_selector(".swal2-container", timeout=5000)
        title = (qpm_page.page.locator("#swal2-title").text_content() or "").strip().lower()
        assert any(w in title for w in ("validation", "already", "exists", "duplicate", "error")), \
            f"Expected duplicate rejection alert, got: '{title}'"
        qpm_page.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        qpm_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        qpm_page.close_popup()
