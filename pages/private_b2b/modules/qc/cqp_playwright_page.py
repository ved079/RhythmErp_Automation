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
        """Search each item in CQP, intercept the API response to get real multiplier values.

        Falls back to DOM reading if the API response can't be parsed.

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

            # Collect all JSON API responses triggered by the row click
            captured = []

            def _on_response(response):
                try:
                    ct = response.headers.get("content-type", "")
                    if response.status == 200 and "json" in ct:
                        captured.append(response.json())
                except Exception:
                    pass

            self.page.on("response", _on_response)
            rows.first.click()
            self.page.wait_for_timeout(2000)
            self.page.remove_listener("response", _on_response)

            # Try to parse quality params from the captured API responses
            parsed = self._parse_cqp_from_api(captured)
            if parsed is not None:
                configs[name] = parsed
                print(f"[CQP-API] '{name}' → {configs[name]}")
            else:
                # Fallback: read from DOM (disabled inputs — may return wrong values)
                configs[name] = self._read_quality_param_table()
                print(f"[CQP-DOM] '{name}' → {configs[name]}")

            self._close_edit_popup()

        return configs

    def _parse_cqp_from_api(self, responses):
        """Try to extract quality param rows from captured API JSON responses.

        Looks for a response whose data contains fields recognisable as CQP rows
        (quality_parameter / min_quality_value / max_quality_value / multiplier).

        Returns list of param dicts on success, None if nothing matched.
        """
        # Field name candidates (snake_case and camelCase variants)
        PARAM_KEYS  = {"quality_parameter", "qualityParameter", "param", "parameter",
                       "quality_param", "qualityParam", "name"}
        MIN_KEYS    = {"min_quality_value", "minQualityValue", "min_q", "minQ",
                       "min_value", "minValue", "min"}
        MAX_KEYS    = {"max_quality_value", "maxQualityValue", "max_q", "maxQ",
                       "max_value", "maxValue", "max"}
        MULT_KEYS   = {"multiplier", "mult", "weight", "coefficient"}
        PCT_KEYS    = {"is_rate_percentage", "isRatePercentage", "is_percentage",
                       "isPercentage", "is_pct", "percentage"}

        def _pick(d, keys):
            for k in keys:
                if k in d:
                    return d[k]
            # case-insensitive fallback
            dl = {x.lower(): v for x, v in d.items()}
            for k in keys:
                if k.lower() in dl:
                    return dl[k.lower()]
            return None

        def _to_float(v):
            try:
                return float(v) if v not in (None, "", "null") else None
            except (TypeError, ValueError):
                return None

        def _try_parse_rows(rows):
            result = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                param = _pick(row, PARAM_KEYS)
                if not param:
                    continue
                min_q  = _to_float(_pick(row, MIN_KEYS))
                max_q  = _to_float(_pick(row, MAX_KEYS))
                mult   = _to_float(_pick(row, MULT_KEYS))
                is_pct = bool(_pick(row, PCT_KEYS))
                result.append({
                    "param":      str(param),
                    "min_q":      min_q  if min_q  is not None else 1.0,
                    "max_q":      max_q  if max_q  is not None else 100.0,
                    "multiplier": mult   if mult   is not None else 1.0,
                    "is_pct":     is_pct,
                })
            return result if result else None

        for resp in responses:
            # Response may be a list of rows directly, or wrapped in a key
            if isinstance(resp, list):
                parsed = _try_parse_rows(resp)
                if parsed:
                    return parsed
            elif isinstance(resp, dict):
                # Common wrapper keys: "data", "result", "records", "items", "rows"
                for key in ("data", "result", "results", "records", "items", "rows",
                            "quality_parameters", "qualityParameters", "params"):
                    if key in resp and isinstance(resp[key], list):
                        parsed = _try_parse_rows(resp[key])
                        if parsed:
                            return parsed
                # Try the dict itself as a single row
                parsed = _try_parse_rows([resp])
                if parsed:
                    return parsed

        return None

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
