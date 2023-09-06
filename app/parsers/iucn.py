import io
import logging
import re
from datetime import date
from io import BytesIO
from random import randint
from tempfile import TemporaryFile
from time import sleep

import datefinder
import docx2txt
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from dateutil.relativedelta import relativedelta
from django.core.files import File
from django.utils.timezone import make_aware
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFSyntaxError

from app.models import Tender, Award, Vendor, WorkerLog, TenderDocument
from app.utils import transform_vendor_name



class IUCNWorker:
    BASE_URI = "https://www.iucn.org"
    IUCN_TENDERS_ENDPOINT_URI = '/procurement/currently-running-tenders'
    IUCN_AWARDS_ENDPOINT_URI = '/procurement/contract-award-notices'

    def get_tenders_html(self):

        sleep(randint(2, 5))
        response = requests.get(self.BASE_URI + self.IUCN_TENDERS_ENDPOINT_URI)
        if response.status_code == 200:
            return response.content
        return None

    def get_awards_html(self):

        sleep(randint(2, 5))
        response = requests.get(self.BASE_URI + self.IUCN_AWARDS_ENDPOINT_URI)
        if response.status_code == 200:
            return response.content
        return None

    def parse_latest_notices(self, last_date):
        try:
            tenders_html = self.get_tenders_html()
            awards_html = self.get_awards_html()

            self.parse_iucn_notice_list(tenders_html, "Contract notice", last_date)
            self.parse_iucn_notice_list(awards_html, "Contract award notice", last_date)
        except Exception as e:
            logging.error(e)

    def update_tenders(self, tenders_to_update = None):
        try:
            tenders_html = self.get_tenders_html()
            awards_html = self.get_awards_html()

            _, updated_tenders, _ = self.parse_iucn_notice_list(tenders_html, "Contract notice", last_date=None, tenders_to_update=tenders_to_update)
            _, updated_award_tenders, _ = self.parse_iucn_notice_list(awards_html, "Contract award notice", last_date=None, tenders_to_update=tenders_to_update)
            return updated_tenders + updated_award_tenders
        except Exception as e:
            logging.error(e)

    @staticmethod
    def parse_iucn_notice_list(html, notice_type, last_date, tenders_to_update = None):
        soup = BeautifulSoup(html, 'html.parser')
        tender_tables = soup.select('table.datatables-enabled')
        tenders = []
        for table in tender_tables:
            tenders += table.select("tr")[1:]

        new_tenders = []
        updated_tenders = []
        new_awards = []
        for tender in tenders:
            try:
                if notice_type == "Contract notice":
                    new_tender = IUCNWorker.parse_iucn_notice(tender, last_date, tenders_to_update)
                    if new_tender:
                        if new_tender[1]:
                            new_tenders.append(new_tender)
                        elif new_tender[2] or new_tender[3]:
                            updated_tenders.append(new_tender)

                elif notice_type == "Contract award notice":
                    new_tender, new_award = IUCNWorker.parse_iucn_award(tender, last_date, tenders_to_update)
                    if new_tender:
                        if new_tender[1]:
                            new_tenders.append(new_tender)
                        elif new_tender[2] or new_tender[3]:
                            updated_tenders.append(new_tender)
                    if new_award:
                        new_awards.append(new_award)

            except Exception as e:
                logging.error(e)
                continue
        return new_tenders, updated_tenders, new_awards

    @staticmethod
    def parse_iucn_notice(tender, last_date, tenders_to_update = None):

        tender_components = tender.select('td')

        submission_deadline = tender_components[0]
        try:
            dates = list(datefinder.find_dates(submission_deadline.text))

            if len(dates) == 0:
                deadline = parser.parse(submission_deadline.text, fuzzy=True)
            else:
                deadline = dates[0]

        except Exception:
            deadline = None

        title_and_links = tender_components[1]
        doc_links = [{'download_url': IUCNWorker.BASE_URI + doc.attrs['href'], 'name': doc.text.strip()} for doc in
                     title_and_links.select('a')]
        first_link = doc_links[0]
        title, reference, published = IUCNWorker.parse_pdf(first_link.get('download_url'))

        if tenders_to_update and reference not in [tender_to_update.reference for tender_to_update in tenders_to_update]:
            return None, None, None, None

        if last_date and published and published < last_date:
            return

        iucn_office = tender_components[2]
        country_of_performance = tender_components[3]
        expected_contract_duration = tender_components[4]
        estimated_contract_value = tender_components[5]
        description = f"Country of performance: {country_of_performance.text}\n" \
                      f"Estimated contract value: {estimated_contract_value.text}\n" \
                      f"Expected contract duration: {expected_contract_duration.text}"

        tender = {
            'source': 'IUCN',
            'url': first_link.get('download_url'),
            'notice_type': "Contract notice",
            'title': title,
            'organization': iucn_office.text.strip(),
            'reference': reference,
            'published': published.date(),
            'deadline': make_aware(deadline),
            'description': description,
        }

        if tender["reference"]:
            new_tender = IUCNWorker.save_tender(tender, doc_links)
            return new_tender

    @staticmethod
    def parse_iucn_award(notice, last_date, tenders_to_update = None):

        notice_components = notice.select('td')

        title_and_links = notice_components[0]
        doc_links = [{ 'download_url' : IUCNWorker.BASE_URI + doc.attrs['href'], 'name': doc.text.strip() } for doc in title_and_links.select('a')]
        first_link = doc_links[0]
        title, reference, published = IUCNWorker.parse_pdf(first_link.get('download_url'))

        if tenders_to_update and reference not in [tender_to_update.reference for tender_to_update in tenders_to_update]:
            return None, None

        if last_date and published and published < last_date:
            return

        iucn_office = notice_components[1]

        tender = {
            'source': 'IUCN',
            'url': first_link.get('download_url'),
            'notice_type': "Contract award notice",
            'title': title,
            'organization': iucn_office.text.replace("\n", ""),
            'reference': reference,
            'published': published.date(),
            'deadline': None,
            'description': '',
        }

        award_date = list(datefinder.find_dates(notice_components[5].text))[0]
        contract_currency = None
        renewal_date = None

        contract_value = extract_first_number(notice_components[4].text)

        for word in notice_components[4].text.replace('\n', ' ').split(" "):
            if word.isupper():
                contract_currency = word
                break

        if notice_components[3].text.lower().find('renewable') != -1:
            try:
                duration = int(extract_first_number(notice_components[3].text))

                if notice_components[3].text.lower().find('weeks') != -1 or notice_components[3].text.lower().find('week') != -1:
                    renewal_date = award_date + relativedelta(weeks=duration)
                elif notice_components[3].text.lower().find('days') != -1 or notice_components[3].text.lower().find('day') != -1:
                    renewal_date = award_date + relativedelta(days=duration)
                elif notice_components[3].text.lower().find('months') != -1 or notice_components[3].text.lower().find('month') != -1:
                    renewal_date = award_date + relativedelta(months=duration)
                elif notice_components[3].text.lower().find('years') != -1 or notice_components[3].text.lower().find('year') != -1:
                    renewal_date = award_date + relativedelta(years=duration)
            except (AttributeError, TypeError, ValueError):
                renewal_date = None

        award = {
            "vendors": [transform_vendor_name(notice_components[6].text)],
            "award_date": award_date,
            "renewal_date": renewal_date,
            "value": contract_value,
            "currency": contract_currency,
            "notified": False,
            "renewal_notified": False,

        }

        if tender["reference"]:
            new_tender = IUCNWorker.save_tender(tender, doc_links)
            new_award = IUCNWorker.save_award(tender, award)
            return new_tender, new_award


    @staticmethod
    def save_tender(tender_dict, doc_links) :
        old_tender = Tender.objects.filter(
            reference=tender_dict['reference']).first()
        new_tender, created = Tender.objects.update_or_create(
            reference=tender_dict['reference'],
            defaults=tender_dict,
        )

        if old_tender and old_tender.notified:
            new_tender.notified = True
            new_tender.save()

        attr_changes = {}
        for attr, value in [(k, v) for (k, v) in tender_dict.items()]:
            old_value = getattr(old_tender, str(attr), None)
            if str(value) != str(old_value):
                attr_changes.update({attr: (old_value, value)})

        new_docs = []
        tender_doc = None
        for doc in doc_links:
            try:
                tender_doc = TenderDocument.objects.get(
                    tender=new_tender, name=doc['name'])

                for k, v in doc.items():
                    old_value = getattr(tender_doc, k)

                    if str(old_value) != str(doc[k]):
                        setattr(tender_doc, k, v)

                tender_doc.save()
            except TenderDocument.DoesNotExist:
                tender_doc = TenderDocument.objects.create(
                    tender=new_tender, **doc)
                new_docs.append(doc)
            finally:
                IUCNWorker.download_document(tender_doc)

        return tender_dict, created, attr_changes, new_docs


    @staticmethod
    def save_award(tender_dict, award_dict) -> Award:
        reference = tender_dict['reference']
        tender_entry = Tender.objects.filter(reference=reference).first()

        if tender_entry:
            vendor_objects = []
            if award_dict.get('vendors'):
                vendors = award_dict.pop('vendors')

                for vendor in vendors:
                    vendor_object, _ = Vendor.objects.get_or_create(name=transform_vendor_name(vendor))
                    vendor_objects.append(vendor_object)
                award, created = Award.objects.get_or_create(
                    tender=tender_entry, defaults=award_dict)

                if not created:
                    award.value += award_dict['value']
                    award.save()
                award.vendors.add(*vendor_objects)
                return award
            else:
                logging.warning(f"No vendors for {reference}.")

    @staticmethod
    def parse_pdf(file_url):
        try:
            sleep(randint(2, 5))
            response = requests.get(file_url)
            i_f = BytesIO(response.content)
            resMgr = PDFResourceManager()
            retData = io.StringIO()
            TxtConverter = TextConverter(resMgr, retData, laparams=LAParams())
            interpreter = PDFPageInterpreter(resMgr, TxtConverter)
            page = list(PDFPage.get_pages(i_f, pagenos=[0]))[0]
            interpreter.process_page(page)

            txt = retData.getvalue()

            return IUCNWorker.parse_extracted_text(txt)

        except PDFSyntaxError:
            return IUCNWorker.parse_docx(file_url)

    @staticmethod
    def parse_docx(file_url):
        sleep(randint(2, 5))
        response = requests.get(file_url)
        i_f = BytesIO(response.content)
        text = docx2txt.process(i_f)

        return IUCNWorker.parse_extracted_text(text)

    @staticmethod
    def parse_extracted_text(txt):
        index = txt.find("Request for Proposals (RfP)")

        if index == -1:
            index = txt.find("Request for Proposal (RfP)")
        title_rows = txt[index:].split('\n')

        title = None
        try:
            if len(title_rows) > 3:
                rows = 2
                title = ""
                i = 0
                while rows:
                    if re.search('[a-zA-Z]', title_rows[i]):
                        title += title_rows[i]
                        rows -= 1

                    i += 1
        except Exception:
            title = None

        if not title:
            title = txt.split('\n')[0]

        index = txt.find("RfP Reference:")
        reference = txt[index:].split('\n')[0].replace("RfP Reference:", "").strip().replace(" ", "")

        if not reference or reference == "":

            index = txt.find("Référence de l’AP:")
            reference = txt[index:].split('\n')[0].replace("Référence de l’AP:", "").strip().replace(" ", "")

        index = txt.find("DATE")
        date = None
        for line in txt[index:].split('\n'):

            dates = list(datefinder.find_dates(line))
            if len(dates):
                date = dates[0]
                break

        return title, reference, date

    @staticmethod
    def add_worker_log(tenders_count):
        log = WorkerLog(
            source="IUCN", update=date.today(), tenders_count=tenders_count)
        log.save()

    @staticmethod
    def download_document(tender_doc):
        with TemporaryFile() as content:
            headers = {
                'User-Agent': 'Mozilla/5.0'
            }

            sleep(randint(1, 3))
            response = requests.get(tender_doc.download_url, headers=headers, stream=True)
            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=4096):
                    content.write(chunk)
                content.seek(0)
                tender_doc.document.save(
                    tender_doc.name, File(content), save=True)


def extract_first_number(string):
    for word in string.replace("\n", " ").split(" "):
        try:
            word = word.replace(',', '')
            return float(word)

        except Exception:
            continue

    return None
