from django.db import models
from .gerente_regional import GerenteRegional


class Region(models.Model):
    """Región - Agrupación geográfica de sucursales"""
    name = models.CharField(max_length=255, unique=True, help_text="Nombre de la región")
    gerente = models.ForeignKey(
        GerenteRegional, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="regiones",
        help_text="Gerente responsable de esta región"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Región"
        verbose_name_plural = "Regiones"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.gerente.name if self.gerente else 'Sin Gerente'})"
