import datetime
import sys
from download import Download
from google_sheet import GoogleSheet


def download_data(downloader: Download, start_date: datetime.date, end_date: datetime.date):
    """Download selected activity types from Garmin Connect and save the data in files. Overwrite previously
    downloaded data if indicated."""

    activity_types = downloader.activity_service_rest_client_pers.get(leaf_route='activityTypes', params=None).json()
    activities = downloader.get_activities(start_date=start_date, end_date=end_date)
    daily_summaries = downloader.get_daily_stats(start_date=start_date, end_date=end_date,
                                                 url_param_function=downloader.url_param_summary_day)
    hydration_days = downloader.get_daily_stats(start_date=start_date, end_date=end_date,
                                                url_param_function=downloader.url_param_hydration_day)
    # monitoring_days = downloader.get_daily_stats(date=start_date, days=count_days,
    # stat_function=downloader.get_monitoring_day)

    sleep_days = downloader.get_daily_stats(start_date=start_date, end_date=end_date,
                                            url_param_function=downloader.url_param_sleep_day)

    weight_days = downloader.get_daily_stats(start_date=start_date, end_date=end_date,
                                             url_param_function=downloader.url_param_weight_day)

    rhr_days = downloader.get_daily_stats(start_date=start_date, end_date=end_date,
                                          url_param_function=downloader.url_param_rhr_day)
    date_dict = {}
    return {"activity_types": activity_types, "activities": activities, "daily_summaries": daily_summaries,
            "hydration_days": hydration_days, "sleep_days": sleep_days, "weight_days": weight_days,
            "rhr_days": rhr_days}


def main(username=None, password=None, start_date: str = None, end_date: str = None, google_sheet_file: str = None):
    if None in [username, password, start_date, end_date, google_sheet_file]:
        sys.exit()
    g_sheet = GoogleSheet(google_sheet_file=google_sheet_file)
    g_sheet.write_dates(start_date, end_date)
    download_instance = Download()
    if not download_instance.login(username, password):
        sys.exit()
    interval_data = download_data(downloader=download_instance, start_date=datetime.date.fromisoformat(start_date),
                                  end_date=datetime.date.fromisoformat(end_date))
    g_sheet.fill_dates(interval_data)


if __name__ == "__main__":
    username_input = sys.argv[1]
    password_input = sys.argv[2]
    start_date_input = sys.argv[3]
    end_date_input = sys.argv[4]
    google_sheet_file_input = sys.argv[5]
    main(username=username_input, password=password_input, start_date=start_date_input, end_date=end_date_input, google_sheet_file=google_sheet_file_input)
