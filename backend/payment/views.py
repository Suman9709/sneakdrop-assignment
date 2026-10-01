from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payment.services import (
    HoldDoesNotBelongToUser,
    HoldNotFound,
    process_successful_payment,
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_payment(request):
    hold_id = request.data.get("hold_id")
    event_id = str(request.data.get("event_id", "")).strip()
    payment_id = str(request.data.get("payment_id", "")).strip()

    try:
        hold_id = int(hold_id)
    except (TypeError, ValueError):
        return Response(
            {"detail": "hold_id must be a valid integer."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if hold_id < 1 or not event_id or not payment_id:
        return Response(
            {
                "detail": (
                    "hold_id, event_id, and payment_id are required."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = process_successful_payment(
            user_id=request.user.id,
            hold_id=hold_id,
            event_id=event_id,
            payment_id=payment_id,
        )

    except HoldNotFound as error:
        return Response(
            {"detail": str(error)},
            status=status.HTTP_404_NOT_FOUND,
        )

    except HoldDoesNotBelongToUser as error:
        return Response(
            {"detail": str(error)},
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(
        {
            "outcome": result.outcome,
            "event_id": result.event.event_id,
            "payment_id": result.event.payment_id,
            "hold_id": result.event.hold_id,
            "order_id": result.order.id if result.order else None,
        },
        status=status.HTTP_200_OK,
    )