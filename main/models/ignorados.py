"""
Modelos para guardar nombres de CEDIS y Sucursales a ignorar durante la normalización.
Estos registros se saltan automáticamente en el proceso de normalización.
"""
from django.db import models


class IgnorarCedis(models.Model):
    """
    Guarda nombres de CEDIS (en datos crudos) que deben ser ignorados.
    Durante la normalización, cualquier registro con este nombre se marca como 'ignored'.
    """
    nombre_crudo = models.CharField(
        max_length=255, 
        unique=True, 
        help_text="Nombre de CEDIS tal como aparece en los Excel que debe ser ignorado"
    )
    razon = models.CharField(
        max_length=500, 
        blank=True, 
        default="",
        help_text="Razón por la cual se ignora este CEDIS"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "CEDIS Ignorado"
        verbose_name_plural = "CEDIS Ignorados"
        ordering = ["nombre_crudo"]

    def __str__(self):
        return f"🚫 {self.nombre_crudo}"


class IgnorarSucursal(models.Model):
    """
    Guarda nombres de Sucursales (en datos crudos) que deben ser ignorados.
    Durante la normalización, cualquier registro con este nombre se marca como 'ignored'.
    """
    nombre_crudo = models.CharField(
        max_length=255, 
        unique=True, 
        help_text="Nombre de Sucursal tal como aparece en los Excel que debe ser ignorado"
    )
    razon = models.CharField(
        max_length=500, 
        blank=True, 
        default="",
        help_text="Razón por la cual se ignora esta Sucursal"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sucursal Ignorada"
        verbose_name_plural = "Sucursales Ignoradas"
        ordering = ["nombre_crudo"]

    def __str__(self):
        return f"🚫 {self.nombre_crudo}"
