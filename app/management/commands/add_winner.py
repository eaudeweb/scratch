from django.core.management.base import BaseCommand
from app.server_requests import get_request_class
from django.utils import timezone
from bs4 import BeautifulSoup
import datetime
from app.models import Tender, Winner, set_notified
import logging

logger = logging.getLogger(__name__)
WINNERS_ENDPOINT_URI = 'https://www.ungm.org/Public/ContractAward'

CSS_TITLE = 'Title'
CSS_REFERENCE = 'Reference'
CSS_AWARD_DATE = 'AwardDate'
CSS_DESCRIPTION = 'raw clear'
CSS_ORGANIZATION = 'AgencyId'
CSS_VALUE = 'ContractValue'
CSS_VENDOR_LIST = 'contractAwardVendorsContainer'


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'integers', metavar='N', type=int, nargs='+',
            help='an integer for the accumulator'
        )

    def handle(self, *args, **options):
        filename = str(options['integers'][0])

        request_cls = get_request_class(public=True)
        url = '/'.join((WINNERS_ENDPOINT_URI, filename))
        html_data = request_cls.get_request(url)

        try:
            tender_fields, winner_fields = self.parse_winner(html_data)
            self.save_winner(tender_fields, winner_fields)
        except TypeError:
            logger.error("Contract does not exist!")

    @staticmethod
    def find_by_label(soup, label):
        return soup.find('label', attrs={'for': label}).next_sibling.next_sibling

    def parse_winner(self, html):
        """ Parse a contract award HTML and return a dictionary with information
         such as: title, reference, vendor etc
        """

        soup = BeautifulSoup(html, 'html.parser')
        description = soup.find_all('div', CSS_DESCRIPTION)
        vendor_list = []
        for vendors_div in soup.find_all(id=CSS_VENDOR_LIST):
            vendors = vendors_div.descendants
            for vendor in vendors:
                if vendor.name == 'div' and vendor.get('class', '') == ['editableListItem']:
                    vendor_list.append(vendor.text.strip())
        vendor_list = ', '.join(vendor_list)
        title = self.find_by_label(soup, CSS_TITLE)
        organization = self.find_by_label(soup, CSS_ORGANIZATION)
        reference = self.find_by_label(soup, CSS_REFERENCE)
        tender_fields = {
            'source': 'UNGM',
            'title': self.to_unicode(title.string),
            'organization': self.to_unicode(organization.string),
            'reference': self.to_unicode(reference.string.strip()),
            # TODO: Find a better way to store published and deadline date
            'published': datetime.datetime.now(tz=timezone.utc),
            'deadline': datetime.datetime.now(tz=timezone.utc),
            'description': self.to_unicode(str(description[0])),
        }
        award_date = self.find_by_label(soup, CSS_AWARD_DATE)
        value = self.find_by_label(soup, CSS_VALUE)
        winner_fields = {
            'award_date': self.string_to_date(award_date.string) or datetime.date.today(),
            'vendor': vendor_list,
            'value': float(value.string or 0) if value.string
            else None
        }
        if winner_fields['value']:
            winner_fields['currency'] = 'USD'

        return tender_fields, winner_fields

    @staticmethod
    def save_winner(tender_fields, winner_fields):
        reference = tender_fields['reference']
        tender = Tender.objects.filter(reference=reference)
        if not tender:
            tender_entry = Tender(**tender_fields)
            set_notified(tender_entry)
            tender_entry.save()
        else:
            tender_entry = tender[0]

        entries = Winner.objects.filter(tender__reference=tender_entry.reference).count()
        if entries == 0:
            winner_entry = Winner(tender=tender_entry, **winner_fields)
            winner_entry.save()

        return tender_entry

    @staticmethod
    def to_unicode(string):
        if not string or isinstance(string, str):
            return string
        else:
            return str(string, 'utf8')

    @staticmethod
    def string_to_date(string_date):
        if string_date:
            return datetime.datetime.strptime(string_date.strip(), '%d-%b-%Y')
        return None
