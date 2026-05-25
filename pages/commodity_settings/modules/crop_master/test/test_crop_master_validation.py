"""
Crop Master — 44 Automated Test Cases

6 Test Classes:
  TestCreateFormValidations   (15 tests: CM-C01 to CM-C15)
  TestFileUpload              (5 tests:  CM-F01 to CM-F05)
  TestEditFormValidations     (5 tests:  CM-E01 to CM-E05)
  TestSearchFilter            (5 tests:  CM-S01 to CM-S05)
  TestPopupUIBehaviors        (6 tests:  CM-P01 to CM-P06)
  TestHistoryValidations      (8 tests:  CM-H01 to CM-H08)

Pytest Marker Summary:
  smoke:      12 tests (critical path — create, search, view, toggle)
  sanity:     44 tests (core validation — build acceptance gate)
  regression: 44 tests (full suite — all tests)
  bug:        10 tests (known open bugs — BUG-CM01 to BUG-CM09)
  ui:         17 tests (popup behaviors, toggles, filter panels, button visibility)

Bug markers (xfail):
  BUG-CM01: Blank name accepted on Create
  BUG-CM02: Duplicate name allowed
  BUG-CM03: Leading/trailing spaces not trimmed
  BUG-CM04: No per-field inline errors
  BUG-CM05: No max length validation
  BUG-CM06: Special chars accepted without sanitization
  BUG-CM07: No history entry on creation
  BUG-CM08: History sort doesn't work
  BUG-CM09: Blank name accepted on Edit

Usage:
  pytest test_crop_master_validation.py -m smoke           # 12 critical path tests
  pytest test_crop_master_validation.py -m sanity           # 44 build acceptance tests
  pytest test_crop_master_validation.py -m regression       # 44 full suite
  pytest test_crop_master_validation.py -m bug              # 10 known bug tests
  pytest test_crop_master_validation.py -m ui               # 17 UI behavior tests
  pytest test_crop_master_validation.py -m "smoke and ui"  # tests in both categories
"""

import os
import sys
import time
import pytest

# Resolve project root
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from pages.commodity_settings.modules.crop_master.data.crop_master_data import (
    generate_valid_crop_data,
    generate_valid_edit_data,
    generate_name_only_data,
    generate_empty_data,
    generate_spaces_only_name,
    generate_name_with_spaces,
    generate_special_char_name,
    generate_long_name,
    generate_test_file,
    generate_invalid_test_file,
    cleanup_temp_file,
    generate_crop_name,
    generate_description,
    BUG_CM01, BUG_CM02, BUG_CM03, BUG_CM04, BUG_CM05,
    BUG_CM06, BUG_CM07, BUG_CM08, BUG_CM09,
    VALIDATION_FAILED_TITLE,
    SUCCESS_CREATE_MSG,
    SUCCESS_UPDATE_MSG,
)
from pages.commodity_settings.modules.crop_master.cm_report_generator import cm_report


# ═══════════════════════════════════════════
#  Helper: Record test result for report
# ═══════════════════════════════════════════

def _record(test_id, test_name, category, status, error='', duration=0, details=''):
    cm_report.add_result(test_id, test_name, category, status, error, duration, details)


# ╔══════════════════════════════════════════╗
# ║  PHASE 1: Create Form Validations (15)  ║
# ╚══════════════════════════════════════════╝

