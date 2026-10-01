from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from waitlist.services import (
    PurchaseLimitReached,
    StockStillAvailable,
    UserHasActiveHold,
    join_waitlist,
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def join_sneaker_waitlist(request):
    try:
        result = join_waitlist(request.user.id)

    except UserHasActiveHold as error:
        return Response(
            {"detail": str(error)},
            status=status.HTTP_409_CONFLICT,
        )

    except PurchaseLimitReached as error:
        return Response(
            {"detail": str(error)},
            status=status.HTTP_409_CONFLICT,
        )

    except StockStillAvailable as error:
        return Response(
            {"detail": str(error)},
            status=status.HTTP_409_CONFLICT,
        )

    return Response(
        {
            "outcome": "already_waiting" if result.already_waiting else "waiting",
            "waitlist_entry_id": result.entry.id,
            "position": result.position,
        },
        status=(
            status.HTTP_200_OK
            if result.already_waiting
            else status.HTTP_201_CREATED
        ),
    )