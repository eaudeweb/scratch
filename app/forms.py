from django import forms
from .models import Tender


class TendersFilter(forms.Form):
    organization = forms.ChoiceField()
    source = forms.ChoiceField(choices=[('', 'All tenders'),
                                        ('UNGM', 'UNGM'),
                                        ('TED', 'TED'),
                                        ])
    status = forms.ChoiceField(choices=[('', 'All tenders'),
                                        ('open', 'OPEN'),
                                        ('closed', 'CLOSED'),
                                        ])
    favourite = forms.ChoiceField(choices=[('', 'All tenders'),
                                           ('True', 'Yes'),
                                           ('False', 'No'),
                                           ])

    def __init__(self):
        super(TendersFilter, self).__init__()
        organizations = Tender.objects.values_list('organization',
                                                   flat=True).distinct()
        self.organization.choices = [('', 'All organizations')] + [
            (org, org) for org in organizations
        ]