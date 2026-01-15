from django.db import models

from .product import Product
from .salida import Salida
from .cendis import Cendis
from .sucursal import Sucursal


class SalidaNormalizada(models.Model):
    """Salida normalizada: Almacén (CEDIS) → Tienda (Sucursal) o Tienda → Tienda"""
    raw = models.OneToOneField(Salida, on_delete=models.CASCADE, related_name="normalizada")
    salida = models.CharField(max_length=100, blank=True, default="")
    fecha_salida = models.DateField(null=True, blank=True)
    sku = models.CharField(max_length=100, blank=True, default="")
    descripcion = models.CharField(max_length=255, blank=True, default="")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    cedis_origen = models.ForeignKey(Cendis, on_delete=models.PROTECT, related_name="salidas_origen", null=True, blank=True, help_text="Almacén origen (si aplica)")
    sucursal_destino = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name="salidas_destino", null=True, blank=True, help_text="Tienda destino")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    origen_nombre = models.CharField(max_length=255, blank=True, default="")
    destino_nombre = models.CharField(max_length=255, blank=True, default="")
    entrada = models.CharField(max_length=100, blank=True, default="")
    fecha_entrada = models.DateField(null=True, blank=True)
    comments = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Salida normalizada"
        verbose_name_plural = "Salidas normalizadas"
        ordering = ["-fecha_salida", "salida", "sku"]
        indexes = [
            models.Index(fields=["fecha_salida", "sku"]),
            models.Index(fields=["fecha_salida", "cedis_origen"]),
            models.Index(fields=["fecha_salida", "sucursal_destino"]),
        ]

    def __str__(self) -> str:
        return f"{self.salida or 'Salida'} - {self.sku}"
