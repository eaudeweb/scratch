from app.models import UNSPSCCode
from app.parsers.ungm import UNGMWorker
from app.management.commands.add_winner import Command
from django.conf import settings
from datetime import timedelta
from django.utils.datetime_safe import datetime
from django.utils.timezone import make_aware
from django.test import TestCase


class UngmParserTestCase(TestCase):

    def setUp(self) -> None:
        self.worker = UNGMWorker()
        self.winner = Command()
        self.url = 'wwww.parser_test.com'
        self.unspsc_codes = UNSPSCCode.objects.all()


    def test_ungm_parse_notice_simple(self):
        pass

    def test_ungm_parse_notice_list_simple(self):
        with open('app/tests/parser_files/base_ungm_notice_list.html', 'r') as f:
            html_string = f.read()

        tenders = self.worker.parse_ungm_notice_list(html_string)
        expected_url = settings.UNGM_ENDPOINT_URI + '/Public/Notice/96949'
        self.assertEqual(len(tenders), 2)
        self.assertEqual(tenders[0]['reference'], '2019/FAAFG/FAAFG/103063')
        self.assertEqual(tenders[0]['published'], '15-Sep-2019')
        self.assertEqual(tenders[1]['reference'], 'ILOAMM_NFQA_G20')
        self.assertEqual(tenders[1]['url'], expected_url)

    def test_ungm_parse_winner_simple(self):
        with open('app/tests/parser_files/base_winner.html', 'r') as f:
            html_string = f.read()

        winner = self.winner.parse_winner(html_string)
        expected_date = datetime.strptime('18-Sep-2019', '%d-%b-%Y')
        self.assertEqual(winner['vendor'], 'E-Secure Sàrl')
        self.assertEqual(winner['value'], 25000.00)
        self.assertEqual(winner['currency'], 'USD')
        self.assertEqual(winner['award_date'], expected_date)

    def test_ungm_parse_notice_empty(self):
        with open('app/tests/parser_files/ungm_notice_all_empty.html', 'r') as f:
            html_string = f.read()
        tender = self.worker.parse_ungm_notice(html_string, self.url,
                                               self.unspsc_codes)

        self.assertEqual(tender['tender']['title'], '')
        self.assertEqual(tender['tender']['source'], '')
        self.assertEqual(tender['tender']['unspsc_codes'], '')
        self.assertEqual(tender['tenders']['url'], self.url)
        self.assertEqual(len(tender['documents']), 0)

    def test_ungm_parser_notice_date_format(self):
        with open('app/tests/parser_files/ungm_notice_date.html', 'r') as f:
            html_string = f.read()
        tender = self.worker.parse_ungm_notice(html_string, self.url,
                                               self.unspsc_codes)

        expected_deadline = make_aware(datetime.strptime('15-Sep-2019 16:45', '%d-%b-%Y %H:%M'))
        time_now = datetime.now()
        time_utc = datetime.utcnow()
        add_hours = round(float((time_utc - time_now).total_seconds()) / 3600)
        expected_deadline += timedelta(hours=add_hours)
        expected_deadline -= timedelta(hours=5)

        self.assertEqual(tender['tender']['published'], '')
        self.assertEqual(tender['tender']['deadline'], expected_deadline)

    def test_ungm_parser_notice_list(self):
        with open('app/tests/parser_files/ungm_notice_list_empty.html', 'r') as f:
            html_string = f.read()

        tender_list = self.worker.parse_ungm_notice_list(html_string)

        self.assertEqual(len(tender_list), 2)
        self.assertEqual(tender_list[1]['published'], '')
        self.assertEqual(tender_list[1]['reference'], '')
        self.assertEqual(tender_list[1]['url'], '')

    def test_ungm_winner_all_empty(self):
        with open('app/tests/parser_files/ungm_winner_all_empty.html', 'r') as f:
            html_string = f.read()

        winner = self.winner.parse_winner(html_string)

        self.assertEqual(winner['vendor'], '')
        self.assertEqual(winner['value'], 0)
        self.assertEqual(winner['currency'], 'USD')
        self.assertEqual(winner['award_date'], datetime.now())

    def test_ungm_winner_date_format(self):
        with open('app/tests/parser_files/ungm_winner_all_empty.html', 'r') as f:
            html_string = f.read()

        winner = self.winner.parse_winner(html_string)
        self.assertEqual(winner['award_date'], datetime.now())