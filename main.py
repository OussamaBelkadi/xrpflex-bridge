# import json
# import os
# import csv
# import time
# from datetime import datetime
#
# import paramiko
# import platform
# import requests
# from dotenv import load_dotenv
# from io import StringIO
# from typing import List, Dict, Any, Optional
#
# class InvoiceDataProcessor:
#     def __init__(self):
#         load_dotenv()
#         self.host = os.getenv('SFTP_HOST')
#         self.username = os.getenv('SFTP_USER')
#         self.password = os.getenv('SFTP_PASSWORD')
#         self.file_path = os.getenv('FILE_PATH')
#         self.is_windows = platform.system() == 'Windows'
#
#         # Configuration d'authentification
#         self.auth_url = "https://xrp-flex-partners.cegid.cloud/lebeltechnologies_23r2/identity/connect/token"
#         self.auth_payload = {
#             'grant_type': 'password',
#             'username': 'Sylvain',
#             'password': 'Cegid+@+2025',
#             'client_id': '50FF99B1-BC0F-8CB1-0B5E-2D37329EE4C5@DEVELOPPEMENT',
#             'client_secret': 'CQJxmsPCsgl4HVWw261krw',
#             'scope': 'api offline_access'
#         }
#         self.auth_headers = {
#             'Content-Type': 'application/x-www-form-urlencoded'
#         }
#
#         self.token = None
#         self.token_expiration = 0
#         self.token_refresh_interval = 3000  # 4 minutes en secondes
#
#         self.column_mapping = {
#             'Code Fournisseur': {'index': 0, 'default': None},
#             'Numéro Facture': {'index': 2, 'default': None},
#             'Date de facture': {'index': 3, 'default': None},
#             'Désignation': {'index': 4, 'default': None},
#             'Quantité': {'index': 5, 'default': '0'},
#             'Unité': {'index': 6, 'default': None},
#             'Coût Unitaire': {'index': 7, 'default': '0'},
#             'Coût Total HT': {'index': 8, 'default': '0'}
#         }
#
#         self.data_table = []
#         self.error_messages = []
#
#     def add_error(self, message: str):
#         timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
#         self.error_messages.append(f"{timestamp} - {message}")
#
#     def normalize_path(self, path: str) -> str:
#         if self.is_windows:
#             path = path.replace('\\', '/')
#             path = path.replace('C:', '/cygdrive/c')
#             return '/' + path if not path.startswith('/') else path
#         return path
#
#     def get_safe_value(self, row: List[str], column_name: str) -> Any:
#         if column_name in self.column_mapping:
#             index = self.column_mapping[column_name]['index']
#             return row[index].strip() if index < len(row) else self.column_mapping[column_name]['default']
#         self.add_error(f"Invalid column name: {column_name}")
#         return None
#
#     def authenticate(self) -> bool:
#         """Authentification et récupération du token"""
#         try:
#             auth_response = requests.post(
#                 self.auth_url,
#                 headers=self.auth_headers,
#                 data=self.auth_payload
#             )
#
#             if auth_response.status_code != 200:
#                 self.add_error(f"Authentication failed: {auth_response.text}")
#                 return False
#
#             response_data = auth_response.json()
#             self.token = response_data.get("access_token")
#             print(self.token);
#             expires_in = response_data.get("expires_in", self.token_refresh_interval)
#
#             if not self.token:
#                 self.add_error("No access token found in the response.")
#                 return False
#
#             self.token_expiration = time.time() + expires_in
#             return True
#
#         except requests.exceptions.RequestException as e:
#             self.add_error(f"Authentication error: {str(e)}")
#             return False
#
#     def is_token_valid(self) -> bool:
#         """Vérifie si le token est toujours valide"""
#         return self.token is not None and time.time() < self.token_expiration
#
#     def get_auth_header(self) -> Optional[Dict[str, str]]:
#         """Obtient l'en-tête d'authentification, rafraîchit le token si nécessaire"""
#         if not self.is_token_valid():
#             if not self.authenticate():
#                 return None
#         return {"Authorization": f"Bearer {self.token}"}
#
#     def call_api(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
#         """Appel API avec authentification automatique"""
#         headers = self.get_auth_header()
#         if not headers:
#             return None
#
#         try:
#             url = f"https://xrp-flex-partners.cegid.cloud/lebeltechnologies_23r2/{endpoint}"
#             if method.upper() == "GET":
#                 response = requests.get(url, headers=headers)
#             elif method.upper() == "POST":
#                 response = requests.post(url, headers=headers, json=data)
#             else:
#                 self.add_error(f"Unsupported HTTP method: {method}")
#                 return None
#
#             response.raise_for_status()
#             return response.json()
#
#         except requests.exceptions.RequestException as e:
#             self.add_error(f"API call failed: {str(e)}")
#             return None
#
#     def read_and_process_file(self) -> bool:
#         """Lecture et traitement du fichier"""
#         self.data_table = []
#         self.error_messages = []
#
#         if not all([self.host, self.username, self.password, self.file_path]):
#             self.add_error("Missing required connection parameters")
#             return False
#
#         ssh = paramiko.SSHClient()
#         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#
#         try:
#             normalized_path = self.normalize_path(self.file_path)
#             ssh.connect(hostname=self.host, username=self.username, password=self.password)
#
#             with ssh.open_sftp() as sftp:
#                 with sftp.file(normalized_path, 'rb') as remote_file:
#                     content = remote_file.read().decode('utf-8', errors='ignore')
#
#                 csv_data = StringIO(content.replace(';', ','))
#                 reader = csv.reader(csv_data)
#
#                 header = next(reader)
#                 for row in reader:
#                     structured_row = {
#                         'Code Fournisseur': self.get_safe_value(row, 'Code Fournisseur'),
#                         'Numéro Facture': self.get_safe_value(row, 'Numéro Facture'),
#                         'Date de facture': self.get_safe_value(row, 'Date de facture'),
#                         'Désignation': self.get_safe_value(row, 'Désignation'),
#                         'Quantité': self.get_safe_value(row, 'Quantité'),
#                         'Unité': self.get_safe_value(row, 'Unité'),
#                         'Coût Unitaire': self.get_safe_value(row, 'Coût Unitaire'),
#                         'Coût Total HT': self.get_safe_value(row, 'Coût Total HT')
#                     }
#                     self.data_table.append(structured_row)
#
#                 return True
#
#         except Exception as e:
#             self.add_error(f"Unexpected error: {str(e)}")
#             return False
#         finally:
#             ssh.close()
#
#     def print_all_rows(self):
#         """Affichage des données"""
#         if self.data_table:
#             print(f"{'Code Fournisseur':<15} | {'Numéro Facture':<12} | {'Date de facture':<15} | "
#                   f"{'Désignation':<30} | {'Quantité':<8} | {'Unité':<6} | "
#                   f"{'Coût Unitaire':<12} | {'Coût Total HT':<10}")
#             print("-" * 120)
#             for row in self.data_table:
#                 print(f"{row.get('Code Fournisseur', ''):<15} | {row.get('Numéro Facture', ''):<12} | "
#                       f"{row.get('Date de facture', ''):<15} | {row.get('Désignation', ''):<30} | "
#                       f"{row.get('Quantité', ''):<8} | {row.get('Unité', ''):<6} | "
#                       f"{row.get('Coût Unitaire', ''):<12} | {row.get('Coût Total HT', ''):<10}")
#         else:
#             print("No data available to display")
#
#     def create_payload(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
#         """Creates the payload for the PUT request based on the invoice data."""
#         current_date = datetime.now().isoformat() + "Z"
#
#         quantity = float(invoice['Quantité']) if invoice['Quantité'] else 0
#         unit_cost = float(invoice['Coût Unitaire']) if invoice['Coût Unitaire'] else 0
#
#         # Calculate ExtendedCost
#         extended_cost = quantity * unit_cost
#
#         payload = {
#             "Type": {"value": "Bill"},
#             "Status": {"value": "On Hold"},
#             "Date": {"value": current_date},
#             "PostPeriod": {"value": (datetime.now().strftime('%m%Y'))},
#             "VendorRef": {"value": invoice['Code Fournisseur']},  # Mapping Code Fournisseur
#             "Description": {"value": invoice['Désignation']},  # Mapping Désignation
#             "ApprovedForPayment": {"value": False},
#             "Vendor": {"value": "EL ROBRINI"},  # Hardcoded for example
#             "LocationID": {"value": "PRINCIPAL"},
#             "CurrencyID": {"value": "EUR"},
#             "Terms": {"value": "30J"},
#             "DueDate": {"value": "2023-11-01T00:00:00+00:00"},  # Replace with dynamic due date if necessary
#             "Hold": {"value": True},
#             "Details": [
#                 {
#                     "Branch": {"value": "LT"},
#                     "InventoryID": {"value": "AT"},
#                     "TransactionDescription": {"value": invoice['Désignation']},  # Mapping Désignation
#                     "Qty": {"value": quantity},
#                     "UOM": {"value": invoice['Unité']},  # Mapping Unité
#                     "UnitCost": {"value": unit_cost},
#                     "ExtendedCost": {"value": extended_cost},
#                     "CalculateDiscountsOnImport": {},
#                     "Amount": {"value": extended_cost},  # Replace with total amount as necessary
#                     "Account": {"value": "604000"},
#                     "Description": {"value": "Achats d'études & prest. services"},  # Hardcoded for example
#                     "Subaccount": {"value": "A1005A2005000"},
#                     "Project": {"value": "FFORMATCEGID PR00"},
#                     "ProjectTask": {"value": "PHASEUNIT"},
#                     "NonBillable": {"value": False},
#                     "TaxCategory": {"value": "2000"}
#                 }
#             ]
#         }
#         return payload
#
#
#     # def process_invoices(self):
#     #     """Exemple de traitement des factures avec appel API"""
#     #     if not self.data_table:
#     #         self.add_error("No data to process")
#     #         return False
#     #
#     #     # Exemple d'appel API pour chaque facture
#     #     for invoice in self.data_table:
#     #         # Préparation des données pour l'API
#     #         api_data = {
#     #             "supplierCode": invoice['Code Fournisseur'],
#     #             "invoiceNumber": invoice['Numéro Facture'],
#     #             "invoiceDate": invoice['Date de facture'],
#     #             "description": invoice['Désignation'],
#     #             "quantity": invoice['Quantité'],
#     #             "unit": invoice['Unité'],
#     #             "unitCost": invoice['Coût Unitaire'],
#     #             "totalCost": invoice['Coût Total HT']
#     #         }
#     #
#     #         # Appel API pour envoyer la facture
#     #         response = self.call_api("api/invoices", "POST", api_data)
#     #         if response:
#     #             print(f"Successfully processed invoice {invoice['Numéro Facture']}")
#     #         else:
#     #             self.add_error(f"Failed to process invoice {invoice['Numéro Facture']}")
#     #
#     #     return True
#
#     def process_invoices(self):
#         def process_invoices(self):
#             """Example method to process invoices and send API requests."""
#             if not self.data_table:
#                 self.add_error("No data to process")
#                 return False
#
#             processed_vendors = set()  # Initialize a set to keep track of processed VendorRefs
#
#             for invoice in self.data_table:
#                 vendor_ref = invoice['Code Fournisseur']
#                 if vendor_ref in processed_vendors:
#                     print(f"Invoice for VendorRef {vendor_ref} has already been processed. Skipping.")
#                     continue
#
#                 # Create payload for the invoice
#                 payload = self.create_payload(invoice)
#
#                 # Print the generated payload
#                 print("Generated Payload:")
#                 print(json.dumps(payload, indent=4))  # Pretty print the JSON payload
#
#                 # Call API for sending the invoice
#                 put_response = requests.put(
#                     "your/api/endpoint/here",  # Update with your actual API endpoint
#                     headers={
#                         'Content-Type': 'application/json; charset=utf-8',
#                         'Authorization': f'Bearer {self.token}'  # Use the existing token
#                     },
#                     data=json.dumps(payload)  # Send the created payload
#                 )
#
#                 if put_response.status_code == 200:
#                     print(f"Successfully processed invoice {invoice['Numéro Facture']}")
#                     processed_vendors.add(vendor_ref)  # Add the vendor to the set after successful processing
#                 else:
#                     self.add_error(f"Failed to process invoice {invoice['Numéro Facture']}: {put_response.text}")
#
#             return True
#
#         # """Example method to process invoices and send API requests."""
#         # if not self.data_table:
#         #     self.add_error("No data to process")
#         #     return False
#         #
#         # # API call for each invoice
#         # for invoice in self.data_table:
#         #     # Create payload for the invoice
#         #     payload = self.create_payload(invoice)
#         #
#         #     # Print the generated payload
#         #     print("Generated Payload:")
#         #     print(json.dumps(payload, indent=4))  # Pretty print the JSON payload
#
#             # Call API for sending the invoice
#             # put_response = requests.put(
#             #     "your/api/endpoint/here",  # Update with your actual API endpoint
#             #     headers={
#             #         'Content-Type': 'application/json; charset=utf-8',
#             #         'Authorization': f'Bearer {self.token}'  # Use the existing token
#             #     },
#             #     data=json.dumps(payload)  # Send the created payload
#             # )
#
#             # if put_response.status_code == 200:
#             #     print(f"Successfully processed invoice {invoice['Numéro Facture']}")
#             # else:
#             #     self.add_error(f"Failed to process invoice {invoice['Numéro Facture']}: {put_response.text}")
#
#         return True
#
# if __name__ == "__main__":
#     processor = InvoiceDataProcessor()
#
#     # Première authentification
#     if not processor.authenticate():
#         print("Initial authentication failed:")
#         for error in processor.error_messages:
#             print(error)
#         exit(1)
#
#     while True:
#         # Lecture et traitement du fichier
#         success = processor.read_and_process_file()
#
#         if success:
#             print("Data processing successful!")
#             processor.print_all_rows()
#
#             # Traitement des factures avec appel API
#             if processor.process_invoices():
#                 print("Invoices processed successfully via API")
#             else:
#                 print("Failed to process some invoices via API")
#                 for error in processor.error_messages:
#                     print(error)
#         else:
#             print("Failed to process the file")
#             for error in processor.error_messages:
#                 print(error)
#
#         # Vérification et rafraîchissement du token si nécessaire
#         if not processor.is_token_valid():
#             print("Token expired, re-authenticating...")
#             if not processor.authenticate():
#                 print("Re-authentication failed")
#                 break
#
#         time.sleep(5)  # Pause de 5 secondes avant la prochaine itération
import json
import os
import csv
from collections import defaultdict
import random
import string
import time
from datetime import datetime
from textwrap import indent

