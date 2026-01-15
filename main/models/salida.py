from django.db import models


class Salida(models.Model):
    salida = models.CharField(max_length=100, blank=True, default="")
    fecha_salida = models.DateField(null=True, blank=True)
    nombre_sucursal_origen = models.CharField(max_length=255, blank=True, default="")
    nombre_almacen_origen = models.CharField(max_length=255, blank=True, default="")
    sku = models.CharField(max_length=100, blank=True, default="")
    descripcion = models.CharField(max_length=255, blank=True, default="")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    sucursal_destino_propuesto = models.CharField(max_length=255, blank=True, default="")
    entrada = models.CharField(max_length=100, blank=True, default="")
    fecha_entrada = models.DateField(null=True, blank=True)
    nombre_sucursal_destino = models.CharField(max_length=255, blank=True, default="")
    nombre_almacen_destino = models.CharField(max_length=255, blank=True, default="")
    comments = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    normalize_status = models.CharField(
        max_length=20,
        choices=[("pending", "Pendiente"), ("ok", "Normalizado"), ("error", "Error")],
        default="pending",
    )
    normalize_notes = models.TextField(blank=True, default="")
    normalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Salida"
        verbose_name_plural = "Salidas"
        ordering = ["-fecha_salida", "-id"]
        indexes = [
            models.Index(fields=["normalize_status", "fecha_salida"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["nombre_sucursal_origen"]),
            models.Index(fields=["nombre_sucursal_destino"]),
        ]

    def __str__(self) -> str:
        return f"{self.salida or 'Salida'} - {self.sku}"
