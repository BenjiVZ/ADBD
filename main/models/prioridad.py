from django.db import models


class Prioridad(models.Model):
    name = models.CharField(max_length=100, unique=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Prioridad"
        verbose_name_plural = "Prioridades"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name
