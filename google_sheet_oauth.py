import datetime
import json
import string

import gspread


class GoogleOauth:
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets'
    ]

    def __init__(self, credentials_path: str, sheet_id: str):
        self.client, authorized_user = gspread.oauth_from_dict(credentials=json.load(open(credentials_path)),
                                                               scopes=GoogleOauth.scopes)
        self.worksheet = self.client.open_by_key(sheet_id).get_worksheet(0)

    def get_all_values_sheet(self):
        return self.worksheet.get_all_values()

    def fill_data(self, interval_data: dict):
        self.fill_dates([k for k in interval_data.keys()])

    def get_dates_between(self, start_date: datetime.date, end_date: datetime.date):
        """Gets an array of dates between two dates, excluding the first one and including the last one."""
        dates = []
        current_date = start_date + datetime.timedelta(days=1)
        while current_date <= end_date:
            if current_date != start_date:
                dates.append(current_date)
            current_date += datetime.timedelta(days=1)
        return dates

    def get_column_letter(self, row_number):
        """Gets the equivalent row letter for Google Sheet, from the row number."""
        alphabet = string.ascii_uppercase
        row_letters = []
        while row_number > 0:
            row_remainder = row_number % 26
            row_letters.append(alphabet[row_remainder - 1])
            row_number //= 26
        row_letters.reverse()
        return "".join(row_letters)

    def fill_dates(self, dates):
        date_col = self.get_col(cell_val="Date")
        weight_col = self.get_col(cell_val="Weight")
        weights_list = self.worksheet.col_values(weight_col)
        dates_list = self.worksheet.col_values(date_col)
        last_date = dates_list[-1]
        last_date_cell = self.worksheet.find(last_date)
        last_date_col = last_date_cell.col
        last_date_row = last_date_cell.row
        today = datetime.date.today()
        dates_between = [x.isoformat() for x in self.get_dates_between(datetime.date.fromisoformat(last_date), today)]
        cells_to_update_range = str(self.get_column_letter(last_date_col)) + str(last_date_row + 1) + ":" + \
                                str(self.get_column_letter(last_date_col)) + str(last_date_row + len(dates_between))
        self.worksheet.update(range_name=cells_to_update_range, values=[[x,] for x in dates_between])
        self.worksheet.format(cells_to_update_range, {'numberFormat': {"type": "DATE", "pattern": "yyyy-mm-dd"}})

    def get_col(self, cell_val: str):
        return self.worksheet.find(cell_val).col
