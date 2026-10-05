from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Mechanic
from apps.customers.models import Bicycle, Customer
from apps.orders.models import OrderService, RepairOrder

from apps.catalog.forms import ServiceForm
from apps.catalog.models import Part, Service


class ServiceFormTest(TestCase):
    def test_negative_price_is_rejected(self):
        form = ServiceForm({"name": "Bad", "base_price": "-5", "is_active": True})
        self.assertFalse(form.is_valid())
        self.assertIn("base_price", form.errors)

    def test_valid_data_is_accepted(self):
        form = ServiceForm({"name": "Good", "base_price": "120", "is_active": True})
        self.assertTrue(form.is_valid())


class PartTest(TestCase):
    def make_part(self, stock, minimum, sku="P1"):
        return Part.objects.create(
            name="Part", sku=sku, stock_quantity=stock, minimum_stock=minimum,
            purchase_price="10", selling_price="20",
        )

    def test_low_stock_flag(self):
        self.assertTrue(self.make_part(3, 5, "A").is_low_stock)
        self.assertTrue(self.make_part(5, 5, "B").is_low_stock)
        self.assertFalse(self.make_part(10, 5, "C").is_low_stock)


class ServicePagesTest(TestCase):
    def setUp(self):
        self.user = Mechanic.objects.create_user(username="tester", password="x")
        self.client.force_login(self.user)
        self.service = Service.objects.create(name="Tune-up", base_price="500")

    def test_service_list_requires_login(self):
        self.client.logout()
        url = reverse("service-list")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_search_by_name(self):
        Service.objects.create(name="Wheel truing", base_price="300")
        response = self.client.get(reverse("service-list"), {"q": "wheel"})
        names = [service.name for service in response.context["services"]]
        self.assertEqual(names, ["Wheel truing"])

    def test_create_service(self):
        response = self.client.post(
            reverse("service-create"),
            {"name": "New", "description": "", "base_price": "120", "is_active": "on"},
        )
        self.assertRedirects(response, reverse("service-list"))
        self.assertTrue(Service.objects.filter(name="New").exists())

    def test_archive_toggle_works_both_ways(self):
        url = reverse("service-toggle", args=[self.service.pk])
        self.client.post(url)
        self.service.refresh_from_db()
        self.assertFalse(self.service.is_active)
        self.client.post(url)
        self.service.refresh_from_db()
        self.assertTrue(self.service.is_active)

    def test_archive_toggle_does_not_accept_get(self):
        response = self.client.get(reverse("service-toggle", args=[self.service.pk]))
        self.assertEqual(response.status_code, 405)

    def test_unused_service_can_be_deleted(self):
        self.client.post(reverse("service-delete", args=[self.service.pk]))
        self.assertFalse(Service.objects.filter(pk=self.service.pk).exists())

    def test_used_service_cannot_be_deleted(self):
        customer = Customer.objects.create(full_name="C", phone="1")
        bicycle = Bicycle.objects.create(customer=customer, brand="A", model="1")
        order = RepairOrder.objects.create(
            bicycle=bicycle, problem_description="x",
            deadline=timezone.now() + timedelta(days=1),
        )
        OrderService.objects.create(
            repair_order=order, service=self.service, quantity=1, unit_price="500"
        )
        self.client.post(reverse("service-delete", args=[self.service.pk]), follow=True)
        self.assertTrue(Service.objects.filter(pk=self.service.pk).exists())
