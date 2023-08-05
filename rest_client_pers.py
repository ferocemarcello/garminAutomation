import enum
import cloudscraper


class RestProtocolPers(enum.Enum):
    """Enums for the protocols used for REST requests."""

    http = 'http'
    https = 'https'


class RestClientPers:

    def __init__(self, session: cloudscraper.CloudScraper, host, base_route, protocol=RestProtocolPers.https, port=443, headers=None):
        """Return a new RestClient instance given a requests session and the base URL of the API."""
        if headers is None:
            self.headers = {}
        else:
            self.headers = headers
        self.session = session
        self.host = host
        self.protocol = protocol
        self.port = port
        self.base_route = base_route

    @classmethod
    def inherit(cls, rest_client, route):
        """Create a new RestClient object from a RestClient object. The new object will handle an API endpoint that
        is a child of the old RestClient."""
        return RestClientPers(session=rest_client.session, host=rest_client.host,
                              base_route=f'{rest_client.base_route}/{route}',
                              protocol=rest_client.protocol, port=rest_client.port, headers=rest_client.headers)

    def compose_url(self, leaf_route=None):
        """Return the url for the REST endpoint including leaf if supplied."""
        if leaf_route is not None:
            path = '%s/%s' % (self.base_route, leaf_route)
        else:
            path = self.base_route
        if (self.protocol == RestProtocolPers.https and self.port == 443) or (
                self.protocol == RestProtocolPers.http and self.port == 80):
            return f'{self.protocol.name}://{self.host}/{path}'
        return f'{self.protocol.name}://{self.host}:{self.port}/{path}'

    def get(self, leaf_route, additional_headers=None, params=None):
        """Make a REST API call using the GET method."""
        if params is None:
            params = {}
        if additional_headers is None:
            additional_headers = {}
        total_headers = self.headers.copy()
        total_headers.update(additional_headers)
        return self.session.get(self.compose_url(leaf_route), headers=total_headers, params=params)

    def post(self, leaf_route, additional_headers, params, data):
        """Make a REST API call using the POST method."""
        total_headers = self.headers.copy()
        total_headers.update(additional_headers)
        return self.session.post(self.compose_url(leaf_route), headers=total_headers, params=params, data=data)