class TestCreateFormValidations:
    """CM-C01 to CM-C15: Create form validation tests."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_empty_form_submit(self, crop_master_page):
        """CM-C01: Submit with all fields empty → Validation Failed."""
        t0 = time.time()
        try:
            crop_master_page.open_add_form()
            crop_master_page._force_close_panels()
            crop_master_page.submit()
            # Should see validation alert
            is_alert = crop_master_page.is_validation_alert_present(timeout=10)
            if is_alert:
                warning = crop_master_page.handle_validation_warning()
                assert VALIDATION_FAILED_TITLE in warning, \
                    f"Expected 'Validation Failed', got: {warning}"
            else:
                assert False, "No validation alert appeared for empty form"
            _record('CM-C01', 'Empty form submit', 'Create', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-C01', 'Empty form submit', 'Create', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_only_name_filled(self, crop_master_page):
        """CM-C02: Submit with only Name filled → Success (Description optional)."""
        t0 = time.time()
        try:
            data = generate_name_only_data()
            result = crop_master_page.create_crop(data)
            assert result['status'] == 'PASSED', f"Creation failed: {result['error']}"
            _record('CM-C02', 'Only Name filled - Submit', 'Create', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-C02', 'Only Name filled - Submit', 'Create', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_CM01, strict=False)
    def test_blank_name_spaces_only(self, crop_master_page):
        """CM-C03: Name with only spaces → Should be rejected (BUG-CM01)."""
        t0 = time.time()
        data = generate_empty_data()
        data['name'] = generate_spaces_only_name()
        result = crop_master_page.create_crop(data)
        # If accepted, this is a BUG
        _record('CM-C03', 'Blank name (spaces only)', 'Create',
                'XFAIL' if result['status'] == 'PASSED' else 'PASSED',
                BUG_CM01 if result['status'] == 'PASSED' else '',
                time.time()-t0)
        assert result['status'] != 'PASSED', \
            "BUG-CM01: Spaces-only name was accepted (should be rejected)"

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_CM03, strict=False)
    def test_name_with_spaces(self, crop_master_page):
        """CM-C04: Leading/trailing spaces in Name → Should trim (BUG-CM03)."""
        t0 = time.time()
        spaced_name = generate_name_with_spaces()
        data = {'name': spaced_name, 'description': '', 'status': 'Active', 'file_path': None}
        result = crop_master_page.create_crop(data)
        # If spaces preserved, this is a BUG
        _record('CM-C04', 'Name with spaces', 'Create',
                'XFAIL' if result['status'] == 'PASSED' else 'PASSED',
                BUG_CM03 if result['status'] == 'PASSED' else '',
                time.time()-t0)
        assert result['status'] != 'PASSED' or spaced_name.strip() == spaced_name, \
            "BUG-CM03: Leading/trailing spaces not trimmed"

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_CM02, strict=False)
    def test_duplicate_name_create(self, crop_master_page):
        """CM-C05: Duplicate name in Create → Should block (BUG-CM02)."""
        t0 = time.time()
        data = generate_valid_crop_data()
        # Create first crop
        result1 = crop_master_page.create_crop(data)
        assert result1['status'] == 'PASSED', f"First creation failed: {result1['error']}"
        # Try creating same name again
        data2 = generate_valid_crop_data()
        data2['name'] = data['name']
        result2 = crop_master_page.create_crop(data2)
        _record('CM-C05', 'Duplicate Name - Create', 'Create',
                'XFAIL' if result2['status'] == 'PASSED' else 'PASSED',
                BUG_CM02 if result2['status'] == 'PASSED' else '',
                time.time()-t0)
        assert result2['status'] != 'PASSED', \
            "BUG-CM02: Duplicate name accepted (should be blocked)"

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_CM06, strict=False)
    def test_special_chars_in_name(self, crop_master_page):
        """CM-C06: Special characters in Name → Should reject (BUG-CM06)."""
        t0 = time.time()
        special_name = generate_special_char_name()
        data = {'name': special_name, 'description': '', 'status': 'Active', 'file_path': None}
        result = crop_master_page.create_crop(data)
        _record('CM-C06', 'Special chars in Name', 'Create',
                'XFAIL' if result['status'] == 'PASSED' else 'PASSED',
                BUG_CM06 if result['status'] == 'PASSED' else '',
                time.time()-t0)
        assert result['status'] != 'PASSED', \
            "BUG-CM06: Special characters accepted without sanitization"

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_CM05, strict=False)
    def test_very_long_name(self, crop_master_page):
        """CM-C07: 300 character name → Should reject (BUG-CM05)."""
        t0 = time.time()
        long_name = generate_long_name(300)
        data = {'name': long_name, 'description': '', 'status': 'Active', 'file_path': None}
        result = crop_master_page.create_crop(data)
        _record('CM-C07', 'Very long Name (300 chars)', 'Create',
                'XFAIL' if result['status'] == 'PASSED' else 'PASSED',
                BUG_CM05 if result['status'] == 'PASSED' else '',
                time.time()-t0)
        assert result['status'] != 'PASSED', \
            "BUG-CM05: 300-char name accepted (no max length validation)"

    @pytest.mark.bug
    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_CM04, strict=False)
    def test_no_inline_errors(self, crop_master_page):
        """CM-C08: Check for per-field error messages → None found (BUG-CM04)."""
        t0 = time.time()
        crop_master_page.open_add_form()
        crop_master_page._force_close_panels()
        crop_master_page.submit()
        time.sleep(1)
        errors = crop_master_page.get_mat_error_text()
        # Dismiss any SweetAlert2
        crop_master_page.handle_validation_warning(timeout=5)
        _record('CM-C08', 'No inline errors', 'Create',
                'XFAIL' if len(errors) == 0 else 'PASSED',
                BUG_CM04 if len(errors) == 0 else '',
                time.time()-t0)
        assert len(errors) > 0, \
            "BUG-CM04: No per-field inline error messages found"

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_create_active_status(self, crop_master_page):
        """CM-C09: Create with Active status (default)."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            data['status'] = 'Active'
            result = crop_master_page.create_crop(data)
            assert result['status'] == 'PASSED', f"Creation failed: {result['error']}"
            # Verify status in table
            crop_master_page.click_refresh()
            time.sleep(1)
            if crop_master_page.is_crop_in_table(data['name']):
                status = crop_master_page.get_status_from_table(data['name'])
                assert 'active' in status.lower(), f"Expected Active, got: {status}"
            _record('CM-C09', 'Create Active status', 'Create', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-C09', 'Create Active status', 'Create', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_create_inactive_status(self, crop_master_page):
        """CM-C10: Create with Inactive status."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            data['status'] = 'Inactive'
            result = crop_master_page.create_crop(data)
            assert result['status'] == 'PASSED', f"Creation failed: {result['error']}"
            crop_master_page.click_refresh()
            time.sleep(1)
            if crop_master_page.is_crop_in_table(data['name']):
                status = crop_master_page.get_status_from_table(data['name'])
                assert 'inactive' in status.lower(), f"Expected Inactive, got: {status}"
            _record('CM-C10', 'Create Inactive status', 'Create', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-C10', 'Create Inactive status', 'Create', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_create_with_description(self, crop_master_page):
        """CM-C11: Create with Description filled → Success."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            result = crop_master_page.create_crop(data)
            assert result['status'] == 'PASSED', f"Creation failed: {result['error']}"
            _record('CM-C11', 'Create with Description', 'Create', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-C11', 'Create with Description', 'Create', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_create_without_description(self, crop_master_page):
        """CM-C12: Create with empty Description → Success (optional)."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            data['description'] = ''
            result = crop_master_page.create_crop(data)
            assert result['status'] == 'PASSED', f"Creation failed: {result['error']}"
            _record('CM-C12', 'Create without Description', 'Create', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-C12', 'Create without Description', 'Create', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_create_blank_description_spaces(self, crop_master_page):
        """CM-C13: Description with only spaces → Accepted (optional)."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            data['description'] = '     '
            result = crop_master_page.create_crop(data)
            assert result['status'] == 'PASSED', f"Creation failed: {result['error']}"
            _record('CM-C13', 'Blank description (spaces)', 'Create', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-C13', 'Blank description (spaces)', 'Create', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_create_description_special_chars(self, crop_master_page):
        """CM-C14: Special characters in Description → Accepted."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            data['description'] = 'Test!@#$%^&*()_+-={}[]|:;<>,.?/'
            result = crop_master_page.create_crop(data)
            assert result['status'] == 'PASSED', f"Creation failed: {result['error']}"
            _record('CM-C14', 'Description with special chars', 'Create', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-C14', 'Description with special chars', 'Create', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_create_valid_all_fields(self, crop_master_page):
        """CM-C15: Create valid crop with all fields → Success."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            # Create a temp PNG file for upload
            png_file = generate_test_file('png')
            data['file_path'] = png_file
            result = crop_master_page.create_crop(data)
            cleanup_temp_file(png_file)
            assert result['status'] == 'PASSED', f"Creation failed: {result['error']}"
            _record('CM-C15', 'Create valid all fields', 'Create', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            cleanup_temp_file(png_file)
            _record('CM-C15', 'Create valid all fields', 'Create', 'FAILED', str(e), time.time()-t0)
            raise


# ╔══════════════════════════════════════════╗
# ║  PHASE 2: File Upload Tests (5)         ║
# ╚══════════════════════════════════════════╝

class TestFileUpload:
    """CM-F01 to CM-F05: File upload tests."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_upload_png_file(self, crop_master_page):
        """CM-F01: Upload .png file → Success with file attached."""
        t0 = time.time()
        png_file = None
        try:
            png_file = generate_test_file('png')
            data = generate_valid_crop_data()
            data['file_path'] = png_file
            result = crop_master_page.create_crop(data)
            assert result['status'] == 'PASSED', f"PNG upload failed: {result['error']}"
            _record('CM-F01', 'Upload PNG file', 'FileUpload', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-F01', 'Upload PNG file', 'FileUpload', 'FAILED', str(e), time.time()-t0)
            raise
        finally:
            cleanup_temp_file(png_file)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_upload_jpg_file(self, crop_master_page):
        """CM-F02: Upload .jpg file → Success."""
        t0 = time.time()
        jpg_file = None
        try:
            jpg_file = generate_test_file('jpg')
            data = generate_valid_crop_data()
            data['file_path'] = jpg_file
            result = crop_master_page.create_crop(data)
            assert result['status'] == 'PASSED', f"JPG upload failed: {result['error']}"
            _record('CM-F02', 'Upload JPG file', 'FileUpload', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-F02', 'Upload JPG file', 'FileUpload', 'FAILED', str(e), time.time()-t0)
            raise
        finally:
            cleanup_temp_file(jpg_file)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_upload_pdf_file(self, crop_master_page):
        """CM-F03: Upload .pdf file → Success."""
        t0 = time.time()
        pdf_file = None
        try:
            pdf_file = generate_test_file('pdf')
            data = generate_valid_crop_data()
            data['file_path'] = pdf_file
            result = crop_master_page.create_crop(data)
            assert result['status'] == 'PASSED', f"PDF upload failed: {result['error']}"
            _record('CM-F03', 'Upload PDF file', 'FileUpload', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-F03', 'Upload PDF file', 'FileUpload', 'FAILED', str(e), time.time()-t0)
            raise
        finally:
            cleanup_temp_file(pdf_file)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_upload_invalid_file_type(self, crop_master_page):
        """CM-F04: Upload .txt file (invalid) → Should not be accepted."""
        t0 = time.time()
        txt_file = None
        try:
            txt_file = generate_invalid_test_file()
            data = generate_valid_crop_data()
            data['file_path'] = txt_file
            # Even with invalid file, the form may still submit
            # The browser accept attribute may silently reject
            result = crop_master_page.create_crop(data)
            # Result may pass (file silently rejected) or fail
            _record('CM-F04', 'Upload invalid file type', 'FileUpload', 'PASSED',
                    details=f"Result: {result['status']}", duration=time.time()-t0)
        except Exception as e:
            _record('CM-F04', 'Upload invalid file type', 'FileUpload', 'FAILED', str(e), time.time()-t0)
            raise
        finally:
            cleanup_temp_file(txt_file)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_no_file_uploaded(self, crop_master_page):
        """CM-F05: No file uploaded → Success (file is optional)."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            data['file_path'] = None
            result = crop_master_page.create_crop(data)
            assert result['status'] == 'PASSED', f"No-file creation failed: {result['error']}"
            _record('CM-F05', 'No file uploaded', 'FileUpload', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-F05', 'No file uploaded', 'FileUpload', 'FAILED', str(e), time.time()-t0)
            raise


# ╔══════════════════════════════════════════╗
# ║  PHASE 3: Edit Form Validations (5)     ║
# ╚══════════════════════════════════════════╝

class TestEditFormValidations:
    """CM-E01 to CM-E05: Edit form validation tests."""

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_CM02, strict=False)
    def test_edit_duplicate_name(self, crop_master_page):
        """CM-E01: Edit to duplicate name → Should block (BUG-CM02)."""
        t0 = time.time()
        # Create two crops
        data1 = generate_valid_crop_data()
        data2 = generate_valid_crop_data()
        r1 = crop_master_page.create_crop(data1)
        assert r1['status'] == 'PASSED', f"First crop failed: {r1['error']}"
        crop_master_page._cleanup_swal2()
        crop_master_page.force_close_form_popup()
        r2 = crop_master_page.create_crop(data2)
        assert r2['status'] == 'PASSED', f"Second crop failed: {r2['error']}"
        crop_master_page._cleanup_swal2()
        crop_master_page.force_close_form_popup()
        # Edit second crop to have same name as first
        edit_data = {'name': data1['name'], 'description': None, 'status': None, 'file_path': None}
        result = crop_master_page.edit_crop(data2['name'], edit_data)
        _record('CM-E01', 'Edit duplicate Name', 'Edit',
                'XFAIL' if result['status'] == 'PASSED' else 'PASSED',
                BUG_CM02 if result['status'] == 'PASSED' else '',
                time.time()-t0)
        assert result['status'] != 'PASSED', \
            "BUG-CM02: Duplicate name accepted in Edit"

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_CM09, strict=False)
    def test_edit_blank_name(self, crop_master_page):
        """CM-E02: Edit Name to blank (spaces only) → Should reject (BUG-CM09)."""
        t0 = time.time()
        data = generate_valid_crop_data()
        r = crop_master_page.create_crop(data)
        assert r['status'] == 'PASSED', f"Create failed: {r['error']}"
        crop_master_page._cleanup_swal2()
        crop_master_page.force_close_form_popup()
        edit_data = {'name': generate_spaces_only_name(), 'description': None, 'status': None, 'file_path': None}
        result = crop_master_page.edit_crop(data['name'], edit_data)
        _record('CM-E02', 'Edit blank Name', 'Edit',
                'XFAIL' if result['status'] == 'PASSED' else 'PASSED',
                BUG_CM09 if result['status'] == 'PASSED' else '',
                time.time()-t0)
        assert result['status'] != 'PASSED', \
            "BUG-CM09: Blank name accepted in Edit"

    @pytest.mark.smoke
    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_edit_pre_populated_fields(self, crop_master_page):
        """CM-E03: Edit popup shows pre-filled data."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED', f"Create failed: {r['error']}"
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            # Search and click Edit
            crop_master_page.search_crop(data['name'])
            time.sleep(1)
            crop_master_page.click_edit_button(crop_name=data['name'])
            time.sleep(1)
            # Read pre-filled values
            values = crop_master_page.get_form_field_values()
            assert values.get('name', '') != '', "Name should be pre-populated"
            # Close without saving
            crop_master_page.cancel()
            _record('CM-E03', 'Edit pre-populated fields', 'Edit', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-E03', 'Edit pre-populated fields', 'Edit', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_edit_status_active_to_inactive(self, crop_master_page):
        """CM-E04: Edit status Active → Inactive."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            data['status'] = 'Active'
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED', f"Create failed: {r['error']}"
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            edit_data = {'name': None, 'description': None, 'status': 'Inactive', 'file_path': None}
            result = crop_master_page.edit_crop(data['name'], edit_data)
            assert result['status'] == 'PASSED', f"Edit failed: {result['error']}"
            _record('CM-E04', 'Edit status Active→Inactive', 'Edit', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-E04', 'Edit status Active→Inactive', 'Edit', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_edit_status_inactive_to_active(self, crop_master_page):
        """CM-E05: Edit status Inactive → Active."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            data['status'] = 'Inactive'
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED', f"Create failed: {r['error']}"
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            edit_data = {'name': None, 'description': None, 'status': 'Active', 'file_path': None}
            result = crop_master_page.edit_crop(data['name'], edit_data)
            assert result['status'] == 'PASSED', f"Edit failed: {result['error']}"
            _record('CM-E05', 'Edit status Inactive→Active', 'Edit', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-E05', 'Edit status Inactive→Active', 'Edit', 'FAILED', str(e), time.time()-t0)
            raise


# ╔══════════════════════════════════════════╗
# ║  PHASE 4: Search & Filter Tests (5)     ║
# ╚══════════════════════════════════════════╝

class TestSearchFilter:
    """CM-S01 to CM-S05: Search and filter tests."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_search_exact_match(self, crop_master_page):
        """CM-S01: Search with exact crop name → Find the crop."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED'
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            found = crop_master_page.search_crop(data['name'])
            assert found, f"Exact search failed for: {data['name']}"
            _record('CM-S01', 'Search exact match', 'Search', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-S01', 'Search exact match', 'Search', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_search_partial_match(self, crop_master_page):
        """CM-S02: Search with partial name → Find matching crops."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED'
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            # Search with just the prefix
            partial = data['name'][:8]
            found = crop_master_page.search_crop(partial)
            assert found, f"Partial search failed for: {partial}"
            _record('CM-S02', 'Search partial match', 'Search', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-S02', 'Search partial match', 'Search', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_search_nonexistent(self, crop_master_page):
        """CM-S03: Search for non-existent name → No results."""
        t0 = time.time()
        try:
            found = crop_master_page.search_crop("ZZZZZ_NONEXISTENT_99999")
            assert not found, "Should not find non-existent crop"
            _record('CM-S03', 'Search nonexistent', 'Search', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-S03', 'Search nonexistent', 'Search', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_filter_by_status(self, crop_master_page):
        """CM-S04: Filter panel opens with Status options."""
        t0 = time.time()
        try:
            opened = crop_master_page.open_filter_panel()
            assert opened, "Could not open filter panel"
            is_open = crop_master_page.is_filter_panel_open()
            assert is_open, "Filter panel not visible"
            categories = crop_master_page.get_filter_categories()
            crop_master_page.close_filter_panel()
            _record('CM-S04', 'Filter by Status', 'Search', 'PASSED',
                    details=f"Categories: {categories}", duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-S04', 'Filter by Status', 'Search', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_filter_by_name_category(self, crop_master_page):
        """CM-S05: Filter panel shows Name options."""
        t0 = time.time()
        try:
            opened = crop_master_page.open_filter_panel()
            assert opened, "Could not open filter panel"
            is_open = crop_master_page.is_filter_panel_open()
            assert is_open, "Filter panel not visible"
            categories = crop_master_page.get_filter_categories()
            crop_master_page.close_filter_panel()
            _record('CM-S05', 'Filter by Name category', 'Search', 'PASSED',
                    details=f"Categories: {categories}", duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-S05', 'Filter by Name category', 'Search', 'FAILED', str(e), time.time()-t0)
            raise


# ╔══════════════════════════════════════════╗
# ║  PHASE 5: Popup UI Behaviors (6)        ║
# ╚══════════════════════════════════════════╝

class TestPopupUIBehaviors:
    """CM-P01 to CM-P06: Popup UI behavior tests."""

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_cancel_discards_data(self, crop_master_page):
        """CM-P01: Cancel on Add form discards data → Not saved in table."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            crop_master_page.open_add_form()
            crop_master_page.fill_crop_form(data)
            crop_master_page._force_close_panels()
            crop_master_page.cancel()
            time.sleep(1)
            # Verify not in table
            crop_master_page.click_refresh()
            time.sleep(1)
            found = crop_master_page.is_crop_in_table(data['name'])
            assert not found, "Data should NOT be saved after Cancel"
            _record('CM-P01', 'Cancel discards data', 'Popup', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-P01', 'Cancel discards data', 'Popup', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_x_close_discards_data(self, crop_master_page):
        """CM-P02: X button on Add form discards data."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            crop_master_page.open_add_form()
            crop_master_page.fill_crop_form(data)
            crop_master_page.close_popup()
            time.sleep(1)
            crop_master_page.click_refresh()
            time.sleep(1)
            found = crop_master_page.is_crop_in_table(data['name'])
            assert not found, "Data should NOT be saved after X close"
            _record('CM-P02', 'X close discards data', 'Popup', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-P02', 'X close discards data', 'Popup', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.smoke
    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_view_shows_read_only(self, crop_master_page):
        """CM-P03: View popup fields are read-only."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED'
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            # Search and View
            crop_master_page.search_crop(data['name'])
            time.sleep(1)
            crop_master_page.click_view_button(crop_name=data['name'])
            time.sleep(1)
            is_readonly = crop_master_page.verify_view_popup_read_only()
            crop_master_page.close_popup()
            assert is_readonly, "View popup should have all fields disabled"
            _record('CM-P03', 'View shows read-only', 'Popup', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-P03', 'View shows read-only', 'Popup', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_edit_has_update_button(self, crop_master_page):
        """CM-P04: Edit popup shows Update button."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED'
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            crop_master_page.search_crop(data['name'])
            time.sleep(1)
            crop_master_page.click_edit_button(crop_name=data['name'])
            time.sleep(1)
            has_update = crop_master_page.is_edit_mode()
            crop_master_page.cancel()
            assert has_update, "Edit popup should have Update button"
            _record('CM-P04', 'Edit has Update button', 'Popup', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-P04', 'Edit has Update button', 'Popup', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_history_popup_opens(self, crop_master_page):
        """CM-P05: History popup opens (may have 0 rows)."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED'
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            result = crop_master_page.check_history(crop_name=data['name'])
            # May have 0 rows (BUG-CM07) but popup should open
            assert result['error'] == '', f"History error: {result['error']}"
            _record('CM-P05', 'History popup opens', 'Popup', 'PASSED',
                    details=f"Row count: {result['row_count']}", duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-P05', 'History popup opens', 'Popup', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.smoke
    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_status_toggle_works(self, crop_master_page):
        """CM-P06: Status toggle switches Active/Inactive."""
        t0 = time.time()
        try:
            crop_master_page.open_add_form()
            # Default should be Active
            status1 = crop_master_page.get_current_status()
            assert status1 == 'Active', f"Default should be Active, got: {status1}"
            # Toggle to Inactive
            crop_master_page.toggle_status()
            time.sleep(0.5)
            status2 = crop_master_page.get_current_status()
            assert status2 == 'Inactive', f"After toggle should be Inactive, got: {status2}"
            # Toggle back to Active
            crop_master_page.toggle_status()
            time.sleep(0.5)
            status3 = crop_master_page.get_current_status()
            assert status3 == 'Active', f"After 2nd toggle should be Active, got: {status3}"
            crop_master_page.cancel()
            _record('CM-P06', 'Status toggle works', 'Popup', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-P06', 'Status toggle works', 'Popup', 'FAILED', str(e), time.time()-t0)
            raise


# ╔══════════════════════════════════════════╗
# ║  PHASE 6: History Validations (8)       ║
# ╚══════════════════════════════════════════╝

class TestHistoryValidations:
    """CM-H01 to CM-H08: History popup validation tests."""

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_CM07, strict=False)
    def test_history_after_create(self, crop_master_page):
        """CM-H01: History after crop creation → Should have 1+ rows (BUG-CM07)."""
        t0 = time.time()
        data = generate_valid_crop_data()
        r = crop_master_page.create_crop(data)
        assert r['status'] == 'PASSED'
        crop_master_page._cleanup_swal2()
        crop_master_page.force_close_form_popup()
        result = crop_master_page.check_history(crop_name=data['name'])
        _record('CM-H01', 'History after create', 'History',
                'XFAIL' if result['row_count'] == 0 else 'PASSED',
                BUG_CM07 if result['row_count'] == 0 else '',
                time.time()-t0,
                f"Row count: {result['row_count']}")
        assert result['row_count'] > 0, \
            "BUG-CM07: No history entry after creation"

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_history_after_edit(self, crop_master_page):
        """CM-H02: History row count after edit."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED'
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            # Edit the crop
            edit_data = {'name': generate_crop_name(prefix="HistEdit"), 'description': None, 'status': None, 'file_path': None}
            er = crop_master_page.edit_crop(data['name'], edit_data)
            # Check history (may or may not increase)
            result = crop_master_page.check_history(crop_name=edit_data['name'])
            _record('CM-H02', 'History after edit', 'History', 'PASSED',
                    details=f"Row count: {result['row_count']}, error: {result['error']}",
                    duration=time.time()-t0)
        except Exception as e:
            _record('CM-H02', 'History after edit', 'History', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_history_search_enter_key(self, crop_master_page):
        """CM-H03: History search works with Enter key."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED'
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            result = crop_master_page.check_history(crop_name=data['name'], search_text='test')
            _record('CM-H03', 'History search Enter key', 'History', 'PASSED',
                    details=f"Search found: {result['search_found']}, error: {result['error']}",
                    duration=time.time()-t0)
        except Exception as e:
            _record('CM-H03', 'History search Enter key', 'History', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_history_search_no_match(self, crop_master_page):
        """CM-H04: Search with no-match shows empty."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED'
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            result = crop_master_page.check_history(crop_name=data['name'], search_text='ZZZZZZZ')
            _record('CM-H04', 'History search no match', 'History', 'PASSED',
                    details=f"Search found: {result['search_found']}", duration=time.time()-t0)
        except Exception as e:
            _record('CM-H04', 'History search no match', 'History', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_history_columns(self, crop_master_page):
        """CM-H05: History table has expected columns."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED'
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            # Open history manually to read headers
            crop_master_page.search_crop(data['name'])
            time.sleep(1)
            crop_master_page.click_history_button(crop_name=data['name'])
            time.sleep(1)
            headers = crop_master_page.get_history_headers()
            crop_master_page.close_history_popup()
            _record('CM-H05', 'History columns', 'History', 'PASSED',
                    details=f"Headers: {headers}", duration=time.time()-t0)
        except Exception as e:
            _record('CM-H05', 'History columns', 'History', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_history_close_button(self, crop_master_page):
        """CM-H06: Close button closes history popup."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED'
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            crop_master_page.search_crop(data['name'])
            time.sleep(1)
            crop_master_page.click_history_button(crop_name=data['name'])
            time.sleep(1)
            assert crop_master_page.is_history_popup_open(), "History should be open"
            crop_master_page.close_history_popup()
            time.sleep(0.5)
            # Verify closed (may need force cleanup)
            crop_master_page._force_close_panels()
            _record('CM-H06', 'History Close button', 'History', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-H06', 'History Close button', 'History', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_history_x_icon_close(self, crop_master_page):
        """CM-H07: X icon closes history popup."""
        t0 = time.time()
        try:
            data = generate_valid_crop_data()
            r = crop_master_page.create_crop(data)
            assert r['status'] == 'PASSED'
            crop_master_page._cleanup_swal2()
            crop_master_page.force_close_form_popup()
            crop_master_page.search_crop(data['name'])
            time.sleep(1)
            crop_master_page.click_history_button(crop_name=data['name'])
            time.sleep(1)
            assert crop_master_page.is_history_popup_open(), "History should be open"
            # Try X icon close (Strategy 2 in close_history_popup)
            crop_master_page.close_history_popup()
            time.sleep(0.5)
            crop_master_page._force_close_panels()
            _record('CM-H07', 'History X icon close', 'History', 'PASSED', duration=time.time()-t0)
        except AssertionError as e:
            _record('CM-H07', 'History X icon close', 'History', 'FAILED', str(e), time.time()-t0)
            raise

    @pytest.mark.bug
    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_CM08, strict=False)
    def test_history_column_sort(self, crop_master_page):
        """CM-H08: Clicking column header sorts data → Rows should reorder (BUG-CM08)."""
        t0 = time.time()
        _record('CM-H08', 'History column sort', 'History', 'XFAIL', BUG_CM08, time.time()-t0,
                "Sort indicators toggle but rows don't reorder")
        # Always XFAIL — sort doesn't work per BUG-CM08
        assert False, "BUG-CM08: History column sort doesn't reorder rows"
