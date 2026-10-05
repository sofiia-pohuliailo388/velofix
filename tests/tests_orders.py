from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Mechanic
from apps.catalog.models import Part, Service
from apps.customers.models import Bicycle, Customer

from apps.orders.forms import OrderServiceForm
from apps.orders.models import OrderPart, OrderService, RepairOrder, RepairOrderMechanic
from apps.orders.services import TransitionError, change_status


class OrderTestBase(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(full_name="Olivia Carter", phone="123")
        self.bicycle = Bicycle.objects.create(
            customer=self.customer, brand="Trek", model="Marlin"
        )
        self.service = Service.objects.create(name="Tune-up", base_price="500.00")
        self.part = Part.objects.create(
            name="Brake pad", sku="BP-1", stock_quantity=10, minimum_stock=2,
            purchase_price="100.00", selling_price="150.00",
        )

    def make_order(self, **kwargs):
        defaults = {
            "bicycle": self.bicycle,
            "problem_description": "Brakes",
            "deadline": timezone.now() + timedelta(days=1),
        }
        defaults.update(kwargs)
        return RepairOrder.objects.create(**defaults)

    def add_service(self, order, quantity=1, price="500.00"):
        return OrderService.objects.create(
            repair_order=order, service=self.service,
            quantity=quantity, unit_price=price,
        )


class RepairOrderTotalsTest(OrderTestBase):
    def test_empty_order_total_is_zero(self):
        self.assertEqual(self.make_order().total, Decimal("0"))

    def test_total_sums_services_and_parts(self):
        order = self.make_order()
        self.add_service(order, quantity=1, price="500.00")
        OrderPart.objects.create(
            repair_order=order, part=self.part, quantity=2, unit_price="150.00"
        )
        self.assertEqual(order.total_services, Decimal("500"))
        self.assertEqual(order.total_parts, Decimal("300"))
        self.assertEqual(order.total, Decimal("800"))

    def test_catalog_price_change_does_not_affect_order(self):
        order = self.make_order()
        self.add_service(order)
        self.service.base_price = Decimal("999.00")
        self.service.save()
        self.assertEqual(order.total_services, Decimal("500"))


class RepairOrderStateTest(OrderTestBase):
    def test_default_status_is_accepted(self):
        self.assertEqual(self.make_order().status, RepairOrder.Status.ACCEPTED)

    def test_overdue_when_deadline_passed(self):
        order = self.make_order(deadline=timezone.now() - timedelta(days=1))
        self.assertTrue(order.is_overdue)

    def test_not_overdue_when_deadline_in_future(self):
        self.assertFalse(self.make_order().is_overdue)

    def test_delivered_and_cancelled_are_never_overdue(self):
        past = timezone.now() - timedelta(days=1)
        for status in (RepairOrder.Status.DELIVERED, RepairOrder.Status.CANCELLED):
            order = self.make_order(deadline=past, status=status)
            self.assertFalse(order.is_overdue)

    def test_quote_approval_follows_versions(self):
        order = self.make_order()
        self.assertFalse(order.is_quote_approved)
        order.approved_version = 1
        self.assertTrue(order.is_quote_approved)
        order.quote_version = 2
        self.assertFalse(order.is_quote_approved)

    def test_closed_orders_have_no_transitions(self):
        for status in (RepairOrder.Status.DELIVERED, RepairOrder.Status.CANCELLED):
            order = self.make_order(status=status)
            self.assertTrue(order.is_closed)
            self.assertEqual(order.allowed_transitions, [])

    def test_open_order_offers_next_steps(self):
        order = self.make_order()
        values = [value for value, label in order.allowed_transitions]
        self.assertEqual(values, ["diagnosis", "cancelled"])
        self.assertFalse(order.is_closed)


class OrderConstraintsTest(OrderTestBase):
    def test_same_mechanic_cannot_be_assigned_twice(self):
        order = self.make_order()
        mechanic = Mechanic.objects.create_user(username="ivan", password="x")
        RepairOrderMechanic.objects.create(repair_order=order, mechanic=mechanic)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RepairOrderMechanic.objects.create(repair_order=order, mechanic=mechanic)

    def test_part_cannot_be_returned_without_being_used(self):
        order = self.make_order()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OrderPart.objects.create(
                    repair_order=order, part=self.part, quantity=1,
                    unit_price="150.00", returned_at=timezone.now(),
                )

    def test_order_line_quantity_must_be_positive(self):
        order = self.make_order()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.add_service(order, quantity=0)

    def test_used_service_cannot_be_deleted_from_catalog(self):
        self.add_service(self.make_order())
        with self.assertRaises(ProtectedError):
            self.service.delete()

    def test_bicycle_with_orders_cannot_be_deleted(self):
        self.make_order()
        with self.assertRaises(ProtectedError):
            self.bicycle.delete()


class ChangeStatusTest(OrderTestBase):
    def test_allowed_transition_changes_status(self):
        order = self.make_order()
        change_status(order, "diagnosis")
        order.refresh_from_db()
        self.assertEqual(order.status, "diagnosis")

    def test_skipping_a_stage_is_rejected(self):
        order = self.make_order()
        with self.assertRaises(TransitionError):
            change_status(order, "delivered")
        order.refresh_from_db()
        self.assertEqual(order.status, "accepted")

    def test_unknown_status_is_rejected(self):
        order = self.make_order()
        with self.assertRaises(TransitionError):
            change_status(order, "bogus")

    def test_work_cannot_start_without_services(self):
        order = self.make_order(status="diagnosis")
        with self.assertRaises(TransitionError):
            change_status(order, "in_progress")
        order.refresh_from_db()
        self.assertEqual(order.status, "diagnosis")

    def test_work_can_start_when_order_has_a_service(self):
        order = self.make_order(status="diagnosis")
        self.add_service(order)
        change_status(order, "in_progress")
        order.refresh_from_db()
        self.assertEqual(order.status, "in_progress")

    def test_ready_sets_completion_date(self):
        order = self.make_order(status="in_progress")
        change_status(order, "ready")
        order.refresh_from_db()
        self.assertIsNotNone(order.completed_at)

    def test_delivery_sets_delivery_and_payment_dates(self):
        order = self.make_order(status="ready")
        change_status(order, "delivered")
        order.refresh_from_db()
        self.assertIsNotNone(order.delivered_at)
        self.assertIsNotNone(order.paid_at)

    def test_order_can_be_cancelled_before_delivery(self):
        order = self.make_order(status="in_progress")
        change_status(order, "cancelled")
        order.refresh_from_db()
        self.assertEqual(order.status, "cancelled")

    def test_closed_order_cannot_be_reopened(self):
        order = self.make_order(status="delivered")
        with self.assertRaises(TransitionError):
            change_status(order, "cancelled")


class OrderPagesTest(OrderTestBase):
    def setUp(self):
        super().setUp()
        self.user = Mechanic.objects.create_user(username="tester", password="x")
        self.client.force_login(self.user)

    def test_order_list_requires_login(self):
        self.client.logout()
        url = reverse("order-list")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_order_detail_page_opens(self):
        order = self.make_order()
        response = self.client.get(order.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Order #{order.pk}")

    def test_adding_service_copies_catalog_price(self):
        order = self.make_order()
        url = reverse("order-service-add", args=[order.pk])
        response = self.client.post(url, {"service": self.service.pk, "quantity": 2})
        self.assertRedirects(response, order.get_absolute_url())

        line = order.service_lines.get()
        self.assertEqual(line.unit_price, Decimal("500.00"))

        self.service.base_price = Decimal("999.00")
        self.service.save()
        line.refresh_from_db()
        self.assertEqual(line.unit_price, Decimal("500.00"))

    def test_zero_quantity_is_rejected(self):
        order = self.make_order()
        url = reverse("order-service-add", args=[order.pk])
        response = self.client.post(url, {"service": self.service.pk, "quantity": 0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(order.service_lines.count(), 0)

    def test_archived_service_is_not_offered(self):
        archived = Service.objects.create(name="Old", base_price="10", is_active=False)
        queryset = OrderServiceForm().fields["service"].queryset
        self.assertIn(self.service, queryset)
        self.assertNotIn(archived, queryset)

    def test_removing_a_service_line(self):
        order = self.make_order()
        line = self.add_service(order)
        response = self.client.post(reverse("order-service-delete", args=[line.pk]))
        self.assertRedirects(response, order.get_absolute_url())
        self.assertEqual(order.service_lines.count(), 0)

    def test_status_change_through_the_page(self):
        order = self.make_order()
        response = self.client.post(
            reverse("order-status", args=[order.pk]), {"status": "diagnosis"}
        )
        self.assertRedirects(response, order.get_absolute_url())
        order.refresh_from_db()
        self.assertEqual(order.status, "diagnosis")

    def test_forbidden_status_change_is_refused_with_a_message(self):
        order = self.make_order()
        response = self.client.post(
            reverse("order-status", args=[order.pk]),
            {"status": "delivered"},
            follow=True,
        )
        order.refresh_from_db()
        self.assertEqual(order.status, "accepted")
        self.assertContains(response, "This change is not allowed.")

    def test_status_change_does_not_accept_get(self):
        order = self.make_order()
        response = self.client.get(reverse("order-status", args=[order.pk]))
        self.assertEqual(response.status_code, 405)

    def test_overdue_filter(self):
        overdue = self.make_order(deadline=timezone.now() - timedelta(days=1))
        self.make_order()
        response = self.client.get(reverse("order-list"), {"overdue": "1"})
        pks = [order.pk for order in response.context["orders"]]
        self.assertEqual(pks, [overdue.pk])

    def test_status_filter(self):
        ready = self.make_order(status="ready")
        self.make_order()
        response = self.client.get(reverse("order-list"), {"status": "ready"})
        pks = [order.pk for order in response.context["orders"]]
        self.assertEqual(pks, [ready.pk])

    def test_search_matches_every_word_in_any_order(self):
        self.make_order()
        url = reverse("order-list")
        found = self.client.get(url, {"q": "Marlin Trek"})
        self.assertEqual(len(found.context["orders"]), 1)
        by_customer = self.client.get(url, {"q": "Carter Marlin"})
        self.assertEqual(len(by_customer.context["orders"]), 1)
        missing = self.client.get(url, {"q": "Giant"})
        self.assertEqual(len(missing.context["orders"]), 0)
