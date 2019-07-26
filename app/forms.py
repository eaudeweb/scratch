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

    def __init__(self, *args, **kwargs):
        super(TendersFilter, self).__init__(*args, **kwargs)
        organizations = Tender.objects.values_list('organization',
                                                   flat=True).distinct()
        self.fields['organization'].choices = [('', 'All organizations')] + [
            (org, org) for org in organizations
        ]
        self.fields['organization'].required = False
        self.fields['favourite'].required = False
        self.fields['source'].required = False
        self.fields['status'].required = False
