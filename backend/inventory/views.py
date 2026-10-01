from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from inventory.models import Inventory
from waitlist.models import WaitlistEntry


@api_view(["GET"])
@permission_classes([AllowAny])
def sneaker_status(request):
    inventory = Inventory.objects.get(
        sku="limited-edition-sneaker"
    )

    waiting_count = WaitlistEntry.objects.filter(
        inventory=inventory,
        status=WaitlistEntry.Status.WAITING,
    ).count()

    return Response(
        {
            "sku": inventory.sku,
            "total_stock": inventory.total_stock,
            "available_stock": inventory.available_stock,
            "sold_out": inventory.available_stock == 0,
            "waitlist_count": waiting_count,
        }
    )