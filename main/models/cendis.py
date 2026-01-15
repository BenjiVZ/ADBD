from django.db import models


class Cendis(models.Model):
    """Centro de Distribución (CEDIS) - Almacén desde donde se despachan productos"""
    origin = models.CharField(max_length=255, help_text="Nombre del almacén/centro de distribución")
    code = models.CharField(max_length=50, unique=True, help_text="Código único del CEDIS")

    class Meta:
        verbose_name = "CEDIS (Almacén)"
        verbose_name_plural = "CEDIS (Almacenes)"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.origin}"
