from django.urls import path

from .views import TendersListView

urlpatterns = [
    path('tenders/', TendersListView.as_view(), name='teders_list_view'),
]
