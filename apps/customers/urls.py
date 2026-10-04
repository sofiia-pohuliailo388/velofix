from django.urls import path

from .views import (
    CustomerList,
    CustomerCreate,
    CustomerDetail,
    CustomerUpdate,
    CustomerDelete,
    BicycleCreate,
    BicycleDelete,
    BicycleUpdate
)

urlpatterns = [
    path("", CustomerList.as_view(), name="customer-list"),
    path("add/", CustomerCreate.as_view(), name="customer-create"),
    path("<int:pk>/", CustomerDetail.as_view(), name="customer-detail"),
    path("<int:pk>/edit/", CustomerUpdate.as_view(), name="customer-update"),
    path("<int:pk>/delete/", CustomerDelete.as_view(), name="customer-delete"),
    path("<int:customer_pk>/bicycles/add/", BicycleCreate.as_view(), name="bicycle-create"),
    path("bicycles/<int:pk>/edit/", BicycleUpdate.as_view(), name="bicycle-update"),
    path("bicycles/<int:pk>/delete/", BicycleDelete.as_view(), name="bicycle-delete"),
]