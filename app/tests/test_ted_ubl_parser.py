from datetime import datetime
from app.factories import CPVCodeFactory, TEDNoticeCodeFactory, TedCountryFactory
from app.parsers.ted import TEDParser
from app.tests.base import BaseTestCase
from django.test import override_settings


@override_settings(
    TED_AUTH_CODES=["eu-ins-bod-ag", "int-org"],
    TED_DOC_CODES=[
        "can-modif",
        "can-social",
        "can-standard",
        "cn-social",
        "cn-standard",
    ],
)
class TedUblParserTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        CPVCodeFactory(code=90732500)
        CPVCodeFactory(code=73200000)
        TedCountryFactory(name="CY", iso_a3="CYP")
        TedCountryFactory(name="BE", iso_a3="BEL")
        TEDNoticeCodeFactory(
            code="cn-standard",
            name="Contract notice - standard regime",
            doc_type="Contract notice",
        )
        TEDNoticeCodeFactory(
            code="can-standard",
            name="Contract award notice - standard regime",
            doc_type="Contract award notice",
        )

        self.parser = TEDParser("", [])

    def test_parse_ted_contact_notice(self):
        with open("app/tests/parser_files/2024-OJS081-00243948.xml") as f:
            expected_deadline = datetime.strptime(
                "2024-06-10T00:00:59+02:00", "%Y-%m-%dT%H:%M:%S%z"
            )
            expected_publish_date = datetime.strptime(
                "2024-04-24Z", "%Y-%m-%d%z"
            ).date()
            expected_title = "Geochemical analysis for soil, water and crops in the Turkish Cypriot community"
            expected_organization = (
                "European Commission, REFORM - Structural Reform Support"
            )
            expected_url = "https://ted.europa.eu/en/notice/-/detail/00243948-2024"

            tender, awards = self.parser._parse_ubl_notice(
                f.read(), [], "test", {}, False
            )

            self.assertEqual(tender["reference"], "00243948-2024")
            self.assertEqual(tender["title"], expected_title)
            self.assertEqual(tender["deadline"], expected_deadline)
            self.assertEqual(tender["published"], expected_publish_date)
            self.assertEqual(tender["source"], "TED")
            self.assertEqual(tender["organization"], expected_organization)
            self.assertEqual(tender["url"], expected_url)
            self.assertIn("Estimated total: 400000 EUR", tender["description"])
            self.assertIn(expected_title, tender["description"])
            self.assertEqual(awards, [])

    def test_parse_ted_contract_award_notice(self):
        with open("app/tests/parser_files/2024-OJS081-00243951.xml") as f:
            expected_deadline = None
            expected_publish_date = datetime.strptime(
                "2024-04-24Z", "%Y-%m-%d%z"
            ).date()
            expected_title = (
                "Study on Potential EU Earth-Observation Services for Governmental Use"
            )
            expected_organization = "European Commission, Directorate-General for Defence Industry and Space (DEFIS)"
            expected_url = "https://ted.europa.eu/en/notice/-/detail/00243951-2024"

            tender, awards = self.parser._parse_ubl_notice(
                f.read(), [], "test", {}, False
            )

            self.assertEqual(tender["reference"], "00243951-2024")
            self.assertEqual(tender["title"], expected_title)
            self.assertEqual(tender["deadline"], expected_deadline)
            self.assertEqual(tender["published"], expected_publish_date)
            self.assertEqual(tender["source"], "TED")
            self.assertEqual(tender["organization"], expected_organization)
            self.assertEqual(tender["url"], expected_url)
            self.assertIn("Estimated total: 5000000 EUR", tender["description"])
            self.assertIn(expected_title, tender["description"])
            self.assertEqual(len(awards), 1)
            self.assertEqual(
                awards[0]["vendors"],
                ["OHB SYSTEM AG"],
            )
            self.assertEqual(awards[0]["award_date"], datetime(2024, 1, 23).date())
            self.assertEqual(awards[0]["renewal_date"], None)
            self.assertEqual(awards[0]["value"], 4651804)
            self.assertEqual(awards[0]["currency"], "EUR")
