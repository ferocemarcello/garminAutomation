import gspread


class GoogleClient:
    def __init__(self: str, credentials_file: str):
        self.client = gspread.service_account(filename=credentials_file)

    def write_dates(self, start_date, end_date):
        pass

    def get_all_values_sheet(self, sheet_id:str):
        return self.client.open_by_key(sheet_id).get_worksheet(0).get_all_values()

    def fill_dates(self, interval_data):
        pass
