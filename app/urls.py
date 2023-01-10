from django.urls import path
from django.views.generic import RedirectView
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
    TenderSeenByView,
    ManagementView,
    ManagementDeleteView,
    ContractAwardDetailView,
    TenderListAjaxView,
    ContractAwardsListAjaxView,
    TenderArchiveAjaxView,
    TenderTagView,
    VendorsListView,
    VendorsListAjaxView
)

urlpatterns = [
    path("", HomepageView.as_view(), name="homepage_view"),
    path("tenders/", TendersListView.as_view(), name="tenders_list_view"),
    path("tenders/<int:pk>/", TenderDetailView.as_view(), name="tender_detail_view"),
    path("tenders/tag/<int:pk>/", TenderTagView.as_view(), name="tender_tag_view"),
    path("tenders/favourite/<int:pk>/", TenderFavouriteView.as_view(), name="tender_favourite_view"),
    path("tenders/seen/<int:pk>/", TenderSeenByView.as_view(), name="tender_seen_view"),
    path("tenders/delete/<int:pk>/", TenderDeleteView.as_view(), name="tender_delete_view"),
    path('tenders/ajax', TenderListAjaxView.as_view(), name='tenders_list_ajax_view'),
    path("overview/", OverviewPageView.as_view(), name="overview_view"),
    path("login/", LoginView.as_view(), name="login_view"),
    path("logout/", LogoutView.as_view(), name="logout_view"),
    path("awards/", ContractAwardsListView.as_view(), name="contract_awards_list_view"),
    path('awards/ajax', ContractAwardsListAjaxView.as_view(), name='contract_awards_list_ajax_view'),
    path("awards/<int:pk>/", ContractAwardDetailView.as_view(), name="contract_awards_detail_view"),
    path("vendors/", VendorsListView.as_view(), name="vendors_list_view"),
    path('vendors/ajax', VendorsListAjaxView.as_view(), name='vendors_list_ajax_view'),
    path('archive/', TenderArchiveView.as_view(), name='tenders_archive_list'),
    path('archive/ajax', TenderArchiveAjaxView.as_view(), name='tenders_archive_list_ajax_view'),
    path('search/<str:pk>', SearchView.as_view(), name='search_results'),
    path('management/', ManagementView.as_view(), name='management_view'),
    path('management/delete/<str:pk>', ManagementDeleteView.as_view(), name='management_delete_view'),
    path('admin_page', RedirectView.as_view(url='/admin'), name='admin_view')
]
