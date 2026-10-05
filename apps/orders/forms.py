from django import forms
from django.utils import timezone

from apps.catalog.models import Service

from .models import OrderService, RepairOrder


class RepairOrderForm(forms.ModelForm):
    class Meta:
        model = RepairOrder
        fields = ["problem_description", "condition_notes", "deadline"]
        widgets = {
            "problem_description": forms.Textarea(attrs={"rows": 3}),
            "condition_notes": forms.Textarea(attrs={"rows": 3}),
            "deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_deadline(self):
        if self.cleaned_data["deadline"] < timezone.now():
            raise forms.ValidationError("Deadline cannot be in the past.")
        return self.cleaned_data["deadline"]


class OrderServiceForm(forms.ModelForm):
    class Meta:
        model = OrderService
        fields = ["service", "quantity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(is_active=True)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return quantity