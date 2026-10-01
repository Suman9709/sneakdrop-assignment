from django.db import models
from django.conf import settings
from django.db.models import Q

# Create your models here.
class Hold(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        PAID = "paid", "Paid"
        
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="holds"
    )
    
    inventory = models.ForeignKey(
        "inventory.Inventory", on_delete=models.PROTECT, related_name="holds"
    )
    
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE,
    )
    
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    
    class Meta:
        indexes = [
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["user", "status"]),
        ]
        
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status="active"),
                name="one_active_hold_per_user",
            ),
        ]

    def __str__(self):
        return f"Hold #{self.pk} - {self.user} - {self.status}"
