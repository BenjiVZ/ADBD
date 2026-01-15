from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0008_planificacion_normalizada"),
    ]

    operations = [
        migrations.AddField(
            model_name="salida",
            name="normalize_status",
            field=models.CharField(choices=[("pending", "Pendiente"), ("ok", "Normalizado"), ("error", "Error")], default="pending", max_length=20),
        ),
        migrations.AddField(
            model_name="salida",
            name="normalize_notes",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="salida",
            name="normalized_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="SalidaNormalizada",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("salida", models.CharField(blank=True, default="", max_length=100)),
                ("fecha_salida", models.DateField(blank=True, null=True)),
                ("sku", models.CharField(blank=True, default="", max_length=100)),
                ("descripcion", models.CharField(blank=True, default="", max_length=255)),
                ("cantidad", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("origen_nombre", models.CharField(blank=True, default="", max_length=255)),
                ("destino_nombre", models.CharField(blank=True, default="", max_length=255)),
                ("entrada", models.CharField(blank=True, default="", max_length=100)),
                ("fecha_entrada", models.DateField(blank=True, null=True)),
                ("comments", models.CharField(blank=True, default="", max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="main.product"),
                ),
                (
                    "raw",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="normalizada", to="main.salida"),
                ),
                (
                    "sucursal_destino",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="salidas_destino", to="main.sucursal"),
                ),
                (
                    "sucursal_origen",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="salidas_origen", to="main.sucursal"),
                ),
            ],
            options={
                "verbose_name": "Salida normalizada",
                "verbose_name_plural": "Salidas normalizadas",
                "ordering": ["-fecha_salida", "salida", "sku"],
                "unique_together": {("salida", "fecha_salida", "sku")},
            },
        ),
    ]
