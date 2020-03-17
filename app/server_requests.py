import requests
import json
import urllib3
from datetime import datetime
from random import randint
from time import sleep
from app.models import UNSPSCCode

LIVE_ENDPOINT_URI = 'https://www.ungm.org'
TENDERS_ENDPOINT_URI = 'https://www.ungm.org/Public/Notice'
WINNERS_ENDPOINT_URI = 'https://www.ungm.org/Public/ContractAward'
SEARCH_UNSPSCS_URI = 'https://www.ungm.org/UNSPSC/Search'


PAYLOAD = {
    'tenders': {
        'PageIndex': 0,
        'PageSize': 15,
        'NoticeTASStatus': [],
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
    },
    'awards': {
        'PageIndex': 0,
        'PageSize': 100,
        'Title': '',
        'Description': '',
        'Reference': '',
        'Supplier': '',
        'AwardFrom': '',
        'AwardTo': '',
        'Countries': [],
        'Agencies': [],
        'UNSPSCs': [],
        'SortField': 'AwardDate',
        'SortAscending': False,
    },
    'unspsc': {
        'filter': '',
        'isreadOnly': False,
        'showSelectAsParent': False,
    }
}


HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.5',
    'Content-Type': 'application/json; charset=UTF-8',
    'Host': 'www.ungm.org',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:31.0)'
    ' Gecko/20100101 Firefox/31.0',
    'X-Requested-With': 'XMLHttpRequest',
}

UNSPSC_CODES = UNSPSCCode.objects.values_list("id", flat=True)


def get_request_class(public=True):
    return UNGMrequester()


class Requester(object):

    def get_request(self, url):
        try:
            response = requests.get(url)
        except requests.exceptions.ConnectionError:
            return None

        if response.status_code == 200:
            return response.content
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
        payload = PAYLOAD[category]
        if category == 'tenders':
            today = datetime.now().strftime('%d-%b-%Y')
            payload['DeadlineFrom'] = payload['PublishedTo'] = today
            payload['PublishedFrom'] = last_date
            payload['PageIndex'] = index
        payload['UNSPSCs'] = list(UNSPSC_CODES)
        return json.dumps(payload)

    def request(self, url, last_date, index):
        for i in range(0, 3):
            html = self.post_request(
                url, url + '/Search', self.get_data(url, last_date, index))
            if html:
                return html
            sleep(randint(10, 15))

    def post_request(
            self, get_url, post_url, data, headers=HEADERS, content_type=None):
        """
        AJAX-like POST request. Does a GET initially to receive cookies that
        are used to the subsequent POST request.

        Returns HTML, NOT Response object.
        """
        try:
            resp = requests.get(get_url)
        except requests.exceptions.ConnectionError:
            return None

        cookies = dict(resp.cookies)
        cookies.update({'UNGM.UserPreferredLanguage': 'en'})
        headers.update({
            'Cookie': '; '.join(
                ['{0}={1}'.format(k, v) for k, v in cookies.items()]),
            'Referer': get_url,
            'Content-Length': str(len(data)),
        })
        if content_type:
            headers.update({'Content-Type': content_type})

        try:
            sleep(randint(2, 5))
            resp = requests.post(post_url, data=data, cookies=cookies,
                                 headers=headers)
        except requests.exceptions.ConnectionError:
            return None

        if resp.status_code == 200:
            return resp.content
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
