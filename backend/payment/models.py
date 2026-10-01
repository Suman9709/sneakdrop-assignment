from django.db import models


class PaymentEvent(models.Model):
    class EventType(models.TextChoices):
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    class Outcome(models.TextChoices):
        PROCESSED = "processed", "Processed"
        DUPLICATE = "duplicate", "Duplicate"
        LATE = "late", "Late"
        IGNORED = "ignored", "Ignored"

    event_id = models.CharField(max_length=255, unique=True)
    payment_id = models.CharField(max_length=255)
    hold = models.ForeignKey(
        "reservation.Hold",
        on_delete=models.PROTECT,
        related_name="payment_events",
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    outcome = models.CharField(
        max_length=20,
        choices=Outcome.choices,
        null=True,
        blank=True,
    )
    payload = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["payment_id"]),
            models.Index(fields=["hold", "received_at"]),
        ]

    def __str__(self):
        return f"{self.event_id} - {self.event_type} - {self.outcome}"
