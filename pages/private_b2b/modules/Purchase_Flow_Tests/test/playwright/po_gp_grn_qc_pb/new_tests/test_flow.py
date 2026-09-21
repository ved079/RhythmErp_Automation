import pytest
from pages.private_b2b.modules.Purchase_Flow_Tests.test.playwright.po_gp_grn_qc_pb.new_tests.pages.qc_page import compute_actual_values


def _get_supplier_options(page):
    """Open the Supplier Name dropdown, collect all option texts, then close it."""
    sel = "xpath=//mat-label[contains(.,'Supplier Name')]/ancestor::mat-form-field//mat-select"
    page.locator(sel).first.click(force=True)
    page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
    opts = [
        o.inner_text().strip()
        for o in page.locator(
            ".mat-mdc-select-panel mat-option:not(.dd-clear-option) span.mdc-list-item__primary-text"
        ).all()
        if o.inner_text().strip()
    ]
    page.keyboard.press("Escape")
    try:
        page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
    except Exception:
        pass
    return opts


@pytest.mark.smoke
class TestSupplierFarmerDropdownAccess:
    """Verify supplier/farmer visibility rules on PO and GP supplier dropdowns.

    Rule:
      - PO supplier dropdown: only Suppliers visible, no Farmers
      - GP supplier dropdown: both Suppliers AND Farmers visible
    """

    def test_po_supplier_dropdown_excludes_farmers(self, po_page, flow_state):
        """PO supplier dropdown must show suppliers — and fewer names than GP (no farmers)."""
        po_page.open_add_form()
        po_names = set(_get_supplier_options(po_page.page))
        po_page.force_close_popup()

        assert po_names, "PO supplier dropdown should not be empty"
        assert "Urban Harvest Ltd" in po_names, "Known supplier must appear in PO dropdown"

        flow_state["po_supplier_names"] = po_names

    def test_gp_has_farmers_not_in_po(self, gp_page, flow_state):
        """GP supplier dropdown must include names absent from PO dropdown (those are farmers)."""
        po_names = flow_state.get("po_supplier_names")
        if not po_names:
            pytest.skip("PO supplier names not captured")

        gp_page.open_add_form()
        gp_names = set(_get_supplier_options(gp_page.page))
        gp_page.force_close_popup()

        assert gp_names, "GP supplier dropdown should not be empty"
        assert "Urban Harvest Ltd" in gp_names, "Known supplier must appear in GP dropdown"

        farmer_only = gp_names - po_names
        assert farmer_only, (
            f"GP dropdown should contain farmer names absent from PO, but sets are equal"
        )
        flow_state["farmer_only_names"] = farmer_only

    def test_gp_farmer_supplier_type_is_farmer(self, gp_page, flow_state):
        """Select a GP-only name and confirm its Supplier Type auto-fills as 'Farmer'."""
        farmer_only = flow_state.get("farmer_only_names")
        if not farmer_only:
            pytest.skip("No GP-only names found")

        farmer_name = next(iter(farmer_only))
        gp_page.open_add_form()

        sel = "xpath=//mat-label[contains(.,'Supplier Name')]/ancestor::mat-form-field//mat-select"
        gp_page.page.locator(sel).first.click(force=True)
        gp_page.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
        for opt in gp_page.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).all():
            if opt.inner_text().strip() == farmer_name:
                opt.click(force=True)
                break
        try:
            gp_page.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        gp_page.page.wait_for_timeout(1000)

        supplier_type = gp_page.page.locator(
            "xpath=//mat-label[contains(.,'Supplier Type')]/ancestor::mat-form-field//mat-select"
        ).text_content().strip()

        gp_page.force_close_popup()

        assert supplier_type == "Farmer", (
            f"Expected Supplier Type='Farmer' for '{farmer_name}', got '{supplier_type}'"
        )


