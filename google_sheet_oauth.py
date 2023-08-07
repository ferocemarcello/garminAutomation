import json

from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
import gspread


class GoogleOauth:
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    credentials = json.load(open("credentials/client_secret_oauth_desktop.json"))

    def __init__(self):
        self.client, authorized_user = gspread.oauth_from_dict(GoogleOauth.credentials)

    def get_all_values_sheet(self, sheet_id: str):
        return self.client.open_by_key(sheet_id).get_worksheet(0).get_all_values()
