"""
Modelos para guardar mapeos/alias de CEDIS y Sucursales.
Estos mapeos NO modifican los datos crudos originales.
"""
from django.db import models


class MapeoCedis(models.Model):
    """
    Guarda la relación entre un nombre crudo y un CEDIS oficial.
    Ejemplo: "Guatire I" -> Cendis(origin="Guatire 1")
    """
    nombre_crudo = models.CharField(max_length=255, unique=True, help_text="Nombre tal como aparece en los Excel")
    cedis_oficial = models.ForeignKey(
        "main.Cendis", 
        on_delete=models.CASCADE, 
        related_name="mapeos",
        help_text="CEDIS oficial al que corresponde"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mapeo de CEDIS"
        verbose_name_plural = "Mapeos de CEDIS"
        ordering = ["nombre_crudo"]

    def __str__(self):
        return f"{self.nombre_crudo} → {self.cedis_oficial.origin}"


class MapeoSucursal(models.Model):
    """
    Guarda la relación entre un nombre crudo y una Sucursal oficial.
    Ejemplo: "SAMBIL VALENCIA" -> Sucursal(name="Sambil Valencia")
    """
    nombre_crudo = models.CharField(max_length=255, unique=True, help_text="Nombre tal como aparece en los Excel")
    sucursal_oficial = models.ForeignKey(
        "main.Sucursal", 
        on_delete=models.CASCADE, 
        related_name="mapeos",
        help_text="Sucursal oficial a la que corresponde"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mapeo de Sucursal"
        verbose_name_plural = "Mapeos de Sucursales"
        ordering = ["nombre_crudo"]

    def __str__(self):
        return f"{self.nombre_crudo} → {self.sucursal_oficial.name}"
