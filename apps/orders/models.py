from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import DecimalField, F, Q, Sum
from django.utils import timezone


class RepairOrder(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = "accepted", "Accepted"
        DIAGNOSIS = "diagnosis", "Diagnosis"
        WAITING_APPROVAL = "waiting_approval", "Waiting for approval"
        WAITING_PARTS = "waiting_parts", "Waiting for parts"
        IN_PROGRESS = "in_progress", "In progress"
        READY = "ready", "Ready for pickup"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class ApprovalMethod(models.TextChoices):
        PHONE = "phone", "Phone"
        MESSENGER = "messenger", "Messenger"
        EMAIL = "email", "Email"
        IN_PERSON = "in_person", "In person"

    bicycle = models.ForeignKey(
        "customers.Bicycle",
        on_delete=models.PROTECT,
        related_name="repair_orders",
        verbose_name="Bicycle",
    )
    mechanics = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="RepairOrderMechanic",
        related_name="repair_orders",
        blank=True,
        verbose_name="Mechanics",
    )

    problem_description = models.TextField("Problem description")
    condition_notes = models.TextField("Condition notes", blank=True)
    diagnosis = models.TextField("Diagnosis", blank=True)
    status = models.CharField(
        "Status",
        max_length=30,
        choices=Status.choices,
        default=Status.ACCEPTED,
    )

    created_at = models.DateTimeField("Created at", auto_now_add=True)
    deadline = models.DateTimeField("Deadline")
    completed_at = models.DateTimeField("Completed at", null=True, blank=True)
    delivered_at = models.DateTimeField("Delivered at", null=True, blank=True)

    quote_version = models.PositiveIntegerField("Quote version", default=1)
    approved_version = models.PositiveIntegerField("Approved version", null=True, blank=True)
    approved_at = models.DateTimeField("Approved at", null=True, blank=True)
    approval_method = models.CharField(
        "Approval method",
        max_length=20,
        choices=ApprovalMethod.choices,
        blank=True,
    )

    quality_check_notes = models.TextField("Quality check notes", blank=True)
    paid_at = models.DateTimeField("Paid at", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "repair order"
        verbose_name_plural = "repair orders"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["deadline"]),
        ]

    def __str__(self):
        return f"Order #{self.pk} - {self.bicycle}"

    @property
    def is_overdue(self):
        active = self.status not in (self.Status.DELIVERED, self.Status.CANCELLED)
        return active and self.deadline < timezone.now()

    @property
    def is_quote_approved(self):
        return self.approved_version == self.quote_version

    @property
    def total_services(self):
        result = self.service_lines.aggregate(
            total=Sum(
                F("quantity") * F("unit_price"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        return result["total"] or Decimal("0.00")

    @property
    def total_parts(self):
        result = self.part_lines.aggregate(
            total=Sum(
                F("quantity") * F("unit_price"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        return result["total"] or Decimal("0.00")

    @property
    def total(self):
        return self.total_services + self.total_parts


class RepairOrderMechanic(models.Model):
    repair_order = models.ForeignKey(
        RepairOrder,
        on_delete=models.CASCADE,
        verbose_name="Repair order",
    )
    mechanic = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Mechanic",
    )
    assigned_at = models.DateTimeField("Assigned at", auto_now_add=True)

    class Meta:
        verbose_name = "order mechanic"
        verbose_name_plural = "order mechanics"
        constraints = [
            models.UniqueConstraint(
                fields=["repair_order", "mechanic"],
                name="unique_mechanic_per_order",
            ),
        ]

    def __str__(self):
        return f"{self.mechanic} on order #{self.repair_order_id}"


class OrderService(models.Model):
    repair_order = models.ForeignKey(
        RepairOrder,
        on_delete=models.CASCADE,
        related_name="service_lines",
        verbose_name="Repair order",
    )
    service = models.ForeignKey(
        "catalog.Service",
        on_delete=models.PROTECT,
        related_name="order_lines",
        verbose_name="Service",
    )
    quantity = models.PositiveIntegerField("Quantity", default=1)
    unit_price = models.DecimalField("Unit price", max_digits=10, decimal_places=2)
    is_completed = models.BooleanField("Completed", default=False)

    class Meta:
        verbose_name = "order service"
        verbose_name_plural = "order services"
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="order_service_quantity_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="order_service_unit_price_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.service} x{self.quantity}"

    @property
    def line_total(self):
        return self.quantity * self.unit_price


class OrderPart(models.Model):
    repair_order = models.ForeignKey(
        RepairOrder,
        on_delete=models.CASCADE,
        related_name="part_lines",
        verbose_name="Repair order",
    )
    part = models.ForeignKey(
        "catalog.Part",
        on_delete=models.PROTECT,
        related_name="order_lines",
        verbose_name="Part",
    )
    quantity = models.PositiveIntegerField("Quantity")
    unit_price = models.DecimalField("Unit price", max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(
        "Unit cost", max_digits=10, decimal_places=2, null=True, blank=True
    )
    used_at = models.DateTimeField("Used at", null=True, blank=True)
    returned_at = models.DateTimeField("Returned at", null=True, blank=True)

    class Meta:
        verbose_name = "order part"
        verbose_name_plural = "order parts"
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="order_part_quantity_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="order_part_unit_price_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(returned_at__isnull=True) | Q(used_at__isnull=False),
                name="order_part_returned_requires_used",
            ),
        ]

    def __str__(self):
        return f"{self.part} x{self.quantity}"

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    @property
    def is_used(self):
        return self.used_at is not None and self.returned_at is None
