from app.models import UNSPSCCode
from app.parsers.ungm import UNGMWorker
from app.management.commands.add_winner import Command

from datetime import timedelta
from django.utils.datetime_safe import datetime
from django.utils.timezone import make_aware
from django.test import TestCase


class UngmParserTestCase(TestCase):

    def setUp(self) -> None:
        self.worker = UNGMWorker()
        self.url = 'wwww.parser_test.com'
        self.unspsc_codes = UNSPSCCode.objects.all()

    def test_ungm_parse_notice_empty(self):
        with open('app/tests/parser_file/ungm_notice_all_empty.html', 'r') as f:
            html_string = f.read()
        tender = self.worker.parse_ungm_notice(html_string, self.url,
                                               self.unspsc_codes)

        self.assertEqual(tender['tender']['title'], '')
        self.assertEqual(tender['tender']['source'], '')
        self.assertEqual(tender['tender']['unspsc_codes'], '')
        self.assertEqual(tender['tenders']['url'], self.url)
        self.assertEqual(len(tender['documents']), 0)

    def test_ungm_parser_notice_date_format(self):
        with open('app/tests/parser_file/ungm_notice_date.html', 'r') as f:
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
        with open('app/tests/parser_file/base_ungm_notice_list.html', 'r') as f:
            html_string = f.read()

        tender_list = self.worker.parse_ungm_notice_list(html_string)

        self.assertEqual(len(tender_list), 2)
        self.assertEqual(tender_list[1]['published'], '')
        self.assertEqual(tender_list[1]['reference'], '')
        self.assertEqual(tender_list[1]['url'], '')
