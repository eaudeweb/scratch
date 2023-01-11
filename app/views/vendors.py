from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.list import ListView

from app.forms import MAX, STEP, AwardsFilter
from app.models import Vendor
from app.views import BaseAjaxListingView


class VendorsListView(LoginRequiredMixin, ListView):
    model = Vendor
    context_object_name = "vendors"
    template_name = "vendors_list.html"
    login_url = "/login"
    redirect_field_name = "login_view"


class VendorsListAjaxView(BaseAjaxListingView):
    order_fields = ['name', 'email', 'contact_name']
    case_sensitive_fields = ['name']
    model = Vendor

    def format_data(self, object_list):
        data = [
            {
                'name': vendor.name,
                'url': reverse('vendor_detail_view', kwargs={'pk': vendor.id}),
                'email': vendor.email,
                'contact_name': vendor.contact_name

            } for vendor in object_list
        ]
        return data

    def filter_data(self, request):
        vendors = super(VendorsListAjaxView, self).filter_data(request)

        search = request.GET.get("search[value]")
        if search:
            vendors = Vendor.objects.filter(
                Q(name__icontains=search) |
                Q(contact_name__icontains=search)
            )

        value = self.request.GET.get("value")
        if value:
            if value == "max":
                vendors = vendors.filter(value__gt=MAX - STEP)
            else:
                value = float(value)
                vendors = vendors.filter(value__range=(value, value + STEP))

        return vendors

    def order_data(self, request, vendors):
        # vendors.order_by('-name')
        vendors = super(VendorsListAjaxView, self).order_data(request, vendors)
        return vendors


class VendorDetailView(LoginRequiredMixin, DetailView):
    model = Vendor
    template_name = "detail_vendor.html"
    context_object_name = "vendor"
    login_url = "/login"
    redirect_field_name = "login_view"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reset = False
        if self.request.GET.get("filter_button"):
            organization = self.request.GET.get("organization")
            source = self.request.GET.get("source")
            value = self.request.GET.get("value")
            reset = any([source, organization, context["vendor"], value])
            form = AwardsFilter(
                initial={
                    "organization": organization,
                    "source": source,
                    "vendor": context["vendor"],
                    "value": value,
                }
            )
        else:
            form = AwardsFilter(
                initial={
                    "organization": None,
                    "source": None,
                    "vendor": context["vendor"],
                    "value": None,
                }
            )

        context["form"] = form
        context["reset"] = reset
        return context
