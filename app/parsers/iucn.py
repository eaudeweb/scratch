import io
import logging
import re
from datetime import date
from io import BytesIO
from tempfile import TemporaryFile
from typing import Tuple

import datefinder
import docx2txt
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from dateutil.relativedelta import relativedelta
from django.core.files import File
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFSyntaxError

from app.models import Tender, Award, Vendor, WorkerLog, TenderDocument
from app.utils import transform_vendor_name


# TODO: save awards to database
# TODO: add iucn source to tender filter
# TODO: filter imported iucn tenders by keyword
# TODO: implement last_date functionality
# TODO: Check warning ->  RuntimeWarning: DateTimeField Tender.deadline received a naive datetime (2022-09-26 00:00:00)
#  while time zone support is active.

class IUCNWorker:
    BASE_URI = "https://www.iucn.org"
    IUCN_TENDERS_ENDPOINT_URI = '/procurement/currently-running-tenders'
    IUCN_AWARDS_ENDPOINT_URI = '/procurement/contract-award-notices'

    def get_tenders_html(self):

        response = requests.get(self.BASE_URI + self.IUCN_TENDERS_ENDPOINT_URI)
        if response.status_code == 200:
            return response.content
        return None

    def get_awards_html(self):

        response = requests.get(self.BASE_URI + self.IUCN_AWARDS_ENDPOINT_URI)
        if response.status_code == 200:
            return response.content
        return None

    def parse_latest_notices(self, last_date):
        try:
            tenders_html = self.get_tenders_html()
            awards_html = self.get_awards_html()

            self.parse_iucn_notice_list(tenders_html, last_date, "Contract notice")
            self.parse_iucn_notice_list(awards_html, last_date, "Contract award notice")
        except Exception as e:
            print(e)

    @staticmethod
    def parse_iucn_notice_list(html, last_date, notice_type):
        soup = BeautifulSoup(html, 'html.parser')
        tender_tables = soup.select('table.datatables-enabled')
        tenders = []
        for table in tender_tables:
            tenders += table.select("tr")[1:]
        for tender in tenders:
            try:
                if notice_type == "Contract notice":
                    IUCNWorker.parse_iucn_notice(tender, last_date)
                elif notice_type == "Contract award notice":
                    IUCNWorker.parse_iucn_award(tender, last_date)
            except Exception as e:
                print(e)
                continue

    # return tenders

    @staticmethod
    def parse_iucn_notice(tender, last_date):

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
        print(first_link.get('download_url'))
        title, reference, published = IUCNWorker.parse_pdf(first_link.get('download_url'))

        if published and published < last_date:
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
            'organization': iucn_office.text,
            'reference': reference,
            'published': published,
            'deadline': deadline,
            'description': description,
        }

        if tender["reference"]:
            IUCNWorker.save_tender(tender, doc_links)

    @staticmethod
    def parse_iucn_award(notice, last_date):

        notice_components = notice.select('td')

        title_and_links = notice_components[0]
        doc_links = [{ 'download_url' : IUCNWorker.BASE_URI + doc.attrs['href'], 'name': doc.text.strip() } for doc in title_and_links.select('a')]
        first_link = doc_links[0]
        print(first_link.get('download_url'))
        title, reference, published = IUCNWorker.parse_pdf(first_link.get('download_url'))

        if published and published < last_date:
            return

        iucn_office = notice_components[1]

        tender = {
            'source': 'IUCN',
            'url': first_link.get('download_url'),
            'notice_type': "Contract award notice",
            'title': title,
            'organization': iucn_office.text.replace("\n", ""),
            'reference': reference,
            'published': published,
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

                if notice_components[3].text.lower().find('weeks') != -1:
                    renewal_date = award_date + relativedelta(weeks=duration)
                elif notice_components[3].text.lower().find('days') != -1:
                    renewal_date = award_date + relativedelta(days=duration)
                elif notice_components[3].text.lower().find('months') != -1:
                    renewal_date = award_date + relativedelta(months=duration)
                elif notice_components[3].text.lower().find('years') != -1:
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
            IUCNWorker.save_tender(tender, doc_links)
            IUCNWorker.save_award(tender, award)


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
