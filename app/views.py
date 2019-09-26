from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from .models import Tender, TenderDocument, Winner, Notification, WorkerLog, CPVCode, UNSPSCCode, Task
from django.core.management import get_commands, load_command_class
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
from django.core.management import call_command
from .forms import TendersFilter, AwardsFilter
from .forms import MAX, STEP, SearchForm
from app.documents import TenderDoc
from django.contrib.auth.models import User
from elasticsearch_dsl import Q as elasticQ
from django.db.models import Q
from django_q.tasks import async_task, result
from django_q.models import Success, Failure
from django.urls import reverse


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
        context["keyword_tenders"] = Tender.objects.filter(
            has_keywords=True
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
        context["worker_logs"] = WorkerLog.objects.order_by('-update')
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
        today = date.today()

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

            keyword = self.request.GET.get("keyword")
            if keyword:
                tenders = tenders.filter(has_keywords=keyword)

            notice_type = self.request.GET.get("type")
            if notice_type:
                tenders = tenders.filter(notice_type=notice_type)

            status = self.request.GET.get("status")
            if status:
                award_refs = [award.tender.reference for award in awards]
                if status == "open":
                    tenders = tenders.exclude(Q(reference__in=award_refs) | Q(deadline__lt=date.today()))
                else:
                    tenders = tenders.filter(Q(reference__in=award_refs) | Q(deadline__lt=date.today()))

            seen = self.request.GET.get("seen")
            if seen:
                if seen == "seen":
                    tenders = tenders.exclude(seen_by=None)
                else:
                    tenders = tenders.filter(seen_by=None)

            ungm_published_today = self.request.GET.get("ungm_published_today")
            ted_published_today = self.request.GET.get("ted_published_today")

            if (ungm_published_today == 'True') | (ted_published_today == 'True'):
                tenders = tenders.filter(published=today)

            ungm_deadline_today = self.request.GET.get("ungm_deadline_today")
            ted_deadline_today = self.request.GET.get("ted_deadline_today")

            if (ungm_deadline_today == 'True') | (ted_deadline_today == 'True'):
                tenders = tenders.filter(
                    deadline__year=today.year,
                    deadline__month=today.month,
                    deadline__day=today.day,
                )

        return tenders

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reset = False
        ungm_published_today = False
        ungm_deadline_today = False
        ted_published_today = False
        ted_deadline_today = False

        if self.request.GET.get("filter_button"):

            organization = self.request.GET.get("organization")
            source = self.request.GET.get("source")
            status = self.request.GET.get("status")
            favourite = self.request.GET.get("favourite")
            keyword = self.request.GET.get("keyword")
            notice_type = self.request.GET.get("type")
            seen = self.request.GET.get("seen")
            reset = any([source, organization, status, favourite, keyword, notice_type, seen])
            form = TendersFilter(
                initial={
                    "organization": organization,
                    "source": source,
                    "status": status,
                    "favourite": favourite,
                    "keyword": keyword,
                    "type": notice_type,
                    "seen": seen
                }
            )
        else:
            form = TendersFilter()

        ungm_published_today |= (self.request.GET.get("ungm_published_today") == 'True')
        ungm_deadline_today |= (self.request.GET.get("ungm_deadline_today") == 'True')
        ted_published_today |= (self.request.GET.get("ted_published_today") == 'True')
        ted_deadline_today |= (self.request.GET.get("ted_deadline_today") == 'True')

        context["form"] = form
        context["reset"] = reset
        context["reset_url"] = '/tenders'
        context["ungm_published_today"] = ungm_published_today
        context["ungm_deadline_today"] = ungm_deadline_today
        context["ted_published_today"] = ted_published_today
        context["ted_deadline_today"] = ted_deadline_today

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
        if deadline and deadline >= datetime.now(timezone.utc):
            deadline -= datetime.now(timezone.utc)
            context["deadline_in"] = self.deadline_in_string(deadline)
        context["documents_set"] = TenderDocument.objects.filter(tender=self.object)
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


class TenderSeenByView(View):
    def post(self, request, pk):
        current_tender = Tender.objects.filter(id=pk)
        state = request.POST["seen"]

        if state == "true" and request.user.is_authenticated:
            user = User.objects.get(username=request.user.username)
            current_tender.update(seen_by=user)
        else:
            current_tender.update(seen_by=None)

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


class ContractAwardDetailView(LoginRequiredMixin, DetailView):
    model = Winner
    template_name = "detail_award.html"
    context_object_name = "winner"
    login_url = "/login"
    redirect_field_name = "login_view"


class SearchView(LoginRequiredMixin, TemplateView):
    template_name = "search_results.html"
    login_url = "/login"
    redirect_field_name = "login_view"

    def get_queryset(self):
        pk = self.kwargs['pk'].replace('+', ' ')

        result = TenderDoc.search().query(
            elasticQ(
                "multi_match",
                query=pk,
                fields=[
                    'title',
                    'organization',
                    'source',
                    'reference',
                    'unspsc_codes',
                    'cpv_codes',
                    'description',
                ]
            )
        )
        tenders = result.to_queryset()

        awards = Winner.objects.all()

        # if self.request.GET.get("filter_button"):
        #     organization = self.request.GET.get("organization")
        #     if organization:
        #         tenders = tenders.filter(organization=organization)
        #
        #     source = self.request.GET.get("source")
        #     if source:
        #         tenders = tenders.filter(source=source)
        #
        #     favourite = self.request.GET.get("favourite")
        #     if favourite:
        #         tenders = tenders.filter(favourite=favourite)
        #
        #     keyword = self.request.GET.get("keyword")
        #     if keyword:
        #         tenders = tenders.filter(keyword=keyword)
        #
        #     status = self.request.GET.get("status")
        #     if status:
        #         award_refs = [award.tender.reference for award in awards]
        #         if status == "open":
        #             tenders = tenders.exclude(reference__in=award_refs)
        #         else:
        #             tenders = tenders.filter(reference__in=award_refs)

        return tenders

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #context["reset_url"] = '/search/' + self.kwargs['pk']
        tenders = []
        awards = []

        pk = self.kwargs['pk'].replace('+', ' ')

        result = TenderDoc.search().query(
            elasticQ(
                "multi_match",
                query=pk,
                fields=[
                    'title',
                    'organization',
                    'source',
                    'reference',
                    'unspsc_codes',
                    'cpv_codes',
                    'description',
                ]
            )
        )
        tenders = result.to_queryset()
        context['tenders'] = tenders
        context['awards'] = awards
        return context


class ManagementView(LoginRequiredMixin, TemplateView):
    template_name = "management.html"
    login_url = "/login"
    redirect_field_name = "login_view"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        def update_fields(task, class_obj):
            try:
                obj = class_obj.objects.get(id=task.id)
                task.stopped = obj.stopped
                task.status = 'success' if obj.success else 'error'
                task.output = obj.result

                task.save()
                return True
            except class_obj.DoesNotExist:
                return False

        available_commands = get_commands()
        module_commands = [cmd for cmd in available_commands.keys() if available_commands[cmd] == 'app']

        commands = []

        for command_name in module_commands:
            try:
                base_class = load_command_class('app', command_name)

                commands.append(
                    {
                        'name': command_name,
                        'help': base_class.help or '',
                        'params': base_class.get_parameters(),
                    }
                )
            except (ModuleNotFoundError, AttributeError):
                continue

        tasks = Task.objects.all().order_by('-started')

        for task in tasks:
            if task.status == 'processing' and not update_fields(task, Success):
                update_fields(task, Failure)

        context["commands"] = commands
        context['tasks'] = tasks

        return context

    def post(self, request):

        query = self.request.POST.dict()

        def sanitize(field):
            return bool(field) and (field == 'on' or int(field))

        command_name = ''
        temp_parameters = []

        for entry in query:
            if 'csrfmiddlewaretoken' in entry:
                continue

            try:
                _, param = entry.split('__')
                temp_parameters.append(
                    {
                        'command': entry,
                        'parameter': param,
                        'value': sanitize(query[entry]),
                    }
                )
            except ValueError:
                command_name = entry

        parsed_parameters = [x for x in temp_parameters if command_name in x['command']]
        parameters = {x['parameter']: x['value'] for x in parsed_parameters if x['value'] is not False}
        formatted_parameters = ', '.join([': '.join((str(k), str(v))) for k, v in parameters.items()])

        if request.user.is_authenticated and request.user.is_superuser:
            id = async_task(call_command, command_name, **parameters)

            t = Task(
                id=id,
                args=command_name,
                kwargs=formatted_parameters,
                started=datetime.now(),
            )

            t.save()

            return redirect('management_view')


class ManagementDeleteView(LoginRequiredMixin, View):
    login_url = "/login"
    redirect_field_name = "login_view"

    def get(self, request, pk):
        task = Task.objects.get(id=pk)
        task.delete()
        return redirect(reverse('management_view') + '#logs')


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
