from django.urls import path

from .views import TendersListView, LoginView

urlpatterns = [
    path('tenders/', TendersListView.as_view(), name='tenders_list_view'),
    path('login/', LoginView.as_view(), name='login_view'),
]
