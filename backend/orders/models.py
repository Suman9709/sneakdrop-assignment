from django.db import models

# Create your models here.
from django.conf import settings


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    hold = models.OneToOneField(
        "reservation.Hold", on_delete=models.PROTECT, related_name="order"
    )
    quantity = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Order #{self.pk} - {self.user} - Quantity: {self.quantity} pair"