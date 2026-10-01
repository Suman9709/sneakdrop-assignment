from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# Create your views here.


from reservation.services import PurchaseLimitReached, buy_for_user, ActiveHoldExists
def hold_data(hold):
    return {
        "hold_id": hold.id,
        "status":hold.status,
        "expires_at": hold.expires_at.isoformat(),
    }
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_sneaker(request):
    try:
        result = buy_for_user(request.user.id)
    except ActiveHoldExists as error:
        return Response(
            {
                "detail": "User already has an active hold.",
                "hold": hold_data(error.hold),
            },
            status = status.HTTP_409_CONFLICT
        )
    except PurchaseLimitReached as error:
        return Response(
            {"detail":str(error) },
            status=status.HTTP_409_CONFLICT
        )
    if result.outcome == "sold_out":
        return Response(
            {
                "outcome": "sold_out",
                "detail":"Snakers are sold out. Keepp waiting for restock."
                },
            status=status.HTTP_409_CONFLICT
        )
    return Response(
        {
            "outcome":"held",
            "hold":hold_data(result.hold)
        },
        status = status.HTTP_201_CREATED
        
    )
        