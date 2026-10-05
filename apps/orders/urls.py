from django.urls import path

from .views import (
    OrderCreate,
    OrderDetail,
    OrderServiceCreate,
    OrderServiceDelete,
    OrderList,
)

urlpatterns = [
    path("bicycle/<int:bicycle_pk>/add/", OrderCreate.as_view(), name="order-create"),
    path("<int:pk>/", OrderDetail.as_view(), name="order-detail"),
    path("<int:order_pk>/services/add/", OrderServiceCreate.as_view(), name="order-service-add"),
    path("services/<int:pk>/delete/", OrderServiceDelete.as_view(), name="order-service-delete"),
path("", OrderList.as_view(), name="order-list"),
]