#!/usr/bin/env python3

"""
A script that imports and analyzes Garmin health device data into a database.

The data is either copied from a USB mounted Garmin device or downloaded from Garmin Connect.
"""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import argparse
import datetime
import logging
import sys

from garmindb import ConfigManager, GarminConnectConfigManager, PluginManager
from garmindb import Download, Copy
from garmindb import Statistics
from garmindb import python_version_check, format_version
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
    return (date, days)


def copy_data(overwite, latest, stats):
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
    download.get_activities(activities_dir, activity_count, False)

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
    """Manage Garmin device data."""
    python_version_check(sys.argv[0])

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="print the program's version", action='version',
                        version=format_version(sys.argv[0]))
    parser.add_argument("-t", "--trace", help="Turn on debug tracing", type=int, default=0)
    modes_group = parser.add_argument_group('Modes')
    modes_group.add_argument("-b", "--backup", help="Backup the database files.", dest='backup_dbs',
                             action="store_true", default=False)
    modes_group.add_argument("-d", "--download", help="Download data from Garmin Connect for the chosen stats.",
                             dest='download_data', action="store_true", default=False)
    modes_group.add_argument("-c", "--copy", help="copy data from a connected device", dest='copy_data',
                             action="store_true", default=False)
    modes_group.add_argument("-i", "--import", help="Import data for the chosen stats", dest='import_data',
                             action="store_true", default=False)
    modes_group.add_argument("--analyze", help="Analyze data in the db and create summary and derived tables.",
                             dest='analyze_data', action="store_true", default=False)
    modes_group.add_argument("--rebuild_db", help="Delete Garmin DB db files and rebuild the database.",
                             action="store_true", default=False)
    modes_group.add_argument("--delete_db", help="Delete Garmin DB db files for the selected activities.",
                             action="store_true", default=False)
    modes_group.add_argument("-e", "--export-activity",
                             help="Export an activity to a TCX file based on the activity\'s id", type=int)
    modes_group.add_argument("--basecamp-activity", help="Export an activity to Garmin BaseCamp", type=int)
    modes_group.add_argument("-g", "--google-earth-activity", help="Export an activity to Google Earth", type=int)
    # stat types to operate on
    stats_group = parser.add_argument_group('Statistics')
    stats_group.add_argument("-A", "--all", help="Download and/or import data for all enabled stats.",
                             action='store_const', dest='stats',
                             const=gc_config.enabled_stats(), default=[])
    stats_group.add_argument("-a", "--activities", help="Download and/or import activities data.", dest='stats',
                             action='append_const', const=Statistics.activities)
    stats_group.add_argument("-m", "--monitoring", help="Download and/or import monitoring data.", dest='stats',
                             action='append_const', const=Statistics.monitoring)
    stats_group.add_argument("-r", "--rhr", help="Download and/or import resting heart rate data.", dest='stats',
                             action='append_const', const=Statistics.rhr)
    stats_group.add_argument("-s", "--sleep", help="Download and/or import sleep data.", dest='stats',
                             action='append_const', const=Statistics.sleep)
    stats_group.add_argument("-w", "--weight", help="Download and/or import weight data.", dest='stats',
                             action='append_const', const=Statistics.weight)
    modifiers_group = parser.add_argument_group('Modifiers')
    modifiers_group.add_argument("-l", "--latest", help="Only download and/or import the latest data.",
                                 action="store_true", default=False)
    modifiers_group.add_argument("-o", "--overwrite",
                                 help="Overwite existing files when downloading. The default is to only download missing files.",
                                 action="store_true", default=False)
    args = parser.parse_args()

    download_data()


if __name__ == "__main__":
    main()
