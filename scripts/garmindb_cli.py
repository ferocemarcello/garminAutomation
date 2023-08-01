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


def download_data():
    """Download selected activity types from Garmin Connect and save the data in files. Overwrite previously
    downloaded data if indicated."""

    download = Download()
    if not download.login():
        logger.error("Failed to login!")
        sys.exit()

    activity_count = gc_config.all_activity_count()
    activities_dir = ConfigManager.get_or_create_activities_dir()
    root_logger.info("Fetching %d activities to %s", activity_count, activities_dir)
    download.get_activity_types(activities_dir, False)
    download.get_activities(count=activity_count, start_date="2023-07-31", end_date="2023-08-01")

    date, days = __get_date_and_days(MonitoringDb(db_params_dict), False, MonitoringHeartRate,
                                     MonitoringHeartRate.heart_rate, 'monitoring')
    if days > 0:
        root_logger.info("Date range to update: %s (%d) to %s", date, days, ConfigManager.get_monitoring_base_dir())
        download.get_daily_summaries(ConfigManager.get_or_create_monitoring_dir, date, days, False)
        download.get_hydration(ConfigManager.get_or_create_monitoring_dir, date, days, False)
        download.get_monitoring(ConfigManager.get_or_create_monitoring_dir, date, days)
        root_logger.info("Saved monitoring files for %s (%d) to %s for processing", date, days,
                         ConfigManager.get_monitoring_base_dir())

    date, days = __get_date_and_days(GarminDb(db_params_dict), False, Sleep, Sleep.total_sleep, 'sleep')
    if days > 0:
        sleep_dir = ConfigManager.get_or_create_sleep_dir()
        root_logger.info("Date range to update: %s (%d) to %s", date, days, sleep_dir)
        download.get_sleep(sleep_dir, date, days, False)
        root_logger.info("Saved sleep files for %s (%d) to %s for processing", date, days, sleep_dir)

    date, days = __get_date_and_days(GarminDb(db_params_dict), False, Weight, Weight.weight, 'weight')
    if days > 0:
        weight_dir = ConfigManager.get_or_create_weight_dir()
        root_logger.info("Date range to update: %s (%d) to %s", date, days, weight_dir)
        download.get_weight(weight_dir, date, days, False)
        root_logger.info("Saved weight files for %s (%d) to %s for processing", date, days, weight_dir)

    date, days = __get_date_and_days(GarminDb(db_params_dict), False, RestingHeartRate,
                                     RestingHeartRate.resting_heart_rate, 'rhr')
    if days > 0:
        rhr_dir = ConfigManager.get_or_create_rhr_dir()
        root_logger.info("Date range to update: %s (%d) to %s", date, days, rhr_dir)
        download.get_rhr(rhr_dir, date, days, False)
        root_logger.info("Saved rhr files for %s (%d) to %s for processing", date, days, rhr_dir)


def main():
    download_data()


if __name__ == "__main__":
    main()
