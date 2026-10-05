from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Mechanic
from apps.catalog.models import Part
from apps.customers.models import Bicycle, Customer
from apps.orders.models import RepairOrder


class DashboardTest(TestCase):
    def setUp(self):
        self.user = Mechanic.objects.create_user(username="tester", password="x")
        self.client.force_login(self.user)
        customer = Customer.objects.create(full_name="C", phone="1")
        self.bicycle = Bicycle.objects.create(customer=customer, brand="A", model="1")

    def make_order(self, status="accepted", days=1):
        return RepairOrder.objects.create(
            bicycle=self.bicycle, problem_description="x", status=status,
            deadline=timezone.now() + timedelta(days=days),
        )

    def make_part(self, sku, stock, minimum, active=True):
        return Part.objects.create(
            name=sku, sku=sku, stock_quantity=stock, minimum_stock=minimum,
            purchase_price="10", selling_price="20", is_active=active,
        )

    def test_home_requires_login(self):
        self.client.logout()
        url = reverse("home")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_counters(self):
        self.make_order(days=-1)                  # active and overdue
        self.make_order(status="ready")           # active, ready
        self.make_order(status="delivered", days=-5)   # closed, never counted
        self.make_order(status="cancelled", days=-5)   # closed, never counted

        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["active_count"], 2)
        self.assertEqual(response.context["overdue_count"], 1)
        self.assertEqual(response.context["ready_count"], 1)

    def test_low_stock_counts_only_active_parts_below_minimum(self):
        self.make_part("LOW", stock=1, minimum=5)
        self.make_part("EDGE", stock=5, minimum=5)
        self.make_part("OK", stock=10, minimum=2)
        self.make_part("OLD", stock=0, minimum=5, active=False)

        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["low_stock_count"], 2)

    def test_overdue_list_starts_with_the_oldest_deadline(self):
        newer = self.make_order(days=-1)
        older = self.make_order(days=-5)
        response = self.client.get(reverse("home"))
        pks = [order.pk for order in response.context["overdue_orders"]]
        self.assertEqual(pks, [older.pk, newer.pk])

    def test_empty_database_shows_zeros(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_count"], 0)
