from django.contrib import admin

from .models import Part, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "base_price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "stock_quantity", "minimum_stock", "selling_price", "low_stock", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "sku")

    @admin.display(boolean=True, description="Low stock")
    def low_stock(self, obj):
        return obj.is_low_stock