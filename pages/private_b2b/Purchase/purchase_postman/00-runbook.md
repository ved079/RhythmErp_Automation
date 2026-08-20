# 1. Runbook — Verified Steps

How to get a working PO → GP → GRN → QC run in Postman. This is the exact sequence that produced the last fully-verified run: PO **3910** → GP **2518** → GRN **2144** → QC **2143** on tenant **795**.

---

## 1.1 Import what's needed

From `pages/private_b2b/Purchase/purchase_postman/`:

1. **`purchase_collection.json`** → Postman **Import → Upload Files** → select it → imports as the **Purchase Chain** collection.
2. **`environment.json`** → imports as the **Purchase Chain** environment. Select it from the environment dropdown (top-right of Postman) so `{{token}}` / `{{base_url}}` / `{{tenant_id}}` resolve.

> Postman may reject the custom `"type": "secret"` entries in `environment.json` on import. That's cosmetic — re-enter the `token` value manually and it works.

## 1.2 Environment variables

Only three must be real for a run:

| Variable | Value | Example |
|----------|-------|---------|
| `base_url` | Tenant URL | `https://rhythmerp.algorhythms.in` |
| `token` | Bearer token (DevTools → any request → Authorization header) | `eyJ...` |
| `tenant_id` | Tenant id | `795` |

Everything else (`pur_*`) is populated by **Discover Context**. Do not manually fill them unless you are doing a manual fallback (see `04-troubleshooting.md`).

## 1.3 Run order (mandatory)

```
1. Setup → Discover Context   (once per tenant/login; rebuilds pur_*)
2. PO    → Create PO          → stores pur_po_id
3. GP    → Create GP          → stores pur_gp_id
4. GRN   → Create GRN         → stores pur_grn_id
5. QC    → Create QC          → stores pur_qc_id + pur_qc_lines
```

- **Discover Context** resolves the supplier (with ship/bill addresses), a PO-usable item, HSN tax rate, best-effort stored-PO header defaults, the GP `delivery_type`, the item's QC quality params (CQP), and the QC bag type (Packages).
- **Create PO** reads only `pur_*` env vars and does **not** call the API itself.
- **Create GP** reads `pur_po_id` + supplier/item deps and the PO's header values; it uses the `pur_gp_delivery_type` from Discover (default 29).
- **Create GRN** reads `pur_po_id` + `pur_gp_id` + supplier/item deps; all quantities = `pur_qty` (single-flow); currency is `1/1` (chain-faithful).
- **Create QC** reads `pur_po_id` + `pur_gp_id` + `pur_grn_id` + supplier/item deps, plus `pur_qc_params` (CQP) and `pur_bags_type_id` (Packages) from Discover; currency follows the PO (8/8 on 795 — unlike GRN).
- If you switch tenants or get a stale env, re-run **Discover Context** — it overwrites the `pur_*` vars and writes a fresh `pur_ctx`.

## 1.4 Success signals

- **Discover Context:** response is the Supplier list JSON (200). Console log prints `Discover done: Discover OK | ...` (View → Show Postman Console, `Ctrl+Alt+C`). Env var `pur_sniff_status` starts with `Discover OK |`.
- **Create PO:** returns `{"status":"Record Created Successfully","id":<id>}`. The test script stores `<id>` into `pur_po_id` and logs `PO created: id=... ref=...`.
- **Create GP:** returns `{"status":"Record Created Successfully","id":<id>}`. The test script stores `<id>` into `pur_gp_id` and logs `GP created: id=...`.
- **Create GRN:** returns `{"status":"Record Created Successfully","id":<id>}`. The test script stores `<id>` into `pur_grn_id` and logs `GRN created: id=...`.
- **Create QC:** returns `{"status":"Record Created Successfully","id":<id>}`. The test script stores `<id>` into `pur_qc_id`, snapshots the QC lines into `pur_qc_lines`, and logs `QC created: id=... ref=...`. Discover logs should include `QC quality params from CQP #...` and `bag type ... from Packages row ...`.

## 1.5 Resolving the token

1. Open the ERP in a browser, log in.
2. DevTools → Network tab → click any API request (`/core/dynamic-screen-wrapper/...`).
3. Copy the full `Authorization: Bearer <token>` value.
4. Paste into the `token` env var in Postman.

Token expiry: JWT — if Discover returns non-JSON / 401/502, your first suspect is an expired token.