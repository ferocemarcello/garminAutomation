import gspread


class GoogleSheet:
    def __init__(self, google_sheet_file: str, credentials_file: str):
        self.sheet_id = google_sheet_file
        self.client = gspread.service_account(filename=credentials_file)

    def write_dates(self, start_date, end_date):
        pass

    def get_all_values(self):
        sheet = self.client.open_by_id(self.sheet_id)
        # Get the data from the sheet
        data = sheet.get_all_values()

    def fill_dates(self, interval_data):
        print(interval_data)
