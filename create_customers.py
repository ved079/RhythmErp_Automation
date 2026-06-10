import json, subprocess, random, string

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgwMzI5MzU5LCJpYXQiOjE3ODAzMTQ5NTksImp0aSI6IjZiMjUzZDY4MDM5ZjRlMDQ5NTY2YzZiMWFjMjViMWJhIiwidXNlcl9pZCI6IjE0NiJ9.br6PtTvqO8iinvJQI-oMoHpj4OZ47Vy_Fl7WooPwXuQ"
TENANT = "681"
URL = "https://rhythmerp.algorhythms.in/core/dynamic-screen-wrapper/"

# FK IDs from captured payload + schemas
# India=8, Maharashtra=101, Pune=233, Pune City=12979
# Ownership: Proprietorship=5, Pvt Ltd=7, Partnership=6, Individual=4, Public Ltd=8, LLP=9
# Sale Type: Export=1264, Services=1266, Contract=1265, Commission=1267
# Supply Type: Both=223, Services=224, Goods=225
# Currency INR=1
# Address Type: Shipping=43, Billing=42
# Account Type: Current=1849, Saving=1850
# Bank Proof: Cancelled Cheque=36, Passbook=35, Bank Statement=1883

customers = [
    {"name": "Sunrise Agro Traders", "ownership": 5, "sale": 1267, "supply": 225, "email": "sunrise.agro@mail.in", "phone": "9823111001", "pan": "AABCS1234A", "address": "12 Station Road Nashik", "pin": "422001", "gstin": "27AABCS1234A1Z5", "bank": "Bank of Maharashtra", "branch": "Nashik Main Branch", "ifsc": "MAHB0001234", "acct": "601234567890", "district": 230, "district_name": "Nashik", "taluka": 12876, "taluka_name": "Khed"},
    {"name": "Metro Fresh Foods Pvt Ltd", "ownership": 7, "sale": 1266, "supply": 223, "email": "metro.fresh@mail.in", "phone": "9823111002", "pan": "AABCM5678B", "address": "78 Laxmi Road Pune", "pin": "411030", "gstin": "27AABCM5678B1Z3", "bank": "HDFC Bank", "branch": "Pune FC Road", "ifsc": "HDFC0001234", "acct": "501234567890", "district": 233, "district_name": "Pune", "taluka": 12979, "taluka_name": "Pune City"},
    {"name": "Krishna Grain Exports", "ownership": 5, "sale": 1264, "supply": 225, "email": "krishna.grain@mail.in", "phone": "9823111003", "pan": "AABCK9012C", "address": "34 MIDC Kolhapur", "pin": "416005", "gstin": "27AABCK9012C1Z1", "bank": "Bank of India", "branch": "Kolhapur Branch", "ifsc": "BKID0001234", "acct": "701234567890", "district": 223, "district_name": "Kolhapur", "taluka": 12752, "taluka_name": "Baramati"},
    {"name": "Sahyadri Herbals Partnership", "ownership": 6, "sale": 1266, "supply": 223, "email": "sahyadri.herbal@mail.in", "phone": "9823111004", "pan": "AABCH3456D", "address": "56 JM Road Shivajinagar", "pin": "411005", "gstin": "27AABCH3456D1Z9", "bank": "State Bank of India", "branch": "Shivajinagar Branch", "ifsc": "SBIN0001234", "acct": "321234567890", "district": 233, "district_name": "Pune", "taluka": 12930, "taluka_name": "Mulshi"},
    {"name": "Narmada Cotton Industries", "ownership": 7, "sale": 1267, "supply": 225, "email": "narmada.cotton@mail.in", "phone": "9823111005", "pan": "AABCN7890E", "address": "90 Ring Road Nagpur", "pin": "440001", "gstin": "27AABCN7890E1Z7", "bank": "Punjab National Bank", "branch": "Nagpur Main", "ifsc": "PUNB0001234", "acct": "141234567890", "district": 227, "district_name": "Nagpur", "taluka": 12731, "taluka_name": "Ambegaon"},
    {"name": "Dakshin Spices and Condiments", "ownership": 5, "sale": 1266, "supply": 223, "email": "dakshin.spice@mail.in", "phone": "9823111006", "pan": "AABCD2345F", "address": "23 MG Road Satara", "pin": "415001", "gstin": "27AABCD2345F1Z5", "bank": "Union Bank of India", "branch": "Satara Branch", "ifsc": "UBIN0001234", "acct": "531234567890", "district": 237, "district_name": "Satara", "taluka": 12765, "taluka_name": "Bhor"},
    {"name": "Western Ghat Produce LLP", "ownership": 9, "sale": 1265, "supply": 223, "email": "wghat.produce@mail.in", "phone": "9823111007", "pan": "AABCW6789G", "address": "45 Hill Road Ratnagiri", "pin": "415612", "gstin": "27AABCW6789G1Z3", "bank": "Canara Bank", "branch": "Ratnagiri Branch", "ifsc": "CNRB0001234", "acct": "251234567890", "district": 235, "district_name": "Ratnagiri", "taluka": 12916, "taluka_name": "Mawal"},
    {"name": "Mumbai Mart Retailers", "ownership": 7, "sale": 1266, "supply": 225, "email": "mumbaimart@mail.in", "phone": "9823111008", "pan": "AABCM1111H", "address": "12 SV Road Mumbai", "pin": "400001", "gstin": "27AABCM1111H1Z1", "bank": "ICICI Bank", "branch": "Mumbai Andheri", "ifsc": "ICIC0001234", "acct": "011234567890", "district": 225, "district_name": "Mumbai", "taluka": 12828, "taluka_name": "Haveli"},
    {"name": "Godavari Fisheries Pvt Ltd", "ownership": 7, "sale": 1267, "supply": 225, "email": "godavari.fish@mail.in", "phone": "9823111009", "pan": "AABCG2222I", "address": "67 Port Road Thane", "pin": "400601", "gstin": "27AABCG2222I1Z9", "bank": "Kotak Mahindra Bank", "branch": "Thane Branch", "ifsc": "KKBK0001234", "acct": "821234567890", "district": 240, "district_name": "Thane", "taluka": 12979, "taluka_name": "Pune City"},
    {"name": "Deccan Sugar and Allied Products", "ownership": 6, "sale": 1265, "supply": 225, "email": "deccan.sugar@mail.in", "phone": "9823111010", "pan": "AABCD3333J", "address": "89 Factory Road Solapur", "pin": "413001", "gstin": "27AABCD3333J1Z7", "bank": "Axis Bank", "branch": "Solapur Branch", "ifsc": "UTIB0001234", "acct": "911234567890", "district": 239, "district_name": "Solapur", "taluka": 12792, "taluka_name": "Daund"},
    {"name": "Tapi Valley Organics", "ownership": 5, "sale": 1264, "supply": 225, "email": "tapi.organics@mail.in", "phone": "9823111011", "pan": "AABCT4444K", "address": "34 Textile Lane Jalgaon", "pin": "425001", "gstin": "27AABCT4444K1Z5", "bank": "Central Bank of India", "branch": "Jalgaon Branch", "ifsc": "CBIN0001234", "acct": "301234567890", "district": 221, "district_name": "Jalgaon", "taluka": 12834, "taluka_name": "Indapur"},
    {"name": "Sindhudurg Coconut Products", "ownership": 5, "sale": 1266, "supply": 225, "email": "sindhudurg.coco@mail.in", "phone": "9823111012", "pan": "AABCS5555L", "address": "56 Beach Road Sindhudurg", "pin": "416510", "gstin": "27AABCS5555L1Z3", "bank": "Dena Bank", "branch": "Sindhudurg Branch", "ifsc": "BKDN0001234", "acct": "461234567890", "district": 238, "district_name": "Sindhudurg", "taluka": 12847, "taluka_name": "Junnar"},
    {"name": "Marathwada Poultry Farm", "ownership": 5, "sale": 1266, "supply": 225, "email": "marathwada.poul@mail.in", "phone": "9823111013", "pan": "AABCM6666M", "address": "78 Chikalthana Chhatrapati Sambhajinagar", "pin": "431001", "gstin": "27AABCM6666M1Z1", "bank": "Bank of Baroda", "branch": "Chhatrapati Sambhajinagar Branch", "ifsc": "BARB0001234", "acct": "371234567890", "district": 215, "district_name": "Chhatrapati Sambhajinagar", "taluka": 13019, "taluka_name": "Shirur"},
    {"name": "Vidarbha Soy Processing LLP", "ownership": 9, "sale": 1265, "supply": 225, "email": "vidarbha.soy@mail.in", "phone": "9823111014", "pan": "AABCV7777N", "address": "45 CIDCO Amravati", "pin": "444001", "gstin": "27AABCV7777N1Z9", "bank": "Indian Bank", "branch": "Amravati Branch", "ifsc": "IDIB0001234", "acct": "621234567890", "district": 210, "district_name": "Amravati", "taluka": 13058, "taluka_name": "Velhe"},
    {"name": "Konkan Cashew Industries", "ownership": 7, "sale": 1264, "supply": 225, "email": "konkan.cashew@mail.in", "phone": "9823111015", "pan": "AABCK8888O", "address": "23 Market Yard Raigad", "pin": "402001", "gstin": "27AABCK8888O1Z7", "bank": "Federal Bank", "branch": "Raigad Branch", "ifsc": "FDRL0001234", "acct": "141234567891", "district": 234, "district_name": "Raigad", "taluka": 12980, "taluka_name": "Purandhar"},
    {"name": "Malwa Trading Company", "ownership": 5, "sale": 1267, "supply": 223, "email": "malwa.trade@mail.in", "phone": "9823111016", "pan": "AABCM9999P", "address": "67 IT Park Nagpur", "pin": "440015", "gstin": "27AABCM9999P1Z5", "bank": "Yes Bank", "branch": "Nagpur IT Park", "ifsc": "YESB0001234", "acct": "781234567890", "district": 227, "district_name": "Nagpur", "taluka": 12765, "taluka_name": "Bhor"},
    {"name": "Panchganga Dairy Products", "ownership": 6, "sale": 1266, "supply": 225, "email": "panchganga.dairy@mail.in", "phone": "9823111017", "pan": "AABCP1010Q", "address": "89 Dairy Road Sangli", "pin": "416416", "gstin": "27AABCP1010Q1Z3", "bank": "UCO Bank", "branch": "Sangli Branch", "ifsc": "UCBA0001234", "acct": "261234567890", "district": 236, "district_name": "Sangli", "taluka": 12916, "taluka_name": "Mawal"},
    {"name": "Sahyadri Fruit Processors", "ownership": 7, "sale": 1266, "supply": 225, "email": "sahyadri.fruit@mail.in", "phone": "9823111018", "pan": "AABCS2020R", "address": "12 Industrial Estate Nashik", "pin": "422011", "gstin": "27AABCS2020R1Z1", "bank": "IndusInd Bank", "branch": "Nashik Industrial", "ifsc": "INDB0001234", "acct": "921234567890", "district": 230, "district_name": "Nashik", "taluka": 12876, "taluka_name": "Khed"},
    {"name": "Chandrapur Mining Supplies", "ownership": 5, "sale": 1265, "supply": 225, "email": "chandrapur.mine@mail.in", "phone": "9823111019", "pan": "AABCC3030S", "address": "56 Station Road Chandrapur", "pin": "442401", "gstin": "27AABCC3030S1Z9", "bank": "Indian Overseas Bank", "branch": "Chandrapur Branch", "ifsc": "IOBA0001234", "acct": "181234567890", "district": 214, "district_name": "Chandrapur", "taluka": 13019, "taluka_name": "Shirur"},
]

