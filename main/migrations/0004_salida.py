from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0003_planning"),
    ]

    operations = [
        migrations.CreateModel(
            name="Salida",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("salida", models.CharField(blank=True, default="", max_length=100)),
                ("fecha_salida", models.DateField(blank=True, null=True)),
                ("nombre_sucursal_origen", models.CharField(blank=True, default="", max_length=255)),
                ("nombre_almacen_origen", models.CharField(blank=True, default="", max_length=255)),
                ("sku", models.CharField(blank=True, default="", max_length=100)),
                ("descripcion", models.CharField(blank=True, default="", max_length=255)),
                ("cantidad", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("sucursal_destino_propuesto", models.CharField(blank=True, default="", max_length=255)),
                ("entrada", models.CharField(blank=True, default="", max_length=100)),
                ("fecha_entrada", models.DateField(blank=True, null=True)),
                ("nombre_sucursal_destino", models.CharField(blank=True, default="", max_length=255)),
                ("nombre_almacen_destino", models.CharField(blank=True, default="", max_length=255)),
                ("comments", models.CharField(blank=True, default="", max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Salida",
                "verbose_name_plural": "Salidas",
                "ordering": ["-fecha_salida", "-id"],
            },
        ),
    ]
