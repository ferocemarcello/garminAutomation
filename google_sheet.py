import gspread


class GoogleClient:
    def __init__(self: str, credentials_file: str):
        self.client = gspread.service_account(filename=credentials_file)

    def write_dates(self, start_date, end_date):
        pass

    def get_all_values_sheet(self, sheet_id:str):
        sheet = self.client.open_by_key(sheet_id)
        # Get the data from the sheet
        data = sheet.get_all_values()
        return data

    def fill_dates(self, interval_data):
        print(interval_data)
