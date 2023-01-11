from datetime import timezone, datetime, date
import re

from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models import Q
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic import TemplateView, View
from django.urls import reverse
from elasticsearch_dsl import Q as elasticQ

from app.documents import TenderDoc, TenderDocumentDoc, AwardDoc
from app.forms import TendersFilter
from app.models import Tender, TenderDocument, Award,Tag
from app.views.base import BaseAjaxListingView


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
            tags = self.request.GET.getlist('tags')
            reset = any([
                source, organization, status, favourite, keyword, notice_type,
                seen,tags
            ])
            form = TendersFilter(
                initial={
                    "organization": organization,
                    "source": source,
                    "status": status,
                    "favourite": favourite,
                    "keyword": keyword,
                    "type": notice_type,
                    "seen": seen,
                    "tags":tags
                    
                }
            )
        else:
            form = TendersFilter()

        ungm_published_today |= (
                self.request.GET.get("ungm_published_today") == 'True')
        ungm_deadline_today |= (
                self.request.GET.get("ungm_deadline_today") == 'True')
        ted_published_today |= (
                self.request.GET.get("ted_published_today") == 'True')
        ted_deadline_today |= (
                self.request.GET.get("ted_deadline_today") == 'True')

        context["form"] = form
        context["reset"] = reset
        context["reset_url"] = '/tenders'
        context["ungm_published_today"] = ungm_published_today
        context["ungm_deadline_today"] = ungm_deadline_today
        context["ted_published_today"] = ted_published_today
        context["ted_deadline_today"] = ted_deadline_today

        return context


class TenderListAjaxView(BaseAjaxListingView):
    filter_names = [
        ('organization', 'organization'),
        ('source', 'source'),
        ('favourite', 'favourite'),
        ('has_keywords', 'has_keywords'),
        ('notice_type', 'notice_type'),
    ]
    order_fields = [
        'title', 'source', 'organization', 'deadline', 'published',
        'notice_type'
    ]
    case_sensitive_fields = ['title', 'source', 'organization', 'notice_type']
    model = Tender

    def format_data(self, object_list):
        data = [
            {
                'title': tender.marked_keyword_title,
                'url': reverse('tender_detail_view', kwargs={'pk': tender.id}),
                'source': tender.source,
                'organization': tender.organization,
                'deadline': 'Not specified' if not tender.deadline else (
                    tender.deadline.strftime("%m/%d/%Y, %H:%M")),
                'published': 'Not specified' if not tender.published else (
                    tender.published.strftime("%m/%d/%Y")),
                'notice_type': render_to_string(
                        'tenders_buttons.html', {'tender': tender}),
                'tags': ', '.join(tender.tags.values_list('name', flat=True))
                
            } for tender in object_list
        ]
        return data

    def order_data(self, request, tenders):
        tenders.order_by('-published')
        tenders = super(TenderListAjaxView, self).order_data(request, tenders)
        return tenders

    def filter_data(self, request):
        tenders = super(TenderListAjaxView, self).filter_data(request)
        tags_request = self.request.GET.get('tags')
        
        if tags_request:
            tags_request = tags_request.split(',')
            tags_request_list = [i for i in tags_request if i != '']
            if len(tags_request_list) > 0:
                tenders = tenders.filter(tags__name__in=tags_request_list)
 
        search = request.GET.get("search[value]")
        if search:
            tenders = Tender.objects.filter(
                Q(title__icontains=search) |
                Q(organization__icontains=search) |
                Q(notice_type=search)
            )

        status = self.request.GET.get("status")

        if status:
            awards = Award.objects.all()
            award_refs = [award.tender.reference for award in awards]
            if status == "open":
                tenders = tenders.exclude(
                    Q(reference__in=award_refs) | Q(deadline__lt=date.today()))
            else:
                tenders = tenders.filter(
                    Q(reference__in=award_refs) | Q(deadline__lt=date.today()))

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
        return tenders


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
        context["documents_set"] = TenderDocument.objects.filter(
            tender=self.object)
        context['tags_autocomplete'] = Tag.objects.all()
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


class TenderTagView(View):

    def post(self,request,pk):
        current_tender = Tender.objects.filter(id=pk)
        tender = current_tender[0]
        tag_received = request.POST['tag_name']

        if tender:
            tag, created = Tag.objects.get_or_create(name=tag_received)
            tender.tags.add(tag)
      
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reset_url'] = '/archive'
        return context


class TenderArchiveAjaxView(TenderListAjaxView):

    def get_objects(self):
        current_time = datetime.now(timezone.utc)
        tenders = Tender.objects.filter(
            deadline__lt=current_time, deadline__isnull=False)
        return tenders


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

    @staticmethod
    def update_award_fields(context, regex):
        for entry in context:
            entry["award"].tender.title = regex.sub(r'<mark>\1</mark>', entry["award"].tender.title)
            entry["award_vendors"] = regex.sub(r'<mark>\1</mark>', entry["award_vendors"])
            entry["award"].currency = regex.sub(r'<mark>\1</mark>', entry["award"].currency)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk'].replace('+', '|')

        # Find the tenders that have documents containing the input string
        result_tender_documents = TenderDocumentDoc.search().query(
            elasticQ(
                "multi_match",
                query=pk,
                fields=[
                    'name',
                    'content',
                ]
            )
        )
        tender_references = [
            o.reference
            for o in result_tender_documents if o.reference is not None
        ]

        # Find the tenders that match the input string and the tender ids of
        # the tender documents
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
            |
            elasticQ(
                "terms",
                reference=tender_references,
            )
        )

        result_awards = AwardDoc.search().query(
            elasticQ(
                "multi_match",
                query=pk,
                fields=[
                    'vendors_name',
                    'tender_title',
                    'currency',
                    'value',
                ]
            )
        )
        context['tenders'] = result_tenders.to_queryset()
        context['awards'] = [
            {
                "award": award,
                "award_vendors": award.get_vendors
            } for award in result_awards.to_queryset()
        ]

        regex = re.compile(rf'(\b({pk})\b(\s*({pk})\b)*)', re.I)

        tender_fields = ['title', 'description']

        SearchView.update_fields(context['tenders'], tender_fields, regex)
        SearchView.update_award_fields(context['awards'], regex)

        return context