success = 0
fail = 0

for i, c in enumerate(customers, 1):
    payload = {
        "id": "",
        "party_ref_id": "",
        "ownership_status_ref_id": c["ownership"],
        "name": c["name"],
        "supply_type_ref_id": c["supply"],
        "sale_type_ref_id": c["sale"],
        "default_currency_ref_id": 1,
        "email_id": c["email"],
        "mobile_no": c["phone"],
        "pan_no": c["pan"],
        "status": True,
        "children": [
            {
                "display_name_as": "",
                "office_no": "",
                "preferred_payment_method_ref_id": "",
                "gst_registration_type": "",
                "payment_terms_ref_id": "",
                "delivery_terms_ref_id": "",
                "mode_of_delivery_ref_id": "",
                "courier_terms_ref_id": "",
                "deposit": 0,
                "quantity_tolerance": "",
                "rate_tolerance": "",
                "is_tds_applicable": False,
                "stepper_name": "Additional Details",
                "children": [],
                "details": [],
                "id": ""
            },
            {
                "stepper_name": "Customer Details",
                "children": [],
                "details": [
                    {
                        "same_as_above": "",
                        "address_type": 43,
                        "country_ref_id_id": 8,
                        "state_ref_id_id": 101,
                        "district_ref_id_id": c["district"],
                        "sub_district_ref_id_id": c["taluka"],
                        "village_ref_id_id": "",
                        "address": c["address"],
                        "pin_code": c["pin"],
                        "gstin": c["gstin"],
                        "id": ""
                    }
                ],
                "id": ""
            },
            {
                "stepper_name": "Customer Bank Details",
                "children": [],
                "details": [
                    {
                        "bank_name": c["bank"],
                        "bank_branch_code": c["branch"],
                        "bank_ifsc_code": c["ifsc"],
                        "account_type": 1849,
                        "bank_account_holder_name": c["name"],
                        "bank_account_no": c["acct"],
                        "bank_doc_id": 36,
                        "bank_attachment_path": "",
                        "id": ""
                    }
                ],
                "id": ""
            }
        ],
        "attribute_name": "Customer"
    }
    
    body_json = json.dumps(payload)
    
    result = subprocess.run(
        ["curl", "-s", "-w", "\\n%{http_code}", "-X", "POST", URL,
         "-H", f"Authorization: Bearer {TOKEN}",
         "-H", f"X-Tenant-ID: {TENANT}",
         "-H", "Content-Type: application/json",
         "-d", body_json,
         "--insecure"],
        capture_output=True, text=True, timeout=15
    )
    
    http_code = result.stdout.strip().split("\n")[-1]
    
    if http_code in ("201", "200"):
        print(f"✅ {i:2d}. {c['name']}")
        success += 1
    else:
        # Try to get error message
        lines = result.stdout.strip().split("\n")
        err = lines[0][:80] if len(lines) > 1 else http_code
        print(f"❌ {i:2d}. {c['name']} (HTTP {http_code}: {err})")
        fail += 1

print(f"\nDone! ✅ Success: {success} | ❌ Failed: {fail}")
