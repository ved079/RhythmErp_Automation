# Documents — Postman Collection

**File:** `documents_collection.json`

---

## Modules Covered

| Module | Requests | FK Fields | Notes |
|--------|----------|-----------|-------|
| Member | List, Get Detail, Create | None | PAN must be unique |
| Directors | List, Get Detail, Create | None | Flat form |
| Constituent Documents | List, Get Detail, Create | None | Flat form |
| Miscellaneous Documents | List, Get Detail, Create | None | Flat form |
| Register of Loan | List, Get Detail, Create | `name` (bank name field) | See bank name note below |
| Register Charges | List, Get Detail, Create | None | Flat form |

---

## Key Rules Discovered

### Member
- `pan_number` must be unique across the tenant — duplicate PAN causes validation failure
- Shares value must be within valid range for the member type

### Register of Loan
- Bank name field in the API payload is `"name"` not `"bank_name"` — ERP stores it under `name`
- This was a bug found during batch create: payload was sending `bank_name` key which the ERP ignored

### Import Paths (batch_create.py)
All documents modules live under `pages.documents.modules.*` — NOT `pages.registration.modules.*`.
The correct mappings in `api/batch_create.py`:
```python
"member":                   "pages.documents.modules.member.data.member_data",
"directors":                "pages.documents.modules.directors.data.directors_data",
"constituent_documents":    "pages.documents.modules.constituent_documents.data.constituent_documents_data",
"miscellaneous_documents":  "pages.documents.modules.miscellaneous_documents.data.miscellaneous_documents_data",
"register_of_loan":         "pages.documents.modules.register_of_loan.data.register_of_loan_data",
"register_charges":         "pages.documents.modules.register_charges.data.register_charges_data",
```

### Screen Name Map (batch_create.py)
These entries were missing from `_SCREEN_NAME_MAP` and had to be added:
```python
"miscellaneous_documents": "Miscellaneous Documents",
"constituent_documents":   "Constituent Documents",
"register_of_loan":        "Register of Loan",
"register_charges":        "Register Charges",
```

---

## What's Not Included
- No Update requests (not needed)
- No Delete requests

---

## See Also
- `pages/POSTMAN_GUIDE.md` — universal guide for building/extending collections
