import datetime
import sys
from download import Download
from google_sheet_oauth import GoogleOauth


def download_data(downloader: Download, start_date: datetime.date, end_date: datetime.date):
    """Download selected activity types from Garmin Connect and save the data in files. Overwrite previously
    downloaded data if indicated."""

    activity_types = downloader.activity_service_rest_client_pers.get(leaf_route='activityTypes', params=None).json()
    activities = downloader.get_activities(start_date=start_date, end_date=end_date)
    daily_summaries = downloader.get_daily_stats(start_date=start_date, end_date=end_date,
                                                 url_param_function=downloader.url_param_summary_day)
    '''hydration_days = downloader.get_daily_stats(start_date=start_date, end_date=end_date,
                                                url_param_function=downloader.url_param_hydration_day)
    '''
    sleep_days = downloader.get_daily_stats(start_date=start_date, end_date=end_date,
                                            url_param_function=downloader.url_param_sleep_day)

    weight_days = downloader.get_daily_stats(start_date=start_date, end_date=end_date,
                                             url_param_function=downloader.url_param_weight_day)

    rhr_days = downloader.get_daily_stats(start_date=start_date, end_date=end_date,
                                          url_param_function=downloader.url_param_rhr_day)
    date_dict = dict()
    delta = end_date - start_date
    for day in range(delta.days + 1):
        index_date = start_date + datetime.timedelta(days=day)
        date_dict[index_date] = dict()
        date_dict[index_date]["activities"] = \
            [item for item in activities.items()
             if datetime.datetime.strptime(item[1]["summaryDTO"]['startTimeLocal'],
                                           '%Y-%m-%dT%H:%M:%S.%f').date().__eq__(index_date)]
        date_dict[index_date]["summaries"] = next(item for item in daily_summaries if item["calendarDate"] ==
                                                  index_date.isoformat())
        date_dict[index_date]["sleep"] = next(item for item in sleep_days if item['dailySleepDTO']["calendarDate"] ==
                                              index_date.isoformat())
        date_dict[index_date]["weight"] = next(item for item in weight_days if item["startDate"] ==
                                               index_date.isoformat())
        date_dict[index_date]["rhr"] = next(item for item in rhr_days if item["statisticsStartDate"] ==
                                            index_date.isoformat())
    return date_dict


def main(username=None, password=None, start_date: str = None, end_date: str = None, google_sheet_file: str = None):
    if None in [username, password, start_date, end_date, google_sheet_file]:
        sys.exit()

    g_oauth = GoogleOauth(credentials_path="credentials/client_secret_oauth_desktop.json")
    download_instance = Download()
    if not download_instance.login(username, password):
        sys.exit()
    interval_data = download_data(downloader=download_instance, start_date=datetime.date.fromisoformat(start_date),
                                  end_date=datetime.date.fromisoformat(end_date))
    g_oauth.fill_data(interval_data=interval_data, sheet_id=google_sheet_file)


if __name__ == "__main__":
    username_input = sys.argv[1]
    password_input = sys.argv[2]
    start_date_input = sys.argv[3]
    end_date_input = sys.argv[4]
    google_sheet_file_input = sys.argv[5]
    main(username=username_input, password=password_input, start_date=start_date_input, end_date=end_date_input,
         google_sheet_file=google_sheet_file_input)
