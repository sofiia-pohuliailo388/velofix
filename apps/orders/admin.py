from django.contrib import admin

from .models import OrderPart, OrderService, RepairOrder, RepairOrderMechanic


class RepairOrderMechanicInline(admin.TabularInline):
    model = RepairOrderMechanic
    extra = 0


class OrderServiceInline(admin.TabularInline):
    model = OrderService
    extra = 0


class OrderPartInline(admin.TabularInline):
    model = OrderPart
    extra = 0


@admin.register(RepairOrder)
class RepairOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "bicycle", "status", "deadline", "overdue", "total")
    list_filter = ("status",)
    search_fields = (
        "bicycle__brand",
        "bicycle__model",
        "bicycle__frame_number",
        "bicycle__customer__full_name",
    )
    list_select_related = ("bicycle__customer",)
    readonly_fields = ("created_at", "total_services", "total_parts", "total")
    inlines = [RepairOrderMechanicInline, OrderServiceInline, OrderPartInline]

    @admin.display(boolean=True, description="Overdue")
    def overdue(self, obj):
        return obj.is_overdue