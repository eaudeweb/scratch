from django.urls import path
from .views import LoginView, LogoutView, ContractAwardsListView
from .views import (
    TendersListView,
    TenderDeleteView,
    TenderDetailView,
    TenderFavouriteView,
    HomepageView,
    OverviewPageView,
    TenderArchiveView,
    SearchView,
    TenderSeenByView
)


urlpatterns = [
    path("", HomepageView.as_view(), name="homepage_view"),
    path("tenders/", TendersListView.as_view(), name="tenders_list_view"),
    path("tenders/<int:pk>/", TenderDetailView.as_view(), name="tender_detail_view"),
    path("tenders/favourite/<int:pk>/", TenderFavouriteView.as_view(), name="tender_favourite_view"),
    path("tenders/seen/<int:pk>/", TenderSeenByView.as_view(), name="tender_seen_view"),
    path("tenders/delete/<int:pk>/", TenderDeleteView.as_view(), name="tender_delete_view"),
    path("overview/", OverviewPageView.as_view(), name="overview_view"),
    path("login/", LoginView.as_view(), name="login_view"),
    path("logout/", LogoutView.as_view(), name="logout_view"),
    path("awards/", ContractAwardsListView.as_view(), name="contract_awards_list_view"),
    path('archive/', TenderArchiveView.as_view(), name='tenders_archive_list'),
    path('search/<str:pk>', SearchView.as_view(), name='search_results'),
]
