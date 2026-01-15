from django.db import models


class PlanningBatch(models.Model):
    plan_date = models.DateField()
    sheet_name = models.CharField(max_length=255)
    source_filename = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Planificacion"
        verbose_name_plural = "Planificaciones"
        ordering = ["-plan_date", "-id"]

    def __str__(self) -> str:
        return f"{self.plan_date} - {self.sheet_name}"


class PlanningEntry(models.Model):
    batch = models.ForeignKey(PlanningBatch, on_delete=models.CASCADE, related_name="entries")
    external_id = models.CharField(max_length=100, blank=True, default="")
    tipo_carga = models.CharField(max_length=100, blank=True, default="")
    ranking_tienda = models.IntegerField(null=True, blank=True)
    sucursal = models.CharField(max_length=255, blank=True, default="")
    item_code = models.CharField(max_length=100, blank=True, default="")
    item_name = models.CharField(max_length=255, blank=True, default="")
    u_categoria = models.CharField(max_length=100, blank=True, default="")
    categoria = models.CharField(max_length=100, blank=True, default="")
    a_despachar_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    motivo_decision = models.CharField(max_length=255, blank=True, default="")
    en_transito = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    ult_entrada_almacen = models.DateField(null=True, blank=True)
    ult_venta_tienda = models.DateField(null=True, blank=True)
    dias_permanencia = models.IntegerField(null=True, blank=True)
    venta_diaria = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    stock_tienda = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    stock_cedis = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    necesidad_urgente = models.BooleanField(default=False)
    cendis = models.CharField(max_length=100, blank=True, default="")
    no_planificar = models.BooleanField(default=False)
    ng = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    ccct = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    sm = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    cubicaje_unidad = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    cubicaje_total = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)

    class Meta:
        verbose_name = "Detalle de Planificacion"
        verbose_name_plural = "Detalle de Planificacion"
        ordering = ["item_code", "sucursal"]

    def __str__(self) -> str:
        return f"{self.batch.plan_date} - {self.item_code}"