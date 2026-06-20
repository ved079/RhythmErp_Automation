"""Tests for api/test_discovery.py — module/test discovery logic."""
import os
from api.test_discovery import (
    discover_all_modules,
    get_display_name,
    _smart_display_name,
    parse_test_functions,
)


class TestDisplayNames:
    def test_smart_display_name_uses_curated(self):
        result = _smart_display_name("test_SP_C02_create_and_verify")
        assert result == "Create & Verify"

    def test_smart_display_name_strips_code_prefix(self):
        result = _smart_display_name("test_BNK_C01_add_bank")
        assert "add bank" in result.lower()

    def test_smart_display_name_fallback(self):
        result = _smart_display_name("test_my_simple_test")
        assert result == "My simple test"

    def test_get_display_name_known_folder(self):
        assert get_display_name("login_screens") == "Login Screens"

    def test_get_display_name_unknown_folder(self):
        assert get_display_name("unknown_folder") == "Unknown Folder"


class TestParseTestFunctions:
    def test_parses_valid_file(self, tmp_path):
        py_file = tmp_path / "test_example.py"
        py_file.write_text(
            "def test_hello():\n    '''Say hello.'''\n    pass\n"
            "def test_world():\n    pass\n"
        )
        tests = parse_test_functions(str(py_file))
        names = [t.name for t in tests]
        assert "test_hello" in names
        assert "test_world" in names

    def test_ignores_non_test_functions(self, tmp_path):
        py_file = tmp_path / "test_example.py"
        py_file.write_text("def helper():\n    pass\n")
        tests = parse_test_functions(str(py_file))
        assert len(tests) == 0

    def test_handles_syntax_error(self, tmp_path):
        py_file = tmp_path / "bad_syntax.py"
        py_file.write_text("def broken(")
        tests = parse_test_functions(str(py_file))
        assert tests == []


class TestDiscoverAllModules:
    def test_returns_empty_when_no_pages_dir(self, tmp_path):
        result = discover_all_modules(str(tmp_path))
        assert result.modules == []

    def test_returns_at_least_one_module(self, tmp_path):
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        mod_dir = pages_dir / "test_module"
        mod_dir.mkdir()
        test_file = mod_dir / "test_sample.py"
        test_file.write_text("def test_demo():\n    '''Demo test.'''\n    pass\n")

        result = discover_all_modules(str(tmp_path))
        assert len(result.modules) >= 1

    def test_each_module_has_name_and_display(self, tmp_path):
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        mod_dir = pages_dir / "my_module"
        mod_dir.mkdir()
        test_file = mod_dir / "test_foo.py"
        test_file.write_text("def test_foo():\n    pass\n")

        result = discover_all_modules(str(tmp_path))
        module = result.modules[0]
        assert module.name == "my_module"
        assert isinstance(module.display, str)
        assert len(module.display) > 0

    def test_submodules_nested_correctly(self, tmp_path):
        """Test that sub-modules inside a modules/ folder are nested correctly."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()

        # Create a top-level module with a modules/ subfolder
        mod_dir = pages_dir / "common_settings"
        mod_dir.mkdir()
        sub_dir = mod_dir / "modules" / "bank"
        sub_dir.mkdir(parents=True)
        test_file = sub_dir / "test_bank.py"
        test_file.write_text("def test_bank_add():\n    pass\n")

        result = discover_all_modules(str(tmp_path))
        module = result.modules[0]
        assert module.name == "common_settings"
        assert len(module.sub_modules) >= 1
        sub = module.sub_modules[0]
        assert sub.name == "bank"
        assert len(sub.tests) >= 1
        assert sub.tests[0].name == "test_bank_add"
