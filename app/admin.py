from django.contrib import admin
from .models import (Tender, TenderDocument, Award, WorkerLog, EmailAddress,
                     UNSPSCCode, CPVCode, TedCountry, Task, Keyword, Vendor)


class TenderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'notice_type', 'organization', 'published', 'deadline',
        'url', 'source', 'unspsc_codes', 'favourite', 'has_keywords'
    ]
    search_fields = [
        'title', 'notice_type', 'published', 'deadline', 'source',
        'organization', 'unspsc_codes'
    ]
    list_filter = (
        'organization', 'notice_type', 'deadline', 'source',
        'unspsc_codes', 'notified'
    )
    readonly_fields = ('keywords', 'created_at', 'updated_at')


class TenderDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'download_url', 'get_tender_title', 'document']
    search_fields = ['name']
    list_filter = ('tender__title',)

    def get_tender_title(self, obj):
        return obj.tender.title

    get_tender_title.short_description = 'Tender Title'
    get_tender_title.admin_order_field = 'tender__title'


class AwardAdmin(admin.ModelAdmin):
    list_display = [
        'value', 'currency', 'award_date', 'notified', 'get_vendors',
        'get_tender_title', 'get_tender_organization', 'get_tender_source',
        'get_tender_deadline',
    ]

    search_fields = ['vendors__name', 'tender__title', 'award_date']
    list_filter = (
        'vendors', 'tender__title', 'tender__deadline', 'tender__source',
        'tender__organization', 'currency', 'award_date',
    )

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


def turn_notifications_off(modeladmin, request, queryset):
    queryset.update(notify=False)


turn_notifications_off.short_description = 'Turn notifications off'


def turn_notifications_on(modeladmin, request, queryset):
    queryset.update(notify=True)


turn_notifications_on.short_description = 'Turn notifications on'


class EmailAddressAdmin(admin.ModelAdmin):
    list_display = ['email', 'notify']
    list_filter = ['notify']
    search_fields = ['email']
    actions = [turn_notifications_off, turn_notifications_on]


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


class VendorAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


admin.site.register(Tender, TenderAdmin)
admin.site.register(TenderDocument, TenderDocumentAdmin)
admin.site.register(Award, AwardAdmin)
admin.site.register(WorkerLog, WorkerLogAdmin)
admin.site.register(EmailAddress, EmailAddressAdmin)
admin.site.register(UNSPSCCode, UNSPSCCodeAdmin)
admin.site.register(CPVCode, CPVCodeAdmin)
admin.site.register(TedCountry, TedCountryAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(Vendor, VendorAdmin)
