# RhythmERP — What Is This Thing?

> A business-oriented introduction to the ERP product you'll be testing. No code here — just understanding what the software does and why each section exists.

---

## What is RhythmERP?

RhythmERP is a **commodity trading and agricultural supply chain management system** built by Algorhythms. It's used by agricultural cooperatives, farmer producer companies (FPCs), and commodity trading businesses across India.

At its core, the ERP handles:
- **Buying and selling commodities** (grains, pulses, oilseeds, etc.)
- **Managing suppliers and customers** who trade these commodities
- **Tracking quality parameters** for commodity grading
- **Managing farmer registrations** with detailed KYC and land records
- **Tax compliance** (GST, HSN/SAC codes)
- **User access control** (roles, permissions, entity groups)

The ERP runs as a web application at `https://rhythmerp.algorhythms.in`. It's built with Angular on the frontend and a proprietary backend API. The frontend uses Angular Material components extensively — this is important because Angular Material has specific behaviors that make automated testing challenging.

---

## The ERP Sections

When you log in, you'll see a left sidebar with these main sections. Each section is a `pages/` folder in our repo:

### 1. Common Settings
**What it does**: Configures the foundational data that every other module references. Think of it as the "system settings."

| Module | Business Purpose |
|--------|-----------------|
| **Bank** | Defines banks and their IFSC codes. Used by Supplier/Customer/Farmer bank details. |
| **UOM** (Unit of Measurement) | Defines measurement units — KG, Quintal, MT, Liter, etc. Used everywhere in commodity trading. |
| **UOM Conversion** | Defines conversion factors between units (1 Quintal = 100 KG). Critical for pricing calculations. |
| **Season** | Defines trading seasons — Kharif, Rabi, Zaid. Commodities are seasonal. |
| **HSN SAC** | Harmonized System of Nomenclature codes for GST compliance. Every commodity needs an HSN code. |
| **Tax Authority** | Defines tax authorities (CGST, SGST, IGST). Used by tax rate configuration. |
| **Tax Rate** | Defines tax rates per HSN code per authority. The only Common Settings module with a stepper. |
| **Designation** | Job titles — Manager, Clerk, Accountant, etc. Used by Employee/Directors modules. |
| **Error Code Master** | System error codes for different categories (Farmer, Debit Note, Credit Note, Workflow). |
| **Vehicle Master** | Vehicle registrations for logistics. Truck, Trailer, Tanker, etc. |

**Key insight**: Common Settings modules are typically created FIRST when setting up a new ERP instance, because other modules depend on them. If Bank doesn't exist, you can't create a Supplier with bank details.

### 2. Commodity Settings
**What it does**: Configures the commodities themselves — what you're trading, how you grade them, and how you price them.

| Module | Business Purpose |
|--------|-----------------|
| **Item Master** | The central commodity catalog. Soybean, Wheat, Rice, etc. with all their attributes. |
| **Item Category** | Classifies items — Grains, Pulses, Oilseeds, Spices. |
| **Item Group** | Groups items for reporting — Food Grains, Cash Crops, Plantation. |
| **Item Attribute** | Defines item attributes — Color, Size, Moisture Content. Items can have up to 5 attributes. |
| **Crop Master** | Links crops to seasons. A crop is different from an item — it's what's grown, not what's traded. |
| **Quality Parameter Master** | Defines quality benchmarks — Moisture %, Foreign Matter %, Damaged Grains %. |
| **Commodity Quality Parameter** | Links quality parameters to specific items. Soybean has different quality thresholds than Wheat. |
| **Commodity Base Rate** | Sets the base price per unit for each commodity. Used as the starting point for pricing calculations. |
| **Services Master** | Defines services (not goods) — Transportation, Storage, Processing. Has its own HSN/SAC codes. |

**Key insight**: Item Master is the most complex Commodity module. Its dropdowns cascade: Category → Group → Type → Attribute 1-5. The fill order matters — you can't select an attribute before selecting the category.

### 3. Registration
**What it does**: Registers the entities that participate in the commodity trading ecosystem.

