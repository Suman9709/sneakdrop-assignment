from dataclasses import dataclass
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from inventory.models import Inventory
from orders.models import Order
from reservation.models import Hold
from waitlist.models import WaitlistEntry


HOLD_DURATION = timedelta(minutes=5)
LIMITED_SNEAKER_SKU = "limited-edition-sneaker"


class ActiveHoldExists(Exception):
    def __init__(self, hold):
        self.hold = hold
        super().__init__("User already has an active hold.")


class PurchaseLimitReached(Exception):
    pass


@dataclass
class BuyResult:
    outcome: str
    hold: Hold | None = None


def _promote_waitlist(inventory: Inventory, now):
    """
    Give every newly available pair to waiting users in FIFO order.

    inventory must already be locked with select_for_update().
    """
    User = get_user_model()
    promoted_holds = []

    while inventory.available_stock > 0:
        entry = (
            WaitlistEntry.objects.select_for_update()
            .filter(
                inventory=inventory,
                status=WaitlistEntry.Status.WAITING,
            )
            .order_by("created_at", "id")
            .first()
        )

        if entry is None:
            break

        user = User.objects.select_for_update().get(pk=entry.user_id)

        user_has_active_hold = (
            Hold.objects.select_for_update()
            .filter(user=user, status=Hold.Status.ACTIVE)
            .exists()
        )

        user_has_reached_limit = Order.objects.filter(user=user).count() >= 2

        # Defensive cleanup: skip queue entries that can no longer receive stock.
        if user_has_active_hold or user_has_reached_limit:
            entry.status = WaitlistEntry.Status.CANCELLED
            entry.save(update_fields=["status"])
            continue

        hold = Hold.objects.create(
            user=user,
            inventory=inventory,
            status=Hold.Status.ACTIVE,
            expires_at=now + HOLD_DURATION,
        )

        entry.status = WaitlistEntry.Status.ASSIGNED
        entry.assigned_hold = hold
        entry.save(update_fields=["status", "assigned_hold"])

        inventory.available_stock -= 1
        promoted_holds.append(hold)

    return promoted_holds


def expire_holds_and_promote_waitlist(inventory: Inventory, now):
 
    expired_holds = list(
        Hold.objects.select_for_update().filter(
            inventory=inventory,
            status=Hold.Status.ACTIVE,
            expires_at__lte=now,
        )
    )

    for hold in expired_holds:
        hold.status = Hold.Status.EXPIRED
        hold.save(update_fields=["status"])

    inventory.available_stock += len(expired_holds)

    promoted_holds = _promote_waitlist(inventory, now)

    if expired_holds or promoted_holds:
        inventory.save(update_fields=["available_stock", "updated_at"])

    return expired_holds, promoted_holds


@transaction.atomic
def buy_for_user(user_id: int) -> BuyResult:
    # Lock stock first. Every stock-changing workflow uses this lock order.
    inventory = Inventory.objects.select_for_update().get(
        sku=LIMITED_SNEAKER_SKU
    )

    now = timezone.now()

    # Do this before allowing a new buyer to claim released stock.
    # It preserves FIFO priority for waitlisted users.
    expire_holds_and_promote_waitlist(inventory, now)

    User = get_user_model()
    user = User.objects.select_for_update().get(pk=user_id)

    active_hold = (
        Hold.objects.select_for_update()
        .filter(user=user, status=Hold.Status.ACTIVE)
        .first()
    )

    if active_hold:
        raise ActiveHoldExists(active_hold)

    if Order.objects.filter(user=user).count() >= 2:
        raise PurchaseLimitReached("A user may buy only two pairs in total.")

    if inventory.available_stock == 0:
        return BuyResult(outcome="sold_out")

    inventory.available_stock -= 1
    inventory.save(update_fields=["available_stock", "updated_at"])

    hold = Hold.objects.create(
        user=user,
        inventory=inventory,
        status=Hold.Status.ACTIVE,
        expires_at=now + HOLD_DURATION,
    )

    return BuyResult(outcome="held", hold=hold)