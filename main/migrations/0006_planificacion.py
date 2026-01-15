from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0005_prioridad"),
    ]

    operations = [
        migrations.CreateModel(
            name="Planificacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plan_month", models.DateField()),
                ("tipo_carga", models.CharField(blank=True, default="", max_length=100)),
                ("item_code", models.CharField(blank=True, default="", max_length=100)),
                ("item_name", models.CharField(blank=True, default="", max_length=255)),
                ("sucursal", models.CharField(blank=True, default="", max_length=255)),
                ("cendis", models.CharField(blank=True, default="", max_length=255)),
                ("a_despachar_total", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Planificacion mensual",
                "verbose_name_plural": "Planificaciones mensuales",
                "ordering": ["-plan_month", "item_code", "sucursal"],
            },
        ),
    ]
