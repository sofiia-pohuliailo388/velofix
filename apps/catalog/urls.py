from django.urls import path

from .views import (
    ServiceList,
    ServiceCreate,
    ServiceUpdate,
    ServiceToggleActive,
    ServiceDelete,
)

urlpatterns = [
    path("", ServiceList.as_view(), name="service-list"),
    path("add/", ServiceCreate.as_view(), name="service-create"),
    path("<int:pk>/edit/", ServiceUpdate.as_view(), name="service-update"),
    path("<int:pk>/toggle/", ServiceToggleActive.as_view(), name="service-toggle"),
    path("<int:pk>/delete/", ServiceDelete.as_view(), name="service-delete"),
]
