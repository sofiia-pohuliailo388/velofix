from django.utils import timezone

class TransitionError(Exception):
    pass


def change_status(order, new_status):
    allowed = [value for value, label in order.allowed_transitions]
    if new_status not in allowed:
        raise TransitionError("This change is not allowed.")

    if new_status == "in_progress" and not order.service_lines.exists():
        raise TransitionError("Add at least one service before starting work.")

    now = timezone.now()
    if new_status == "ready":
        order.completed_at = now
    if new_status == "delivered":
        order.delivered_at = now
        order.paid_at = now

    order.status = new_status
    order.save()