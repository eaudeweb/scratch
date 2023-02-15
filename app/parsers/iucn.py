import io
from io import BytesIO

import datefinder
import docx2txt
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from dateutil.relativedelta import relativedelta
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFSyntaxError

from app.utils import transform_vendor_name


# TODO: save tenders and awards to database
# TODO: check notified attribute
# TODO: add command for importing tenders from iucn

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

    @staticmethod
    def parse_iucn_notice_list(html, notice_type):
        soup = BeautifulSoup(html, 'html.parser')
        tender_tables = soup.select('table.datatables-enabled')
        tenders = []
        for table in tender_tables:
            tenders += table.select("tr")[1:]

        for tender in tenders:

            if notice_type == "Contract notice":
                IUCNWorker.parse_iucn_notice(tender)
            elif notice_type == "Contract award notice":
                IUCNWorker.parse_iucn_award(tender)

    # return tenders

    @staticmethod
    def parse_iucn_notice(tender):

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

        first_link = title_and_links.select('a')[0].attrs['href']

        print(IUCNWorker.BASE_URI + first_link)
        title, reference, published = IUCNWorker.parse_pdf(IUCNWorker.BASE_URI + first_link)

        iucn_office = tender_components[2]
        country_of_performance = tender_components[3]
        expected_contract_duration = tender_components[4]
        estimated_contract_value = tender_components[5]
        description = f"Country of performance: {country_of_performance.text}\n" \
                      f"Estimated contract value: {estimated_contract_value.text}\n" \
                      f"Expected contract duration: {expected_contract_duration.text}"

        tender = {
            'source': 'IUCN',
            'url': IUCNWorker.BASE_URI + IUCNWorker.IUCN_TENDERS_ENDPOINT_URI,
            'notice_type': "Contract notice",
            'title': title,
            'organization': iucn_office.text,
            'reference': reference,
            'published': published,
            'deadline': deadline,
            'description': description,
        }

        print(tender)

    @staticmethod
    def parse_iucn_award(notice):

        notice_components = notice.select('td')

        title_and_links = notice_components[0]
        first_link = title_and_links.select('a')[0].attrs['href']
        print(IUCNWorker.BASE_URI + first_link)
        title, reference, published = IUCNWorker.parse_pdf(IUCNWorker.BASE_URI + first_link)
        iucn_office = notice_components[2]

        tender = {
            'source': 'IUCN',
            'url': IUCNWorker.BASE_URI + IUCNWorker.IUCN_TENDERS_ENDPOINT_URI,
            'notice_type': "Contract notice",
            'title': title,
            'organization': iucn_office.text,
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

        print(tender)
        print(award)

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
        title_rows = txt[index:].split('\n')

        title = None

        if len(title_rows) > 3:
            title = title_rows[0] \
                    + title_rows[1] \
                    + title_rows[2] \
                    + title_rows[3]

        if not title:
            title = txt.split('\n')[0]

        index = txt.find("RfP Reference:")
        reference = txt[index:].split('\n')[0].replace("RfP Reference:", "").strip().replace(" ", "")

        index = txt.find("DATE")
        date = None
        for line in txt[index:].split('\n'):

            dates = list(datefinder.find_dates(line))
            if len(dates):
                date = dates[0]
                break

        return title, reference, date

    def parse_latest_notices(self, last_date):
        try:
            tenders_html = self.get_tenders_html()
            awards_html = self.get_awards_html()

            # self.parse_iucn_notice_list(tenders_html, "Contract notice")
            self.parse_iucn_notice_list(awards_html, "Contract award notice")
        except Exception as e:
            print(e)


def extract_first_number(string):
    for word in string.replace("\n", " ").split(" "):
        try:
            word = word.replace(',', '')
            return float(word)

        except Exception:
            continue

    return None
