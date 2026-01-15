from django.db import models

from .product import Product


class Pvp(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="pvps")
    sku = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "PVP"
        verbose_name_plural = "PVP"
        ordering = ["sku"]

    def __str__(self) -> str:
        return f"{self.sku} - {self.description} (${self.price})"
