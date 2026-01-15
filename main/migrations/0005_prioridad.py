from django.db import migrations, models


def seed_prioridades(apps, schema_editor):
    Prioridad = apps.get_model("main", "Prioridad")
    data = [
        ("1. PRIORIDAD", 1),
        ("2. LANZAMIENTO", 2),
        ("3. RELLENO", 3),
    ]
    for name, order in data:
        Prioridad.objects.get_or_create(name=name, defaults={"sort_order": order})


def unseed_prioridades(apps, schema_editor):
    Prioridad = apps.get_model("main", "Prioridad")
    names = ["1. PRIORIDAD", "2. LANZAMIENTO", "3. RELLENO"]
    Prioridad.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0004_salida"),
    ]

    operations = [
        migrations.CreateModel(
            name="Prioridad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("sort_order", models.IntegerField(default=0)),
            ],
            options={
                "verbose_name": "Prioridad",
                "verbose_name_plural": "Prioridades",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.RunPython(seed_prioridades, reverse_code=unseed_prioridades),
    ]
