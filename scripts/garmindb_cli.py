#!/usr/bin/env python3

"""
A script that imports and analyzes Garmin health device data into a database.

The data is either copied from a USB mounted Garmin device or downloaded from Garmin Connect.
"""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import datetime
import logging
import sys
from garmindb import ConfigManager, GarminConnectConfigManager, PluginManager
from garmindb import Download

logging.basicConfig(filename='garmindb.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()

gc_config = GarminConnectConfigManager()
db_params_dict = ConfigManager.get_db_params()
plugin_manager = PluginManager(ConfigManager.get_or_create_plugins_dir(), db_params_dict)


def __get_date_and_days(db, latest, table, col, stat_name):
    if latest:
        last_ts = table.latest_time(db, col)
        if last_ts is None:
            date, days = gc_config.stat_start_date(stat_name)
        else:
            # start from the day before the last day in the DB
            date = last_ts.date() if isinstance(last_ts, datetime.datetime) else last_ts
            days = max((datetime.date.today() - date).days, 1)
    else:
        date, days = gc_config.stat_start_date(stat_name)
        days = min((datetime.date.today() - date).days, days)
    if date is None or days is None:
        sys.exit()
    return date, days


def download_data(downloader: Download, activity_count, start_date: datetime.date, end_date: datetime.date):
    """Download selected activity types from Garmin Connect and save the data in files. Overwrite previously
    downloaded data if indicated."""

    count_days = (end_date - start_date).days + 1
    activity_types = downloader.activity_service_rest_client.get(leaf_route='activityTypes', params=None,
                                                                 ignore_errors=None).json()
    activities = downloader.get_activities(count=activity_count, start_date=start_date, end_date=end_date)
    daily_summaries = downloader.get_daily_stats(date=start_date, days=count_days,
                                                 url_param_function=downloader.url_param_summary_day)
    hydration_days = downloader.get_daily_stats(date=start_date, days=count_days,
                                                url_param_function=downloader.url_param_hydration_day)
    # monitoring_days = downloader.get_daily_stats(date=start_date, days=count_days, stat_function=downloader.get_monitoring_day)

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
    print(str([start_date,end_date,interval_data]))


def main(username=None, password=None, start_date: str = None, end_date: str = None):
    if None in [username, password, start_date, end_date]:
        logger.error("One of the inputs is None")
        sys.exit()
    download_instance = Download()
    if not download_instance.login(username, password):
        logger.error("Failed to login!")
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
