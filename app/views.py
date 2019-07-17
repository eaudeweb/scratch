from django.views.generic.list import ListView
from .models import Tender


class TendersListView(ListView):
    model = Tender
    context_object_name = 'tenders'
    template_name = 'tenders_list.html'
