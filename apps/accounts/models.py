from django.contrib.auth.models import AbstractUser
from django.db import models


class Mechanic(AbstractUser):
    specialization = models.CharField(
        max_length=255,
        blank=True
    )

    def __str__(self):
        name = self.get_full_name() or self.username
        return f"{name} ({self.specialization})" if self.specialization else name
