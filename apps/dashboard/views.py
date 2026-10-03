from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic


class Home(LoginRequiredMixin, generic.TemplateView):
    template_name = "dashboard/home.html"