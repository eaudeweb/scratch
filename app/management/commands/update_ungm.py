
import json
import os
import re
from app.models import Tender
from app.server_requests import get_request_class
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand
from datetime import date, timedelta
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import get_current_timezone


json_unspsc_codes = os.path.join(settings.BASE_DIR, 'UNSPSC_codes_software.json')
ENDPOINT_URI = 'https://www.ungm.org'


class Command(BaseCommand):

    @staticmethod
    def find_by_label(soup, label):
        return soup.find('label', attrs={'for': label}).next_sibling.next_sibling

    @staticmethod
    def find_by_class(soup, class_value, element_type="span", text_return=False):
        try:
            result = soup.find_all(element_type, {"class": class_value})
            if text_return:
                result = result[0].text.strip()
            return result
        except IndexError:
            return None


    @staticmethod
    def parse_notice_list(html):
        soup = BeautifulSoup(html, 'html.parser')
        tenders = soup.find_all('div', 'tableRow dataRow')

        tenders_list = [
            {
                'published': tender.contents[7].span.string or date.today(),
                'reference': tender.contents[13].span.string,
                'url': ENDPOINT_URI + tender.contents[3].a['href']
            }
            for tender in tenders
        ]

        return tenders_list

    def parse_notice(self, html, url):
        soup = BeautifulSoup(html, 'html.parser')
        documents = self.find_by_class(soup, "lnkShowDocument", "a")
        description = self.find_by_class(soup, "ungm-list-item ungm-background", "div")
        description = description[1].text.strip().lstrip('Description')
        nodes = self.find_by_class(soup, "nodeName", "span")
        scraped_nodes = [parent.find_all("span")[0].text for parent in nodes[1:]]
        with open(json_unspsc_codes, 'rb') as fp:
            codes = json.load(fp)
        unspsc_codes = [
            code['id'] for code in codes
            if code['id_ungm'] in scraped_nodes
        ]
        notice_type = self.find_by_class(soup, "status-tag", "span", True)
        title = self.find_by_class(soup, "title", "span", True)
        organization = self.find_by_class(soup, "highlighted", "span", True)

        reference = soup.find('span', text=re.compile('Reference:')).next_sibling.next_sibling.text
        published = soup.find('span', text=re.compile('Published on:')).next_sibling.next_sibling.text
        deadline = soup.find('span', text=re.compile('Deadline on:')).next_sibling.next_sibling.text

        tender = {
            'source': 'UNGM',
            'url': url,
            'notice_type': notice_type,
            'title': title,
            'organization': organization,
            'reference': reference,
            'published': parse_date(published) or date.today(),
            'deadline': parse_datetime(deadline[:17]),
            'description': description,
            'unspsc_codes': ', '.join(unspsc_codes),
            'deadline': deadline
            # 'documents': [
            #     {
            #         'name': document.text.strip(),
            #         'download_url': ENDPOINT_URI + documents[0]['href']
            #     }
            #     for document in documents
            # ],
        }

        new_tender = Tender.objects.create(**tender)
        new_tender.save()

        # gmt = deadline
        # gmt = gmt[gmt.find("GMT") + 4:gmt.find(")")]
        # if gmt:
        #     tender['deadline'] -= timedelta(hours=float(gmt))
        #     tender['deadline'] += timedelta(hours=get_current_timezone())

        return tender

    def handle(self, *args, **kwargs):
        requester = get_request_class(public=True)
        requested_html_tenders = requester.request_tenders_list()

        if not requested_html_tenders:
            return []

        extracted_tenders = self.parse_notice_list(requested_html_tenders)
        parsed_tenders = []
        for tender in extracted_tenders:
            text = requester.get_request(tender['url'])
            parsed_tenders.append(self.parse_notice(text, tender['url']))

        return self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s %s"' % (parsed_tenders[0]['organization'],parsed_tenders[0]['url'])))

