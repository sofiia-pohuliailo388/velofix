from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.utils import timezone
from django.views import generic

from apps.catalog.models import Part
from apps.orders.models import RepairOrder


class Home(LoginRequiredMixin, generic.TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active = RepairOrder.objects.exclude(
            status__in=[RepairOrder.Status.DELIVERED, RepairOrder.Status.CANCELLED]
        )
        overdue = active.filter(deadline__lt=timezone.now())
        ready = RepairOrder.objects.filter(status=RepairOrder.Status.READY)
        low_stock = Part.objects.filter(
            is_active=True, stock_quantity__lte=F("minimum_stock")
        )

        context["active_count"] = active.count()
        context["overdue_count"] = overdue.count()
        context["ready_count"] = ready.count()
        context["low_stock_count"] = low_stock.count()

        context["overdue_orders"] = overdue.select_related(
            "bicycle__customer"
        ).order_by("deadline")[:5]
        context["ready_orders"] = ready.select_related("bicycle__customer")[:5]
        context["low_stock_parts"] = low_stock.order_by("stock_quantity")[:5]
        return context