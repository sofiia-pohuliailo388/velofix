from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View, generic

from .forms import ServiceForm
from .models import Service


class ServiceList(LoginRequiredMixin, generic.ListView):
    model = Service
    template_name = "catalog/service_list.html"
    context_object_name = "services"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(name__icontains=q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        return context


class ServiceCreate(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "catalog/service_form.html"
    success_url = reverse_lazy("service-list")
    success_message = "Service created."


class ServiceUpdate(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = "catalog/service_form.html"
    success_url = reverse_lazy("service-list")
    success_message = "Service updated."


class ServiceToggleActive(LoginRequiredMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        service.is_active = not service.is_active
        service.save()
        if service.is_active:
            messages.success(request, "Service restored.")
        else:
            messages.success(request, "Service archived.")
        return redirect("service-list")


class ServiceDelete(LoginRequiredMixin, generic.DeleteView):
    model = Service
    template_name = "catalog/service_confirm_delete.html"
    success_url = reverse_lazy("service-list")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Service deleted.")
            return response
        except ProtectedError:
            messages.error(
                self.request,
                "Cannot delete: this service is used in repair orders. Archive it instead.",
            )
            return redirect("service-list")