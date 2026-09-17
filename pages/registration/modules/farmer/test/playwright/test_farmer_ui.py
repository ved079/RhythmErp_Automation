import os
import tempfile
import pytest
import openpyxl
from pages.registration.modules.farmer.data.farmer_data import (
    generate_farmer_name,
    generate_email,
    generate_phone,
    generate_kyc_number,
)


def _make_data(category):
    return {
        "farmer_name":     generate_farmer_name(),
        "email":           generate_email(),
        "phone_number":    generate_phone(),
        "farmer_category": category,
        "state":           "Maharashtra",
        "address":         "101 MG Road, Pune",
        "bank_name":       "HDFC Bank",
        "bank_branch":     "Pune Branch",
        "bank_ifsc":       "SBIN0807508",
        "account_type":    "Current",
        "bank_holder":     "Account Holder",
        "bank_account":    "100000000498",
        "bank_proof":      "Cancelled Cheque",
    }


@pytest.mark.smoke
class TestWalkinFarmerCreate:
    def test_create_search_view(self, farmer_page):
        data = _make_data("Walk-in Farmer")

        farmer_page.create_record(data, category="Walk-in Farmer")

        farmer_page.search_farmer(data["farmer_name"])
        farmer_page.verify_farmer_exists(data["farmer_name"])

        farmer_page.click_view_button(data["farmer_name"])
        actual = farmer_page.page.locator(
            "xpath=//mat-label[contains(.,'Farmer Name')]/ancestor::mat-form-field//input"
        ).input_value()
        assert actual == data["farmer_name"], \
            f"View shows '{actual}', expected '{data['farmer_name']}'"
        farmer_page.force_close_popup()


@pytest.mark.smoke
class TestFPCMemberFarmerCreate:
    def test_create_search_view(self, farmer_page):
        data = _make_data("FPC Member")

        farmer_page.create_record(data, category="FPC Member")

        farmer_page.search_farmer(data["farmer_name"])
        farmer_page.verify_farmer_exists(data["farmer_name"])

        farmer_page.click_view_button(data["farmer_name"])
        actual = farmer_page.page.locator(
            "xpath=//mat-label[contains(.,'Farmer Name')]/ancestor::mat-form-field//input"
        ).input_value()
        assert actual == data["farmer_name"], \
            f"View shows '{actual}', expected '{data['farmer_name']}'"
        farmer_page.force_close_popup()


@pytest.mark.validation
class TestFarmerRequiredFieldValidation:
    REQUIRED_FIELDS = [
        "Farmer Name",
        "Phone Number",
        "Address Type",
        "State",
        "District",
        "Taluka",
        "Pin Code",
    ]

    def _assert_required_errors(self, page):
        for field in self.REQUIRED_FIELDS:
            loc = page.locator(
                f"xpath=//mat-form-field[contains(@class,'ng-invalid') and .//mat-label[contains(.,'{field}')]]"
            ).first
            assert loc.count() > 0, f"Expected ng-invalid on form field for '{field}'"

    def _dismiss_swal2(self, page):
        page.wait_for_selector(".swal2-container", timeout=10000)
        page.locator(".swal2-confirm").click()
        page.wait_for_selector(".swal2-container", state="hidden", timeout=15000)

    def test_walkin_required_fields(self, farmer_page):
        farmer_page.open_add_form()
        farmer_page.submit()
        farmer_page.page.wait_for_selector(".swal2-container", timeout=10000)
        self._assert_required_errors(farmer_page.page)
        self._dismiss_swal2(farmer_page.page)
        farmer_page._click_next()  # Bank Details — all optional
        farmer_page.force_close_popup()

    def test_fpc_required_fields(self, farmer_page):
        farmer_page.open_add_form()
        farmer_page._select_mat_option_by_text(farmer_page.FARMER_CATEGORY, "FPC Member")
        farmer_page.submit()
        farmer_page.page.wait_for_selector(".swal2-container", timeout=10000)
        self._assert_required_errors(farmer_page.page)
        self._dismiss_swal2(farmer_page.page)
        for _ in range(5):  # Additional → Land → Crop → KYC → Bank
            farmer_page._click_next()
        farmer_page.force_close_popup()

    def test_borrower_required_fields(self, farmer_page):
        farmer_page.open_add_form()
        farmer_page._select_mat_option_by_text(farmer_page.FARMER_CATEGORY, "Borrower Farmer")
        farmer_page.page.wait_for_timeout(1500)
        farmer_page.submit()
        farmer_page.page.wait_for_selector(".swal2-container", timeout=10000)
        self._assert_required_errors(farmer_page.page)
        self._dismiss_swal2(farmer_page.page)
        for _ in range(12):  # Family→Additional→Other→Land→Crop→KYC→Vehicle→Income→Bank→Irrigation→Award→Loan
            farmer_page._click_next()
        farmer_page.force_close_popup()


