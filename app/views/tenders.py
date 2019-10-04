from datetime import timezone, datetime, date
import json
import re

from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic import TemplateView, View
from django.urls import reverse
from elasticsearch_dsl import Q as elasticQ

from app.documents import TenderDoc, WinnerDoc
from app.forms import TendersFilter
from app.models import Tender, TenderDocument, Winner

class TendersListView(LoginRequiredMixin, ListView):
    model = Tender
    template_name = "tenders_list.html"
    context_object_name = "tenders"
    login_url = "/login"
    redirect_field_name = "login_view"

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

class TenderListAjaxView(View):

    def get(self, request):
        tenders = self.get_data(request)
        return HttpResponse(json.dumps(tenders, cls=DjangoJSONEncoder),
                            content_type='application/json')

    def filter_by_field(self, request, tenders):
        filter_names = ['organization', 'source', 'favourite', 'has_keywords', 'notice_type']
        filters = {}
        for filter_name in filter_names:
            filter_value = self.request.GET.get(filter_name)
            if filter_value:
                filters.update({filter_name: filter_value})

        status = self.request.GET.get("status")

        if status:
            awards = Winner.objects.all()
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

        today = date.today()

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

        tenders = tenders.filter(**filters)
        return tenders

    def filter_data(self, request):
        tenders = Tender.objects.all()
        
        search = request.GET.get("search[value]")
        if search:
            tenders = Tender.objects.filter(
                           Q(title__icontains=search)|
                           Q(organization__icontains=search)|
                           Q(notice_type=search)
                       )
        tenders = self.filter_by_field(request, tenders)
        return tenders

    def order_data(self, request, tenders):
        fields = ['title', 'source', 'organization', 'deadline', 'published', 'notice_type']
        field = request.GET.get('order[0][column]')
        sort_types = {
            'asc': '',
            'desc': '-',
        }
        sort_type =  request.GET.get('order[0][dir]')
        if field and sort_type:
            return tenders.order_by(sort_types[sort_type] + fields[int(field)])
        return tenders.order_by('-published')

    def get_data(self, request):

        length = int(request.GET.get('length'))
        start = int(request.GET.get("start"))
        draw = int(request.GET.get("draw"))

        tenders = self.filter_data(request)
        tenders = self.order_data(request, tenders)
        tenders_count = tenders.count()
        tenders_filtered_count = tenders_count

        paginator = Paginator(tenders, length)
        page_number = start / length + 1

        try:
            object_list = paginator.page(page_number).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(1).object_list

        data = [
            {
                'title': tender.marked_keyword_title,
                'url': reverse('tender_detail_view', kwargs={'pk':tender.id}),
                'source': tender.source,
                'organization': tender.organization,
                'deadline': 'Not specified' if not tender.deadline  else tender.deadline.strftime("%m/%d/%Y, %H:%M"),
                'published': 'Not specified' if not tender.published else tender.published.strftime("%m/%d/%Y"),
                'notice_type': render_to_string('tenders_buttons.html', {'tender': tender})
            } for tender in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': tenders_count,
            'recordsFiltered': tenders_filtered_count,
            'data': data,
        }

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

class SearchView(LoginRequiredMixin, TemplateView):
    template_name = "search_results.html"
    login_url = "/login"
    redirect_field_name = "login_view"

    @staticmethod
    def update_fields(context, fields, regex):
        for entry in context:
            for item in fields:
                field = getattr(entry, item)
                setattr(entry, item, regex.sub(r'<mark>\1</mark>', field))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk'].replace('+', '|')

        result_tenders = TenderDoc.search().query(
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

        result_awards = WinnerDoc.search().query(
            elasticQ(
                "multi_match",
                query=pk,
                fields=[
                    'vendor',
                    'tender_title',
                    'currency',
                    'value',
                ]
            )
        )

        context['tenders'] = result_tenders.to_queryset()
        context['awards'] = result_awards.to_queryset()

        regex = re.compile(rf'(\b({pk})\b(\s*({pk})\b)*)', re.I)

        tender_fields = ['title', 'description']
        award_fields = ['title', 'vendor', 'value', 'currency']

        SearchView.update_fields(context['tenders'], tender_fields, regex)
        SearchView.update_fields(context['awards'], award_fields, regex)

        return context
