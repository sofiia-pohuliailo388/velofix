from django.urls import path

from .views import CustomerList

urlpatterns = [
    path("", CustomerList.as_view(), name="customer-list"),
]