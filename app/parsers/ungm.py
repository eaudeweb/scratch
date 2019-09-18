from datetime import date, datetime, timedelta
import re
import requests
from tempfile import TemporaryFile

from bs4 import BeautifulSoup
from django.core.files import File
from django.utils.timezone import make_aware

from app.models import UNSPSCCode, WorkerLog, Tender, TenderDocument
from app.server_requests import get_request_class
from scratch import settings


def get_ungm_parser_class():
    return UNGMWorker()


class UNGMWorker:
    requester = get_request_class(public=True)

    def parse_tenders(self, tenders):
        codes = UNSPSCCode.objects.all()
        parsed_tenders = []
        for tender in tenders:
            text = self.requester.get_request(getattr(tender, 'url'))
            parsed_tenders.append(self.parse_ungm_notice(text, getattr(tender, 'url'), codes))
        return UNGMWorker.update_ungm_tenders(parsed_tenders)

    def parse_latest_notices(self, last_date):
        codes = UNSPSCCode.objects.all()
        last_date = last_date.strftime('%d-%b-%Y')
        page_index = 0
        tenders_count = 0
        while True:
            requested_html_tenders = self.requester.request_tenders_list(last_date, page_index)
            page_index += 1
            extracted_tenders = self.parse_ungm_notice_list(requested_html_tenders)
            if not len(extracted_tenders):
                break
            parsed_tenders = []
            for tender in extracted_tenders:
                text = self.requester.get_request(tender['url'])
                parsed_tender = self.parse_ungm_notice(text, tender['url'], codes)
                if parsed_tender:
                    parsed_tenders.append(parsed_tender)
            ungm_tenders, added_tenders = UNGMWorker.update_ungm_tenders(parsed_tenders)
            tenders_count += added_tenders

        WorkerLog.objects.create(update=date.today(), source='UNGM', tenders_count=tenders_count)
        return

    @staticmethod
    def parse_ungm_notice_list(html):
        soup = BeautifulSoup(html, 'html.parser')
        tenders = soup.find_all('div', 'tableRow dataRow')

        tenders_list = [
            {
                'published': tender.contents[7].span.string or date.today(),
                'reference': tender.contents[13].span.string,
                'url': settings.UNGM_ENDPOINT_URI + tender.contents[3].a['href']
            }
            for tender in tenders
        ]

        return tenders_list

    @staticmethod
    def parse_ungm_notice(html, url, codes):
        soup = BeautifulSoup(html, 'html.parser')
        documents = UNGMWorker.find_by_class(soup, "lnkShowDocument", "a")
        description = UNGMWorker.find_by_class(soup, "ungm-list-item ungm-background", "div")
        try:
            description = description[1].text.strip().lstrip('Description')
        except IndexError:
            description = ''
        nodes = UNGMWorker.find_by_class(soup, "nodeName", "span")
        scraped_nodes = [parent.find_all("span")[0].text for parent in nodes[1:]]
        unspsc_codes = [
            code.id for code in codes
            if code.id_ungm in scraped_nodes
        ]
        notice_type = UNGMWorker.find_by_class(soup, "status-tag", "span", True)
        title = UNGMWorker.find_by_class(soup, "title", "span", True)
        organization = UNGMWorker.find_by_class(soup, "highlighted", "span", True)

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
                    'download_url': settings.UNGM_ENDPOINT_URI + document['href']
                }
                for document in documents
            ],

        }

        return tender_item

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
    def update_ungm_tenders(parsed_tenders):
        changed_tenders = []
        new_tenders = 0
        for item in parsed_tenders:
            reference = item['tender'].pop('reference')
            old_tender = Tender.objects.filter(reference=reference).first()
            new_tender, created = Tender.objects.update_or_create(reference=reference, defaults=dict(item['tender']))

            if created:
                new_tenders += 1
            attr_changes = {}
            if old_tender:
                for attr, value in [(k, v) for (k, v) in item['tender'].items()]:
                    old_value = getattr(old_tender, str(attr), None)
                    if str(value) != str(old_value):
                        attr_changes.update({attr: (old_value, value)})

            new_docs = []
            tender_doc = None
            for doc in item['documents']:
                try:
                    tender_doc = TenderDocument.objects.get(tender=old_tender, name=doc['name'])

                    for k, v in doc.items():
                        old_value = getattr(tender_doc, k)

                        if str(old_value) != str(doc[k]):
                            setattr(tender_doc, k, v)

                    tender_doc.save()
                except TenderDocument.DoesNotExist:
                    tender_doc = TenderDocument.objects.create(tender=new_tender, **doc)
                    new_docs.append(doc)
                finally:
                    UNGMWorker.download_document(tender_doc)

            if not created and (attr_changes or new_docs):
                changed_tenders.append((item['tender'], attr_changes, new_docs))

        return changed_tenders, new_tenders

    @staticmethod
    def download_document(tender_doc):
        with TemporaryFile() as content:
            response = requests.get(tender_doc.download_url, stream=True)
            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=4096):
                    content.write(chunk)
                content.seek(0)
                tender_doc.document.save(tender_doc.name, File(content), save=True)
