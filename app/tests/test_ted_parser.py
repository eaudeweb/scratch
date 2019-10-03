from datetime import date, datetime, timedelta

from django.test import override_settings
from django.utils.datetime_safe import datetime
from django.utils.timezone import make_aware

from app.factories import CPVCodeFactory, TedCountryFactory
from app.models import Winner, Tender
from app.parsers.ted import TEDParser
from app.tests.base import BaseTestCase


@override_settings(
    TED_DOC_TYPES="Contract award notice",
    TED_AUTH_TYPE="European Institution/Agency or International Organisation"
)
class TedParserTestCase(BaseTestCase):

    def setUp(self) -> None:
        super(TedParserTestCase, self).setUp()
        CPVCodeFactory(code=44115800)
        CPVCodeFactory(code=72320000)
        TedCountryFactory(name="BE")
        TedCountryFactory(name="ES")

        self.parser = TEDParser("", [])

        expected_deadline = make_aware(datetime.strptime("25-Oct-2019 00:00", "%d-%b-%Y %H:%M"))
        time_now = datetime.now()
        time_utc = datetime.utcnow()
        add_hours = round(float((time_utc - time_now).total_seconds()) / 3600)
        expected_deadline += timedelta(hours=add_hours)
        expected_deadline -= timedelta(hours=5)
        self.expected_deadline = expected_deadline

        self.expected_title = "Belgium-Brussels: \n" \
                              "Renovation of MEPs’ areas in the buildings of the European " \
                              "Parliament in Brussels\n"

        self.expected_title_1 = "Spain-Seville: Licence for a database on " \
                                "digital music downloads in 2012 and 2013"

    def test_ted_parse_notice_simple(self):
        with open("app/tests/parser_files/base_ted_notice.xml", "r") as f:
            tender, winners = self.parser._parse_notice(f.read(), [], "test", {}, False)

            self.assertEqual(tender["reference"], "125860-2019")
            self.assertEqual(tender["title"], self.expected_title)
            self.assertEqual(tender["published"], datetime.strptime("20190319", "%Y%m%d").date())
            self.assertEqual(tender["deadline"], self.expected_deadline)
            self.assertEqual(tender["source"], "TED")
            self.assertEqual(tender["organization"], "European Parliament")
            self.assertEqual(tender["url"], "http://ted.europa.eu/udl?uri=TED:NOTICE:125860-2019:TEXT:EN:HTML")
            self.assertNotEqual(tender["description"], "")

            self.assertEqual(len(winners), 1)
            self.assertEqual(winners[0]["vendor"], "Société Momentanée Cit Blaton-Jacques Delens")
            self.assertEqual(winners[0]["award_date"], datetime(2019, 3, 11, 0, 0))
            self.assertEqual(winners[0]["value"], 17565752.85)
            self.assertEqual(winners[0]["currency"], "EUR")

    def test_ted_parse_notice_full(self):
        with open("app/tests/parser_files/ted_notice_full.xml", "r") as f:
            tender, winners = self.parser._parse_notice(f.read(), [], "test", {}, False)

            self.assertEqual(tender["reference"], "125860-2019")
            self.assertEqual(tender["title"], self.expected_title)
            self.assertEqual(tender["published"], datetime.strptime("20190319", "%Y%m%d").date())
            self.assertEqual(tender["deadline"], None)
            self.assertEqual(tender["source"], "TED")
            self.assertEqual(tender["organization"], "European Parliament")
            self.assertEqual(tender["url"], "http://ted.europa.eu/udl?uri=TED:NOTICE:125860-2019:TEXT:EN:HTML")
            self.assertNotEqual(tender["description"], "")
            self.parser.save_tender(tender, {})

            self.assertEqual(len(winners), 2)
            for winner in winners:
                self.assertEqual(winner["vendor"], "Société Momentanée Cit Blaton-Jacques Delens")
                self.assertEqual(winner["award_date"], datetime(2019, 3, 11, 0, 0))
                self.assertEqual(winner["value"], 17565752.85)
                self.assertEqual(winner["currency"], "EUR")
                self.parser.save_winner(tender, winner)

            tender_entry = Tender.objects.filter(reference=tender["reference"]).first()
            winners = Winner.objects.filter(tender=tender_entry)
            self.assertEqual(len(winners), 1)

    def test_ted_parse_notice_contract_award(self):
        with open("app/tests/parser_files/ted_notice_contract_award.xml", "r") as f:
            tender, winners = self.parser._parse_notice(f.read(), [], "test", {}, False)

            self.assertEqual(tender["reference"], "386555-2014")
            self.assertEqual(tender["title"], self.expected_title_1)
            self.assertEqual(tender["published"], datetime.strptime("20141113", "%Y%m%d").date())
            self.assertEqual(tender["deadline"], None)
            self.assertEqual(tender["source"], "TED")
            self.assertEqual(tender["organization"],
                             "European Commission, JRC, Institute for Prospective Technological Studies (IPTS)")
            self.assertEqual(tender["url"], "http://ted.europa.eu/udl?uri=TED:NOTICE:386555-2014:TEXT:EN:HTML")
            self.assertEqual(tender["description"], "")

            self.assertEqual(len(winners), 1)
            self.assertEqual(winners[0]["vendor"], "The Nielsen Company LLC")
            self.assertEqual(winners[0]["award_date"], datetime(2014, 10, 16).date())
            self.assertEqual(winners[0]["value"], "60000")
            self.assertEqual(winners[0]["currency"], "EUR")

    def test_ted_parse_notice_all_empty(self):
        with open("app/tests/parser_files/ted_notice_all_empty.xml", "r") as f:
            tender, winners = self.parser._parse_notice(f.read(), [], "test", {}, False)

            self.assertEqual(tender["title"], "")
            self.assertEqual(tender["source"], "TED")
            self.assertEqual(tender["reference"], "")
            self.assertEqual(tender["published"], None)
            self.assertEqual(tender["deadline"], None)
            self.assertEqual(tender["organization"], "")
            self.assertEqual(tender["url"], "")
            self.assertNotEqual(tender["description"], "")

    def test_ted_parser_notice_date_format(self):
        with open("app/tests/parser_files/ted_notice_date.xml", "r") as f:
            tender, winners = self.parser._parse_notice(f.read(), [], "test", {}, False)

            self.assertEqual(tender["published"], None)
            self.assertEqual(tender["deadline"], None)

    def test_ted_winner_all_empty(self):
        with open("app/tests/parser_files/ted_notice_winner_all_empty.xml", "r") as f:
            tender, winners = self.parser._parse_notice(f.read(), [], "test", {}, False)

            self.assertEqual(len(winners), 1)
            self.assertEqual(winners[0]["vendor"], "")
            self.assertEqual(winners[0]["award_date"], date.today())
            self.assertEqual(winners[0]["value"], 0)
            self.assertEqual(winners[0]["currency"], "N/A")

    def test_ted_winner_date_format(self):
        with open("app/tests/parser_files/ted_notice_winner_date.xml", "r") as f:
            tender, winners = self.parser._parse_notice(f.read(), [], "test", {}, False)

            self.assertEqual(winners[0]["award_date"], date.today())
