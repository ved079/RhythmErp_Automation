"""
create_companies.py
-------------------
Logs into the local ERP via Playwright, grabs the Bearer token automatically,
then uses the API to batch-create Company Onboarding records.
"""

from playwright.sync_api import sync_playwright
from pages.company_onboarding.data.company_onboarding_data import generate_batch_payloads
from common.erp_api_client import RhythmERPAPIClient

LOGIN_URL = 'http://localhost:4200'
CORE_URL  = 'http://localhost:8001'

print("\n=== Company Onboarding Batch Creator ===\n")

is_multi    = input("Multi-tenant login? (y/n): ").strip().lower() == 'y'
email       = input("Email: ").strip()
password    = input("Password: ").strip()
tenant_name = input("Tenant name (as in dropdown): ").strip() if is_multi else None
tenant_id   = input("Tenant ID: ").strip()
count       = int(input("How many companies to create? ").strip())

print("\nOpening browser and logging in...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=200)
    page = browser.new_page()

    page.goto(f"{LOGIN_URL}/#/authentication/signin")
    page.wait_for_selector("input[name='Username']", timeout=15000)
    page.fill("input[name='Username']", email)
    page.fill("input[name='Password']", password)
    page.locator("button[type='submit']").click()
    page.wait_for_timeout(2000)

    if is_multi and tenant_name:
        page.wait_for_selector("mat-select", timeout=15000)
        page.locator("mat-select").first.click(force=True)
        page.wait_for_selector(".dd-search-input", timeout=10000)
        page.locator(".dd-search-input").fill(tenant_name)
        page.wait_for_timeout(800)
        for opt in page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text").all():
            if opt.inner_text().strip() == tenant_name:
                opt.click(force=True)
                break
        try:
            page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    page.locator("button[type='submit']").click(force=True)
    page.wait_for_url(
        lambda url: "signin" not in url.lower() and "authentication" not in url.lower(),
        timeout=20000,
    )
    print("  Logged in successfully.")

    print("  Capturing access token from network...")
    captured = {}

    def handle_request(request):
        auth = request.headers.get('authorization', '')
        if auth.startswith('Bearer ') and 'token' not in captured:
            captured['token'] = auth.replace('Bearer ', '')

    page.on('request', handle_request)
    page.wait_for_timeout(1500)
    page.reload()
    page.wait_for_timeout(4000)
    token = captured.get('token')

    browser.close()

if not token:
    print("\nERROR: Could not capture token. Try again.")
    exit(1)

print(f"  Token captured: {token[:30]}...")

client = RhythmERPAPIClient(username='', password='', tenant_id=tenant_id)
client.BASE_URL = CORE_URL
client.login_from_browser(token=token, tenant_id=tenant_id)

print("\nDiscovering Company Onboarding structure...")
structure = client.discover_structure('Company Onboarding')
if not structure:
    print("\nERROR: No existing Company Onboarding records found.")
    print("Create at least one company manually in your ERP first, then re-run.")
    exit(1)

print(f"  Found: {structure.get('name')} (parent_id={structure.get('parent_id')})\n")

payloads = generate_batch_payloads(count=count, existing_entries=[structure])

print(f"Creating {count} companies...\n")
for p in payloads:
    result = client.create_entry(p)
    if result:
        print(f"  CREATED #{result.get('id')} - {p['name']}")
    else:
        resp = getattr(client, '_last_raw_response', None)
        if resp is not None:
            print(f"  FAILED  - {p['name']}: HTTP {resp.status_code} — {resp.text[:500]}")
        else:
            print(f"  FAILED  - {p['name']}: connection error (no response)")
