from django.core.management.base import BaseCommand
from app.server_requests import get_request_class
from django.utils import timezone
from bs4 import BeautifulSoup
import json
import datetime
from time import sleep
from random import randint
from urllib.parse import urlencode
from app.models import Tender, Winner, set_notified
from app.server_requests import (
    TENDERS_ENDPOINT_URI,
    SEARCH_UNSPSCS_URI,
    PAYLOAD,
)
import logging

logger = logging.getLogger(__name__)
WINNERS_ENDPOINT_URI = "https://www.ungm.org/Public/ContractAward"

CSS_TITLE = "Title"
CSS_REFERENCE = "Reference"
CSS_AWARD_DATE = "AwardDate"
CSS_DESCRIPTION = "raw clear"
CSS_ORGANIZATION = "AgencyId"
CSS_VALUE = "ContractValue"
CSS_VENDOR_LIST = "contractAwardVendorsContainer"


class Command(BaseCommand):
    def handle(self, *args, **options):
        expired_tenders = Tender.objects.filter(
            deadline__lt=datetime.datetime.now(timezone.utc)
        )
        for tender in expired_tenders:
            winner = Winner.objects.filter(
                tender__reference=tender.reference
            ).first()

            if not winner:
                contract_id = self.get_contract_id(tender.reference)

                request_cls = get_request_class(public=True)
                url = '/'.join((WINNERS_ENDPOINT_URI, contract_id))
                html_data = request_cls.get_request(url)

                try:
                    tender_fields, winner_fields = self.parse_winner(html_data)
                    self.save_winner(tender_fields, winner_fields)
                except TypeError:
                    logger.error("Contract does not exist!")

    @staticmethod
    def find_by_label(soup, label):
        return soup.find(
            "label", attrs={"for": label}
        ).next_sibling.next_sibling

    @staticmethod
    def get_contract_id(reference):
        if len(reference) < 3:
            logger.error("The search text must be at least 3 characters long.")
            return

        requester = get_request_class(public=True)

        payload = PAYLOAD["winners"]
        payload["Reference"] = reference

        for i in range(0, 3):
            resp = requester.post_request(
                WINNERS_ENDPOINT_URI,
                WINNERS_ENDPOINT_URI + "/Search",
                json.dumps(payload),
            )
            if resp:
                soup = BeautifulSoup(resp, "html.parser")
                contract_id = soup.find("div", {"class": "tableRow dataRow"})["data-contractawardid"]
                return contract_id
            sleep(randint(10, 15))

        logger.error("POST request failed.")
        return None

    def parse_winner(self, html):
        """ Parse a contract award HTML and return a dictionary with information
         such as: title, reference, vendor etc
        """

        soup = BeautifulSoup(html, "html.parser")
        description = soup.find_all("div", CSS_DESCRIPTION)
        vendor_list = []
        for vendors_div in soup.find_all(id=CSS_VENDOR_LIST):
            vendors = vendors_div.descendants
            for vendor in vendors:
                if vendor.name == "div" and vendor.get("class", "") == [
                    "editableListItem"
                ]:
                    vendor_list.append(vendor.text.strip())
        vendor_list = ", ".join(vendor_list)
        title = self.find_by_label(soup, CSS_TITLE)
        organization = self.find_by_label(soup, CSS_ORGANIZATION)
        reference = self.find_by_label(soup, CSS_REFERENCE)
        tender_fields = {
            "source": "UNGM",
            "title": self.to_unicode(title.string),
            "organization": self.to_unicode(organization.string),
            "reference": self.to_unicode(reference.string.strip()),
            "published": None,
            "deadline": None,
            "description": self.to_unicode(str(description[0].get_text())),
        }
        award_date = self.find_by_label(soup, CSS_AWARD_DATE)
        value = self.find_by_label(soup, CSS_VALUE)
        winner_fields = {
            "award_date": self.string_to_date(award_date.string)
            or datetime.date.today(),
            "vendor": vendor_list,
            "value": float(value.string or 0) if value.string else None,
        }
        if winner_fields["value"]:
            winner_fields["currency"] = "USD"

        return tender_fields, winner_fields

    @staticmethod
    def save_winner(tender_fields, winner_fields):
        reference = tender_fields["reference"]
        tender = Tender.objects.filter(reference=reference)
        tender_entry = tender[0]

        winner_entry = Winner(tender=tender_entry, **winner_fields)
        winner_entry.save()

        return tender_entry

    @staticmethod
    def to_unicode(string):
        if not string or isinstance(string, str):
            return string
        else:
            return str(string, "utf8")

    @staticmethod
    def string_to_date(string_date):
        if string_date:
            return datetime.datetime.strptime(string_date.strip(), "%d-%b-%Y")
        return None
