from django.db import models
from django.db.models import Q
from django.conf import settings

# Create your models here.


class WaitlistEntry(models.Model):
    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        ASSIGNED = "assigned", "Assigned"
        CANCELLED = "cancelled", "Cancelled"
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="waitlist_entries"
    )
    inventory = models.ForeignKey(
        "inventory.Inventory", on_delete=models.PROTECT, related_name="waitlist_entries"
    )
    
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.WAITING
    )
    assigned_hold = models.OneToOneField(
        "reservation.Hold", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="waitlist_entry"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    class Meta:
        indexes = [
            models.Index(fields=["inventory", "status", "created_at", "id"]),
        ]
        
        
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status="waiting"),
                name="one_waiting_entry_per_user",
            ),
        ]

    def __str__(self):
        return f"WaitlistEntry #{self.pk} - {self.user} - {self.status}"