@pytest.mark.smoke
class TestPOGPGRNQCPBFlow:
    def test_create_po(self, po_page, flow_state, chain_config):
        flow_state["chain_config"] = chain_config
        item = chain_config["item_name"]
        qty  = chain_config["quantity"]
        rate = chain_config["rate"]

        prev_top = po_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:PO:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            po_page.open_add_form()
            po_page.select_supplier("Urban Harvest Ltd")
            po_page.select_item_category("Raw material")
            po_page.select_location("Pune")
            po_page.select_department("Soyabean")
            po_page.select_division("Trading")
            po_page.select_type_of_sale("B2B")
            po_page.select_delivery_terms("Delivery")
            po_page.select_item_name(item)
            po_page.fill_quantity(str(qty))
            po_page.fill_rate(str(rate))
            po_page.select_gst_type("IGST")
            po_page.select_random_tax_rate()
            po_page.fill_expected_delivery_date()
            po_page.submit()
            ref_no = _confirmed_new(po_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:PO:{attempt} (ref unchanged — refreshing)", flush=True)
            _hard_refresh(po_page)
        assert ref_no, f"PO not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["po_ref_no"] = ref_no
        print(f"DOC_CREATED:PO:{ref_no}", flush=True)

    def test_create_gp(self, gp_page, flow_state):
        cfg  = flow_state["chain_config"]
        item = cfg["item_name"]
        qty  = cfg["quantity"]

        prev_top = gp_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:GP:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            gp_page.open_add_form()
            gp_page.select_supplier("Urban Harvest Ltd")
            gp_page.select_purchase_order(flow_state["po_ref_no"])
            gp_page.select_item_name(item)
            gp_page.fill_no_of_bags(str(qty))
            gp_page.fill_quantity(str(qty))
            gp_page.submit()
            ref_no = _confirmed_new(gp_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:GP:{attempt} (ref unchanged — refreshing)", flush=True)
            _hard_refresh(gp_page)
        assert ref_no, f"GP not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["gp_ref_no"] = ref_no
        print(f"DOC_CREATED:GP:{ref_no}", flush=True)

    def test_create_grn(self, grn_page, flow_state):
        cfg = flow_state["chain_config"]

        prev_top = grn_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:GRN:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            grn_page.open_add_form()
            grn_page.select_supplier("Urban Harvest Ltd")
            grn_page.select_gate_pass(flow_state["gp_ref_no"])
            grn_page.fill_received_quantity(str(cfg["quantity"]))
            grn_page.submit()
            ref_no = _confirmed_new(grn_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:GRN:{attempt} (ref unchanged — refreshing)", flush=True)
            _hard_refresh(grn_page)
        assert ref_no, f"GRN not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["grn_ref_no"] = ref_no
        print(f"DOC_CREATED:GRN:{ref_no}", flush=True)

    def test_create_qc(self, qc_page, flow_state):
        cfg            = flow_state["chain_config"]
        cqp_params     = cfg["cqp_params"]
        per_bag_weight = cfg["per_bag_weight"]

        actual_values = compute_actual_values(cqp_params)

        qc_page.open_add_form()

        qc_page.select_supplier("Urban Harvest Ltd")
        qc_page.select_gate_pass(flow_state["gp_ref_no"])

        # ── Bags detail ─────────────────────────────────────────────────
        # Total Weight = 1 × per_bag_weight = qty × 0.04 < qty ✓
        qc_page.open_bags_detail()
        qc_page.select_type_of_bag("test")
        qc_page.fill_no_of_bags("1")
        qc_page.fill_per_bag_weight(str(per_bag_weight))
        qc_page.done_bags()

        # ── Quality parameters ───────────────────────────────────────────
        # actual_values computed from CQP slab data via compute_actual_values()
        qc_page.open_quality_params()
        visible_count = qc_page.count_actual_value_inputs()
        for i, actual_val in enumerate(actual_values[:visible_count]):
            qc_page.fill_actual_value(i, str(actual_val))
        qc_page.done_quality_params()
        qc_page.close_quality_params_popup()

        qc_page.submit()

        ref_no = qc_page.get_ref_no_of_first_row()
        assert ref_no, "QC ref_no should not be empty"
        flow_state["qc_ref_no"] = ref_no

    def test_create_pb(self, pb_page, flow_state):
        prev_top = pb_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:PB:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            pb_page.open_add_form()
            pb_page.select_supplier("Urban Harvest Ltd")
            pb_page.select_qc(flow_state["qc_ref_no"])
            pb_page.select_gst_type("IGST")
            pb_page.select_gst_rate_any()
            if not pb_page.computed_fields_ready():
                print(f"RETRY:PB:{attempt} (computed fields empty — refreshing)", flush=True)
                pb_page.cancel_form()
                _hard_refresh(pb_page)
                continue
            try:
                pb_page.submit()
            except RuntimeError as e:
                print(f"RETRY:PB:{attempt} (submit failed: {e} - refreshing)", flush=True)
                pb_page.cancel_form()
                _hard_refresh(pb_page)
                continue
            ref_no = _confirmed_new(pb_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:PB:{attempt} (ref unchanged - refreshing)", flush=True)
            _hard_refresh(pb_page)
        assert ref_no, f"PB not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["pb_ref_no"] = ref_no
        print(f"DOC_CREATED:PB:{ref_no}", flush=True)

    def test_verify_closed_status(self, po_page, gp_page, grn_page, qc_page, flow_state):
        """After PB submission: QC → GRN → GP → PO should all show Closed status."""
        po_ref  = flow_state["po_ref_no"]
        gp_ref  = flow_state["gp_ref_no"]
        grn_ref = flow_state["grn_ref_no"]
        qc_ref  = flow_state["qc_ref_no"]

        # QC — Purchase Booking Status
        qc_page.navigate_to_page()
        qc_page.search(qc_ref)
        qc_status = qc_page.page.locator(
            f"tr:has-text('{qc_ref}') td.mat-column-booking_status span"
        ).first.text_content().strip()
        assert qc_status == "Closed", f"QC Purchase Booking Status: expected 'Closed', got '{qc_status}'"

        # GRN — QC Status
        grn_page.navigate_to_page()
        grn_page.search(grn_ref)
        grn_status = grn_page.page.locator(
            f"tr:has-text('{grn_ref}') td.mat-column-booking_status span"
        ).first.text_content().strip()
        assert grn_status == "Closed", f"GRN QC Status: expected 'Closed', got '{grn_status}'"

        # GP — GRN Status
        gp_page.navigate_to_page()
        gp_page.search(gp_ref)
        gp_status = gp_page.page.locator(
            f"tr:has-text('{gp_ref}') td.mat-column-booking_status span"
        ).first.text_content().strip()
        assert gp_status == "Closed", f"GP GRN Status: expected 'Closed', got '{gp_status}'"

        # PO — PO Status
        po_page.navigate_to_page()
        po_page.search(po_ref)
        po_status = po_page.page.locator(
            f"tr:has-text('{po_ref}') td.mat-column-po_status span"
        ).first.text_content().strip()
        assert po_status == "Closed", f"PO status: expected 'Closed', got '{po_status}'"


_MAX_RETRIES = 3


def _hard_refresh(page_obj):
    """Hard-reload the listing page (bypass cache) before starting the next creation."""
    page_obj.page.keyboard.press("Control+Shift+R")
    page_obj.page.wait_for_load_state("networkidle", timeout=15000)
    page_obj.page.wait_for_timeout(500)


def _confirmed_new(page_obj, prev_top):
    """Return new top ref_no if it differs from prev_top, else None."""
    ref_no = page_obj.get_ref_no_of_first_row()
    if ref_no and ref_no != prev_top:
        return ref_no
    return None


@pytest.mark.smoke
class TestConnectorWagoFlow:
    """PO→GP→GRN→QC→PB with CONNECTOR WAGO — create only, no verify steps.
    Rate/qty resolved from CBR; item and actual_values are hardcoded.

    Each step records the top-of-table ref_no before creating, then verifies
    the table shows a new ref_no after save — proving the record was persisted.
    Retries up to _MAX_RETRIES times if the top hasn't changed."""

    def test_create_po(self, po_page, flow_state, wago_config):
        flow_state["wago_config"] = wago_config
        cfg = wago_config
        prev_top = po_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:PO:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            po_page.open_add_form()
            po_page.select_supplier("Urban Harvest Ltd")
            po_page.select_item_category("Raw material")
            po_page.select_location("Pune")
            po_page.select_department("Soyabean")
            po_page.select_division("Trading")
            po_page.select_type_of_sale("B2B")
            po_page.select_delivery_terms("Delivery")
            po_page.select_item_name(cfg["item_name"])
            po_page.fill_quantity(str(cfg["quantity"]))
            po_page.fill_rate(str(cfg["rate"]))
            po_page.select_gst_type("IGST")
            po_page.select_random_tax_rate()
            po_page.fill_expected_delivery_date()
            po_page.submit()
            ref_no = _confirmed_new(po_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:PO:{attempt} (ref unchanged — refreshing)", flush=True)
            _hard_refresh(po_page)
        assert ref_no, f"PO not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["po_ref_no"] = ref_no
        print(f"DOC_CREATED:PO:{ref_no}", flush=True)

    def test_create_gp(self, gp_page, flow_state):
        cfg = flow_state["wago_config"]
        prev_top = gp_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:GP:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            gp_page.open_add_form()
            gp_page.select_supplier("Urban Harvest Ltd")
            gp_page.select_purchase_order(flow_state["po_ref_no"])
            gp_page.select_item_name(cfg["item_name"])
            gp_page.fill_no_of_bags(str(cfg["quantity"]))
            gp_page.fill_quantity(str(cfg["quantity"]))
            gp_page.submit()
            ref_no = _confirmed_new(gp_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:GP:{attempt} (ref unchanged — refreshing)", flush=True)
            _hard_refresh(gp_page)
        assert ref_no, f"GP not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["gp_ref_no"] = ref_no
        print(f"DOC_CREATED:GP:{ref_no}", flush=True)

    def test_create_grn(self, grn_page, flow_state):
        cfg = flow_state["wago_config"]
        prev_top = grn_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:GRN:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            grn_page.open_add_form()
            grn_page.select_supplier("Urban Harvest Ltd")
            grn_page.select_gate_pass(flow_state["gp_ref_no"])
            grn_page.fill_received_quantity(str(cfg["quantity"]))
            grn_page.submit()
            ref_no = _confirmed_new(grn_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:GRN:{attempt} (ref unchanged — refreshing)", flush=True)
            _hard_refresh(grn_page)
        assert ref_no, f"GRN not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["grn_ref_no"] = ref_no
        print(f"DOC_CREATED:GRN:{ref_no}", flush=True)

    def test_create_qc(self, qc_page, flow_state):
        cfg = flow_state["wago_config"]
        prev_top = qc_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:QC:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            qc_page.open_add_form()
            qc_page.select_supplier("Urban Harvest Ltd")
            qc_page.select_gate_pass(flow_state["gp_ref_no"])
            qc_page.open_bags_detail()
            qc_page.select_type_of_bag("test")
            qc_page.fill_no_of_bags("1")
            qc_page.fill_per_bag_weight(str(cfg["per_bag_weight"]))
            qc_page.done_bags()
            qc_page.open_quality_params()
            visible_count = qc_page.count_actual_value_inputs()
            vals = cfg["actual_values"]
            padded = (vals + [vals[-1]] * (visible_count - len(vals)))[:visible_count]
            for i, val in enumerate(padded):
                qc_page.fill_actual_value(i, str(val))
            qc_page.done_quality_params()
            qc_page.close_quality_params_popup()
            if not qc_page.computed_fields_ready():
                print(f"RETRY:QC:{attempt} (computed fields empty — refreshing)", flush=True)
                qc_page.cancel_form()
                _hard_refresh(qc_page)
                continue
            qc_page.submit()
            ref_no = _confirmed_new(qc_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:QC:{attempt}", flush=True)
        assert ref_no, f"QC not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["qc_ref_no"] = ref_no
        print(f"DOC_CREATED:QC:{ref_no}", flush=True)

    def test_create_pb(self, pb_page, flow_state):
        prev_top = pb_page.get_ref_no_of_first_row()
        print(f"PRE_TOP:PB:{prev_top}", flush=True)

        ref_no = None
        for attempt in range(1, _MAX_RETRIES + 1):
            pb_page.open_add_form()
            pb_page.select_supplier("Urban Harvest Ltd")
            pb_page.select_qc(flow_state["qc_ref_no"])
            pb_page.select_gst_type("IGST")
            pb_page.select_gst_rate_any()
            if not pb_page.computed_fields_ready():
                print(f"RETRY:PB:{attempt} (computed fields empty — refreshing)", flush=True)
                pb_page.cancel_form()
                _hard_refresh(pb_page)
                continue
            try:
                pb_page.submit()
            except RuntimeError as e:
                print(f"RETRY:PB:{attempt} (submit failed: {e} - refreshing)", flush=True)
                pb_page.cancel_form()
                _hard_refresh(pb_page)
                continue
            ref_no = _confirmed_new(pb_page, prev_top)
            if ref_no:
                break
            print(f"RETRY:PB:{attempt} (ref unchanged - refreshing)", flush=True)
            _hard_refresh(pb_page)
        assert ref_no, f"PB not confirmed in table after {_MAX_RETRIES} attempts"
        flow_state["pb_ref_no"] = ref_no
        print(f"DOC_CREATED:PB:{ref_no}", flush=True)


@pytest.mark.smoke
class TestConnectorWagoBatchFlow:
    """Batch mode: create all N POs first, then all N GPs, then GRNs, QCs, PBs.

    Configs are pre-generated by the FastAPI backend and passed via WAGO_CONFIGS
    env var — 1 CBR API call for chain 1, rest randomized locally from the rate band.
    Each test method loops over all N chains for that document type.
    """

    def test_batch_po(self, po_page, flow_state, wago_configs):
        flow_state["wago_configs"] = wago_configs
        flow_state["po_refs"] = []
        for i, cfg in enumerate(wago_configs):
            if i > 0:
                _hard_refresh(po_page)
            prev_top = po_page.get_ref_no_of_first_row()
            print(f"PRE_TOP:PO:{prev_top}", flush=True)
            ref_no = None
            for attempt in range(1, _MAX_RETRIES + 1):
                try:
                    po_page.open_add_form()
                except Exception as e:
                    print(f"RETRY:PO[{i+1}]:{attempt} (open_add_form: {type(e).__name__} — refreshing)", flush=True)
                    _hard_refresh(po_page)
                    continue
                po_page.select_supplier("Urban Harvest Ltd")
                po_page.select_item_category("Raw material")
                po_page.select_location("Pune")
                po_page.select_department("Soyabean")
                po_page.select_division("Trading")
                po_page.select_type_of_sale("B2B")
                po_page.select_delivery_terms("Delivery")
                po_page.select_item_name(cfg["item_name"])
                po_page.fill_quantity(str(cfg["quantity"]))
                po_page.fill_rate(str(cfg["rate"]))
                po_page.select_gst_type("IGST")
                po_page.select_random_tax_rate()
                po_page.fill_expected_delivery_date()
                po_page.submit()
                ref_no = _confirmed_new(po_page, prev_top)
                if ref_no:
                    break
                print(f"RETRY:PO[{i+1}]:{attempt} (ref unchanged — refreshing)", flush=True)
                _hard_refresh(po_page)
            assert ref_no, f"PO[{i+1}] not confirmed after {_MAX_RETRIES} attempts"
            flow_state["po_refs"].append(ref_no)
            print(f"DOC_CREATED:PO:{ref_no}", flush=True)

    def test_batch_gp(self, gp_page, flow_state):
        flow_state["gp_refs"] = []
        for i, cfg in enumerate(flow_state["wago_configs"]):
            if i > 0:
                _hard_refresh(gp_page)
            prev_top = gp_page.get_ref_no_of_first_row()
            print(f"PRE_TOP:GP:{prev_top}", flush=True)
            ref_no = None
            for attempt in range(1, _MAX_RETRIES + 1):
                try:
                    gp_page.open_add_form()
                except Exception as e:
                    print(f"RETRY:GP[{i+1}]:{attempt} (open_add_form: {type(e).__name__} — refreshing)", flush=True)
                    _hard_refresh(gp_page)
                    continue
                gp_page.select_supplier("Urban Harvest Ltd")
                gp_page.select_purchase_order(flow_state["po_refs"][i])
                gp_page.select_item_name(cfg["item_name"])
                gp_page.fill_no_of_bags(str(cfg["quantity"]))
                gp_page.fill_quantity(str(cfg["quantity"]))
                gp_page.submit()
                ref_no = _confirmed_new(gp_page, prev_top)
                if ref_no:
                    break
                print(f"RETRY:GP[{i+1}]:{attempt} (ref unchanged — refreshing)", flush=True)
                _hard_refresh(gp_page)
            assert ref_no, f"GP[{i+1}] not confirmed after {_MAX_RETRIES} attempts"
            flow_state["gp_refs"].append(ref_no)
            print(f"DOC_CREATED:GP:{ref_no}", flush=True)

    def test_batch_grn(self, grn_page, flow_state):
        flow_state["grn_refs"] = []
        for i, cfg in enumerate(flow_state["wago_configs"]):
            if i > 0:
                _hard_refresh(grn_page)
            prev_top = grn_page.get_ref_no_of_first_row()
            print(f"PRE_TOP:GRN:{prev_top}", flush=True)
            ref_no = None
            for attempt in range(1, _MAX_RETRIES + 1):
                try:
                    grn_page.open_add_form()
                except Exception as e:
                    print(f"RETRY:GRN[{i+1}]:{attempt} (open_add_form: {type(e).__name__} — refreshing)", flush=True)
                    _hard_refresh(grn_page)
                    continue
                grn_page.select_supplier("Urban Harvest Ltd")
                grn_page.select_gate_pass(flow_state["gp_refs"][i])
                grn_page.fill_received_quantity(str(cfg["quantity"]))
                grn_page.submit()
                ref_no = _confirmed_new(grn_page, prev_top)
                if ref_no:
                    break
                print(f"RETRY:GRN[{i+1}]:{attempt} (ref unchanged — refreshing)", flush=True)
                _hard_refresh(grn_page)
            assert ref_no, f"GRN[{i+1}] not confirmed after {_MAX_RETRIES} attempts"
            flow_state["grn_refs"].append(ref_no)
            print(f"DOC_CREATED:GRN:{ref_no}", flush=True)

    def test_batch_qc_pb(self, qc_page, pb_page, flow_state):
        """Interleaved: QC[i] then PB[i] for each chain before moving to i+1."""
        flow_state["qc_refs"] = []
        for i, cfg in enumerate(flow_state["wago_configs"]):
            # ── QC[i] ────────────────────────────────────────────────────────
            qc_page.navigate_to_page()
            prev_top = qc_page.get_ref_no_of_first_row()
            print(f"PRE_TOP:QC[{i+1}]:{prev_top}", flush=True)
            ref_no = None
            for attempt in range(1, _MAX_RETRIES + 1):
                try:
                    qc_page.open_add_form()
                except Exception as e:
                    print(f"RETRY:QC:{attempt} (open_add_form: {type(e).__name__} — refreshing)", flush=True)
                    _hard_refresh(qc_page)
                    continue
                qc_page.select_supplier("Urban Harvest Ltd")
                qc_page.select_gate_pass(flow_state["gp_refs"][i])
                qc_page.open_bags_detail()
                qc_page.select_type_of_bag("test")
                qc_page.fill_no_of_bags("1")
                qc_page.fill_per_bag_weight(str(cfg["per_bag_weight"]))
                qc_page.done_bags()
                qc_page.open_quality_params()
                visible_count = qc_page.count_actual_value_inputs()
                vals = cfg["actual_values"]
                padded = (vals + [vals[-1]] * (visible_count - len(vals)))[:visible_count]
                for j, val in enumerate(padded):
                    qc_page.fill_actual_value(j, str(val))
                qc_page.done_quality_params()
                qc_page.close_quality_params_popup()
                if not qc_page.computed_fields_ready():
                    print(f"RETRY:QC:{attempt} (computed fields empty — refreshing)", flush=True)
                    qc_page.cancel_form()
                    _hard_refresh(qc_page)
                    continue
                qc_page.submit()
                ref_no = _confirmed_new(qc_page, prev_top)
                if ref_no:
                    break
                print(f"RETRY:QC:{attempt}", flush=True)
            assert ref_no, f"QC[{i+1}] not confirmed after {_MAX_RETRIES} attempts"
            flow_state["qc_refs"].append(ref_no)
            print(f"DOC_CREATED:QC:{ref_no}", flush=True)

            # ── PB[i] ────────────────────────────────────────────────────────
            pb_page.navigate_to_page()
            prev_top = pb_page.get_ref_no_of_first_row()
            print(f"PRE_TOP:PB[{i+1}]:{prev_top}", flush=True)
            ref_no = None
            for attempt in range(1, _MAX_RETRIES + 1):
                try:
                    pb_page.open_add_form()
                except Exception as e:
                    print(f"RETRY:PB:{attempt} (open_add_form: {type(e).__name__} — refreshing)", flush=True)
                    _hard_refresh(pb_page)
                    continue
                pb_page.select_supplier("Urban Harvest Ltd")
                pb_page.select_qc(flow_state["qc_refs"][i])
                pb_page.select_gst_type("IGST")
                pb_page.select_gst_rate_any()
                if not pb_page.computed_fields_ready():
                    print(f"RETRY:PB:{attempt} (computed fields empty — refreshing)", flush=True)
                    pb_page.cancel_form()
                    _hard_refresh(pb_page)
                    continue
                try:
                    pb_page.submit()
                except RuntimeError as e:
                    print(f"RETRY:PB:{attempt} (submit failed: {e} — refreshing)", flush=True)
                    pb_page.cancel_form()
                    _hard_refresh(pb_page)
                    continue
                ref_no = _confirmed_new(pb_page, prev_top)
                if ref_no:
                    break
                print(f"RETRY:PB:{attempt} (ref unchanged — refreshing)", flush=True)
                _hard_refresh(pb_page)
            assert ref_no, f"PB[{i+1}] not confirmed after {_MAX_RETRIES} attempts"
            print(f"DOC_CREATED:PB:{ref_no}", flush=True)
