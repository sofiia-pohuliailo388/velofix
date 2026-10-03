from django.db import models
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