@pytest.mark.regression
class TestFarmerCreateEditHistory:
    def test_create_edit_view_history(self, farmer_page):
        data = _make_data("Walk-in Farmer")
        updated_name = generate_farmer_name()

        farmer_page.create_record(data, category="Walk-in Farmer")

        farmer_page.search_farmer(data["farmer_name"])
        farmer_page.verify_farmer_exists(data["farmer_name"])

        assert farmer_page.get_history_entry_count(data["farmer_name"]) == 0

        farmer_page.click_edit_button(data["farmer_name"])
        loc = farmer_page.page.locator(farmer_page.FARMER_NAME).first
        loc.click(click_count=3)
        loc.fill(updated_name)
        loc.press("Tab")
        farmer_page.click_update()
        farmer_page.page.wait_for_timeout(1000)

        farmer_page.search_farmer(updated_name)
        farmer_page.verify_farmer_exists(updated_name)

        assert farmer_page.get_history_entry_count(updated_name) == 1


@pytest.mark.smoke
class TestFarmerViewExisting:
    def test_view_first_farmer(self, farmer_page):
        farmer_page.page.locator("button.erp-row-trigger").nth(0).click()
        farmer_page.page.wait_for_selector(".mat-mdc-menu-panel", timeout=8000)
        farmer_page.page.get_by_role("menuitem", name="visibility View Open record").click()
        farmer_page.page.wait_for_selector(farmer_page.FARMER_NAME, timeout=8000)
        name = farmer_page.page.locator(farmer_page.FARMER_NAME).input_value()
        assert name, "Farmer Name should not be empty in View mode"
        farmer_page.force_close_popup()


@pytest.mark.smoke
class TestFarmerExportMaster:
    def test_export_matches_table(self, farmer_page):
        farmer_page.set_page_size("1000")

        table_data = farmer_page.read_table_data([1, 2, 3])
        assert table_data, "Table must have at least one row before export"

        download = farmer_page.export_master()
        ext = os.path.splitext(download.suggested_filename)[1].lower()
        tmp_path = os.path.join(tempfile.gettempdir(), download.suggested_filename)
        download.save_as(tmp_path)

        excel_data = []
        wb = openpyxl.load_workbook(tmp_path)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        data_start = next(
            (i + 1 for i, row in enumerate(rows) if str(row[0] or "").strip() == "Sr No"),
            None,
        )
        if data_start is not None:
            for row in rows[data_start:]:
                col1 = str(row[1] or "").strip()
                if not col1:
                    continue
                col2 = str(row[2] or "").strip()
                col3 = str(row[3] or "").strip()
                excel_data.append((col1, col2, col3))

        assert data_start is not None, "Could not find 'Sr No' header row in exported Excel"
        assert len(excel_data) == len(table_data), (
            f"Row count mismatch: table={len(table_data)}, excel={len(excel_data)}"
        )
        for i, (t, e) in enumerate(zip(table_data, excel_data)):
            assert t[0] == e[0], f"Row {i+1} col1 mismatch: table={t[0]!r}, excel={e[0]!r}"


@pytest.mark.smoke
class TestBorrowerFarmerCreate:
    def test_create_search_view(self, farmer_page):
        data = _make_data("Borrower Farmer")

        farmer_page.create_record(data, category="Borrower Farmer")

        farmer_page.search_farmer(data["farmer_name"])
        farmer_page.verify_farmer_exists(data["farmer_name"])

        farmer_page.click_view_button(data["farmer_name"])
        actual = farmer_page.page.locator(
            "xpath=//mat-label[contains(.,'Farmer Name')]/ancestor::mat-form-field//input"
        ).input_value()
        assert actual == data["farmer_name"], \
            f"View shows '{actual}', expected '{data['farmer_name']}'"
        farmer_page.force_close_popup()
