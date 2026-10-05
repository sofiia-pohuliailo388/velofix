from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Mechanic


@admin.register(Mechanic)
class MechanicAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name", "specialization", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Work", {"fields": ("specialization",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Work", {"fields": ("specialization",)}),
    )
