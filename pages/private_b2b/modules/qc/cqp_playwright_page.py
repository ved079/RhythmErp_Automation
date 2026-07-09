import math
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class CQPPlaywrightPage(BasePlaywrightPage):
    """Commodity Quality Parameter master screen — read quality param configs per item."""
    URL = f"{BASE_URL}/#/dynamic-screens/Commodity%20Quality%20Parameter"

    def navigate_to_page(self):
        self.page.goto(self.URL)
        try:
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=15000)
        except Exception:
            self.page.reload()
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=20000)
        self.page.wait_for_timeout(500)

    def read_configs_for_items(self, item_names):
        """Search each item in the CQP listing, click the row, read quality param table.

        Returns:
            {item_name: [{"param": str, "min_q": float, "max_q": float,
                          "multiplier": float, "is_pct": bool}]}
        """
        configs = {}
        for name in item_names:
            if not name:
                continue
            self.navigate_to_page()
            self.search_entry(name)
            self.page.wait_for_timeout(800)

            rows = self.page.locator("table.mat-mdc-table tbody tr")
            if rows.count() == 0:
                print(f"[CQP] No rows found for item '{name}'")
                configs[name] = []
                continue

            # Click the row directly — Edit is disabled on CQP, row click opens detail view
            rows.first.click()
            self.page.wait_for_timeout(1500)

            configs[name] = self._read_quality_param_table()
            print(f"[CQP] '{name}' → {configs[name]}")
            self._close_edit_popup()

        return configs

    def _read_quality_param_table(self):
        """Read quality param rows from the popup, mapping columns by header text."""
        params = []

        # Find the table that has quality parameter headers
        table = self.page.locator(
            "xpath=//table[.//th[contains(.,'Quality Parameter')] or "
            ".//mat-header-cell[contains(.,'Quality Parameter')]]"
        ).first

        if not table.is_visible():
            # Fallback: any table inside the edit popup
            table = self.page.locator(
                "xpath=//div[contains(@class,'edit_pop_up') or "
                "contains(@class,'cdk-overlay-pane')]//table"
            ).first

        # Build column-name → index map from the header row
        col_map = {}
        header_cells = table.locator("thead th, thead mat-header-cell")
        for idx in range(header_cells.count()):
            text = header_cells.nth(idx).inner_text().strip().lower()
            col_map[text] = idx

        # Resolve column indices by keyword match
        def _col(keywords):
            for key, idx in col_map.items():
                if any(kw in key for kw in keywords):
                    return idx
            return None

        col_param  = _col(["quality parameter", "param"])
        col_min_q  = _col(["min"])
        col_max_q  = _col(["max"])
        col_is_pct = _col(["rate", "percentage", "is rate"])
        col_mult   = _col(["multiplier", "mult"])

        table_rows = table.locator("tbody tr")
        for i in range(table_rows.count()):
            row = table_rows.nth(i)
            cells = row.locator("td")
            if cells.count() == 0:
                continue

            def _cell(col_idx):
                if col_idx is None or col_idx >= cells.count():
                    return ""
                cell = cells.nth(col_idx)
                inp = cell.locator("input")
                sel = cell.locator("mat-select")
                if inp.count() > 0:
                    return inp.first.input_value().strip()
                if sel.count() > 0:
                    return sel.first.inner_text().strip()
                return cell.inner_text().strip()

            param_name = _cell(col_param if col_param is not None else 0)
            min_q_str  = _cell(col_min_q  if col_min_q  is not None else 1)
            max_q_str  = _cell(col_max_q  if col_max_q  is not None else 2)
            is_pct_str = _cell(col_is_pct if col_is_pct is not None else 3)
            mult_str   = _cell(col_mult   if col_mult   is not None else 4)

            if not param_name or param_name.lower() == "quality parameter":
                continue

            try:
                min_q  = float(min_q_str)  if min_q_str  else 100.0
                max_q  = float(max_q_str)  if max_q_str  else 1.0
                mult   = float(mult_str)   if mult_str   else 1.0
                is_pct = "percentage" in is_pct_str.lower()
            except (ValueError, AttributeError):
                continue

            params.append({
                "param":      param_name,
                "min_q":      min_q,
                "max_q":      max_q,
                "multiplier": mult,
                "is_pct":     is_pct,
            })

        return params

    def _close_edit_popup(self):
        try:
            cancel = self.page.locator(
                "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
            )
            cancel.first.wait_for(state="visible", timeout=3000)
            cancel.first.click()
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=8000)
        except Exception:
            try:
                self.page.locator("xpath=//mat-icon[text()='close']/ancestor::button").first.click()
            except Exception:
                try:
                    self.page.keyboard.press("Escape")
                except Exception:
                    pass
        self.page.wait_for_timeout(500)


def safe_values_from_params(params, max_pct):
    """Compute actual values so total deduction_pct <= max_pct.

    Formula: deduction_pct = sum(min_q_i / v_i * mult_i)
    To keep total <= max_pct, each param should contribute <= max_pct / n_params.
    Min safe v_i = ceil(min_q_i * mult_i * n_params / max_pct), clamped to [1, 99].
    """
    if not params:
        return []
    n = len(params)
    result = []
    for p in params:
        min_safe = math.ceil(p["min_q"] * p["multiplier"] * n / max_pct)
        min_safe = max(1, min(min_safe, 99))
        import random
        result.append(random.randint(min_safe, 99))
    return result
