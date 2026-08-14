from pages.company_onboarding.data.company_onboarding_data import generate_batch_payloads
from common.erp_api_client import RhythmERPAPIClient

token = input("Paste your ERP token: ").strip()
tenant_id = input("Paste your tenant ID: ").strip()
count = int(input("How many companies to create? ").strip())

client = RhythmERPAPIClient(username='', password='', tenant_id=tenant_id)
client.login_from_browser(token=token, tenant_id=tenant_id)

existing = client.list_entries('Company Onboarding', page_size=5)
rows = existing.get('screenmatlistingdata_set', [])
enriched = []
for row in rows[:2]:
    detail = client.get_entry('Company Onboarding', row['id'])
    if detail:
        enriched.append(detail)

payloads = generate_batch_payloads(count=count, existing_entries=enriched)
for p in payloads:
    result = client.create_entry(p)
    if result:
        print(f"CREATED #{result.get('id')} - {p['name']}")
    else:
        print(f"FAILED - {p['name']}")
