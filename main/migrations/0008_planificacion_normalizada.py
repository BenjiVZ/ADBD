from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0007_sucursal"),
    ]

    operations = [
        migrations.AddField(
            model_name="planificacion",
            name="normalize_status",
            field=models.CharField(
                choices=[("pending", "Pendiente"), ("ok", "Normalizado"), ("error", "Error")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="planificacion",
            name="normalize_notes",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="planificacion",
            name="normalized_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="PlanificacionNormalizada",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plan_month", models.DateField()),
                ("tipo_carga", models.CharField(blank=True, default="", max_length=100)),
                ("item_code", models.CharField(blank=True, default="", max_length=100)),
                ("item_name", models.CharField(blank=True, default="", max_length=255)),
                ("cendis", models.CharField(blank=True, default="", max_length=255)),
                ("a_despachar_total", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="main.product",
                    ),
                ),
                (
                    "raw",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="normalizada",
                        to="main.planificacion",
                    ),
                ),
                (
                    "sucursal",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="main.sucursal"),
                ),
            ],
            options={
                "verbose_name": "Planificacion normalizada",
                "verbose_name_plural": "Planificaciones normalizadas",
                "ordering": ["-plan_month", "item_code", "sucursal__name"],
                "unique_together": {("plan_month", "item_code", "sucursal")},
            },
        ),
    ]
