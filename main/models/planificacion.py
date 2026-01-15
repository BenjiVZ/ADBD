from django.db import models


class Planificacion(models.Model):
    plan_month = models.DateField()
    tipo_carga = models.CharField(max_length=100, blank=True, default="")
    item_code = models.CharField(max_length=100, blank=True, default="")
    item_name = models.CharField(max_length=255, blank=True, default="")
    sucursal = models.CharField(max_length=255, blank=True, default="")
    cendis = models.CharField(max_length=255, blank=True, default="")
    a_despachar_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    normalize_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pendiente"), 
            ("ok", "Normalizado"), 
            ("error", "Error"),
            ("ignored", "Ignorado"),
        ],
        default="pending",
    )
    normalize_notes = models.TextField(blank=True, default="")
    normalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Planificacion mensual"
        verbose_name_plural = "Planificaciones mensuales"
        ordering = ["-plan_month", "item_code", "sucursal"]
        indexes = [
            models.Index(fields=["normalize_status", "plan_month"]),
            models.Index(fields=["item_code"]),
            models.Index(fields=["sucursal"]),
            models.Index(fields=["plan_month", "item_code", "sucursal"]),
        ]

    def __str__(self) -> str:
        return f"{self.plan_month} - {self.item_code}"
