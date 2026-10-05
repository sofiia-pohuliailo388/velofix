from typing import Any

from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseBase
from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import redirect, get_object_or_404

from .models import Customer, Bicycle

from .forms import CustomerForm, BicycleForm

class CustomerList(LoginRequiredMixin, generic.ListView):
    model = Customer
    template_name = "customers/customer_list.html"
    context_object_name = "customers"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().annotate(bicycle_count=Count("bicycles"))
        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(full_name__icontains=q) | Q(phone__icontains=q)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        return context


class CustomerCreate(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customers/customer_form.html"
    success_url = reverse_lazy("customer-list")
    success_message = "Customer created"


class CustomerDetail(LoginRequiredMixin, generic.DetailView):
    model = Customer
    template_name = "customers/customer_detail.html"


class CustomerUpdate(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customers/customer_form.html"
    success_message = "Customer updated."


class CustomerDelete(LoginRequiredMixin, generic.DeleteView):
    model = Customer
    template_name = "customers/customer_confirm_delete.html"
    success_url = reverse_lazy("customer-list")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Customer deleted")
            return response
        except ProtectedError:
            count = self.object.bicycles.count()
            messages.error(
                self.request,
                f"Cannot delete this customer: they have {count} bicycle(s) with repair history",
            )
            return redirect(self.object)

class BicycleCreate(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    models = Bicycle
    form_class = BicycleForm
    template_name = "customers/bicycle_form.html"
    success_message = "Bicycle added"

    def dispatch(self, request: http.HttpRequest, *args: Any, **kwargs: Any):
        self.customer = get_object_or_404(Customer, pk=kwargs["customer_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.customer = self.customer
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context["customer"] = self.customer
        return context

    def get_success_url(self):
        return self.customer.get_absolute_url()


class BicycleUpdate(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = Bicycle
    form_class = BicycleForm
    template_name = "customers/bicycle_form.html"
    success_message = "Bicycle updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer"] = self.object.customer
        return context

    def get_success_url(self):
        return self.object.customer.get_absolute_url()


class BicycleDelete(LoginRequiredMixin, generic.DeleteView):
    model = Bicycle
    template_name = "customers/bicycle_confirm_delete.html"

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Bicycle deleted")
            return response
        except ProtectedError:
            count = self.object.repair_orders.count()
            messages.error(
                self.request,
                f"Cannot delete this bicycle: it has {count} repair order(s)",
            )
            return redirect(self.object.customer)

    def get_success_url(self):
        return self.object.customer.get_absolute_url()

class BicycleDetail(LoginRequiredMixin, generic.DetailView):
    model = Bicycle
    queryset = Bicycle.objects.select_related("customer").prefetch_related("repair_orders")
    template_name = "customers/bicycle_detail.html"