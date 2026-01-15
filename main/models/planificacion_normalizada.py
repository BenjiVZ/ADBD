from django.db import models

from .planificacion import Planificacion
from .product import Product
from .cendis import Cendis
from .sucursal import Sucursal


class PlanificacionNormalizada(models.Model):
    """Planificación normalizada: Almacén (CEDIS) → Tienda (Sucursal)"""
    raw = models.OneToOneField(Planificacion, on_delete=models.CASCADE, related_name="normalizada")
    plan_month = models.DateField()
    tipo_carga = models.CharField(max_length=100, blank=True, default="")
    item_code = models.CharField(max_length=100, blank=True, default="")
    item_name = models.CharField(max_length=255, blank=True, default="")
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name="planificaciones_destino", help_text="Tienda destino")
    cedis_origen = models.ForeignKey(Cendis, on_delete=models.PROTECT, null=True, blank=True, related_name="planificaciones_origen", help_text="Almacén origen")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    cendis = models.CharField(max_length=255, blank=True, default="")  # Mantener para referencia
    a_despachar_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Planificacion normalizada"
        verbose_name_plural = "Planificaciones normalizadas"
        ordering = ["-plan_month", "item_code", "sucursal__name"]
        indexes = [
            models.Index(fields=["plan_month", "item_code"]),
            models.Index(fields=["plan_month", "sucursal"]),
        ]

    def __str__(self) -> str:
        return f"{self.plan_month} - {self.item_code} - {self.sucursal.name}"
