from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.accounts.models import Mechanic
from apps.customers.models import Customer


class Command(BaseCommand):
    help = "Create the demo user and load demo data if the database is empty"

    def handle(self, *args, **options):
        user, _ = Mechanic.objects.get_or_create(
            username="user",
            defaults={
                "first_name": "Demo",
                "last_name": "User",
                "specialization": "Recruiter preview",
            },
        )
        user.set_password("user12345")
        user.save()

        if not Customer.objects.exists():
            fixture = settings.BASE_DIR / "fixtures" / "demo_data.json"
            call_command("loaddata", str(fixture))
            self.stdout.write("Demo data loaded.")

        self.stdout.write(self.style.SUCCESS("Demo user is ready."))
