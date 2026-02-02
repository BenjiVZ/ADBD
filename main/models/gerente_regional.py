from django.db import models


class GerenteRegional(models.Model):
    """Gerente Regional - Responsable de un grupo de regiones"""
    name = models.CharField(max_length=255, unique=True, help_text="Nombre del gerente regional")
    email = models.EmailField(blank=True, null=True, help_text="Correo electrónico del gerente")
    telefono = models.CharField(max_length=50, blank=True, null=True, help_text="Teléfono de contacto")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Gerente Regional"
        verbose_name_plural = "Gerentes Regionales"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
