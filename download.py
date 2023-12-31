import datetime
import json
import re
import time

import cloudscraper
from tqdm import tqdm

from rest_client_pers import RestClientPers


def get_static_url_params(url: str, params: dict):
    return url, params


def get_json(page_html, key):
    found = re.search(key + r" = (\{.*});", page_html, re.M)
    if found:
        json_text = found.group(1).replace('\\"', '"')
        return json.loads(json_text)


class Download:
    """Class for downloading health data from Garmin Connect."""

    garmin_connect_base_url = "https://connect.garmin.com"
    garmin_connect_en_us_url = garmin_connect_base_url + "/en-US"
    garmin_connect_sso_login = 'signin'
    garmin_connect_login_url = garmin_connect_en_us_url + "/signin"
    garmin_connect_css_url = 'https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css'
    garmin_connect_privacy_url = "//connect.garmin.com/en-U/privacy"
    garmin_connect_user_profile_url = "proxy/userprofile-service/userprofile"
    garmin_connect_wellness_url = "proxy/wellness-service/wellness"
    garmin_connect_sleep_daily_url = garmin_connect_wellness_url + "/dailySleepData"
    garmin_connect_rhr = "proxy/userstats-service/wellness/daily"
    garmin_connect_weight_url = "proxy/weight-service/weight/dateRange"
    garmin_connect_activity_search_url = "proxy/activitylist-service/activities/search/activities"
    garmin_connect_user_summary_url = "proxy/usersummary-service/usersummary"
    garmin_connect_daily_summary_url = garmin_connect_user_summary_url + "/daily"
    garmin_connect_daily_hydration_url = garmin_connect_user_summary_url + "/hydration/allData"
    garmin_headers = {'NK': 'NT'}

    def __init__(self):
        """Create a new Download class instance."""
        self.social_profile = None
        self.user_prefs = None
        self.full_name = None
        self.display_name = None
        self.session = cloudscraper.CloudScraper()
        self.sso_rest_client_pers = RestClientPers(session=self.session, host='sso.garmin.com', base_route='sso',
                                                   headers=self.garmin_headers)
        self.modern_rest_client_pers = RestClientPers(session=self.session, host='connect.garmin.com',
                                                      base_route='modern', headers=self.garmin_headers)
        self.activity_service_rest_client_pers = RestClientPers.inherit(self.modern_rest_client_pers,
                                                                        "proxy/activity-service/activity")
        self.download_service_rest_client_pers = RestClientPers.inherit(self.modern_rest_client_pers,
                                                                        "proxy/download-service/files")

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
            'service': self.modern_rest_client_pers.compose_url(),
            'webhost': self.garmin_connect_base_url,
            'source': self.garmin_connect_login_url,
            'redirectAfterAccountLoginUrl': self.modern_rest_client_pers.compose_url(),
            'redirectAfterAccountCreationUrl': self.modern_rest_client_pers.compose_url(),
            'gauthHost': self.sso_rest_client_pers.compose_url(),
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
        response = self.sso_rest_client_pers.get(self.garmin_connect_sso_login, get_headers, params)
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
        response = self.sso_rest_client_pers.post(self.garmin_connect_sso_login, post_headers, params, data)
        if response.status_code == 429:
            raise Exception("Too many requests")
        found = re.search(r"\?ticket=([\w-]*)", response.text, re.M)
        params = {
            'ticket': found.group(1)
        }
        response = self.modern_rest_client_pers.get('', params=params)
        self.user_prefs = get_json(response.text, 'VIEWER_USERPREFERENCES')
        self.display_name = self.user_prefs['displayName']
        self.social_profile = get_json(response.text, 'VIEWER_SOCIAL_PROFILE')
        self.full_name = self.social_profile['fullName']
        return True

    def get_daily_stats(self, start_date: datetime.date, end_date: datetime.date, url_param_function):
        daily_stats = list()
        delta = end_date - start_date
        for day in tqdm(range(delta.days+1), unit='day'):
            download_date = start_date + datetime.timedelta(days=day)
            static_url, static_params = url_param_function(download_date)
            daily_stats.append(self.modern_rest_client_pers.get(leaf_route=static_url, params=static_params).json())
            # pause for a second between every page access
            time.sleep(1)
        return daily_stats

    def url_param_summary_day(self, date: datetime.date):
        url = f'{self.garmin_connect_daily_summary_url}/{self.display_name}'
        params = {
            'calendarDate': date.strftime('%Y-%m-%d')
        }
        return url, params

    def url_param_hydration_day(self, date: datetime.date):
        url = f"{self.garmin_connect_daily_hydration_url}/{date.strftime('%Y-%m-%d')}"
        return url, None

    def url_param_sleep_day(self, date: datetime.date):
        return f'{self.garmin_connect_sleep_daily_url}/{self.display_name}', {
            'date': date.strftime("%Y-%m-%d"),
            'nonSleepBufferMinutes': 60
        }

    def url_param_weight_day(self, date: datetime.date):
        return self.garmin_connect_weight_url, {
            'startDate': date.strftime('%Y-%m-%d'),
            'endDate': date.strftime('%Y-%m-%d'),
        }

    def url_param_rhr_day(self, date: datetime.date):
        date_str = date.strftime('%Y-%m-%d')
        params = {
            'fromDate': date_str,
            'untilDate': date_str,
            'metricId': 60
        }
        return f'{self.garmin_connect_rhr}/{self.display_name}', params

    def get_activities(self, start_date: datetime.date, end_date: datetime.date):
        """Download activities files from Garmin Connect"""
        activities = self.modern_rest_client_pers.get(self.garmin_connect_activity_search_url, params={
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat()
        }).json()

        all_activities = dict()
        for activity in tqdm(activities or [], unit='activity'):
            activity_id_str = str(activity['activityId'])
            activity_details = self.activity_service_rest_client_pers\
                .get(leaf_route=activity_id_str, params=None).json()
            all_activities.__setitem__(activity_id_str, activity_details)
            # pause for a second between every page access
            time.sleep(1)
        return all_activities