| Module | Business Purpose |
|--------|-----------------|
| **Supplier** | Companies/people who SELL commodities TO the organization. Has multi-step registration with address and bank details. |
| **Customer** | Companies/people who BUY commodities FROM the organization. Similar structure to Supplier. |
| **Farmer** | Individual farmers who grow crops. The most complex registration — up to 13 tabs depending on farmer category. |
| **Agent** | Commission agents who facilitate trades between buyers and sellers. |
| **Employee** | Internal staff of the organization. Simple registration. |
| **Directors** | Board of directors for the organization. Has KYC details. |
| **Member** | Members of the farmer producer company. Similar to Directors with KYC. |

**Key insight**: Supplier and Customer are the most battle-tested modules in the entire repo. Farmer is the most complex by tab count. Agent and Farmer currently lack API tests — these are gaps to fill.

### 4. Access
**What it does**: Controls who can access what in the ERP.

| Module | Business Purpose |
|--------|-----------------|
| **Entity Group Definition** | Groups entities (companies) together. A user's access is scoped to their entity group. |
| **Role Creation** | Defines roles (Admin, Manager, Operator) and what screens each role can access. |
| **User Creation** | Creates user accounts with a role and entity group assignment. |

**Key insight**: These modules are simple in form (2-4 fields each) but have the most bugs. No API tests exist yet.

### 5. Company Onboarding
**What it does**: Registers new companies/tenants in the ERP. This is a 6-step wizard that sets up an entire company with its details, promoters, address, business info, and infrastructure.

**Key insight**: This is the only module with a dedicated **update flow**. The page object for updates inherits from the create page object. Also the only module with bulk creation (up to 1000 companies at once via API).

---

## How the ERP's API Works

All ERP screens follow the same API pattern:

```
POST /core/dynamic-screen-wrapper/
```

With a JSON payload like:
```json
{
    "attribute_name": "Bank",
    "field1": "value1",
    "field2": "value2",
    "details": [],
    "children": []
}
```

Key concepts:
- **`attribute_name`**: Identifies which screen/entity you're creating. "Bank", "Supplier", "UOM", etc.
- **`details`**: Array of row data for repeating sections on the same stepper
- **`children`**: Array of stepper child objects. Each child has its own `stepper_name`, `is_stepper: true`, and its own `details` array

This means every single ERP screen uses the same endpoint — only the `attribute_name` and the payload structure change.

### Authentication

The ERP uses JWT-based auth:
1. `POST /auth/login1/` with `username`, `password`, `tenant`
2. The response's `Set-Cookie` header contains a `refresh_token` — this is your JWT
3. All subsequent requests include `X-Tenant-ID: 599` and the cookie

Our `common/erp_api_client.py` handles all of this automatically.

---

## The Multi-Tenant Nature

The ERP is multi-tenant. Tenant ID `599` is the test environment. This matters because:
- **FK IDs are tenant-specific**. Bank ID 1005 in tenant 599 might not exist in tenant 600
- **Test data is shared**. Anyone using tenant 599 sees your test entries
- **Never test against production tenants**. Always use 599

---

## What Makes This ERP Hard to Test

1. **Angular Material dropdowns**: Clicking an option in a `mat-select` does NOT update Angular's reactive form model. You have to use JavaScript to set the value and dispatch events manually. This is the #1 source of flaky tests.

2. **No consistent validation UX**: Some screens show a success SweetAlert, others silently close the form. Some show field-specific error messages, others show a generic "Validation Failed". You can't write one pattern and expect it to work everywhere.

3. **Cascading FK dependencies**: Selecting a Country narrows down available States. Selecting a State narrows down Districts. And so on. If you pick the wrong Country, the State dropdown is empty.

4. **Slow and stateful**: The ERP sometimes takes 3-5 seconds to save. If you assert too early, your test fails. If you wait too long, your test is slow.

5. **Shared database**: Test data from previous runs can interfere with current runs. A "Test Bank 123" created yesterday will cause a duplicate error today.

---

## Logging In Manually

To understand the ERP, log in yourself:

1. Open `https://rhythmerp.algorhythms.in` in your browser
2. Enter:
   - **Username**: `user@admin.com`
   - **Password**: `Tenant@123456789`
   - **Tenant**: `599`
3. Click Login

You'll see the dashboard. Navigate the sidebar to explore each section. Try creating a Bank entry manually — watch how the dropdowns behave, how the form validates, what happens when you submit.

> **This manual exploration is essential.** You cannot automate what you don't understand. Spend at least 2 hours clicking around the ERP before writing any test code.
