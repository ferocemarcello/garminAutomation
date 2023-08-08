import json

import gspread


class GoogleOauth:
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self, credentials_path):
        self.client, authorized_user = gspread.oauth_from_dict(credentials=json.load(open(credentials_path)),
                                                               scopes=GoogleOauth.scopes)

    def get_all_values_sheet(self, sheet_id: str):
        return self.client.open_by_key(sheet_id).get_worksheet(0).get_all_values()

    def fill_dates(self, interval_data):
        pass
