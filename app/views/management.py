from datetime import timezone, datetime, date, timedelta

from django.conf import settings
from django.contrib.auth import (
    REDIRECT_FIELD_NAME,
    login as auth_login,
    logout as auth_logout,
)
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.management import (
    call_command, get_commands, load_command_class
)
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import (
    FormView, RedirectView, TemplateView, View
)
from django.urls import reverse
from django_q.tasks import async_task
from django_q.models import Success, Failure

from app.forms import SearchForm
from app.models import (
    CPVCode, UNSPSCCode, Task, Tender, Award, WorkerLog
)
from app.utils import emails_to_notify


class HomepageView(TemplateView):
    template_name = "homepage.html"

    def post(self, request):

        form = SearchForm(request.POST)

        if form.is_valid() and request.user.is_authenticated:
            return redirect('search_results', pk=form.cleaned_data['terms'].replace(' ', '+'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = date.today()
        now = datetime.now(timezone.utc)
        deadline_gte = now.replace(hour=0, minute=0, second=0, microsecond=0)
        deadline_lt = now.replace(
            hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

        context["ungm_tenders"] = Tender.objects.filter(source="UNGM").count()
        context["ted_tenders"] = Tender.objects.filter(source="TED").count()
        if self.request.user.is_authenticated:
            context["favorite_tenders"] = self.request.user.favorite_tenders.count()
        else:
            context["favorite_tenders"] = 0
        context["keyword_tenders"] = Tender.objects.filter(
            has_keywords=True
        ).count()
        context["awards"] = Award.objects.all().count()
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
            deadline__gte=deadline_gte, deadline__lt=deadline_lt, source="UNGM"
        ).count()
        context["ted_deadline_today"] = Tender.objects.filter(
            deadline__gte=deadline_gte, deadline__lt=deadline_lt, source="TED"
        ).count()

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
        module_commands = [
            cmd for cmd in available_commands.keys()
            if available_commands[cmd] == 'app' and cmd not in (
                "notify_user_favorites", "user_deadline_notifications"
            )
        ]

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

        parsed_parameters = [
            x for x in temp_parameters if command_name in x['command']]
        parameters = {x['parameter']: x['value']
                      for x in parsed_parameters if x['value'] is not False}
        formatted_parameters = ', '.join(
            [': '.join((str(k), str(v))) for k, v in parameters.items()])

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


class OverviewPageView(LoginRequiredMixin, TemplateView):
    template_name = "overview.html"
    login_url = "/login"
    redirect_field_name = "login_view"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["deadline_notifications"] = settings.DEADLINE_NOTIFICATIONS
        context["emails"] = emails_to_notify()
        context["worker_logs"] = WorkerLog.objects.order_by('-update')
        context["unspscs_codes"] = UNSPSCCode.objects.all()
        context["cpv_codes"] = CPVCode.objects.all()

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
        if not url_has_allowed_host_and_scheme(
            url=redirect_to, allowed_hosts=self.request.get_host()
        ):
            redirect_to = self.success_url
        return redirect_to


class LogoutView(RedirectView):
    url = "/login"

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)
