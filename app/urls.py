from django.urls import path

from .views import LoginView, LogoutView, ContractAwardsListVew
from .views import TendersListView, TenderDetailView, TenderFavouriteView


urlpatterns = [
    path('tenders/', TendersListView.as_view(), name='tenders_list_view'),
    path('tenders/<int:pk>/', TenderDetailView.as_view(), name='tender_detail_view'),
    path('tenders/favourite/<int:pk>', TenderFavouriteView.as_view(), name='tender_favourite_view'),
    path('login/', LoginView.as_view(), name='login_view'),
    path('logout/', LogoutView.as_view(), name='logout_view'),
    path('awards/', ContractAwardsListVew.as_view(), name='contract_awards_list_view'),
]
