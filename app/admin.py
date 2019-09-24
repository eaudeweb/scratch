from django.contrib import admin
from .models import (Tender, TenderDocument, Winner, WorkerLog, Notification,
                     UNSPSCCode, CPVCode, TedCountry, Task, Keyword)


class TenderAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'notice_type', 'organization', 'published',
                    'deadline', 'url', 'source', 'unspsc_codes', 'favourite', 'has_keywords']
    search_fields = ['title', 'notice_type', 'published', 'deadline', 'source',
                     'organization', 'unspsc_codes']
    list_filter = ('organization', 'notice_type', 'deadline', 'source',
                   'unspsc_codes', 'notified')


class TenderDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'download_url', 'get_tender_title', 'document']
    search_fields = ['name']
    list_filter = ('tender__title',)

    def get_tender_title(self, obj):
        return obj.tender.title

    get_tender_title.short_description = 'Tender Title'
    get_tender_title.admin_order_field = 'tender__title'


class WinnerAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'value', 'currency', 'award_date', 'notified',
                    'get_tender_title', 'get_tender_organization',
                    'get_tender_source', 'get_tender_deadline']
    search_fields = ['vendor', 'tender__title', 'award_date']
    list_filter = ('vendor', 'tender__title', 'tender__deadline',
                   'tender__source', 'tender__organization', 'currency',
                   'award_date')

    def get_tender_title(self, obj):
        return obj.tender.title

    get_tender_title.short_description = 'Tender Title'
    get_tender_title.admin_order_field = 'tender__title'

    def get_tender_organization(self, obj):
        return obj.tender.organization

    get_tender_organization.short_description = 'Tender Organization'
    get_tender_organization.admin_order_field = 'tender__organization'

    def get_tender_source(self, obj):
        return obj.tender.source

    get_tender_source.short_description = 'Tender Source'
    get_tender_source.admin_order_field = 'tender__source'

    def get_tender_deadline(self, obj):
        return obj.tender.deadline

    get_tender_deadline.short_description = 'Tender Deadline'
    get_tender_deadline.admin_order_field = 'tender__deadline'


class WorkerLogAdmin(admin.ModelAdmin):
    list_display = ['update', 'source', 'tenders_count']
    list_filter = ('update',)
    search_fields = ['update']


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['email']
    search_fields = ['email']


class UNSPSCCodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'id_ungm', 'name']
    search_fields = ['id', 'id_ungm', 'name']


class CPVCodeAdmin(admin.ModelAdmin):
    list_display = ['code']
    search_fields = ['code']


class TedCountryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'args', 'kwargs', 'started', 'stopped', 'status']
    search_fields = ['id', 'args', 'kwargs', 'started', 'stopped', 'status']
    list_filter = ('id', 'args', 'kwargs', 'started', 'stopped', 'status')


class KeywordAdmin(admin.ModelAdmin):
    list_display = ['value']
    search_fields = ['value']


admin.site.register(Tender, TenderAdmin)
admin.site.register(TenderDocument, TenderDocumentAdmin)
admin.site.register(Winner, WinnerAdmin)
admin.site.register(WorkerLog, WorkerLogAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(UNSPSCCode, UNSPSCCodeAdmin)
admin.site.register(CPVCode, CPVCodeAdmin)
admin.site.register(TedCountry, TedCountryAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Keyword, KeywordAdmin)
