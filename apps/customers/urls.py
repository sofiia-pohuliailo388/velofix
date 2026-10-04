from django.urls import path

from .views import CustomerList, CustomerCreate, CustomerDetail, CustomerUpdate, CustomerDelete

urlpatterns = [
    path("", CustomerList.as_view(), name="customer-list"),
    path("add/", CustomerCreate.as_view(), name="customer-create"),
    path("<int:pk>/", CustomerDetail.as_view(), name="customer-detail"),
    path("<int:pk>/edit/", CustomerUpdate.as_view(), name="customer-update"),
    path("<int:pk>/delete/", CustomerDelete.as_view(), name="customer-delete"),
]