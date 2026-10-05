from django import forms

from apps.catalog.models import Service

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "description", "base_price", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"

    def clean_base_price(self):
        price = self.cleaned_data["base_price"]
        if price < 0:
            raise forms.ValidationError("Price cannot be negative")
        return price