import paramiko
import platform
import requests
from dotenv import load_dotenv
from io import StringIO
from typing import List, Dict, Any, Optional

class InvoiceDataProcessor:
    def __init__(self):
        load_dotenv()
        self.host = os.getenv('SFTP_HOST')
        self.username = os.getenv('SFTP_USER')
        self.password = os.getenv('SFTP_PASSWORD')
        self.file_path = os.getenv('FILE_PATH')
        self.is_windows = platform.system() == 'Windows'

        # Authentication configuration
        self.auth_url = "https://xrp-flex-partners.cegid.cloud/lebeltechnologies_23r2/identity/connect/token"
        self.auth_payload = {
            'grant_type': 'password',
            'username': 'Sylvain',
            'password': 'Cegid+@+2025',
            'client_id': '50FF99B1-BC0F-8CB1-0B5E-2D37329EE4C5@DEVELOPPEMENT',
            'client_secret': 'CQJxmsPCsgl4HVWw261krw',
            'scope': 'api offline_access'
        }
        self.auth_headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        self.token = None
        self.token_expiration = 0

        self.column_mapping = {
            'Code Fournisseur': {'index': 0, 'default': None},
            'Numéro Facture': {'index': 2, 'default': None},
            'Date de facture': {'index': 3, 'default': None},
            'Désignation': {'index': 4, 'default': None},
            'Quantité': {'index': 5, 'default': '0'},
            'Unité': {'index': 6, 'default': None},
            'Coût Unitaire': {'index': 7, 'default': '0'},
            'Coût Total HT': {'index': 8, 'default': '0'}
        }

        self.data_table = []
        self.error_messages = []

    def add_error(self, message: str):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.error_messages.append(f"{timestamp} - {message}")

    def normalize_path(self, path: str) -> str:
        if self.is_windows:
            path = path.replace('\\', '/')
            path = path.replace('C:', '/cygdrive/c')
            return '/' + path if not path.startswith('/') else path
        return path

    def get_safe_value(self, row: List[str], column_name: str) -> Any:
        if column_name in self.column_mapping:
            index = self.column_mapping[column_name]['index']
            return row[index].strip() if index < len(row) else self.column_mapping[column_name]['default']
        self.add_error(f"Invalid column name: {column_name}")
        return None

    def authenticate(self) -> bool:
        """Authenticate and retrieve the token."""
        try:
            auth_response = requests.post(
                self.auth_url,
                headers=self.auth_headers,
                data=self.auth_payload
            )

            if auth_response.status_code != 200:
                self.add_error(f"Authentication failed: {auth_response.text}")
                return False

            response_data = auth_response.json()
            self.token = response_data.get("access_token")

            if not self.token:
                self.add_error("No access token found in the response.")
                return False

            self.token_expiration = time.time() + response_data.get("expires_in", 3600)  # Default to 1 hour
            return True

        except requests.exceptions.RequestException as e:
            self.add_error(f"Authentication error: {str(e)}")
            return False

    def is_token_valid(self) -> bool:
        """Check if the token is still valid."""
        return self.token is not None and time.time() < self.token_expiration

    def get_auth_header(self) -> Optional[Dict[str, str]]:
        """Get the authentication header, refresh the token if necessary."""
        if not self.is_token_valid():
            if not self.authenticate():
                return None
        return {"Authorization": f"Bearer {self.token}"}

    def call_api(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """API call with automatic authentication."""
        headers = self.get_auth_header()
        if not headers:
            return None

        try:
            url = f"https://xrp-flex-partners.cegid.cloud/lebeltechnologies_23r2/{endpoint}"
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                self.add_error(f"Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            self.add_error(f"API call failed: {str(e)}")
            return None

    def read_and_process_file(self) -> bool:
        """Read and process the CSV file from SFTP."""
        self.data_table = []
        self.error_messages = []

        if not all([self.host, self.username, self.password, self.file_path]):
            self.add_error("Missing required connection parameters")
            return False

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            normalized_path = self.normalize_path(self.file_path)
            ssh.connect(hostname=self.host, username=self.username, password=self.password)

            with ssh.open_sftp() as sftp:
                with sftp.file(normalized_path, 'rb') as remote_file:
                    content = remote_file.read().decode('utf-8', errors='ignore')

                csv_data = StringIO(content.replace(';', ','))
                reader = csv.reader(csv_data)

                header = next(reader)
                for row in reader:
                    structured_row = {
                        'Code Fournisseur': self.get_safe_value(row, 'Code Fournisseur'),
                        'Numéro Facture': self.get_safe_value(row, 'Numéro Facture'),
                        'Date de facture': self.get_safe_value(row, 'Date de facture'),
                        'Désignation': self.get_safe_value(row, 'Désignation'),
                        'Quantité': self.get_safe_value(row, 'Quantité'),
                        'Unité': self.get_safe_value(row, 'Unité'),
                        'Coût Unitaire': self.get_safe_value(row, 'Coût Unitaire'),
                        'Coût Total HT': self.get_safe_value(row, 'Coût Total HT')
                    }
                    self.data_table.append(structured_row)
                print(self.data_table)

                return True

        except Exception as e:
            self.add_error(f"Unexpected error: {str(e)}")
            return False
        finally:
            ssh.close()

    def print_all_rows(self):
        """Display the data."""
        if self.data_table:
            print(f"{'Code Fournisseur':<15} | {'Numéro Facture':<12} | {'Date de facture':<15} | "
                  f"{'Désignation':<30} | {'Quantité':<8} | {'Unité':<6} | "
                  f"{'Coût Unitaire':<12} | {'Coût Total HT':<10}")
            print("-" * 120)
            for row in self.data_table:
                print(f"{row.get('Code Fournisseur', ''):<15} | {row.get('Numéro Facture', ''):<12} | "
                      f"{row.get('Date de facture', ''):<15} | {row.get('Désignation', ''):<30} | "
                      f"{row.get('Quantité', ''):<8} | {row.get('Unité', ''):<6} | "
                      f"{row.get('Coût Unitaire', ''):<12} | {row.get('Coût Total HT', ''):<10}")
        else:
            print("No data available to display")

    def create_payload(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Creates the payload for the PUT request based on the invoice data."""

        current_date = "2025-06-02T00:00:00Z"
        details = []  # Initialize an empty list for details

        # Extract relevant data from the invoice
        quantity = float(invoice.get('Quantité', 0))  # Use .get() to avoid KeyError
        unit_cost = float(invoice.get('Coût Unitaire', 0))  # Same here
        extended_cost = quantity * unit_cost

        # Create the detail entry directly from the invoice keys
        detail = {
            "Branch": {"value": "LT"},
            "InventoryID": {"value": "AT"},  # You can adjust this as needed
            "TransactionDescription": {"value": invoice.get('Désignation', "Assistance Technique")},
            "Qty": {"value": quantity},
            "UOM": {"value": "JOUR"},
            "UnitCost": {"value": unit_cost},
            "ExtendedCost": {"value": extended_cost},
            "CalculateDiscountsOnImport": {},
            "Amount": {"value": extended_cost},
            "Account": {"value": "604000"},
            "Description": {"value": "Achats d'études & prest. services"},
            "Subaccount": {"value": "A1005A2005000"},
            "Project": {"value": "A000000000000?"},  # Adjust as needed
            "NonBillable": {"value": False},
            "TaxCategory": {"value": "2000"},
        }
        details.append(detail)  # Append the single detail entry

        # Construct the payload
        payload = {
            "Type": {"value": "Bill"},
            "Status": {"value": "On Hold"},
            "Date": {"value": current_date},
            "PostPeriod": {"value": "062025"},  # Adjust as necessary
            "VendorRef": {"value": invoice.get('Code Fournisseur')},  # Use .get() for safety
            "Description": {"value": invoice.get('Désignation')},  # Ensure this retrieves the correct description
            "ApprovedForPayment": {"value": False},
            "Vendor": {"value": "EL ROBRINI"},  # Adjust this as necessary
            "Hold": {"value": True},
            "Details": details
        }

        return payload

    def fetch_vendors(self):
        get_url = "https://xrp-flex-partners.cegid.cloud/lebeltechnologies_23r2/entity/DefaultExtended/23.200.001/Vendor"
        get_headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json'
        }

        response = requests.get(get_url, headers=get_headers)

        if response.status_code != 200:
            print("Failed to fetch vendors:", response.text)
            exit()

        vendors = response.json()
        vendor_list = []

        for vendor in vendors:
            # print(json.dumps(vendor, indent=4))
            # Create a set of vendor references for easy lookup
            legal_name = vendor.get("LegalName", {}).get("value", "")
            vendor_list.append(legal_name)
        print(vendor_list)
        return vendor_list

    def process_invoices(self):
        """Process invoices and send API requests."""
        global ref_facture
        if not self.data_table:
            self.add_error("No data to process")
            return False

        processed_vendors = processor.fetch_vendors()
        invoices_by_number = defaultdict(list)  # Group invoices by Numéro Facture
        characters = string.ascii_letters + string.digits
        # Group the invoices by Numéro Facture
        for invoice in self.data_table:
            num_facture = invoice['Numéro Facture']
            invoices_by_number[num_facture].append(invoice)

        # Process each group of invoices
        for num_facture, invoices in invoices_by_number.items():
            first_invoice = invoices[0]  # Use the first invoice to get common fields
            vendor_ref = first_invoice['Code Fournisseur']

            # if vendor_ref not in processed_vendors:
            #     print(f"Invoice for VendorRef {vendor_ref} not exist.")
            #     continue

            # Create payload using the combined details from grouped invoices
            details = []
            for invoice in invoices:
                quantity = float(invoice.get('Quantité', 0))
                unit_cost = float(invoice.get('Coût Unitaire', 0))
                ref_facture = invoice.get('Numéro Facture', 0)
                extended_cost = quantity * unit_cost
                date = invoice.get('Date de facture', 0)
                date_object = datetime.strptime(date, "%d/%m/%Y")
                detail = {
                    "Branch": {"value": "LT"},
                    "InventoryID": {"value": "AT"},
                    "TransactionDescription": {"value": invoice.get('Désignation', "Prestation de service")},
                    "Qty": {"value": quantity},
                    "UOM": {"value": "JOUR"},
                    "UnitCost": {"value": unit_cost},
                    "ExtendedCost": {"value": extended_cost},
                    "CalculateDiscountsOnImport": {},
                    "Amount": {"value": extended_cost},
                    "Account": {"value": "604000"},
                    "Description": {"value": "Achats d'études & prest. services"},
                    "Subaccount": {"value": "A1005A2005000"},
                    "Project": {"value": "A000000000000?"},  # Adjust as needed
                    "NonBillable": {"value": False},
                    "TaxCategory": {"value": "2000"},
                }
                details.append(detail)  # Collect details for this invoice

            # Construct the complete payload
            payload = {
                "Type": {"value": "Bill"},
                "Status": {"value": "On Hold"},
                "Date": {"value": date_object.strftime("%Y-%m-%dT00:00:00Z")},
                "PostPeriod": {"value": "062025"},  # Adjust as necessary
                "VendorRef": {"value": ref_facture},  # Use common vendor code
                "Description": {"value": first_invoice.get('Désignation')},  # Use the first invoice's description
                "ApprovedForPayment": {"value": False},
                "Vendor": {"value": "EL ROBRINI"},  # Adjust this as necessary
                "Hold": {"value": True},
                "Details": details
            }
            print(payload, indent=0)
            # Send API request
            put_response = requests.put(
                "https://xrp-flex-partners.cegid.cloud/lebeltechnologies_23r2/entity/DefaultExtended/23.200.001/Bill",
                headers={
                    'Content-Type': 'application/json; charset=utf-8',
                    'Authorization': f'Bearer {self.token}'
                },
                data=json.dumps(payload)
            )
            if put_response.status_code == 200:
                print(f"Successfully processed invoice {num_facture}")
            else:
                print(put_response.status_code)
                print(put_response.text)
                pass

        return True

if __name__ == "__main__":
    processor = InvoiceDataProcessor()

    # Initial authentication
    if not processor.authenticate():
        print("Initial authentication failed:")
        for error in processor.error_messages:
            print(error)
        exit(1)

    while True:
        # Read and process the file
        success = processor.read_and_process_file()
        if success:
            print("Data processing successful!")
            # processor.print_all_rows()

            # Process invoices with API calls
            if processor.process_invoices():
                print("Invoices processed successfully via API")
            else:
                print("Failed to process some invoices via API")
                for error in processor.error_messages:
                    print(error)
        else:
            print("Failed to process the file")
            for error in processor.error_messages:
                print(error)

        # Check and refresh the token if necessary
        if not processor.is_token_valid():
            print("Token expired, re-authenticating...")
            if not processor.authenticate():
                print("Re-authentication failed")
                break

        time.sleep(5)  # Pause for 5 seconds before the next iteration
