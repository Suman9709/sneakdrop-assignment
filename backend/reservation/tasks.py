from celery import shared_task
from django.db import transaction
from django.utils import timezone

from inventory.models import Inventory
from reservation.services import (
    LIMITED_SNEAKER_SKU,
    expire_holds_and_promote_waitlist,
)


@shared_task(name="reservation.expire_expired_holds")
def expire_expired_holds():
    with transaction.atomic():
        inventory = Inventory.objects.select_for_update().get(
            sku=LIMITED_SNEAKER_SKU
        )

        expired_holds, promoted_holds = expire_holds_and_promote_waitlist(
            inventory=inventory,
            now=timezone.now(),
        )

    return {
        "expired_hold_ids": [hold.id for hold in expired_holds],
        "promoted_hold_ids": [hold.id for hold in promoted_holds],
    }