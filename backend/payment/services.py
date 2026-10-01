from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone

from inventory.models import Inventory
from orders.models import Order
from payment.models import PaymentEvent
from reservation.models import Hold
from reservation.services import expire_holds_and_promote_waitlist


class HoldNotFound(Exception):
    pass


class HoldDoesNotBelongToUser(Exception):
    pass


@dataclass
class PaymentResult:
    outcome: str
    event: PaymentEvent
    order: Order | None


def _order_for_hold(hold_id):
    return Order.objects.filter(hold_id=hold_id).first()


@transaction.atomic
def process_successful_payment(
    *,
    user_id,
    hold_id,
    event_id,
    payment_id,
):
    # Idempotency: the same provider event must never be processed twice.
    existing_event = PaymentEvent.objects.filter(event_id=event_id).first()
    if existing_event:
        return PaymentResult(
            outcome=existing_event.outcome,
            event=existing_event,
            order=_order_for_hold(existing_event.hold_id),
        )

    hold_info = Hold.objects.filter(pk=hold_id).values(
        "inventory_id",
        "user_id",
    ).first()

    if hold_info is None:
        raise HoldNotFound("Reservation hold does not exist.")

    if hold_info["user_id"] != user_id:
        raise HoldDoesNotBelongToUser(
            "You cannot pay for another user's reservation."
        )

    # Keep the same lock order as buy/expiry workflows: inventory first.
    inventory = Inventory.objects.select_for_update().get(
        pk=hold_info["inventory_id"]
    )

    now = timezone.now()
    expire_holds_and_promote_waitlist(inventory, now)

    # Check again after acquiring the inventory lock.
    existing_event = PaymentEvent.objects.filter(event_id=event_id).first()
    if existing_event:
        return PaymentResult(
            outcome=existing_event.outcome,
            event=existing_event,
            order=_order_for_hold(existing_event.hold_id),
        )

    hold = Hold.objects.select_for_update().get(pk=hold_id)

    if hold.status == Hold.Status.ACTIVE:
        hold.status = Hold.Status.PAID
        hold.paid_at = now
        hold.save(update_fields=["status", "paid_at"])

        order = Order.objects.create(
            user_id=user_id,
            hold=hold,
            quantity=1,
        )
        outcome = PaymentEvent.Outcome.PROCESSED

    elif hold.status == Hold.Status.PAID:
        order = _order_for_hold(hold.id)
        outcome = PaymentEvent.Outcome.DUPLICATE

    else:
        # The hold expired before payment arrived.
        order = None
        outcome = PaymentEvent.Outcome.LATE

    try:
        with transaction.atomic():
            event = PaymentEvent.objects.create(
                event_id=event_id,
                payment_id=payment_id,
                hold=hold,
                event_type=PaymentEvent.EventType.SUCCEEDED,
                outcome=outcome,
                payload={
                    "hold_id": hold.id,
                    "payment_id": payment_id,
                },
            )
    except IntegrityError:
        # Handles two identical webhook requests arriving at once.
        event = PaymentEvent.objects.get(event_id=event_id)
        return PaymentResult(
            outcome=event.outcome,
            event=event,
            order=_order_for_hold(event.hold_id),
        )

    return PaymentResult(outcome=outcome, event=event, order=order)