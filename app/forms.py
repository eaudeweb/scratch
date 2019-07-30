from django import forms
from .models import Tender, Winner

MAX = 220000
STEP = 20000

SOURCES = [
    ("", "All tenders"),
    ("UNGM", "UNGM"),
    ("TED", "TED")
]

STATUS = [
    ("", "All tenders"),
    ("open", "OPEN"),
    ("closed", "CLOSED")
]

FAVOURITES = [
    ("", "All tenders"),
    ("True", "Yes"),
    ("False", "No")
]

ORGANIZATIONS_LIST = Tender.objects.values_list("organization", flat=True).distinct()
ORGANIZATIONS = [("", "All organizations")] + [(org, org) for org in ORGANIZATIONS_LIST]

VENDORS_LIST = Winner.objects.values_list("vendor", flat=True).distinct()
VENDORS = [("", "All vendors")] + [(vendor, vendor) for vendor in VENDORS_LIST]

r = range(0, MAX, STEP)
VALUES = (
    [("", "All values")]
    + [
        (str(k), "%s - %s" % (format(r[cnt], ",d"), format(r[cnt + 1], ",d")))
        for k, cnt in zip(r, range(len(r[:-1])))
    ]
    + [("max", ">%s" % format(MAX - STEP, ",d"))]
)


class TendersFilter(forms.Form):
    organization = forms.ChoiceField(choices=ORGANIZATIONS, required=False)
    source = forms.ChoiceField(choices=SOURCES, required=False)
    status = forms.ChoiceField(choices=STATUS, required=False)
    favourite = forms.ChoiceField(choices=FAVOURITES, required=False)


class AwardsFilter(forms.Form):
    source = forms.ChoiceField(choices=SOURCES, required=False)
    organization = forms.ChoiceField(choices=ORGANIZATIONS, required=False)
    vendor = forms.ChoiceField(choices=VENDORS, required=False)
    value = forms.ChoiceField(choices=VALUES, required=False)
