from django.db import models


class Sucursal(models.Model):
    """Sucursal - Tienda/Punto de venta donde se reciben productos"""
    bpl_id = models.IntegerField(unique=True, help_text="ID único de la sucursal en el sistema ERP")
    name = models.CharField(max_length=255, unique=True, help_text="Nombre de la tienda/sucursal")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sucursal (Tienda)"
        verbose_name_plural = "Sucursales (Tiendas)"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.bpl_id})"
