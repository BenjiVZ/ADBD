from django.db import models


class Product(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    group = models.CharField(max_length=255, blank=True, default="")
    manufacturer = models.CharField(max_length=255, blank=True, default="")
    category = models.CharField(max_length=255, blank=True, default="")
    subcategory = models.CharField(max_length=255, blank=True, default="")
    size = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Maestro de Productos"
        verbose_name_plural = "Maestro de Productos"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
