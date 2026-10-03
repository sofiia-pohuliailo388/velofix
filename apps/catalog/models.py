from django.db import models


class Service(models.Model):
    name = models.CharField("Name", max_length=150)
    description = models.TextField("Description", blank=True)
    base_price = models.DecimalField("Base price", max_digits=10, decimal_places=2)
    is_active = models.BooleanField("Active", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "service"
        verbose_name_plural = "services"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(base_price__gte=0),
                name="service_base_price_gte_0",
            ),
        ]

    def __str__(self):
        return self.name


class Part(models.Model):
    name = models.CharField("Name", max_length=150)
    sku = models.CharField("SKU", max_length=100, unique=True)
    stock_quantity = models.PositiveIntegerField("Stock quantity", default=0)
    minimum_stock = models.PositiveIntegerField("Minimum stock", default=0)
    purchase_price = models.DecimalField("Purchase price", max_digits=10, decimal_places=2)
    selling_price = models.DecimalField("Selling price", max_digits=10, decimal_places=2)
    is_active = models.BooleanField("Active", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "part"
        verbose_name_plural = "parts"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(purchase_price__gte=0),
                name="part_purchase_price_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(selling_price__gte=0),
                name="part_selling_price_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.minimum_stock