import datetime
import sys
from download import Download


def download_data(downloader: Download, activity_count, start_date: datetime.date, end_date: datetime.date):
    """Download selected activity types from Garmin Connect and save the data in files. Overwrite previously
    downloaded data if indicated."""

    count_days = (end_date - start_date).days + 1
    activity_types = downloader.activity_service_rest_client_pers.get(leaf_route='activityTypes', params=None).json()
    activities = downloader.get_activities(count=activity_count, start_date=start_date, end_date=end_date)
    daily_summaries = downloader.get_daily_stats(date=start_date, days=count_days,
                                                 url_param_function=downloader.url_param_summary_day)
    hydration_days = downloader.get_daily_stats(date=start_date, days=count_days,
                                                url_param_function=downloader.url_param_hydration_day)
    # monitoring_days = downloader.get_daily_stats(date=start_date, days=count_days,
    # stat_function=downloader.get_monitoring_day)

    sleep_days = downloader.get_daily_stats(date=start_date, days=count_days,
                                            url_param_function=downloader.url_param_sleep_day)

    weight_days = downloader.get_daily_stats(date=start_date, days=count_days,
                                             url_param_function=downloader.url_param_weight_day)

    rhr_days = downloader.get_daily_stats(date=start_date, days=count_days,
                                          url_param_function=downloader.url_param_rhr_day)
    return {"activity_types": activity_types, "activities": activities, "daily_summaries": daily_summaries,
            "hydration_days": hydration_days, "sleep_days": sleep_days, "weight_days": weight_days,
            "rhr_days": rhr_days}


def load_data_into_sheet(start_date, end_date, interval_data):
    print(str([start_date, end_date, interval_data]))


def main(username=None, password=None, start_date: str = None, end_date: str = None):
    if None in [username, password, start_date, end_date]:
        sys.exit()
    download_instance = Download()
    if not download_instance.login(username, password):
        sys.exit()
    interval_data = download_data(downloader=download_instance, activity_count=100,
                                  start_date=datetime.date.fromisoformat(start_date),
                                  end_date=datetime.date.fromisoformat(end_date))
    load_data_into_sheet(start_date, end_date, interval_data)


if __name__ == "__main__":
    username_input = sys.argv[1]
    password_input = sys.argv[2]
    start_date_input = sys.argv[3]
    end_date_input = sys.argv[4]
    main(username=username_input, password=password_input, start_date=start_date_input, end_date=end_date_input)
