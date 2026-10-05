from django import forms
from django.utils import timezone

from apps.orders.models import RepairOrder


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