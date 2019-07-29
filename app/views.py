from django.http import HttpResponse
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from .models import Tender, Winner
from django.utils.http import is_safe_url
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import (
    REDIRECT_FIELD_NAME,
    login as auth_login,
    logout as auth_logout,
)
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView, RedirectView
from django.views.generic import View
from datetime import timezone, datetime
from .forms import TendersFilter


class TendersListView(LoginRequiredMixin, ListView):
    model = Tender
    template_name = "tenders_list.html"
    context_object_name = "tenders"
    login_url = "/app/login"
    redirect_field_name = "login_view"

    def get_queryset(self):
        tenders = Tender.objects.all()

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

        return tenders

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reset = False
        if self.request.GET.get("filter_button"):
            organization = self.request.GET.get("organization")
            source = self.request.GET.get("source")
            favourite = self.request.GET.get("favourite")
            reset = any([source, organization, favourite])
            form = TendersFilter(
                initial={
                    "organization": organization,
                    "source": source,
                    "favourite": favourite,
                }
            )
        else:
            form = TendersFilter()

        context["form"] = form
        context["reset"] = reset
        return context


class TenderDetailView(LoginRequiredMixin, DetailView):
    model = Tender
    template_name = "detail_tender.html"
    context_object_name = "tender"
    login_url = "/app/login"
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


class ContractAwardsListVew(LoginRequiredMixin, ListView):
    model = Winner
    context_object_name = "awards"
    template_name = "contract_awards_list.html"
    login_url = "/app/login"
    redirect_field_name = "login_view"


class LoginView(FormView):
    success_url = "/app/tenders"
    form_class = AuthenticationForm
    redirect_field_name = REDIRECT_FIELD_NAME
    template_name = "login.html"

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
    url = "/app/login"

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)
