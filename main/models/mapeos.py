"""
Modelos para guardar mapeos/alias de CEDIS y Sucursales.
Estos mapeos NO modifican los datos crudos originales.

El sistema de normalización busca coincidencias en este orden:
1. Búsqueda directa por nombre, ID o código en maestros
2. Búsqueda en mapeos por nombre_crudo (puede ser nombre o ID)
3. El mapeo automáticamente incluye el ID del registro oficial mapeado
"""
from django.db import models


class MapeoCedis(models.Model):
    """
    Guarda la relación entre un nombre/ID crudo y un CEDIS oficial.
    Ejemplos:
    - "Guatire I" -> Cendis(origin="Guatire 1")
    - "123" -> Cendis(id=5)
    - "VALENCIA" -> Cendis(code="VAL")
    
    Durante la normalización, el sistema busca por:
    - nombre_crudo (puede contener nombre o ID)
    - ID del CEDIS oficial (automático)
    - código del CEDIS oficial (automático)
    """
    nombre_crudo = models.CharField(max_length=255, unique=True, help_text="Nombre o ID tal como aparece en los Excel")
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
    Guarda la relación entre un nombre/ID crudo y una Sucursal oficial.
    Ejemplos:
    - "SAMBIL VALENCIA" -> Sucursal(name="Sambil Valencia")
    - "25" -> Sucursal(bpl_id=25)
    - "SUC-025" -> Sucursal(bpl_id=25)
    
    Durante la normalización, el sistema busca por:
    - nombre_crudo (puede contener nombre o ID)
    - BPL_ID de la sucursal oficial (automático)
    """
    nombre_crudo = models.CharField(max_length=255, unique=True, help_text="Nombre o ID tal como aparece en los Excel")
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
