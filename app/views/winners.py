from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models.functions import Lower
from django.template.defaultfilters import floatformat
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.urls import reverse
from app.forms import AwardsFilter, MAX, STEP
from app.models import Winner
from app.views import BaseAjaxListingView


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


class ContractAwardsListAjaxView(BaseAjaxListingView):
    filter_names = [
        ('organization', 'tender__organization'),
        ('source', 'tender__source'),
        ('vendor', 'vendor__name'),
    ]
    order_fields = ['tender__title', 'tender__source', 'tender__organization',
                    'award_date', 'vendor__name', 'value', 'currency']
    case_sensitive_fields = ['tender__title', 'tender__source', 'tender__organization', 'vendor__name']
    model = Winner

    def format_data(self, object_list):
        data = [
            {
                'title': winner.tender.title,
                'url': reverse('contract_awards_detail_view', kwargs={'pk': winner.id}),
                'source': winner.tender.source,
                'organization': winner.tender.organization,
                'award_date': 'Not specified' if not winner.award_date else winner.award_date.strftime("%m/%d/%Y"),
                'vendor': winner.vendor.name,
                'value': floatformat(winner.value, '0'),
                'currency': winner.currency,

            } for winner in object_list
        ]
        return data

    def filter_data(self, request):
        awards = super(ContractAwardsListAjaxView, self).filter_data(request)
        
        search = request.GET.get("search[value]")
        if search:
            awards = Winner.objects.filter(
                        Q(tender__title__icontains=search) |
                        Q(tender__organization__icontains=search) |
                        Q(vendor__name=search)
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
        awards.order_by(Lower('vendor__name')).reverse()
        awards = super(ContractAwardsListAjaxView, self).order_data(request, awards)
        return awards


class ContractAwardDetailView(LoginRequiredMixin, DetailView):
    model = Winner
    template_name = "detail_award.html"
    context_object_name = "winner"
    login_url = "/login"
    redirect_field_name = "login_view"
