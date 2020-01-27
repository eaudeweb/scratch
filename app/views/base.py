import json

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.views.generic import View


class BaseAjaxListingView(View):
    filter_names = []
    order_fields = ['id']
    case_sensitive_fields = []
    model = None

    def get(self, request):
        objects = self.get_data(request)
        return HttpResponse(json.dumps(objects, cls=DjangoJSONEncoder),
                            content_type='application/json')

    def format_data(self, object_list):
        return object_list

    def get_objects(self):
        return self.model.objects.order_by('id')

    def order_data(self, request, objects):
        field = request.GET.get('order[0][column]')
        sort_type = request.GET.get('order[0][dir]')
        if field and sort_type:
            field_name = self.order_fields[int(field)]
            if field_name in self.case_sensitive_fields:
                field_name = Lower(field_name)
            objects = objects.order_by(field_name)
            if sort_type == 'desc':
                return objects.reverse()
        return objects

    def filter_data(self, request):
        objects = self.get_objects()

        filters = {}
        for filter_name, filter_field in self.filter_names:
            filter_value = self.request.GET.get(filter_name)
            if filter_value:
                filters.update({filter_field: filter_value})

        objects = objects.filter(**filters)
        return objects

    def get_data(self, request):

        length = int(request.GET.get('length'))
        start = int(request.GET.get("start"))
        draw = int(request.GET.get("draw"))

        objects = self.filter_data(request)
        objects = self.order_data(request, objects)
        objects_count = objects.count()
        objects_filtered_count = objects_count

        paginator = Paginator(objects, length)
        page_number = start / length + 1

        try:
            object_list = paginator.page(page_number).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(1).object_list

        data = self.format_data(object_list)

        return {
            'draw': draw,
            'recordsTotal': objects_count,
            'recordsFiltered': objects_filtered_count,
            'data': data,
        }
