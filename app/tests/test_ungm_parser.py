from datetime import timedelta, date

from django.conf import settings
from django.utils.datetime_safe import datetime
from django.utils.timezone import make_aware

from app.models import UNSPSCCode
from app.parsers.ungm import UNGMWorker
from app.management.commands.add_award import Command
from app.tests.base import BaseTestCase


class UngmParserTestCase(BaseTestCase):

    def setUp(self) -> None:
        super(UngmParserTestCase, self).setUp()
        self.worker = UNGMWorker()
        self.award = Command()
        self.url = 'wwww.parser_test.com'
        self.unspsc_codes = UNSPSCCode.objects.all()

        expected_deadline = make_aware(datetime.strptime('15-Sep-2019 16:45', '%d-%b-%Y %H:%M'))
        time_now = datetime.now()
        time_utc = datetime.utcnow()
        add_hours = round(float((time_utc - time_now).total_seconds()) / 3600)
        expected_deadline += timedelta(hours=add_hours)
        expected_deadline -= timedelta(hours=5)
        self.deadline = expected_deadline

    def test_ungm_parse_notice_simple(self):
        with open('app/tests/parser_files/base_ungm_notice.html', 'r') as f:
            html_string = f.read()

        tender = self.worker.parse_ungm_notice(html_string, self.url,
                                               self.unspsc_codes)

        expected_published = datetime.strptime('04-Sep-2019', '%d-%b-%Y').date()
        self.assertEqual(tender['tender']['reference'], 'LRFQ-2019-9151917')
        self.assertEqual(tender['tender']['published'], expected_published)
        self.assertEqual(tender['tender']['deadline'], self.deadline)
        self.assertEqual(tender['tender']['source'], 'UNGM')
        self.assertEqual(tender['tender']['organization'], 'UNICEF')
        self.assertEqual(tender['tender']['url'], self.url)
        self.assertNotEqual(tender['tender']['description'], '')
        self.assertEqual(len(tender['documents']), 1)

    def test_ungm_parse_notice_list_simple(self):
        with open('app/tests/parser_files/base_ungm_notice_list.html', 'r') as f:
            html_string = f.read()

        tenders = self.worker.parse_ungm_notice_list(html_string)
        expected_url = settings.UNGM_ENDPOINT_URI + '/Public/Notice/96949'
        self.assertEqual(len(tenders), 2)
        self.assertEqual(tenders[0]['reference'], '2019/FAAFG/FAAFG/103063')
        self.assertEqual(tenders[0]['published'],  datetime.strptime('15-Sep-2019', '%d-%b-%Y').date())
        self.assertEqual(tenders[1]['reference'], 'ILOAMM_NFQA_G20')
        self.assertEqual(tenders[1]['url'], expected_url)

    def test_ungm_parse_award_simple(self):
        with open('app/tests/parser_files/base_award.html', 'r') as f:
            html_string = f.read()

        award = self.award.parse_award(html_string)
        expected_date = datetime.strptime('18-Sep-2019', '%d-%b-%Y')
        self.assertEqual(award['vendors'][0], 'E-Secure Sàrl')
        self.assertEqual(award['value'], 25000.00)
        self.assertEqual(award['currency'], 'USD')
        self.assertEqual(award['award_date'], expected_date)

    def test_ungm_parse_notice_empty(self):
        with open('app/tests/parser_files/ungm_notice_all_empty.html', 'r') as f:
            html_string = f.read()
        tender = self.worker.parse_ungm_notice(html_string, self.url,
                                               self.unspsc_codes)

        self.assertEqual(tender['tender']['title'], '')
        self.assertEqual(tender['tender']['source'], 'UNGM')
        self.assertEqual(tender['tender']['unspsc_codes'], '')
        self.assertEqual(tender['tender']['url'], self.url)
        self.assertEqual(len(tender['documents']), 0)

    def test_ungm_parser_notice_date_format(self):
        with open('app/tests/parser_files/ungm_notice_date.html', 'r') as f:
            html_string = f.read()
        tender = self.worker.parse_ungm_notice(html_string, self.url,
                                               self.unspsc_codes)

        self.assertEqual(tender['tender']['published'], date.today())
        self.assertEqual(tender['tender']['deadline'], None)

    def test_ungm_parser_notice_list_empty(self):
        with open('app/tests/parser_files/ungm_notice_list_empty.html', 'r') as f:
            html_string = f.read()

        tender_list = self.worker.parse_ungm_notice_list(html_string)

        self.assertEqual(len(tender_list), 2)
        self.assertEqual(tender_list[1]['published'], datetime.strptime('16-Sep-2019', '%d-%b-%Y').date())
        self.assertEqual(tender_list[1]['reference'], '')
        self.assertEqual(tender_list[1]['url'], '')

    def test_ungm_award_all_empty(self):
        with open('app/tests/parser_files/ungm_award_all_empty.html', 'r') as f:
            html_string = f.read()

        award = self.award.parse_award(html_string)

        self.assertEqual(award['vendors'][0], '')
        self.assertEqual(award['value'], '')
        self.assertEqual(award['currency'], '')
        self.assertEqual(award['award_date'], datetime.now().date())

    def test_ungm_award_date_format(self):
        with open('app/tests/parser_files/ungm_award_all_empty.html', 'r') as f:
            html_string = f.read()

        award = self.award.parse_award(html_string)
        self.assertEqual(award['award_date'], datetime.now().date())
