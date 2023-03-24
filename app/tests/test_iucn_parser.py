import logging
from datetime import timedelta, date
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.utils.datetime_safe import datetime
from django.utils.timezone import make_aware

from app.models import UNSPSCCode
from app.parsers.iucn import IUCNWorker
from app.parsers.ungm import UNGMWorker
from app.management.commands.add_award import Command
from app.tests.base import BaseTestCase


class UngmParserTestCase(BaseTestCase):

    def setUp(self) -> None:
        super(UngmParserTestCase, self).setUp()
        self.parser = IUCNWorker()

        expected_deadline = make_aware(datetime.strptime('25-Oct-2019 00:00', '%d-%b-%Y %H:%M'))
        time_now = datetime.now()
        time_utc = datetime.utcnow()
        add_hours = round(float((time_utc - time_now).total_seconds()) / 3600)
        expected_deadline += timedelta(hours=add_hours)
        expected_deadline -= timedelta(hours=5)

        self.expected_deadline = expected_deadline
        self.latest_date = datetime.strptime('01-Jan-2020 00:00', '%d-%b-%Y %H:%M')


        self.expected_title = ''

        self.expected_title_1 = ''

    @patch('app.parsers.iucn.requests')
    def test_ungm_parse_notice_list(self, mock_requests):
        with open('app/tests/parser_files/rfp-publication-digitisation_final.pdf', 'rb') as g:
            # mock the response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = g.read()

        mock_requests.get.return_value = mock_response

        with open('app/tests/parser_files/iucn_contract_notice_list.html', 'r') as f:
            html_string = f.read()

        tender_list, _ = self.parser.parse_iucn_notice_list(html_string, self.latest_date,"Contract notice")
        self.assertEqual(len(tender_list), 1)
        tender = tender_list[0]
        expected_published = datetime.strptime('17-Mar-2023 00:00', '%d-%b-%Y %H:%M')
        self.assertEqual(tender.reference, 'IUCN-23-01-P03858-1')
        self.assertEqual(tender.published, expected_published)
        self.assertEqual(tender.deadline, datetime.strptime('12-Apr-2023', '%d-%b-%Y'))
        self.assertEqual(tender.source, 'IUCN')
        self.assertEqual(tender.organization, 'IUCN Headquarters')
        self.assertEqual(tender.url, 'https://www.iucn.org/sites/default/files/2023-03/rfp-publication-digitisation_final.pdf')
        self.assertEqual(len(tender.tenderdocument_set.all()), 4)

    @patch('app.parsers.iucn.requests')
    def test_ungm_parse_award_notice_list(self, mock_requests):
        with open('app/tests/parser_files/contract_award_notice_document.docx', 'rb') as g:
            # mock the response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = g.read()

        mock_requests.get.return_value = mock_response

        with open('app/tests/parser_files/iucn_contract_award_notice_list.html', 'r') as f:
            html_string = f.read()

        tender_list, award_list = self.parser.parse_iucn_notice_list(html_string, self.latest_date, "Contract award notice")
        self.assertEqual(len(tender_list), 1)
        tender = tender_list[0]
        expected_published = datetime.strptime('14-Oct-2022 00:00', '%d-%b-%Y %H:%M')
        self.assertEqual(tender.reference, 'IUCN/ROWA-22-09-P03861-01')
        self.assertEqual(tender.published, expected_published)
        self.assertEqual(tender.deadline, None)
        self.assertEqual(tender.source, 'IUCN')
        self.assertEqual(tender.organization, 'IUCN ROWA, Jordan')
        self.assertEqual(tender.url,
                         'https://www.iucn.org/sites/default/files/2022-10/sop_1_template_1.1_rfp_open_procedure_irrigation-systems.docx')
        self.assertEqual(len(tender.tenderdocument_set.all()), 1)

        self.assertEqual(len(award_list), 1)
        award = award_list[0]
        self.assertEqual(len(award.vendors.all()), 1)
        self.assertEqual(award.vendors.all()[0].name, "FAEQ AGRICULTURE TRADING ESTABLISHMENT")
        self.assertEqual(award.award_date, datetime.strptime('06-Dec-2022', '%d-%b-%Y'))
        self.assertEqual(award.renewal_date, None)
        self.assertEqual(award.value, 114351)
        self.assertEqual(award.currency, "CHF")

    @patch('app.parsers.iucn.requests')
    def test_ungm_parse_award_notice_list_renewable(self, mock_requests):
        with open('app/tests/parser_files/contract_award_notice_document.docx', 'rb') as g:
            # mock the response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = g.read()

        mock_requests.get.return_value = mock_response

        with open('app/tests/parser_files/iucn_contract_award_notice_list_renewable.html', 'r') as f:
            html_string = f.read()

        tender_list, award_list = self.parser.parse_iucn_notice_list(html_string, self.latest_date,
                                                                     "Contract award notice")
        self.assertEqual(len(tender_list), 1)
        tender = tender_list[0]
        expected_published = datetime.strptime('14-Oct-2022 00:00', '%d-%b-%Y %H:%M')
        self.assertEqual(tender.reference, 'IUCN/ROWA-22-09-P03861-01')
        self.assertEqual(tender.published, expected_published)
        self.assertEqual(tender.deadline, None)
        self.assertEqual(tender.source, 'IUCN')
        self.assertEqual(tender.organization, 'IUCN ROWA, Jordan')
        self.assertEqual(tender.url,
                         'https://www.iucn.org/sites/default/files/2022-10/sop_1_template_1.1_rfp_open_procedure_irrigation-systems.docx')
        self.assertEqual(len(tender.tenderdocument_set.all()), 1)

        self.assertEqual(len(award_list), 1)
        award = award_list[0]
        self.assertEqual(len(award.vendors.all()), 1)
        self.assertEqual(award.vendors.all()[0].name, "FAEQ AGRICULTURE TRADING ESTABLISHMENT")
        self.assertEqual(award.award_date, datetime.strptime('06-Dec-2022', '%d-%b-%Y'))
        self.assertEqual(award.renewal_date, datetime.strptime('06-Jan-2023', '%d-%b-%Y'))
        self.assertEqual(award.value, 114351)
        self.assertEqual(award.currency, "CHF")
