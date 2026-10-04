from django.urls import path

from .views import CustomerList, CustomerCreate

urlpatterns = [
    path("", CustomerList.as_view(), name="customer-list"),
    path("add/", CustomerCreate.as_view(), name="customer-create"),
]