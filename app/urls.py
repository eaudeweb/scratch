from django.urls import path

from .views import TendersListView, LoginView, LogoutView, ContractAwardsListVew

urlpatterns = [
    path('tenders/', TendersListView.as_view(), name='tenders_list_view'),
    path('login/', LoginView.as_view(), name='login_view'),
    path('logout/', LogoutView.as_view(), name='logout_view'),
    path('awards/', ContractAwardsListVew.as_view(), name='contract_awards_list_view'),
]
