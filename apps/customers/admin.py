from django.contrib import admin
from .models import Customer, Bicycle


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "email")
    search_fields = ("full_name", "phone")


@admin.register(Bicycle)
class BicycleAdmin(admin.ModelAdmin):
    list_display = ("brand", "model", "bike_type", "customer")
    list_filter = ("bike_type",)
    search_fields = ("brand", "model", "frame_number")