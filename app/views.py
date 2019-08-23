from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from .models import Tender, Winner, Notification, WorkerLog, CPVCode, UNSPSCCode
from django.utils.http import is_safe_url
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import (
    REDIRECT_FIELD_NAME,
    login as auth_login,
    logout as auth_logout,
)
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView, RedirectView, TemplateView
from django.views.generic import View
from datetime import timezone, datetime, date, timedelta
from .forms import TendersFilter, AwardsFilter
from .forms import MAX, STEP, SearchForm
from app.documents import TenderDoc
from elasticsearch_dsl import Q


class HomepageView(TemplateView):
    template_name = "homepage.html"

    def post(self, request):
        form = SearchForm(request.POST)

        if form.is_valid() and request.user.is_authenticated:
            return redirect('search_results', pk=form.cleaned_data['terms'].replace(' ', '+'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = date.today()
        tomorrow = today + timedelta(days=1)

        context["ungm_tenders"] = Tender.objects.filter(source="UNGM").count()
        context["ted_tenders"] = Tender.objects.filter(source="TED").count()
        context["favorite_tenders"] = Tender.objects.filter(
            favourite=True
        ).count()
        context["winners"] = Winner.objects.all().count()
        context["expired_tenders"] = Tender.objects.filter(
            deadline__lt=datetime.now(timezone.utc)
        ).count()
        context["ungm_published_today"] = Tender.objects.filter(
            published__exact=today, source="UNGM"
        ).count()
        context["ted_published_today"] = Tender.objects.filter(
            published__exact=today, source="TED"
        ).count()
        context["ungm_deadline_today"] = Tender.objects.filter(
            deadline__gte=today, deadline__lt=tomorrow, source="UNGM"
        ).count()
        context["ted_deadline_today"] = Tender.objects.filter(
            deadline__gte=today, deadline__lt=tomorrow, source="TED"
        ).count()

        return context


class OverviewPageView(LoginRequiredMixin, TemplateView):
    template_name = "overview.html"
    login_url = "/login"
    redirect_field_name = "login_view"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["deadline_notifications"] = settings.DEADLINE_NOTIFICATIONS
        context["emails"] = Notification.objects.all()
        context["worker_logs"] = WorkerLog.objects.order_by('-update').distinct('update')
        context["unspscs_codes"] = UNSPSCCode.objects.all()
        context["cpv_codes"] = CPVCode.objects.all()

        return context


class TendersListView(LoginRequiredMixin, ListView):
    model = Tender
    template_name = "tenders_list.html"
    context_object_name = "tenders"
    login_url = "/login"
    redirect_field_name = "login_view"

    def get_queryset(self):
        tenders = Tender.objects.all()
        awards = Winner.objects.all()

        if self.request.GET.get("filter_button"):
            organization = self.request.GET.get("organization")
            if organization:
                tenders = tenders.filter(organization=organization)

            source = self.request.GET.get("source")
            if source:
                tenders = tenders.filter(source=source)

            favourite = self.request.GET.get("favourite")
            if favourite:
                tenders = tenders.filter(favourite=favourite)

            status = self.request.GET.get("status")
            if status:
                award_refs = [award.tender.reference for award in awards]
                if status == "open":
                    tenders = tenders.exclude(reference__in=award_refs)
                else:
                    tenders = tenders.filter(reference__in=award_refs)

        return tenders

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reset = False
        if self.request.GET.get("filter_button"):

            organization = self.request.GET.get("organization")
            source = self.request.GET.get("source")
            status = self.request.GET.get("status")
            favourite = self.request.GET.get("favourite")
            reset = any([source, organization, status, favourite])
            form = TendersFilter(
                initial={
                    "organization": organization,
                    "source": source,
                    "status": status,
                    "favourite": favourite,
                }
            )
        else:
            form = TendersFilter()

        context["form"] = form
        context["reset"] = reset
        context["reset_url"] = '/tenders'
        return context


class TenderDetailView(LoginRequiredMixin, DetailView):
    model = Tender
    template_name = "detail_tender.html"
    context_object_name = "tender"
    login_url = "/login"
    redirect_field_name = "login_view"

    @staticmethod
    def deadline_in_string(tdelta):
        d_val = tdelta.days
        d_string = "days" if d_val != 1 else "day"

        h_val, rest = divmod(tdelta.seconds, 3600)
        h_string = "hours" if h_val != 1 else "hour"

        m_val, rest = divmod(rest, 60)
        m_string = "minutes" if m_val != 1 else "minute"

        return "{} {} {} {} {} {}".format(
            d_val, d_string, h_val, h_string, m_val, m_string
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        deadline = self.object.deadline
        if deadline:
            deadline -= datetime.now(timezone.utc)
            context["deadline_in"] = self.deadline_in_string(deadline)
        return context


class TenderFavouriteView(View):
    def post(self, request, pk):
        current_tender = Tender.objects.filter(id=pk)
        state = request.POST["favourite"]

        if state == "true":
            current_tender.update(favourite=True)
        else:
            current_tender.update(favourite=False)

        return HttpResponse("Success!")


class TenderDeleteView(View):
    def post(self, request, pk):
        success_url = "/tenders"
        Tender.objects.filter(id=pk).delete()
        return HttpResponse(success_url)


class TenderArchiveView(TendersListView):
    template_name = "tenders_archive.html"
    context_object_name = "archive"
    login_url = "/login"
    redirect_field_name = "login_view"

    def get_queryset(self):
        tenders = super().get_queryset()
        current_time = datetime.now(timezone.utc)
        archive = []
        for tender in tenders:
            if tender.deadline and current_time > tender.deadline:
                archive.append(tender)
        return archive

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reset_url'] = '/archive'
        return context


class ContractAwardsListView(LoginRequiredMixin, ListView):
    model = Winner
    context_object_name = "winners"
    template_name = "contract_awards_list.html"
    login_url = "/login"
    redirect_field_name = "login_view"

    def get_queryset(self):
        awards = Winner.objects.all()

        if self.request.GET.get("filter_button"):
            organization = self.request.GET.get("organization")
            if organization:
                awards = awards.filter(tender__organization=organization)

            source = self.request.GET.get("source")
            if source:
                awards = awards.filter(tender__source=source)

            vendor = self.request.GET.get("vendor")
            if vendor:
                awards = awards.filter(vendor=vendor)

            value = self.request.GET.get("value")
            if value:
                if value == "max":
                    awards = awards.filter(value__gt=MAX - STEP)
                else:
                    value = float(value)
                    awards = awards.filter(value__range=(value, value + STEP))

        return awards

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


class SearchView(TendersListView):

    def get_queryset(self):
        pk = self.kwargs['pk'].replace('+', ' ')

        result = TenderDoc.search().query(
            Q(
                "multi_match",
                query=pk,
                fields=[
                    'title',
                    'organization',
                    'source',
                    'reference',
                    'unspsc_codes',
                    'cpv_codes'
                ]
            )
        )

        tenders = result.to_queryset()
        awards = Winner.objects.all()

        if self.request.GET.get("filter_button"):
            organization = self.request.GET.get("organization")
            if organization:
                tenders = tenders.filter(organization=organization)

            source = self.request.GET.get("source")
            if source:
                tenders = tenders.filter(source=source)

            favourite = self.request.GET.get("favourite")
            if favourite:
                tenders = tenders.filter(favourite=favourite)

            status = self.request.GET.get("status")
            if status:
                award_refs = [award.tender.reference for award in awards]
                if status == "open":
                    tenders = tenders.exclude(reference__in=award_refs)
                else:
                    tenders = tenders.filter(reference__in=award_refs)

        return tenders

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reset_url"] = '/search/' + self.kwargs['pk']
        return context


class LoginView(FormView):
    success_url = "/tenders"
    form_class = AuthenticationForm
    redirect_field_name = REDIRECT_FIELD_NAME
    template_name = "login.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('homepage_view')
        return super(LoginView, self).get(request, *args, **kwargs)

    @method_decorator(sensitive_post_parameters("password"))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        request.session.set_test_cookie()

        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        auth_login(self.request, form.get_user())

        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()

        return super(LoginView, self).form_valid(form)

    def get_success_url(self):
        redirect_to = self.request.GET.get(self.redirect_field_name)
        if not is_safe_url(
            url=redirect_to, allowed_hosts=self.request.get_host()
        ):
            redirect_to = self.success_url
        return redirect_to


class LogoutView(RedirectView):
    url = "/login"

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)
