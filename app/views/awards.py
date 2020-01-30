from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models.functions import Lower
from django.template.defaultfilters import floatformat
from django.template.loader import render_to_string
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.urls import reverse
from app.forms import AwardsFilter, MAX, STEP
from app.models import Award
from app.views import BaseAjaxListingView


class ContractAwardsListView(LoginRequiredMixin, ListView):
    model = Award
    context_object_name = "awards"
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


class ContractAwardsListAjaxView(BaseAjaxListingView):
    filter_names = [
        ('organization', 'tender__organization'),
        ('source', 'tender__source'),
        ('vendor', 'vendors__name'),
    ]
    order_fields = ['tender__title', 'tender__source', 'tender__organization', 
                    'award_date', '', 'value', 'currency']
    case_sensitive_fields = ['tender__title', 'tender__source', 'tender__organization']
    model = Award

    def format_data(self, object_list):
        data = [
            {
                'title': award.tender.title,
                'url': reverse('contract_awards_detail_view', kwargs={'pk': award.id}),
                'source': award.tender.source,
                'organization': award.tender.organization,
                'award_date': 'Not specified' if not award.award_date  else award.award_date.strftime("%m/%d/%Y"),
                'vendor': render_to_string('award_vendors.html', {'vendors': award.vendors.all()}),
                'value': floatformat(award.value, '0'),
                'currency': award.currency,

            } for award in object_list
        ]
        return data

    def filter_data(self, request):
        awards = super(ContractAwardsListAjaxView, self).filter_data(request)
        
        search = request.GET.get("search[value]")
        if search:
            awards = Award.objects.filter(
                        Q(tender__title__icontains=search)|
                        Q(tender__organization__icontains=search)|
                        Q(vendors__name__icontains=search)
                    )

        value = self.request.GET.get("value")
        if value:
            if value == "max":
                awards = awards.filter(value__gt=MAX - STEP)
            else:
                value = float(value)
                awards = awards.filter(value__range=(value, value + STEP))

        return awards

    def order_data(self, request, awards):
        awards.order_by('-award_date')
        awards = super(ContractAwardsListAjaxView, self).order_data(request, awards)
        return awards


class ContractAwardDetailView(LoginRequiredMixin, DetailView):
    model = Award
    template_name = "detail_award.html"
    context_object_name = "award"
    login_url = "/login"
    redirect_field_name = "login_view"
