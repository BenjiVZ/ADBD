from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0002_cendis"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlanningBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plan_date", models.DateField()),
                ("sheet_name", models.CharField(max_length=255)),
                ("source_filename", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Planificacion",
                "verbose_name_plural": "Planificaciones",
                "ordering": ["-plan_date", "-id"],
            },
        ),
        migrations.CreateModel(
            name="PlanningEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.CharField(blank=True, default="", max_length=100)),
                ("tipo_carga", models.CharField(blank=True, default="", max_length=100)),
                ("ranking_tienda", models.IntegerField(blank=True, null=True)),
                ("sucursal", models.CharField(blank=True, default="", max_length=255)),
                ("item_code", models.CharField(blank=True, default="", max_length=100)),
                ("item_name", models.CharField(blank=True, default="", max_length=255)),
                ("u_categoria", models.CharField(blank=True, default="", max_length=100)),
                ("categoria", models.CharField(blank=True, default="", max_length=100)),
                ("a_despachar_total", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("motivo_decision", models.CharField(blank=True, default="", max_length=255)),
                ("en_transito", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("ult_entrada_almacen", models.DateField(blank=True, null=True)),
                ("ult_venta_tienda", models.DateField(blank=True, null=True)),
                ("dias_permanencia", models.IntegerField(blank=True, null=True)),
                ("venta_diaria", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("stock_tienda", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("stock_cedis", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("necesidad_urgente", models.BooleanField(default=False)),
                ("cendis", models.CharField(blank=True, default="", max_length=100)),
                ("no_planificar", models.BooleanField(default=False)),
                ("ng", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("ccct", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("sm", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("cubicaje_unidad", models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True)),
                ("cubicaje_total", models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True)),
                ("batch", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="entries", to="main.planningbatch")),
            ],
            options={
                "verbose_name": "Detalle de Planificacion",
                "verbose_name_plural": "Detalle de Planificacion",
                "ordering": ["item_code", "sucursal"],
            },
        ),
    ]
