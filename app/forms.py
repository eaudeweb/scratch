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

KEYWORDS = [
    ("", "All tenders"),
    ("True", "Yes"),
    ("False", "No")
]

SEEN = [
    ("", "All tenders"),
    ("seen", "Yes"),
    ("unseen", "No")
]

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
    organization = forms.ChoiceField(required=False)
    source = forms.ChoiceField(choices=SOURCES, required=False)
    status = forms.ChoiceField(choices=STATUS, required=False)
    favourite = forms.ChoiceField(choices=FAVOURITES, required=False)
    keyword = forms.ChoiceField(choices=KEYWORDS, required=False)
    type = forms.ChoiceField(required=False)
    seen = forms.ChoiceField(choices=SEEN, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        organizations_list = (
            Tender.objects.order_by("organization")
            .values_list("organization", flat=True)
            .distinct()
        )
        self.fields["organization"].choices = [("", "All organizations")] + [
            (org, org) for org in organizations_list
        ]
        types_list = Tender.objects.values_list(
            "notice_type", flat=True
        ).distinct()
        self.fields["type"].choices = [("", "All notice types")] + [
            (tp, tp) for tp in types_list
        ]


class AwardsFilter(forms.Form):
    source = forms.ChoiceField(choices=SOURCES, required=False)
    organization = forms.ChoiceField(required=False)
    vendor = forms.ChoiceField(required=False)
    value = forms.ChoiceField(choices=VALUES, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        organizations_list = (
            Tender.objects.order_by("organization")
            .values_list("organization", flat=True)
            .distinct()
        )
        self.fields["organization"].choices = [("", "All organizations")] + [
            (org, org) for org in organizations_list
        ]
        vendors_list = Winner.objects.values_list(
            "vendors__name", flat=True
        ).distinct()
        self.fields["vendor"].choices = [("", "All vendors")] + [
            (vendor, vendor) for vendor in vendors_list
        ]


class SearchForm(forms.Form):
    terms = forms.CharField(max_length=255)
