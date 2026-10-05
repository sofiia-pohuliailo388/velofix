from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.views import generic

from apps.customers.models import Bicycle

from .forms import RepairOrderForm
from .models import RepairOrder


class OrderCreate(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = RepairOrder
    form_class = RepairOrderForm
    template_name = "orders/order_form.html"
    success_message = "Repair order created."

    def dispatch(self, request, *args, **kwargs):
        self.bicycle = get_object_or_404(Bicycle, pk=kwargs["bicycle_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.bicycle = self.bicycle
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bicycle"] = self.bicycle
        return context


class OrderDetail(LoginRequiredMixin, generic.DetailView):
    queryset = RepairOrder.objects.select_related("bicycle__customer")
    template_name = "orders/order_detail.html"
    context_object_name = "order"