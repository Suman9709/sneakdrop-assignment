from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db import transaction

from inventory.models import Inventory
from orders.models import Order
from reservation.models import Hold
from waitlist.models import WaitlistEntry


LIMITED_SNEAKER_SKU = "limited-edition-sneaker"


class UserHasActiveHold(Exception):
    pass


class PurchaseLimitReached(Exception):
    pass


class StockStillAvailable(Exception):
    pass


@dataclass
class WaitlistResult:
    entry: WaitlistEntry
    position: int
    already_waiting: bool = False


def get_waitlist_position(entry: WaitlistEntry) -> int:
    return (
        WaitlistEntry.objects.filter(
            inventory=entry.inventory,
            status=WaitlistEntry.Status.WAITING,
        )
        .filter(
            created_at__lt=entry.created_at
        )
        .count()
        + 1
    )


@transaction.atomic
def join_waitlist(user_id: int) -> WaitlistResult:
   
    # Add a user to the FIFO waitlist only when no stock is available.
   

    inventory = Inventory.objects.select_for_update().get(
        sku=LIMITED_SNEAKER_SKU
    )

    User = get_user_model()
    user = User.objects.select_for_update().get(pk=user_id)

    active_hold = (
        Hold.objects.select_for_update()
        .filter(user=user, status=Hold.Status.ACTIVE)
        .first()
    )

    if active_hold:
        raise UserHasActiveHold("A user with an active hold cannot join the waitlist.")

    if Order.objects.filter(user=user).count() >= 2:
        raise PurchaseLimitReached("A user may buy only two pairs in total.")

    existing_entry = (
        WaitlistEntry.objects.select_for_update()
        .filter(
            user=user,
            inventory=inventory,
            status=WaitlistEntry.Status.WAITING,
        )
        .first()
    )

    if existing_entry:
        return WaitlistResult(
            entry=existing_entry,
            position=get_waitlist_position(existing_entry),
            already_waiting=True,
        )

    if inventory.available_stock > 0:
        raise StockStillAvailable(
            "Stock is available. The user should create a hold instead."
        )

    entry = WaitlistEntry.objects.create(
        user=user,
        inventory=inventory,
        status=WaitlistEntry.Status.WAITING,
    )

    return WaitlistResult(
        entry=entry,
        position=get_waitlist_position(entry),
    )