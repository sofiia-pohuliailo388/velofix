from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.shortcuts import redirect

from .models import Customer

from .forms import CustomerForm

class CustomerList(LoginRequiredMixin, generic.ListView):
    model = Customer
    template_name = "customers/customer_list.html"
    context_object_name = "customers"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
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
