import json

from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import Lower
from django.template.defaultfilters import floatformat
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic import TemplateView, View
from django.urls import reverse
from app.forms import AwardsFilter, MAX, STEP
from app.models import Winner

class ContractAwardsListView(LoginRequiredMixin, ListView):
    model = Winner
    context_object_name = "winners"
    template_name = "contract_awards_list.html"
    login_url = "/login"
    redirect_field_name = "login_view"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reset = False
        if self.request.GET.get("filter_button"):
            organization = self.request.GET.get("organization")
            source = self.request.GET.get("source")
            vendor = self.request.GET.get("vendor")
            value = self.request.GET.get("value")
            reset = any([source, organization, vendor, value])
            form = AwardsFilter(
                initial={
                    "organization": organization,
                    "source": source,
                    "vendor": vendor,
                    "value": value,
                }
            )
        else:
            form = AwardsFilter()

        context["form"] = form
        context["reset"] = reset
        return context

class ContractAwardsListAjaxView(View):

    def get(self, request):
        awards = self.get_data(request)
        return HttpResponse(json.dumps(awards, cls=DjangoJSONEncoder),
                            content_type='application/json')

    def filter_by_field(self, request, awards):
        filter_names = [
            ('organization', 'tender__organization'),
            ('source', 'tender__source'),
            ('vendor', 'vendor__name'),
        ]
        filters = {}
        for filter_name, filter_field in filter_names:
            filter_value = self.request.GET.get(filter_name)

            if filter_value:
                filters.update({filter_field: filter_value})

        awards = awards.filter(**filters)

        value = self.request.GET.get("value")
        if value:
            if value == "max":
                awards = awards.filter(value__gt=MAX - STEP)
            else:
                value = float(value)
                awards = awards.filter(value__range=(value, value + STEP))

        return awards

    def filter_data(self, request):
        awards = Winner.objects.all()
        
        search = request.GET.get("search[value]")
        if search:
            awards = Winner.objects.filter(
                        Q(tender__title__icontains=search)|
                        Q(tender__organization__icontains=search)|
                        Q(vendor__name=search)
                    )
        awards = self.filter_by_field(request, awards)
        return awards

    def order_data(self, request, awards):
        fields = ['tender__title', 'tender__source', 'tender__organization', 'award_date', 'vendor__name', 'value', 'currency']
        case_sensitive_fields = ['tender__title', 'tender__source', 'tender__organization', 'vendor__name']

        field = request.GET.get('order[0][column]')
        sort_type =  request.GET.get('order[0][dir]')
        if field and sort_type:
            field_name = fields[int(field)]
            if field_name in case_sensitive_fields:
                field_name =  Lower(fields[int(field)])
            awards = awards.order_by(field_name)
            if sort_type == 'desc':
                return awards.reverse()
            return awards
        return awards.order_by(Lower(vendor__name)).reverse()

    def get_data(self, request):

        length = int(request.GET.get('length'))
        start = int(request.GET.get("start"))
        draw = int(request.GET.get("draw"))

        awards = self.filter_data(request)
        awards = self.order_data(request, awards)
        awards_count = awards.count()
        awards_filtered_count = awards_count

        paginator = Paginator(awards, length)
        page_number = start / length + 1

        try:
            object_list = paginator.page(page_number).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(1).object_list
        data = [
            {
                'title': winner.tender.title,
                'url': reverse('contract_awards_detail_view', kwargs={'pk':winner.id}),
                'source': winner.tender.source,
                'organization': winner.tender.organization,
                'award_date': 'Not specified' if not winner.award_date  else winner.award_date.strftime("%m/%d/%Y"),
                'vendor': winner.vendor.name,
                'value': floatformat(winner.value, '0'),
                'currency': winner.currency,

            } for winner in object_list
        ]
        return {
            'draw': draw,
            'recordsTotal': awards_count,
            'recordsFiltered': awards_filtered_count,
            'data': data,
        }

class ContractAwardDetailView(LoginRequiredMixin, DetailView):
    model = Winner
    template_name = "detail_award.html"
    context_object_name = "winner"
    login_url = "/login"
    redirect_field_name = "login_view"