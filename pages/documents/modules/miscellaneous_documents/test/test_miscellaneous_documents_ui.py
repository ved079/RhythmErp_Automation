import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)

_DOC_TYPES = [
    "Loan Statement", "Bank Certificate", "NOC Letter", "Audit Report", "Balance Sheet",
    "Income Certificate", "Land Record", "Property Document", "Insurance Policy", "Tax Receipt",
    "Share Certificate", "Membership Certificate", "Lease Agreement", "Sale Deed", "Power of Attorney",
    "Board Resolution", "AGM Minutes", "Valuation Report", "Legal Notice", "Affidavit",
    "Mortgage Deed", "Hypothecation Agreement", "Guarantee Letter", "Sanction Letter", "Disbursement Letter",
    "Recovery Notice", "Compliance Certificate", "Registration Certificate", "Renewal Notice", "Closure Letter",
]

_DOC_SUBJECTS = [
    "Kharif Season", "Rabi Season", "FY 2024-25", "FY 2025-26", "Q1 Review",
    "Q2 Review", "Q3 Review", "Q4 Review", "Annual Audit", "Half Year Review",
    "Crop Loan", "Term Loan", "Gold Loan", "Vehicle Loan", "Housing Loan",
    "Working Capital", "Project Finance", "Subsidy Claim", "Grant Application", "Welfare Fund",
    "Primary Society", "District Federation", "State Level", "Central Scheme", "State Scheme",
    "NABARD Refinance", "RBI Compliance", "SEBI Filing", "MCA Submission", "ROC Filing",
    "Member Account", "Borrower Account", "Supplier Account", "Farmer Account", "Agent Account",
]


def _unique_doc_name():
    doc_type = _rng.choice(_DOC_TYPES)
    subject  = _rng.choice(_DOC_SUBJECTS)
    return f"{doc_type} {subject}"


def _unique_data():
    global _counter
    _counter += 1
    return {
        "document_name":   _unique_doc_name(),
        "document_number": str(_rng.randint(10000, 99999)),
        "registered_date": "08/01/2026",
        "expiry_date":     "07/08/2030",
        "brief_details":   f"Automated test details {_counter}",
    }


class TestMiscellaneousDocumentsUIGroup1:
    def test_create_smoke(self, md_page):
        data = _unique_data()
        md_page.create_record(data)
        md_page.search_document(data["document_name"])
        md_page.verify_document_exists(data["document_name"])


class TestMiscellaneousDocumentsUIGroup2:
    def test_form_discard(self, md_page):
        data = _unique_data()
        md_page.open_add_form()
        md_page.page.locator(md_page.DOCUMENT_NAME).first.click(force=True)
        md_page.page.locator(md_page.DOCUMENT_NAME).first.fill(data["document_name"])
        md_page.close_popup()
        assert not md_page.is_document_in_table(data["document_name"])

    def test_validation_sweep(self, md_page):
        md_page.open_add_form()
        md_page.submit()
        md_page.handle_validation_alert()
        md_page.close_popup()


class TestMiscellaneousDocumentsUIGroup3:
    def test_listing_and_search(self, md_page):
        assert md_page.get_table_row_count() > 0


class TestMiscellaneousDocumentsUIGroup4:
    def test_full_row_actions(self, md_page):
        data = _unique_data()
        md_page.create_record(data)
        md_page.search_document(data["document_name"])
        md_page.verify_document_exists(data["document_name"])
        md_page.click_view_button(data["document_name"])
        md_page.verify_view_popup_read_only()
        md_page.close_popup()
        md_page.search_document(data["document_name"])
        md_page.click_history_button(data["document_name"])
        assert md_page.page.locator(".popup-footer").count() > 0
        md_page.close_popup()
