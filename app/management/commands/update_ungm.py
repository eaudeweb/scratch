import json
import os
import re
from app.models import Tender, TenderDocument, UNSPSCCode
from app.server_requests import get_request_class
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand
from datetime import date, datetime, timedelta
from django.utils.timezone import make_aware

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
    def parse_ungm_notice_list(html):
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

    def parse_ungm_notice(self, html, url, codes):
        soup = BeautifulSoup(html, 'html.parser')
        documents = self.find_by_class(soup, "lnkShowDocument", "a")
        description = self.find_by_class(soup, "ungm-list-item ungm-background", "div")
        description = description[1].text.strip().lstrip('Description')
        nodes = self.find_by_class(soup, "nodeName", "span")
        scraped_nodes = [parent.find_all("span")[0].text for parent in nodes[1:]]
        unspsc_codes = [
            code.id for code in codes
            if code.id_ungm in scraped_nodes
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
            'published': datetime.strptime(published, '%d-%b-%Y').date() or date.today(),
            'deadline': make_aware(datetime.strptime(deadline[:17], '%d-%b-%Y %H:%M')),
            'description': description,
            'unspsc_codes': ', '.join(unspsc_codes),
        }

        gmt = deadline
        try:
            gmt = gmt[gmt.find("GMT") + 4:gmt.find(")")]
            if gmt:
                hours = float(gmt)
                tender['deadline'] -= timedelta(hours=hours)
        except ValueError:
            pass

        time_now = datetime.now()
        time_utc = datetime.utcnow()
        add_hours = round(float((time_utc - time_now).total_seconds()) / 3600)
        tender['deadline'] += timedelta(hours=add_hours)

        tender_item = {
            'tender': tender,
            'documents': [
                {
                    'name': document.text.strip(),
                    'download_url': ENDPOINT_URI + documents[0]['href']
                }
                for document in documents
            ],

        }

        return tender_item

    @staticmethod
    def update_ungm_tenders(parsed_tenders):
        for item in parsed_tenders:
            try:
                tender_item = Tender.objects.get(reference=item['tender']['reference'])
                Tender.objects.filter(reference=item['tender']['reference']).update(**item['tender'])

                for doc in item['documents']:
                    try:
                        tender_doc = TenderDocument.objects.get(tender=tender_item, name=doc['name'])

                        for k, v in doc.items():
                            old_value = getattr(tender_doc, k)

                            if str(old_value) != str(doc[k]):
                                setattr(tender_doc, k, v)

                        tender_doc.save()

                    except TenderDocument.DoesNotExist:
                        TenderDocument.objects.create(tender=tender_item, **doc)
            except Tender.DoesNotExist:
                new_tender_item = Tender.objects.create(**item['tender'])

                for doc in item['documents']:
                    TenderDocument.objects.create(tender=new_tender_item, **doc)

    def add_arguments(self, parser):
        parser.add_argument(
            '--days_ago',
            help='Get tenders published n days ago',
            type=int,
        )

    def handle(self, *args, **kwargs):

        if kwargs['days_ago']:
            days_ago = kwargs['days_ago']
            last_date = (datetime.today() - timedelta(days=days_ago)).date()
        elif not Tender.objects.all():
            raise Exception(
                "Command error: The database is empty, argument --days_ago is missing"
            )
        else:
            last_date = Tender.objects.latest('published').published

        codes = UNSPSCCode.objects.all()
        requester = get_request_class(public=True)
        last_date = last_date.strftime('%d-%b-%Y')
        page_index = 0
        while True:
            requested_html_tenders = requester.request_tenders_list(last_date, page_index)
            page_index += 1
            extracted_tenders = self.parse_ungm_notice_list(requested_html_tenders)
            if not len(extracted_tenders):
                break
            parsed_tenders = []
            for tender in extracted_tenders:
                text = requester.get_request(tender['url'])
                parsed_tenders.append(self.parse_ungm_notice(text, tender['url'], codes))
            self.update_ungm_tenders(parsed_tenders)

        return self.stdout.write(self.style.SUCCESS('Ungm tenders updated'))
