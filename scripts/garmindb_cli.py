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
from garmindb import Download, Copy
from garmindb import Statistics
from garmindb.garmindb import GarminDb, Sleep, Weight, RestingHeartRate, MonitoringDb, MonitoringHeartRate, \
    ActivitiesDb, GarminSummaryDb
from garmindb.summarydb import SummaryDb

logging.basicConfig(filename='garmindb.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()

gc_config = GarminConnectConfigManager()
db_params_dict = ConfigManager.get_db_params()
plugin_manager = PluginManager(ConfigManager.get_or_create_plugins_dir(), db_params_dict)

stats_to_db_map = {
    Statistics.monitoring: MonitoringDb,
    Statistics.steps: MonitoringDb,
    Statistics.itime: MonitoringDb,
    Statistics.sleep: GarminDb,
    Statistics.rhr: GarminDb,
    Statistics.weight: GarminDb,
    Statistics.activities: ActivitiesDb
}

summary_dbs = [GarminSummaryDb, SummaryDb]


def __get_date_and_days(db, latest, table, col, stat_name):
    if latest:
        last_ts = table.latest_time(db, col)
        if last_ts is None:
            date, days = gc_config.stat_start_date(stat_name)
            logger.info("Recent %s data not found, using: %s : %s", stat_name, date, days)
        else:
            # start from the day before the last day in the DB
            logger.info("Downloading latest %s data from: %s", stat_name, last_ts)
            date = last_ts.date() if isinstance(last_ts, datetime.datetime) else last_ts
            days = max((datetime.date.today() - date).days, 1)
    else:
        date, days = gc_config.stat_start_date(stat_name)
        days = min((datetime.date.today() - date).days, days)
        logger.info("Downloading all %s data from: %s [%d]", stat_name, date, days)
    if date is None or days is None:
        logger.error("Missing config: need %s_start_date and download_days. Edit GarminConnectConfig.py.", stat_name)
        sys.exit()
    return date, days


def copy_data(latest, stats):
    """Copy data from a mounted Garmin USB device to files."""
    logger.info("___Copying Data___")
    copy = Copy(gc_config.device_mount_dir())

    settings_dir = ConfigManager.get_or_create_fit_files_dir()
    root_logger.info("Copying settings to %s", settings_dir)
    copy.copy_settings(settings_dir)

    if Statistics.activities in stats:
        activities_dir = ConfigManager.get_or_create_activities_dir()
        root_logger.info("Copying activities to %s", activities_dir)
        copy.copy_activities(activities_dir, latest)

    if Statistics.monitoring in stats:
        monitoring_dir = ConfigManager.get_or_create_monitoring_dir(datetime.datetime.now().year)
        root_logger.info("Copying monitoring to %s", monitoring_dir)
        copy.copy_monitoring(monitoring_dir, latest)

    if Statistics.sleep in stats:
        monitoring_dir = ConfigManager.get_or_create_monitoring_dir(datetime.datetime.now().year)
        root_logger.info("Copying sleep to %s", monitoring_dir)
        copy.copy_sleep(monitoring_dir, latest)


def download_data(downloader: Download, activity_count=100, start_date="2023-07-31", end_date="2023-08-01"):
    """Download selected activity types from Garmin Connect and save the data in files. Overwrite previously
    downloaded data if indicated."""

    activity_types = downloader.get_activity_types()
    activities = downloader.get_activities(count=activity_count, start_date=start_date, end_date=end_date).json()

    date, days = __get_date_and_days(MonitoringDb(db_params_dict), False, MonitoringHeartRate,
                                     MonitoringHeartRate.heart_rate, 'monitoring')
    if days > 0:
        downloader.get_daily_summaries(ConfigManager.get_or_create_monitoring_dir, date, days, False)
        downloader.get_hydration(ConfigManager.get_or_create_monitoring_dir, date, days, False)
        downloader.get_monitoring(ConfigManager.get_or_create_monitoring_dir, date, days)

    date, days = __get_date_and_days(GarminDb(db_params_dict), False, Sleep, Sleep.total_sleep, 'sleep')
    if days > 0:
        sleep_dir = ConfigManager.get_or_create_sleep_dir()
        downloader.get_sleep(sleep_dir, date, days, False)
    date, days = __get_date_and_days(GarminDb(db_params_dict), False, Weight, Weight.weight, 'weight')
    if days > 0:
        weight_dir = ConfigManager.get_or_create_weight_dir()
        downloader.get_weight(weight_dir, date, days, False)
    date, days = __get_date_and_days(GarminDb(db_params_dict), False, RestingHeartRate,
                                     RestingHeartRate.resting_heart_rate, 'rhr')
    if days > 0:
        rhr_dir = ConfigManager.get_or_create_rhr_dir()
        downloader.get_rhr(rhr_dir, date, days, False)


def main(username=None, password=None):
    if password is None or username is None:
        logger.error("Password is None")
        sys.exit()
    download_instance = Download()
    if not download_instance.login(username, password):
        logger.error("Failed to login!")
        sys.exit()
    download_data(downloader=download_instance, activity_count=100, start_date="2023-07-31", end_date="2023-08-01")


if __name__ == "__main__":
    main(username="ferocemarcello@gmail.com", password="894U%rS7bAt8VV*9r")
