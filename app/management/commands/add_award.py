from django.core.management.base import BaseCommand
from app.server_requests import get_request_class
from django.utils import timezone
from bs4 import BeautifulSoup
import json
import datetime
from time import sleep
from random import randint
from app.models import Tender, Award, Vendor
from app.utils import transform_vendor_name
from app.server_requests import (
    PAYLOAD, WINNERS_ENDPOINT_URI, WINNERS_SEARCH_URI
)
import logging
from app.management.commands.base.params import BaseParamsUI

logger = logging.getLogger(__name__)

CSS_TITLE = 'Title'
CSS_REFERENCE = 'Reference'
CSS_AWARD_DATE = 'AwardDate'
CSS_DESCRIPTION = 'raw clear'
CSS_ORGANIZATION = 'AgencyId'
CSS_VALUE = 'ContractValue'
CSS_VENDOR_LIST = 'contractAwardVendorsContainer'

# Only look for awards of tenders whose deadline passed within this many days.
# Each tender costs at least 3 requests to UNGM, so older tenders that never got an
# award published would otherwise be searched again on every run.
AWARD_SEARCH_DAYS = 90


class Command(BaseCommand, BaseParamsUI):
    help = (
        'Finds the contract awards of UNGM tenders whose deadline passed in '
        f'the last {AWARD_SEARCH_DAYS} days and have no award yet. TED and '
        'IUCN awards are imported by update_ted and update_iucn.'
    )

    def handle(self, *args, **options):
        now = datetime.datetime.now(timezone.utc)
        expired_tenders = Tender.objects.filter(
            source='UNGM',
            deadline__lt=now,
            deadline__gte=now - datetime.timedelta(days=AWARD_SEARCH_DAYS),
            awards__isnull=True,
        )

        requester = get_request_class(public=True)
        for tender in expired_tenders:
            # Space out the requests to UNGM, like a person browsing
            sleep(randint(2, 5))
            contract_ids = self.get_contract_ids(tender.reference)
            if not contract_ids:
                logger.warning(f'No award was found for the corresponding tender reference ({ tender.reference })')
                continue

            # A tender split into lots has one contract award per lot
            awards = []
            for contract_id in contract_ids:
                sleep(randint(2, 5))
                html_data = requester.get_request(
                    '/'.join((WINNERS_ENDPOINT_URI, contract_id)))
                if html_data:
                    awards.append(self.parse_award(html_data))
                else:
                    logger.error(f'Could not load contract award {contract_id}')

            if awards:
                self.save_award(tender.reference, self.merge_awards(awards))

    @staticmethod
    def find_by_label(soup, label):
        try:
            return soup.find('label', attrs={'for': label}).next_sibling.next_sibling.string
        except AttributeError:
            return ''

    @staticmethod
    def get_contract_ids(reference):
        if len(reference) < 3:
            logger.error('The search text must be at least 3 characters long.')
            return []

        requester = get_request_class(public=True)

        payload = dict(PAYLOAD['awards'], Reference=reference)
        for i in range(0, 3):
            resp = requester.post_request(
                WINNERS_ENDPOINT_URI,
                WINNERS_SEARCH_URI,
                json.dumps(payload),
            )
            if resp:
                return Command.parse_contract_ids(resp, reference)
            sleep(randint(30, 60))

        logger.error('POST request failed.')
        return []

    @staticmethod
    def parse_contract_ids(html, reference):
        """
        Return the ids of the contract awards in a search result whose
        reference is exactly `reference`. UNGM's reference filter also
        matches partially (e.g. "RFQ/2026/640" finds "RFQ/2026/64033").
        """
        soup = BeautifulSoup(html, 'html.parser')
        contract_ids = []
        for row in soup.select('div.tableRow.dataRow[data-contractawardid]'):
            cell = row.find('div', attrs={'data-description': 'Reference'})
            if cell and cell.get_text().strip() == reference.strip():
                contract_ids.append(row['data-contractawardid'])
        return contract_ids

    @staticmethod
    def merge_awards(awards):
        """
        Merge the contract awards of one tender (one per lot) into a single
        award, like the TED and IUCN parsers do: values are added up, vendors
        collected and the latest award date kept.
        """
        values = [award['value'] for award in awards if award['value'] is not None]
        vendors = []
        for award in awards:
            for vendor in award['vendors']:
                if vendor and vendor not in vendors:
                    vendors.append(vendor)
        return {
            'award_date': max(award['award_date'] for award in awards),
            'vendors': vendors,
            'value': sum(values) if values else None,
            'currency': 'USD' if values else '',
        }

    def parse_award(self, html):
        """ Parse a contract award HTML and return a dictionary with information
         such as: title, reference, vendor etc
        """

        soup = BeautifulSoup(html, 'html.parser')
        vendor_list = []
        for vendors_div in soup.find_all(id=CSS_VENDOR_LIST):
            vendors = vendors_div.descendants
            for vendor in vendors:
                if vendor.name == 'div' and vendor.get('class', '') == [
                    'editableListItem'
                ]:
                    vendor_list.append(vendor.text.strip())
        vendor_list = vendor_list
        award_date = self.find_by_label(soup, CSS_AWARD_DATE)
        value = self.find_by_label(soup, CSS_VALUE)
        award_fields = {
            'award_date': self.string_to_date(award_date) or datetime.date.today(),
            'vendors': vendor_list,
            'value': float(value.strip().replace(',', '')) if value and value.strip() else None,
            'currency': '',
        }

        if award_fields['value']:
            award_fields['currency'] = 'USD'

        return award_fields

    @staticmethod
    def save_award(reference, award_fields):
        tender_entry = Tender.objects.filter(reference=reference).first()
        vendors = award_fields.pop('vendors')
        vendor_objects = []
        for vendor in vendors:
            vendor_object, _ = Vendor.objects.get_or_create(
                name=transform_vendor_name(vendor))
            vendor_objects.append(vendor_object)
        award, _ = Award.objects.update_or_create(
            tender=tender_entry, defaults=award_fields)
        award.vendors.add(*vendor_objects)

        return award

    @staticmethod
    def to_unicode(string):
        if not string or isinstance(string, str):
            return string
        else:
            return str(string, 'utf8')

    @staticmethod
    def string_to_date(string_date):
        if string_date:
            return datetime.datetime.strptime(
                string_date.strip(), '%d-%b-%Y').date()
        return None
