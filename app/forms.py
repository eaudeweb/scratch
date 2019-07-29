from django import forms
from .models import Tender

SOURCES = [('', 'All tenders'),
          ('UNGM', 'UNGM'),
          ('TED', 'TED'),
          ]

STATUS = [('', 'All tenders'),
          ('open', 'OPEN'),
          ('closed', 'CLOSED'),
          ]

FAVOURITES = [('', 'All tenders'),
              ('True', 'Yes'),
              ('False', 'No'),
              ]

ORGANIZATIONS_LIST = Tender.objects.values_list('organization',
                                                flat=True).distinct()
ORGANIZATIONS = [('', 'All organizations')] + [
            (org, org) for org in ORGANIZATIONS_LIST
            ]


class TendersFilter(forms.Form):
    organization = forms.ChoiceField(choices=ORGANIZATIONS, required=False)
    source = forms.ChoiceField(choices=SOURCES, required=False)
    status = forms.ChoiceField(choices=STATUS, required=False)
    favourite = forms.ChoiceField(choices=FAVOURITES, required=False)
