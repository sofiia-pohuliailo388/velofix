from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import generic
from django.views.generic.base import View

from apps.customers.models import Bicycle

from .forms import RepairOrderForm, OrderServiceForm
from .models import RepairOrder, OrderService
from .services import TransitionError, change_status


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

class OrderServiceCreate(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = OrderService
    form_class = OrderServiceForm
    template_name = "orders/orderservice_form.html"
    success_message = "Service added."

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(RepairOrder, pk=kwargs["order_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.repair_order = self.order
        form.instance.unit_price = form.cleaned_data["service"].base_price
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        return context

    def get_success_url(self):
        return self.order.get_absolute_url()


class OrderServiceDelete(LoginRequiredMixin, View):
    def post(self, request, pk):
        line = get_object_or_404(OrderService, pk=pk)
        order = line.repair_order
        line.delete()
        messages.success(request, "Service removed.")
        return redirect(order)

class OrderList(LoginRequiredMixin, generic.ListView):
    queryset = RepairOrder.objects.select_related("bicycle__customer")
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "")
        overdue = self.request.GET.get("overdue", "")

        for word in q.split():
            queryset = queryset.filter(
                Q(bicycle__customer__full_name__icontains=word)
                | Q(bicycle__brand__icontains=word)
                | Q(bicycle__model__icontains=word)
                | Q(bicycle__frame_number__icontains=word)
            )
        if status:
            queryset = queryset.filter(status=status)
        if overdue == "1":
            queryset = queryset.exclude(
                status__in=[RepairOrder.Status.DELIVERED, RepairOrder.Status.CANCELLED]
            ).filter(deadline__lt=timezone.now())
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["status"] = self.request.GET.get("status", "")
        context["overdue"] = self.request.GET.get("overdue", "")
        context["statuses"] = RepairOrder.Status.choices
        return context

class OrderChangeStatus(LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(RepairOrder, pk=pk)
        new_status = request.POST.get("status", "")
        try:
            change_status(order, new_status)
            messages.success(request, "Status updated.")
        except TransitionError as error:
            messages.error(request, str(error))
        return redirect(order)