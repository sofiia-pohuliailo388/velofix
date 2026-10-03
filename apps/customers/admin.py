from django.contrib import admin

from .models import Bicycle, Customer


class BicycleInline(admin.TabularInline):
    model = Bicycle
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "email")
    search_fields = ("full_name", "phone")
    inlines = [BicycleInline]


@admin.register(Bicycle)
class BicycleAdmin(admin.ModelAdmin):
    list_display = ("brand", "model", "bike_type", "frame_number", "customer")
    list_filter = ("bike_type",)
    search_fields = ("brand", "model", "frame_number", "customer__full_name")
    list_select_related = ("customer",)