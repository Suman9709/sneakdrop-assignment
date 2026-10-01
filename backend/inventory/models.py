from django.db import models
from django.db.models import F, Q


class Inventory(models.Model):
    sku = models.CharField(
        max_length=100,
        unique=True,
        default="limited-edition-sneaker",
    )
    total_stock = models.PositiveIntegerField(default=20)
    available_stock = models.PositiveIntegerField(default=20)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(available_stock__gte=0),
                name="inventory_available_stock_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(total_stock__gte=F("available_stock")),
                name="inventory_available_stock_not_above_total",
            ),
        ]

    def __str__(self):
        return f"{self.sku}: {self.available_stock}/{self.total_stock} available"
