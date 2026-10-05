from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Mechanic
from apps.orders.models import RepairOrder
from django.utils import timezone
from datetime import timedelta

from apps.customers.models import Bicycle, Customer


class CustomerTestBase(TestCase):
    def setUp(self):
        self.user = Mechanic.objects.create_user(username="tester", password="x")
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(full_name="Olivia Carter", phone="111")


class CustomerPagesTest(CustomerTestBase):
    def test_customer_list_requires_login(self):
        self.client.logout()
        url = reverse("customer-list")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_search_matches_words_in_any_order(self):
        Customer.objects.create(full_name="Liam Harris", phone="222")
        response = self.client.get(reverse("customer-list"), {"q": "Carter Olivia"})
        names = [customer.full_name for customer in response.context["customers"]]
        self.assertEqual(names, ["Olivia Carter"])

    def test_search_by_phone(self):
        Customer.objects.create(full_name="Liam Harris", phone="222")
        response = self.client.get(reverse("customer-list"), {"q": "222"})
        names = [customer.full_name for customer in response.context["customers"]]
        self.assertEqual(names, ["Liam Harris"])

    def test_list_shows_bicycle_count(self):
        Bicycle.objects.create(customer=self.customer, brand="Trek", model="A")
        Bicycle.objects.create(customer=self.customer, brand="Giant", model="B")
        response = self.client.get(reverse("customer-list"))
        customer = response.context["customers"][0]
        self.assertEqual(customer.bicycle_count, 2)

    def test_create_customer(self):
        response = self.client.post(
            reverse("customer-create"), {"full_name": "New Person", "phone": "333"}
        )
        self.assertRedirects(response, reverse("customer-list"))
        self.assertTrue(Customer.objects.filter(full_name="New Person").exists())

    def test_phone_is_required(self):
        response = self.client.post(reverse("customer-create"), {"full_name": "No Phone"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Customer.objects.filter(full_name="No Phone").exists())

    def test_customer_without_bicycles_can_be_deleted(self):
        self.client.post(reverse("customer-delete", args=[self.customer.pk]))
        self.assertFalse(Customer.objects.filter(pk=self.customer.pk).exists())

    def test_customer_with_bicycles_cannot_be_deleted(self):
        Bicycle.objects.create(customer=self.customer, brand="Trek", model="A")
        response = self.client.post(
            reverse("customer-delete", args=[self.customer.pk]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Customer.objects.filter(pk=self.customer.pk).exists())


class BicycleTest(CustomerTestBase):
    def bicycle_data(self, **extra):
        data = {
            "brand": "Trek", "model": "Marlin", "bike_type": "mountain",
            "frame_number": "", "notes": "",
        }
        data.update(extra)
        return data

    def test_bicycle_is_attached_to_customer_from_the_url(self):
        url = reverse("bicycle-create", args=[self.customer.pk])
        response = self.client.post(url, self.bicycle_data())
        self.assertRedirects(response, self.customer.get_absolute_url())
        self.assertEqual(Bicycle.objects.get(brand="Trek").customer, self.customer)

    def test_unknown_customer_gives_404(self):
        response = self.client.get(reverse("bicycle-create", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_duplicate_frame_number_is_rejected(self):
        Bicycle.objects.create(
            customer=self.customer, brand="A", model="1", frame_number="X1"
        )
        url = reverse("bicycle-create", args=[self.customer.pk])
        response = self.client.post(url, self.bicycle_data(frame_number="X1"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Bicycle.objects.count(), 1)

    def test_bicycles_without_frame_number_are_allowed(self):
        url = reverse("bicycle-create", args=[self.customer.pk])
        self.client.post(url, self.bicycle_data(brand="A"))
        self.client.post(url, self.bicycle_data(brand="B"))
        self.assertEqual(Bicycle.objects.count(), 2)

    def test_bicycle_edit_keeps_its_own_frame_number(self):
        bicycle = Bicycle.objects.create(
            customer=self.customer, brand="A", model="1", frame_number="X1"
        )
        response = self.client.post(
            reverse("bicycle-update", args=[bicycle.pk]),
            self.bicycle_data(brand="A", model="2", frame_number="X1"),
        )
        self.assertRedirects(response, self.customer.get_absolute_url())
        bicycle.refresh_from_db()
        self.assertEqual(bicycle.model, "2")

    def test_bicycle_with_orders_cannot_be_deleted(self):
        bicycle = Bicycle.objects.create(customer=self.customer, brand="A", model="1")
        RepairOrder.objects.create(
            bicycle=bicycle, problem_description="x",
            deadline=timezone.now() + timedelta(days=1),
        )
        self.client.post(reverse("bicycle-delete", args=[bicycle.pk]))
        self.assertTrue(Bicycle.objects.filter(pk=bicycle.pk).exists())

    def test_bicycle_without_orders_can_be_deleted(self):
        bicycle = Bicycle.objects.create(customer=self.customer, brand="A", model="1")
        self.client.post(reverse("bicycle-delete", args=[bicycle.pk]))
        self.assertFalse(Bicycle.objects.filter(pk=bicycle.pk).exists())

    def test_bicycle_page_shows_repair_history(self):
        bicycle = Bicycle.objects.create(customer=self.customer, brand="A", model="1")
        order = RepairOrder.objects.create(
            bicycle=bicycle, problem_description="x",
            deadline=timezone.now() + timedelta(days=1),
        )
        response = self.client.get(reverse("bicycle-detail", args=[bicycle.pk]))
        self.assertContains(response, f"#{order.pk}")
