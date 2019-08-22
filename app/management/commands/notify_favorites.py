from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from app.models import Tender, TenderDocument, Notification, UNSPSCCode
from app.server_requests import get_request_class
from django.conf import settings
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from django.utils.timezone import make_aware
from .notify import build_email
from getenv import env
import json
import re
import os

ENDPOINT_URI = 'https://www.ungm.org'


class Command(BaseCommand):

    @staticmethod
    def find_by_class(soup, class_value, element_type="span", text_return=False):
        try:
            result = soup.find_all(element_type, {"class": class_value})
            if text_return:
                result = result[0].text.strip()
            return result
        except IndexError:
            return None

    def add_arguments(self, parser):
        parser.add_argument(
            '--digest',
            action='store_true',
            help='If set, all tenders will be notified in one email.'
        )

    def handle(self, *args, **options):
        digest = options['digest']
        request_cls = get_request_class(public=True)
        changed_tenders = self.scrap_favorites(request_cls)

        if changed_tenders:
            self.send_update_email(changed_tenders, digest)

    @staticmethod
    def send_update_email(tenders, digest):
        subject = 'Favorite tenders Update' if digest else 'Favorite tender Update'
        notifications = Notification.objects.all()
        recipients = [notification.email for notification in notifications]
        tends = [tx[0] for tx in tenders]

        if digest:
            html_content = render_to_string(
                'mails/tender_update.html',
                {
                    'tenders': tends,
                    'domain': env('BASE_URL')
                }
            )

            email = build_email(subject, recipients, None, html_content)
            email.send()

        else:
            for tender in tenders:
                html_content = render_to_string(
                    'mails/tender_update.html',
                    {
                        'tenders': [tender[0]],
                        'domain': env('BASE_URL')
                    }
                )

                email = build_email(subject, recipients, None, html_content)
                email.send()

    def scrap_favorites(self, request_cls):
        favorites = self.get_favorite_tenders()
        #import pdb;pdb.set_trace()
        changed_tenders = []
        for tender in favorites:
            html_data = request_cls.get_request(tender.url)
            if html_data is None:
                continue

            codes = UNSPSCCode.objects.all()
            tender_fields = self.parse_tender(html_data, tender.url, codes)
            attr_changes = {}
            for attr, value in [(k, v) for (k, v) in tender_fields['tender'].items()
                                if k != 'documents']:

                old_value = getattr(tender, attr)
                if str(value) != str(old_value):

                    attr_changes.update({attr: (old_value, value)})
                    self.update_tender(tender, attr, value)

            received_docs = tender_fields['documents']
            saved_docs = [
                {'name': d['name'], 'download_url': d['download_url']}
                for d in tender_fields['documents']
            ]

            new_docs = []
            for document in received_docs:
                if document not in saved_docs:
                    new_docs.append(document)
                    self.save_document_to_models(tender, document)

            if attr_changes or new_docs:
                changed_tenders.append((tender, attr_changes, new_docs))

        return changed_tenders

    def parse_tender(self, html, url, codes):

        soup = BeautifulSoup(html, 'html.parser')
        documents = self.find_by_class(soup, "lnkShowDocument", "a")
        description = self.find_by_class(soup, "ungm-list-item ungm-background", "div")
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
    def save_document_to_models(tender, document):
        document_entry = TenderDocument(tender=tender, **document)
        document_entry.save()

    @staticmethod
    def get_favorite_tenders():
        tenders = Tender.objects.filter(favourite=True, source='UNGM')
        return tenders

    @staticmethod
    def update_tender(tender, attribute, value):
        setattr(tender, attribute, value)
        tender.save()
