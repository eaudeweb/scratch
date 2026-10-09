import logging

import requests
import json
import urllib3
from datetime import datetime
from random import randint
from time import sleep

from urllib3.exceptions import NewConnectionError

from bs4 import BeautifulSoup
from django.conf import settings

from app.models import UNSPSCCode

LIVE_ENDPOINT_URI = settings.UNGM_ENDPOINT_URI
TENDERS_ENDPOINT_URI = LIVE_ENDPOINT_URI + '/Public/Notice'
WINNERS_ENDPOINT_URI = LIVE_ENDPOINT_URI + '/Public/ContractAward'
WINNERS_SEARCH_URI = WINNERS_ENDPOINT_URI + '/PublicSearch'
SEARCH_UNSPSCS_URI = LIVE_ENDPOINT_URI + '/UNSPSC/Search'


PAYLOAD = {
    'tenders': {
        'PageIndex': 0,
        'PageSize': 15,
        'Description': '',
        'Title': '',
        'DeadlineFrom': '',
        'SortField': 'DatePublished',
        'UNSPSCs': [],
        'Countries': [],
        'Agencies': [],
        'PublishedTo': '',
        'SortAscending': False,
        'isPicker': False,
        'PublishedFrom': '',
        'NoticeTypes': [],
        'Reference': '',
        'DeadlineTo': '',
        'IsSustainable': False,
        'IsActive': True,
        'NoticeDisplayType': None,
        'NoticeSearchTotalLabelId': 'noticeSearchTotal',
        'TypeOfCompetitions': [],
    },
    'awards': {
        'PageIndex': 0,
        'PageSize': 15,
        'Title': '',
        'Description': '',
        'Reference': '',
        'Supplier': '',
        'AwardFrom': '',
        'AwardTo': '',
        'Countries': [],
        'SupplierCountries': [],
        'Agencies': [],
        'SortField': 'AwardDate',
        'SortAscending': False,
    },
    'unspsc': {
        'filter': '',
        'isreadOnly': False,
        'showSelectAsParent': False,
    }
}


# Keep these consistent with a single current browser: UNGM sits behind a
# bot filter and mismatched or outdated User-Agents get flagged.
USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0'
)

GET_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

POST_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': LIVE_ENDPOINT_URI,
}

# (connect, read) timeout in seconds for every request made to UNGM
REQUEST_TIMEOUT = (10, 60)

# Name of the ASP.NET antiforgery field rendered in the page; its value must
# be sent back in the RequestVerificationToken header, together with the
# matching cookie the server set on the same session.
ANTIFORGERY_FIELD = '__RequestVerificationToken'
ANTIFORGERY_HEADER = 'RequestVerificationToken'


UNSPSC_CODES = UNSPSCCode.objects.values_list("id", flat=True)


class RequestsFailedError(Exception):
    def __init__(self, message="Requests to get UNGM tenders html failed"):
        self.message = message
        super().__init__(self.message)

def get_request_class(public=True):
    return UNGMrequester()


class Requester(object):

    def get_request(self, url):
        try:
            response = requests.get(
                url, headers=GET_HEADERS, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            logging.warning(e)
            return None

        if response.status_code == 200:
            return response.content
        logging.warning(
            'GET %s failed with status code: %s', url, response.status_code)
        return None

    def request_document(self, url):
        try:
            response = urllib3.urlopen(url)
            return response.read()
        except urllib3.HTTPError:
            return None

    def request_tenders_list(self, last_date, index):
        """ Returns HTML page with a list of tenders """
        return self.request(TENDERS_ENDPOINT_URI, last_date, index)

    def request_awards_list(self):
        """ Returns HTML page with a list of awards """
        return self.request(WINNERS_ENDPOINT_URI)


class UNGMrequester(Requester):
    TENDERS_ENDPOINT_URI = TENDERS_ENDPOINT_URI
    WINNERS_ENDPOINT_URI = WINNERS_ENDPOINT_URI

    def get_data(self, url, last_date, index):
        category = 'tenders' if 'Notice' in url else 'awards'
        payload = dict(PAYLOAD[category])
        if category == 'tenders':
            today = datetime.now().strftime('%d-%b-%Y')
            payload['DeadlineFrom'] = payload['PublishedTo'] = today
            payload['PublishedFrom'] = last_date
            payload['PageIndex'] = index
            # UNGM expects the internal code ids as numbers
            payload['UNSPSCs'] = [int(code) for code in UNSPSC_CODES]
        return json.dumps(payload)

    def request(self, url, last_date, index):
        for i in range(0, 3):
            html = self.post_request(
                url, url + '/Search', self.get_data(url, last_date, index))
            if html:
                return html
            sleep(randint(30, 60))
        raise RequestsFailedError

    @staticmethod
    def get_antiforgery_token(html):
        soup = BeautifulSoup(html, 'html.parser')
        field = soup.find('input', {'name': ANTIFORGERY_FIELD})
        if field and field.get('value'):
            return field['value']
        meta = soup.find('meta', {'name': ANTIFORGERY_HEADER})
        if meta and meta.get('content'):
            return meta['content']
        return None

    def post_request(self, get_url, post_url, data, headers=None):
        """
        AJAX-like POST request. Loads `get_url` first, in the same session,
        to receive the cookies and the antiforgery token the POST requires.

        Returns HTML, NOT Response object.
        """
        session = requests.Session()
        session.cookies.set('UNGM.UserPreferredLanguage', 'en')
        try:
            resp = session.get(
                get_url, headers=GET_HEADERS, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            logging.warning(e)
            return None

        if resp.status_code != 200:
            logging.warning(
                'GET %s failed with status code: %s', get_url,
                resp.status_code)
            return None

        token = self.get_antiforgery_token(resp.content)
        if not token:
            logging.warning('No antiforgery token found on %s', get_url)
            return None

        post_headers = dict(POST_HEADERS, **(headers or {}))
        post_headers.update({
            ANTIFORGERY_HEADER: token,
            'Referer': get_url,
        })

        try:
            sleep(randint(2, 5))
            resp = session.post(
                post_url, data=data, headers=post_headers,
                timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            logging.warning(e)
            return None

        if resp.status_code == 200:
            return resp.content

        logging.warning(
            'POST %s failed with status code: %s', post_url, resp.status_code)
        return None

#
# class LOCALrequester(Requester):
#
#     TENDERS_ENDPOINT_URI = TENDERS_ENDPOINT_URI + '/tender_notices'
#     WINNERS_ENDPOINT_URI = WINNERS_ENDPOINT_URI + '/contract_awards'
#
#     def get_request(self, url):
#         url = url.replace(LIVE_ENDPOINT_URI, app.config['LOCAL_ENDPOINT_URI'])
#         url += '.html'
#         return super(LOCALrequester, self).get_request(url)
#
#     def request(self, url):
#         return self.get_request(url)
#
#     def request_document(self, url):
#         url = url.replace(LIVE_ENDPOINT_URI, app.config['LOCAL_ENDPOINT_URI'])
#         splitted_url = url.split('?docId=')
#         url = splitted_url[0] + '/' + splitted_url[1]
#         return super(LOCALrequester, self).request_document(url)
