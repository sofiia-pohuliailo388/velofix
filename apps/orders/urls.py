from django.urls import path

from .views import (
    OrderCreate,
    OrderDetail,
)

urlpatterns = [
    path("bicycle/<int:bicycle_pk>/add/", OrderCreate.as_view(), name="order-create"),
    path("<int:pk>/", OrderDetail.as_view(), name="order-detail"),
]