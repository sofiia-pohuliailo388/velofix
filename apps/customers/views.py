from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from .models import Customer


class CustomerList(LoginRequiredMixin, generic.ListView):
    model = Customer
    template_name = "customers/customer_list.html"
    context_object_name = "customers"
