from django.db import models
from django.urls import reverse


class Customer(models.Model):
    full_name = models.CharField("Full name", max_length=150)
    phone = models.CharField("Phone", max_length=30)
    email = models.EmailField("Email", blank=True)
    notes = models.TextField("Notes", blank=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "customer"
        verbose_name_plural = "customers"

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse("customer-detail", kwargs={"pk": self.pk})


class Bicycle(models.Model):
    class BikeType(models.TextChoices):
        CITY = "city", "City bike"
        MOUNTAIN = "mountain", "Mountain bike"
        ROAD = "road", "Road bike"
        GRAVEL = "gravel", "Gravel bike"
        HYBRID = "hybrid", "Hybrid bike"
        TOURING = "touring", "Touring bike"
        BMX = "bmx", "BMX"
        FAT = "fat", "Fat bike"
        FOLDING = "folding", "Folding bike"
        CARGO = "cargo", "Cargo bike"
        KIDS = "kids", "Kids' bike"
        OTHER = "other", "Other"

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="bicycles",
        verbose_name="Customer",
    )
    brand = models.CharField("Brand", max_length=100)
    model = models.CharField("Model", max_length=100)
    bike_type = models.CharField(
        "Type",
        max_length=20,
        choices=BikeType.choices,
        default=BikeType.OTHER,
    )
    frame_number = models.CharField("Frame number", max_length=100, blank=True)
    notes = models.TextField("Notes", blank=True)

    class Meta:
        ordering = ["brand", "model"]
        verbose_name = "bicycle"
        verbose_name_plural = "bicycles"
        constraints = [
            models.UniqueConstraint(
                fields=["frame_number"],
                condition=~models.Q(frame_number=""),
                name="unique_frame_number_if_set",
            ),
        ]

    def __str__(self):
        return f"{self.brand} {self.model}"
