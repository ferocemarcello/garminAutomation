import json

import gspread


class GoogleOauth:
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets'
    ]

    def __init__(self, credentials_path):
        self.client, authorized_user = gspread.oauth_from_dict(credentials=json.load(open(credentials_path)),
                                                               scopes=GoogleOauth.scopes)

    def get_all_values_sheet(self, sheet_id: str):
        return self.client.open_by_key(sheet_id).get_worksheet(0).get_all_values()

    def fill_data(self, interval_data: dict, sheet_id: str):
        self.fill_dates(interval_data.keys(), sheet_id=sheet_id)

    def fill_dates(self, dates, sheet_id: str):
        date_col = self.get_col(sheet_id=sheet_id, cell_val="Date")
        weight_col = self.get_col(sheet_id=sheet_id,cell_val="Weight")
        weights_list = self.client.open_by_key(sheet_id).get_worksheet(0).col_values(weight_col)
        dates_list = self.client.open_by_key(sheet_id).get_worksheet(0).col_values(date_col)
        pass

    def get_col(self, sheet_id: str, cell_val: str):
        return self.client.open_by_key(sheet_id).get_worksheet(0).find(cell_val).col

