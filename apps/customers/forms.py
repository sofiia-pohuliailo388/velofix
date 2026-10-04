from django import forms

from apps.customers.models import Customer, Bicycle


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["full_name", "phone", "email", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class BicycleForm(forms.ModelForm):
    class Meta:
        model = Bicycle
        fields = ["brand", "model", "bike_type", "frame_number", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-select"