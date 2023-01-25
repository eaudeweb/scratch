from datetime import date, datetime, timedelta
from multiprocessing import Process
from unittest.mock import patch, MagicMock

from dateutil.relativedelta import relativedelta
from django.test import override_settings
from django.utils.timezone import make_aware

from app.factories import CPVCodeFactory, TedCountryFactory
from app.models import Award, Tender
from app.parsers.ted import TEDParser, process_daily_archive
from app.tests.base import BaseTestCase


@override_settings(
    TED_DOC_TYPES='Contract award notice',
    TED_AUTH_TYPE='European Institution/Agency or International Organisation'
)
class TedParserTestCase(BaseTestCase):

    def setUp(self) -> None:
        super(TedParserTestCase, self).setUp()
        CPVCodeFactory(code=44115800)
        CPVCodeFactory(code=72320000)
        TedCountryFactory(name='BE')
        TedCountryFactory(name='ES')

        self.parser = TEDParser('', [])

        expected_deadline = make_aware(datetime.strptime('25-Oct-2019 00:00', '%d-%b-%Y %H:%M'))
        time_now = datetime.now()
        time_utc = datetime.utcnow()
        add_hours = round(float((time_utc - time_now).total_seconds()) / 3600)
        expected_deadline += timedelta(hours=add_hours)
        expected_deadline -= timedelta(hours=5)
        self.expected_deadline = expected_deadline

        self.expected_title = 'Belgium-Brussels: \n' \
                              'Renovation of MEPs’ areas in the buildings of the European ' \
                              'Parliament in Brussels\n'

        self.expected_title_1 = 'Spain-Seville: Licence for a database on ' \
                                'digital music downloads in 2012 and 2013'

    @patch('app.parsers.ted.requests')
    def test_ted_parse_notice_simple(self, mock_requests):
        with open('app/tests/parser_files/contract_notice_nonrenewable.xml', 'r') as g:
            # mock the response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = g.read()

        mock_requests.get.return_value = mock_response

        with open('app/tests/parser_files/base_ted_notice.xml', 'r') as f:
            tender, awards = self.parser._parse_notice(f.read(), [], 'test', {}, False)

            self.assertEqual(tender['reference'], '125860-2019')
            self.assertEqual(tender['title'], self.expected_title)
            self.assertEqual(tender['published'], datetime.strptime('20190319', '%Y%m%d').date())
            self.assertEqual(tender['deadline'], self.expected_deadline)
            self.assertEqual(tender['source'], 'TED')
            self.assertEqual(tender['organization'], 'European Parliament')
            self.assertEqual(
                tender['url'],
                'http://ted.europa.eu/udl?uri=TED:NOTICE:125860-2019:TEXT:EN:HTML',
            )
            self.assertNotEqual(tender['description'], '')

            self.assertEqual(len(awards), 1)
            self.assertEqual(awards[0]["vendors"], ["Société Momentanée Cit Blaton-Jacques Delens"])
            self.assertEqual(awards[0]["award_date"], datetime(2019, 3, 11, 0, 0))
            self.assertEqual(awards[0]["renewal_date"], None)
            self.assertEqual(awards[0]["value"], 17565752.85)
            self.assertEqual(awards[0]["currency"], "EUR")

    @patch('app.parsers.ted.requests')
    def test_ted_parse_notice_full(self, mock_requests):
        with open('app/tests/parser_files/contract_notice.xml', 'r') as g:
            # mock the response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = g.read()

        mock_requests.get.return_value = mock_response
        with open('app/tests/parser_files/ted_notice_full.xml', 'r') as f:
            tender, awards = self.parser._parse_notice(f.read(), [], 'test', {}, False)

            self.assertEqual(tender['reference'], '125860-2019')
            self.assertEqual(tender['title'], self.expected_title)
            self.assertEqual(tender['published'], datetime.strptime('20190319', '%Y%m%d').date())
            self.assertEqual(tender['deadline'], None)
            self.assertEqual(tender['source'], 'TED')
            self.assertEqual(tender['organization'], 'European Parliament')
            self.assertEqual(
                tender['url'],
                'http://ted.europa.eu/udl?uri=TED:NOTICE:125860-2019:TEXT:EN:HTML',
            )
            self.assertNotEqual(tender['description'], '')
            self.parser.save_tender(tender, {})

            self.assertEqual(len(awards), 1)
            self.assertEqual(awards[0]["vendors"], ["Société Momentanée Cit Blaton-Jacques Delens", "Société Momentanée Cit Blaton-Jacques Delens"])
            self.assertEqual(awards[0]["award_date"], datetime(2019, 3, 11, 0, 0))
            self.assertEqual(awards[0]["renewal_date"], datetime(2024, 7, 11, 0, 0))
            self.assertEqual(awards[0]["value"], 17565752.85)
            self.assertEqual(awards[0]["currency"], "EUR")
            self.parser.save_award(tender, awards[0])

            tender_entry = Tender.objects.filter(reference=tender['reference']).first()
            awards = Award.objects.filter(tender=tender_entry)
            self.assertEqual(len(awards), 1)

    @patch('app.parsers.ted.requests')
    def test_ted_parse_notice_many_awards(self, mock_requests):
        with open('app/tests/parser_files/contract_notice.xml', 'r') as g:
            # mock the response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = g.read()

        mock_requests.get.return_value = mock_response
        with open('app/tests/parser_files/ted_notice_many_awards.xml', 'r') as f:
            tender, awards = self.parser._parse_notice(f.read(), [], 'test', {}, False)

            self.assertEqual(tender['reference'], '125860-2019')
            self.assertEqual(tender['title'], self.expected_title)
            self.assertEqual(tender['published'], datetime.strptime('20190319', '%Y%m%d').date())
            self.assertEqual(tender['deadline'], None)
            self.assertEqual(tender['source'], 'TED')
            self.assertEqual(tender['organization'], 'European Parliament')
            self.assertEqual(
                tender['url'],
                'http://ted.europa.eu/udl?uri=TED:NOTICE:125860-2019:TEXT:EN:HTML',
            )
            self.assertNotEqual(tender['description'], '')
            self.parser.save_tender(tender, {})

            mock_requests.get.assert_called_once()
            self.assertEqual(len(awards), 71)
            self.assertEqual(awards[0]["vendors"], ["Société Momentanée Cit Blaton-Jacques Delens", "Société Momentanée Cit Blaton-Jacques Delens"])
            self.assertEqual(awards[0]["award_date"], datetime(2019, 3, 11, 0, 0))
            self.assertEqual(awards[0]["renewal_date"], datetime(2024, 7, 11, 0, 0))
            self.assertEqual(awards[0]["value"], 17565752.85)
            self.assertEqual(awards[0]["currency"], "EUR")
            self.parser.save_award(tender, awards[0])

            tender_entry = Tender.objects.filter(reference=tender['reference']).first()
            awards = Award.objects.filter(tender=tender_entry)
            self.assertEqual(len(awards), 1)

    @patch('app.parsers.ted.requests')
    def test_ted_parse_notice_contract_award(self, mock_requests):
        with open('app/tests/parser_files/contract_notice_alt.xml', 'r') as g:
            # mock the response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = g.read()

        mock_requests.get.return_value = mock_response
        with open('app/tests/parser_files/ted_notice_contract_award.xml', 'r') as f:
            tender, awards = self.parser._parse_notice(f.read(), [], 'test', {}, False)

            self.assertEqual(tender['reference'], '386555-2014')
            self.assertEqual(tender['title'], self.expected_title_1)
            self.assertEqual(tender['published'], datetime.strptime('20141113', '%Y%m%d').date())
            self.assertEqual(tender['deadline'], None)
            self.assertEqual(tender['source'], 'TED')
            self.assertEqual(
                tender['organization'],
                'European Commission, JRC, Institute for Prospective Technological Studies (IPTS)',
            )
            self.assertEqual(
                tender['url'],
                'http://ted.europa.eu/udl?uri=TED:NOTICE:386555-2014:TEXT:EN:HTML',
            )
            self.assertEqual(tender['description'], '')

            self.assertEqual(len(awards), 1)
            self.assertEqual(awards[0]['vendor'], 'The Nielsen Company LLC')
            self.assertEqual(awards[0]['award_date'], datetime(2014, 10, 16).date())
            self.assertEqual(awards[0]['renewal_date'], datetime(2019, 10, 16).date())
            self.assertEqual(awards[0]['value'], '60000')
            self.assertEqual(awards[0]['currency'], 'EUR')

    def test_ted_parse_notice_all_empty(self):
        with open('app/tests/parser_files/ted_notice_all_empty.xml', 'r') as f:
            tender, _ = self.parser._parse_notice(f.read(), [], 'test', {}, False)

            self.assertEqual(tender['title'], '')
            self.assertEqual(tender['source'], 'TED')
            self.assertEqual(tender['reference'], '')
            self.assertEqual(tender['published'], None)
            self.assertEqual(tender['deadline'], None)
            self.assertEqual(tender['organization'], '')
            self.assertEqual(tender['url'], '')
            self.assertNotEqual(tender['description'], '')

    def test_ted_parser_notice_date_format(self):
        with open('app/tests/parser_files/ted_notice_date.xml', 'r') as f:
            tender, _ = self.parser._parse_notice(f.read(), [], 'test', {}, False)

            self.assertEqual(tender['published'], None)
            self.assertEqual(tender['deadline'], None)

    @patch('app.parsers.ted.requests')
    def test_ted_award_all_empty(self, mock_requests):
        with open('app/tests/parser_files/contract_notice_nonrenewable.xml', 'r') as g:
            # mock the response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = g.read()

        mock_requests.get.return_value = mock_response
        with open('app/tests/parser_files/ted_notice_award_all_empty.xml', 'r') as f:
            _, awards = self.parser._parse_notice(f.read(), [], 'test', {}, False)

            self.assertEqual(len(awards), 1)
            self.assertEqual(awards[0]["vendors"], [])
            self.assertEqual(awards[0]["award_date"], date.today())
            self.assertEqual(awards[0]["renewal_date"], None)
            self.assertEqual(awards[0]["value"], 0)
            self.assertEqual(awards[0]["currency"], "N/A")

    @patch('app.parsers.ted.requests')
    def test_ted_award_date_format(self, mock_requests):
        with open('app/tests/parser_files/contract_notice.xml', 'r') as g:
            # mock the response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = g.read()

        mock_requests.get.return_value = mock_response
        with open('app/tests/parser_files/ted_notice_award_date.xml', 'r') as f:
            _, awards = self.parser._parse_notice(f.read(), [], 'test', {}, False)

            self.assertEqual(awards[0]['award_date'], date.today())
            self.assertEqual(awards[0]['renewal_date'], date.today() + relativedelta(months=64))

    def test_multiple_update_ted_ftp_retry(self):
        def run_process_daily_archive():
            process_daily_archive(date(day=13, month=10, year=2019))

        processes = []
        for _ in range(4):
            p = Process(target=run_process_daily_archive)
            p.start()
            processes.append(p)

        join = [p.join() for p in processes]
        assert len([p for p in join if p]) == 0
