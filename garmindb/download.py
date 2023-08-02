"""Class for downloading health data from Garmin Connect."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import datetime
import json
import re
import time

import cloudscraper
import fitfile.conversions as conversions
from idbutils import RestClient
from tqdm import tqdm

from .config_manager import ConfigManager
from .garmin_connect_config_manager import GarminConnectConfigManager


def get_static_url_params(url: str, params: dict):
    return url, params


class Download:
    """Class for downloading health data from Garmin Connect."""

    garmin_connect_base_url = "https://connect.garmin.com"
    garmin_connect_enus_url = garmin_connect_base_url + "/en-US"

    garmin_connect_sso_login = 'signin'

    garmin_connect_login_url = garmin_connect_enus_url + "/signin"

    garmin_connect_css_url = 'https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css'

    garmin_connect_privacy_url = "//connect.garmin.com/en-U/privacy"

    garmin_connect_user_profile_url = "proxy/userprofile-service/userprofile"
    garmin_connect_wellness_url = "proxy/wellness-service/wellness"
    garmin_connect_sleep_daily_url = garmin_connect_wellness_url + "/dailySleepData"
    garmin_connect_rhr = "proxy/userstats-service/wellness/daily"
    garmin_connect_weight_url = "proxy/weight-service/weight/dateRange"

    garmin_connect_activity_search_url = "proxy/activitylist-service/activities/search/activities"

    garmin_connect_usersummary_url = "proxy/usersummary-service/usersummary"
    garmin_connect_daily_summary_url = garmin_connect_usersummary_url + "/daily"
    garmin_connect_daily_hydration_url = garmin_connect_usersummary_url + "/hydration/allData"

    # https://connect.garmin.com/modern/proxy/usersummary-service/usersummary/hydration/allData/2019-11-29

    garmin_headers = {'NK': 'NT'}

    def __init__(self):
        """Create a new Download class instance."""
        self.social_profile = None
        self.user_prefs = None
        self.full_name = None
        self.display_name = None
        self.session = cloudscraper.CloudScraper()
        self.sso_rest_client = RestClient(self.session, 'sso.garmin.com', 'sso', aditional_headers=self.garmin_headers)
        self.modern_rest_client = RestClient(self.session, 'connect.garmin.com', 'modern',
                                             aditional_headers=self.garmin_headers)
        self.activity_service_rest_client = RestClient.inherit(self.modern_rest_client,
                                                               "proxy/activity-service/activity")
        self.download_service_rest_client = RestClient.inherit(self.modern_rest_client, "proxy/download-service/files")
        self.gc_config = GarminConnectConfigManager()
        self.download_days_overlap = 3  # Existing downloaded data will be re-downloaded and overwritten if it is
        # within this number of days of now.

    def __get_json(self, page_html, key):
        found = re.search(key + r" = (\{.*\});", page_html, re.M)
        if found:
            json_text = found.group(1).replace('\\"', '"')
            return json.loads(json_text)

    def login(self, username, password):
        """Login to Garmin Connect."""
        username = username
        password = password
        if not username or not password:
            return False

        get_headers = {
            'Referer': self.garmin_connect_login_url
        }
        params = {
            'service': self.modern_rest_client.url(),
            'webhost': self.garmin_connect_base_url,
            'source': self.garmin_connect_login_url,
            'redirectAfterAccountLoginUrl': self.modern_rest_client.url(),
            'redirectAfterAccountCreationUrl': self.modern_rest_client.url(),
            'gauthHost': self.sso_rest_client.url(),
            'locale': 'en_US',
            'id': 'gauth-widget',
            'cssUrl': self.garmin_connect_css_url,
            'privacyStatementUrl': '//connect.garmin.com/en-US/privacy/',
            'clientId': 'GarminConnect',
            'rememberMeShown': 'true',
            'rememberMeChecked': 'false',
            'createAccountShown': 'true',
            'openCreateAccount': 'false',
            'displayNameShown': 'false',
            'consumeServiceTicket': 'false',
            'initialFocus': 'true',
            'embedWidget': 'false',
            'generateExtraServiceTicket': 'true',
            'generateTwoExtraServiceTickets': 'false',
            'generateNoServiceTicket': 'false',
            'globalOptInShown': 'true',
            'globalOptInChecked': 'false',
            'mobile': 'false',
            'connectLegalTerms': 'true',
            'locationPromptShown': 'true',
            'showPassword': 'true'
        }
        response = self.sso_rest_client.get(self.garmin_connect_sso_login, get_headers, params)
        found = re.search(r"name=\"_csrf\" value=\"(\w*)", response.text, re.M)

        data = {
            'username': username,
            'password': password,
            'embed': 'false',
            '_csrf': found.group(1)
        }
        post_headers = {
            'Referer': response.url,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = self.sso_rest_client.post(self.garmin_connect_sso_login, post_headers, params, data)
        found = re.search(r"\?ticket=([\w-]*)", response.text, re.M)
        params = {
            'ticket': found.group(1)
        }
        response = self.modern_rest_client.get('', params=params)
        self.user_prefs = self.__get_json(response.text, 'VIEWER_USERPREFERENCES')
        self.display_name = self.user_prefs['displayName']
        self.social_profile = self.__get_json(response.text, 'VIEWER_SOCIAL_PROFILE')
        self.full_name = self.social_profile['fullName']
        return True

    def __get_stat(self, stat_function, directory, date, days, overwrite):
        for day in tqdm(range(0, days), unit='days'):
            download_date = date + datetime.timedelta(days=day)
            stat_function(directory, download_date, overwrite)
            # pause for a second between every page access
            time.sleep(1)

    def get_daily_stats(self, date, days, url_param_function):
        daily_stats = list()
        for day in tqdm(range(0, days), unit='days'):
            download_date = date + datetime.timedelta(days=day)
            static_url, static_params = url_param_function(download_date)
            daily_stats.append(self.modern_rest_client.get(leaf_route=static_url, params=static_params).json())
            # pause for a second between every page access
            time.sleep(1)
        return daily_stats

    def url_param_summary_day(self, date: datetime.date):
        url = f'{self.garmin_connect_daily_summary_url}/{self.display_name}'
        params = {
            'calendarDate': date.strftime('%Y-%m-%d'),
            '_': str(conversions.dt_to_epoch_ms(conversions.date_to_dt(date)))
        }
        return url, params

    def url_param_hydration_day(self, date: datetime.date):
        url = f"{self.garmin_connect_daily_hydration_url}/{date.strftime('%Y-%m-%d')}"
        return url, None

    def __get_weight_day(self, directory, day, overwrite=False):
        date_str = day.strftime('%Y-%m-%d')
        params = {
            'startDate': date_str,
            'endDate': date_str,
            '_': str(conversions.dt_to_epoch_ms(conversions.date_to_dt(day)))
        }
        json_filename = f'{directory}/weight_{date_str}'
        self.modern_rest_client.download_json_file(self.garmin_connect_weight_url, json_filename, overwrite, params)

    def get_weight(self, directory, date, days, overwrite=True):
        """Download the sleep data from Garmin Connect and save to a JSON file."""
        self.__get_stat(self.__get_weight_day, directory, date, days, overwrite)

    def get_activities(self, count, start_date: datetime.date, end_date: datetime.date):
        """Download activities files from Garmin Connect"""
        activities = self.modern_rest_client.get(self.garmin_connect_activity_search_url, params={
            'start': str(0),
            "limit": str(count),
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat()
        }).json()
        all_activities = dict()
        for activity in tqdm(activities or [], unit='activities'):
            activity_id_str = str(activity['activityId'])
            activity_details = self.activity_service_rest_client.get(leaf_route=activity_id_str, params=None,
                                                                     ignore_errors=None).json()
            all_activities.__setitem__(activity_id_str, activity_details)
            # pause for a second between every page access
            time.sleep(1)
        return all_activities

    def get_activity_types(self):
        """Download the activity types from Garmin Connect"""
        return self.activity_service_rest_client.get(leaf_route='activityTypes', params=None, ignore_errors=None).json()

    def __get_sleep_day(self, directory, date, overwite=False):
        json_filename = f'{directory}/sleep_{date}'
        params = {
            'date': date.strftime("%Y-%m-%d"),
            'nonSleepBufferMinutes': 60
        }
        url = f'{self.garmin_connect_sleep_daily_url}/{self.display_name}'
        self.modern_rest_client.download_json_file(url, json_filename, overwite, params)

    def get_sleep(self, directory, date, days, overwrite=True):
        """Download the sleep data from Garmin Connect and save to a JSON file."""
        self.__get_stat(self.__get_sleep_day, directory, date, days, overwrite)

    def __get_rhr_day(self, directory, day, overwrite=False):
        date_str = day.strftime('%Y-%m-%d')
        json_filename = f'{directory}/rhr_{date_str}'
        params = {
            'fromDate': date_str,
            'untilDate': date_str,
            'metricId': 60
        }
        url = f'{self.garmin_connect_rhr}/{self.display_name}'
        self.modern_rest_client.download_json_file(url, json_filename, overwrite, params)

    def get_rhr(self, directory, date, days, overwite):
        """Download the resting heart rate data from Garmin Connect and save to a JSON file."""
        self.__get_stat(self.__get_rhr_day, directory, date, days, overwite)
