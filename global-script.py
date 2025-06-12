import requests
import json

# === Step 1: Authenticate and retrieve bearer token ===
auth_url = "https://xrp-flex-partners.cegid.cloud/lebeltechnologies_23r2/identity/connect/token"

auth_payload = {
    'grant_type': 'password',
    'username': 'Sylvain',
    'password': 'Cegid+@+2025',
    'client_id': '50FF99B1-BC0F-8CB1-0B5E-2D37329EE4C5@DEVELOPPEMENT',
    'client_secret': 'CQJxmsPCsgl4HVWw261krw',
    'scope': 'api offline_access'
}

auth_headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

auth_response = requests.post(auth_url, headers=auth_headers, data=auth_payload)

if auth_response.status_code != 200:
    print("Authentication failed:", auth_response.text)
    exit()

token = auth_response.json().get("access_token")
if not token:
    print("No access token found in the response.")
    exit()

print("Authenticated successfully. Access token obtained.")

get_url = "https://xrp-flex-partners.cegid.cloud/lebeltechnologies_23r2/entity/DefaultExtended/23.200.001/Vendor"

get_headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json'
}

response = requests.get(get_url, headers=get_headers)

if response.status_code != 200:
    print("Failed to fetch vendors:", response.text)
    exit()

vendors = response.json()

vendor_list = []
for vendor in vendors:
    print(json.dumps(vendor, indent=4))
    vendor_list.append(vendor.get('Vendor'))
    vendor_id = vendor.get("VendorID", {}).get("value", "")
    legal_name = vendor.get("LegalName", {}).get("value", "")
    vendor_list.append({"VendorID": vendor_id, "LegalName": legal_name})

print(json.dumps(vendor_list, indent=2, ensure_ascii=False))


# === Step 2: Send the PUT request with bearer token ===
# put_url = "https://xrp-flex-partners.cegid.cloud/lebeltechnologies_23r2/entity/DefaultExtended/23.200.001/Bill"
#
# put_payload = {
#     "Type": {"value": "Bill"},
#     "Status": {"value": "On Hold"},
#     "Date": {"value": "2025-06-02T00:00:00Z"},
#     "PostPeriod": {"value": "062025"},
#     "VendorRef": {"value": "Vendor ref 06 2025"},
#     "Description": {"value": "Payment of june 2025"},
#     "ApprovedForPayment": {"value": False},
#     "Vendor": {"value": "EL ROBRINI"},
#     "LocationID": {"value": "PRINCIPAL"},
#     "CurrencyID": {"value": "EUR"},
#     "Terms": {"value": "30J"},
#     "DueDate": {"value": "2023-11-01T00:00:00+00:00"},
#     "Hold": {"value": True},
#     "Details": [
#         {
#             "Branch": {"value": "LT"},
#             "InventoryID": {"value": "AT"},
#             "TransactionDescription": {"value": "Assistance Technique"},
#             "Qty": {"value": 20.0},
#             "UOM": {"value": "JOUR"},
#             "UnitCost": {"value": 500.0},
#             "ExtendedCost": {"value": 10000.0},
#             "CalculateDiscountsOnImport": {},
#             "Amount": {"value": 10000.0},
#             "Account": {"value": "604000"},
#             "Description": {"value": "Achats d'études & prest. services"},
#             "Subaccount": {"value": "A1005A2005000"},
#             "Project": {"value": "FFORMATCEGID PR00"},
#             "ProjectTask": {"value": "PHASEUNIT"},
#             "NonBillable": {"value": False},
#             "TaxCategory": {"value": "2000"}
#         },
#         {
#             "Branch": {"value": "LT"},
#             "InventoryID": {"value": "AT"},
#             "TransactionDescription": {"value": "Assistance Technique sec row"},
#             "Qty": {"value": 20.0},
#             "UOM": {"value": "JOUR"},
#             "UnitCost": {"value": 500.0},
#             "ExtendedCost": {"value": 10000.0},
#             "CalculateDiscountsOnImport": {},
#             "Amount": {"value": 10000.0},
#             "Account": {"value": "604000"},
#             "Description": {"value": "Achats d'études & prest. services"},
#             "Subaccount": {"value": "A1005A2005000"},
#             "Project": {"value": "FFORMATCEGID PR00"},
#             "ProjectTask": {"value": "PHASEUNIT"},
#             "NonBillable": {"value": False},
#             "TaxCategory": {"value": "2000"}
#         }
#     ]
# }
#
# put_headers = {
#     'Content-Type': 'application/json; charset=utf-8',
#     'Authorization': f'Bearer {token}'
# }
#
# # Convert payload to JSON string
# put_response = requests.put(put_url, headers=put_headers, data=json.dumps(put_payload))
#
# print("PUT request response:")
# print(put_response.status_code)
# print(put_response.text)
